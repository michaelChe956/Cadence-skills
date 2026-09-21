# account-service

## 职责与边界

- 稳定 ID：`SERVICE-account-service`；类型：Java 后端（Spring Boot 3.2.5 + MyBatis，Java 17）。
- 职责：提供用户账户信息查询，并包含每日账户对账任务 [代码证据]（`account-service/src/main/java/com/demo/account/controller/AccountController.java:7-22`、`job/ReconcileJob.java:6-17`）。
- 边界内：账户号、余额、状态的读取；对账任务调度声明。
- 边界外：用户基本信息（`SERVICE-user-service`）、订单与导出（`SERVICE-order-service`）。
- 数据写入：未发现写入 `t_user_account` 的映射；对账实现未提供（fixture 静态样本），写入链路待确认（Q-M4 关联项）。

## 模块与入口

| 模块 ID | 职责 | 关键类或文件 | 证据 |
|---------|------|--------------|------|
| MODULE-account-core | 账户查询链路 | `AccountController`、`AccountService`、`AccountMapper`、`AccountEntity` | `account-service/src/main/java/com/demo/account/{controller,service,mapper,entity}` |
| MODULE-account-reconcile | 每日对账定时任务 | `ReconcileJob` | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:11-17` |

| 入口类型 | 入口 | 说明 | 证据 |
|----------|------|------|------|
| 进程入口 | `com.demo.account.AccountApplication`（`@SpringBootApplication`） | 启动类，组件扫描 `com.demo.account` | `account-service/src/main/java/com/demo/account/AccountApplication.java:8-11` |
| HTTP 入口 | `GET /api/account/{userId}` | 返回账户信息实体；注释标注为对内 REST，供聚合能力复用 | `account-service/src/main/java/com/demo/account/controller/AccountController.java:9,19-21` |
| 定时入口 | `@Scheduled(cron = "0 0 2 * * ?")` | 启用条件待确认（未发现 `@EnableScheduling`） | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:14` |
| 监听端口 | `server.port` 配置键 | 端口值非敏感，记录于配置文档 | `account-service/src/main/resources/application.yml:1-2` |

## 数据模型

| 逻辑表稳定 ID | 数据库/Schema | 读/写 | 映射入口 | 证据 |
|----------------|---------------|-------|----------|------|
| TABLE-t_user_account | DB-demo_account | 读 | `AccountMapper.selectByUserId` / `AccountMapper.xml#selectByUserId` | `account-service/src/main/resources/mapper/AccountMapper.xml:5-7` |

- 详细字段清单：`data-models/DB-demo_account/TABLE-t_user_account.md`
- 映射风险：`SELECT *` 且未维护 `resultMap`，字段映射依赖未确认的驼峰映射设置（Q-M3）。

## 配置

- 配置状态：`全量`（已纳入本服务）。
- 来源：`src/main/resources/application.yml`（键数与清单见 `configurations/SERVICE-account-service.md`）。
- 配置组：`CONFIGGROUP-account-server`、`CONFIGGROUP-account-datasource`、`CONFIGGROUP-account-reconcile`（对账组为 `待确认`）。
- 敏感值统一 `<redacted>`；快照指纹与范围摘要见 `configurations/README.md`。

## 中间件

| 中间件 ID | 装配状态 | 证据 |
|------------|----------|------|
| MIDDLEWARE-mysql | 已装配（开发 fixture 快照；生产装配未确认） | `account-service/pom.xml:16`、数据源配置键、`AccountMapper.xml` |

未发现本服务的其他中间件依赖（对账任务未发现消息队列或调度中间件配置证据）。

## API

- 阶段状态：已分析（api）
- API 导航：

| API 稳定 ID | 能力名称 | 分类 | 类型 | 状态 | 主文件 | 参数与报文 |
|-------------|----------|------|------|------|--------|------------|
| `API-account-query` | 账户信息查询接口 | 对内 | REST | 已实现、已装配、已暴露 | [`API-account-query_账户信息查询_queryAccount.md`](../interfaces/API-account-query_账户信息查询_queryAccount.md) | [`参数与报文`](../interfaces/API-account-query_账户信息查询_queryAccount_参数与报文.md) |
| `JOB-reconcile` | 每日账户对账任务 | 对内 | 任务 | 代码存在但不可达（空实现；未发现 `@EnableScheduling`） | [`JOB-reconcile_每日账户对账任务.md`](../interfaces/JOB-reconcile_每日账户对账任务.md) | 不适用（任务能力不生成配套文件） |

- 分类说明：`AccountController` 类注释自称“对外能力 API-B”，用户清单未登记，按规则保留对内分类（Q-M7）。
- 证据：`account-service/src/main/java/com/demo/account/controller/AccountController.java:19-22`、`job/ReconcileJob.java:14-17`；总索引 `interfaces/README.md`。

## 页面

- 阶段状态：已分析（pages）
- 页面导航（消费本服务 API 的页面；页面由 `SERVICE-web-portal` 承载）：

| PAGE 稳定 ID | ROUTE 稳定 ID | 路由路径 | 页面主文件 | 关系证据 |
|--------------|---------------|----------|------------|----------|
| `PAGE-account-query` | `ROUTE-web-portal-accounts` | `/accounts` | [`PAGE-account-query`](../pages/PAGE-account-query.md) | 页面 → `API-account-query` → `MODULE-account-core`（`web-portal/src/views/AccountPage.vue:12`、`web-portal/src/api/index.js:3`、`account-service/src/main/java/com/demo/account/controller/AccountController.java:19-22`） |

- 说明：本服务不承载前端页面；`JOB-reconcile` 无页面调用证据，未建立页面导航。
- 证据：`web-portal/src/main.js:6,13`、`web-portal/src/views/AccountPage.vue:1-13`；页面索引 `pages/README.md`。

## 横切机制

| 机制 | 状态 | 证据 |
|------|------|------|
| 定时调度/重试 | 待确认（缺 `@EnableScheduling`，重试键无绑定代码） | `ReconcileJob.java:8-17`、配置键 `reconcile.*` |
| 认证/授权 | 未发现 | `account-service/pom.xml:13-17` |
| 事务边界 | 未发现（无 `@Transactional`） | `account-service/src/main/java/com/demo/account/**` |
| 全局异常处理 | 未发现 | 同上 |
| 可观测性 | 未发现 | 同上 |

## 构建验证

| 场景 | 命令 | 状态 | 来源 |
|------|------|------|------|
| 构建 | `mvn -f account-service/pom.xml package` | 未执行（只读分析；Maven 依赖需联网解析） | `account-service/pom.xml` |
| 测试 | 未发现本服务测试源码与测试依赖 | 不适用 | `account-service/pom.xml`、`account-service/src/test` 不存在 |
| 启动 | 未确认（未声明 `spring-boot-maven-plugin`，无启动脚本） | 待确认 | `account-service/pom.xml:13-17` |

## 证据导航

- 入口与装配：`account-service/src/main/java/com/demo/account/AccountApplication.java`
- HTTP 入口：`account-service/src/main/java/com/demo/account/controller/AccountController.java:19-21`
- 定时任务：`account-service/src/main/java/com/demo/account/job/ReconcileJob.java:11-17`
- 数据访问：`account-service/src/main/resources/mapper/AccountMapper.xml:4-7`
- 配置：`account-service/src/main/resources/application.yml`
- 相关文档：`services/README.md`、`data-models/DB-demo_account/TABLE-t_user_account.md`、`configurations/SERVICE-account-service.md`
