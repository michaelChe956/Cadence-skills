# 证据来源索引

## 元数据

| 项目 | 内容 |
|------|------|
| 证据基线 | 1f867b9fcdf95f2e11808454898f333d7d512e90（分支 master） |
| 分析时间 | 2026-09-20 |
| 工具 | 只读文本检索与定向阅读（`rg`/`sed`/`cat`）；未使用 CodeGraph 或 `ast-grep outline`（环境未提供），已按降级边界在有界目录内检索 |
| 快照边界 | 外部快照 `/home/tester/work/snapshots/baseline-config` 只读，未复制、未写入、未记录单文件哈希 |
| 敏感处理 | 口令、账号、完整连接串、内部域名与 IP 一律 `<redacted>`，未记录任何敏感值哈希 |

## 工程与代码证据

| 证据 ID | 类型 | 路径或来源 | 覆盖范围 | 说明 |
|---------|------|------------|----------|------|
| SRC-REPO | 仓库 | `.`（单仓多模块，分支 master） | 四工程 | 基线 1f867b9 |
| SRC-README | 文档 | `README.md:1-5` | 仓库说明 | 自述过时，仅描述 user-service，不作为结构依据（Q-L2） |
| SRC-USER-POM | 构建 | `user-service/pom.xml` | 依赖与 Java 版本 | Spring Boot 3.2.5、Java 17、MyBatis 3.0.3、MySQL 驱动 8.0.33 |
| SRC-ACCOUNT-POM | 构建 | `account-service/pom.xml` | 依赖与 Java 版本 | 同上（无 AMQP） |
| SRC-ORDER-POM | 构建 | `order-service/pom.xml` | 依赖与 Java 版本 | 同上 + `spring-boot-starter-amqp` |
| SRC-USER-JAVA | 代码 | `user-service/src/main/java/com/demo/user/**` | 入口、控制器、服务、Mapper、实体 | 5 个源文件 |
| SRC-ACCOUNT-JAVA | 代码 | `account-service/src/main/java/com/demo/account/**` | 入口、控制器、服务、Mapper、实体、定时任务 | 6 个源文件 |
| SRC-ORDER-JAVA | 代码 | `order-service/src/main/java/com/demo/order/**` | 入口、控制器、服务、Mapper、实体、消息 | 9 个源文件 |
| SRC-ORDER-TEST | 测试 | `order-service/src/test/java/com/demo/order/OrderServiceTest.java` | 状态机行为规格 | 使用 JUnit 5，但 pom 未声明测试依赖（Q-H1） |
| SRC-WEB-PORTAL | 前端代码与构建 | `web-portal/**`（`package.json`、`vite.config.js`、`src/**`） | 应用装配、路由、请求封装、页面 | 无锁文件（Q-L1） |
| SRC-GIT-HISTORY | Git | `54959c91e603b42092331bf5ba3d90107bdb2bf1..HEAD` | 提交历史 | 两个提交：init、导出保留期修复 30→7 天 |

## 数据模型证据

| 证据 ID | 类型 | 路径 | 覆盖范围 | 证据状态 |
|---------|------|------|----------|----------|
| SRC-DDL | DDL | `db/init.sql` | demo_user、demo_account、demo_order 三库 4 表 | DDL 已确认 |
| SRC-MAPPER-USER | Mapper XML | `user-service/src/main/resources/mapper/UserMapper.xml` | `t_user` 查询映射 | 代码可推导 |
| SRC-MAPPER-ACCOUNT | Mapper XML | `account-service/src/main/resources/mapper/AccountMapper.xml` | `t_user_account` 查询映射（`SELECT *`，无 `resultMap`） | 代码可推导（Q-M3） |
| SRC-MAPPER-ORDER | Mapper XML | `order-service/src/main/resources/mapper/OrderMapper.xml` | `t_order` 查询与状态更新 | 代码可推导 |
| SRC-ENTITY-* | Entity | 三个 `entity/*Entity.java` | 字段与注释 | 代码可推导 |
| 迁移/手写 SQL/人工资料 | - | 未声明 | - | 不适用（`evidence.data_model_sources` 中 migrations/sql/manual 为空列表） |

## 配置证据

| 证据 ID | 类型 | 路径 | 覆盖范围 | 说明 |
|---------|------|------|----------|------|
| SRC-SNAPSHOT-BASELINE | 外部不可变快照 | `/home/tester/work/snapshots/baseline-config`（只读） | 3 个 `application.yml` | 指纹 92bb968da5721d10403cbe72a128a492ea6c5fa2220788b736f9adab743aa71b；首次计算 == 结束计算 == Manifest 授权指纹 |
| SRC-CONFIG-USER | 配置文件 | `user-service/src/main/resources/application.yml` | 5 键 | 与快照内容一致（运行内比对，未记录哈希） |
| SRC-CONFIG-ACCOUNT | 配置文件 | `account-service/src/main/resources/application.yml` | 7 键 | 同上 |
| SRC-CONFIG-ORDER | 配置文件 | `order-service/src/main/resources/application.yml` | 5 键 | 同上；未发现数据源键（Q-M6） |
| 配置中心/远程配置 | - | 未连接 | - | 按规则禁止访问 |

## 中间件与横切机制证据

| 证据 ID | 类型 | 路径 | 覆盖范围 | 说明 |
|---------|------|------|----------|------|
| SRC-MQ-PRODUCER | 代码 | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java` | 事件生产与常量 | `order.exchange` / `order.paid` |
| SRC-MQ-LISTENER | 代码 | `order-service/src/main/java/com/demo/order/mq/OrderEventListener.java` | 事件消费与队列绑定 | `order.paid.queue`（durable） |
| SRC-RECONCILE | 代码 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java` | 定时调度与重试声明 | `@Scheduled`；无 `@EnableScheduling`（Q-M1） |
| SRC-REQUEST-WRAPPER | 代码 | `web-portal/src/api/request.js` | 前端统一请求封装 | axios 实例 |
| SRC-STATE-MACHINE | 代码 + 测试 | `order-service/.../service/OrderService.java`、`entity/OrderStatus.java`、`src/test/.../OrderServiceTest.java` | 订单状态机规则 | 业务规则候选 |

## 用户资料证据

| 证据 ID | 类型 | 路径 | 覆盖范围 |
|---------|------|------|----------|
| SRC-INPUT-BASE | 用户输入 | `cadence/knowledge-base/user-input/base-info.md` | 六领域范围声明 |
| SRC-INPUT-PRODUCT | 用户输入 | `cadence/knowledge-base/user-input/product.md` | 产品目的、目标用户、关键特性（业务目标未提供） |
| SRC-INPUT-SCOPE-* | 用户输入 | `project-scope.md`、`data-model-scope.md`、`configuration-scope.md`、`middleware-scope.md`、`api-scope.md`、`page-scope.md` | 各领域授权范围 |
| SRC-INPUT-INVENTORY | 用户输入清单 | `cadence/knowledge-base/input-inventory.md` | 输入解析与快照校验结论 |

## 工具降级与未覆盖范围

- 未提供 CodeGraph 与 `ast-grep outline`，本次使用有界文本检索与定向阅读；降级未扩大任何授权范围。
- 未发现 CI 配置、部署/发布/启动脚本、迁移工具、前端锁文件、日志与可观测性配置，因此相关结论标记 `待确认` 或记录为“未发现”。
- 未连接数据库、配置中心或任何外部系统；数据库事实仅来自授权 DDL、Mapper 与代码。

## API 与集成能力证据（api 阶段）

| 证据 ID | 类型 | 路径或来源 | 覆盖范围 | 说明 |
|---------|------|------------|----------|------|
| SRC-API-SCOPE | 用户输入 | `cadence/knowledge-base/user-input/api-scope.md` | 对外能力清单 2 条、能力组合诉求 1 条 | 对外分类的唯一权威来源 |
| SRC-API-CTRL-USER | 代码 | `user-service/src/main/java/com/demo/user/controller/UserBasicController.java` | `API-user-basic` 入口 | `GET /api/user/basic/{userId}`，直接返回实体 |
| SRC-API-CTRL-ACCOUNT | 代码 | `account-service/src/main/java/com/demo/account/controller/AccountController.java` | `API-account-query`（对内） | 类注释自称“对外能力 API-B”，与用户清单冲突（Q-M7） |
| SRC-API-CTRL-ORDER | 代码 | `order-service/src/main/java/com/demo/order/controller/OrderController.java` | `API-order-ship`（对内） | `POST /api/order/{orderId}/ship` |
| SRC-API-CTRL-EXPORT | 代码 | `order-service/src/main/java/com/demo/order/controller/ExportController.java` | `API-order-export` 入口 | 存根实现，返回字面量 `taskId`（Q-H2） |
| SRC-API-STATE-MACHINE | 代码 + 测试 | `order-service/src/main/java/com/demo/order/service/OrderService.java`、`entity/OrderStatus.java`、`src/test/java/com/demo/order/OrderServiceTest.java` | 发货状态机规则 | 测试依赖未在 `pom.xml` 声明（Q-H1） |
| SRC-API-EVENT | 代码 | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java`、`mq/OrderEventListener.java` | `EVENT-order-paid` | exchange `order.exchange`、routing key `order.paid`、queue `order.paid.queue`；生产触发点不可达（Q-M10） |
| SRC-API-JOB | 代码 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java` | `JOB-reconcile` | 空实现；未发现 `@EnableScheduling`（Q-M1、Q-M2） |
| SRC-API-FILE | 代码 + DDL | `order-service/src/main/java/com/demo/order/service/ExportService.java`、`db/init.sql` | `FILE-order-export-file` | 仅保留期常量与登记表 DDL，无文件生成/登记/清理实现（Q-M4） |
| SRC-API-WEB | 前端代码 | `web-portal/src/api/request.js`、`src/api/index.js`、`src/views/*.vue` | 前端调用关系（4 个后端路径） | 调用方证据；web-portal 自身无接口能力（api 导航为“已验证为空”） |
| SRC-API-DOCS | KnowledgeBase 文档 | `cadence/knowledge-base/interfaces/README.md` 及各能力主文件、配套参数与报文文件 | 对外 2 项、对内 5 项能力 | 本阶段产出物索引 |

## 页面能力证据（pages 阶段）

| 证据 ID | 类型 | 路径或来源 | 覆盖范围 | 说明 |
|---------|------|------------|----------|------|
| SRC-PAGE-SCOPE | 用户输入 | `cadence/knowledge-base/user-input/page-scope.md` | 前端应用清单（web-portal）与路由来源声明 | 声明“代码静态路由（src/main.js）”，与代码证据一致 |
| SRC-PAGE-ROUTES | 代码 | `web-portal/src/main.js` | 3 条静态路由与组件装配（`/users`、`/orders`、`/accounts`） | `createWebHistory`；无 `meta`、无守卫、无懒加载 |
| SRC-PAGE-SHELL | 代码 | `web-portal/src/App.vue` | 根组件与渲染出口 | 仅 `<router-view />`，无 Layout 与菜单入口（Q-M12） |
| SRC-PAGE-REQUEST | 代码 | `web-portal/src/api/request.js`、`web-portal/src/api/index.js` | 统一请求封装与 4 个接口函数 | `baseURL: /api`；页面调用位置证据 |
| SRC-PAGE-VIEWS | 代码 | `web-portal/src/views/UserList.vue`、`AccountPage.vue`、`OrderPage.vue` | 3 个页面组件的展示字段与操作行为 | 请求参数均为硬编码 `1`（Q-L7）；账户字段依赖隐式映射（Q-M3） |
| SRC-PAGE-BUILD | 构建 | `web-portal/package.json`、`web-portal/vite.config.js` | 依赖范围与开发代理 | 无锁文件（Q-L1）；代理单一目标端点（Q-L4）；仓库内未发现 `index.html`（Q-H3） |
| SRC-PAGE-DOCS | KnowledgeBase 文档 | `cadence/knowledge-base/pages/README.md` 与 `pages/PAGE-*.md` | 页面索引与 3 个单页面能力文档 | 本阶段产出物索引 |
