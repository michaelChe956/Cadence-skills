# 基础信息、字段级数据模型与配置快照案例

## 场景

Manifest 4.0 授权分析虚构的 `order-service`、`customer-service` 和 `admin-web`。`evidence.data_model_sources` 包含部分 MySQL DDL、迁移、Entity、Mapper XML 和手写 SQL；订单表按 `tenant_id` 分成 16 张物理表。`scope.configurations` 授权一个锁定测试发布批次的外部不可变配置快照，配置分析前后的最终快照指纹一致。

固定生成：

- `data-models/README.md`
- `data-models/SCHEMA-commerce/README.md`
- `data-models/SCHEMA-commerce/TABLE-customer.md`
- `data-models/SCHEMA-commerce/TABLE-order.md`
- `data-models/SCHEMA-commerce/TABLE-order-item.md`
- `configurations/README.md`
- `configurations/SERVICE-order-service.md`
- `configurations/SERVICE-customer-service.md`
- `configurations/SERVICE-admin-web.md`

## 普通逻辑表字段级摘要

`TABLE-customer` 对应普通逻辑表 `t_customer`，每张逻辑表均有独立文档。字段清单示例：

| 字段 | 类型 | 可空 | 默认值 | 主键 | 含义 | 代码映射 | 证据状态 | 证据位置 |
|------|------|------|--------|------|------|----------|----------|----------|
| `id` | `BIGINT` | 否 | 待确认 | 是 | 客户 ID | `CustomerEntity.id` | DDL 已确认 | `inputs/ddl/customer.sql:4` |
| `name` | `VARCHAR(128)` | 否 | 待确认 | 否 | 客户名称 | `CustomerEntity.name` | DDL 已确认 | `inputs/ddl/customer.sql:5` |
| `created_at` | `DATETIME` | 否 | `CURRENT_TIMESTAMP` | 否 | 创建时间 | `CustomerEntity.createdAt` | DDL 已确认 | `inputs/ddl/customer.sql:6` |

文档同时记录 `CustomerMapper#selectById` 为读映射、`CustomerMapper#insert` 为写映射，并关联 `SERVICE-customer-service`、`API-customer-detail` 和 `PAGE-customer-detail`。

## 分片逻辑表与物理表规则

`TABLE-order` 只生成一个逻辑表文档：

| 项目 | 内容 | 证据状态 | 证据位置 |
|------|------|----------|----------|
| 逻辑表 | `t_order` | 用户提供 | `user-input/data-model-scope.md` |
| 分片键 | `tenant_id` | 用户提供 | `user-input/data-model-scope.md` |
| 物理表规则 | `t_order_${00..15}` | 用户提供 | `user-input/data-model-scope.md` |
| 路由规则 | `tenant_id % 16` | 代码可推导 | `ShardTableAlgorithm#doSharding` |

不为 `t_order_00` 至 `t_order_15` 分别生成文档。Schema 索引只列 `TABLE-order`，物理分片数量和规则写入“分库分表”章节。

## DDL 与 Entity 字段冲突

DDL 定义 `t_order.status VARCHAR(16) NOT NULL DEFAULT 'CREATED'`，Entity 声明 `@Column(length = 32) private String status`。字段清单保留两侧原值：

| 字段 | 类型 | 可空 | 默认值 | 主键 | 含义 | 代码映射 | 证据状态 | 证据位置 |
|------|------|------|--------|------|------|----------|----------|----------|
| `status` | DDL：`VARCHAR(16)`；Entity：长度 32 | DDL：否 | DDL：`CREATED` | 否 | 订单状态 | `OrderEntity.status` | 来源冲突 | `inputs/ddl/order.sql:8`；`OrderEntity.java:27` |

不得选择其中一个覆盖另一个。冲突、可能的截断风险和待确认的生产 Schema 版本同时进入“证据与来源冲突”和 `open-questions.md`。

## 无 DDL 的 Mapper/SQL 推导

`TABLE-order-item` 没有 DDL 或完整迁移，仅在 `OrderItemMapper.xml` 和手写 SQL 中出现：

| 字段 | 类型 | 可空 | 默认值 | 主键 | 含义 | 代码映射 | 证据状态 | 证据位置 |
|------|------|------|--------|------|------|----------|----------|----------|
| `id` | 待确认 | 待确认 | 待确认 | 待确认 | 订单项标识，待确认 | `OrderItemMapper.resultMap.id` | 代码可推导 | `OrderItemMapper.xml#OrderItemMap` |
| `order_id` | 待确认 | 待确认 | 待确认 | 待确认 | 关联订单，数据库外键待确认 | `OrderItemEntity.orderId` | 代码可推导 | `OrderItemMapper.xml#selectByOrderId` |
| `sku` | 待确认 | 待确认 | 待确认 | 待确认 | 商品 SKU | `OrderItemEntity.sku` | 代码可推导 | `OrderItemMapper.xml#OrderItemMap` |
| `quantity` | 待确认 | 待确认 | 待确认 | 待确认 | 数量 | `OrderItemEntity.quantity` | 代码可推导 | `OrderItemRepository.java:41` |

Mapper 的 `SELECT` 和手写 SQL 的 `INSERT` 可以证明代码引用这些字段，但不能证明数据库类型、默认值、主键、外键、可空性或实际索引。文档明确标记动态 SQL 分支可能不完整；`order_id` 与订单表字段同名不能单独证明外键关系。

## 配置快照分类与重复合并

虚构快照包含以下文件：

| 文件 | 判定 | 文档处理 |
|------|------|----------|
| `order-service/application-test.yml` | 运行时配置 | 进入 `SERVICE-order-service.md` |
| `customer-service/application-test.yml` | 与订单服务共享文件内容相同 | 当前运行内临时哈希确认后合并分析，并分别记录两个适用服务；哈希不写入 KnowledgeBase |
| `order-service/OrderMapper.xml` | Mapper XML | 转交 `TABLE-order` 数据模型文档，配置文档只关联 `TABLE-order` |
| `order-service/logback.xml` | 日志配置 | 归入可观测性，配置文档只记录导航 |
| `deploy.sh` | 部署脚本 | 只作为加载顺序证据，禁止执行 |
| `.idea/workspace.xml`、`.gitkeep`、空文件、`application.xml-20220215` | 默认排除项或明确历史备份 | 不纳入当前配置基线 |

相同内容文件只分析一次，但服务导航和服务文档仍分别记录适用服务。相同 basename 若内容、Profile 或加载顺序不同，则分别保留，不能仅凭名称合并。

## 配置键绑定与 Profile 差异

`order-service` 的虚构配置组通过 `@ConfigurationProperties(prefix = "acme.order")` 绑定到 `OrderFeatureProperties`。服务配置文档记录 `acme.order.retry-enabled` 的绑定位置和条件装配证据。测试 Profile 启用重试，而默认 Profile 未发现同名键，因此分别记录环境差异；不能把测试 Profile 结论升级为生产事实。

配置键清单示例：

| 配置键 | 用途 | 值类型 | 环境 | 来源文件 | 绑定位置 | 敏感级别 | 状态 | 证据 |
|--------|------|--------|------|----------|----------|----------|------|------|
| `acme.order.retry-enabled` | 控制订单重试装配 | Boolean | test | `application-test.yml` | `OrderFeatureProperties` | 普通 | 存在 | 配置与代码绑定 |
| `spring.datasource.password` | 数据源认证 | String | test | `application-test.yml` | `DataSourceProperties` | 高 | 存在 | 值为 `<redacted>` |
| `partner.access-key` | 外部系统认证 | String | test | `application-test.yml` | `PartnerClientProperties` | 高 | 存在 | 值为 `<redacted>` |
| `partner.internal-url` | 内部端点 | URL | test | `application-test.yml` | `PartnerClientProperties` | 高 | 存在 | 值为 `<redacted>` |

文档不保存上述敏感值的哈希、文件内容哈希或完整连接串。若配置键同时出现在共享基线与服务覆盖文件且值或加载顺序冲突，状态写 `来源冲突`，不自行选择生效值。

## 其他基础信息示例

- `MIDDLEWARE-kafka-order-created` 同时具有代码和配置证据；Topic 实际值写 `<redacted>`。
- Nacos 与开发配置的 Redis DB 不一致时分别记录环境并标记来源冲突，不选择单一值。
- 后端构建命令来自 Maven Wrapper，前端命令来自 `package.json`；未发现安全的本地数据库初始化入口时不执行迁移。
- `base-information.md` 的配置章节只保留当前快照、Profile、配置组、风险和 `configurations/README.md` 导航，不复制服务配置键清单。

## Manifest 生命周期示例

BaseInfo 分析前 Manifest 的 `generated_at` 为知识库首次生成时间。本次分析新增一个高优先级配置来源冲突，并解决一个中优先级字段问题：先更新 `open-questions.md` 的两条记录，再按全部未解决条目重算阻断、高、中、低计数。受影响领域文档、待确认文档和 Manifest 四级计数原子写入；`generated_at` 保持原值，不改为本次分析时间。
