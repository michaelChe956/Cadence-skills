# 服务索引

## 元数据

| 项目 | 内容 |
|------|------|
| 范围来源 | `cadence/knowledge-base/user-input/project-scope.md`（状态：全量） |
| 基线提交 | 1f867b9fcdf95f2e11808454898f333d7d512e90 |
| 服务数量 | 4（3 个 Java 后端、1 个 Vue3 前端） |
| 中间件范围 | 全量：MySQL、RabbitMQ（中间件适用，故索引不记录不适用原因） |
| API 阶段状态 | 进行中：`coverage.initialization.completed_stages` 不含 `api` 且 `scope.api.status: 全量` |
| 页面阶段状态 | 进行中：`coverage.initialization.completed_stages` 不含 `pages` 且 `scope.pages.status: 全量` |

> 本索引只保存摘要、稳定 ID 与领域文档链接，不复制字段清单、配置键、接口明细或页面明细。

## 服务清单

| ID | 名称 | 类型 | 职责 | 模块 | 入口 | 状态 | 文档 | 证据 |
|----|------|------|------|------|------|------|------|------|
| SERVICE-user-service | user-service | Java 后端（Spring Boot 3.2.5 / MyBatis） | 维护并对外提供用户基本信息查询（`t_user`） | MODULE-user-basic | `com.demo.user.UserApplication` | 已识别 | `services/SERVICE-user-service.md` | `user-service/src/main/java/com/demo/user/UserApplication.java:6-11` |
| SERVICE-account-service | account-service | Java 后端（Spring Boot 3.2.5 / MyBatis） | 用户账户信息查询与每日对账任务 | MODULE-account-core、MODULE-account-reconcile | `com.demo.account.AccountApplication` | 已识别 | `services/SERVICE-account-service.md` | `account-service/src/main/java/com/demo/account/AccountApplication.java:6-11` |
| SERVICE-order-service | order-service | Java 后端（Spring Boot 3.2.5 / MyBatis + AMQP） | 订单状态机、订单导出、订单已支付事件生产与消费 | MODULE-order-core、MODULE-order-export、MODULE-order-event | `com.demo.order.OrderApplication` | 已识别 | `services/SERVICE-order-service.md` | `order-service/src/main/java/com/demo/order/OrderApplication.java:6-11` |
| SERVICE-web-portal | web-portal | Vue3 前端（Vite SPA） | 运营门户页面（用户、账户、订单）与统一请求封装 | MODULE-web-portal-app、MODULE-web-portal-api、MODULE-web-portal-views | `web-portal/src/main.js`（挂载 `#app`） | 已识别 | `services/SERVICE-web-portal.md` | `web-portal/src/main.js:8-15` |

## 模块与归属

| 模块 ID | 所属服务 | 模块职责 | 证据 |
|---------|----------|----------|------|
| MODULE-user-basic | SERVICE-user-service | 用户基本信息查询链路（Controller/Service/Mapper/Entity） | `user-service/src/main/java/com/demo/user/**` |
| MODULE-account-core | SERVICE-account-service | 账户查询链路（Controller/Service/Mapper/Entity） | `account-service/src/main/java/com/demo/account/**`（不含 job 包） |
| MODULE-account-reconcile | SERVICE-account-service | 每日对账定时任务 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:11-17` |
| MODULE-order-core | SERVICE-order-service | 订单状态机与读写（Controller/Service/Mapper/Entity/枚举） | `order-service/src/main/java/com/demo/order/{controller,service,mapper,entity}` |
| MODULE-order-export | SERVICE-order-service | 订单导出接口与非持久化导出服务 | `order-service/src/main/java/com/demo/order/controller/ExportController.java:5-13`、`service/ExportService.java:5-11` |
| MODULE-order-event | SERVICE-order-service | RabbitMQ 事件生产与消费 | `order-service/src/main/java/com/demo/order/mq/**` |
| MODULE-web-portal-app | SERVICE-web-portal | 应用装配与静态路由 | `web-portal/src/main.js:1-16`、`web-portal/src/App.vue:1` |
| MODULE-web-portal-api | SERVICE-web-portal | 统一请求封装与接口封装 | `web-portal/src/api/request.js:1-4`、`web-portal/src/api/index.js:1-4` |
| MODULE-web-portal-views | SERVICE-web-portal | 页面视图 | `web-portal/src/views/UserList.vue`、`AccountPage.vue`、`OrderPage.vue` |

## 领域导航

- 基础信息：`base-information.md`
- 数据模型：`data-models/README.md`
- 配置：`configurations/README.md`
- 证据：`evidence/source-index.md`、`evidence/traceability-matrix.md`、`evidence/relation-graph.yaml`
- 待确认项：`open-questions.md`
