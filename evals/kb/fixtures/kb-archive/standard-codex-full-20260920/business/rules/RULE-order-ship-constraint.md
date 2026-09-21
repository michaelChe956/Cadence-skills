# 订单发货状态约束

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 规则稳定 ID | RULE-order-ship-constraint |
| 条目状态 | confirmed |
| 规则类型 | 状态迁移 |
| 来源 | 测试断言 + 代码证据 + `user-input/product.md`（订单管理） |

## 2. 规则陈述

只有处于“已支付（`PAID`）”状态的订单可以发货并流转为“已发货（`SHIPPED`）”；“已取消（`CANCELLED`）”订单不允许发货；其他非 `PAID` 状态同样被拒绝发货。

## 3. 适用范围

| 实体稳定 ID | 关系说明 |
|------------|----------|
| API-order-ship | 发货接口在服务层执行该校验，违规时抛 `IllegalStateException` |
| PAGE-order-manage | 页面“发货”按钮是该规则的用户触发入口 |
| FLOW-order-ship | 该规则是流程第 5 步的核心判定分支 |
| TABLE-t_order | `status` 字段是该规则的判定依据与写入目标 |
| MODULE-order-core | 校验与状态更新实现所在模块 |

## 4. 证据

| 证据类型 | 位置 | 说明 |
|----------|------|------|
| 测试 | `order-service/src/test/java/com/demo/order/OrderServiceTest.java:14-28` | 桩返回 `CANCELLED` 订单并断言 `ship(1L)` 抛 `IllegalStateException`（测试即规格） |
| 代码 | `order-service/src/main/java/com/demo/order/service/OrderService.java:25-35` | `CANCELLED` 拒绝发货；非 `PAID` 拒绝发货；仅 `PAID` 写入 `SHIPPED` |
| 代码 | `order-service/src/main/java/com/demo/order/controller/OrderController.java:26-30` | `POST /api/order/{orderId}/ship` 调用 `OrderService#ship` |
| DDL 注释 | `db/init.sql:32` | 表注释声明状态迁移受 `OrderService` 状态机约束 |
| 用户权威输入 | `cadence/knowledge-base/user-input/product.md:15` | 关键特性包含订单管理（提供业务语境，不定义校验细节） |

## 5. 关联与例外

- 关联规则：RULE-order-status-transition（提供状态取值与完整迁移链）。
- 已知例外与未确认：`OrderService#ship` 读状态与写状态为两次独立操作，未使用 `@Transactional`、无乐观锁或条件更新，并发场景可能重复更新（Q-M11）；测试依赖未在 `pom.xml` 声明，规格当前不可执行（Q-H1）。

