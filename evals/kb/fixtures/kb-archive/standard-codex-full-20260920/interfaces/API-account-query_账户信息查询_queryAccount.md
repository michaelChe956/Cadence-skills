# API-account-query 账户信息查询接口（对内 REST）

> **能力 ID**：`API-account-query`
> **分类**：对内
> **能力类型**：REST
> **数据来源**：工程扫描（`account-service` 代码、`db/init.sql`、配置快照）、`user-input/api-scope.md` 能力组合诉求
> **梳理日期**：2026-09-20
> **参数与报文**：见同目录 `API-account-query_账户信息查询_queryAccount_参数与报文.md`

## 一、能力基础信息

| 项目 | 值 |
|------|----|
| 能力名称 | 账户信息查询接口 |
| API 名称或逻辑标识 | `queryAccount` |
| 分类 | 对内（用户对外能力清单未登记；见 5.1 分类冲突） |
| 能力类型 | REST |
| 协议与方法 | HTTP GET |
| 路径或逻辑地址 | `/api/account/{userId}` |
| 数据格式 | JSON（`AccountEntity` 直接序列化，未发现显式 `produces`） |
| 是否需授权 | 未发现鉴权实现（无 Spring Security 依赖、无过滤器） |
| 版本 | 未提供（代码未声明版本） |
| 调用方或生产者 | `web-portal` 账户查询页（`web-portal/src/api/index.js:3`、`web-portal/src/views/AccountPage.vue:12`）；`user-input/api-scope.md` 组合诉求“全部用户信息”的来源能力之一 |
| 落地方或消费者 | `SERVICE-account-service`（`MODULE-account-core`） |
| 生命周期状态 | 已实现、已装配、已暴露 |
| 数据来源表 | `TABLE-t_user_account`（只读） |

### 调用入口

| 环境 | 地址 | 证据状态 |
|------|------|----------|
| 开发（fixture 快照） | `http://localhost:8082/api/account/{userId}`（端口取 `server.port` 键，非敏感） | `account-service/src/main/resources/application.yml:1-2` |
| 生产 | 未提供（未发现网关或域名配置） | 待确认 |
| 前端访问路径 | `/api/account/{userId}`（合并 axios `baseURL: /api` 后） | `web-portal/src/api/index.js:3`，代理目标见 Q-L4 |

## 二、业务需求描述

- 按用户 ID 查询账户号、余额与账户状态（`AccountController.java:18`、`AccountEntity.java:4-13`）。
- 组合诉求引用：`user-input/api-scope.md:21` 将本接口列为“全部用户信息”组合能力的来源能力，连接键为 `userId`；连接键核实结论见 `interfaces/README.md`“能力组合诉求核实”。
- 余额业务硬约束：`t_user_account` 表注释声明“余额不可为负”（`db/init.sql:19,22`），本查询链路未做余额校验或修正（只读）。
- 账户状态取值：`NORMAL`/`FROZEN`/`CLOSED`（`db/init.sql:20`、`AccountEntity.java:11-12`）。

## 三、输入参数

详见 `API-account-query_账户信息查询_queryAccount_参数与报文.md` 第一节（路径参数 `userId`）。

## 四、输出参数

详见 `API-account-query_账户信息查询_queryAccount_参数与报文.md` 第二节（`userId`、`accountNo`、`balance`、`status`）。

## 五、代码实现定位

### 5.1 用户清单与代码映射

| 来源 | 标识 | 结论 | 证据 |
|------|------|------|------|
| 用户对外能力清单 | 未登记（`api-scope.md` 仅登记 `API-user-basic`、`API-order-export`） | 按规则归为对内能力 | `cadence/knowledge-base/user-input/api-scope.md:10-13` |
| 当前代码 | `AccountController` 类注释自称“对外能力 API-B” | 保留对内分类：用户清单是唯一权威，注释不能证明对外属性；分类冲突登记 Q-M7 | `account-service/src/main/java/com/demo/account/controller/AccountController.java:7` |
| 当前代码 | `AccountController#queryAccount` | 实现已定位 | `account-service/src/main/java/com/demo/account/controller/AccountController.java:19-22` |

### 5.2 实现清单

| 层级 | 符号 | 文件路径 | 状态 | 说明 |
|------|------|----------|------|------|
| 入口 | `com.demo.account.controller.AccountController#queryAccount` | `account-service/src/main/java/com/demo/account/controller/AccountController.java:19-22` | 已确认 | `@RestController` + `@RequestMapping("/api/account")` + `@GetMapping("/{userId}")` |
| 业务 | `com.demo.account.service.AccountService#queryAccount` | `account-service/src/main/java/com/demo/account/service/AccountService.java:18-20` | 已确认 | 直接委派 Mapper |
| 数据访问 | `com.demo.account.mapper.AccountMapper#selectByUserId` | `account-service/src/main/java/com/demo/account/mapper/AccountMapper.java:10` | 已确认 | `@Mapper`，参数 `@Param("userId")` |
| SQL | `AccountMapper.xml#selectByUserId` | `account-service/src/main/resources/mapper/AccountMapper.xml:5-7` | 来源冲突 | `SELECT * FROM t_user_account WHERE user_id = #{userId}`，无 `resultMap`，字段映射依赖隐式驼峰（Q-M3） |
| 模型 | `com.demo.account.entity.AccountEntity` | `account-service/src/main/java/com/demo/account/entity/AccountEntity.java:4-13` | 已确认 | 4 字段（不含表主键 `id`） |

## 六、调用链路

### 6.1 调用树

```text
API-account-query（GET /api/account/{userId}）
└─ SERVICE-account-service / MODULE-account-core
   ├─ AccountController.queryAccount（AccountController.java:19-22）
   │  └─ AccountService.queryAccount（AccountService.java:18-20）
   │     └─ AccountMapper.selectByUserId（AccountMapper.java:10）
   │        └─ AccountMapper.xml#selectByUserId（AccountMapper.xml:5-7）
   ├─ TABLE-t_user_account
   │  ├─ 条件：user_id = #{userId}（显式绑定）
   │  └─ 结果列：id/account_no/user_id/balance/status（SELECT *，映射见 7.1）
   └─ CONFIGURATION CONFIGGROUP-account-datasource
      └─ spring.datasource.url/username/password → DataSource/MyBatis 自动配置（无项目内显式绑定）
```

### 6.2 分支与触发条件

| 条件 | 路径 | 结果 | 证据 |
|------|------|------|------|
| 未发现分支条件（无 `if`/开关/灰度判断） | Controller → Service → Mapper | 恒定单路径查询 | `AccountController.java:19-22`、`AccountService.java:18-20` |
| 同一 `user_id` 存在多行 | `SELECT *` 无 `LIMIT` | MyBatis 单结果返回多行将抛 `TooManyResultsException`（未发现唯一约束限制） | `AccountMapper.xml:5-7`、`db/init.sql:14-22`（`user_id` 非唯一键）；待确认 |
| `reconcile.*` 配置为 `false` | 与本接口无调用关系（定时任务独立） | 不影响本接口 | `account-service/src/main/resources/application.yml:10-12` |

### 6.3 逐层调用明细

| 层级 | 符号 | 职责 | 下游 | 证据 |
|------|------|------|------|------|
| REST 入口 | `AccountController#queryAccount(Long)` | 绑定路径变量并返回实体 | `AccountService` | `AccountController.java:19-22` |
| 业务 | `AccountService#queryAccount(Long)` | 直接委派查询 | `AccountMapper` | `AccountService.java:18-20` |
| 数据访问 | `AccountMapper#selectByUserId` | 参数绑定 | `AccountMapper.xml#selectByUserId` | `AccountMapper.java:10` |
| SQL | `AccountMapper.xml#selectByUserId` | 按 `user_id` 等值查询 | `TABLE-t_user_account` | `AccountMapper.xml:5-7` |
| 装配 | `@SpringBootApplication` 组件扫描 `com.demo.account` | Controller/Service/Mapper 装配 | `SERVICE-account-service` | `AccountApplication.java:7-11` |

## 七、数据模型与配置依赖

### 7.1 数据模型影响

| TABLE 稳定 ID | Schema/逻辑表 | 读写 | 涉及字段 | API 模型映射 | Mapper/DAO/SQL | 表字段证据状态 | 端到端映射状态 | 表文档链接 |
|---------------|---------------|------|----------|--------------|----------------|------------------|------------------|------------|
| TABLE-t_user_account | `DB-demo_account` / `t_user_account` | R | 条件：`user_id`；读取：`id`（结果集含但 Entity 无对应字段）、`account_no`、`user_id`、`balance`、`status` | 请求 `userId` → `WHERE user_id = #{userId}`（显式）；响应 `userId`/`accountNo`/`balance`/`status` → `user_id`/`account_no`/`balance`/`status`（依赖隐式驼峰映射，无 `resultMap`） | `AccountMapper.xml#selectByUserId`（`AccountMapper.xml:5-7`）、`AccountEntity` | DDL 已确认（`db/init.sql:14-22`） | 待确认：请求条件跳已确认，响应字段跳缺少显式映射或 `map-underscore-to-camel-case` 配置证据（Q-M3） | [`TABLE-t_user_account`](../data-models/DB-demo_account/TABLE-t_user_account.md) |

> 特别提示：`SELECT *` 使结果集包含 `id`，而 `AccountEntity` 无 `id` 属性；未发现 `autoMappingUnknownColumnBehavior` 配置，未匹配列的处理方式待确认（Q-M3）。
> `balance` 的“不可为负”为表级业务硬约束（`db/init.sql:19,22`），本能力未读取或校验约束元数据。

### 7.2 配置依赖

| 配置组稳定 ID | 服务配置实体 | 配置键 | 直接影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| CONFIGGROUP-account-datasource | `CONFIG-SERVICE-account-service` | `spring.datasource.url`、`spring.datasource.username`、`spring.datasource.password`（值均 `<redacted>`） | 数据源/中间件：决定 `t_user_account` 是否可读 | 开发（default Profile） | Spring Boot DataSource 自动配置 + MyBatis Starter；未发现项目内显式绑定 | 已确认（开发快照）；连接串含内部端点，生产未确认（Q-M6） | [`SERVICE-account-service`](../configurations/SERVICE-account-service.md) |
| CONFIGGROUP-account-server | `CONFIG-SERVICE-account-service` | `server.port` | 路由/监听：决定该路径的暴露端口 | 开发（default Profile） | Spring Boot 内置属性绑定 | 已确认 | [`SERVICE-account-service`](../configurations/SERVICE-account-service.md) |

> `CONFIGGROUP-account-reconcile`（`reconcile.enabled`、`reconcile.retry-times`）只影响定时任务，对本接口无直接行为影响，不纳入本节。

## 八、中间件使用明细

### 8.1 缓存与队列

| 类型 | 名称或 Key 模式 | 读写方向 | 触发时机 | 证据 |
|------|-----------------|----------|----------|------|
| 未发现 | - | - | - | `account-service/pom.xml:13-17` 无缓存/队列依赖 |

### 8.2 消息

| Topic/Queue/Group | 方向 | 消息模型 | 重试与幂等 | 证据 |
|-------------------|------|----------|------------|------|
| 未发现 | - | - | - | `account-service/pom.xml` 无 AMQP/Kafka 依赖 |

### 8.3 搜索与本地缓存

未发现。

### 8.4 RPC 与下游 HTTP

| 服务 | 协议 | 版本或分组 | 触发条件 | 证据 |
|------|------|------------|----------|------|
| 未发现 | - | - | - | 未发现 Feign/RestTemplate/WebClient/RPC 依赖或调用代码；本工程不调用 `SERVICE-user-service` |

### 8.5 文件与对象存储

| 协议或存储 | 逻辑位置 | 文件格式 | 触发方 | 接收方 | 证据 |
|------------|----------|----------|--------|--------|------|
| 未发现 | - | - | - | - | `account-service/src/main/java/com/demo/account/**` 无文件读写 |

### 8.6 定时任务与批处理

| 任务 | 触发方式 | 并发与锁 | 重试与补偿 | 证据 |
|------|----------|----------|------------|------|
| `JOB-reconcile` 每日对账（独立能力，不属于本接口链路） | `@Scheduled(cron = "0 0 2 * * ?")` | 未发现 | 未发现 | `interfaces/JOB-reconcile_每日账户对账任务.md` |

## 九、数据源与副作用分析

- 主数据来源：`DB-demo_account`.`t_user_account`（MyBatis 等值查询），中间件 `MIDDLEWARE-mysql`。
- 实时查询或补充路径：无（无下游服务、无缓存、无跨服务调用）。
- 写入、副作用或异步结果：未发现（只读链路）。
- 事务、一致性和失败处理：未发现 `@Transactional`、异常转换或降级；查无结果时返回 `null`（HTTP 200 空体），未发现 404 语义。
- 数据暴露面提示：响应含账户余额与账户状态，接口无鉴权实现（对内调用方为运营门户），敏感级别需在安全评审中确认。

## 十、关键证据引用

| 引用 | 文件或资料位置 |
|------|----------------|
| 用户对外能力清单（未登记本能力） | `cadence/knowledge-base/user-input/api-scope.md:10-13` |
| 组合诉求来源能力声明 | `cadence/knowledge-base/user-input/api-scope.md:21` |
| 入口定义 | `account-service/src/main/java/com/demo/account/controller/AccountController.java:8-22` |
| 入口实现 | `account-service/src/main/java/com/demo/account/service/AccountService.java:18-20` |
| 数据访问 | `TABLE-t_user_account`、`data-models/DB-demo_account/TABLE-t_user_account.md`、`db/init.sql:14-22`、`account-service/src/main/resources/mapper/AccountMapper.xml:5-7` |
| 配置依赖 | `CONFIG-SERVICE-account-service`、`spring.datasource.*`、`server.port`、`configurations/SERVICE-account-service.md` |
| 中间件与外部调用 | `account-service/pom.xml:13-17`（MySQL 驱动）、未发现其他中间件客户端 |

## 十一、请求、响应或载荷示例

请求与响应示例见同目录 `API-account-query_账户信息查询_queryAccount_参数与报文.md` 第三、四节。
