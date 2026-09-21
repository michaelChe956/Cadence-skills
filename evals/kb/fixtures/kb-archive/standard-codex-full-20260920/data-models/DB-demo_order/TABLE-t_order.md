# t_order

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 逻辑表稳定 ID | TABLE-t_order |
| 数据库/Schema 稳定 ID | DB-demo_order |
| 逻辑表名称 | t_order |
| 物理表名称或规则 | `t_order`（未发现物理分片规则） |
| 业务域 | 订单 |
| 证据基线（必填） | 1f867b9fcdf95f2e11808454898f333d7d512e90 |
| 最后核验时间（必填） | 2026-09-20 |

> `证据基线`（本次分析 Git 基线提交）与 `最后核验时间`（本次分析日期）为必填字段；为空视为文档不完整，阶段不得完成。

## 2. 业务含义

订单表，保存订单号、下单用户、状态、金额与创建时间；表注释声明状态迁移受 `OrderService` 状态机约束 [代码证据]（`db/init.sql:32`、`order-service/src/main/java/com/demo/order/service/OrderService.java:21-35`）。

## 3. 字段清单

| 字段 | 类型 | 可空 | 默认值 | 主键 | 含义 | 代码映射 | 证据状态 | 证据位置 |
|------|------|------|--------|------|------|----------|----------|----------|
| `order_id` | `BIGINT` | 否 | DDL 未声明 | 是 | 订单号 | `OrderEntity.orderId`；`OrderMapper.xml#selectById`（`order_id AS orderId`） | DDL 已确认 | `db/init.sql:27`；`order-service/src/main/resources/mapper/OrderMapper.xml:5` |
| `user_id` | `BIGINT` | 否 | DDL 未声明 | 否 | 下单用户，注释声明与 `t_user.user_id` 同源 | `OrderEntity.userId`（`user_id AS userId`） | DDL 已确认 | `db/init.sql:28`；`OrderMapper.xml:5` |
| `status` | `VARCHAR(16)` | 否 | DDL 未声明（代码以 `CREATED` 为起始状态，未发现建单写入证据） | 否 | 订单状态：`CREATED`/`PAID`/`SHIPPED`/`COMPLETED`/`CANCELLED` | `OrderEntity.status`、`OrderStatus` | DDL 已确认 | `db/init.sql:29`；`order-service/src/main/java/com/demo/order/entity/OrderStatus.java:4-9` |
| `amount` | `DECIMAL(18,2)` | 否 | DDL 未声明 | 否 | 订单金额 | `OrderEntity.amount`（`amount`） | DDL 已确认 | `db/init.sql:30`；`OrderMapper.xml:5` |
| `created_at` | `DATETIME` | 是（DDL 未声明 `NOT NULL`） | `CURRENT_TIMESTAMP` | 否 | 创建时间 | 未映射（代码未使用该字段） | DDL 已确认 | `db/init.sql:31` |

> 证据状态只允许 `DDL 已确认`、`迁移已确认`、`代码可推导`、`用户提供`、`来源冲突`、`待确认`。缺少证据的属性单独写 `待确认`；不得依据 Entity、Mapper 或 SQL 补造实际索引、默认值或数据库约束。

## 4. 索引与约束

| 名称 | 类型 | 字段与顺序 | 定义 | 证据状态 | 证据位置 |
|------|------|------------|------|----------|----------|
| PRIMARY | 主键 | `order_id` | `PRIMARY KEY` | DDL 已确认 | `db/init.sql:27` |

未发现二级索引、唯一约束、外键、检查约束或触发器；`user_id` 未声明索引（按 `user_id` 查询的效率无法从授权证据确认）。实际数据库中是否存在其他索引无法确认。

## 5. 分库分表

| 项目 | 内容 | 证据状态 | 证据位置 |
|------|------|----------|----------|
| 分片键 | 未发现 | 待确认 | 未发现分片配置或路由代码 |
| 分片规则 | 未发现 | 待确认 | 同上 |
| 物理表规则 | 未发现（按单表 `t_order` 建模） | 待确认 | `db/init.sql:26` |
| 配置组稳定 ID | 不适用 | 已确认 | `configurations/SERVICE-order-service.md` |

> 一张逻辑表只生成本文件一份；物理分片只记录规则，不为每个物理表复制文档。

## 6. Entity、Mapper 与 SQL 映射

| 类型 | 稳定 ID 或符号 | 操作 | 字段范围 | 证据位置 | 完整性限制 |
|------|----------------|------|----------|----------|------------|
| Entity | `CODE-OrderEntity`（`com.demo.order.entity.OrderEntity`） | - | `orderId`、`userId`、`status`、`amount` | `order-service/src/main/java/com/demo/order/entity/OrderEntity.java:3-11` | getter/setter 未在样本中展开（注释说明省略） |
| Mapper 接口 | `CODE-OrderMapper`（`com.demo.order.mapper.OrderMapper`） | SELECT、UPDATE | `order_id` 条件、`status` 赋值 | `order-service/src/main/java/com/demo/order/mapper/OrderMapper.java:10-11` | - |
| Mapper XML | `CODE-OrderMapperXml-selectById` | SELECT | `order_id`、`user_id`、`status`、`amount` | `order-service/src/main/resources/mapper/OrderMapper.xml:4-6` | 显式 `AS` 映射；无动态 SQL |
| Mapper XML | `CODE-OrderMapperXml-updateStatus` | UPDATE | `status`、`order_id` | `order-service/src/main/resources/mapper/OrderMapper.xml:7-9` | 无乐观锁或状态前置条件（状态机校验在服务层） |

未发现 `INSERT`、`DELETE` 语句，因此订单建单与删除链路缺失（仅表示授权证据未覆盖）。

## 7. 读写服务

| 服务稳定 ID | 方法或入口 | 读/写 | 调用映射 | 证据位置 |
|-------------|------------|-------|----------|----------|
| SERVICE-order-service | `OrderService.ship(Long)` | 读 + 写 | `OrderMapper.selectById`、`OrderMapper.updateStatus(SHIPPED)` | `order-service/src/main/java/com/demo/order/service/OrderService.java:25-35` |
| SERVICE-order-service | `OrderService.markPaid(Long)` | 写 | `OrderMapper.updateStatus(PAID)` | `order-service/src/main/java/com/demo/order/service/OrderService.java:38-41` |
| 未发现 | 建单/取消调用方 | 写 | - | 未发现 `INSERT` 或调用入口 |

## 8. 关联 API 与页面

| 类型 | 稳定 ID | 名称 | 关系 | 证据位置 |
|------|---------|------|------|----------|
| API | 未生成（`api` 阶段尚未执行，本阶段不扫描接口） | - | - | `open-questions.md` |
| 页面 | 未生成（`pages` 阶段尚未执行，本阶段不扫描页面） | - | - | `open-questions.md` |

## 9. 特殊字段与数据规则

| 字段 | 规则类型 | 规则说明 | 证据状态 | 证据位置 |
|------|----------|----------|----------|----------|
| `status` | 状态机 | `CREATED → PAID → SHIPPED → COMPLETED`；任意非终态 → `CANCELLED`；已取消不可发货，仅 `PAID` 可发货 | 代码可推导（代码 + 测试规格） | `order-service/src/main/java/com/demo/order/entity/OrderStatus.java:3-9`、`service/OrderService.java:21-35`、`src/test/java/com/demo/order/OrderServiceTest.java:14-28`；规则卡 `business/rules/RULE-order-ship-constraint.md`、`business/rules/RULE-order-status-transition.md` |
| `status` | 枚举取值 | 取值集合与 DDL 注释一致 | DDL 已确认 | `db/init.sql:29` |
| `user_id` | 标识关联 | 注释声明与 `t_user.user_id` 同源（候选关联） | 待确认 | `db/init.sql:28` |
| `created_at` | 默认值 | 未显式赋值时按数据库默认 `CURRENT_TIMESTAMP` | DDL 已确认 | `db/init.sql:31` |

## 10. 证据与来源冲突

| 对象或属性 | 来源 A | 来源 B | 冲突或限制 | 影响 | 处理状态 |
|------------|--------|--------|------------|------|----------|
| `status` 默认值 | `db/init.sql:29`（无 `DEFAULT`） | `OrderStatus.java:5`（`CREATED` 为起始状态） | DDL 未声明默认值，建单链路未发现 | 无法确认建单时状态如何赋值 | 待确认（Q-M4 关联项） |
| `user_id` 引用 | `db/init.sql:28` 注释 | DDL 无 `FOREIGN KEY` | 注释不能证明约束 | 跨库关联不能作为数据库事实 | 待确认（Q-M5） |
| 写入链路完整性 | `OrderMapper.xml:7-9`（仅 `updateStatus`） | 未发现创建订单的 `INSERT` 或调用方 | 授权证据未覆盖建单路径 | 订单生命周期不完整 | 待确认（Q-M4 关联项） |

## 11. 变更记录

| 日期 | 基线 | 变更内容 | 来源 |
|------|------|----------|------|
| 2026-09-20 | 1f867b9fcdf95f2e11808454898f333d7d512e90 | 首次生成字段级文档 | knowledge-base-base-info |
