# knowledge-base-context-gating Specification

## Purpose

定义 `knowledge-base-context` Skill 的选择前置门禁，避免未启用 KnowledgeBase 的项目误选该 Skill，同时保持 Schema 4.0 KnowledgeBase 项目的正常上下文流程。

## Requirements

### Requirement: Skill description 选择前置门禁

仓库源头 `cadence-init/skills/knowledge-base-context/SKILL.md` 的 frontmatter `description` MUST 包含选择前置门禁：仅当 `cadence/knowledge-base/manifest.yaml` 存在且 `schema_version` 为 `"4.0"` 时才可选择本 Skill；Manifest 缺失或 Schema 非 4.0 时 MUST NOT 选择、调用或读取本 Skill，MUST 按普通流程继续，MUST NOT 输出知识库相关提示，MUST NOT 引导 `knowledge-base-bootstrap`。门禁句 MUST 追加在 description 末尾，原有触发描述 MUST 保持不变；Skill 正文与异常处理表 MUST NOT 修改。

#### Scenario: 无 Manifest 项目的普通任务

- **WHEN** Agent 在不存在 `cadence/knowledge-base/manifest.yaml` 的项目中执行需求澄清、设计、编码、测试、审查或调试任务
- **THEN** Agent 依据 description 门禁不选择 `knowledge-base-context`，按普通流程继续，不输出知识库相关提示

#### Scenario: Manifest 为 Schema 4.0 的项目

- **WHEN** Agent 在 `cadence/knowledge-base/manifest.yaml` 存在且 `schema_version` 为 `"4.0"` 的项目中执行上述任务
- **THEN** Agent 照常选择并调用 `knowledge-base-context`，行为与门禁引入前一致

#### Scenario: Skill 被显式手动调用但 Manifest 缺失

- **WHEN** 用户显式手动调用 `knowledge-base-context` 且 Manifest 缺失或 Schema 非 4.0
- **THEN** Skill 正文的"Schema 4.0 前置校验"作为异常处理生效，报告缺失路径或版本

### Requirement: L0 路由内核门禁

L0 受管区块模板 `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md` MUST 在路由表之后包含 `knowledge-base-context` 选择前置门禁句，语义与 description 门禁一致。本仓库 `CLAUDE.md` 与 `AGENTS.md` 的 L0 受管块内 MUST 逐字包含同一门禁句；受管块版本标记 MUST NOT 变更；受管块外的入口文件内容 MUST NOT 修改。

#### Scenario: 消费项目升级受管块

- **WHEN** 消费项目执行 rule-config 且其 L0 受管块与新版模板不一致
- **THEN** 按既有 L0 升级机制替换为含门禁句的新版受管块，块外内容保留

#### Scenario: 本仓库入口与模板一致性

- **WHEN** 比对本仓库 `CLAUDE.md`、`AGENTS.md` 的 L0 受管块与 `agent-routing-kernel.md`
- **THEN** 三处门禁句逐字一致，rule-config 不将其判为本地修改

### Requirement: 项目规则文档化兜底

本仓库 MUST 存在 `cadence/project-rules/knowledge-base-gating.md`，内容 MUST 包含：选择前置门禁的判定条件与禁止行为；"Manifest 缺失则停止"属于已确认需要知识库或显式调用时的异常处理、不得用于阻断普通任务的解读。`cadence/project-rules/README.md` 的文件说明 MUST 登记该规则文件。框架 MUST NOT 在消费项目的 `cadence/project-rules/` 强制创建该文件。

#### Scenario: Agent 读取项目规则

- **WHEN** Agent 在本仓库读取 `cadence/project-rules/README.md`
- **THEN** 能发现 `knowledge-base-gating.md` 并理解门禁意图及异常处理的正确解读
