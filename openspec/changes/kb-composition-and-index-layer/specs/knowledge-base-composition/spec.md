# knowledge-base-composition 规格

## ADDED Requirements

### Requirement: CAP 组合能力实体

`knowledge-base-bootstrap` 固定输出树、固定产物检测集合与固定输入声明 MUST 包含 `capabilities/`。`knowledge-base-overview` MUST 提供组合文档模板（元数据含 `CAP-*` 稳定 ID 与 `proposed / verified / retired` 状态、目的与非目标、输入能力清单、编排与字段映射、输出契约、约束与鉴权、实现关联、证据）。组合实体的生成 MUST 限定两通道：`api-scope.md`"能力组合诉求"表声明的用户诉求通道（状态 `proposed`），或工程内已有聚合端点的反向建立通道（可 `verified`）；会话中推导的组合候选 MUST NOT 生成持久实体。`implementation_api_ids` 为空时状态 MUST 保持 `proposed`；`verified` MUST NOT 等同于对外已暴露，对外属性唯一权威仍是用户 api-scope 清单。`interfaces/README.md` 的"能力组合"分区 MUST 仅含导航字段（ID/名称/状态/明细链接）。Manifest MUST 含 `documents.capabilities` 登记域。

#### Scenario: 用户诉求生成组合

- **WHEN** api-scope 声明"用 API-A 与 API-B 组合提供全部用户信息"的诉求且输入 API 均存在
- **THEN** overview 生成 `CAP-*` 文档（状态 proposed），登记 COMPOSES 边与 documents.capabilities

#### Scenario: 已有聚合端点反向建立

- **WHEN** api 阶段发现某对外端点聚合调用两个既有能力且有实现证据
- **THEN** Overview 建立对应 CAP 并关联 implementation_api_ids，状态可为 verified

#### Scenario: 会话候选不落库

- **WHEN** Agent 在会话中推导出潜在组合但无用户诉求亦无实现证据
- **THEN** 只输出会话级候选并登记待确认，不生成 CAP 实体

#### Scenario: 无诉求且无聚合端点

- **WHEN** 项目没有任何组合诉求与聚合端点
- **THEN** `capabilities/` 只含带"未提供"说明的 README，初始化正常完成

### Requirement: JOIN_KEY 证据纪律

组合的连接键字段 MUST 由两个输入 API 各自经"API 模型 → SERVICE/MODULE → Mapper/SQL → TABLE 字段"逐跳映射到同一表字段证明；字段同名 MUST NOT 构成关联依据。任一映射跳缺失或待确认时，`JOIN_KEY` 边 MUST 标待确认，关联组合 MUST NOT 处于 `verified` 状态。

#### Scenario: 连接键逐跳可证

- **WHEN** 两侧 userId 均经 Mapper/SQL 映射到 TABLE-USER.ID
- **THEN** JOIN_KEY 边登记且证据为两侧映射锚点

#### Scenario: 映射跳缺失

- **WHEN** 某输入 API 的连接键字段端到端映射状态为待确认
- **THEN** JOIN_KEY 标待确认，组合状态保持/降为 proposed

### Requirement: 派生关系图与等值校验

`evidence/relation-graph.yaml` MUST 作为追溯矩阵的唯一机读投影：严格派生（与矩阵在同一次原子写入中重建受影响条目，禁止手工编辑）、节点覆盖全部已登记稳定 ID 实体、每边保留 source span、`derived_from` 指向矩阵。`knowledge-base-bootstrap` 的 global-validation MUST 新增第 6 项等值校验：图边数等于矩阵数据行数、图节点 ID 集等于 Manifest 各 documents 域登记与矩阵两端 ID 的并集；任一不符判 `failed`。relation-types.md 横向 3 类（`COMPOSES`/`JOIN_KEY`/`PROVIDES_FIELD`）MUST 改标"已启用（2b）"，且 MUST 限定组合层（Overview 通道）为其唯一合法写入方；api 与 pages 的矩阵写入行 MUST 仍限定纵向类型。

#### Scenario: 矩阵与图同批写入

- **WHEN** 任一领域 Skill 原子写入矩阵行
- **THEN** relation-graph.yaml 对应边在同一原子写入中重建

#### Scenario: 等值校验失败

- **WHEN** global-validation 发现图边数与矩阵数据行数不一致
- **THEN** 验收判 `failed`，保持 `in_progress` 与空 `completed_at`

#### Scenario: 横向类型写入方限定

- **WHEN** api 或 pages 阶段尝试写入 COMPOSES/JOIN_KEY/PROVIDES_FIELD 边
- **THEN** 写入被拒绝并登记待确认；横向边只能由组合层通道生成

### Requirement: context 图消费与漂移分级

`knowledge-base-context` 的精确种子直取 MUST 优先在 relation-graph.yaml 命中节点（读取 doc 引用与一跳边）；图缺失或不命中时 MUST 降级 README 索引链并记录降级原因。任务种子命中 `CAP-*` 时 MUST 读取其输入 API 的契约锚点与 JOIN_KEY 证据并执行漂移检查。漂移 MUST 分级：普通漂移（相关代码变化但契约字段、鉴权、连接键映射未证伪）判 `有条件就绪` 并记录明细；关键失效（输入 API 删除或转 `已废弃`、契约字段或鉴权变化影响任务结论、JOIN_KEY 证据跳失效）判 `阻断`。MUST NOT 新增状态枚举或新增漂移落盘出口（保存走既有 `task-contexts/`）。

#### Scenario: 精确种子走图

- **WHEN** 种子为精确稳定 ID 且 relation-graph.yaml 存在
- **THEN** 直接读取命中节点的 doc 与一跳边，不读总入口与领域索引

#### Scenario: 图缺失降级

- **WHEN** relation-graph.yaml 不存在
- **THEN** 回退 README 索引链并在证据摘要记录降级原因

#### Scenario: 组合输入 API 关键失效

- **WHEN** 任务命中某 CAP 且其输入 API 已转 `已废弃`
- **THEN** 就绪状态判 `阻断`，输出失效明细与修正建议

### Requirement: Update 横向重算与锚点复核

`knowledge-base-update` 的影响链命中横向边（COMPOSES/JOIN_KEY/PROVIDES_FIELD）时 MUST 重算：输入 API 被删除或转 `已废弃` 时，关联 CAP MUST 标 `待确认` 或 `retired`，MUST NOT 保留断链 `verified`；JOIN_KEY 证据跳失效时 CAP MUST 降 `proposed` 并登记待确认。Update 更新受影响实体文档时 MUST 复核文档内证据锚点（文件:行号）在当前提交可定位，失效锚点 MUST 登记"待重锚"待确认。横向重算与 relation-graph 重建 MUST 在同一原子提交。

#### Scenario: 输入 API 被删除

- **WHEN** 变更包影响链显示某 CAP 的输入 API 实体被删除
- **THEN** 该 CAP 标待确认或 retired，COMPOSES 边失效记录入变更历史

#### Scenario: 锚点失效

- **WHEN** 受影响实体文档的证据锚点在当前提交不可定位
- **THEN** 登记待重锚待确认项，不静默保留失效锚点
