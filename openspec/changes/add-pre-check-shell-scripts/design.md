# Design: add-pre-check-shell-scripts

## Context

`pre-check` 是 cadence-init 插件的第一个初始化 Skill，负责安装并验证 npx/uvx/ast-grep/codegraph/openspec/pi-mcp-adapter 六个工具，并向 Superpowers 四个目标目录同步软链。当前实现把六个工具的全部安装/验证命令、增量分支、no-interrupt 门槛以正文形式写在 `SKILL.md` 中，由模型逐条推理执行。

根因调查与 brainstorming 已确认三个痛点：

1. **模型负担**：六个工具约 20 条命令与大量增量/冲突分支全靠模型推理，token 消耗高、一致性差。
2. **大陆可用性**：默认 npm/pypi/GitHub 源在大陆不稳定，现有逻辑无镜像切换能力。
3. **重复执行慢**：增量判断靠模型逐条比对，缺毫秒级版本探测与秒跳过机制。

约束与现状：

- 项目已有脚本目录约定：`skill-creator/scripts/`（Python 脚本，由所属 skill 调用）。本设计沿用“脚本放 skill 同级 `scripts/` 目录”的约定；但 SKILL.md 对脚本的引用**不沿用相对路径**——因 Agent 各命令在独立 shell 执行、无共享 cwd，SKILL.md 改用完整绝对路径 `<PRE_CHECK_SH>` 调用脚本（详见决策 8）。
- Superpowers 国内 Git 镜像已由用户同步至 `https://gitee.com/michaelChe-World/superpowers.git`。
- `openspec/specs/init-skill-sequencing` 已定义 OpenSpec 三客户端产物补齐与失败门槛语义，本 change 保留这些语义，仅补充脚本化后的执行主体口径。
- OpenSpec config.yaml 归属 rule-config 步骤 11，pre-check 不创建，本 change 不改变该边界。

## Goals / Non-Goals

**Goals:**

- 六个工具的检查/安装/验证移交单一 bash 脚本，模型从"逐条编排"变为"一次调用 + 读 JSON 报告 + 处理剩余四项"。
- 提供可切换的镜像源配置（通用源 / 大陆镜像源），覆盖 npm、pypi、Superpowers Git 三类来源。
- 已就绪工具毫秒级版本探测后秒跳过；升级能力 opt-in（`--upgrade`），且升级版本以当前源为准。
- 脚本对 stdout 输出结构化 JSON、对 stderr 输出彩色摘要，模型解析零歧义、人可直接阅读。
- 支持 mac 与 Linux 的 POSIX 兼容 bash，无额外依赖（仅依赖工具自身与 git）。

**Non-Goals:**

- 不修改 rule-config 与 mcp-configuration（后续单独 change）。
- 脚本不实现 Superpowers 软链同步、OpenSpec 三客户端产物补齐、Playwright 安装、API Key 收集——这四项逻辑分支多、需语义判断，保留给 SKILL.md。
- 不自动修改用户 git 全局配置；国内 Git 镜像经环境变量注入。
- 不支持 Windows（无 .bat/.ps1）；不引入 Python/Node 运行时依赖（保持纯 bash）。
- 不做单工具安装子命令（保持一键，避免 SKILL.md 退化为逐条编排）。
- pi-mcp-adapter、uvx 临时包与 playwright-cli 不纳入升级范围（playwright-cli 为可选按需项，不进入脚本）。

## Decisions

### 决策 1：单一主脚本 + 可切换镜像配置，而非两个独立脚本

- **选择**：`scripts/pre-check.sh` 一份逻辑，`scripts/mirrors/default.sh` 与 `scripts/mirrors/cn.sh` 仅定义源地址环境变量，经 `--mirror <name>` 选择后 `source` 注入。
- **理由**：两个独立脚本 80% 逻辑重复，新增检查项需改两处易不一致；单一脚本 + 镜像配置实现"机制与策略分离"，逻辑只维护一份，镜像配置独立演进。
- **备选否决**：按场景切两个完全独立脚本（重复维护、易漂移）。

### 决策 2：脚本端到端执行 + JSON 报告，SKILL.md 只读报告（B2）

- **选择**：脚本一次完成六个工具的探测/安装/复验，stdout 输出 JSON（`overall`/`steps[]`/`next_actions`/`hints`），stderr 输出彩色摘要；SKILL.md 调用脚本后读 JSON，仅处理 Superpowers 软链、OpenSpec 三客户端、Playwright、API Key 四项。
- **理由**：最大化减轻模型思考；六个工具是确定性无歧义操作，适合脚本化；软链与三客户端判断需语义分支，留模型更稳妥。
- **备选否决**：脚本仅作工具函数库（install_npx/check_npx 等子命令），模型仍编排顺序与跳过（减负不彻底，SKILL.md 仍含大量分支）。

### 决策 3：镜像配置经环境变量注入，不改用户全局配置

- **选择**：`mirrors/cn.sh` 定义 `CADENCE_NPM_REGISTRY`、`CADENCE_PY_INDEX`、`CADENCE_SUPERPOWERS_GIT`；脚本在命令级注入（`npm --registry=`、uv 索引环境变量），并把 `CADENCE_SUPERPOWERS_GIT` 写入 JSON 报告的 `hints.superpowers_git`。SKILL.md 的 Superpowers 步骤从报告 `<REPORT>` 读取该地址用于 clone/pull（`$CADENCE_SUPERPOWERS_GIT` 仅是脚本子进程内部变量，不直接暴露给模型，经 JSON 传递）。不执行 `git config --global`、不写 `~/.npmrc`、不写 `~/.config/uv/uv.toml`。
- **理由**：零副作用、可随 `--mirror` 即时切换、易回滚；改全局配置污染用户环境且卸载难回滚。
- **备选否决**：脚本直接写用户全局 npm/uv/git 配置（副作用大、难回滚）；Superpowers 走 git 代理（用户已提供国内 Git 镜像，无需代理）。

### 决策 4：升级 opt-in，默认秒跳过不查远端

- **选择**：默认 `run`/`check` 仅做本地版本探测，已就绪即跳过、不查远端 latest（保持秒跳过）；携带 `--upgrade` 时才查询当前源 latest 并升级落后工具。升级范围限 npm 系工具（ast-grep/codegraph/openspec）与 uv 本体；playwright-cli 为可选按需项，不进入脚本，也不纳入升级（由 SKILL.md 在用户明确要求时处理）。
- **理由**：与"已装秒跳过、节约时间"目标一致；每次查远端 latest 会产生 6 次网络请求，拖慢重复执行；默认稳定，升级由用户显式触发。
- **备选否决**：总是对齐 latest（重复执行变慢、新版 breaking change 风险）；低于 min_version 才升级（需维护版本阈值表，且仍需查远端比对）。

### 决策 5：升级版本"镜像即权威"，不跨源比对

- **选择**：`--mirror cn --upgrade` 以 npmmirror/清华 latest 为目标版本；通用源 `--upgrade` 以 npmjs/pypi latest 为目标版本；不做跨源版本比对或告警。
- **理由**：用户明确"用镜像以镜像为准、不用镜像以主版本为准"；跨源比对增加一次额外网络请求且语义模糊（两源 latest 不同步时无法裁决）。
- **备选否决**：始终比对主仓库 latest（镜像未同步时误报"非最新"，且大陆访问主仓库慢）。

### 决策 6：JSON 走 stdout、彩色摘要走 stderr

- **选择**：结构化 JSON 唯一权威输出到 stdout（模型解析）；彩色人类摘要输出到 stderr（终端直跑可读）。`overall` 三态（success/partial/failed），`steps[].status` 固定枚举（ready/installed/upgraded/skipped/failed），`next_actions` 列出脚本不管的四项提醒 SKILL.md。
- **理由**：模型与人消费通道分离互不干扰；固定枚举消除歧义；`next_actions` 防止模型漏掉脚本未覆盖的四项。
- **备选否决**：仅彩色文本输出（模型解析脆弱、no-interrupt 判定不可靠）。

### 决策 7：mac/Linux 兼容的 POSIX bash，无额外运行时依赖

- **选择**：脚本用 `#!/usr/bin/env bash`，避免 GNU 专属语法（如 `sed -i` 差异、`grep -P`），用 `command -v` 探测、工具自身 `--version` 探测；镜像配置用 POSIX `source`。
- **理由**：mac 自带 bash 3.2 与 BSD 工具，Linux 为 GNU；保持最低公分母确保两平台一致行为。
- **备选否决**：依赖 bash 4+/GNU coreutils（mac 默认不满足，需用户装 Homebrew coreutils，违背开箱即用）。

### 决策 8：SKILL.md 命令自包含 + 绝对路径（Agent 独立 shell 约束）

- **选择**：SKILL.md 给出的每条可执行命令完全自包含——使用绝对路径，不依赖 cwd，不依赖环境变量，不依赖前一条命令状态。模型先确定并记住三个字面值后在每条命令中显式写出（且加引号容忍空格路径）：项目根 `<PROJECT_ROOT>`（openspec 产物与 `.claude/.codex/.pi` 落点）、脚本 `<PRE_CHECK_SH>`（skill 关联脚本完整绝对路径，只读、不 cd 进 skill 目录）、报告 `<REPORT>`（`mktemp` 在 `/tmp` 生成的原子唯一路径）。openspec 命令用 `cd "<PROJECT_ROOT>" && ...`，Superpowers 用 `git -C`。
- **理由**：Agent（pi/Codex）的每条命令在独立 shell 执行，cwd、环境变量、`cd` 结果均不跨命令保留；相对路径、环境变量传递、`cd` 后续命令在独立 shell 下都会失效或落到错误目录（如把 `.claude` 写进 Skill 源码目录）。唯一可靠的跨命令传递方式是让模型把字面路径写进每条命令。报告用 `mktemp` 原子唯一（`date +%s` 同秒重名）且放 `/tmp`（临时产物、不污染项目根、免入 .gitignore）。
- **备选否决**：环境变量 + `export`（独立 shell 不保留）；固定相对路径 `./.precheck-report.json`（cwd 变化错位 + 并发覆盖 + 误删）；`date +%s` 命名（同秒并发重名）；强制全程在 Skill 目录执行（openspec/`.claude` 会写进源码目录）。

## Risks / Trade-offs

- [mac bash 3.2 与 BSD 工具差异导致脚本在 mac 行为异常] → 仅用 POSIX 子集，避免关联数组、`sed -i` 原地差异、`grep -P`；在 mac 与 Linux 各验证一次六个工具全路径。
- [脚本与 SKILL.md 职责边界漂移，未来改动只改一处] → 在 SKILL.md 与脚本头部注释中明确"脚本管六工具、SKILL.md 管四项"的分工，并把 `next_actions` 作为单一权威提醒源。
- [国内 Git 镜像落后于 obra/superpowers 上游] → 这是用户自行维护的同步职责；`cn.sh` 注释说明需用户定期同步；通用源仍可用官方地址。
- [`--upgrade` 升级到镜像 latest 引入未验证新版] → 升级为 opt-in，默认不触发；报告记录 `from`/`to`/`source` 便于追溯与回滚（重装旧版）。
- [JSON 中混入工具自身 stdout 干扰解析] → 脚本内将各安装/探测命令输出重定向，仅在最终汇总处向 stdout 打印一次完整 JSON。
- [no-interrupt 下脚本失败但 SKILL.md 误报成功] → 脚本失败时 `overall=failed` 且退出码非零，SKILL.md 以退出码 + `overall` 双重判定，禁止降级为警告。

## Migration Plan

1. 新增 `scripts/pre-check.sh` 与 `scripts/mirrors/{default,cn}.sh`（纯新增，不影响现有行为）。
2. 在 mac 与 Linux 分别手动执行 `run`/`check`/`--upgrade`/两种 mirror，验证六工具全路径与 JSON 结构。
3. 改写 `SKILL.md`：六工具正文替换为脚本调用约定 + 剩余四项处理；Superpowers 步骤从报告 `<REPORT>` 的 `hints.superpowers_git` 读取镜像地址（经 JSON 传递，非直接读脚本内部变量）。
4. 更新 `init-skill-sequencing` spec 口径（执行主体由正文逐步执行改为脚本执行）。
5. 回滚策略：脚本与镜像文件为纯新增，删除即回滚；SKILL.md 经 git 还原；不产生用户环境副作用（未改全局配置）。

## Open Questions

- 无（brainstorming 已确认范围、镜像地址、升级语义、报告格式、平台范围；rule-config/mcp-configuration 的脚本化留待后续 change 评估）。
