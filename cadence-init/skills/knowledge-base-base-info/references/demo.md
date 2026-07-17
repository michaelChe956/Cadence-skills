# 基础信息与字段级数据模型案例

## 场景

Manifest 4.0 授权分析 `order-service`、`customer-service` 和 `admin-web`。`evidence.data_model_sources` 包含部分 MySQL DDL、迁移、Entity、Mapper XML 和手写 SQL；订单表按 `tenant_id` 分成 16 张物理表。

固定生成：

- `data-models/README.md`
- `data-models/SCHEMA-commerce/README.md`
- `data-models/SCHEMA-commerce/TABLE-customer.md`
- `data-models/SCHEMA-commerce/TABLE-order.md`
- `data-models/SCHEMA-commerce/TABLE-order-item.md`

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

## 其他基础信息示例

- `MIDDLEWARE-kafka-order-created` 同时具有代码和配置证据；Topic 实际值写 `<redacted>`。
- Nacos 与开发配置的 Redis DB 不一致时分别记录环境并标记来源冲突，不选择单一值。
- 后端构建命令来自 Maven Wrapper，前端命令来自 `package.json`；未发现安全的本地数据库初始化入口时不执行迁移。
