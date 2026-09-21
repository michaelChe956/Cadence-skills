# user-service

## 职责与边界

- 稳定 ID：`SERVICE-user-service`；类型：Java 后端（Spring Boot 3.2.5 + MyBatis，Java 17）。
- 职责：维护并对外提供用户基本信息（`t_user`）查询能力 [代码证据]（`user-service/src/main/java/com/demo/user/UserBasicController.java:7-22`、`UserBasicService.java:17-20`）。
- 边界内：用户基本信息的读取与对外 HTTP 暴露；不包含账户、订单域逻辑。
- 边界外：账户余额与状态（属于 `SERVICE-account-service`）、订单状态与事件（属于 `SERVICE-order-service`）。
- 数据写入：本服务未发现写入 `t_user` 的映射或调用。
- 项目定位引用 [用户提供]：为商城运营方提供用户、账户与订单的统一管理能力（`user-input/product.md`）。

## 模块与入口

| 模块 ID | 职责 | 关键类或文件 | 证据 |
|---------|------|--------------|------|
| MODULE-user-basic | 用户基本信息查询链路 | `UserBasicController`、`UserBasicService`、`UserMapper`、`UserEntity` | `user-service/src/main/java/com/demo/user/**` |

| 入口类型 | 入口 | 说明 | 证据 |
|----------|------|------|------|
| 进程入口 | `com.demo.user.UserApplication`（`@SpringBootApplication`） | Spring Boot 启动类，组件扫描 `com.demo.user` | `user-service/src/main/java/com/demo/user/UserApplication.java:8-11` |
| HTTP 入口 | `GET /api/user/basic/{userId}` | 返回用户基本信息实体 | `user-service/src/main/java/com/demo/user/controller/UserBasicController.java:9,19-21` |
| 监听端口 | `server.port` 配置键（值见 `configurations/SERVICE-user-service.md`） | 端口值非敏感，记录于配置文档 | `user-service/src/main/resources/application.yml:1-2` |

## 数据模型

| 逻辑表稳定 ID | 数据库/Schema | 读/写 | 映射入口 | 证据 |
|----------------|---------------|-------|----------|------|
| TABLE-t_user | DB-demo_user | 读 | `UserMapper.selectById` / `UserMapper.xml#selectById` | `user-service/src/main/resources/mapper/UserMapper.xml:4-7` |

- 详细字段清单：`data-models/DB-demo_user/TABLE-t_user.md`
- 与 `t_user_account.user_id`、`t_order.user_id` 的同源关系为候选关系（DDL 未声明外键，见 `open-questions.md` Q-M5）。

## 配置

- 配置状态：`全量`（`scope.configurations` 已纳入本服务）。
- 来源：`src/main/resources/application.yml`（键数与清单见 `configurations/SERVICE-user-service.md`）。
- 快照：`baseline-config-v1`（开发 fixture 本地快照），指纹与分析前后校验见 `configurations/README.md`。
- 本行程仅记录键名、用途与值类型，敏感值统一 `<redacted>`。

## 中间件

| 中间件 ID | 装配状态 | 证据 |
|------------|----------|------|
| MIDDLEWARE-mysql | 已装配（开发 fixture 快照；生产装配未确认） | `user-service/pom.xml:16`、数据源配置键、`UserMapper.xml` |

未发现本服务的其他中间件依赖。

## API

- 阶段状态：已分析（api）
- API 导航：

| API 稳定 ID | 能力名称 | 分类 | 类型 | 状态 | 主文件 | 参数与报文 |
|-------------|----------|------|------|------|--------|------------|
| `API-user-basic` | 查询用户基本信息 | 对外 | REST | 已声明、已实现、已装配、已暴露 | [`API-user-basic_查询用户基本信息_queryBasic.md`](../interfaces/API-user-basic_查询用户基本信息_queryBasic.md) | [`参数与报文`](../interfaces/API-user-basic_查询用户基本信息_queryBasic_参数与报文.md) |

- 调用方：客户端（用户清单）、`web-portal` 用户列表页（`web-portal/src/api/index.js:2`、`src/views/UserList.vue:12`）。
- 证据：`user-service/src/main/java/com/demo/user/controller/UserBasicController.java:19-21`；总索引 `interfaces/README.md`。

## 页面

- 阶段状态：已分析（pages）
- 页面导航（消费本服务 API 的页面；页面由 `SERVICE-web-portal` 承载）：

| PAGE 稳定 ID | ROUTE 稳定 ID | 路由路径 | 页面主文件 | 关系证据 |
|--------------|---------------|----------|------------|----------|
| `PAGE-user-list` | `ROUTE-web-portal-users` | `/users` | [`PAGE-user-list`](../pages/PAGE-user-list.md) | 页面 → `API-user-basic` → `MODULE-user-basic`（`web-portal/src/views/UserList.vue:12`、`web-portal/src/api/index.js:2`、`user-service/src/main/java/com/demo/user/controller/UserBasicController.java:19-21`） |

- 说明：本服务不承载前端页面；上表页面经 `API-user-basic` 调用本服务。
- 证据：`web-portal/src/main.js:4,11`、`web-portal/src/views/UserList.vue:1-13`；页面索引 `pages/README.md`。

## 横切机制

| 机制 | 状态 | 证据 |
|------|------|------|
| 认证/授权 | 未发现（无 Spring Security 依赖或鉴权代码） | 三个 `pom.xml` 依赖清单 |
| 事务边界 | 未发现（无 `@Transactional`） | `user-service/src/main/java/com/demo/user/**` |
| 全局异常处理 | 未发现（无 `@ControllerAdvice`） | 同上 |
| 可观测性 | 未发现（无日志/指标/Trace 依赖或配置） | 同上 |

## 构建验证

| 场景 | 命令 | 状态 | 来源 |
|------|------|------|------|
| 构建 | `mvn -f user-service/pom.xml package` | 未执行（只读分析；Maven 依赖需联网解析） | `user-service/pom.xml` |
| 测试 | 未发现本服务测试源码与测试依赖 | 不适用 | `user-service/pom.xml`、`user-service/src/test` 不存在 |
| 启动 | 未确认（`pom.xml` 未声明 `spring-boot-maven-plugin`，无启动脚本） | 待确认 | `user-service/pom.xml:13-17` |

## 证据导航

- 入口与装配：`user-service/src/main/java/com/demo/user/UserApplication.java`
- HTTP 入口：`user-service/src/main/java/com/demo/user/controller/UserBasicController.java:19-21`
- 数据访问：`user-service/src/main/resources/mapper/UserMapper.xml:4-7`、`user-service/src/main/java/com/demo/user/mapper/UserMapper.java:10`
- 配置：`user-service/src/main/resources/application.yml`
- 相关文档：`services/README.md`、`data-models/DB-demo_user/TABLE-t_user.md`、`configurations/SERVICE-user-service.md`
