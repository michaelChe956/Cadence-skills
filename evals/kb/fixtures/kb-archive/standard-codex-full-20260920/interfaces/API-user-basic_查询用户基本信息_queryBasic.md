# API-user-basic 查询用户基本信息

> **能力 ID**：`API-user-basic`
> **分类**：对外
> **能力类型**：REST
> **数据来源**：用户对外能力清单（`user-input/api-scope.md`）、`user-service` 工程代码、`db/init.sql`、配置快照 `baseline-config-v1`
> **梳理日期**：2026-09-20
> **参数与报文**：见同目录 `API-user-basic_查询用户基本信息_queryBasic_参数与报文.md`

## 一、能力基础信息

| 项目 | 值 |
|------|----|
| 能力名称 | 查询用户基本信息 |
| API 名称或逻辑标识 | `queryBasic` |
| 分类 | 对外（来源：用户对外能力清单） |
| 能力类型 | REST |
| 协议与方法 | HTTP GET |
| 路径或逻辑地址 | `/api/user/basic/{userId}` |
| 数据格式 | JSON（`UserEntity` 直接序列化，未发现显式 `produces` 配置） |
| 是否需授权 | 未发现鉴权实现（无 Spring Security 依赖、无过滤器、无网关工程）；对外鉴权要求待确认（Q-M8） |
| 版本 | v1（用户清单） |
| 调用方或生产者 | 客户端（用户清单）；`web-portal` 用户列表页（代码证据：`web-portal/src/api/index.js:2`、`web-portal/src/views/UserList.vue:12`） |
| 落地方或消费者 | `SERVICE-user-service`（`MODULE-user-basic`） |
| 生命周期状态 | 已声明、已实现、已装配、已暴露 |
| 数据来源表 | `TABLE-t_user`（只读） |

### 调用入口

| 环境 | 地址 | 证据状态 |
|------|------|----------|
| 开发（fixture 快照） | `http://localhost:8081/api/user/basic/{userId}`（端口取 `server.port` 键，非敏感） | `user-service/src/main/resources/application.yml:1-2` |
| 生产 | 未提供（未发现网关或域名配置） | 待确认 |
| 前端访问路径 | `/api/user/basic/{userId}`（合并 axios `baseURL: /api` 后） | `web-portal/src/api/request.js:3`、`web-portal/src/api/index.js:2`，代理目标见 Q-L4 |

## 二、业务需求描述

- 按用户唯一标识查询用户基本信息：用户 ID、姓名、手机号与邮箱（`user-input/api-scope.md`、`UserBasicController.java:18`）。
- 服务边界：只返回用户主数据，不返回账户余额/状态（属 `SERVICE-account-service`）与订单（属 `SERVICE-order-service`）。
- 主链路只读，未发现鉴权、限流、审计或压缩逻辑。
- 业务目标与使用场景细节：未提供（`user-input/product.md` 仅声明“用户信息查询”为关键特性）。

## 三、输入参数

详见 `API-user-basic_查询用户基本信息_queryBasic_参数与报文.md` 第一节（路径参数 `userId`）。

## 四、输出参数

详见 `API-user-basic_查询用户基本信息_queryBasic_参数与报文.md` 第二节（`userId`、`userName`、`mobile`、`email`）。

## 五、代码实现定位

### 5.1 用户清单与代码映射

| 来源 | 标识 | 结论 | 证据 |
|------|------|------|------|
| 用户对外能力清单 | `API-user-basic`（查询用户基本信息，REST API，v1，使用中，调用方：客户端） | 对外分类，已实现 | `user-input/api-scope.md:12` |
| 当前代码 | `UserBasicController#queryBasic` | 实现已定位，无实现冲突 | `user-service/src/main/java/com/demo/user/controller/UserBasicController.java:19-21` |

### 5.2 实现清单

| 层级 | 符号 | 文件路径 | 状态 | 说明 |
|------|------|----------|------|------|
| 入口 | `com.demo.user.controller.UserBasicController#queryBasic` | `user-service/src/main/java/com/demo/user/controller/UserBasicController.java:19-21` | 已确认 | `@RestController` + `@RequestMapping("/api/user")` + `@GetMapping("/basic/{userId}")` |
| 业务 | `com.demo.user.service.UserBasicService#queryBasic` | `user-service/src/main/java/com/demo/user/service/UserBasicService.java:18-20` | 已确认 | 直接委派 Mapper，无分支与转换 |
| 数据访问 | `com.demo.user.mapper.UserMapper#selectById` | `user-service/src/main/java/com/demo/user/mapper/UserMapper.java:10` | 已确认 | `@Mapper`，参数 `@Param("userId")` |
| SQL | `UserMapper.xml#selectById` | `user-service/src/main/resources/mapper/UserMapper.xml:4-7` | 已确认 | `SELECT user_id AS userId, user_name AS userName, mobile, email FROM t_user WHERE user_id = #{userId}` |
| 模型 | `com.demo.user.entity.UserEntity` | `user-service/src/main/java/com/demo/user/entity/UserEntity.java:4-9` | 已确认 | 4 字段，无 getter/setter 源文件（fixture 静态样本） |

## 六、调用链路

### 6.1 调用树

```text
API-user-basic（GET /api/user/basic/{userId}）
└─ SERVICE-user-service / MODULE-user-basic
   ├─ UserBasicController.queryBasic（UserBasicController.java:19-21）
   │  └─ UserBasicService.queryBasic（UserBasicService.java:18-20）
   │     └─ UserMapper.selectById（UserMapper.java:10）
   │        └─ UserMapper.xml#selectById（UserMapper.xml:4-7）
   ├─ TABLE-t_user
   │  └─ user_id/user_name/mobile/email → SELECT 列与 AS 别名（UserMapper.xml:5）
   └─ CONFIGURATION CONFIGGROUP-user-datasource
      └─ spring.datasource.url/username/password → DataSource/MyBatis 自动配置（无项目内显式绑定）
```

### 6.2 分支与触发条件

| 条件 | 路径 | 结果 | 证据 |
|------|------|------|------|
| 未发现分支条件（无 `if`/开关/灰度判断） | Controller → Service → Mapper | 恒定单路径查询 | `UserBasicController.java:19-21`、`UserBasicService.java:18-20` |
| `userId` 非数字 | Spring MVC 路径变量类型转换 | 400（框架默认行为，未发现自定义异常处理） | 待确认（无 `@ControllerAdvice`） |

### 6.3 逐层调用明细

| 层级 | 符号 | 职责 | 下游 | 证据 |
|------|------|------|------|------|
| REST 入口 | `UserBasicController#queryBasic(Long)` | 绑定路径变量并返回实体 | `UserBasicService` | `UserBasicController.java:19-21` |
| 业务 | `UserBasicService#queryBasic(Long)` | 直接委派查询 | `UserMapper` | `UserBasicService.java:18-20` |
| 数据访问 | `UserMapper#selectById` | 参数绑定 | `UserMapper.xml#selectById` | `UserMapper.java:10` |
| SQL | `UserMapper.xml#selectById` | 按主键等值查询 `t_user` | `TABLE-t_user` | `UserMapper.xml:4-7` |
| 装配 | `@SpringBootApplication` 组件扫描 `com.demo.user` | Controller/Service/Mapper 装配 | `SERVICE-user-service` | `UserApplication.java:7-11`、`UserMapper.java:8` |

## 七、数据模型与配置依赖

### 7.1 数据模型影响

| TABLE 稳定 ID | Schema/逻辑表 | 读写 | 涉及字段 | API 模型映射 | Mapper/DAO/SQL | 表字段证据状态 | 端到端映射状态 | 表文档链接 |
|---------------|---------------|------|----------|--------------|----------------|------------------|------------------|------------|
| TABLE-t_user | `DB-demo_user` / `t_user` | R | 条件：`user_id`；读取：`user_id`、`user_name`、`mobile`、`email`（`created_at` 未读取） | `userId`→`user_id`（显式 `AS userId`）；`userName`→`user_name`（显式 `AS userName`）；`mobile`→`mobile`、`email`→`email`（同名默认映射） | `UserMapper.xml#selectById`（`UserMapper.xml:4-7`）、`UserEntity` | DDL 已确认（`db/init.sql:4-10`） | 已确认（请求条件、SQL 列、Entity 字段逐跳一致） | [`TABLE-t_user`](../data-models/DB-demo_user/TABLE-t_user.md) |

> 只摘录本能力直接读写的字段。`表字段证据状态` 仅描述字段定义证据；`端到端映射状态` 判断 `API 模型 → SERVICE/MODULE → Mapper/SQL → TABLE 字段` 是否完整。本能力未发现写操作。

### 7.2 配置依赖

| 配置组稳定 ID | 服务配置实体 | 配置键 | 直接影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| CONFIGGROUP-user-datasource | `CONFIG-SERVICE-user-service` | `spring.datasource.url`、`spring.datasource.username`、`spring.datasource.password`（值均 `<redacted>`） | 数据源/中间件：决定 `t_user` 是否可读 | 开发（default Profile） | Spring Boot DataSource 自动配置 + MyBatis Starter；默认 profile 加载 `application.yml` 且驱动可解析；未发现项目内显式绑定 | 已确认（开发快照）；生产环境未确认（Q-M6） | [`SERVICE-user-service`](../configurations/SERVICE-user-service.md) |
| CONFIGGROUP-user-server | `CONFIG-SERVICE-user-service` | `server.port` | 路由/监听：决定该路径的暴露端口 | 开发（default Profile） | Spring Boot 内置属性绑定 | 已确认 | [`SERVICE-user-service`](../configurations/SERVICE-user-service.md) |

> `spring.application.name` 仅标识应用，不影响本能力请求、响应、路由或副作用，不纳入本节。

## 八、中间件使用明细

### 8.1 缓存与队列

| 类型 | 名称或 Key 模式 | 读写方向 | 触发时机 | 证据 |
|------|-----------------|----------|----------|------|
| 未发现 | - | - | - | 未发现 Redis 依赖或缓存代码（`user-service/pom.xml:13-17`） |

### 8.2 消息

| Topic/Queue/Group | 方向 | 消息模型 | 重试与幂等 | 证据 |
|-------------------|------|----------|------------|------|
| 未发现 | - | - | - | `user-service/pom.xml` 无 AMQP/Kafka 依赖 |

### 8.3 搜索与本地缓存

未发现。

### 8.4 RPC 与下游 HTTP

| 服务 | 协议 | 版本或分组 | 触发条件 | 证据 |
|------|------|------------|----------|------|
| 未发现 | - | - | - | 未发现 Feign/RestTemplate/WebClient/RPC 依赖或调用代码 |

### 8.5 文件与对象存储

| 协议或存储 | 逻辑位置 | 文件格式 | 触发方 | 接收方 | 证据 |
|------------|----------|----------|--------|--------|------|
| 未发现 | - | - | - | - | `user-service/src/main/java/com/demo/user/**` 无文件读写 |

### 8.6 定时任务与批处理

| 任务 | 触发方式 | 并发与锁 | 重试与补偿 | 证据 |
|------|----------|----------|------------|------|
| 未发现 | - | - | - | 未发现调度注解或调度框架 |

## 九、数据源与副作用分析

- 主数据来源：`DB-demo_user`.`t_user`（MyBatis 等值查询），中间件 `MIDDLEWARE-mysql`。
- 实时查询或补充路径：无（单次同步查询，无下游调用、无缓存）。
- 写入、副作用或异步结果：未发现（只读链路，无事务、无消息、无文件）。
- 事务、一致性和失败处理：未发现 `@Transactional` 与异常转换；查无结果时 `selectById` 返回 `null`，Controller 直接返回实体（HTTP 200、空响应体），未发现 404 语义实现（待确认）。

## 十、关键证据引用

| 引用 | 文件或资料位置 |
|------|----------------|
| 用户对外能力清单 | `cadence/knowledge-base/user-input/api-scope.md:12` |
| 入口定义 | `user-service/src/main/java/com/demo/user/controller/UserBasicController.java:9,19-21` |
| 入口实现 | `user-service/src/main/java/com/demo/user/service/UserBasicService.java:18-20` |
| 数据访问 | `TABLE-t_user`、`data-models/DB-demo_user/TABLE-t_user.md`、`db/init.sql:4-10`、`user-service/src/main/resources/mapper/UserMapper.xml:4-7` |
| 配置依赖 | `CONFIG-SERVICE-user-service`、`spring.datasource.*`、`server.port`、`configurations/SERVICE-user-service.md` |
| 中间件与外部调用 | `user-service/pom.xml:13-17`（MySQL 驱动）、未发现其他中间件客户端 |

## 十一、请求、响应或载荷示例

请求与响应示例见同目录 `API-user-basic_查询用户基本信息_queryBasic_参数与报文.md` 第三、四节。
