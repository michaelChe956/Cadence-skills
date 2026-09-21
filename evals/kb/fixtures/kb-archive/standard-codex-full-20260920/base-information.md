# 项目基础信息

## 文档元数据

- 生成时间：2026-09-20
- Git 分支：master
- 基线提交：1f867b9fcdf95f2e11808454898f333d7d512e90
- 执行模式：续跑（初始化 `in_progress`，本次执行 `base-info` 阶段）
- 输入来源：`cadence/knowledge-base/user-input/`（base-info.md、project-scope.md、data-model-scope.md、configuration-scope.md、middleware-scope.md、api-scope.md、page-scope.md、product.md）、`cadence/knowledge-base/input-inventory.md`、`cadence/knowledge-base/manifest.yaml`
- 未覆盖范围：API/页面/业务域/组合能力明细（`api`、`pages`、`overview` 阶段）；web-portal 前端构建配置（`scope.configurations` 未纳入）；生产环境配置与运行态中间件；Node 依赖锁定版本。

## 1. 项目与仓库

- 仓库稳定 ID：`REPO-demo-commerce`，本地路径 `.`（单仓多模块），分支 `master`，基线提交 `1f867b9fcdf95f2e11808454898f333d7d512e90`。
- 项目定位：为商城运营方提供用户、账户与订单的统一管理能力；目标用户为内部运营人员；关键特性为用户信息查询、账户查询、订单管理与导出 [用户提供]（`user-input/product.md`）。业务目标：未提供。
- 纳入范围（`scope.projects` 状态 `全量`，来源 `user-input/project-scope.md`）：
  - `user-service`（`./user-service`，Java 后端）
  - `account-service`（`./account-service`，Java 后端）
  - `order-service`（`./order-service`，Java 后端）
  - `web-portal`（`./web-portal`，Vue3 前端）
- Git 历史范围：`54959c91e603b42092331bf5ba3d90107bdb2bf1..HEAD`，范围内仅两个提交：`54959c9`（init: demo 商城初始版本）、`1f867b9`（修复：导出文件保留期应为 7 天，原误配 30 天）[代码证据]。
- 排除范围：`.idea`、`.gitkeep`、空文件与历史备份（默认排除规则）；仓库根 `README.md` 自述为过时文档，不作为当前工程结构依据。
- 未覆盖范围：未发现 CI 配置、容器化文件、部署/发布/启动脚本、数据库迁移工具与前端锁文件；配置授权范围不含 `web-portal`。

## 2. 技术栈

| 技术 | 版本 | 使用位置 | 证据 | 可信度 |
|------|------|----------|------|--------|
| Java | 17 | user-service、account-service、order-service | `user-service/pom.xml:12`、`account-service/pom.xml:12`、`order-service/pom.xml:12` | 已确认 |
| Spring Boot | 3.2.5（parent） | 三个后端服务 | `user-service/pom.xml:4-8` 及另两个同名段落 | 已确认 |
| spring-boot-starter-web | 由 parent 管理（3.2.5 体系） | 三个后端服务 | 三个 `pom.xml` dependencies | 已确认 |
| MyBatis Spring Boot Starter | 3.0.3 | 三个后端服务数据访问 | `user-service/pom.xml:15`、`account-service/pom.xml:15`、`order-service/pom.xml:15` | 已确认 |
| mysql-connector-java | 8.0.33 | 三个后端服务数据源驱动 | `user-service/pom.xml:16`、`account-service/pom.xml:16`、`order-service/pom.xml:16` | 已确认 |
| spring-boot-starter-amqp | 由 parent 管理（3.2.5 体系） | order-service 消息生产与消费 | `order-service/pom.xml:17` | 已确认 |
| Maven（无 wrapper） | 未声明 | 三个后端服务构建 | 三个 `pom.xml`；未发现 `mvnw`/`.mvn` | 合理推断 |
| MySQL 服务端 | 未确认 | demo_user、demo_account、demo_order | `db/init.sql`（MySQL 方言）、驱动 8.0.33 | 待确认 |
| Vue | 声明 `^3.4.0` | web-portal | `web-portal/package.json:5` | 声明范围已确认，精确解析版本待确认 |
| vue-router | 声明 `^4.3.0` | web-portal 路由 | `web-portal/package.json:5` | 同上 |
| axios | 声明 `^1.6.0` | web-portal 请求封装 | `web-portal/package.json:5` | 同上 |
| vite | 声明 `^5.2.0`（devDependency） | web-portal 构建与开发服务器 | `web-portal/package.json:6` | 同上 |
| JUnit 5（org.junit.jupiter） | 未声明依赖 | order-service 测试源码 | `order-service/src/test/java/com/demo/order/OrderServiceTest.java:8`；三个 `pom.xml` 均未声明测试依赖 | 来源冲突（见 Q-H1） |

未发现：Spring Security、Spring Data JPA、MyBatis-Plus、Flyway/Liquibase、Redis 客户端、日志与可观测性依赖、前端锁文件、CI 配置、Docker/部署描述文件。

## 3. 服务与模块

> 本章节只保存服务与模块摘要及导航。完整职责边界、领域关系、构建验证和证据导航见 `services/README.md` 及各单服务文档。

- 服务总索引：`services/README.md`

| ID | 名称 | 类型 | 职责 | 入口 | 依赖 | 状态 | 文档链接 | 证据 |
|----|------|------|------|------|------|------|----------|------|
| SERVICE-user-service | user-service | Java 后端（Spring Boot） | 维护并对外提供用户基本信息查询 | `com.demo.user.UserApplication` | MySQL `demo_user`、MyBatis | 已识别 | `services/SERVICE-user-service.md` | `user-service/src/main/java/com/demo/user/UserApplication.java:6-11` |
| SERVICE-account-service | account-service | Java 后端（Spring Boot） | 维护用户账户查询与每日对账 | `com.demo.account.AccountApplication` | MySQL `demo_account`、MyBatis | 已识别 | `services/SERVICE-account-service.md` | `account-service/src/main/java/com/demo/account/AccountApplication.java:6-11` |
| SERVICE-order-service | order-service | Java 后端（Spring Boot） | 订单状态机、订单导出与订单事件收发 | `com.demo.order.OrderApplication` | MySQL `demo_order`、RabbitMQ、MyBatis | 已识别 | `services/SERVICE-order-service.md` | `order-service/src/main/java/com/demo/order/OrderApplication.java:6-11` |
| SERVICE-web-portal | web-portal | Vue3 前端（Vite SPA） | 运营门户：用户、账户、订单页面 | `web-portal/src/main.js`（`#app` 挂载） | HTTP 调用后端服务、vue-router、axios | 已识别 | `services/SERVICE-web-portal.md` | `web-portal/src/main.js:8-15` |

模块：`MODULE-user-basic`、`MODULE-account-core`、`MODULE-account-reconcile`、`MODULE-order-core`、`MODULE-order-export`、`MODULE-order-event`、`MODULE-web-portal-app`、`MODULE-web-portal-api`、`MODULE-web-portal-views`（模块归属见各单服务文档与 `services/README.md`）。

## 4. 数据模型

> 本章节只保存摘要与导航。完整字段清单、索引与约束证据、Mapper/SQL 映射和读写服务见 `data-models/README.md` 及各逻辑表文档。

### 当前范围与覆盖率

| 数据模型状态 | 数据库/Schema 数 | 逻辑表数 | 已生成字段级文档 | 待确认对象 | 证据基线 |
|--------------|-----------------|----------|------------------|------------|----------|
| 全量 | 3 | 4 | 4 | 2 类：`TABLE-t_export_file` 读写服务未确认；跨库同名 `user_id` 关联未确认外键 | 1f867b9fcdf95f2e11808454898f333d7d512e90 |

### 数据库与 Schema 导航

| 稳定 ID | 数据库/Schema | 业务域 | 逻辑表数 | 证据状态 | 索引链接 |
|---------|---------------|--------|----------|----------|----------|
| DB-demo_user | demo_user | 用户基本信息 | 1 | DDL 已确认 | `data-models/DB-demo_user/README.md` |
| DB-demo_account | demo_account | 用户账户 | 1 | DDL 已确认 | `data-models/DB-demo_account/README.md` |
| DB-demo_order | demo_order | 订单与导出文件 | 2 | DDL 已确认 | `data-models/DB-demo_order/README.md` |

### 关键关系与分库分表摘要

| 逻辑表稳定 ID | 业务含义 | 主要关系 | 读服务 | 写服务 | 分片摘要 | 文档链接 |
|----------------|----------|----------|--------|--------|----------|----------|
| TABLE-t_user | 用户基本信息表 | `user_id` 与 `t_user_account.user_id`、`t_order.user_id` 同源（候选关系，DDL 未声明外键） | SERVICE-user-service | 未发现写入 | 未发现分片 | `data-models/DB-demo_user/TABLE-t_user.md` |
| TABLE-t_user_account | 用户账户表 | `user_id` 指向 `t_user.user_id`（候选关系）；`uk_account_no` 唯一约束 | SERVICE-account-service | 未发现写入（对账实现未提供） | 未发现分片 | `data-models/DB-demo_account/TABLE-t_user_account.md` |
| TABLE-t_order | 订单表 | `user_id` 指向 `t_user.user_id`（候选关系）；状态迁移受状态机约束 | SERVICE-order-service | SERVICE-order-service（`OrderMapper.xml#updateStatus`） | 未发现分片 | `data-models/DB-demo_order/TABLE-t_order.md` |
| TABLE-t_export_file | 订单导出文件登记表 | `order_id` 关联订单（候选关系，无语义约束证据） | 未发现 | 未发现 | 未发现分片 | `data-models/DB-demo_order/TABLE-t_export_file.md` |

未发现分库分表配置、路由规则或物理分片表；4 张表均为单一逻辑表。

### 来源冲突与未覆盖范围

| 对象稳定 ID | 问题 | 影响 | 处理状态 | 详情链接 |
|-------------|------|------|----------|----------|
| TABLE-t_user_account | `AccountMapper.xml` 使用 `SELECT *` 且未维护 `resultMap`，`account_no → accountNo` 依赖未确认的驼峰映射设置 | 账户查询字段映射可能失效 | 待确认（Q-M3） | `data-models/DB-demo_account/TABLE-t_user_account.md` |
| TABLE-t_export_file | 仅有 DDL 与导出保留期常量，未发现持久化调用或 Mapper | 导出登记链路无法确认 | 待确认（Q-M4） | `data-models/DB-demo_order/TABLE-t_export_file.md` |
| TABLE-t_user / TABLE-t_user_account / TABLE-t_order | 同名字段 `user_id` 与注释同源说明不能单独证明数据库外键 | 跨库关联只能作为候选关系 | 待确认（Q-M5） | `data-models/README.md` |

## 5. 配置体系

> 本章节只保存当前配置快照摘要与导航。完整配置键、代码绑定、生效条件、Profile 差异和来源冲突见 `configurations/README.md` 及各服务配置文档。

### 当前配置快照

| 配置状态 | 快照标识 | 环境 | 发布批次 | 最终快照指纹 | 范围摘要 | 纳入文件数量或清单摘要 | 服务与规则摘要 | 分析前后校验 | 未覆盖范围 |
|----------|----------|------|----------|--------------|----------|--------------------------|----------------|--------------|------------|
| 全量 | baseline-config-v1 | 开发（fixture 本地快照） | fixture-batch-001 | 92bb968da5721d10403cbe72a128a492ea6c5fa2220788b736f9adab743aa71b | 三服务 application.yml 全量纳入（3 文件） | 3 个：account-service-application.yml、order-service-application.yml、user-service-application.yml | 服务：user-service、account-service、order-service；规则：仅 `src/main/resources/application.yml` | 首次计算 == 结束计算 == Manifest 授权指纹（一致） | web-portal 构建配置未授权；无历史快照可比对 |

### 配置来源与加载顺序

| 服务稳定 ID | 配置来源摘要 | 加载顺序摘要 | Profile | 证据 | 文档链接 |
|--------------|--------------|--------------|---------|------|----------|
| SERVICE-user-service | `src/main/resources/application.yml`（5 键） | Spring Boot 默认加载 `classpath:/application.yml`，未发现 profile 专用文件或外部覆盖 | 未声明（默认 default） | `user-service/src/main/resources/application.yml:1-9`；快照 `user-service-application.yml` | `configurations/SERVICE-user-service.md` |
| SERVICE-account-service | `src/main/resources/application.yml`（7 键） | 同上 | 未声明（默认 default） | `account-service/src/main/resources/application.yml:1-12`；快照 `account-service-application.yml` | `configurations/SERVICE-account-service.md` |
| SERVICE-order-service | `src/main/resources/application.yml`（5 键） | 同上 | 未声明（默认 default） | `order-service/src/main/resources/application.yml:1-9`；快照 `order-service-application.yml` | `configurations/SERVICE-order-service.md` |

### 配置组与影响能力

| 配置组稳定 ID | 用途 | 影响服务 | 关联代码 | 关联数据模型或中间件 | 状态 | 文档链接 |
|----------------|------|----------|----------|----------------------|------|----------|
| CONFIGGROUP-user-server | 用户服务 HTTP 端口 | SERVICE-user-service | 未发现显式绑定（Spring Boot 内置） | 未发现 | 存在 | `configurations/SERVICE-user-service.md` |
| CONFIGGROUP-user-datasource | 用户库数据源连接 | SERVICE-user-service | MyBatis/DataSource 自动配置 | DB-demo_user、MIDDLEWARE-mysql | 存在 | `configurations/SERVICE-user-service.md` |
| CONFIGGROUP-account-server | 账户服务 HTTP 端口 | SERVICE-account-service | 未发现显式绑定（Spring Boot 内置） | 未发现 | 存在 | `configurations/SERVICE-account-service.md` |
| CONFIGGROUP-account-datasource | 账户库数据源连接 | SERVICE-account-service | MyBatis/DataSource 自动配置 | DB-demo_account、MIDDLEWARE-mysql | 存在 | `configurations/SERVICE-account-service.md` |
| CONFIGGROUP-account-reconcile | 对账任务开关与重试次数 | SERVICE-account-service | 仅 `ReconcileJob` 类注释声明，未发现绑定代码 | 未发现 | 待确认 | `configurations/SERVICE-account-service.md` |
| CONFIGGROUP-order-server | 订单服务 HTTP 端口 | SERVICE-order-service | 未发现显式绑定（Spring Boot 内置） | 未发现 | 存在 | `configurations/SERVICE-order-service.md` |
| CONFIGGROUP-order-datasource | 订单库数据源连接（授权配置中未出现数据源键） | SERVICE-order-service | MyBatis/DataSource 自动配置 | DB-demo_order、MIDDLEWARE-mysql | 缺失 | `configurations/SERVICE-order-service.md` |
| CONFIGGROUP-order-rabbitmq | RabbitMQ 连接 | SERVICE-order-service | RabbitAutoConfiguration、`RabbitTemplate`、`@RabbitListener` | MIDDLEWARE-rabbitmq | 存在 | `configurations/SERVICE-order-service.md` |

### 风险与待确认摘要

| 对象稳定 ID | 风险或来源冲突 | 影响 | 处理状态 | 详情链接 |
|--------------|----------------|------|----------|----------|
| CONFIGGROUP-account-reconcile | `reconcile.enabled` / `reconcile.retry-times` 无代码绑定，仅有类注释声明 | 配置是否生效无法确认 | 待确认（Q-M2） | `configurations/SERVICE-account-service.md` |
| CONFIGGROUP-account-datasource | 快照为开发 fixture，数据源指向非本机地址键存在但值已脱敏，生产环境未确认 | 不能作为生产数据源事实 | 待确认（Q-M6） | `configurations/SERVICE-account-service.md` |
| CONFIGGROUP-order-rabbitmq | 仅 `host`/`username`/`password`，未发现 exchange/queue 配置键（名称硬编码于代码常量） | 运行环境需另行确认队列绑定 | 已记录 | `configurations/SERVICE-order-service.md` |

### 配置导航

- 配置总索引：`configurations/README.md`
- 服务配置文档：见配置总索引的“服务配置导航”。

## 6. 中间件

| 范围状态 | 授权摘要或 selected | 原因 | 未覆盖范围 |
|----------|---------------------|------|------------|
| 全量 | MySQL、RabbitMQ（来源 `user-input/middleware-scope.md`） | 不适用 | 未确认生产环境中间件拓扑与版本；未授权其他工程的中间件 |

| ID | 中间件 | 版本 | 场景 | 生产者 | 消费者 | 状态 | 证据 |
|----|--------|------|------|--------|--------|------|------|
| MIDDLEWARE-mysql | MySQL | 未确认（驱动 8.0.33） | 三个业务库的关系型存储 | 未发现 | SERVICE-user-service、SERVICE-account-service、SERVICE-order-service（读写数据源） | 已装配（开发 fixture 快照；生产装配未确认） | `user-service/pom.xml:16`、`spring.datasource.*` 键、各 `*Mapper.xml` |
| MIDDLEWARE-rabbitmq | RabbitMQ | 未确认（starter 由 parent 管理） | 订单已支付事件收发（`order.exchange` / `order.paid` / `order.paid.queue`） | MODULE-order-event（`OrderEventProducer.sendOrderPaid`） | MODULE-order-event（`OrderEventListener.onOrderPaid`） | 已装配（代码与配置证据；生产装配未确认） | `order-service/pom.xml:17`、`OrderEventProducer.java:10-21`、`OrderEventListener.java:13-19`、`spring.rabbitmq.*` 键 |

依赖声明只证明可能使用；上表状态区分了代码/配置证据与生产装配事实。未发现 Redis、消息队列以外的中间件、注册中心、网关或缓存组件。

## 7. 横切关注点

| 横切机制稳定 ID | 机制 | 实现位置 | 关联配置 | 证据状态 | 说明 |
|------------------|------|----------|----------|----------|------|
| CONCERN-frontend-request-wrapper | 前端统一 HTTP 请求封装（baseURL 与超时统一注入） | `web-portal/src/api/request.js:3` | 不在配置授权范围 | 已确认（代码） | 各页面经 `web-portal/src/api/index.js` 调用 |
| CONCERN-scheduled-reconcile | 定时调度与重试 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:14-17` | CONFIGGROUP-account-reconcile | 待确认（缺 `@EnableScheduling` 与绑定代码） | 见 Q-M1、Q-M2 |
| CONCERN-annotation-driven-messaging | 注解驱动消息生产与消费（隐式调用） | `order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java:19-21`、`OrderEventListener.java:13-19` | CONFIGGROUP-order-rabbitmq | 已确认（代码，含配置键） | 生产环境可达性未测 |
| CONCERN-order-state-machine | 订单状态机约束（已取消不可发货、仅已支付可发货） | `order-service/src/main/java/com/demo/order/service/OrderService.java:25-35`、`OrderStatus.java:3-9` | 未发现专用配置 | 已确认（代码 + 测试规格） | 业务规则候选，待 `overview` 登记 |

未发现：认证/授权链（无 Spring Security 依赖）、`@Transactional` 事务边界、全局异常处理器、审计、幂等与限流组件、日志 Trace/Metrics 配置。

## 8. 部署与外部依赖

- 运行形态：三个独立 Spring Boot 应用（端口键 8081/8082/8083）+ 一个 Vite 单页应用；未见网关工程。
- 外部依赖：MySQL（三库）、RabbitMQ（订单事件）、前端经 HTTP 调用后端（代理目标为内部端点，值 `<redacted>`）。
- 未发现部署描述、发布脚本、启动脚本、容器编排或 CI 配置，因此部署方式与加载顺序只能依据 Spring Boot 默认约定 [合理推断]。
- 本次分析未运行任何应用、迁移、部署或启动脚本。

## 9. 风险与来源冲突

| 对象稳定 ID | 风险或冲突 | 影响 | 状态 |
|--------------|------------|------|------|
| REPO-demo-commerce | 仓库根 `README.md` 自述过时，仅描述 user-service | 误导导航；以代码与 Manifest 为准 | 已登记（Q-L2） |
| TABLE-t_user_account | `SELECT *` + 无 `resultMap`，映射依赖未确认设置 | 字段映射结果不确定 | 待确认（Q-M3） |
| CONFIGGROUP-account-reconcile | 配置键缺代码绑定，且缺 `@EnableScheduling` | 定时任务可能未生效 | 待确认（Q-M1、Q-M2） |
| 三服务配置 | 授权快照为开发 fixture，生产配置未知 | 不能把开发配置升级为生产事实 | 已记录 |

## 10. 待人工确认

- Q-H1、Q-M1 至 Q-M6、Q-L1 至 Q-L5 见 `open-questions.md`（未解决计数：blocking 0、high 1、medium 6、low 5）。
- API/页面/业务域/组合能力等未执行领域的明细由 `api`、`pages`、`overview` 阶段补齐。
