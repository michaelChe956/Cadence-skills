# API-order-export 订单导出

> **能力 ID**：`API-order-export`
> **分类**：对外
> **能力类型**：REST
> **数据来源**：用户对外能力清单（`user-input/api-scope.md`）、`order-service` 工程代码、`db/init.sql`、git 提交 `1f867b9`
> **梳理日期**：2026-09-20
> **参数与报文**：见同目录 `API-order-export_订单导出_export_参数与报文.md`

## 一、能力基础信息

| 项目 | 值 |
|------|----|
| 能力名称 | 订单导出 |
| API 名称或逻辑标识 | `export` |
| 分类 | 对外（来源：用户对外能力清单） |
| 能力类型 | REST（工程内实现为存根） |
| 协议与方法 | HTTP POST |
| 路径或逻辑地址 | `/api/order/export` |
| 数据格式 | 未提供（方法返回 `String` 字面量，未声明 `produces`） |
| 是否需授权 | 未发现鉴权实现（无 Spring Security 依赖、无过滤器、无网关工程）；对外鉴权要求待确认（Q-M8） |
| 版本 | v1（用户清单） |
| 调用方或生产者 | 客户端（用户清单）；`web-portal` 订单管理页（代码证据：`web-portal/src/api/index.js:4`、`web-portal/src/views/OrderPage.vue:11`） |
| 落地方或消费者 | `SERVICE-order-service`（`MODULE-order-export`） |
| 生命周期状态 | 已声明、已实现（存根）、已装配、已暴露；端到端导出链路未实现 |
| 数据来源表 | `TABLE-t_export_file`（设计意图，代码未访问；见 Q-H2、Q-M4） |

### 调用入口

| 环境 | 地址 | 证据状态 |
|------|------|----------|
| 开发（fixture 快照） | `http://localhost:8083/api/order/export`（端口取 `server.port` 键，非敏感） | `order-service/src/main/resources/application.yml:1-2` |
| 生产 | 未提供（未发现网关或域名配置） | 待确认 |
| 前端访问路径 | `/api/order/export`（合并 axios `baseURL: /api` 后） | `web-portal/src/api/index.js:4`、`web-portal/src/api/request.js:3`，代理目标见 Q-L4 |

## 二、业务需求描述

- 用户清单声明：订单导出能力，REST API，v1，状态“使用中”，调用方为客户端（`user-input/api-scope.md:13`）。
- 代码侧线索：导出文件保留 7 天后清理（`ExportService.RETENTION_DAYS = 7`，`ExportService.java:9-10`，git 提交 `1f867b9`“导出文件保留期应为 7 天，原误配 30 天”）；`t_export_file` 表登记导出文件路径与导出时间（`db/init.sql:35-40`，字段注释“保留 7 天后清理”）。
- 实现冲突：`ExportController#export` 无入参解析、未调用 `ExportService`、直接返回字面量 `"taskId"`，未发现文件生成、登记、下载或清理实现；与用户清单“使用中”不一致，登记 Q-H2。
- 导出范围、文件格式、异步通知方式等业务语义：未提供。

## 三、输入参数

详见 `API-order-export_订单导出_export_参数与报文.md` 第一节（未提供输入参数）。

## 四、输出参数

详见 `API-order-export_订单导出_export_参数与报文.md` 第二节（字面量 `taskId`）。

## 五、代码实现定位

### 5.1 用户清单与代码映射

| 来源 | 标识 | 结论 | 证据 |
|------|------|------|------|
| 用户对外能力清单 | `API-order-export`（订单导出，REST API，v1，使用中，调用方：客户端） | 保留对外分类；代码入口存在但实现为存根 | `user-input/api-scope.md:13` |
| 当前代码 | `ExportController#export` | 已装配、已暴露；无业务实现与数据访问 | `order-service/src/main/java/com/demo/order/controller/ExportController.java:10-13` |

### 5.2 实现清单

| 层级 | 符号 | 文件路径 | 状态 | 说明 |
|------|------|----------|------|------|
| 入口 | `com.demo.order.controller.ExportController#export` | `order-service/src/main/java/com/demo/order/controller/ExportController.java:10-13` | 已确认（存根） | `@PostMapping` 无路径与方法参数，返回字面量 `"taskId"` |
| 业务 | `com.demo.order.service.ExportService` | `order-service/src/main/java/com/demo/order/service/ExportService.java:5-11` | 已确认（仅常量） | 只有 `RETENTION_DAYS = 7`；Bean 存在但无任何调用方 |
| 数据访问 | 未发现 | - | 未发现 | 未发现引用 `t_export_file` 的 Mapper、Entity 或 SQL |
| 装配 | `@SpringBootApplication` 组件扫描 `com.demo.order` | `order-service/src/main/java/com/demo/order/OrderApplication.java:7-11` | 已确认 | Controller 与 Service 均被扫描注册 |

## 六、调用链路

### 6.1 调用树

```text
API-order-export（POST /api/order/export）
└─ SERVICE-order-service / MODULE-order-export
   └─ ExportController.export（ExportController.java:10-13）
      └─ 返回字面量 "taskId"（链路到此中止）
         ├─ [未实现] ExportService.RETENTION_DAYS（ExportService.java:9-10，无调用方）
         ├─ [未实现] TABLE-t_export_file 写入（无 Mapper/SQL/Entity）
         └─ [未实现] 文件生成、下载与保留期清理
   └─ CONFIGURATION CONFIGGROUP-order-server
      └─ server.port → 暴露端口（Spring Boot 内置绑定）
```

### 6.2 分支与触发条件

| 条件 | 路径 | 结果 | 证据 |
|------|------|------|------|
| 未发现任何条件分支（无入参、无开关、无异步任务登记） | `ExportController#export` | 恒定返回 `"taskId"` | `ExportController.java:10-13` |
| 若按 DDL 与保留期常量推断的实现路径 | 导出 → 登记 `t_export_file` → 7 天后清理 | 未实现，链路不可达 | `db/init.sql:35-40`、`ExportService.java:9-10`；待确认（Q-M4） |

### 6.3 逐层调用明细

| 层级 | 符号 | 职责 | 下游 | 证据 |
|------|------|------|------|------|
| REST 入口 | `ExportController#export()` | 返回字面量 `"taskId"` | 无 | `ExportController.java:10-13` |
| 业务 | `ExportService` | 仅定义保留期常量 | 无 | `ExportService.java:5-11` |
| 数据访问 | 未发现 | - | - | `order-service/src/main/resources/mapper/OrderMapper.xml` 仅含 `t_order` 语句 |

## 七、数据模型与配置依赖

### 7.1 数据模型影响

| TABLE 稳定 ID | Schema/逻辑表 | 读写 | 涉及字段 | API 模型映射 | Mapper/DAO/SQL | 表字段证据状态 | 端到端映射状态 | 表文档链接 |
|---------------|---------------|------|----------|--------------|----------------|------------------|------------------|------------|
| TABLE-t_export_file | `DB-demo_order` / `t_export_file` | 待确认（按 DDL 与保留期常量推断为 W） | 推断涉及：`order_id`、`file_path`、`created_at`（`id` 主键未发现生成方式） | 未发现（无请求/响应模型与表字段的转换证据） | 未发现（无 Mapper/Entity/SQL） | DDL 已确认（`db/init.sql:35-40`） | 待确认（API 模型 → SERVICE/MODULE → Mapper/SQL → TABLE 字段缺少全部下游跳） | [`TABLE-t_export_file`](../data-models/DB-demo_order/TABLE-t_export_file.md) |

> `表字段证据状态` 只说明字段定义来自 DDL；本能力缺少 Entity、Mapper、SQL 与文件生成代码，端到端映射不可确认，登记 Q-M4。

### 7.2 配置依赖

| 配置组稳定 ID | 服务配置实体 | 配置键 | 直接影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| CONFIGGROUP-order-server | `CONFIG-SERVICE-order-service` | `server.port` | 路由/监听：决定该路径的暴露端口 | 开发（default Profile） | Spring Boot 内置属性绑定 | 已确认 | [`SERVICE-order-service`](../configurations/SERVICE-order-service.md) |

> `CONFIGGROUP-order-datasource` 在授权快照中状态为“缺失”（`order-service/application.yml` 无 `spring.datasource.*`），当前实现未访问数据库，故未列入直接依赖；若补齐导出持久化，需先澄清数据源来源（Q-M6）。
> `CONFIGGROUP-order-rabbitmq` 仅影响事件生产/消费链路，对导出接口无直接行为影响，不纳入本节。

## 八、中间件使用明细

### 8.1 缓存与队列

| 类型 | 名称或 Key 模式 | 读写方向 | 触发时机 | 证据 |
|------|-----------------|----------|----------|------|
| 未发现 | - | - | - | `order-service/pom.xml:13-18` 无缓存/队列依赖 |

### 8.2 消息

| Topic/Queue/Group | 方向 | 消息模型 | 重试与幂等 | 证据 |
|-------------------|------|----------|------------|------|
| 未发现（导出链路不发布/消费消息） | - | - | - | `ExportController.java:10-13`、`ExportService.java:5-11` |

### 8.3 搜索与本地缓存

未发现。

### 8.4 RPC 与下游 HTTP

| 服务 | 协议 | 版本或分组 | 触发条件 | 证据 |
|------|------|------------|----------|------|
| 未发现 | - | - | - | 未发现 Feign/RestTemplate/WebClient/RPC 依赖或调用代码 |

### 8.5 文件与对象存储

| 协议或存储 | 逻辑位置 | 文件格式 | 触发方 | 接收方 | 证据 |
|------------|----------|----------|--------|--------|------|
| 未发现（无 FTP/SFTP/对象存储/上传下载实现） | 未发现（`t_export_file.file_path` 为登记字段，非实现） | 未发现 | 未发现 | 未发现 | `db/init.sql:35-40`、`ExportService.java:9-10`；无文件读写代码 |
| 关联能力 | `FILE-order-export-file`（对内，状态未知） | - | - | - | `interfaces/FILE-order-export-file_订单导出文件.md` |

### 8.6 定时任务与批处理

| 任务 | 触发方式 | 并发与锁 | 重试与补偿 | 证据 |
|------|----------|----------|------------|------|
| 保留期清理（推断） | 未发现（DDL 注释声明“保留 7 天后清理”，无调度代码） | 未发现 | 未发现 | `db/init.sql:39`、`ExportService.java:9-10` |

## 九、数据源与副作用分析

- 主数据来源：`order-service` 授权配置快照中无数据源键；当前实现未访问任何数据源（Q-M6）。
- 实时查询或补充路径：无。
- 写入、副作用或异步结果：未发现（既无文件写出，也无 `t_export_file` 登记；返回值为字面量）。
- 事务、一致性和失败处理：未发现 `@Transactional`、任务登记、异常处理或幂等控制；导出结果无跟踪标识生成逻辑（返回的 `"taskId"` 为固定字面量，不具唯一性）。
- 对外契约缺口：无入参定义、无真实状态/结果查询方式，调用方无法获知导出结果。

## 十、关键证据引用

| 引用 | 文件或资料位置 |
|------|----------------|
| 用户对外能力清单 | `cadence/knowledge-base/user-input/api-scope.md:13` |
| 入口定义 | `order-service/src/main/java/com/demo/order/controller/ExportController.java:5-13` |
| 入口实现 | `order-service/src/main/java/com/demo/order/controller/ExportController.java:10-13`（存根） |
| 数据访问 | 未发现；相关表文档 `data-models/DB-demo_order/TABLE-t_export_file.md`、DDL `db/init.sql:35-40` |
| 配置依赖 | `CONFIG-SERVICE-order-service`、`server.port`、`configurations/SERVICE-order-service.md` |
| 中间件与外部调用 | 未发现（`order-service/pom.xml:13-18`） |
| 业务规则来源 | git 提交 `1f867b9`（导出保留期 30→7 天修复）、`order-service/src/main/java/com/demo/order/service/ExportService.java:9-10`；规则卡 `business/rules/RULE-order-export-retention.md` |

## 十一、请求、响应或载荷示例

请求与响应示例见同目录 `API-order-export_订单导出_export_参数与报文.md` 第三、四节（无请求体，响应为纯文本 `taskId`）。
