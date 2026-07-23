# Design: fix-init-skill-dependency

## Context

`pre-check` 与 `rule-config` 是 cadence-init 插件的前两个初始化 Skill，README 约定执行顺序为 `/pre-check` → `/rule-config` → `/mcp-configuration`。根因调查（systematic-debugging）已确认：

- pre-check 步骤 5 的完成门槛包含 `openspec/config.yaml`，但其唯一创建手段 `openspec init --tools ...` 在 OpenSpec CLI ≥1.4.1 下必然跳过 config 创建（传入 `--tools` 即非交互，`canPromptInteractively()` 恒为 false；无 `--force` 时 `createConfig()` 返回 `'skipped'`）。
- `openspec/config.yaml` 的内容权威在 rule-config 步骤 11（含 Cadence 协作上下文，本仓库实际文件与其模板逐字一致）。
- rule-config 步骤 9/11 依赖 pre-check 安装的 codegraph/openspec CLI。
- 二者构成双向依赖环；且 pre-check 增量分支以"config.yaml 是否存在"为判断条件，缺失"config.yaml 存在但 claude/codex 产物缺失"分支，导致"rule-config 先行"也无法解套。

本设计来自已经用户确认的 brainstorming 结论（范围 C：验收口径调整 + 增量分支补齐 + README 同步）。

## Goals / Non-Goals

**Goals:**

- 斩断反向依赖边：pre-check 的 OpenSpec 验收不再依赖 rule-config 的产物（config.yaml），依赖图从环变为单向（rule-config → pre-check 工具层）。
- pre-check 增量分支按 claude/codex/pi 客户端产物存在性精确补齐，覆盖"rule-config 先行"与部分缺失中间态。
- README 与 pre-check SKILL.md 口径一致，职责边界落到文档。

**Non-Goals:**

- 不修改 rule-config 的行为逻辑（其 config.yaml 创建/合并流程本身正确）。
- pre-check 不创建 config.yaml（避免双写职责与无 Cadence 上下文的空壳配置）。
- 不对 `openspec init` 使用 `--force`（覆盖语义未验证，风险不可控）。
- 不编写任何代码或脚本；本 change 仅修改 Skill 行为定义文档与 README。

## Decisions

### 决策 1：config.yaml 移出 pre-check 完成门槛，缺失时仅提示

- **选择**：完成条件改为"OpenSpec CLI + 三客户端指令产物验证成功"；config.yaml 缺失输出提示"将由 rule-config 步骤 11 创建"，两种参数模式均不失败。
- **理由**：config.yaml 的内容权威在 rule-config（含 Cadence 协作上下文）；pre-check 创建的任何版本都是待合并空壳，反而增加合并分支与误导。
- **备选否决**：pre-check 自建最小 config.yaml（双写职责，rule-config 合并路径多一个分支）；init 加 `--force`（对已有产物的覆盖语义未验证，且仍生成无 Cadence 上下文的空配置）。

### 决策 2：增量分支按客户端产物存在性检测，仅 init 缺失客户端

- **选择**：分别检测 claude（`.claude/commands/opsx/` 或 `.claude/skills/openspec-*`）、codex（`.codex/skills/openspec-*`）、pi（`.pi/skills/openspec-*` 与 `.pi/prompts/opsx-*`）产物，缺失哪个就对哪个执行 `openspec init --tools <缺失客户端列表>`，再 `openspec update`；config.yaml 存在性不再作为分支条件。
- **理由**：与 pre-check 全文"已就绪跳过、不覆盖用户改动"的增量原则一致；`openspec update` 只刷新已初始化工具，不会补缺失客户端，必须由 init 完成。
- **备选否决**：任一缺失就 init 三客户端全量（会重新生成已存在客户端的产物，有覆盖用户本地改动的风险）。

### 决策 3：保留正向依赖（rule-config → pre-check 工具层）

- **选择**：rule-config 步骤 9/11 对 codegraph/openspec CLI 的依赖保持不变，README 顺序约定不变（pre-check 先、rule-config 后）。
- **理由**：工具安装职责天然归 pre-check；斩断反向边后该单向依赖自然成立，顺序颠倒时 pre-check 也能靠决策 2 补齐产物。

### 决策 4：依赖 CLI 的 extend 语义保护 rule-config 已写入的 config.yaml

- **选择**：决策 2 中 `openspec init --tools ...` 在 config.yaml 已存在时原样保留（CLI 源码 `createConfig()` 返回 `'exists'`，已核实）。
- **理由**：这是"rule-config 先行"场景安全补齐产物的前提，无需额外保护逻辑。

## Risks / Trade-offs

- [用户只跑 pre-check、长期不跑 rule-config，项目无 config.yaml] → OpenSpec 使用默认 schema（`spec-driven`，与框架要求一致）；pre-check 输出提示指向 rule-config；README 明确顺序约定。
- [未来 OpenSpec CLI 改变非交互行为（如默认创建 config.yaml）] → 不产生冲突：rule-config 对已存在 config.yaml 走保守合并路径（该能力已存在并经测试覆盖）。
- [产物检测与 CLI 产物布局耦合（`.claude/commands/opsx/` vs `.claude/skills/openspec-*`）] → 沿用 pre-check 现有验证命令的判定口径，不引入新的布局假设；CLI 布局变化时验证与检测同步失效，问题可见而非静默。
- [文档行为定义与实际执行偏差] →  specs 为每个改动点定义 WHEN/THEN 验收场景，实施后逐条对照文档原文核验，并推荐在测试项目实证一次完整初始化流程。

## Migration Plan

无需迁移。已完成初始化的老项目重跑 `/pre-check` 行为不变（产物齐全时仅执行 `openspec update`）；曾卡在 OpenSpec 检查的项目重跑即可通过。
