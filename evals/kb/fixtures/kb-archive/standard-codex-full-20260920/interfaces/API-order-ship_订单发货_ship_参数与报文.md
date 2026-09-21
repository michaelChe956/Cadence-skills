# API-order-ship 订单发货接口 - 参数与报文

> **主文件**：`API-order-ship_订单发货_ship.md`
> **能力 ID**：`API-order-ship`
> **分类**：对内
> **HTTP 方法与路径**：`POST /api/order/{orderId}/ship`
> **数据来源**：`OrderController`、`OrderService`、`OrderStatus`、`OrderMapper.xml`、`db/init.sql`

## 一、输入参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| `orderId` | 路径 | 是 | Long | BIGINT，十进制整数 | 订单号，对应 `t_order.order_id` | `OrderController.java:18`、`OrderMapper.xml:8`、`db/init.sql:27` |
| （请求头/请求体） | - | - | - | - | 未发现鉴权头、幂等键或请求体解析；无请求体 | `OrderController.java:17-21`；未发现安全依赖 |

未发现物流单号、承运商、操作人等业务入参。

## 二、输出参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| 响应体 | 根 | 是 | String | 固定字面量 `ok` | 无订单状态、时间戳或业务结果字段 | `OrderController.java:20` |

## 三、请求报文示例

```http
POST /api/order/1/ship HTTP/1.1
Host: localhost:8083
Content-Length: 0
```

前端调用形态：`request.post('/order/${orderId}/ship')`（`web-portal/src/api/index.js:4`）。

## 四、响应报文示例

```text
ok
```

> 该值为源码字面量（`OrderController.java:20`），不反映实际状态迁移结果；调用方需另行查询订单状态（本阶段未发现查单接口）。

## 五、错误或异常载荷

| 错误码或类型 | 触发条件 | 含义 | 来源 |
|--------------|----------|------|------|
| `IllegalStateException`（消息：已取消订单不可发货） | 当前状态为 `CANCELLED` | 状态机拒绝发货；未发现统一异常处理，按框架默认返回 500（待确认） | `OrderService.java:28-30` |
| `IllegalStateException`（消息：仅已支付订单可发货） | 当前状态为 `CREATED`/`SHIPPED`/`COMPLETED` | 状态机拒绝发货；同上 | `OrderService.java:31-33` |
| `NullPointerException` | `orderId` 不存在（`selectById` 返回 `null`） | 未发现空值校验，异常按框架默认返回 500（待确认） | `OrderService.java:26-27` |
| 400（框架默认，待确认） | `orderId` 非数字 | 参数格式错误 | 待确认（无自定义处理证据） |
| 未提供（未发现统一错误码定义） | - | 未发现 `@ControllerAdvice` 或错误码枚举 | `order-service/src/main/java/com/demo/order/**` |
