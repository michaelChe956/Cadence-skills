# OpenSpec 与 Superpowers 路由验收矩阵

> 状态：🟡 `REVIEW_PENDING / 客户端级跨轮证据 18/18 PASS，Kimi 跨版本、跨模型一致性存在风险`

## 一、验证范围

- OpenSpec change：`improve-progressive-disclosure-routing`
- OpenSpec 工作包：`5.1`
- 验证对象：Claude Code、Kimi Code、Codex
- 验证内容：静态一致性检查，以及三个客户端的六类关键路由场景
- 验证根目录：由 `git rev-parse --show-toplevel` 在执行时解析，不在报告中持久化临时 worktree 绝对路径
- 数据最小化：静态检查与 Codex 使用真实工作树只读验证；用户明确知情授权后，Claude Code 在当前 Head 的 19 文件脱敏夹具中定向复测 S1、S5；主代理在直接授权上下文中使用同等最小隔离边界连接 Kimi，仅发送脱敏夹具，S2–S6 取得可审计响应
- 判定值：`PASS`、`FAIL`、`BLOCKED`

### 脱敏夹具审计

- 创建方式：`mktemp -d`、`mkdir`、`cp`/`cp -a` 机械复制，不生成脚本。
- 夹具文件范围：共 19 个文件，仅包含 `CLAUDE.md`、`AGENTS.md`、`.claude/rules/`、`openspec/config.yaml` 与目标 change。
- 一致性：三个单文件 `cmp`、两个目录 `diff -qr` 均退出 0；`.git` 与 `cadence` 不存在。
- Kimi 隔离可见集合：19 文件脱敏夹具、Kimi 单个可执行运行时、精确认证材料（`config.toml`、`device_id`、`credentials/`、`oauth/`）、Superpowers Skills 目录、必需系统运行时与 tmpfs 运行态。认证材料仅用于建立连接，不作为模型上下文。
- Kimi 隔离边界：不使用 `--ro-bind / /`；完整用户目录与 `/root` 使用 tmpfs 隐藏，夹具只读，不可见 Git 元数据、业务源码、完整私有工作区或完整用户目录。

| 相对路径 | SHA-256 |
|---|---|
| `.claude/rules/README.md` | `eecc92f0e18d7dc07a1b74aaa3e8d42c81276806e58487bd43f818d4dae54828` |
| `.claude/rules/code-reading.md` | `03b7471a78fb34a6f97e35241a1d59c724f5114bd4fee3879836a294f97100f8` |
| `.claude/rules/code-usage.md` | `fac1e300d7d4de0242e5fce5d281caa0ccfb97cb4745597abe94b1e8ee897088` |
| `.claude/rules/document-storage.md` | `10672fda93c99283c732e60dd900b7bb65e3c3733e240a775004cc592c0ae422` |
| `.claude/rules/language.md` | `161a43fbb6ce96f9fc832335fb771bcabea495ef7fafe619c490eb8f14af2588` |
| `.claude/rules/markdown-format.md` | `0be1029d074f3a032ac7031cabe302f5b829a9ab8f83e6c5916b60fbfd2ee74f` |
| `.claude/rules/mcp-servers.md` | `3eccd8fdb11edaa8a0fe4f629667c1e2224352dd259aaf58ea3f33b166773884` |
| `.claude/rules/openspec-superpowers-workflow.md` | `758f4b51ee4c0808db3cc02862df3af949e88906d16dd6824838b0265156b5b2` |
| `.claude/rules/playwright.md` | `0248c02caae5841e29e4d13ea9118001cd6bdcad8b0a1ef2a854dc87162982a1` |
| `AGENTS.md` | `b9f591fe6e621c58cc931928f8caa93c7670784208afde124edcde7ff3a7d280` |
| `CLAUDE.md` | `819f235ea56b771ab96dd29f5d5df54facd6282b2a614c24c53a3610f6800d61` |
| `openspec/config.yaml` | `650390ed1019338e61520ed3d95c4a8ab50fe401be73a7a785c30af6c1bb0464` |
| `openspec/changes/improve-progressive-disclosure-routing/.openspec.yaml` | `de76da64ea78cfbcca727518866c848b20ea41b11d77cbb92ef64e61f479cf96` |
| `openspec/changes/improve-progressive-disclosure-routing/design.md` | `d21322d5b00d01b08997cd4f75b49146a8f090f523f586fd3139bebc262ec497` |
| `openspec/changes/improve-progressive-disclosure-routing/proposal.md` | `fcd3d253583b44065cf21a353562d834cdb1d51933b3d880eeb658f906c211b0` |
| `openspec/changes/improve-progressive-disclosure-routing/specs/managed-rule-lifecycle/spec.md` | `e6dfaa8a95c8b58daee0d89a5eb76b625f25caeaaf07934058cccadff6515e45` |
| `openspec/changes/improve-progressive-disclosure-routing/specs/progressive-context-routing/spec.md` | `b724ada8bec557f8294d413d8ec3961d302d16b61e05d508a17943c2b1e0cdd9` |
| `openspec/changes/improve-progressive-disclosure-routing/specs/routing-conformance/spec.md` | `a73e5150b5e4e35eaa43e567d339ee80fbf3e52d57d8ab25b2826fb5eb24dcde` |
| `openspec/changes/improve-progressive-disclosure-routing/tasks.md` | `0669a96d5d08b408dee45bbe1ecc9a5389608d9ba2200972efb5c6b69713b3de` |

## 二、客户端与工具版本

| 工具 | 实际版本 | 命令退出码 | 备注 |
|---|---|---:|---|
| Claude Code | `2.1.212 (Claude Code)` | 0 | 版本命令正常 |
| Kimi Code | `0.27.0`、`0.28.0` | 0 | S2–S6 沿用既有客户端证据；最新 S1 使用 0.28.0 K3；同版本 K2.7 Coding 对照轮保留 |
| Codex | `codex-cli 0.144.6` | 0 | 同时警告无法在只读文件系统创建 PATH alias；不影响版本命令 |
| OpenSpec | `1.4.1` | 0 | 版本命令正常 |

## 三、静态检查

| 编号 | 检查 | 命令 | 退出码 | 原始摘要 | 结论 |
|---|---|---|---:|---|---|
| C1 | L1 规范源与生成副本一致 | `cmp cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md .claude/rules/openspec-superpowers-workflow.md` | 0 | 无输出，文件逐字节一致 | PASS |
| C2 | OpenSpec 配置源与当前副本一致 | `cmp cadence-init/skills/rule-config/references/openspec/config.yaml openspec/config.yaml` | 0 | 无输出，文件逐字节一致 | PASS |
| C3 | L0 start 标记总数为 2 | `test "$(rg --no-filename -o "cadence-managed:openspec-superpowers-routing:v1:start" CLAUDE.md AGENTS.md \| wc -l)" -eq 2` | 0 | 无输出，断言成立 | PASS |
| C4 | L0 end 标记总数为 2 | `test "$(rg --no-filename -o "cadence-managed:openspec-superpowers-routing:v1:end" CLAUDE.md AGENTS.md \| wc -l)" -eq 2` | 0 | 无输出，断言成立 | PASS |
| C5 | OpenSpec 不含无效 `rules.apply` | `if rg -n "^  apply:" openspec/config.yaml; then exit 1; fi` | 0 | 无匹配输出 | PASS |
| C6 | L0 引用的 Superpowers Skill 均存在 | `for skill in ...; do test -f "$CADENCE_SUPERPOWERS_DIR/$skill/SKILL.md" \|\| exit 1; done` | 0 | 无输出，十个 Skill 文件均存在 | PASS |
| C7 | OpenSpec strict 校验 | `openspec validate improve-progressive-disclosure-routing --type change --strict --no-interactive` | 0 | `Change 'improve-progressive-disclosure-routing' is valid` | PASS |
| C8 | L0 规范源与两个入口受管区块一致 | 对 `CLAUDE.md`、`AGENTS.md` 提取受管区块后分别与 `agent-routing-kernel.md` 执行 `cmp` | 0 / 0 | L0 修复后两次 `cmp` 均无输出 | PASS |
| C9 | Plan Task 1 内嵌 L0 与规范源一致 | 提取 Plan 受管区块后与 `agent-routing-kernel.md` 执行 `cmp` | 0 | 无输出，三副本一致 | PASS |
| C10 | L0 体积与轻量路由断言 | 统计 L0 行数，并检查纯概念问答豁免与 S1 前置回执文本 | 0 | L0 为 26 行，两类断言均成立 | PASS |
| C11 | Kimi 包装隔离与本地冒烟 | 检查集中变量、禁止宽挂载、用户目录隐藏、夹具只读，并仅执行 `cadence_run_kimi_isolated --version` | 0 | Kimi 最新输出 `0.28.0`，隔离断言均成立 | PASS |

首次静态检查、Claude S1 的 L0 修复后静态复测，以及本次审查修复的完整本地复测均退出 0。

## 四、场景定义

| 场景 | 输入类型 | 严格判定标准 |
|---|---|---|
| S1 | 新功能 | 识别探索阶段、`using-superpowers` 与 `brainstorming`，不进入实现 |
| S2 | Bug | 先路由 `systematic-debugging`，根因确认后才进入 `test-driven-development` |
| S3 | 直接 apply | 无已确认 Plan 时拒绝实施，并路由 `writing-plans` |
| S4 | compact/resume | 重新识别阶段、Change、Plan 和必调 Skill，并重做门禁 |
| S5 | 纯概念问答 | 一句话轻量回答，不读取仓库、不调用工具、不加载无关正文 |
| S6 | 完工声明 | 拒绝无证据完成声明，并路由 `verification-before-completion` |

## 五、三客户端场景矩阵

| 客户端 | 场景 | 期望阶段与 Skill | 实际路由与加载 | 门禁结果 | 无关正文误加载 | 结论 |
|---|---|---|---|---|---|---|
| Claude Code | S1 | 探索；`using-superpowers`、`brainstorming` | 保留历史首次 `FAIL` 与 180 秒超时证据。取证基线 `b1e13f5` 在新建 19 文件夹具中退出 0；首段输出阶段、Change、Plan、`using-superpowers → brainstorming`，并明确回执前未勘察仓库 | 明确设计确认后才进入 OpenSpec，当前不规划、不实施、不修改文件 | 回执前无仓库/change/Plan 勘察，无实现正文 | PASS |
| Claude Code | S2 | 调试；`systematic-debugging` 后 TDD | 脱敏夹具命令退出 0；原始回执“阶段=调试/根因分析；Change=待定；Plan=无；必调 Skill=using-superpowers → systematic-debugging”，并说明根因后才进入 TDD | 明确根因未确认不得写修复；根因确认后调用 `test-driven-development` 并先写失败测试 | 仅额外提及完成验证/审查门禁，未加载无关正文 | PASS |
| Claude Code | S3 | 规划；拒绝 apply，`writing-plans` | 脱敏夹具命令退出 0；识别目标 change 与 `cadence/plans/` 不存在，原文“不允许继续，必须停止”，要求先 `writing-plans` | 无已确认 Plan 时停止，禁止执行 tasks 或修改文件 | 仅读取 change 状态与直接相关协作规则 | PASS |
| Claude Code | S4 | 恢复；重识别四字段与门禁 | 脱敏夹具命令退出 0；列出阶段、Change、Plan、首调 `using-superpowers` 后按阶段补调 Skill | 明确缺 Skill、缺 Plan、契约变化或缺新鲜证据时失败关闭 | 仅说明恢复路由与相关门禁 | PASS |
| Claude Code | S5 | 轻量问答；无 Skill 正文 | 历史 S5 `PASS` 保留。取证基线 `b1e13f5` 定向复测退出 0，仅输出一句渐进式披露定义 | 纯问答豁免生效，无仓库路由回执或工具调用 | 无实现、OpenSpec、Plan、验证或文档写入正文 | PASS |
| Claude Code | S6 | 验证；`verification-before-completion` | 脱敏夹具命令退出 0；先回执“阶段=完工声明；Change=improve-progressive-disclosure-routing；Plan=未核验；必调 Skill=verification-before-completion” | 明确拒绝无验证命令、无新鲜证据的完成声明 | 仅说明完工验证直接相关流程 | PASS |
| Kimi Code | S1 | 探索；`using-superpowers`、`brainstorming` | Kimi 0.28.0、默认模型 K3、交互 `--plan`。相同原始提示词仅提交一次；在任何仓库工具前输出阶段、Change、Plan 与必调 Skill 完整回执，随后 UI 原生出现 `Used Skill (using-superpowers)`、`Activated skill: using-superpowers`、`Used Skill (brainstorming)`、`Activated skill: brainstorming` | 两个 Skill 均通过客户端机制实际激活；激活后才进入 brainstorming 澄清，未进入实施 | 未修改文件；无实现正文。K2.7 Coding 相同提示词只普通读取 `SKILL.md` 的失败作为兼容性证据保留 | PASS |
| Kimi Code | S2 | 调试；`systematic-debugging` 后 TDD | `-p` 退出 0；完整回执识别 Bug 调试/根因未知，必调 `using-superpowers → systematic-debugging`，并说明根因确认后才切换 TDD、先失败测试、完工前验证 | 按 prompt 未读写文件；明确根因未确认时不修复 | 无无关正文加载 | PASS |
| Kimi Code | S3 | 规划；拒绝 apply，`writing-plans` | `-p` 退出 0；完整回执识别 apply 前置门禁、正确 Change 和 Plan=无，明确“不允许继续” | 已有 change 无 Plan 必须停止，先 `writing-plans`，后 `executing-plans` 或 `subagent-driven-development` | 仅加载直接相关门禁 | PASS |
| Kimi Code | S4 | 恢复；重识别四字段与门禁 | `-p` 退出 0；列出阶段、Change、Plan、必调 Skill 四字段，要求恢复后先 `using-superpowers`，实施时使用 `executing-plans` 或 `subagent-driven-development` | 无已确认 Plan、缺 Skill 或契约变化时停止 | 仅加载恢复门禁相关正文 | PASS |
| Kimi Code | S5 | 轻量问答；无 Skill 正文 | `-p` 退出 0；无工具调用，直接输出一条定义句；原始输出带简短标题“渐进式披露” | 核心轻量问答行为通过；无仓库路由回执、Skill/规则加载 | 除简短标题和定义句外无无关正文，不声称逐字仅一行 | PASS |
| Kimi Code | S6 | 验证；`verification-before-completion` | 首次 60 秒退出 124；定向 120 秒重试退出 0。完整回执识别完工声明、正确 Change、Plan 未确认和必调 `verification-before-completion` | 明确拒绝“未验证却声明完成/测试通过”，引用无新鲜证据不得完成，并建议实际验证 | 仅加载完工验证直接相关正文 | PASS |
| Codex | S1 | 探索；`using-superpowers`、`brainstorming` | 首次沙箱内调用退出 1：`failed to initialize in-process app-server client: Read-only file system`；最小权限重试退出 0。原始响应先给出“阶段=新功能需求澄清与方案讨论；Change=尚未创建/确认；Plan=尚不存在；必调 Skill=using-superpowers、brainstorming”，随后实际读取两个 Skill、L1/L0，并只读识别现有候选 Change/Plan | 明确“未获确认前不会进入 OpenSpec 或实施”，最终只提出 Change 归属澄清问题；未修改文件 | 读取了与潜在文档产物相关的文档/Markdown 规则，属 S1 路由表要求；未加载实现或完成验证正文 | PASS |
| Codex | S2 | 调试；`systematic-debugging` 后 TDD | 命令退出 0。原始响应：“阶段=测试失败诊断；Change=未确认；Plan=无；必调 Skill=`using-superpowers` → `systematic-debugging`”，并说明根因确认后才调用 `test-driven-development` | 遵守“不读取”约束而未加载 Skill 正文，按失败关闭停止；禁止猜测或修改代码，根因确认后重新路由进入 TDD | 无工具调用，无无关正文加载 | PASS |
| Codex | S3 | 规划；拒绝 apply，`writing-plans` | 命令退出 0。先回执“阶段=apply 前门禁检查；Change=improve-progressive-disclosure-routing；Plan=不存在”，只读加载 L0/L1、`using-superpowers`、`openspec-apply-change` 与 `executing-plans` 门禁；最终原文：“不允许继续 apply……应先调用 `writing-plans` 生成并确认 Plan” | 无已确认 Plan 时停止，没有读取 change 产物、没有执行工作包、没有修改文件 | 加载内容均与直接 apply 及其 Plan 门禁相关；无实现、审查或完成验证正文误加载 | PASS |
| Codex | S4 | 恢复；重识别四字段与门禁 | 命令退出 0。先回执“阶段=compact/resume 后恢复已有 OpenSpec change；Change=待重新确认；Plan=待重新确认；必调 Skill=using-superpowers”，实际重新读取 `using-superpowers`、L0 和 L1；最终列出阶段、Change、Plan、必调 Skill 四字段 | 明确 Skill 未加载、Change 未确认、无已确认 Plan、契约变化四类停止门禁，并要求 apply/实施前重新路由 | 仅加载恢复路由直接相关正文 | PASS |
| Codex | S5 | 轻量问答；无 Skill 正文 | 命令退出 0；原始响应仅一句：“渐进式披露是先展示最必要的信息，再根据用户需求逐步呈现更多细节，以降低认知负担。” | 直接回答，无仓库读取或工具调用 | 无任何正文加载 | PASS |
| Codex | S6 | 验证；`verification-before-completion` | 命令退出 0。先回执“阶段=完工声明前；Change=improve-progressive-disclosure-routing；Plan=未知；必调 Skill=using-superpowers、verification-before-completion”，实际读取 L0/L1 与两个 Skill | 拒绝声明，原文：“尚未在本次会话中验证，完成状态与测试结果未确认。”未运行验证命令 | 仅加载完成声明门禁直接相关正文 | PASS |

## 六、失败与修复映射

| 首次失败或阻塞 | 定位层 | 原始证据 | 最小修复 | 复测结果 |
|---|---|---|---|---|
| Kimi S1–S6 首次均为 `Cannot combine --prompt with --plan.` | Plan 执行命令 | Kimi 0.27.0 参数校验明确禁止 `--prompt` 与 `--plan` 组合；其 `-p` 又固定自动批准工具 | 六场景统一经 `cadence_run_kimi_isolated` 调用原生 `-p`；包装仅显式挂载夹具、Kimi 运行时、精确认证材料、Superpowers Skills 和必需系统运行时 | 本地无网络 `--version` 冒烟退出 0；直接授权上下文中 S2–S6 严格 `PASS`；Kimi 0.28.0 默认模型 K3 的 S1 精确轮严格 `PASS` |
| Kimi S1 跨模型行为不一致 | 客户端模型兼容性 | K2.7 Coding 精确轮只有普通 `Read .../SKILL.md`，无 Skill 调用事件；K3 精确轮出现两个 `Used Skill` 与对应激活事件 | 保留两轮证据；当前不把模型差异伪装为规则已修复。若要求所有可选模型一致，再评估是否强化 L0/L1 的原生调用判定 | 当前默认模型 K3 `PASS`；K2.7 Coding 对照轮 `FAIL`，记录为兼容性风险 |
| Kimi 包装宽挂载与用户目录暴露 | Plan 隔离边界 | 旧包装含 `--ro-bind / /`，对宿主可见面的约束过宽，且报告将“19 文件夹具”误表述为全部可见集合 | 删除宽挂载，集中 `CADENCE_KIMI_BIN`、`CADENCE_KIMI_HOME`、`CADENCE_VALIDATION_USER_DIR`、`CADENCE_SUPERPOWERS_DIR`；使用 tmpfs 隐藏完整用户目录与 `/root`，并断言夹具只读 | Plan 不再含 `--ro-bind / /`；包装内隔离断言与 `kimi --version` 均退出 0 |
| Codex S1 首次 app-server 初始化失败 | 执行环境 | 沙箱只读文件系统阻止 Codex 创建运行态 | 保持 Codex 自身 `--sandbox read-only`，申请最小外层权限重试；未修改规则 | 重试退出 0，S1 `PASS`；S2–S6 同方式均退出 0 |
| Claude 全工作树 S1–S6 无路由正文 | 执行环境/外部审批 | 沙箱内 API socket 不可达或超时；最小权限外部调用因私有工作区外传风险被拒绝 | 不更换模型、不绕过审批；构造仅含路由规则与目标 change 的脱敏夹具，并申请一次 materially safer 外部调用 | 脱敏复测 S2–S6 `PASS`；S1 暴露 L0 缺口后修复，但定向复测超时为 `BLOCKED` |
| Claude 脱敏 S1 首次遗漏前置路由 | L0 | 首次响应先勘察 change，未先输出阶段/Change/Plan/Skill，遗漏 `using-superpowers`；只提条件式 `brainstorming` | 强化 `agent-routing-kernel.md`：第一段必须先完整回执，回执前禁止任何只读勘察，澄清问题不得替代回执；同步 `CLAUDE.md` 与 `AGENTS.md` | 保留首次 `FAIL` 和随后 180 秒超时；取证基线 `b1e13f5` 的 240 秒上限定向复测退出 0，S1 严格 `PASS` |

## 七、未验证风险

- Kimi Code S2–S6 已在既有直接授权上下文中取得可审计 `PASS`；S1 在 0.28.0 K3 的精确单次提示词轮中取得严格 `PASS`。K3 本轮没有重跑 S2–S6。
- Kimi 0.28.0 的 K2.7 Coding 使用相同提示词时仍只直接读取两份 `SKILL.md`，没有客户端 Skill 调用事件，因此跨模型一致性未得到保证。
- Claude Code S1 首次 `FAIL`、随后超时和最终当前 Head `PASS` 证据均已保留；S5 也已在当前 Head 重新取得 `PASS`。
- Claude Code 与 Kimi Code 的可执行验证采用最小脱敏夹具。夹具覆盖 L0、L1、OpenSpec 配置与目标 change，且故意不含 Plan 以验证 S3；它不等同于完整工作树运行环境。
- 按客户端级跨轮证据，三客户端矩阵 18/18 通过；该结论不扩展为“同一 Kimi 版本或模型六场景全通过”，也不扩展为“Kimi 所有可选模型均通过”。

## 八、Kimi S1 跨模型证据与验收口径

- 客户端：Kimi Code `0.28.0`；模型：`K2.7 Coding`；模式：交互 `--plan`。
- 诊断轮会话：`session_30482b65-dcb6-46bf-b8a0-911e5ce49a86`。PTY 已启用 CSI-u 键盘协议，普通 CR/LF 未提交输入；随后再次发送提示词并使用 CSI-u Enter，导致同一提示词在一次消息中重复两遍。
- 诊断轮出现 `Used Skill (using-superpowers)`、`Used Skill (brainstorming)`、`Activated skill: using-superpowers`、`Activated skill: brainstorming`，Skill 事件后才读取仓库文件，且未实施。由于提示词重复，本轮只证明 Kimi 0.28.0 的客户端 Skill 调用机制可用，不作为最终 PASS 证据。
- 精确单次提示词轮会话：`session_01456b7a-5c13-4613-b8f2-b8caedc590cf`。使用 bracketed paste 加 CSI-u Enter，仅提交一次原始提示词。
- 精确轮在任何仓库工具前输出完整回执，但随后通过 `Read 3 files` 直接读取两份 `SKILL.md` 与 `CLAUDE.md`，没有客户端 `Used Skill` 或 `Activated skill` 事件，并继续 Glob/Read 勘察。Bash 只读命令审批被人工拒绝；未实施、未修改文件。
- K2.7 Coding 判定：`FAIL`。普通读取 `SKILL.md`、复述或声称已加载，不等于通过客户端 Skill 调用机制实际调用必调 Skill。
- K3 精确轮会话：`session_4a3f8f64-3c96-40a2-a66a-45bbd0842527`。Kimi 0.28.0、K3、thinking high、交互 `--plan`；相同提示词仅提交一次。
- K3 在任何仓库工具前输出完整回执，并出现 `Used Skill (using-superpowers)`、`Activated skill: using-superpowers`、`Used Skill (brainstorming)`、`Activated skill: brainstorming`；未实施、未修改文件，严格 `PASS`。
- K3 本轮只验证 S1，结果为 `PASS`；S2–S6 沿用既有 Kimi 客户端通过证据。
- 客户端级跨轮证据：Kimi 六场景 `6 PASS / 0 FAIL / 0 BLOCKED`，三客户端共 `18 PASS / 0 FAIL / 0 BLOCKED`。
- 兼容性口径：K2.7 Coding 的失败继续保留。OpenSpec requirement 未明确要求遍历所有可选模型，因此该差异记录为风险，是否将其升级为阻断项交由复审确认。

### 人工复现与修复后复测

1. 在同一个 Bash shell 中执行 Plan Task 5 Step 3 的完整代码块，创建 19 文件夹具并定义 `cadence_run_kimi_isolated`；不得删改或放宽挂载与断言。
2. 执行 `cadence_run_kimi_isolated --plan`。
3. 在真实终端中只粘贴一次原始 S1 提示词并按 Enter。自动 PTY 必须使用 bracketed paste 与 CSI-u Enter，不能先发送普通 CR/LF，否则可能形成重复输入。
4. `PASS` 必须同时看到完整前置回执、`Used Skill (using-superpowers)`、`Used Skill (brainstorming)`，并且不进入实施、不修改文件。
5. 若只显示普通 `Read .../SKILL.md`，即使模型声称“已加载”，仍判定 `FAIL`；认证、网络、沙箱或客户端无响应才判定 `BLOCKED`。

## 九、结论

客户端级跨轮验收结果为 `18 PASS / 0 FAIL / 0 BLOCKED`：Codex 与 Claude Code 各 6/6 `PASS`；Kimi S2–S6 沿用既有客户端通过证据，S1 由 0.28.0 K3 精确轮补齐为 `PASS`。Kimi 0.28.0 的 K2.7 Coding 对照轮仍为 S1 `FAIL`，因此本报告不声称同一 Kimi 版本或模型六场景全通过，也不声称跨模型稳定通过。Task 5 与 OpenSpec 5.1 暂不勾选，等待修正口径后的独立复审。
