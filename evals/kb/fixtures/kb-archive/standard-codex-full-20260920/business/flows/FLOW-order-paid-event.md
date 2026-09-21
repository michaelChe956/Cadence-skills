# 订单已支付事件处理流程

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 流程稳定 ID | FLOW-order-paid-event |
| 条目状态 | ai-draft |
| 来源 | 代码与配置证据（用户资料未描述事件流程） |

## 2. 目的与边界

订单支付成功后发布 `order.paid` 事件，由同一服务的监听器消费以完成支付后处理（通知、积分）。不覆盖：支付本身（支付渠道与回调入口均未发现）；不覆盖事件重试、死信与幂等策略（未实现）。

## 3. 步骤链

| 步骤 | 实体稳定 ID | 证据（文件:行号） | 说明 |
|------|-------------|-------------------|------|
| 1 | PAGE 不适用（无触发页面与 REST 入口） | `order-service/src/main/java/com/demo/order/service/OrderService.java:38-41` | `markPaid` 无调用方，全工程无支付回调入口（Q-M10） |
| 2 | API（事件旁路节点）EVENT-order-paid | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java:10-21` | `order.exchange` + routing key `order.paid`，消息体为 `{"orderId":N}` 字符串拼接 |
| 3 | MODULE-order-core | `order-service/src/main/java/com/demo/order/service/OrderService.java:37-41` | 先更新 `status = PAID`，再发送事件（无事务包裹） |
| 4 | TABLE-t_order | `order-service/src/main/resources/mapper/OrderMapper.xml:7-9` | `UPDATE t_order SET status = #{status} WHERE order_id = #{orderId}` |
| 5 | MODULE-order-event（消费者） | `order-service/src/main/java/com/demo/order/mq/OrderEventListener.java:31-41` | `@RabbitListener` 绑定 `order.paid.queue`（durable）；方法体为空实现 |
| 6 | MIDDLEWARE-rabbitmq / CONFIGGROUP-order-rabbitmq | `order-service/src/main/resources/application.yml:6-9`、`order-service/pom.xml:17` | 连接键存在（值 `<redacted>`）；未发现 exchange/queue 配置键（名称硬编码于代码常量） |

```text
PAGE（不适用，无入口）→ EVENT-order-paid → SERVICE-order-service/MODULE-order-core 与 MODULE-order-event
→ TABLE-t_order → CONFIGGROUP-order-rabbitmq/MIDDLEWARE-rabbitmq
```

## 4. 状态流转

| 状态迁移 | 触发条件 | 证据（文件:行号） |
|----------|----------|-------------------|
| `CREATED → PAID` | 调用 `OrderService#markPaid`（当前无调用方，不可达） | `order-service/src/main/java/com/demo/order/service/OrderService.java:37-41`；Q-M10 |

## 5. 关联规则

| 规则稳定 ID | 关系说明 |
|-------------|----------|
| RULE-order-status-transition | 本流程实现 `CREATED → PAID` 迁移片段 |

## 6. 失败处理与异步边界

- 异步边界：`RabbitTemplate.convertAndSend` 发送、`@RabbitListener` 消费，两者在同一服务内；未发现重试、死信队列、幂等键与消费失败处理。
- 事务边界：状态更新与事件发送无事务与补偿，更新成功而发送失败时状态与事件可能不一致。
- 生产触发点不可达（`markPaid` 无调用方）；消费方法为空实现，事件暂无业务效果（Q-M10）。
- 运行态 MQ 可达性、队列预声明与消息格式兼容性无运行证据（Q-M6）。

