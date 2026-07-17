# KnowledgeBase 使用规则

## 强制要求

1. 进行需求澄清、Design、Plan、Coding、Testing、Review 或 Debug 时，先使用 `knowledge-base-context` 获取最小任务上下文。
2. 修改代码前读取 `cadence/knowledge-base/README.md`。
3. 只接受 Schema 4.0；先确认 `manifest.yaml` 为 Schema 4.0，再按任务范围渐进读取相关一级入口和子文档。
4. 表相关任务必须读取 `cadence/knowledge-base/data-models/README.md`、字段级表文档和 `cadence/knowledge-base/evidence/` 中的当前结构证据。
5. 配置相关任务必须读取 `cadence/knowledge-base/configurations/README.md`、服务配置文档和 `cadence/knowledge-base/evidence/` 中的当前快照证据。
6. KnowledgeBase 与当前源码、DDL、有效配置和当前证据同等重要；冲突时同时保留双方证据，以可验证实现描述当前行为，不静默覆盖业务语义。
7. `[合理推断]`、`[来源冲突]` 和 `[待人工确认]` 不得作为确定事实使用。
8. 修改字段、SQL/Mapper、配置、Profile/Feature Flag、API 参数、页面字段、中间件或核心流程后，必须准备包含变更范围、实现证据、验证结果和文档目标的完整变更包，并由 `knowledge-base-update` 消费后执行 Update。
9. 大型知识库按导航渐进加载，不一次读取全部子文档或全仓源码。

## 知识库定位

知识库是项目事实索引和代码导航，不替代源码、DDL、有效配置、测试和用户确认。

## 一级导航

- `base-information.md`
- `development-guide.md`
- `interfaces/README.md`
- `pages/README.md`
- `services/`
- `data-models/README.md`
- `configurations/README.md`
- `evidence/`
- `change-history.md`
- `open-questions.md`

先从入口摘要选择与当前任务相关的文档，再渐进读取子文档；不要把字段清单或全部配置键复制到入口。

## 调用方式

- 自然语言任务由代理根据 `knowledge-base-context` 的 Skill Description 自动选择。
- Claude Code 插件手动调用：`/cadence-init:knowledge-base-context`。
- Codex 在 Skill 已安装或被项目发现后手动调用：`$knowledge-base-context`。
- Manifest 只提供 Schema、范围和基线，不参与 Skill 触发。
- 上下文准备完成后继续用户原始任务，不因该 Skill 自动命中而停止 Design、Plan、Coding、Testing、Review 或 Debug。

## 修改场景读取顺序

| 修改场景 | 必读文档 |
|----------|----------|
| 字段变更 | `data-models/README.md`、字段级表文档、当前结构证据、相关 API 和页面文档 |
| SQL/Mapper 变更 | 字段级表文档、SQL/Mapper 当前证据、服务调用关系和验证指南 |
| 配置键变更 | `configurations/README.md`、服务配置文档、当前快照证据和验证指南 |
| Profile/Feature Flag | 服务配置文档、环境差异、当前快照证据和启用条件 |
| API 参数变更 | `interfaces/README.md`、对应接口主文件、调用方、服务和数据模型文档 |
| 页面字段变更 | `pages/README.md`、页面主文档、API 参数和字段映射文档 |
| 中间件配置变化 | `configurations/README.md`、服务配置文档、中间件当前证据和依赖服务文档 |
| 跨模块流程 | `README.md`、相关服务、接口、页面、表、配置和证据文档 |

## Update 变更包

完整变更包至少包含：

- 变更范围和受影响的稳定 ID
- 当前实现、DDL、SQL/Mapper 或配置快照证据
- 已执行的验证及其结果
- 需要更新的 KnowledgeBase 文档
- 尚未确认的冲突或风险

没有完整变更包时不得把 Update 标记为完成。
