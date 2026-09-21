# API-order-ship 订单发货接口（对内 REST）

> **能力 ID**：`API-order-ship`
> **分类**：对内
> **能力类型**：REST
> **数据来源**：工程扫描（`order-service` 代码、测试规格、`db/init.sql`、配置快照）
> **梳理日期**：2026-09-20
> **参数与报文**：见同目录 `API-order-ship_订单发货_ship_参数与报文.md`

## 一、能力基础信息

| 项目 | 值 |
|------|----|
| 能力名称 | 订单发货接口 |
| API 名称或逻辑标识 | `ship` |
| 分类 | 对内（用户对外能力清单未登记） |
| 能力类型 | REST |
| 协议与方法 | HTTP POST |
| 路径或逻辑地址 | `/api/order/{orderId}/ship` |
| 数据格式 | 未声明（返回 `String` 字面量） |
| 是否需授权 | 未发现鉴权实现（无 Spring Security 依赖、无过滤器） |
| 版本 | 未提供（代码未声明版本） |
| 调用方或生产者 | `web-portal` 订单管理页（`web-portal/src/api/index.js:4`、`web-portal/src/views/OrderPage.vue:10`） |
| 落地方或消费者 | `SERVICE-order-service`（`MODULE-order-core`） |
| 生命周期状态 | 已实现、已装配、已暴露 |
| 数据来源表 | `TABLE-t_order`（读 + 写） |

### 调用入口

| 环境 | 地址 | 证据状态 |
|------|------|----------|
| 开发（fixture 快照） | `http://localhost:8083/api/order/{orderId}/ship`（端口取 `server.port` 键，非敏感） | `order-service/src/main/resources/application.yml:1-2` |
| 生产 | 未提供（未发现网关或域名配置） | 待确认 |
| 前端访问路径 | `/api/order/{orderId}/ship`（合并 axios `baseURL: /api` 后） | `web-portal/src/api/index.js:4`，代理目标见 Q-L4 |

## 二、业务需求描述

- 承运发货业务动作：仅已支付订单可流转为已发货（`OrderService.java:21-35`）。
- 状态机：`CREATED → PAID → SHIPPED → COMPLETED`，任意非终态 → `CANCELLED`（`OrderStatus.java:3-9`）；已取消订单不可发货（`OrderService.java:28-30`）；规则卡 `business/rules/RULE-order-ship-constraint.md`、`business/rules/RULE-order-status-transition.md`。
- 行为规格由测试固化：`OrderServiceTest#cancelledOrderCannotShip` 断言已取消订单发货抛 `IllegalStateException`（`order-service/src/test/java/com/demo/order/OrderServiceTest.java:14-28`），但测试依赖未在 `pom.xml` 声明（Q-H1）。
- 未发现发货所需物流单号、承运商、幂等键等业务入参。
- 本接口不发布消息；`OrderService.markPaid`（发布 `order.paid` 事件）无任何调用方（见 `EVENT-order-paid` 能力文档）。

## 三、输入参数

详见 `API-order-ship_订单发货_ship_参数与报文.md` 第一节（路径参数 `orderId`）。

## 四、输出参数

详见 `API-order-ship_订单发货_ship_参数与报文.md` 第二节（字面量 `ok`）。

## 五、代码实现定位

### 5.1 用户清单与代码映射

| 来源 | 标识 | 结论 | 证据 |
|------|------|------|------|
| 用户对外能力清单 | 未登记（`api-scope.md` 仅登记 2 条对外能力） | 按规则归为对内能力 | `cadence/knowledge-base/user-input/api-scope.md:10-13` |
| 当前代码 | `OrderController#ship` | 实现已定位，写入 `t_order.status` | `order-service/src/main/java/com/demo/order/controller/OrderController.java:17-21` |

### 5.2 实现清单

| 层级 | 符号 | 文件路径 | 状态 | 说明 |
|------|------|----------|------|------|
| 入口 | `com.demo.order.controller.OrderController#ship` | `order-service/src/main/java/com/demo/order/controller/OrderController.java:17-21` | 已确认 | `@PostMapping("/{orderId}/ship")`，返回固定字符串 `ok` |
| 业务（状态机） | `com.demo.order.service.OrderService#ship` | `order-service/src/main/java/com/demo/order/service/OrderService.java:25-35` | 已确认 | 读状态 → 校验 → 更新状态 |
| 状态枚举 | `com.demo.order.entity.OrderStatus` | `order-service/src/main/java/com/demo/order/entity/OrderStatus.java:4-9` | 已确认 | `CREATED`/`PAID`/`SHIPPED`/`COMPLETED`/`CANCELLED` |
| 数据访问 | `com.demo.order.mapper.OrderMapper#selectById` / `#updateStatus` | `order-service/src/main/java/com/demo/order/mapper/OrderMapper.java:10-11` | 已确认 | 读 + 写 |
| SQL | `OrderMapper.xml#selectById` / `#updateStatus` | `order-service/src/main/resources/mapper/OrderMapper.xml:4-9` | 已确认 | 显式列与 `AS` 别名 |
| 测试规格 | `OrderServiceTest#cancelledOrderCannotShip` | `order-service/src/test/java/com/demo/order/OrderServiceTest.java:14-28` | 来源冲突 | 测试依赖未声明（Q-H1），规格不可执行性待确认 |

## 六、调用链路

### 6.1 调用树

```text
API-order-ship（POST /api/order/{orderId}/ship）
└─ SERVICE-order-service / MODULE-order-core
   ├─ OrderController.ship（OrderController.java:17-21）
   │  └─ OrderService.ship（OrderService.java:25-35）
   │     ├─ OrderMapper.selectById → OrderMapper.xml#selectById（读 t_order）
   │     ├─ OrderStatus.valueOf(order.getStatus())（状态机校验）
   │     └─ OrderMapper.updateStatus → OrderMapper.xml#updateStatus（写 t_order.status）
   ├─ TABLE-t_order
   │  ├─ R：order_id（条件）、order_id/user_id/status/amount（读取）
   │  └─ W：status = SHIPPED（WHERE order_id）
   └─ CONFIGURATION CONFIGGROUP-order-server
      └─ server.port → 暴露端口（Spring Boot 内置绑定）
```

### 6.2 分支与触发条件

| 条件 | 路径 | 结果 | 证据 |
|------|------|------|------|
| 订单不存在（`selectById` 返回 `null`） | `OrderService.ship` 第 27 行 `order.getStatus()` | `NullPointerException`（未发现空值校验） | `OrderService.java:26-27` |
| 当前状态为 `CANCELLED` | `ship` → `throw IllegalStateException("已取消订单不可发货")` | 不写库，异常上抛 | `OrderService.java:28-30`、`OrderServiceTest.java:14-28` |
| 当前状态为 `CREATED`/`SHIPPED`/`COMPLETED` | `ship` → `throw IllegalStateException("仅已支付订单可发货")` | 不写库，异常上抛 | `OrderService.java:31-33` |
| 当前状态为 `PAID` | `ship` → `updateStatus(orderId, "SHIPPED")` | 状态更新为已发货，返回 `ok` | `OrderService.java:34`、`OrderMapper.xml:7-9` |

### 6.3 逐层调用明细

| 层级 | 符号 | 职责 | 下游 | 证据 |
|------|------|------|------|------|
| REST 入口 | `OrderController#ship(Long)` | 绑定路径变量，调用业务并返回 `ok` | `OrderService` | `OrderController.java:17-21` |
| 业务 | `OrderService#ship(Long)` | 状态机校验与状态更新 | `OrderMapper` | `OrderService.java:25-35` |
| 数据访问 | `OrderMapper#selectById` / `#updateStatus` | 读取与更新订单 | `OrderMapper.xml` | `OrderMapper.java:10-11` |
| SQL | `OrderMapper.xml#selectById` / `#updateStatus` | 按主键查询与更新状态 | `TABLE-t_order` | `OrderMapper.xml:4-9` |
| 装配 | `@SpringBootApplication` 组件扫描 `com.demo.order` | Controller/Service/Mapper 装配 | `SERVICE-order-service` | `OrderApplication.java:7-11` |

## 七、数据模型与配置依赖

### 7.1 数据模型影响

| TABLE 稳定 ID | Schema/逻辑表 | 读写 | 涉及字段 | API 模型映射 | Mapper/DAO/SQL | 表字段证据状态 | 端到端映射状态 | 表文档链接 |
|---------------|---------------|------|----------|--------------|----------------|------------------|------------------|------------|
| TABLE-t_order | `DB-demo_order` / `t_order` | R + W | R：`order_id`（条件）、`order_id`、`user_id`、`status`、`amount`；W：`status`（`SHIPPED`） | 请求 `orderId` → `WHERE order_id = #{orderId}`（显式）；响应无实体字段（返回字面量 `ok`）；读取 `status` → `OrderStatus.valueOf` | `OrderMapper.xml#selectById`、`#updateStatus`（`OrderMapper.xml:4-9`）、`OrderEntity` | DDL 已确认（`db/init.sql:26-32`） | 已确认（请求条件、读取列与写入列均有显式 SQL 证据；响应无模型映射需求） | [`TABLE-t_order`](../data-models/DB-demo_order/TABLE-t_order.md) |

> 本能力不读取或写入 `t_export_file`；导出登记链路见 `API-order-export` 与 `FILE-order-export-file`（Q-M4）。

### 7.2 配置依赖

| 配置组稳定 ID | 服务配置实体 | 配置键 | 直接影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| CONFIGGROUP-order-server | `CONFIG-SERVICE-order-service` | `server.port` | 路由/监听：决定该路径的暴露端口 | 开发（default Profile） | Spring Boot 内置属性绑定 | 已确认 | [`SERVICE-order-service`](../configurations/SERVICE-order-service.md) |
| CONFIGGROUP-order-datasource | `CONFIG-SERVICE-order-service` | `spring.datasource.*` | 数据源/中间件：本能力实际读写 `t_order`，但授权快照中该配置组状态为“缺失” | 开发（default Profile） | 无法确认：`order-service/application.yml` 无数据源键，`pom.xml:16` 声明 MySQL 驱动，`OrderMapper.xml` 直接查询 `t_order` | 待确认（Q-M6） | [`SERVICE-order-service`](../configurations/SERVICE-order-service.md) |

> `CONFIGGROUP-order-rabbitmq` 只影响事件收发链路（`MODULE-order-event`），对发货接口无直接行为影响，不纳入本节。

## 八、中间件使用明细

### 8.1 缓存与队列

| 类型 | 名称或 Key 模式 | 读写方向 | 触发时机 | 证据 |
|------|-----------------|----------|----------|------|
| 未发现 | - | - | - | `order-service/pom.xml:13-18` 无缓存/队列依赖 |

### 8.2 消息

| Topic/Queue/Group | 方向 | 消息模型 | 重试与幂等 | 证据 |
|-------------------|------|----------|------------|------|
| 未发现（发货接口不发布事件） | - | - | - | `OrderService.java:25-35`、`interfaces/EVENT-order-paid_订单已支付事件.md` |

### 8.3 搜索与本地缓存

未发现。

### 8.4 RPC 与下游 HTTP

| 服务 | 协议 | 版本或分组 | 触发条件 | 证据 |
|------|------|------------|----------|------|
| 未发现 | - | - | - | 未发现 Feign/RestTemplate/WebClient/RPC 依赖或调用代码 |

### 8.5 文件与对象存储

| 协议或存储 | 逻辑位置 | 文件格式 | 触发方 | 接收方 | 证据 |
|------------|----------|----------|--------|--------|------|
| 未发现 | - | - | - | - | `OrderController.java:17-21`、`OrderService.java:25-35` 无文件读写 |

### 8.6 定时任务与批处理

| 任务 | 触发方式 | 并发与锁 | 重试与补偿 | 证据 |
|------|----------|----------|------------|------|
| 未发现（本服务无调度代码） | - | - | - | `order-service/src/main/java/com/demo/order/**` 无 `@Scheduled`；对账任务在 `SERVICE-account-service` |

## 九、数据源与副作用分析

- 主数据来源：`DB-demo_order`.`t_order`（读 + 写），中间件 `MIDDLEWARE-mysql`。
- 实时查询或补充路径：无（无下游服务、无缓存）。
- 写入、副作用或异步结果：更新 `t_order.status` 为 `SHIPPED`；不发布消息、不写文件、不产生导出记录。
- 事务、一致性和失败处理：未发现 `@Transactional`；读状态与写状态为两次独立操作，存在并发下重复发货或状态覆盖风险（先读后写，无乐观锁/条件更新 `WHERE status='PAID'`）；异常未经统一处理，`IllegalStateException` 将按框架默认行为返回 500（待确认）。

## 十、关键证据引用

| 引用 | 文件或资料位置 |
|------|----------------|
| 用户对外能力清单（未登记本能力） | `cadence/knowledge-base/user-input/api-scope.md:10-13` |
| 入口定义 | `order-service/src/main/java/com/demo/order/controller/OrderController.java:7-21` |
| 入口实现 | `order-service/src/main/java/com/demo/order/service/OrderService.java:21-35` |
| 数据访问 | `TABLE-t_order`、`data-models/DB-demo_order/TABLE-t_order.md`、`db/init.sql:26-32`、`order-service/src/main/resources/mapper/OrderMapper.xml:4-9` |
| 配置依赖 | `CONFIG-SERVICE-order-service`、`server.port`、`spring.datasource.*`（缺失，Q-M6）、`configurations/SERVICE-order-service.md` |
| 中间件与外部调用 | `order-service/pom.xml:13-18` |
| 行为规格 | `order-service/src/test/java/com/demo/order/OrderServiceTest.java:14-28`（Q-H1） |

## 十一、请求、响应或载荷示例

请求与响应示例见同目录 `API-order-ship_订单发货_ship_参数与报文.md` 第三、四节。
