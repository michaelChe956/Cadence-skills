# pre-check-shell-execution Specification

## ADDED Requirements

### Requirement: 单一主脚本承接六工具检查与安装

pre-check MUST 提供单一主脚本 `scripts/pre-check.sh`（mac/Linux 兼容 bash），承接 npx、uvx、ast-grep、codegraph、openspec、pi-mcp-adapter 六个工具的就绪探测、缺失安装与安装后复验。SKILL.md MUST NOT 再在正文中逐条罗列这六个工具的安装与验证命令，MUST 改为调用脚本并读取其报告。其中 npx 随 Node.js 运行时提供，脚本 MUST NOT 自动安装 Node.js；npx 缺失时标记为外部前置条件未满足并按失败处理，不尝试安装。

#### Scenario: 脚本存在且承接六工具

- **WHEN** 查看 `cadence-init/skills/pre-check/scripts/pre-check.sh` 与对应 SKILL.md
- **THEN** 脚本包含六个工具的探测、安装、复验逻辑；SKILL.md 不含六工具的逐条安装命令，仅含脚本调用约定

#### Scenario: 脚本处理范围边界

- **WHEN** 执行脚本
- **THEN** 脚本仅处理六个工具，不执行 Superpowers 软链同步、OpenSpec 三客户端产物补齐、Playwright 安装或 API Key 收集

### Requirement: run 与 check 子命令语义

脚本 MUST 提供 `run` 与 `check` 两个子命令。`run` MUST 对缺失工具执行安装并复验；`check` MUST 仅探测就绪状态而不执行任何安装。两个子命令 MUST 支持 `--mirror <name>` 与 `--no-interrupt` 参数；`--no-interrupt` MUST 沿用失败关闭语义：任一基础工具失败即以非零退出码终止。npx 为例外：脚本 MUST NOT 安装 Node.js，npx 缺失时 run 模式标记 install-unavailable 并判定失败。

#### Scenario: check 不安装

- **WHEN** 在缺少 ast-grep 的环境执行 `pre-check.sh check`
- **THEN** 脚本探测 ast-grep 未就绪并在报告中标记，但不执行安装命令，环境状态不变

#### Scenario: run 安装缺失工具

- **WHEN** 在缺少 ast-grep 的环境执行 `pre-check.sh run`
- **THEN** 脚本安装 ast-grep，安装后复验成功，报告中标记为已安装

#### Scenario: npx 缺失不自动安装

- **WHEN** 在缺少 npx（未安装 Node.js）的环境执行 `pre-check.sh run`
- **THEN** 脚本不尝试安装 Node.js 或 npx，将 npx 标记为 failed（action=install-unavailable），报告提示需用户自行安装 Node.js，并按失败处理

#### Scenario: no-interrupt 失败关闭

- **WHEN** 执行 `pre-check.sh run --no-interrupt` 且某基础工具安装失败
- **THEN** 脚本以非零退出码终止，报告 `overall` 为 failed，不宣称成功

### Requirement: 已就绪工具秒跳过

脚本对每个工具 MUST 先执行本地版本探测（如 `<tool> --version`）；探测成功时 MUST 将该工具标记为就绪并跳过安装，MUST NOT 查询远端版本，MUST NOT 执行安装命令。本地版本探测 MUST 为毫秒级，不产生网络请求。

#### Scenario: 已安装工具快速跳过

- **WHEN** 六个工具均已安装时执行 `pre-check.sh run`
- **THEN** 每个工具仅执行一次本地版本探测即标记就绪，不触发任何远端版本查询或安装命令

#### Scenario: 安装后强制复验

- **WHEN** 脚本安装了某工具
- **THEN** 脚本在安装后再次执行版本探测，仅当复验成功才标记该工具为已安装，否则标记失败

### Requirement: 升级 opt-in 且以当前源为准

脚本 MUST 仅在显式携带 `--upgrade` 参数时查询当前源的 latest 版本并升级落后工具；未携带 `--upgrade` 时 MUST NOT 查询远端 latest。升级目标版本 MUST 以当前生效源为准：`--mirror cn` 时以 npmmirror/清华镜像 latest 为准，通用源时以 npmjs/pypi latest 为准；脚本 MUST NOT 跨源比对版本。升级范围 MUST 限定为 npm 系工具（ast-grep/codegraph/openspec）与 uv 本体；pi-mcp-adapter、uvx 临时包与 playwright-cli MUST NOT 纳入升级。

#### Scenario: 默认不升级

- **WHEN** 某工具已安装但非最新版本时执行 `pre-check.sh run`（不带 `--upgrade`）
- **THEN** 脚本不查询远端 latest，不执行升级，该工具标记为就绪

#### Scenario: cn 镜像升级以镜像为准

- **WHEN** 执行 `pre-check.sh run --mirror cn --upgrade` 且 ast-grep 落后于 npmmirror latest
- **THEN** 脚本将 ast-grep 升级至 npmmirror latest，报告记录升级前后版本与来源

#### Scenario: 通用源升级以主仓库为准

- **WHEN** 执行 `pre-check.sh run --upgrade`（默认 mirror）且 codegraph 落后于 npmjs latest
- **THEN** 脚本将 codegraph 升级至 npmjs latest

#### Scenario: pi-mcp-adapter 不升级

- **WHEN** 执行 `pre-check.sh run --upgrade` 且 pi-mcp-adapter 已安装
- **THEN** 脚本不升级 pi-mcp-adapter，保持现状

### Requirement: JSON 报告结构权威且走 stdout

脚本 MUST 向 stdout 输出一份结构化 JSON 报告作为机器消费的权威输出，MUST 向 stderr 输出人类可读彩色摘要。JSON MUST 包含：`overall`（success/partial/failed 三态）、`steps[]`（每项含 `name`、`status`、`action`、`version`、`error`）、`next_actions`（脚本不处理、需 SKILL.md 接手的项）、`hints`（含 superpowers_git）。`steps[].status` MUST 使用固定枚举 ready/installed/upgraded/skipped/failed。脚本 MUST 将各安装与探测命令的输出重定向，确保 stdout 仅含一份完整 JSON。

#### Scenario: stdout 仅含一份 JSON

- **WHEN** 执行 `pre-check.sh run` 并仅捕获 stdout
- **THEN** stdout 内容为单份可解析 JSON，不混入 npm/uvx 等工具的安装日志

#### Scenario: 报告状态枚举

- **WHEN** 读取任一 `steps[]` 项
- **THEN** `status` 值为 ready/installed/upgraded/skipped/failed 之一，`action` 区分 already-installed、installed-via-<pm>、upgraded、conditional-skip、install-attempted 等

#### Scenario: next_actions 提醒剩余四项

- **WHEN** 脚本执行完成
- **THEN** JSON 的 `next_actions` 列出 Superpowers 软链、OpenSpec 三客户端产物、Playwright（可选）、API Key 占位提醒，提示 SKILL.md 继续处理

### Requirement: mac 与 Linux 兼容

脚本 MUST 使用 `#!/usr/bin/env bash` 与 POSIX 兼容语法，避免依赖 GNU 专属特性；MUST 在 mac（bash 3.2 + BSD 工具）与 Linux（GNU 工具）上行为一致；MUST NOT 引入 Python/Node 运行时依赖。

#### Scenario: mac 与 Linux 行为一致

- **WHEN** 分别在 mac 与 Linux 执行 `pre-check.sh run`
- **THEN** 两平台对六个工具的探测、跳过、安装、报告行为一致，不出现平台专属错误
