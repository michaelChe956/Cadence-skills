# KnowledgeBase Schema 4.0 初始化案例

## 无 DDL，但有代码结构证据

数据模型状态为 `全量`，`data-model-scope.md` 登记了 Entity、Mapper XML 和迁移文件，未提供 `database-ddl.sql`。

处理结果：

1. 校验可定位证据和纳入范围。
2. 允许继续初始化。
3. 将来源写入 `evidence.data_model_sources`，并在结论中标记证据限制。
4. Manifest 使用 `scope.data_models`，不把 DDL 缺失视为阻断。

## 配置快照缺失

配置状态为 `指定`，但 `configuration-scope.md` 中的外部目录不存在或不可读。

处理结果：

1. 在扫描前停止。
2. 报告缺失目录、模板路径和对 `scope.configurations` 的影响。
3. 不连接配置中心补取资料，不生成 Manifest 或半成品知识库。

## 配置不适用

配置状态为 `不适用`，原因是本次没有可授权的配置快照。

处理结果：

- Manifest 记录 `scope.configurations` 的状态与原因。
- `evidence.configuration_snapshots` 保持空基线。
- 初始化固定 `configurations/` 目录，但不分析配置内容。
- 其他领域继续执行。

## 六领域全部通过

工程信息、数据模型、配置、中间件、接口和页面均声明合法状态，引用文件有效；数据模型至少有一种结构证据，适用的配置快照目录可读。

处理结果：

1. 生成 `schema_version: "4.0"` 的 Manifest 和输入清单。
2. 初始化 `data-models/`、`configurations/` 等固定目录。
3. 领域 Skills 只消费 Manifest 的六个 `scope` 范围。
4. 配置基线写入 `evidence.configuration_snapshots.baseline`，包含最终指纹、`scope_summary`、纳入文件数量或清单摘要、服务摘要和文件规则摘要。
5. 首次初始化的 `update.processed_packages` 为空列表。
6. 按 `knowledge-base-base-info`、`knowledge-base-api`、`knowledge-base-pages`、`knowledge-base-overview`、`global-validation` 的顺序执行适用阶段；完成阶段写入 `completed_stages`，不适用阶段写入 `skipped_stages` 和原因。
7. `global-validation` 通过后写入 `global_validation: passed`、`status: complete` 和 `completed_at`。
8. `generated_at` 写入生成时间，`open_questions` 四级默认计数为 0。

## 快照标识映射冲突

`configuration-scope.md` 使用已经登记的快照标识 `test-release-20260717`，但声明了不同环境或不同外部目录。

处理结果：扫描前停止，报告冲突标识、已登记环境与目录、当前声明环境与目录；不重新解释为新快照，不覆盖 Manifest 基线。

## 既有 Manifest 门禁

1. 目标目录已有非 Schema 4.0 Manifest：立即停止，报告版本与固定产物路径，不覆盖、不迁移、不删除。
2. Manifest 缺失或不可解析，但 `data-models/`、`README.md` 或其他任一固定产物仍存在：不得按首次初始化继续；立即停止并报告已有产物与 Manifest 状态。
3. 用户明确授权“重新初始化 Schema 4.0”：先列出将清理的固定路径、人工内容丢失、基线与历史失效风险及重新生成范围；记录用户对范围和风险的授权后，清理固定产物并按六领域输入全新重建，不迁移旧字段或目录。

## 未完成初始化续跑

Manifest 为 Schema 4.0，`coverage.initialization.status: in_progress`；`completed_stages` 已登记 `knowledge-base-base-info`，接口领域适用但尚未完成。

处理结果：

1. 核对六领域范围没有变化，并确认已登记的基础信息文档、索引和证据一致。
2. 复用 `knowledge-base-base-info`，不重复扫描。
3. 从 `knowledge-base-api` 继续初始化，再按条件执行 `knowledge-base-pages`、`knowledge-base-overview` 和 `global-validation`。
4. 每阶段完成后更新 `completed_stages`；全局验收失败时写入 `global_validation: failed`，保持 `status: in_progress`，完成报告只列缺失项和继续初始化入口。

## 完整初始化保护

Manifest 为 Schema 4.0，`coverage.initialization.status: complete`，用户只要求“初始化 KnowledgeBase”。

处理结果：停止重复初始化，不修改既有产物；引导使用 Context 查询知识库，或使用 Update 处理变更包。只有用户显式授权重新初始化的精确清理范围和风险后，才进入全新重建。

如果 Schema 4.0 Manifest 缺少 `coverage.initialization`，则核对所有适用领域的文档登记和实际产物：全部一致时按完整初始化保护，否则按未完成初始化续跑，不要求删除现有产物。

## 指定接口模式

接口状态为 `指定`，`api-scope.md` 的指定能力为 `API-example-query`。

处理结果：只深挖该能力和完成调用链所需的内部依赖，不额外盘点无关接口。
