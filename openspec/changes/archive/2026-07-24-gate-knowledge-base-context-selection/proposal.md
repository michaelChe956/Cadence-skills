# Proposal: gate-knowledge-base-context-selection

## Why

`knowledge-base-context` Skill 的自动触发完全由 frontmatter `description` 决定，而当前仓库源头的 description 没有任何选择前置条件。在未启用 KnowledgeBase 的项目中，Agent 进行需求澄清、设计、编码、调试等普通任务时可能误选该 Skill，随后因 Manifest 缺失被 Skill 内部校验阻断，把"项目根本没有启用知识库"的普通任务错误地升级为知识库异常。需要把门禁写成"选择 Skill 前的门禁"，而不是 Skill 内部规则，同时不能影响已启用 KnowledgeBase 的使用者。

## What Changes

- 在仓库源头 `cadence-init/skills/knowledge-base-context/SKILL.md` 的 frontmatter `description` 末尾追加选择前置门禁：仅当 `cadence/knowledge-base/manifest.yaml` 存在且 `schema_version` 为 `"4.0"` 时才可选择本 Skill；否则不得选择、调用或读取，按普通流程继续，不输出知识库相关提示，不引导 `knowledge-base-bootstrap`。
- 在 L0 受管区块模板 `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md` 的路由表之后追加同语义的路由层门禁短句，随 rule-config 分发到所有消费项目的 CLAUDE.md/AGENTS.md。
- 将门禁句逐字同步进本仓库 `CLAUDE.md` 与 `AGENTS.md` 的 L0 受管块内，保持模板与产物一致。
- 新建本仓库项目规则 `cadence/project-rules/knowledge-base-gating.md` 作为文档化兜底，并在 `cadence/project-rules/README.md` 文件说明中登记。
- 不修改 `knowledge-base-context` Skill 正文与异常处理表；正文"Manifest 缺失则停止并引导 bootstrap"保留为显式手动调用时的异常处理。

## Capabilities

### New Capabilities

- `knowledge-base-context-gating`: `knowledge-base-context` Skill 的选择前置门禁，覆盖 description 层、L0 路由层与项目规则文档层三处门禁载体及其一致性要求。

### Modified Capabilities

（无）

## Impact

- 受影响文件：
  - `cadence-init/skills/knowledge-base-context/SKILL.md`（仅 frontmatter description）
  - `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`
  - 本仓库 `CLAUDE.md`、`AGENTS.md`（仅 L0 受管块内）
  - `cadence/project-rules/knowledge-base-gating.md`（新建）
  - `cadence/project-rules/README.md`（登记）
- 对使用者的影响：
  - 未启用 KnowledgeBase 的项目：Agent 在选择 Skill 时即可看到门禁，不再误选；零额外成本。
  - 已启用 KnowledgeBase 的项目：Manifest 存在且为 Schema 4.0 时照常触发，行为不变。
- 分发路径：description 随 Skill 安装生效；L0 门禁随消费项目下次执行 rule-config 升级受管块生效。
- 非目标：不修改 Skill 正文的渐进读取流程、异常处理表与输出契约；不在消费项目的 `cadence/project-rules/` 强制创建用户规则文件。
