# knowledge-base-context-gating Delta

## MODIFIED Requirements

### Requirement: L0 路由内核门禁

L0 受管区块模板 `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`（当前版本 v3）MUST 在路由表之后包含 `knowledge-base-context` 选择前置门禁句，语义与 description 门禁一致：仅当 `cadence/knowledge-base/manifest.yaml` 存在且 `schema_version` 为 `"4.0"` 时才可选择该 Skill，否则跳过且不输出知识库相关提示。该门禁句自 v3 起为框架模板标准内容，所有新装与经升级机制到达 v3 的项目 MUST 统一携带，MUST NOT 依赖项目手写维护。本仓库 `CLAUDE.md` 与 `AGENTS.md` 的 L0 受管块内 MUST 逐字包含同一门禁句；受管块外内容 MUST NOT 修改。

#### Scenario: 消费项目升级受管块

- **WHEN** 消费项目执行 rule-config 且其 L0 受管块与新版模板不一致（含 v2 漂移区块）
- **THEN** 按既有 L0 升级机制替换为含门禁句的 v3 受管块，块外内容保留
- **AND** 升级后的门禁句来自框架模板，与项目此前的手写门禁行无关

#### Scenario: 本仓库入口与模板一致性

- **WHEN** 比对本仓库 `CLAUDE.md`、`AGENTS.md` 的 L0 受管块与 `agent-routing-kernel.md`
- **THEN** 三处门禁句逐字一致，rule-config 不将其判为本地修改

#### Scenario: 无 KnowledgeBase 项目无副作用

- **WHEN** 不存在 `cadence/knowledge-base/manifest.yaml` 的项目携带 v3 受管块
- **THEN** 门禁句为条件性描述，不产生知识库相关提示或额外动作
