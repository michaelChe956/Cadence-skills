# KnowledgeBase Skill 选择门禁

在选择 `knowledge-base-context` 前，先只读检查
`cadence/knowledge-base/manifest.yaml`：

- 文件不存在，或 `schema_version` 不等于 `"4.0"`：不得选择、调用或读取
  `knowledge-base-context` Skill；按普通代码阅读、调试或实现流程继续。
- 文件存在且 `schema_version: "4.0"`：任务涉及需求澄清、设计、计划、编码、测试、
  审查或调试时，必须调用 `knowledge-base-context` Skill。
- 不得因为 Manifest 缺失而调用该 Skill 后再以"缺少 Schema"为由阻断普通仓库任务。

## 异常处理的正确解读

`knowledge-base-context` Skill 正文的"Manifest 缺失则停止"仅适用于：已确认
需要知识库、或用户显式手动调用该 Skill 时，发现知识库损坏或丢失的异常处理；
不得用于"项目根本没有启用知识库"的普通任务。
