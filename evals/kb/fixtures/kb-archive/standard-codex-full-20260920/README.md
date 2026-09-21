# 项目概览

## 文档元数据

- 生成时间：2026-09-20
- Git 分支：master
- 基线提交：1f867b9fcdf95f2e11808454898f333d7d512e90
- 执行模式：续跑（初始化 `coverage.initialization.status: in_progress`；本次执行 `overview` 阶段，`global-validation` 尚未执行）
- 覆盖范围：工程全量（`user-service`、`account-service`、`order-service`、`web-portal`）；数据模型全量（3 库 4 表）；配置全量（3 个后端 `application.yml`，快照 `baseline-config-v1`）；中间件全量（MySQL、RabbitMQ）；接口全量（对外 2、对内 5）；页面全量（`web-portal` 1 个应用、3 条路由）；业务域与组合能力层由本次 overview 生成
- 未覆盖范围：测试/预发/生产环境配置与运行态中间件；前端构建与部署入口；业务目标（`user-input/product.md` 记`未提供`）；未由用户清单登记的对外能力；`web-portal` 构建配置不在配置授权范围内
- 各领域最后核验时间：数据模型 2026-09-20（4 张表文档元数据`最后核验时间`最大值）；接口 未采集；页面 未采集；服务 未采集；配置 未采集（上述领域文档暂无该字段）

## 项目摘要

`demo 商城系统` 为商城运营方提供用户、账户与订单的统一管理能力，目标用户为内部运营人员，关键特性为用户信息查询、账户查询、订单管理与导出 [用户提供]（`user-input/product.md`）；业务目标未提供。

- 系统组成：单仓多模块（`REPO-demo-commerce`），3 个 Spring Boot 3.2.5 / Java 17 后端（`user-service`、`account-service`、`order-service`）与 1 个 Vue 3 + Vite 单页应用（`web-portal`，3 条静态路由）。
- 主要外部系统与中间件：MySQL（`demo_user`、`demo_account`、`demo_order` 三库，经 MyBatis 访问）与 RabbitMQ（仅 `order-service` 使用，`order.exchange` / `order.paid` / `order.paid.queue`）；未发现 Redis、配置中心、注册中心、网关、第三方 API 客户端与前端服务端框架。
- 证据显示的范围外职责：不含鉴权与认证中心（三后端与前端均未发现安全依赖、过滤器、路由守卫或权限码）；不含对外网关与反向代理（未发现网关工程，前端开发代理仅指向单一目标端点）；不承担中间件部署与运维（未发现容器化、部署、发布、启动脚本与 CI 配置）。
- 仓库根 `README.md` 自述过时（仅描述 `user-service`），不作为项目定位依据（Q-L2）。

## 一级导航

| 入口 | 内容 |
|------|------|
| [`base-information.md`](base-information.md) | 项目基础信息、技术栈与系统边界 |
| [`development-guide.md`](development-guide.md) | 开发、构建、验证与配置基线指南 |
| [`interfaces/README.md`](interfaces/README.md) | 对外、对内能力索引与能力组合导航 |
| [`pages/README.md`](pages/README.md) | 页面、路由、权限与字段映射导航 |
| [`services/`](services/) | 服务与模块导航 |
| [`data-models/README.md`](data-models/README.md) | 字段级数据模型与表导航 |
| [`configurations/README.md`](configurations/README.md) | 服务配置、Profile 与中间件配置导航 |
| [`evidence/`](evidence/) | 源码、结构、配置快照与关系证据 |
| [`change-history.md`](change-history.md) | KnowledgeBase 变更历史 |
| [`open-questions.md`](open-questions.md) | 待确认项 |

> 业务域与组合能力的入口在 `business/README.md` 与 `capabilities/README.md`；两者未列入一级导航，按需从本页“核心业务流程”或接口索引进入。

## 核心业务流程

稳定主链：

```text
PAGE → API → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE
```

以下为最重要的 5 条流程；步骤、字段与证据明细见各自流程文档，完整清单见 [`business/README.md`](business/README.md)。

| 流程稳定 ID | 名称 | 稳定链路（摘要） | 条目状态 | 流程文档 |
|-------------|------|------------------|----------|----------|
| `FLOW-user-basic-query` | 用户基本信息查询 | `PAGE-user-list` → `API-user-basic` → `SERVICE-user-service`/`MODULE-user-basic` → `TABLE-t_user` → `CONFIGGROUP-user-datasource`/`MIDDLEWARE-mysql` | confirmed | [`FLOW-user-basic-query`](business/flows/FLOW-user-basic-query.md) |
| `FLOW-account-query` | 账户信息查询 | `PAGE-account-query` → `API-account-query` → `SERVICE-account-service`/`MODULE-account-core` → `TABLE-t_user_account` → `CONFIGGROUP-account-datasource`/`MIDDLEWARE-mysql` | confirmed | [`FLOW-account-query`](business/flows/FLOW-account-query.md) |
| `FLOW-order-ship` | 订单发货 | `PAGE-order-manage`/`ROUTE-web-portal-orders` → `API-order-ship` → `MODULE-order-core` → `TABLE-t_order` → `CONFIGGROUP-order-server` | confirmed | [`FLOW-order-ship`](business/flows/FLOW-order-ship.md) |
| `FLOW-order-export` | 订单导出 | `PAGE-order-manage` → `API-order-export` → `MODULE-order-export` → `TABLE-t_export_file` → `CONFIGGROUP-order-server` | ai-draft（端到端链路未实现，Q-H2） | [`FLOW-order-export`](business/flows/FLOW-order-export.md) |
| `FLOW-order-paid-event` | 订单已支付事件处理 | `MODULE-order-core` → `EVENT-order-paid` → `MODULE-order-event` → `MIDDLEWARE-rabbitmq`/`CONFIGGROUP-order-rabbitmq` | ai-draft（生产触发点不可达，Q-M10） | [`FLOW-order-paid-event`](business/flows/FLOW-order-paid-event.md) |

> 另有 `FLOW-account-reconcile`（每日账户对账，ai-draft，Q-M1/Q-M2）未列入上表，见 `business/README.md`。
> 业务流程只能追踪到上述稳定 ID 与证据；知识库与源码冲突时，以源码、DDL、有效配置与当前证据为准并回写知识库。

## 常见修改场景

| 场景 | 必读文档 | 主要实体 | 影响检查 | 验证入口 |
|------|----------|----------|----------|----------|
| 字段变更 | [`data-models/README.md`](data-models/README.md)、字段级表文档、`evidence/` 当前结构证据 | TABLE、COLUMN | 关联 API、页面、SQL/Mapper 与服务 | [`development-guide.md`](development-guide.md) |
| SQL/Mapper 变更 | 字段级表文档、`evidence/` SQL/Mapper 证据、服务文档 | TABLE、MAPPER、SERVICE/MODULE | 字段映射、事务、查询调用方 | [`development-guide.md`](development-guide.md) |
| 配置键变更 | [`configurations/README.md`](configurations/README.md)、服务配置文档、当前快照证据 | CONFIGURATION、CONFIGGROUP | Profile、依赖服务与中间件 | [`development-guide.md`](development-guide.md) |
| Profile/Feature Flag 变更 | 服务配置文档、环境差异、当前快照证据 | PROFILE、FEATURE_FLAG | 环境差异、默认值与启用条件（本项目未发现 Feature Flag） | [`development-guide.md`](development-guide.md) |
| API 参数变更 | [`interfaces/README.md`](interfaces/README.md)、接口主文档与参数报文、服务与数据模型文档 | API、PARAMETER | 调用方（含页面）、服务、表 | [`development-guide.md`](development-guide.md) |
| 页面字段变更 | [`pages/README.md`](pages/README.md)、页面文档、接口与数据模型文档 | PAGE、FIELD | API 参数、字段映射与校验 | [`development-guide.md`](development-guide.md) |
| 中间件配置变化 | [`configurations/README.md`](configurations/README.md)、中间件证据、依赖服务文档 | MIDDLEWARE、CONFIGURATION | 连接、队列绑定、消费与部署环境 | [`development-guide.md`](development-guide.md) |
| 页面或路由变更 | [`pages/README.md`](pages/README.md)、页面或路由文档、接口文档、[`services/README.md`](services/README.md) | PAGE、ROUTE、API、SERVICE/MODULE | 导航、守卫、菜单与调用链 | [`development-guide.md`](development-guide.md) |
| 消息生产/消费或异步任务变更 | [`interfaces/README.md`](interfaces/README.md)、`EVENT-order-paid`/`JOB-reconcile` 主文件、[`services/README.md`](services/README.md)、配置与证据 | EVENT、JOB、API、SERVICE/MODULE | 生产者、消费者、调度、重试、事务与幂等 | [`development-guide.md`](development-guide.md) |
| 鉴权/权限/数据权限变更 | 页面与路由文档、接口主文件、[`services/README.md`](services/README.md)、配置与证据 | PAGE、ROUTE、API、SERVICE/MODULE | 前端控制、后端鉴权、数据范围与调用方（当前均未实现，Q-M8/Q-M12） | [`development-guide.md`](development-guide.md) |
| 新增服务或模块 | [`services/README.md`](services/README.md)、服务文档、[`base-information.md`](base-information.md)、[`development-guide.md`](development-guide.md) 及关联接口/页面/数据模型/配置/证据 | SERVICE、MODULE、API、PAGE、TABLE、CONFIGURATION | 入口、依赖、装配、领域导航与上下游影响 | [`development-guide.md`](development-guide.md) |

## 高风险区域

- 对外能力 `API-order-export` 声明“使用中”但代码仅存根，端到端导出链路与结果获取方式缺失（Q-H2）。
- 三后端与前端均未发现鉴权实现，且 `API-user-basic`、`API-account-query` 响应含姓名、手机号、邮箱与账户余额（Q-M8、Q-M12）。
- `web-portal` 未发现 Vite 入口 `index.html`，前端能否构建/启动未确认（Q-H3）。
- 每日对账任务无调度启用证据、配置键无代码绑定（Q-M1、Q-M2）；`EVENT-order-paid` 生产触发点不可达且消费方法体为空（Q-M10）。
- 详细清单与影响见 [`open-questions.md`](open-questions.md)。

## 待确认项

blocking 0、high 3、medium 13、low 8（未解决条目合计 24）。完整问题、影响、证据与建议确认方式见 [`open-questions.md`](open-questions.md)。
