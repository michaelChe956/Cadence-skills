# 订单状态迁移链

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 规则稳定 ID | RULE-order-status-transition |
| 条目状态 | ai-draft |
| 规则类型 | 状态迁移 |
| 来源 | 代码与 DDL 注释（完整链路无用户权威输入与测试断言覆盖） |

## 2. 规则陈述

订单状态取值为 `CREATED`、`PAID`、`SHIPPED`、`COMPLETED`、`CANCELLED`，迁移链为 `CREATED → PAID → SHIPPED → COMPLETED`，任意非终态可迁移到 `CANCELLED`。

## 3. 适用范围

| 实体稳定 ID | 关系说明 |
|------------|----------|
| TABLE-t_order | `status` 字段承载状态取值 |
| MODULE-order-core | 状态枚举与迁移实现所在模块 |
| FLOW-order-ship | 使用 `PAID → SHIPPED` 迁移 |
| FLOW-order-paid-event | 使用 `CREATED → PAID` 迁移并触发事件 |
| API-order-ship | 发货接口只在 `PAID` 状态下允许迁移 |

## 4. 证据

| 证据类型 | 位置 | 说明 |
|----------|------|------|
| 代码 | `order-service/src/main/java/com/demo/order/entity/OrderStatus.java:3-9` | 类注释声明迁移链，枚举定义 5 个状态 |
| 代码 | `order-service/src/main/java/com/demo/order/service/OrderService.java:37-41` | `markPaid` 写入 `PAID` |
| 代码 | `order-service/src/main/java/com/demo/order/service/OrderService.java:25-35` | `PAID → SHIPPED` 分支及拒绝分支 |
| DDL 注释 | `db/init.sql:29,32` | 列注释列出 5 个状态取值；表注释声明迁移受 `OrderService` 约束 |

## 5. 关联与例外

- 关联规则：RULE-order-ship-constraint（`PAID → SHIPPED` 的具体约束）。
- 已知例外与未确认：`COMPLETED`、`CANCELLED` 的迁移实现、触发入口与校验均未在代码中发现，也没有建单路径（Q-M4）；该完整迁移链只有枚举与注释证据，条目状态为 `ai-draft`，登记待确认 Q-L9。

