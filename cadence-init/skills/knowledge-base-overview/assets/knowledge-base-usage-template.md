# KnowledgeBase 使用规则

## 强制要求

1. 修改代码前读取 `cadence/knowledgeBase/README.md`。
2. 按任务范围读取相关服务、API、页面、数据和开发指南文档。
3. 知识库与当前代码冲突时，以可验证的当前实现为准，并更新知识库。
4. `[合理推断]`、`[来源冲突]` 和 `[待人工确认]` 不得作为确定事实使用。
5. 修改 API、页面、DDL、配置、中间件或核心流程后，执行 `knowledge-base-update`。
6. 大型知识库按导航渐进加载，不一次读取全部子文档。

## 知识库定位

知识库是项目事实索引和代码导航，不替代源码、DDL、有效配置、测试和用户确认。

## 修改场景读取顺序

| 修改场景 | 必读文档 |
|----------|----------|
| 页面或路由 | `03-page-capabilities.md`、相关 API 文档 |
| REST 或 RPC | `02-api-capabilities.md`、基础信息和数据文档 |
| 数据模型 | `01-base-information.md`、API 和页面影响关系 |
| 配置或中间件 | `01-base-information.md`、`06-development-guide.md` |
| 跨模块流程 | `00-project-overview.md`、关系矩阵和相关领域文档 |

