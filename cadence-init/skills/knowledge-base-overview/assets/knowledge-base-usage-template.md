# KnowledgeBase 使用规则

## 强制要求

1. 进行需求澄清、Design、Plan、Coding、Testing、Review 或 Debug 时，先使用 `knowledge-base-context` 获取最小任务上下文。
2. 修改代码前读取 `cadence/knowledge-base/README.md`。
3. 只接受 Schema 4.0；先确认 `manifest.yaml` 为 Schema 4.0，再按任务范围渐进读取相关一级入口和子文档。
4. 表相关任务必须读取 `cadence/knowledge-base/data-models/README.md`、字段级表文档和 `cadence/knowledge-base/evidence/` 中的当前结构证据。
5. 配置相关任务必须读取 `cadence/knowledge-base/configurations/README.md`、服务配置文档和 `cadence/knowledge-base/evidence/` 中的当前快照证据。
6. KnowledgeBase 与当前源码、DDL、有效配置和当前证据同等重要；冲突时同时保留双方证据，以可验证实现描述当前行为，不静默覆盖业务语义。
7. `[合理推断]`、`[来源冲突]` 和 `[待人工确认]` 不得作为确定事实使用。
8. 修改字段、SQL/Mapper、配置、Profile/Feature Flag、API 参数、页面字段、中间件或核心流程后，必须由用户显式指定唯一变更标识，在 `cadence/knowledge-base/user-input/updates/CHANGE-变更标识/` 准备符合固定契约的完整变更包，并由 `knowledge-base-update` 消费后执行 Update。
9. 大型知识库按导航渐进加载，不一次读取全部子文档或全仓源码。

## 知识库定位

知识库是项目事实索引和代码导航，不替代源码、DDL、有效配置、测试和用户确认。

## 一级导航

- `base-information.md`
- `development-guide.md`
- 接口：Manifest 适用时为 `interfaces/README.md`；`scope.api.status` 为 `不适用` 时输出无链接 `interfaces：不适用（原因）`
- 页面：Manifest 适用时为 `pages/README.md`；`scope.pages.status` 为 `不适用` 时输出无链接 `pages：不适用（原因）`
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
| API 参数变更 | 接口适用时读取 `interfaces/README.md`、对应接口主文件、调用方、服务和数据模型文档；不适用时记录原因 |
| 页面字段变更 | 页面适用时读取 `pages/README.md`、页面主文档、API 参数和字段映射文档；不适用时记录原因 |
| 中间件配置变化 | `configurations/README.md`、服务配置文档、中间件当前证据和依赖服务文档 |
| 跨模块流程 | `README.md`、相关服务、接口、页面、表、配置和证据文档 |

## Update 变更包

完整变更包的变更标识必须由用户显式指定，唯一合法根目录为：

```text
cadence/knowledge-base/user-input/updates/CHANGE-变更标识/
```

根目录始终包含以下五份固定文件，文件之间不得合并，也不得省略：

```text
change-summary.md
code-change.md
database-change.md
configuration-change.md
verification.md
```

附件只能提供补充证据，不能替代任何固定文件。即使数据库无变更，`database-change.md` 仍必须存在并写明无变更及判断依据。`configuration-change.md` 始终必须存在：配置范围适用时无变更仍需双快照，配置范围不适用时必须写无变更和原因，快照字段可填写带原因的不适用并跳过比较。目录、文件和依据不完整时，不得调用 `knowledge-base-update` 或把 Update 标记为完成。
