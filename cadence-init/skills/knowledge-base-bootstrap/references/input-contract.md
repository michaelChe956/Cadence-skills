# KnowledgeBase Schema 4.0 输入契约

## 唯一入口与授权边界

`cadence/knowledge-base/user-input/base-info.md` 是唯一入口。只有六领域输入全部通过校验，才能扫描代码、生成 Manifest 或调用领域 Skills。

Manifest 只允许 `schema_version: "4.0"`。`scope.projects`、`scope.data_models`、`scope.configurations`、`scope.middleware`、`scope.api` 和 `scope.pages` 是领域 Skills 的唯一授权范围，不得重新解释原始输入或扩大范围。

## 既有 Manifest 与重新初始化授权

在校验六领域输入前检查整个 `cadence/knowledge-base/`，不能只检查 Manifest。检测集合为：`manifest.yaml`、`input-inventory.md`、`README.md`、`base-information.md`、`development-guide.md`、`interfaces/`、`pages/`、`services/`、`data-models/`、`configurations/`、`evidence/`、`domain-glossary.md`、`open-questions.md`、`change-history.md`。

- 检测集合全部不存在：按首次初始化继续。
- 任一固定产物存在：不得按首次初始化继续，必须校验 Manifest 和重新初始化授权。
- 固定产物存在但 Manifest 缺失、不可解析、缺少 `schema_version` 或版本不是 4.0：立即停止，不覆盖、不迁移、不删除，并报告现有产物、Manifest 状态和影响。
- Manifest 为 Schema 4.0，但用户未显式授权“重新初始化 Schema 4.0”：立即停止，不修改现有 KnowledgeBase。
- 只有用户明确授权“重新初始化 Schema 4.0”时才允许清理固定产物并全新重建。清理前一次性列出精确路径、人工内容丢失风险、Git/配置/变更历史基线失效风险和重新生成范围，取得用户对范围与风险的授权并写入输入清单。
- 重新初始化不读取旧 Manifest 字段进行映射，不迁移旧目录或兼容旧 Schema。普通初始化、补文档、修复或 Update 请求不构成清理重建授权。

## 六领域输入

| 领域 | 引用文件 | 适用说明 |
|------|----------|----------|
| 工程信息 | `project-scope.md` | 定义允许扫描的本地工程与路径 |
| 数据模型 | `data-model-scope.md` | 定义数据库、Schema、结构证据、分库分表和排除范围 |
| 配置 | `configuration-scope.md` | 定义当前基线快照、纳入服务、文件规则与敏感信息边界 |
| 中间件 | `middleware-scope.md` | 定义中间件及其已知使用范围 |
| 接口 | `api-scope.md` | 登记全部对外能力与本次执行范围 |
| 页面 | `page-scope.md` | 定义前端应用、页面、路由和权限范围 |

`database-ddl.sql` 是数据模型的可选证据，不是独立领域，也不是继续执行的硬前置。

## 状态与扫描前校验

状态只允许 `全量`、`指定`、`不适用`。

| 状态 | 校验与行为 |
|------|------------|
| 全量 | 引用文件必须存在且可读；只在已声明工程和资料范围内全盘分析该领域 |
| 指定 | 引用文件必须存在且可读；指定清单或匹配规则不得为空，只分析明确范围及必要依赖 |
| 不适用 | 必须填写原因；不要求引用文件可用，Manifest 记录原因并跳过领域 |

扫描前一次性校验：六领域章节、合法状态、资料链接、指定范围、不适用原因、工程路径和配置快照目录。空白状态、未知状态、失效链接、空指定范围和互相冲突的声明均属于输入缺失。

## 数据模型证据

数据模型状态为 `全量` 或 `指定` 时，`data-model-scope.md` 必须至少登记一种可定位且纳入分析的结构证据。允许的证据类型为：

- DDL
- 数据库迁移文件
- Entity
- Mapper 接口或 Mapper XML
- 普通 SQL
- 人工资料

DDL 可以不提供。没有 DDL、但存在其他有效结构证据时继续，并在 `evidence.data_model_sources` 记录来源类型、路径和证据限制。没有任何结构证据时停止，要求补充证据或将数据模型改为 `不适用` 并填写原因。

Mapper XML 和迁移文件归入数据模型证据；结构来源冲突时不擅自裁决，把冲突和影响写入 `open_questions`。迁移文件只能作为只读证据，不得执行。

## 配置快照

配置是独立一级输入。配置状态为 `全量` 或 `指定` 时：

1. `configuration-scope.md` 必须填写当前基线快照。
2. 来源必须是锁定发布批次的不可变快照；外部目录必须可读，且与声明的环境和发布批次一致。
3. `指定` 状态必须提供非空服务清单或文件匹配规则。
4. 快照目录全程只读，不得复制到 `cadence/knowledge-base/`，不得连接配置中心或远程环境补取资料。
5. 配置仓库作为来源时必须固定到明确提交、标签或导出快照，不得指向持续变化的工作目录。
6. 必须填写 `scope_summary` 对应的范围摘要，以及纳入文件数量或文件清单摘要、服务摘要和文件规则摘要；这些摘要必须能与纳入服务和文件规则逐项核对。
7. 同一 `snapshot_id` 不得映射到不同环境或不同外部目录。当前输入、Manifest 已登记基线或同批次资料出现同名快照时，环境和目录必须完全一致，否则停止并报告冲突。
8. 分析开始和结束时必须按固定算法分别计算最终快照指纹；两次指纹不一致、范围摘要不一致或目录内容变化时立即停止，不得生成配置结论。

默认排除 `.idea`、`.gitkeep`、空文件和明确历史备份。部署脚本、发布脚本和启动脚本只能作为配置加载链路的只读证据，不得执行。只记录敏感配置键、用途和值类型，不复制实际值。

敏感信息包括密码、Token、AccessKey、Secret、密钥、私钥、完整连接串，以及内部域名、IP、URL 等敏感内部地址。Manifest 可以记录用户授权的本地文件系统路径；配置值中的内部端点必须脱敏，不得把实际端点写入 Manifest 或知识库文档。

快照指纹按以下固定算法生成：

1. 取纳入范围内文件并按相对路径排序。
2. 为每个文件计算 SHA-256。
3. 形成 `相对路径 + 制表符 + 文件 SHA-256` 的有序清单。
4. 对该清单计算最终 SHA-256。

Manifest 的 `evidence.configuration_snapshots.baseline` 保存最终快照指纹、来源元数据、`scope_summary`、纳入文件数量或清单摘要、服务摘要和文件规则摘要，不保存原始配置内容或单个敏感配置值的哈希。重复文件哈希只允许在当前分析过程中临时使用。

## 对外能力与缺失处理

`api-scope.md` 是全部对外能力的权威清单。清单内能力保持对外分类；工程内发现但未登记的能力归入对内能力；清单与代码冲突时保留用户分类并登记待确认项。

任一输入缺失或冲突时停止，不生成 Manifest、输入清单或半成品目录。一次性返回：

- 缺失项和影响
- 目标项目期望路径
- 对应插件模板路径
- 最小填写示例
- 补齐后重新执行方式

## Schema 4.0 输出契约

- 初始化 `data-models/` 和 `configurations/`，即使对应领域为 `不适用` 也保留固定空目录。
- 数据模型来源写入 `evidence.data_model_sources`。
- 配置快照基线写入 `evidence.configuration_snapshots.baseline`，并保留可审计范围摘要。
- 首次初始化时 `update.last_change_package` 为空对象，`update.processed_packages` 为空列表。
- `documents.data_models` 和 `documents.configurations` 分别登记领域文档。
- `generated_at` 记录本次新知识库的首次生成时间；`open_questions.blocking`、`high`、`medium`、`low` 按新生成的待确认文档初始化，并在后续流程中按实际待确认项更新。

只生成 Schema 4.0，不读取、兼容或迁移其他版本知识库。
