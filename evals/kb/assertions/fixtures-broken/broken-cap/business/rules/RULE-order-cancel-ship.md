# 已取消订单不可发货

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 规则稳定 ID | RULE-order-cancel-ship |
| 条目状态 | ai-draft |
| 规则类型 | 状态迁移 |
| 来源 | 测试断言 |

## 2. 规则陈述

已取消（CANCELLED）订单不可发货。

## 4. 证据

| 证据类型 | 位置 |
|----------|------|
| 测试 | order-service/src/test/java/com/demo/order/OrderServiceTest.java:21 |
