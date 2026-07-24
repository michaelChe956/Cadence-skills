# Design: gate-knowledge-base-context-selection

## Context

`knowledge-base-context` 的自动触发只由 frontmatter `description` 决定。当前仓库源头的 description 无选择前置条件，导致未启用 KnowledgeBase 的项目中 Agent 可能误选该 Skill，再被 Skill 内部"Schema 4.0 前置校验"阻断并引导 `knowledge-base-bootstrap`，把普通任务错误升级为知识库异常。

已确认的三项摸底事实：

1. 本仓库 `CLAUDE.md`/`AGENTS.md` 的路由段是 cadence-managed L0 受管块，由 `rule-config` 从模板 `agent-routing-kernel.md` 生成；直接改入口文件会被视为"无法识别的本地修改"，下次 rule-config 执行时被询问或替换。
2. 用户机器上已安装的 Skill 副本 description 已带门禁措辞，但仓库源头没有，两边不一致，重新安装会丢失门禁。
3. description 是 Agent 选择 Skill 时唯一必看的内容；路由表与项目规则都在更晚阶段才读取。

约束：不能影响已启用 KnowledgeBase 的使用者（Manifest 存在且为 Schema 4.0 时行为不变）；不能给未启用 KnowledgeBase 的使用者增加任何提示或成本。

## Goals / Non-Goals

**Goals:**

- 门禁写在"选择 Skill 之前"：Agent 在浏览 Skill 清单和读取入口文件时即可看到门禁。
- 三处门禁载体语义一致、逐字同步：Skill description、L0 路由内核模板、本仓库入口文件受管块。
- 项目规则文件作为文档化兜底，说明门禁意图与"Manifest 缺失则停止"的正确解读。

**Non-Goals:**

- 不修改 `knowledge-base-context` Skill 正文、渐进读取流程、异常处理表与输出契约。
- 不在消费项目的 `cadence/project-rules/` 强制创建用户规则文件。
- 不改变 rule-config 的 L0 受管块版本号与升级机制。

## Decisions

### 决策 1：门禁载体选择"选择前"位置，而非 Skill 内部规则

- 主门禁放在 frontmatter `description`：这是 Skill 发现阶段 Agent 唯一必读的字段，是真正的"选择前门禁"。
- 二次防线放在 L0 路由内核模板：会话开始读取入口文件时生效，随 rule-config 分发到所有消费项目。
- 项目规则文件只作文档化兜底：项目规则在 Skill 之后才读取，无法阻止误选，只承载意图说明与异常处理的正确解读。
- 备选方案（仅项目规则文件、仅 description）均因生效时机过晚或缺少二次防线被放弃。

### 决策 2：门禁判定条件

- 只读检查 `cadence/knowledge-base/manifest.yaml`：文件存在且 `schema_version` 为 `"4.0"` 才可选择。
- Manifest 缺失或版本不符时：不得选择、调用或读取该 Skill；不输出知识库相关提示；不引导 `knowledge-base-bootstrap`；按普通流程继续。
- "不引导 bootstrap"的理由：项目未启用知识库是正常状态而非异常，不应把普通任务引导到知识库初始化。

### 决策 3：Skill 正文不改，异常处理保留

- 正文"Manifest 缺失则停止并引导 `knowledge-base-bootstrap`"重新解读为：已确认需要知识库、或用户显式手动调用时，发现知识库损坏或丢失的异常处理；不用于"项目根本没有启用知识库"的普通任务。
- 备选方案（删除正文中的 bootstrap 引导）会增加知识库使用者的行为变化风险，且显式调用场景下引导 bootstrap 是合理的，故保留。

### 决策 4：模板与本仓库入口文件逐字一致

- 内核模板、`CLAUDE.md`、`AGENTS.md` 三处的门禁句逐字相同，避免 rule-config 的内容比对把本仓库入口判为本地修改。
- 不重跑整个 rule-config，只同步受管块内文本，避免无关变更。

### 决策 5：门禁措辞复用已安装副本的表述

- description 采用用户机器上已安装副本已有的门禁措辞，保持安装产物与仓库源头一致。

## Risks / Trade-offs

- [description 变长，可能稀释原触发语义] → 门禁句追加在末尾，保留原有"MUST use when…"触发描述不变。
- [消费项目不重新执行 rule-config 时拿不到 L0 门禁] → description 主门禁随 Skill 安装即生效，L0 只是二次防线，可接受渐进分发。
- [门禁依赖 Agent 自觉遵守，无硬强制] → 三层载体（description、L0、项目规则）叠加提高遵守概率；这与本框架其他规则一致，均为约定式强制。
- [Manifest 路径或 Schema 版本未来变化] → 门禁句中路径与版本为字面量；若 Schema 升级需同步修订门禁，已在本 change 的 spec 中固化为验收场景。

## Migration Plan

无需迁移。知识库使用者在 Manifest 存在且为 Schema 4.0 时行为完全不变；未启用知识库的项目只是不再误选 Skill。

## Open Questions

无。
