# 接口能力索引

## 元数据

| 项目 | 内容 |
|------|------|
| 执行模式 | 全量（`scope.api.status: 全量`，来源 `user-input/api-scope.md`） |
| 对外能力权威来源 | 用户对外能力清单（`cadence/knowledge-base/user-input/api-scope.md:10-13`） |
| 工程范围 | `user-service`、`account-service`、`order-service`、`web-portal`（`manifest.yaml` `scope.projects.items`） |
| 数据模型与配置授权 | `data-models/`（4 张逻辑表）、`configurations/`（3 个服务配置实体） |
| 证据基线 | `1f867b9fcdf95f2e11808454898f333d7d512e90`（分支 `master`） |
| 分析时间 | 2026-09-20 |
| 能力数量 | 对外 2；对内 5（REST 2、消息 1、任务 1、文件 1） |
| 阶段状态 | 本阶段（`api`）分析已完成；`pages`、`overview` 未执行 |
| 工具与边界 | 只读文本检索与定向阅读；未连接数据库、中间件或远程环境；敏感值统一 `<redacted>` |

> 索引只保存稳定 ID、状态、实现位置、证据与文档链接，不复制参数清单、字段清单或配置值。

## 对外能力

| ID | 能力名称 | 分类 | 类型 | 状态 | 实现位置 | 主文件 | 参数与报文 | 证据 |
|----|----------|------|------|------|----------|--------|------------|------|
| `API-user-basic` | 查询用户基本信息 | 对外 | REST | 已声明、已实现、已装配、已暴露 | `SERVICE-user-service` / `MODULE-user-basic`；`UserBasicController#queryBasic` | [`API-user-basic_查询用户基本信息_queryBasic.md`](./API-user-basic_查询用户基本信息_queryBasic.md) | [`参数与报文`](./API-user-basic_查询用户基本信息_queryBasic_参数与报文.md) | `user-service/src/main/java/com/demo/user/controller/UserBasicController.java:19-21` |
| `API-order-export` | 订单导出 | 对外 | REST | 已声明、已实现（存根）、已装配、已暴露（端到端导出链路未实现） | `SERVICE-order-service` / `MODULE-order-export`；`ExportController#export` | [`API-order-export_订单导出_export.md`](./API-order-export_订单导出_export.md) | [`参数与报文`](./API-order-export_订单导出_export_参数与报文.md) | `order-service/src/main/java/com/demo/order/controller/ExportController.java:10-13`；用户清单 `user-input/api-scope.md:13` |

对外分类说明：`API-order-export` 在代码中仅有存根实现，仍按规则保留对外分类（用户清单为唯一权威），实现冲突登记 Q-H2。

## 对内能力

| ID | 能力名称 | 分类 | 类型 | 状态 | 实现位置 | 主文件 | 参数与报文 | 证据 |
|----|----------|------|------|------|----------|--------|------------|------|
| `API-account-query` | 账户信息查询接口 | 对内 | REST | 已实现、已装配、已暴露 | `SERVICE-account-service` / `MODULE-account-core`；`AccountController#queryAccount` | [`API-account-query_账户信息查询_queryAccount.md`](./API-account-query_账户信息查询_queryAccount.md) | [`参数与报文`](./API-account-query_账户信息查询_queryAccount_参数与报文.md) | `account-service/src/main/java/com/demo/account/controller/AccountController.java:19-22` |
| `API-order-ship` | 订单发货接口 | 对内 | REST | 已实现、已装配、已暴露 | `SERVICE-order-service` / `MODULE-order-core`；`OrderController#ship` + `OrderService#ship` | [`API-order-ship_订单发货_ship.md`](./API-order-ship_订单发货_ship.md) | [`参数与报文`](./API-order-ship_订单发货_ship_参数与报文.md) | `order-service/src/main/java/com/demo/order/controller/OrderController.java:17-21` |
| `EVENT-order-paid` | 订单已支付事件 | 对内 | 消息 | 已实现、已装配；生产触发点不可达（`OrderService#markPaid` 无调用方） | `SERVICE-order-service` / `MODULE-order-event`；`OrderEventProducer`、`OrderEventListener` | [`EVENT-order-paid_订单已支付事件.md`](./EVENT-order-paid_订单已支付事件.md) | 不适用 | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java:10-21`、`mq/OrderEventListener.java:13-19` |
| `JOB-reconcile` | 每日账户对账任务 | 对内 | 任务 | 代码存在但不可达（空实现；未发现 `@EnableScheduling`） | `SERVICE-account-service` / `MODULE-account-reconcile`；`ReconcileJob#reconcile` | [`JOB-reconcile_每日账户对账任务.md`](./JOB-reconcile_每日账户对账任务.md) | 不适用 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:14-17` |
| `FILE-order-export-file` | 订单导出文件 | 对内 | 文件 | 状态未知（仅 DDL 与保留期常量，无文件实现） | `SERVICE-order-service` / `MODULE-order-export`（仅常量） | [`FILE-order-export-file_订单导出文件.md`](./FILE-order-export-file_订单导出文件.md) | 不适用 | `order-service/src/main/java/com/demo/order/service/ExportService.java:9-10`、`db/init.sql:35-40` |

### 全量扫描中未发现的能力维度

| 能力类型 | 扫描结论 | 证据 |
|----------|----------|------|
| 服务间 REST（Feign/RestTemplate/WebClient/自定义 Client） | 未发现（三个后端工程均无此类依赖或调用代码） | `user-service/pom.xml:13-17`、`account-service/pom.xml:13-17`、`order-service/pom.xml:13-18` |
| RPC（Dubbo/gRPC/HSF 等 Provider/Consumer） | 未发现 | 同上（无 RPC 依赖、无注册中心配置键） |
| Redis Pub/Sub、Stream、List 等队列式能力 | 未发现 | 同上（无 Redis 客户端依赖；三份 `application.yml` 无 Redis 键） |
| 消息生产/消费 | 已发现 1 项（`EVENT-order-paid`），无其他 Topic/Queue | `order-service/src/main/java/com/demo/order/mq/**` |
| 文件交换（FTP/SFTP/对象存储/上传下载） | 已发现 1 项待确认能力（`FILE-order-export-file`，无实现）；无其他文件能力 | `db/init.sql:35-40`、`ExportService.java:9-10` |
| 定时任务/批处理/异步作业 | 已发现 1 项（`JOB-reconcile`）；未发现批处理与异步作业 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:14-17` |
| 前端工程自有服务端接口 | 未发现（web-portal 为纯 SPA，无服务端框架依赖） | `web-portal/package.json:4-6` |

## 能力组合诉求核实

`user-input/api-scope.md:15-21` 声明组合诉求：目标能力“全部用户信息”（期望输出：用户基本信息 + 账户信息），来源能力 `API-user-basic` 与对内 REST `GET /api/account/{userId}`（account-service），连接键 `userId`。

本阶段核实结论（api 不生成组合实体，结论供 `overview` 生成 CAP 使用）：

| 核实项 | 结论 | 证据 |
|--------|------|------|
| 来源能力 1 存在性 | 存在：`API-user-basic` 已登记为对外能力，代码已定位 | `user-input/api-scope.md:12`、`UserBasicController.java:19-21` |
| 来源能力 2 存在性 | 存在：`GET /api/account/{userId}` 已登记为对内能力 `API-account-query`（用户清单以“预期登记为对内能力”表述，本阶段完成登记） | `user-input/api-scope.md:21`、`AccountController.java:19-22` |
| 契约锚点（参数与报文文件） | 两来源均具备可导航锚点 | [`API-user-basic 参数与报文`](./API-user-basic_查询用户基本信息_queryBasic_参数与报文.md)、[`API-account-query 参数与报文`](./API-account-query_账户信息查询_queryAccount_参数与报文.md) |
| 鉴权要求 | 两个来源均未发现鉴权实现（无 Spring Security 依赖、无过滤器、无网关工程）；对外能力的暴露与鉴权要求待确认 | `user-service/pom.xml:13-17`、`account-service/pom.xml:13-17`；Q-M8 |
| `JOIN_KEY` 端到端映射（`userId`） | 部分确认：user 侧 已确认（`user_id AS userId`，`WHERE user_id = #{userId}`）；account 侧 请求条件 已确认（`WHERE user_id = #{userId}`），响应字段依赖隐式驼峰映射 待确认 | `UserMapper.xml:4-7`、`AccountMapper.xml:5-7`；Q-M3 |
| 连接键值域与类型一致性 | 一致：两侧均为 BIGINT/Long，且 DDL 注释声明同源 | `db/init.sql:5,17`、`UserEntity.java:6`、`AccountEntity.java:6` |
| 跨库键的数据库约束 | 无外键约束，仅为注释级同源声明，不能作为连接约束事实 | `db/init.sql`（无 `FOREIGN KEY`）；Q-M5 |
| 结论 | 来源能力与契约锚点齐备；`JOIN_KEY` 端到端映射未闭合，供 `overview` 生成 CAP 时按“待确认”处理 | 见 `open-questions.md` Q-M3、Q-M5、Q-M9 |

> 组合层横向关系类型（`COMPOSES`、`JOIN_KEY`、`PROVIDES_FIELD`）本阶段不写入追溯矩阵，仅由 `knowledge-base-overview` 通道写入。

## 能力组合

| CAP 稳定 ID | 名称 | 状态 | 输入 API | 明细 |
|-------------|------|------|----------|------|
| `CAP-user-full-info` | 全部用户信息 | proposed | `API-user-basic`、`API-account-query` | [`CAP-user-full-info`](../capabilities/CAP-user-full-info.md) |

> 本分区只提供组合能力导航（由 `knowledge-base-overview` 同批写入）；输入能力清单、编排、JOIN_KEY 证据与实现关联见明细文档。`proposed` 不等于对外已暴露，对外属性唯一权威是用户 `api-scope` 清单。

## 证据可信度

| 能力 ID | 可信度 | 判定依据 |
|---------|--------|----------|
| `API-user-basic` | 高 | 用户清单、入口实现、Bean 装配与调用方（前端 + 客户端声明）证据相互支持，无来源冲突 |
| `API-order-export` | 低 | 存在来源冲突：用户清单声明“使用中”，代码仅存根实现且无数据访问与文件产出（Q-H2） |
| `API-account-query` | 中 | 实现、装配与调用方已确认，但响应字段映射缺少显式 `resultMap` 或映射配置证据（Q-M3、Q-M9） |
| `API-order-ship` | 高 | 入口、状态机实现、SQL 读写与调用方证据完整；状态机行为规格测试因依赖缺失暂不可执行（Q-H1） |
| `EVENT-order-paid` | 中 | 生产与消费代码、队列绑定已确认，但生产触发点不可达且运行态 MQ 可达性、重试与幂等证据缺失（Q-M10、Q-M6） |
| `JOB-reconcile` | 低 | 任务实现为空体，`@EnableScheduling` 与 `reconcile.*` 绑定均无证据，仅注释声明（Q-M1、Q-M2） |
| `FILE-order-export-file` | 低 | 仅有登记表 DDL 与保留期常量，无文件生成、登记、交付或清理实现（Q-M4），属名称与设计意图候选 |

## 分类、状态与待确认摘要

- 对外能力完全来自用户清单，未因代码未实现而降级分类。
- 工程内发现但未登记的能力（2 个对内 REST、1 个消息、1 个任务、1 个文件）全部归为对内能力。
- 分类冲突：`AccountController` 类注释自称“对外能力 API-B”，但用户清单未登记；保留对内分类并登记 Q-M7。
- 高优先级待确认：对外能力 `API-order-export` 端到端链路未实现（Q-H2）。
- 其他相关待确认：Q-M1、Q-M2（对账任务启用与配置）、Q-M3（账户响应字段隐式映射）、Q-M4（导出登记与保留期清理缺失）、Q-M5（跨库同源无外键）、Q-M6（数据源配置来源）、Q-M9（组合连接键映射）、Q-M10（事件生产不可达）、Q-M8（对外能力鉴权实现缺失）。
