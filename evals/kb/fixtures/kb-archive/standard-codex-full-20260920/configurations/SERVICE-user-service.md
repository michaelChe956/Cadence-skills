# user-service配置

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 服务稳定 ID | SERVICE-user-service |
| 配置状态 | 全量 |
| 当前环境 | 开发（fixture 本地快照） |
| 当前 Profile | 未声明（Spring Boot 默认 default） |
| 快照标识 | baseline-config-v1 |
| 发布批次 | fixture-batch-001 |
| 最终快照指纹 | 92bb968da5721d10403cbe72a128a492ea6c5fa2220788b736f9adab743aa71b |
| 范围摘要 | 三服务 application.yml 全量纳入（3 文件） |
| 纳入文件数量或清单摘要 | 3 个：account-service-application.yml、order-service-application.yml、user-service-application.yml（本服务对应 user-service-application.yml） |
| 服务与文件规则摘要 | 服务：user-service；规则：仅 `src/main/resources/application.yml` |
| 来源文件键数 | 5 |
| 文档收录键数 | 5 |
| 未覆盖范围 | web-portal 构建配置（未授权）；测试/预发/生产环境配置 |

## 2. 配置来源与加载顺序

| 顺序 | 配置来源 | 来源类型 | 环境/Profile | 覆盖对象 | 证据状态 | 证据 |
|------|----------|----------|--------------|----------|----------|------|
| 1 | `classpath:/application.yml`（快照 `user-service-application.yml`，与工程内文件一致） | Spring Boot 默认配置文件 | 开发 / default | 本服务全部配置键 | 已确认 | 快照 `user-service-application.yml`；`user-service/src/main/resources/application.yml:1-9` |

未发现 profile 专用文件、配置中心、环境变量或命令行覆盖来源。

部署、发布和启动脚本只作为配置加载链路证据，禁止执行。相同内容文件合并分析时，保留全部适用服务与来源位置，不记录运行时重复文件哈希。

## 3. Profile 与环境

| 环境 | Profile | 激活或适用条件 | 基线来源 | 覆盖来源 | 差异摘要 | 状态 | 证据 |
|------|---------|----------------|----------|----------|----------|------|------|
| 开发（fixture 本地快照） | default（未声明） | 无 `spring.config.activate.on-profile`，始终加载 | baseline-config-v1 | 无 | 无 | 已确认 | `user-service/src/main/resources/application.yml` |
| 测试/预发/生产 | 未提供 | - | 未提供 | 未提供 | 未知 | 待确认 | 未提供任何环境配置资料 |

## 4. 配置键清单

| 配置键 | 用途 | 值类型 | 环境 | 来源文件 | 绑定位置 | 敏感级别 | 状态 | 证据 |
|--------|------|--------|------|----------|----------|----------|------|------|
| `server.port` | HTTP 监听端口（值 8081） | integer | 开发 | user-service-application.yml | 未发现显式绑定（Spring Boot 内置） | 低 | 存在 | `user-service/src/main/resources/application.yml:1-2` |
| `spring.application.name` | 应用名（值 user-service） | string | 开发 | user-service-application.yml | 未发现显式绑定（Spring Boot 内置） | 低 | 存在 | `user-service/src/main/resources/application.yml:3-5` |
| `spring.datasource.url` | 用户库 JDBC 连接串（完整连接串） | string | 开发 | user-service-application.yml | DataSource/MyBatis 自动配置 | 高 | 存在 | `user-service/src/main/resources/application.yml:6-7` |
| `spring.datasource.username` | 用户库连接账号 | string | 开发 | user-service-application.yml | DataSource/MyBatis 自动配置 | 中 | 存在 | `user-service/src/main/resources/application.yml:8` |
| `spring.datasource.password` | 用户库连接口令 | string | 开发 | user-service-application.yml | DataSource/MyBatis 自动配置 | 高 | 存在 | `user-service/src/main/resources/application.yml:9` |

状态只允许：`存在`、`新增`、`删除`、`修改`、`缺失`、`来源冲突`、`待确认`。

密码、Token、AccessKey、Secret、密钥、私钥、完整连接串、内部域名、IP 和 URL 等敏感值统一写为 `<redacted>`；不得保存敏感值哈希。

## 5. 代码绑定与生效条件

| 配置键或配置组 | 绑定方式 | 代码位置 | 生效条件 | 装配或调用证据 | 状态 |
|----------------|----------|----------|----------|----------------|------|
| `spring.datasource.*` | Spring Boot DataSource 自动配置 + MyBatis Starter 会话工厂 | 未发现项目内 `@ConfigurationProperties` 或 `@Value`；依赖声明见 `user-service/pom.xml:14-16` | 默认 profile 下加载 `application.yml` 且驱动可解析 | `UserMapper.xml:4-7` 实际查询 `t_user` | 存在 |
| `server.port` / `spring.application.name` | Spring Boot 内置属性绑定 | 未发现项目内绑定代码 | 同上 | 启动类 `UserApplication.java:8-11` | 存在 |

未发现显式绑定声明，绑定推断基于依赖与自动配置约定 [合理推断]；未发现任何键被代码以字符串方式读取。

## 6. 数据源与分片配置

| 配置组稳定 ID | 用途 | 数据源或 Schema | 逻辑表稳定 ID | 分片或路由摘要 | 代码绑定 | 状态 | 证据 |
|----------------|------|-----------------|----------------|----------------|----------|------|------|
| CONFIGGROUP-user-datasource | 用户库连接 | DB-demo_user | TABLE-t_user | 未发现分片或路由规则 | DataSource/MyBatis 自动配置 | 存在 | `user-service/src/main/resources/application.yml:6-9`；`mapper/UserMapper.xml:4-7` |

Mapper XML 归入字段级数据模型文档。本章节只建立配置与数据源、Schema、逻辑表及分片规则的关系，不复制 Mapper SQL 或字段清单。

## 7. 中间件与外部系统配置

| 配置组稳定 ID | 中间件或外部系统 | 用途 | 代码绑定或客户端 | 生效条件 | 敏感级别 | 状态 | 证据 |
|----------------|------------------|------|------------------|----------|------------|------|------|
| CONFIGGROUP-user-datasource | MIDDLEWARE-mysql | 用户库关系型存储 | `mysql-connector-java`（`pom.xml:16`）+ MyBatis | 快照为开发环境；生产环境未确认 | 高（含连接串与口令） | 存在 | `user-service/src/main/resources/application.yml:6-9` |

本服务未发现消息队列、缓存、注册中心或其他外部系统配置键。内部主机、完整连接串与认证信息均已脱敏；只有配置键不能证明中间件在生产环境已启用。

## 8. 敏感配置

| 配置键 | 用途 | 值类型 | 环境 | 敏感级别 | 脱敏结果 | 证据 |
|--------|------|--------|------|------------|----------|------|
| `spring.datasource.url` | 用户库 JDBC 连接串 | string（完整连接串） | 开发 | 高 | `<redacted>` | `user-service/src/main/resources/application.yml:7` |
| `spring.datasource.username` | 用户库连接账号 | string | 开发 | 中 | `<redacted>` | `user-service/src/main/resources/application.yml:8` |
| `spring.datasource.password` | 用户库连接口令 | string | 开发 | 高 | `<redacted>` | `user-service/src/main/resources/application.yml:9` |

脱敏结果固定写 `<redacted>`，不记录原值、敏感值哈希或其他可关联的确定性衍生物。本服务第 4 节共 5 键，其中敏感键 3 个，均已逐键列出。

## 9. 来源冲突与待确认项

| 配置键或对象稳定 ID | 问题 | 来源一 | 来源二 | 影响 | 状态 | 处理建议 |
|----------------------|------|--------|--------|------|------|----------|
| CONFIGGROUP-user-datasource | 快照为开发 fixture，连接串指向本地端点（已脱敏），生产数据源未知 | 快照 `user-service-application.yml` | 未提供生产配置 | 不能作为生产事实 | 待确认 | 补充生产环境配置快照后再核验（Q-M6） |
| 全部配置键 | 未发现显式代码绑定，且未发现 `.env`/启动参数覆盖 | `application.yml` | 未发现启动脚本 | 生效路径推断成分较高 | 已记录 | 如需强证据，补充启动命令或部署描述 |

## 10. 变更记录

| 对比基线 | 当前基线 | 配置键或配置组 | 变更类型 | 影响 | 证据 |
|----------|----------|----------------|----------|------|------|
| 无历史基线 | baseline-config-v1 | 全部 5 键 | 不适用 | 首次建立配置基线 | `open-questions.md`（无历史快照可比对） |

没有历史基线时记录“无历史基线”，不得把文件时间或首次发现误写为 `新增`。
