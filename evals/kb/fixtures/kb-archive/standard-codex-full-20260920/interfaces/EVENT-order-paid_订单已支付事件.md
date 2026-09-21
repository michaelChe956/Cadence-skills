# EVENT-order-paid 订单已支付事件

> **能力 ID**：`EVENT-order-paid`
> **分类**：对内
> **能力类型**：消息（生产 + 消费）
> **数据来源**：工程扫描（`order-service` 消息代码、配置快照 `baseline-config-v1`）
> **梳理日期**：2026-09-20
> **参数与报文**：不适用（消息能力不生成配套参数与报文文件）

## 一、能力基础信息

| 项目 | 值 |
|------|----|
| 能力名称 | 订单已支付事件 |
| API 名称或逻辑标识 | 事件逻辑名 `order.paid`；交换机 `order.exchange`；路由键 `order.paid`；队列 `order.paid.queue` |
| 分类 | 对内（用户对外能力清单未登记） |
| 能力类型 | 消息 |
| 协议与方法 | AMQP（`RabbitTemplate.convertAndSend` / `@RabbitListener`） |
| 路径或逻辑地址 | exchange `order.exchange` → routing key `order.paid` → queue `order.paid.queue`（durable 声明） |
| 数据格式 | JSON 字符串（源码手工拼接，`{"orderId":<Long>}`） |
| 是否需授权 | 由 RabbitMQ 连接账号决定（`spring.rabbitmq.username`，值 `<redacted>`） |
| 版本 | 未提供（未发现版本或 schema 字段） |
| 生产者 | `SERVICE-order-service` / `MODULE-order-event`（`OrderEventProducer#sendOrderPaid`） |
| 消费者 | `SERVICE-order-service` / `MODULE-order-event`（`OrderEventListener#onOrderPaid`） |
| 生命周期状态 | 已实现、已装配；生产触发点代码存在但不可达（`OrderService#markPaid` 无调用方）；运行态 MQ 可达性与队列实际声明待确认 |

## 二、业务需求描述

- 订单支付成功后发布“已支付”领域事件，用于后续处理（通知、积分）（`OrderEventProducer.java:6`、`OrderEventListener.java:9`）。
- 业务处理语义在 fixture 中未实现（消费方法为空体），下游是否落库、是否通知外部系统：未提供。

## 三、输入参数

消息载荷输入模型：`{"orderId": <Long>}`（源码字符串拼接，非序列化框架）。

未发现消息头、租户字段、事件 ID、幂等键或版本字段（`OrderEventProducer.java:20`）。

## 四、输出参数

- 生产者输出：向 `order.exchange` 以 `order.paid` 路由键发送单条 JSON 字符串消息。
- 消费者输出：未发现（`onOrderPaid` 方法为空实现），无数据库写入、无外部调用、无二次消息。
- 业务响应：不适用（非请求响应能力）。

## 五、代码实现定位

### 5.1 用户清单与代码映射

| 来源 | 标识 | 结论 | 证据 |
|------|------|------|------|
| 用户对外能力清单 | 未登记（`api-scope.md` 无消息类能力） | 按规则归为对内能力 | `cadence/knowledge-base/user-input/api-scope.md:10-13` |
| 当前代码 | `OrderEventProducer` / `OrderEventListener` | 生产与消费均已实现并装配 | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java:8-21`、`mq/OrderEventListener.java:11-19` |

### 5.2 实现清单

| 层级 | 符号 | 文件路径 | 状态 | 说明 |
|------|------|----------|------|------|
| 生产者 | `com.demo.order.mq.OrderEventProducer#sendOrderPaid` | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java:19-21` | 已确认 | 常量 `EXCHANGE`/`ROUTING_KEY` 硬编码（非配置键） |
| 生产触发点 | `com.demo.order.service.OrderService#markPaid` | `order-service/src/main/java/com/demo/order/service/OrderService.java:38-41` | 代码存在但不可达 | 先更新状态为 `PAID` 再发送事件；全工程未发现调用方，也无 REST 入口 |
| 消费者 | `com.demo.order.mq.OrderEventListener#onOrderPaid` | `order-service/src/main/java/com/demo/order/mq/OrderEventListener.java:13-19` | 已确认（空实现） | `@RabbitListener` + `@QueueBinding` 声明 durable 队列 |
| 连接依赖 | `RabbitTemplate`（自动配置注入） | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java:13-17` | 已确认 | 由 `spring-boot-starter-amqp` 提供 |

## 六、调用链路

### 6.1 调用树

```text
EVENT-order-paid（order.exchange / order.paid → order.paid.queue）
├─ 生产：SERVICE-order-service / MODULE-order-event
│  └─ OrderService.markPaid（OrderService.java:38-41）[无调用方，不可达]
│     ├─ OrderMapper.updateStatus → TABLE-t_order.status（W，PAID）
│     └─ OrderEventProducer.sendOrderPaid（OrderEventProducer.java:19-21）
│        └─ RabbitTemplate.convertAndSend("order.exchange", "order.paid", payload)
├─ 消费：SERVICE-order-service / MODULE-order-event
│  └─ OrderEventListener.onOrderPaid（OrderEventListener.java:13-19）[空实现]
└─ CONFIGURATION CONFIGGROUP-order-rabbitmq
   └─ spring.rabbitmq.host/username/password → RabbitAutoConfiguration（值均 <redacted>）
```

### 6.2 分支与触发条件

| 条件 | 路径 | 结果 | 证据 |
|------|------|------|------|
| 通过 `OrderService#markPaid` 调用 | `markPaid` → `updateStatus(PAID)` → `sendOrderPaid` | 发送事件（无状态校验，未校验是否为 `CREATED`） | `OrderService.java:38-41` |
| 通过 `ship` 调用 | `ship` → `updateStatus(SHIPPED)` | 不发送事件（发货链路与事件链路无关联） | `OrderService.java:25-35` |
| 未发现任何 REST/任务/其他触发点调用 `markPaid` | - | 生产路径在当前代码中不可达（生产不可达，登记 Q-M10） | `order-service/src/main/java/com/demo/order/**` 全文未发现调用方 |
| 消息到达 `order.paid.queue` | `@RabbitListener` 绑定消费 | 空实现，无副作用 | `OrderEventListener.java:13-19` |

### 6.3 逐层调用明细

| 层级 | 符号 | 职责 | 下游 | 证据 |
|------|------|------|------|------|
| 业务触发 | `OrderService#markPaid(Long)` | 更新状态为 `PAID` 并发布事件 | `OrderMapper`、`OrderEventProducer` | `OrderService.java:38-41` |
| 生产者 | `OrderEventProducer#sendOrderPaid(Long)` | 拼接 JSON 并发送 | RabbitMQ exchange | `OrderEventProducer.java:19-21` |
| 消费者 | `OrderEventListener#onOrderPaid(String)` | 接收消息（空体） | 无 | `OrderEventListener.java:13-19` |
| 装配 | `@Component` + `@RabbitListener` | Bean 注册与队列绑定声明 | RabbitMQ | `OrderEventListener.java:10-16` |

## 七、数据模型与配置依赖

### 7.1 数据模型影响

| TABLE 稳定 ID | Schema/逻辑表 | 读写 | 涉及字段 | API 模型映射 | Mapper/DAO/SQL | 表字段证据状态 | 端到端映射状态 | 表文档链接 |
|---------------|---------------|------|----------|--------------|----------------|------------------|------------------|------------|
| TABLE-t_order | `DB-demo_order` / `t_order` | W（生产触发点内） | `status`（置为 `PAID`） | 消息字段 `orderId` → `WHERE order_id = #{orderId}`（显式） | `OrderMapper.xml#updateStatus`（`OrderMapper.xml:7-9`） | DDL 已确认（`db/init.sql:26-32`） | 已确认（仅覆盖生产触发点的状态写入；消费链路未发现数据访问） | [`TABLE-t_order`](../data-models/DB-demo_order/TABLE-t_order.md) |

> 消费侧未发现任何表访问；事件是否驱动账户、通知或积分数据变更无证据，不得据名称推断。

### 7.2 配置依赖

| 配置组稳定 ID | 服务配置实体 | 配置键 | 直接影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| CONFIGGROUP-order-rabbitmq | `CONFIG-SERVICE-order-service` | `spring.rabbitmq.host`、`spring.rabbitmq.username`、`spring.rabbitmq.password`（值均 `<redacted>`） | 中间件：决定事件能否收发 | 开发（default Profile） | RabbitAutoConfiguration 绑定 `RabbitTemplate`/`ConnectionFactory`；默认 profile 加载配置、`spring-boot-starter-amqp` 在类路径、MQ 可达 | 已确认（开发快照）；生产与运行态可达性待确认（Q-M6） | [`SERVICE-order-service`](../configurations/SERVICE-order-service.md) |
| 事件路由常量（非配置键） | `CONFIG-SERVICE-order-service` | 无配置键：`EXCHANGE`/`ROUTING_KEY`/队列名硬编码 | 路由：决定交换机、路由键与队列名 | - | 随代码发布生效 | 已确认（代码证据） | [`SERVICE-order-service`](../configurations/SERVICE-order-service.md) |

## 八、中间件使用明细

> 补充：授权快照 5 键中与消息相关者仅 `spring.rabbitmq.host/username/password`；未发现 `spring.rabbitmq.virtual-host`、发布确认、死信队列或重试相关配置键。

### 8.1 缓存与队列

| 类型 | 名称或 Key 模式 | 读写方向 | 触发时机 | 证据 |
|------|-----------------|----------|----------|------|
| 未发现 Redis 等队列式能力 | - | - | - | `order-service/pom.xml:13-18` 仅 AMQP |

### 8.2 消息

| Topic/Queue/Group | 方向 | 消息模型 | 重试与幂等 | 证据 |
|-------------------|------|----------|------------|------|
| exchange `order.exchange` / routing key `order.paid` | 生产 | `{"orderId": <Long>}` JSON 字符串 | 未发现重试、发布确认或幂等键；未发现消息 ID | `OrderEventProducer.java:10-11,19-21` |
| queue `order.paid.queue`（durable） | 消费 | 同上（反序列化为 `String`） | 未发现死信队列、重试策略、ack 模式或幂等处理 | `OrderEventListener.java:13-19` |

### 8.3 搜索与本地缓存

未发现。

### 8.4 RPC 与下游 HTTP

| 服务 | 协议 | 版本或分组 | 触发条件 | 证据 |
|------|------|------------|----------|------|
| 未发现 | - | - | - | 未发现 Feign/RestTemplate/WebClient/RPC 依赖或调用代码 |

### 8.5 文件与对象存储

| 协议或存储 | 逻辑位置 | 文件格式 | 触发方 | 接收方 | 证据 |
|------------|----------|----------|--------|--------|------|
| 未发现 | - | - | - | - | `mq/**` 无文件读写 |

### 8.6 定时任务与批处理

| 任务 | 触发方式 | 并发与锁 | 重试与补偿 | 证据 |
|------|----------|----------|------------|------|
| 未发现（本能力不涉及调度） | - | - | - | `order-service/src/main/java/com/demo/order/**` 无 `@Scheduled` |

## 九、数据源与副作用分析

- 主数据来源：生产触发点读写的 `DB-demo_order`.`t_order`（`status` 更新为 `PAID`）；消息中间件为 `MIDDLEWARE-rabbitmq`。
- 实时查询或补充路径：无。
- 写入、副作用或异步结果：向 MQ 发送一条消息；消费侧无副作用（空实现）。
- 事务、一致性和失败处理：`markPaid` 未使用 `@Transactional`，状态更新与消息发送非原子（更新成功但发送失败会造成状态与事件不一致）；未发现本地消息表、重试、补偿或发布确认机制。

## 十、关键证据引用

| 引用 | 文件或资料位置 |
|------|----------------|
| 用户对外能力清单（未登记本能力） | `cadence/knowledge-base/user-input/api-scope.md:10-13` |
| 生产者定义 | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java:10-11,19-21` |
| 生产触发点 | `order-service/src/main/java/com/demo/order/service/OrderService.java:38-41` |
| 消费者与队列绑定 | `order-service/src/main/java/com/demo/order/mq/OrderEventListener.java:13-19` |
| 数据访问 | `TABLE-t_order`、`data-models/DB-demo_order/TABLE-t_order.md`、`order-service/src/main/resources/mapper/OrderMapper.xml:7-9` |
| 配置依赖 | `CONFIG-SERVICE-order-service`、`spring.rabbitmq.*`、`configurations/SERVICE-order-service.md` |
| 中间件 | `order-service/pom.xml:17`、`configurations/README.md`（MIDDLEWARE-rabbitmq） |

## 十一、请求、响应或载荷示例

```json
{"orderId":1}
```

> 该载荷为源码字符串拼接结果（`OrderEventProducer.java:20`）；未发现消息头、事件 ID、时间戳或版本字段。无响应载荷（消息能力）。
