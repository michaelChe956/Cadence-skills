# 项目领域术语

## 文档元数据

| 项目 | 内容 |
|------|------|
| 证据基线 | 1f867b9fcdf95f2e11808454898f333d7d512e90（分支 master） |
| 最后更新 | 2026-09-20（overview 阶段生成） |
| 来源优先级 | 用户权威输入（`user-input/product.md`、`user-input/api-scope.md`）> 测试断言 > 代码与 DDL 候选 |
| 状态取值 | `confirmed`（有用户权威输入或可定位证据且无来源冲突）、`ai-draft`（候选词义，待人工裁决） |

## 正式术语

| 术语 | 缩写/同义词 | 关联术语 | 项目内含义 | 适用范围 | 来源标签 | 可信度 | 证据位置 | 状态 |
|------|-------------|----------|------------|----------|----------|--------|----------|------|
| 用户基本信息 | 用户资料、user profile | 账户信息、订单 | 用户在 `t_user` 中的主数据视图：用户标识、姓名、手机号、邮箱 | `API-user-basic`、`FLOW-user-basic-query`、`PAGE-user-list`、`TABLE-t_user` | [用户提供] | 高 | `user-input/product.md:13`；`user-service/src/main/java/com/demo/user/controller/UserBasicController.java:26-30`；`user-service/src/main/resources/mapper/UserMapper.xml:4-7` | confirmed |
| 账户信息 | 账户、account | 用户基本信息、余额、账户状态 | 用户在 `t_user_account` 中的账户号、余额与状态 | `API-account-query`、`FLOW-account-query`、`PAGE-account-query`、`TABLE-t_user_account` | [用户提供] | 高 | `user-input/product.md:14`；`account-service/src/main/java/com/demo/account/controller/AccountController.java:26-30` | confirmed |
| 订单管理 | 订单、order | 订单状态机、订单发货、订单导出 | 订单的查询、状态流转与导出等运营操作集合 | `PAGE-order-manage`、`API-order-ship`、`API-order-export`、`FLOW-order-ship` | [用户提供] | 高 | `user-input/product.md:15`；`web-portal/src/views/OrderPage.vue:1-12` | confirmed |
| 订单导出 | 导出、export | 导出文件保留期、订单管理 | 用户声明的对外能力：将订单数据导出为文件 | `API-order-export`、`FLOW-order-export`、`FILE-order-export-file` | [用户提供] | 中（实现缺失，Q-H2） | `user-input/product.md:15`、`user-input/api-scope.md:13`；`order-service/src/main/java/com/demo/order/controller/ExportController.java:36-44` | confirmed |
| 内部运营人员 | 运营人员 | 运营门户、页面 | 知识库声明的目标用户类型，通过运营门户页面完成用户、账户与订单操作 | `SERVICE-web-portal`、`PAGE-user-list`、`PAGE-order-manage`、`PAGE-account-query` | [用户提供] | 高 | `user-input/product.md:9` | confirmed |

> 用户权威输入只定义词义，不证明实现状态；实现状态以接口、页面与数据模型领域文档为准。

## 与通用含义不同的术语

- 账户信息：项目内仅指账户号、余额与状态，不含登录凭证、角色或权限数据（`TABLE-t_user_account`；未发现认证实现，Q-M8）。
- 订单导出：项目内指对外订单导出能力及其导出文件登记，不是数据库备份或运维导出（`API-order-export`、`TABLE-t_export_file`）。
- 对账：项目内为每日账户核对任务的占位语义，不是财务对账单或结算流程（`JOB-reconcile`，无实现，Q-M1/Q-M2）。
- 订单状态机：项目内指 `OrderStatus` 枚举与服务层分支校验，不是可配置的流程引擎（`OrderStatus.java:3-9`、`OrderService.java:21-35`）。

## 候选术语

候选术语必须标记 `[合理推断]` 或 `[待人工确认]`，不得直接写成正式定义。以下候选由代码标识符、注释与测试名自动采集，词义裁决必须人工，未裁决前不得进入正式术语表主体。

| 术语 | 缩写/同义词 | 项目内候选含义 | 适用范围 | 来源标签 | 可信度 | 证据位置 | 状态 |
|------|-------------|----------------|----------|----------|--------|----------|------|
| 订单状态机 | OrderStatus、状态机 | 订单状态取值与迁移约束：`CREATED → PAID → SHIPPED → COMPLETED`，任意非终态 → `CANCELLED` | `MODULE-order-core`、`API-order-ship`、`FLOW-order-ship` | [合理推断] | 中 | `order-service/src/main/java/com/demo/order/entity/OrderStatus.java:3-9`、`service/OrderService.java:21-35` | ai-draft |
| 订单发货 | ship、发货 | 将已支付订单流转为 `SHIPPED` 的运营操作 | `API-order-ship`、`PAGE-order-manage` | [合理推断] | 中 | `order-service/src/main/java/com/demo/order/service/OrderService.java:25-35`、`controller/OrderController.java:26-30` | ai-draft |
| 已支付事件 | order.paid、EVENT-order-paid | 订单支付成功后发布的领域事件及其支付后处理 | `MODULE-order-event`、`FLOW-order-paid-event` | [合理推断] | 中 | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java:6-21`、`mq/OrderEventListener.java:31-41` | ai-draft |
| 导出文件保留期 | RETENTION_DAYS、保留 7 天 | 导出文件的保留天数常量，声明 7 天后清理 | `MODULE-order-export`、`FILE-order-export-file` | [合理推断] | 中 | `order-service/src/main/java/com/demo/order/service/ExportService.java:9-10`、`db/init.sql:39` | ai-draft |
| 账户状态 | status、NORMAL/FROZEN/CLOSED | 账户的业务状态取值集合 | `TABLE-t_user_account`、`MODULE-account-core` | [合理推断] | 低 | `db/init.sql:20` | ai-draft |
| 每日对账 | reconcile、对账任务 | 每日 02:00 触发的账户核对任务，支持启用开关与重试次数 | `MODULE-account-reconcile`、`JOB-reconcile` | [合理推断] | 低 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:49-59`、`src/main/resources/application.yml:10-12` | ai-draft |

> 候选术语均登记待确认（`open-questions.md` Q-L9），未经人工裁决不得写入正式术语表主体，也不得作为确定业务定义使用。
