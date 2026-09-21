# order-service配置

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 服务稳定 ID | SERVICE-order-service |
| 配置状态 | 全量 |
| 当前环境 | 开发（fixture 本地快照） |
| 当前 Profile | 未声明（Spring Boot 默认 default） |
| 快照标识 | baseline-config-v1 |
| 发布批次 | fixture-batch-001 |
| 最终快照指纹 | 92bb968da5721d10403cbe72a128a492ea6c5fa2220788b736f9adab743aa71b |
| 范围摘要 | 三服务 application.yml 全量纳入（3 文件） |
| 纳入文件数量或清单摘要 | 3 个：account-service-application.yml、order-service-application.yml、user-service-application.yml（本服务对应 order-service-application.yml） |
| 服务与文件规则摘要 | 服务：order-service；规则：仅 `src/main/resources/application.yml` |
| 来源文件键数 | 5 |
| 文档收录键数 | 5 |
| 未覆盖范围 | web-portal 构建配置（未授权）；测试/预发/生产环境配置；RabbitMQ exchange/queue 名称（在代码常量中，非配置键） |

## 2. 配置来源与加载顺序

| 顺序 | 配置来源 | 来源类型 | 环境/Profile | 覆盖对象 | 证据状态 | 证据 |
|------|----------|----------|--------------|----------|----------|------|
| 1 | `classpath:/application.yml`（快照 `order-service-application.yml`，与工程内文件一致） | Spring Boot 默认配置文件 | 开发 / default | 本服务全部配置键 | 已确认 | 快照 `order-service-application.yml`；`order-service/src/main/resources/application.yml:1-9` |

未发现 profile 专用文件、配置中心、环境变量或命令行覆盖来源。

部署、发布和启动脚本只作为配置加载链路证据，禁止执行。相同内容文件合并分析时，保留全部适用服务与来源位置，不记录运行时重复文件哈希。

## 3. Profile 与环境

| 环境 | Profile | 激活或适用条件 | 基线来源 | 覆盖来源 | 差异摘要 | 状态 | 证据 |
|------|---------|----------------|----------|----------|----------|------|------|
| 开发（fixture 本地快照） | default（未声明） | 无 `spring.config.activate.on-profile`，始终加载 | baseline-config-v1 | 无 | 无 | 已确认 | `order-service/src/main/resources/application.yml` |
| 测试/预发/生产 | 未提供 | - | 未提供 | 未提供 | 未知（MQ 主机与数据源可能不同） | 待确认 | 未提供任何环境配置资料 |

## 4. 配置键清单

| 配置键 | 用途 | 值类型 | 环境 | 来源文件 | 绑定位置 | 敏感级别 | 状态 | 证据 |
|--------|------|--------|------|----------|----------|----------|------|------|
| `server.port` | HTTP 监听端口（值 8083） | integer | 开发 | order-service-application.yml | 未发现显式绑定（Spring Boot 内置） | 低 | 存在 | `order-service/src/main/resources/application.yml:1-2` |
| `spring.application.name` | 应用名（值 order-service） | string | 开发 | order-service-application.yml | 未发现显式绑定（Spring Boot 内置） | 低 | 存在 | `order-service/src/main/resources/application.yml:3-5` |
| `spring.rabbitmq.host` | RabbitMQ 主机（内部域名） | string | 开发 | order-service-application.yml | RabbitAutoConfiguration | 高 | 存在 | `order-service/src/main/resources/application.yml:6-7` |
| `spring.rabbitmq.username` | RabbitMQ 连接账号 | string | 开发 | order-service-application.yml | RabbitAutoConfiguration | 中 | 存在 | `order-service/src/main/resources/application.yml:8` |
| `spring.rabbitmq.password` | RabbitMQ 连接口令 | string | 开发 | order-service-application.yml | RabbitAutoConfiguration | 高 | 存在 | `order-service/src/main/resources/application.yml:9` |

状态只允许：`存在`、`新增`、`删除`、`修改`、`缺失`、`来源冲突`、`待确认`。

密码、Token、AccessKey、Secret、密钥、私钥、完整连接串、内部域名、IP 和 URL 等敏感值统一写为 `<redacted>`；不得保存敏感值哈希。

## 5. 代码绑定与生效条件

| 配置键或配置组 | 绑定方式 | 代码位置 | 生效条件 | 装配或调用证据 | 状态 |
|----------------|----------|----------|----------|----------------|------|
| `spring.rabbitmq.*` | RabbitAutoConfiguration 属性绑定 → `RabbitTemplate` / `ConnectionFactory` | 未发现项目内绑定声明；`mq/OrderEventProducer.java:13-17` 注入 `RabbitTemplate` | 默认 profile 加载配置、`spring-boot-starter-amqp` 在类路径、MQ 可达 | `mq/OrderEventProducer.java:19-21` 发送、`mq/OrderEventListener.java:13-19` 消费 | 存在 |
| `server.port` / `spring.application.name` | Spring Boot 内置属性绑定 | 未发现项目内绑定代码 | 默认 profile | 启动类 `OrderApplication.java:8-11` | 存在 |
| exchange / routing key / queue | 未使用配置键，硬编码为 Java 常量 | `mq/OrderEventProducer.java:10-11`、`mq/OrderEventListener.java:14-16` | 随代码发布生效 | 生产/消费注释与注解 | 存在（代码证据） |

注意：本服务未在 `application.yml` 中配置 `spring.datasource.*`，但 `pom.xml:16` 声明了 MySQL 驱动、`OrderMapper.xml` 直接查询 `t_order`；数据源配置来源在授权快照中缺失，属未覆盖范围（见第 9 节）。

## 6. 数据源与分片配置

| 配置组稳定 ID | 用途 | 数据源或 Schema | 逻辑表稳定 ID | 分片或路由摘要 | 代码绑定 | 状态 | 证据 |
|----------------|------|-----------------|----------------|----------------|----------|------|------|
| CONFIGGROUP-order-datasource | 订单库连接（配置键未在授权快照中出现） | DB-demo_order（推断） | TABLE-t_order、TABLE-t_export_file（推断） | 未发现分片或路由规则 | DataSource/MyBatis 自动配置 | 缺失 | `order-service/src/main/resources/application.yml`（无数据源键）；`mapper/OrderMapper.xml:4-9` |

Mapper XML 归入字段级数据模型文档。本章节只建立配置与数据源、Schema、逻辑表及分片规则的关系，不复制 Mapper SQL 或字段清单。

## 7. 中间件与外部系统配置

| 配置组稳定 ID | 中间件或外部系统 | 用途 | 代码绑定或客户端 | 生效条件 | 敏感级别 | 状态 | 证据 |
|----------------|------------------|------|------------------|----------|------------|------|------|
| CONFIGGROUP-order-rabbitmq | MIDDLEWARE-rabbitmq | 订单已支付事件收发 | `spring-boot-starter-amqp`（`pom.xml:17`）、`RabbitTemplate`、`@RabbitListener` | 默认 profile 加载配置且 MQ 可达 | 高（含内部域名、账号与口令） | 存在 | `order-service/src/main/resources/application.yml:6-9`；`mq/OrderEventProducer.java:19-21`、`mq/OrderEventListener.java:13-19` |
| CONFIGGROUP-order-datasource | MIDDLEWARE-mysql | 订单库关系型存储 | `mysql-connector-java`（`pom.xml:16`）+ MyBatis | 数据源配置来源缺失，未确认 | 高（预期含连接串，当前快照未提供） | 缺失 | `order-service/pom.xml:16`、`mapper/OrderMapper.xml:4-9` |

内部域名、连接串与认证信息均已脱敏；只有配置键不能证明中间件在生产环境已启用。RabbitMQ 的 exchange（`order.exchange`）、routing key（`order.paid`）与队列（`order.paid.queue`）来自代码常量，不是配置键，运行环境是否复用需另行确认。

## 8. 敏感配置

| 配置键 | 用途 | 值类型 | 环境 | 敏感级别 | 脱敏结果 | 证据 |
|--------|------|--------|------|------------|----------|------|
| `spring.rabbitmq.host` | RabbitMQ 主机（内部域名） | string | 开发 | 高 | `<redacted>` | `order-service/src/main/resources/application.yml:7` |
| `spring.rabbitmq.username` | RabbitMQ 连接账号 | string | 开发 | 中 | `<redacted>` | `order-service/src/main/resources/application.yml:8` |
| `spring.rabbitmq.password` | RabbitMQ 连接口令 | string | 开发 | 高 | `<redacted>` | `order-service/src/main/resources/application.yml:9` |

脱敏结果固定写 `<redacted>`，不记录原值、敏感值哈希或其他可关联的确定性衍生物。本服务第 4 节共 5 键，其中敏感键 3 个，均已逐键列出。

## 9. 来源冲突与待确认项

| 配置键或对象稳定 ID | 问题 | 来源一 | 来源二 | 影响 | 状态 | 处理建议 |
|----------------------|------|--------|--------|------|------|----------|
| CONFIGGROUP-order-datasource | `pom.xml` 声明 MySQL 驱动、Mapper 查询 `t_order`，但授权配置中无数据源键 | `order-service/pom.xml:16`、`mapper/OrderMapper.xml:4-9` | `order-service/src/main/resources/application.yml`（仅 5 键） | 数据源配置来源未覆盖，运行必需配置缺失 | 缺失 | 确认数据源配置是否由外部化配置/环境变量提供（Q-M6） |
| CONFIGGROUP-order-rabbitmq | exchange/queue/routing key 未作为配置键管理 | `mq/OrderEventProducer.java:10-11` | `application.yml:6-9`（仅连接参数） | 环境差异需改代码或另建配置 | 已记录 | 若需多环境差异化，建议外置为配置键 |
| CONFIGGROUP-order-rabbitmq | 快照为开发环境，MQ 主机为内部域名（已脱敏） | 快照 `order-service-application.yml` | 未提供生产配置 | 不能作为生产事实 | 待确认 | 补充生产环境快照（Q-M6） |

## 10. 变更记录

| 对比基线 | 当前基线 | 配置键或配置组 | 变更类型 | 影响 | 证据 |
|----------|----------|----------------|----------|------|------|
| 无历史基线 | baseline-config-v1 | 全部 5 键 | 不适用 | 首次建立配置基线 | `open-questions.md`（无历史快照可比对） |

没有历史基线时记录“无历史基线”，不得把文件时间或首次发现误写为 `新增`。
