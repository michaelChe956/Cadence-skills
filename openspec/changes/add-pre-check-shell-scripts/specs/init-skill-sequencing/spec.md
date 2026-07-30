# init-skill-sequencing Delta Specification

## ADDED Requirements

### Requirement: 六工具检查由脚本执行

pre-check 对 npx、uvx、ast-grep、codegraph、openspec、pi-mcp-adapter 六个基础工具的就绪探测、缺失安装与安装后复验 MUST 由 `scripts/pre-check.sh` 执行；SKILL.md MUST 调用脚本并读取其 JSON 报告，MUST NOT 在正文中逐条罗列六工具的安装与验证命令。OpenSpec 三客户端指令产物的检测与补齐 MUST 仍由 SKILL.md 依据本 spec 既有 Requirements 执行，脚本 MUST NOT 接管。

#### Scenario: SKILL.md 调用脚本处理六工具

- **WHEN** 执行 `/pre-check`
- **THEN** SKILL.md 以完整绝对路径 `<PRE_CHECK_SH>` 调用脚本完成六工具检查与安装，读取 JSON 报告判定六工具状态，正文不含六工具的逐条安装命令，也不以相对路径 `scripts/pre-check.sh` 调用

#### Scenario: OpenSpec 三客户端仍由 SKILL.md 处理

- **WHEN** 脚本执行完成后 SKILL.md 处理 OpenSpec 检查
- **THEN** SKILL.md 按 claude/codex/pi 客户端产物存在性检测并补齐，脚本不执行 `openspec init`/`openspec update` 的客户端产物判断

### Requirement: 脚本报告驱动 SKILL.md 后续动作

脚本 JSON 报告的 `overall` 与 `steps[].status` MUST 作为 SKILL.md 判定六工具门槛的权威依据；`next_actions` MUST 提示 SKILL.md 继续处理 Superpowers 软链、OpenSpec 三客户端产物、Playwright（可选）与 API Key 占位提醒。脚本以非零退出码终止、`overall` 为 partial 或 failed、或任一 `steps[].status=failed` 时，no-interrupt 模式 MUST 立即终止 `/pre-check`，普通模式 MUST 报告失败且 MUST NOT 继续后续步骤，均 MUST NOT 降级为警告或继续；仅 `overall=success` 时据 `next_actions` 继续处理 Superpowers 软链、OpenSpec 三客户端、Playwright（可选）与 API Key 占位提醒。

#### Scenario: success 时依据报告继续

- **WHEN** 脚本返回 `overall` 为 success
- **THEN** SKILL.md 依据各 `steps[].status` 判定六工具门槛通过，并据 `next_actions` 继续处理剩余项

#### Scenario: partial 按失败处理

- **WHEN** 脚本返回 `overall` 为 partial
- **THEN** no-interrupt 模式立即终止 `/pre-check` 并报告失败，普通模式报告失败且不继续后续步骤、不宣称初始化成功

#### Scenario: 脚本失败触发失败关闭

- **WHEN** 脚本以非零退出码终止或报告 `overall` 为 failed
- **THEN** no-interrupt 模式立即终止 `/pre-check` 并报告失败，普通模式报告失败，不宣称初始化成功

### Requirement: SKILL.md 命令自包含与绝对路径

Agent 的每条命令在独立 shell 中执行，cwd、环境变量、上一条命令的状态 MUST NOT 被假设为跨命令保留。SKILL.md 给出的每条可执行命令 MUST 完全自包含：使用绝对路径，不依赖 cwd，不依赖环境变量，不依赖前一条命令的任何状态。

SKILL.md MUST 引导模型先确定并记住两个字面绝对路径后在每条命令中显式写出：项目根 `<PROJECT_ROOT>`（待初始化项目的绝对路径，openspec 产物与 `.claude/.codex/.pi` 落在其中）与脚本路径 `<PRE_CHECK_SH>`（pre-check skill 关联脚本的完整绝对路径，脚本只读、不得 `cd` 进 skill 目录执行）。路径字面值在命令中 MUST 加引号，以容忍含空格的路径。

报告是临时中间产物，MUST 用 `mktemp` 生成原子唯一的绝对路径（如 `mktemp -t precheck-report.XXXXXX.json`，落在 `/tmp`），模型记住该字面值后在每条命令中显式写出；MUST NOT 用 `date +%s`（同秒并发重名）或 `pwd` 推导（独立 shell cwd 可变）。无论成功或失败，完成后 MUST 删除该次调用的独占报告文件。

#### Scenario: 命令不依赖独立 shell 的 cwd

- **WHEN** 模型在任意 cwd 下按 SKILL.md 逐条执行命令
- **THEN** openspec init/update 与 `.claude/.codex/.pi` 检查作用于 `<PROJECT_ROOT>`，报告读写作用于 `<REPORT>`（`/tmp` 下 mktemp 路径），均不写入 Skill 源码目录，也不因 cwd 变化而落到错误目录

#### Scenario: 报告路径独占且用完清理

- **WHEN** 同一环境先后或并发执行多次 `/pre-check`
- **THEN** 每次调用用 `mktemp` 生成唯一报告路径，互不覆盖、互不误删；每次调用结束后删除自己的报告文件

#### Scenario: 不 cd 进 skill 目录

- **WHEN** SKILL.md 指导模型调用脚本
- **THEN** 模型以完整绝对路径 `<PRE_CHECK_SH>` 调用脚本，不 `cd` 进 skill 目录，skill 目录不被写入任何产物
