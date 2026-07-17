# KnowledgeBase Schema 4.0 输入契约

## 唯一入口与授权边界

`cadence/knowledge-base/user-input/base-info.md` 是唯一入口。只有六领域输入全部通过校验，才能扫描代码、生成 Manifest 或调用领域 Skills。

Manifest 只允许 `schema_version: "4.0"`。`scope.projects`、`scope.data_models`、`scope.configurations`、`scope.middleware`、`scope.api` 和 `scope.pages` 是领域 Skills 的唯一授权范围，不得重新解释原始输入或扩大范围。

## 初始化生命周期与重新初始化授权

在校验六领域输入前检查整个 `cadence/knowledge-base/`，不能只检查 Manifest。检测集合为：`manifest.yaml`、`input-inventory.md`、`README.md`、`base-information.md`、`development-guide.md`、`interfaces/`、`pages/`、`services/`、`data-models/`、`configurations/`、`evidence/`、`domain-glossary.md`、`open-questions.md`、`change-history.md`。

按以下顺序得到唯一判定：

1. 检测集合全部不存在：按首次初始化继续。
2. 任一固定产物存在，但 Manifest 缺失、不可解析、缺少 `schema_version` 或版本不是 4.0：立即停止，不覆盖、不迁移、不删除，并报告现有产物、Manifest 状态和影响。
3. Manifest 为 Schema 4.0：先执行下述完整初始化不变量只读校验。整个初始化块缺失时进入唯一兼容分支；块存在但字段损坏或矛盾时停止且不修改。
4. 初始化块合法且 `status: in_progress`：判定为未完成初始化；重新核对六领域输入范围、已登记阶段、实际文档和证据后继续初始化。
5. 初始化块合法且 `status: complete`：确认实际产物仍满足 complete 等价条件，保护已完成知识库，停止重复初始化，并引导使用 Context 或 Update。
6. 用户明确授权“重新初始化 Schema 4.0”：Manifest 版本和初始化状态仍须合法；清理前一次性列出精确路径、人工内容丢失风险、Git/配置/变更历史基线失效风险和全新生成范围，取得用户对范围与风险的授权并写入输入清单，再清理固定产物并全新重建。

第 4、5 项适用于没有显式重新初始化授权的请求；授权已明确且全部门禁通过时进入第 6 项，不把重建降级为续跑或完成保护。

`coverage.initialization` 缺失时，不要求删除现有 Schema 4.0 产物，也不得只凭文档登记或产物齐全推断完成。必须先执行当前完整 `global-validation`：

- 验收通过：按已完成知识库保护，并回填 `status: complete`、包含阶段 ID `global-validation` 的 `completed_stages`、适用的 `skipped_stages`、`global_validation: passed` 和 `completed_at`。
- 验收失败：按未完成初始化续跑，回填 `status: in_progress`、已独立验证完成的阶段 ID、`global_validation: failed` 和空 `completed_at`，再从首个缺失或不一致阶段继续。

重新初始化不读取旧 Manifest 字段进行映射，不迁移旧目录或兼容旧 Schema。普通初始化、补文档、修复、Context 或 Update 请求不构成清理重建授权。

## 完整初始化不变量

任何续跑、复用、领域调用、完成保护、清理或写入前，都必须只读验证 `coverage.initialization`；每次准备改变阶段状态或提交原子写入前必须重验。初始化块存在时，仅以下结构和状态合法：

| 字段 | 不变量 |
|------|--------|
| `status` | 只能是 `in_progress` 或 `complete` |
| `global_validation` | 只能是 `pending`、`failed` 或 `passed` |
| `completed_stages` | 无重复字符串列表；元素只能是 `base-info`、`api`、`pages`、`overview`、`global-validation` |
| `skipped_stages` | 无重复对象列表；每项仅有 `stage`、`reason`，`stage` 只能是 `api` 或 `pages`，`reason` 是非空字符串 |
| `completed_at` | `in_progress` 时为空；`complete` 时非空 |

阶段状态还必须同时满足：

1. 固定顺序是 `base-info → api → pages → overview → global-validation`。将合法跳过的 `api`、`pages` 合并到时间线后，`completed_stages` 必须是该固定顺序的合法前缀或子序列；前置阶段未完成且未合法跳过时不能出现后续阶段，`global-validation` 只能最后出现。
2. `completed_stages` 与 `skipped_stages` 不得重叠。`base-info`、`overview`、`global-validation` 永不可跳过。
3. `scope.api.status: 不适用` 时必须跳过 `api` 且不得完成；接口适用时必须不跳过。`pages` 与 `scope.pages.status` 使用同一领域适用性一致规则。
4. `status: in_progress` 时，`global_validation` 只能是 `pending` 或 `failed`，`completed_stages` 不含 `global-validation`，`completed_at` 为空。
5. `status: complete` 当且仅当 `base-info`、`overview`、`global-validation` 完成，所有适用的 `api`、`pages` 完成，所有不适用的 `api`、`pages` 正确跳过，`global_validation: passed`，`completed_at` 非空，而且实际适用产物、文档索引、Manifest 登记、服务导航和证据满足全部阶段完成条件。

初始化块存在但字段缺失、类型错误、非法 status、非法阶段 ID、重复、重叠、逆序、适用性冲突或 complete 与实际产物矛盾时，立即停止且不修改任何产物。一次性报告异常字段实际值、违反规则、影响阶段和风险；不得把它当成续跑，不得自动补齐、去重、重排、改写或通过显式重新初始化绕过。

整个初始化块缺失不属于字段损坏，保留唯一兼容分支：先只读执行当前完整 `global-validation`。通过后一次性回填合法 complete 状态并进入完成保护；失败后一次性回填合法 in_progress 状态，再从首个缺失或不一致阶段续跑。全局验收完成和初始化块回填前不得修改其他产物。

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

任一输入缺失或冲突时停止。首次初始化不生成 Manifest、输入清单或半成品目录；未完成初始化续跑时保留现有 Schema 4.0 产物和 `coverage.initialization.status: in_progress`。一次性返回：

- 缺失项和影响
- 目标项目期望路径
- 对应插件模板路径
- 最小填写示例
- 补齐后重新执行方式

## 领域编排与初始化进度

六领域输入完整后，必须按固定顺序调用 Skill 或执行内置阶段。Skill 名只用于调用，Manifest 只使用阶段 ID：

| 顺序 | 调用或动作 | 阶段 ID | 条件 |
|------|------------|---------|------|
| 1 | 调用 `knowledge-base-base-info` | `base-info` | 始终执行或验证完成 |
| 2 | 调用 `knowledge-base-api` | `api` | `scope.api.status != 不适用` 时执行 |
| 3 | 调用 `knowledge-base-pages` | `pages` | `scope.pages.status != 不适用` 时执行 |
| 4 | 调用 `knowledge-base-overview` | `overview` | 所有适用领域完成后执行 |
| 5 | 执行当前完整全局验收 | `global-validation` | 通过后才允许完成初始化 |

每个已执行或验证完成的阶段立即把字符串阶段 ID 写入 `coverage.initialization.completed_stages`，例如 `["base-info", "api"]`；不得写入 Skill 名。已经完成且 Manifest 登记、文档和证据一致的阶段复用，不重复扫描。

`coverage.initialization.skipped_stages` 的唯一结构是对象列表，每项仅包含 `stage` 和 `reason`，例如 `[{stage: "api", reason: "接口范围不适用"}]`。`stage` 只能是 `api` 或 `pages`；不得增加 `status`、`skill`、`name` 或其他键。列表不得重复，也不得与 `completed_stages` 重叠；默认空列表 `[]` 仅在 API 与 Pages 都适用时合法。

验收失败时将 `coverage.initialization.global_validation` 写为 `failed`，保持 `status: in_progress`；验收通过时写为 `passed`，将阶段 ID `global-validation` 加入 `completed_stages`，再将 `status` 写为 `complete` 并填写 `completed_at`。

## Schema 4.0 输出契约

- 初始化 `data-models/` 和 `configurations/`，即使对应领域为 `不适用` 也保留固定空目录。
- 数据模型来源写入 `evidence.data_model_sources`。
- 配置快照基线写入 `evidence.configuration_snapshots.baseline`，并保留可审计范围摘要。
- 首次初始化时 `update.last_change_package` 为空对象，`update.processed_packages` 为空列表。
- `documents.data_models` 和 `documents.configurations` 分别登记领域文档。
- `coverage.initialization` 只使用 `status`、`completed_stages`、`skipped_stages`、`global_validation` 和 `completed_at` 跟踪初始化进度。
- `generated_at` 记录本次新知识库的首次生成时间；`open_questions.blocking`、`high`、`medium`、`low` 按新生成的待确认文档初始化，并在后续流程中按实际待确认项更新。

只生成 Schema 4.0，不读取、兼容或迁移其他版本知识库。
