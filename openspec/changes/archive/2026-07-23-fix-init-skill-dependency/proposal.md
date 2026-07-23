# Proposal: fix-init-skill-dependency

## Why

全新项目按 README 约定顺序执行 `/pre-check` → `/rule-config` 初始化时必然失败：pre-check 步骤 5 将 `openspec/config.yaml` 列为 OpenSpec 检查的硬性完成门槛，但其调用的 `openspec init --tools ...`（非交互且无 `--force`）在 OpenSpec CLI ≥1.4.1 下刻意跳过 config.yaml 创建（源码行为：`Config: skipped (non-interactive mode)`）；全仓库唯一创建该文件的步骤是 rule-config 步骤 11，而 rule-config 又依赖 pre-check 安装的 openspec/codegraph CLI。两个 Skill 构成双向依赖环，文档约定顺序在第一步卡死，no-interrupt 模式立即终止，且 pre-check 重跑无法自愈。本 change 来自已经用户确认的 brainstorming 设计结论。

## What Changes

- 调整 pre-check 的 OpenSpec 完成门槛：移除 `openspec/config.yaml` 断言，完成条件改为"OpenSpec CLI + 三客户端指令产物验证成功"；config.yaml 缺失降级为提示信息（指向 rule-config 步骤 11 创建），两种参数模式均不因此失败。
- pre-check 步骤 5 增量分支的判断条件从"`openspec/config.yaml` 是否存在"改为"按 claude/codex/pi 三客户端逐一检测指令产物存在性"，缺失哪个客户端就对哪个执行 `openspec init --tools <缺失客户端>`，再执行 `openspec update`；config.yaml 不再作为分支判断条件。
- README 同步两个 Skill 的职责边界与 OpenSpec 检查口径：pre-check 管 CLI 与指令产物，rule-config 管 `openspec/config.yaml` 的创建与合并。
- 非目标：不修改 rule-config 的行为逻辑；pre-check 不创建 config.yaml（避免双写职责与空壳配置）；不对 `openspec init` 使用 `--force`（覆盖语义风险未验证）。

## Capabilities

### New Capabilities

- `init-skill-sequencing`: pre-check 与 rule-config 在项目初始化中的职责边界——OpenSpec 检查验收口径、三客户端指令产物的增量补齐行为，以及 config.yaml 的归属与缺失提示语义。

### Modified Capabilities

（无：现有 specs 不覆盖初始化 Skill 的验收口径与顺序行为。）

## Impact

- 受影响文档：`cadence-init/skills/pre-check/SKILL.md`（完成门槛、快速参考、验证命令、增量要求、行为说明）、`README.md`（Skill 说明行、no-interrupt 行为表、初始化顺序说明段）。
- 受影响行为：`/pre-check` 的 OpenSpec 检查判定语义；全新项目与"rule-config 先行"项目状态下初始化流程的可用性。
- 不受影响：rule-config 行为与模板、mcp-configuration、OpenSpec CLI 本身、其他五个基础检查项的门槛地位。
