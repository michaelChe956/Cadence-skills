# 订单发货流程

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 流程稳定 ID | FLOW-order-ship |
| 条目状态 | confirmed |
| 来源 | 用户资料（`user-input/product.md:15` 关键特性“订单管理”）+ 测试断言、接口与代码证据 |

## 2. 目的与边界

运营人员在订单管理页对已支付订单执行发货，将订单状态由 `PAID` 流转为 `SHIPPED`。不覆盖：创建订单、支付回调、完成与取消（未发现实现，Q-M4）；不覆盖并发控制与事务边界（未实现，Q-M11）。

## 3. 步骤链

| 步骤 | 实体稳定 ID | 证据（文件:行号） | 说明 |
|------|-------------|-------------------|------|
| 1 | PAGE-order-manage | `web-portal/src/views/OrderPage.vue:4,10` | 点击“发货”按钮触发 `shipOrder(1)`；`orderId` 为硬编码常量（Q-L7） |
| 2 | ROUTE-web-portal-orders | `web-portal/src/main.js:5,12` | `/orders` 静态路由装配到 `views/OrderPage.vue` |
| 3 | MODULE-web-portal-api | `web-portal/src/api/index.js:4`、`web-portal/src/api/request.js:3` | axios 实例拼接 `POST /order/{orderId}/ship` |
| 4 | API-order-ship | `order-service/src/main/java/com/demo/order/controller/OrderController.java:26-30` | `POST /api/order/{orderId}/ship` → `OrderService#ship` |
| 5 | MODULE-order-core | `order-service/src/main/java/com/demo/order/service/OrderService.java:25-35` | 读状态 → 状态机校验（`CANCELLED` 与非 `PAID` 拒绝）→ 更新状态；承载 RULE-order-ship-constraint |
| 6 | TABLE-t_order | `order-service/src/main/resources/mapper/OrderMapper.xml:4-6`（读）、`:7-9`（写） | `SELECT order_id, user_id, status, amount FROM t_order WHERE order_id = #{orderId}`；`UPDATE t_order SET status = #{status} WHERE order_id = #{orderId}` |
| 7 | CONFIGGROUP-order-server / MIDDLEWARE-mysql / DB-demo_order | `order-service/src/main/resources/application.yml:1-5`、`order-service/pom.xml:16` | 服务端口与应用名键存在；未发现 `spring.datasource.*` 键（Q-M6）；MySQL 驱动已声明 |

```text
PAGE-order-manage → ROUTE-web-portal-orders → API-order-ship
→ SERVICE-order-service/MODULE-order-core → TABLE-t_order
→ CONFIGGROUP-order-server/MIDDLEWARE-mysql
```

## 4. 状态流转

| 状态迁移 | 触发条件 | 证据（文件:行号） |
|----------|----------|-------------------|
| `PAID → SHIPPED` | 发货请求且当前状态为 `PAID` | `order-service/src/main/java/com/demo/order/service/OrderService.java:31-34` |
| 拒绝发货（`CANCELLED`） | 当前状态为 `CANCELLED` | `order-service/src/main/java/com/demo/order/service/OrderService.java:28-30`；测试 `order-service/src/test/java/com/demo/order/OrderServiceTest.java:14-28` |
| 拒绝发货（其他非 `PAID`） | 当前状态为 `CREATED`、`SHIPPED`、`COMPLETED` | `order-service/src/main/java/com/demo/order/service/OrderService.java:31-33` |

## 5. 关联规则

| 规则稳定 ID | 关系说明 |
|-------------|----------|
| RULE-order-ship-constraint | 本流程第 5 步实现的状态迁移约束 |
| RULE-order-status-transition | 提供状态取值与完整迁移链定义 |

## 6. 失败处理与异步边界

- 状态不合法时抛 `IllegalStateException`，由框架返回默认错误响应，未定义业务错误码；接口无 `@Transactional`，读状态与写状态为两次独立操作，无乐观锁或条件更新（Q-M11）。
- 同步 HTTP 调用；本流程不发布 `EVENT-order-paid`（该事件仅由 `OrderService#markPaid` 触发，且触发点不可达，Q-M10）。
- 页面无错误提示与重试逻辑（`web-portal/src/views/OrderPage.vue:9-11`）。

