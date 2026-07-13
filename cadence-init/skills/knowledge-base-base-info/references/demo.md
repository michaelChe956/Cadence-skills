# 基础信息案例

## 场景

项目包含：

- `order-service`：Spring Boot、MyBatis-Plus
- `admin-web`：Vue 3、Pinia、Vite
- MySQL 订单库，按 `tenant_id` 分成 16 张订单表
- Kafka 订单事件
- Redis 缓存和分布式锁
- Nacos 配置中心

## 示例结论

### 数据模型

- `TABLE-order` `[DDL事实]` `[可信度：高]`
  - 逻辑表：`t_order`
  - 物理表：`t_order_00` 至 `t_order_15`
  - 分片键：`tenant_id`
  - 证据：`inputs/ddl/order.sql`、分片规则说明

### 中间件

- `MIDDLEWARE-kafka-order-created` `[代码事实]` `[配置事实]` `[可信度：高]`
  - Producer：`OrderEventPublisher#publishCreated`
  - Topic 配置键：`order.kafka.topic.created`
  - 实际值：`<redacted>`
  - Consumer：当前仓库未发现，标记外部消费者待确认

### 来源冲突

- Nacos 配置声明 Redis DB 为 `2`，开发配置为 `0` `[来源冲突]`
  - 处理：分别记录环境，不选择单一值
  - 待确认：生产环境有效命名空间

### 开发指南

- 后端构建命令来源于 Maven Wrapper。
- 前端命令来源于 `package.json`。
- 未发现可安全执行的本地数据库初始化脚本，因此只记录迁移入口，不自动运行。

