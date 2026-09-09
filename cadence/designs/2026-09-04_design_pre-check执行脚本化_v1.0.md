# 设计文档：pre-check 执行脚本化提速

> **版本**：v1.0
> **日期**：2026-09-04
> **状态**：已获维护者口头批准，转入 Plan
> **证据源**：`cadence/plans/2026-09-04_计划文档_pre-check执行提速分析_v0.1.md`（sol-worker，389 行，transcript 实证）
> **关联**：eval 夜测体系（rule-eval-p0 已归档）；初始化命令顺序变更（提交 27e87e2）

## 一、背景与问题

eval 夜测对 pre-check skill 的真实执行（claude CLI，GLM 后端默认模型）实测 **6 分 38 秒**，维护者预期 2-3 分钟。transcript 实证分解：

- 22 次工具调用，**真实执行合计 8.45 秒**；
- 模型等待合计 **350.8 秒（97.65%）**，其中 4 段手写 bash heredoc 的设计/生成超过 139 秒（执行仅 4.96 秒）；
- 机械动作明细：基础工具复验 0.55s、OpenSpec init+update 2.44s、Superpowers fetch/pull 4.60s、软链盘点/同步 0.36s。

根因：`pre-check.sh` 只覆盖六基础工具；OpenSpec 四端投影、Superpowers git 更新、四层软链同步由 SKILL.md 以**文字描述**交给模型自由编排——模型临场编程、跳步、拼错 URL、zsh 分词失败重试等路径不确定性既慢又不可断言。

## 二、目标与非目标

**目标**

1. 总耗时 **≤2 分钟**，不分增量/冷启动（首次工具安装与 Superpowers 首次克隆依赖 cn 镜像加速，同样纳入 2 分钟目标）；240 秒仅作为网络异常的熔断硬上限，超时判 INFRA_FAIL，不作为合格线；
2. 执行路径 100% 确定：模型工具调用次数 ≤5，全部动作可由 JSON 报告断言；
3. 产物与现状 **1:1**（改前/改后同 fixture 产物树 diff 为零）；
4. 幂等：已初始化项目重跑 → 五个 phase 均零写入，统一记 `skipped` + 产物零变化。

**非目标**

1. 不改 mcp-configuration / rule-config / project-rules-examples；
2. 不为冷启动另设预算或宽松验收（网络极端异常由 240 秒熔断兑底，不回退模型自由执行）；
3. 不砍普通模式的报告详尽度；
4. 不引入新依赖（纯 Bash + 现有 CLI）。

## 三、两层契约（架构核心）

### 模型层：SKILL.md 收敛为三步

1. 定位 skill 目录，拼出 `<PRE_CHECK_SH>` 绝对路径（现有约定不变）；
2. 在**项目根目录**执行一次：`bash "<PRE_CHECK_SH>" run [--mirror cn] [--no-interrupt]`（cwd 即项目根，**不新增参数**）；
3. 读 JSON 报告 → 中文呈现；失败按模式处理（no-interrupt 终止 / 普通模式报告不继续）。

模型**不得**自行改写安装/更新/软链命令；脚本 `unsupported` 场景报告需人工处理，不静默回退模型自由发挥。

### 脚本层：run 子命令内部五阶段

````text
base-tools → openspec → superpowers-git → superpowers-links → verify
````

全部确定性动作入脚本；各阶段独立计时、独立失败语义。

## 四、pre-check.sh 扩展设计

### 4.1 接口（零变化）

````text
pre-check.sh run   [--mirror <name>] [--no-interrupt] [--upgrade]
pre-check.sh check [--mirror <name>] [--no-interrupt]
````

- `run` 内部顺序执行五阶段；`check` 仅探测不写入（现状语义保持，输出扩展为全阶段状态）；
- 项目根取 `$(pwd -P)`，不新增 `--project-root` 参数（模型在项目内执行，子进程继承 cwd）。

### 4.2 阶段设计

| 阶段 | 动作 | 幂等规则 |
|---|---|---|
| base-tools | 现有六工具探测/安装（不动） | 已装且零写入 → `skipped`；首跑安装/更新按实际写入记 `success` |
| openspec | 四端检测：`.claude/skills/openspec-*`+`.claude/commands/opsx/`、`.agents/skills/openspec-*`、`.pi/skills/`(5)+`.pi/prompts/`(5)、`.kimi-code/skills/`(5)；只对缺失端执行 `openspec init --tools`，仅在本次补齐后最多一次 `openspec update` | 四端齐全不执行 `update`；齐全且零写入 → `skipped` |
| superpowers-git | 来源目录有效性校验（非 Git work tree 即失败，不拿任意目录兜底）；已有仓库：候选 origin 逐个切换 + `fetch` + `pull --ff-only`；无仓库：候选逐个 `clone --depth 1`。候选在 **Bash 数组**内逐个解析，禁止拼接 | `fetch`/`pull` 无新 revision 或 `Already up to date` 且零写入 → `skipped`；有 revision 写入 → `success`；每次命令受 phase 180 秒总预算约束 |
| superpowers-links | 四层软链（`~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills`、`~/.pi/agent/skills`）：correct → skip；stale/broken（仅 Superpowers 所有权范围）→ 修复；同名非软链 → 普通模式 warning/skip，no-interrupt 备份→创建→验证。`correct` 按解析后最终等价判定，直连源路径和经 `~/.agents/skills` 中转均正确 | 本 phase `created=updated=0` 且 `conflicts=0` → `skipped`；否则有写入 → `success` |
| verify | 各阶段产物路径/数量/软链可解析性复核，输出进报告 | 只读、零写入且无冲突 → `skipped`、`action=all-skipped` |

### 4.3 报告 schema（向后兼容）

- 原 `steps[]`（六工具）**字段不动**；
- **新增 `phases[]`：** 每项含 `phase` / `result`（`success|partial|failed|skipped`）/ `action` / `duration_ms` / `created|updated|skipped|conflicts` 计数 / `error`（`string|null`）；`superpowers-git` 另含 `origin`、`branch`、`before_revision`、`after_revision`。`GIT_ERROR`、`VERIFY_ERROR` 必须落入对应 phase 的 `error` 字段；`skipped` 仅表示该 phase 零写入且无冲突。
- **顶层字段：** `overall` 判定纳入五阶段；`hints` 保留。

### 4.4 约束

- Bash 3.2 兼容（macOS）：不用关联数组、`mapfile`/`readarray`、`sort -V`、`grep -P`、GNU-only `readlink -f` 或 Bash 4.x 特性；候选使用普通 indexed array，声明 `MAX_GIT_CANDIDATES=3` 限制候选数，并用静态禁用清单检查 `declare -A`、`mapfile`、`readarray`、`&>>` 等写法；zsh 测试使用 `skipUnless(shutil.which("zsh"))`。
- 网络预算：单候选 git timeout 60s，整个 `superpowers-git` phase 180s；phase 内每次 `clone`/`fetch`/`pull` 先计算 `phase_remaining_s`，将单次预算与动态剩余预算取小值传给 `run_with_timeout`，剩余不足 1 秒时不再启动命令；`duration_ms` 为非负整数，精度注明为毫秒整数（Bash 3.2/macOS 可回退到秒级计时，不承诺亚毫秒精度）。
- 失败快返：no-interrupt 任一阶段失败立即非零退出，不执行下游写入；普通模式由 `run_required_phase` 记录失败 phase、返回码和 `partial`，继续执行下游并由主流程统一 `emit_report`，不静默回退模型自由编排；`handle_failure` 只记录失败 phase、错误和返回码，不提前 emit 或 exit。
- 完整策略配置：`policy.json` 保留现有 13 个键，仅新增 `stage1_pre_check_timeout_s=240`（pre-check 单命令熔断，其余三命令沿用 `stage1_timeout_s=1200`），共 14 键；验收线（≤2 分钟）由断言层执行，不进 policy。
- 四端投影、四层链接 fixture 和旧实现兼容性 baseline 必须纳入测试；正确软链通过解析最终目标判定，`skipped` 仅用于零写入 phase。
- 独占 report 文件由调用方（模型）以 mktemp 创建并清理（现状约定不变）。

## 五、SKILL.md 改造

1. 参数模式不变（`no-interrupt` / `--no-interrupt` / 镜像由脚本参数承载）；
2. 步骤 1-6 的模型执行描述（OpenSpec init、Superpowers update、软链同步、逐项验证）全部替换为“读 `phases[]` 呈现”；第 48-60 行 no-interrupt 完成策略表、第 150-170 行增量运行、第 195-232 行 dot 图/快速参考表必须逐节删除或改写为五 phase/三步契约；第 375-378 行软链拓扑描述改为解析后等价（现网直连源路径、兼容中转链）。
3. 删除诱导模型临时编程的长 one-liner/heredoc 示例；
4. 保留：人工 fallback 说明、Playwright 显式 opt-in（不装不写）、API Key 只展示占位符的约束；
5. no-interrupt 完成判定表更新：以 `overall=success` + 五阶段 result 为准；首跑有确定性写入的 phase 按 `success` 断言，二跑/已就绪且 `created=updated=conflicts=0` 的 phase 按 `skipped` 断言。

## 六、兼容性策略

| 项 | 策略 |
|---|---|
| 产物 1:1 | 兼容性验收使用同一隔离 fixture 的旧实现基线与新实现快照逐项 diff；对目标写入按四端 OpenSpec 投影、Superpowers Git 与软链契约核对，zero-change 断言只要求非目标文件零改动，不能把四端投影白名单纳入“零改动”比较 |
| 软链拓扑 | 以解析后等价判定：`readlink` 原文解析后的最终路径必须等于 `$SUPERPOWERS_DIR/skills/<name>`；现网四层为直连源路径，兼容经 `~/.agents/skills/<name>` 中转的分层拓扑；两种拓扑都记 `correct`/`skipped`，不按 `readlink` 原文字符串比较。 |
| 普通模式交互降级 | 原模型现场询问冲突 → 报告 warning 列出、决策留给维护者（已获批准）；phase 失败记 `partial` 并继续下游，最终由主流程统一报告 |
| 报告消费方 | SKILL.md 后续步骤、eval stage1 断言同步扩展 |
| eval 断言联动 | 新增：四端投影路径/数量、软链 14/14 可解析、首跑有写入 phase 为 `success`、二跑/已就绪零写入 phase 为 `skipped`、工具调用次数 ≤5、总时长 ≤2 分钟；zero-change 断言排除四端投影白名单 |
| 兼容性基线 | Task 1 的前置门禁先用旧脚本+旧 `SKILL.md` 在隔离 fixture 采集一次产物树，保存每条软链 `readlink` 原文与解析目标；Task 8 对 old/new 快照执行硬 diff |

## 七、测试与验收

### 7.1 单元/fixture（10 条负向，源自分析文档第五节）

1. 基础工具失败：no-interrupt 立即失败，无下游产物；
2. OpenSpec 仅缺 pi/kimi：只 init 缺失端，已就绪端不覆盖；
3. Superpowers 来源不存在：候选逐一 clone，失败清理并返回失败；
4. 来源非 Git：立即失败；
5. 外层 shell 为 zsh 且多候选：脚本内仍逐个解析，不拼接；
6. 四层已有正确链：全 skipped，不重写；
7. 同名非软链：普通 warning/skip；no-interrupt 备份→创建→验证，原内容不删除；
8. pi 层缺 Cadence skill：Superpowers 阶段仍 success，不为总数相等补链（不比较四层总数）；
9. Playwright 未请求：不安装不写入；
10. 成功/失败/超时均清理独占 report。

### 7.2 集成验收

- 真实 claude 跑 `/pre-check no-interrupt --mirror cn`：transcript 断言工具调用 ≤5 次、总时长 ≤2 分钟、产物 1:1；
- 已初始化项目重跑：五阶段均零写入并记 `skipped` + 产物树零变化。

### 7.3 eval 联动

- stage1 断言扩展（见第六节）；
- timeout 预算：验收线统一 ≤2 分钟（所有场景）；`stage1_pre_check_timeout_s=240` 仅作网络异常熔断，超时判 INFRA_FAIL。

## 八、提速预估

````text
现状 398s ≈ 启动 20s + 定位探索 30s + 脚本 0.6s + 模型编排思考 345s
优化后  ≈ 启动+读SKILL 40s + 定位拼命令 30s + 脚本执行 ~8s + 读报告呈现 30s
        ≈ 110s（约 1.8 分钟）
````

收益全部来自消除模型临场编程（heredoc 生成 139s + 状态探测决策停顿约 200s）。

## 九、风险与缓解

| 风险 | 缓解 |
|---|---|
| HOME 所有权误判（覆盖用户文件） | 仅按 Superpowers 条目所有权操作；非目标内容快照前后对比断言 |
| openspec/codegraph CLI 版本演进改目录布局 | 断言锚定路径而非 stdout 文案；`unsupported` 显式报告 |
| Bash 3.2 兼容性 | 单测覆盖；禁用 4.x 特性 |
| 网络抖动误判 INFRA_FAIL | 单候选/总 timeout 分层；失败输出结构化错误 |
| 评估回归 | 改前后产物树 diff + eval 全量单测（133+）绿 |
