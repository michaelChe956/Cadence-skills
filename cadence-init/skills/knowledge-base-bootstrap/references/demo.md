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
6. `generated_at` 写入生成时间，`open_questions` 四级默认计数为 0。

## 快照标识映射冲突

`configuration-scope.md` 使用已经登记的快照标识 `test-release-20260717`，但声明了不同环境或不同外部目录。

处理结果：扫描前停止，报告冲突标识、已登记环境与目录、当前声明环境与目录；不重新解释为新快照，不覆盖 Manifest 基线。

## 既有 Manifest 门禁

1. 目标目录已有非 Schema 4.0 Manifest：立即停止，报告版本与固定产物路径，不覆盖、不迁移、不删除。
2. Manifest 缺失或不可解析，但 `data-models/`、`README.md` 或其他任一固定产物仍存在：不得按首次初始化继续；立即停止并报告已有产物与 Manifest 状态。
3. 目标目录已有 Schema 4.0 Manifest，但用户只说“初始化 KnowledgeBase”：立即停止，要求用户明确是否“重新初始化 Schema 4.0”，不把普通初始化请求当作授权。
4. 用户明确授权“重新初始化 Schema 4.0”：先列出将清理的固定路径、人工内容丢失、基线与历史失效风险及重新生成范围；记录用户对范围和风险的授权后，清理固定产物并按六领域输入全新重建，不迁移旧字段或目录。

## 指定接口模式

接口状态为 `指定`，`api-scope.md` 的指定能力为 `API-example-query`。

处理结果：只深挖该能力和完成调用链所需的内部依赖，不额外盘点无关接口。
