# order-service

## 职责与边界

- 稳定 ID：`SERVICE-order-service`；类型：Java 后端（Spring Boot 3.2.5 + MyBatis + Spring AMQP，Java 17）。
- 职责：订单状态机与读写、订单导出、订单已支付事件的生产与消费 [代码证据]（`order-service/src/main/java/com/demo/order/service/OrderService.java:9-41`）。
- 边界内：`t_order` 读与状态更新、导出接口与非持久化导出服务、`order.exchange`/`order.paid` 事件收发。
- 边界外：用户基本信息与账户信息；跨服务聚合逻辑未见实现。
- 数据写入：`t_order`（`updateStatus`）；`t_export_file` 未发现读写调用（Q-M4）。

## 模块与入口

| 模块 ID | 职责 | 关键类或文件 | 证据 |
|---------|------|--------------|------|
| MODULE-order-core | 订单状态机与读写 | `OrderController`、`OrderService`、`OrderMapper`、`OrderEntity`、`OrderStatus` | `order-service/src/main/java/com/demo/order/{controller,service,mapper,entity}` |
| MODULE-order-export | 订单导出接口与导出服务 | `ExportController`、`ExportService` | `order-service/src/main/java/com/demo/order/controller/ExportController.java:5-13`、`service/ExportService.java:5-11` |
| MODULE-order-event | 事件生产与消费 | `OrderEventProducer`、`OrderEventListener` | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java:10-21`、`OrderEventListener.java:11-19` |

| 入口类型 | 入口 | 说明 | 证据 |
|----------|------|------|------|
| 进程入口 | `com.demo.order.OrderApplication` | 启动类，组件扫描 `com.demo.order` | `order-service/src/main/java/com/demo/order/OrderApplication.java:8-11` |
| HTTP 入口 | `POST /api/order/{orderId}/ship` | 触发状态机发货，非法状态抛 `IllegalStateException` | `order-service/src/main/java/com/demo/order/controller/OrderController.java:17-21` |
| HTTP 入口 | `POST /api/order/export` | 返回 `taskId` 字符串（fixture 静态实现） | `order-service/src/main/java/com/demo/order/controller/ExportController.java:10-13` |
| 消息生产 | `order.exchange` / 路由键 `order.paid` | `OrderService.markPaid` 调用 `sendOrderPaid` | `OrderEventProducer.java:10-21`、`OrderService.java:38-41` |
| 消息消费 | 队列 `order.paid.queue`（durable） | `@RabbitListener` 绑定交换与路由键 | `OrderEventListener.java:13-19` |
| 监听端口 | `server.port` 配置键 | 端口值非敏感，记录于配置文档 | `order-service/src/main/resources/application.yml:1-2` |

## 数据模型

| 逻辑表稳定 ID | 数据库/Schema | 读/写 | 映射入口 | 证据 |
|----------------|---------------|-------|----------|------|
| TABLE-t_order | DB-demo_order | 读、写 | `OrderMapper.selectById`、`OrderMapper.updateStatus` | `order-service/src/main/resources/mapper/OrderMapper.xml:4-9` |
| TABLE-t_export_file | DB-demo_order | 未发现 | 未发现 Mapper 或 SQL | `db/init.sql:22-28`（仅 DDL） |

- 详细字段清单：`data-models/DB-demo_order/TABLE-t_order.md`、`data-models/DB-demo_order/TABLE-t_export_file.md`
- 状态机业务规则：CREATED → PAID → SHIPPED → COMPLETED，任意非终态 → CANCELLED；已取消订单不可发货 [代码证据 + 测试规格]（`entity/OrderStatus.java:3-9`、`service/OrderService.java:21-35`、`src/test/java/com/demo/order/OrderServiceTest.java:14-28`）。

## 配置

- 配置状态：`全量`（已纳入本服务）。
- 来源：`src/main/resources/application.yml`（键数与清单见 `configurations/SERVICE-order-service.md`）。
- 配置组：`CONFIGGROUP-order-server`、`CONFIGGROUP-order-datasource`、`CONFIGGROUP-order-rabbitmq`。
- 未发现 profile 专用配置或外部覆盖；敏感值统一 `<redacted>`（含内部主机名与认证信息）。

## 中间件

| 中间件 ID | 装配状态 | 证据 |
|------------|----------|------|
| MIDDLEWARE-mysql | 已装配（开发 fixture 快照；生产装配未确认） | `order-service/pom.xml:16`、数据源配置键、`OrderMapper.xml` |
| MIDDLEWARE-rabbitmq | 已装配（代码与配置证据；生产装配未确认） | `order-service/pom.xml:17`、`spring.rabbitmq.*` 键、`OrderEventProducer.java:19-21`、`OrderEventListener.java:13-19` |

## API

- 阶段状态：已分析（api）
- API 导航：

| API 稳定 ID | 能力名称 | 分类 | 类型 | 状态 | 主文件 | 参数与报文 |
|-------------|----------|------|------|------|--------|------------|
| `API-order-export` | 订单导出 | 对外 | REST | 已声明、已实现（存根）、已装配、已暴露（端到端链路未实现，Q-H2） | [`API-order-export_订单导出_export.md`](../interfaces/API-order-export_订单导出_export.md) | [`参数与报文`](../interfaces/API-order-export_订单导出_export_参数与报文.md) |
| `API-order-ship` | 订单发货接口 | 对内 | REST | 已实现、已装配、已暴露 | [`API-order-ship_订单发货_ship.md`](../interfaces/API-order-ship_订单发货_ship.md) | [`参数与报文`](../interfaces/API-order-ship_订单发货_ship_参数与报文.md) |
| `EVENT-order-paid` | 订单已支付事件 | 对内 | 消息 | 已实现、已装配；生产触发点不可达（Q-M10） | [`EVENT-order-paid_订单已支付事件.md`](../interfaces/EVENT-order-paid_订单已支付事件.md) | 不适用（消息能力不生成配套文件） |
| `FILE-order-export-file` | 订单导出文件 | 对内 | 文件 | 状态未知（无文件实现，Q-M4） | [`FILE-order-export-file_订单导出文件.md`](../interfaces/FILE-order-export-file_订单导出文件.md) | 不适用（文件能力不生成配套文件） |

- 证据：`order-service/src/main/java/com/demo/order/controller/ExportController.java:10-13`、`controller/OrderController.java:17-21`、`service/OrderService.java:25-41`、`mq/**`、`service/ExportService.java:9-10`；总索引 `interfaces/README.md`。

## 页面

- 阶段状态：已分析（pages）
- 页面导航（消费本服务 API 的页面；页面由 `SERVICE-web-portal` 承载）：

| PAGE 稳定 ID | ROUTE 稳定 ID | 路由路径 | 页面主文件 | 关系证据 |
|--------------|---------------|----------|------------|----------|
| `PAGE-order-manage` | `ROUTE-web-portal-orders` | `/orders` | [`PAGE-order-manage`](../pages/PAGE-order-manage.md) | 页面 → `API-order-ship` → `MODULE-order-core`；页面 → `API-order-export` → `MODULE-order-export`（`web-portal/src/views/OrderPage.vue:10-11`、`web-portal/src/api/index.js:4`） |

- 说明：本服务不承载前端页面；`EVENT-order-paid`、`FILE-order-export-file` 无页面调用证据，未建立页面导航。
- 证据：`web-portal/src/main.js:5,12`、`web-portal/src/views/OrderPage.vue:1-12`；页面索引 `pages/README.md`。

## 横切机制

| 机制 | 状态 | 证据 |
|------|------|------|
| 注解驱动消息调用 | 已确认（代码 + 配置键） | `OrderEventListener.java:13-19`、`OrderEventProducer.java:19-21` |
| 订单状态机约束 | 已确认（代码 + 测试规格） | `OrderService.java:25-35`、`OrderServiceTest.java:14-28` |
| 全局异常处理 | 未发现（无 `@ControllerAdvice`），非法状态以 `IllegalStateException` 直接抛出 | `OrderService.java:28-33` |
| 事务边界 | 未发现（无 `@Transactional`；状态更新与事件发布之间无事务包装） | `OrderService.java:37-41` |
| 认证/授权 | 未发现 | `order-service/pom.xml:13-18` |
| 可观测性 | 未发现 | 同上 |

## 构建验证

| 场景 | 命令 | 状态 | 来源 |
|------|------|------|------|
| 构建 | `mvn -f order-service/pom.xml package` | 未执行（只读分析；Maven 依赖需联网解析） | `order-service/pom.xml` |
| 测试 | `mvn -f order-service/pom.xml test`（JUnit 5 规格 `OrderServiceTest`） | 未执行且依赖未声明（Q-H1：三个 `pom.xml` 均未声明测试依赖） | `order-service/src/test/java/com/demo/order/OrderServiceTest.java:8` |
| 启动 | 未确认（未声明 `spring-boot-maven-plugin`，无启动脚本） | 待确认 | `order-service/pom.xml:13-18` |

## 证据导航

- 入口与装配：`order-service/src/main/java/com/demo/order/OrderApplication.java`
- 状态机：`order-service/src/main/java/com/demo/order/service/OrderService.java:21-41`、`entity/OrderStatus.java:3-9`
- 导出：`order-service/src/main/java/com/demo/order/controller/ExportController.java`、`service/ExportService.java:9-10`
- 事件：`order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java`、`OrderEventListener.java`
- 数据访问：`order-service/src/main/resources/mapper/OrderMapper.xml`
- 测试规格：`order-service/src/test/java/com/demo/order/OrderServiceTest.java`
- 配置：`order-service/src/main/resources/application.yml`
- 相关文档：`services/README.md`、`data-models/DB-demo_order/README.md`、`configurations/SERVICE-order-service.md`
