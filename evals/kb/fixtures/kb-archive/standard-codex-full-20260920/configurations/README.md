# 配置知识索引

## 当前配置基线

| 配置状态 | 快照标识 | 环境 | 发布批次 | 来源类型 | 最终快照指纹 | 范围摘要 | 纳入文件数量或清单摘要 | 服务与规则摘要 | 分析前后校验 |
|----------|----------|------|----------|----------|--------------|----------|--------------------------|----------------|--------------|
| 全量 | baseline-config-v1 | 开发（fixture 本地快照） | fixture-batch-001 | 工作区配置导出快照（锁定） | 92bb968da5721d10403cbe72a128a492ea6c5fa2220788b736f9adab743aa71b | 三服务 application.yml 全量纳入（3 文件） | 3 个：account-service-application.yml、order-service-application.yml、user-service-application.yml | 服务：user-service、account-service、order-service；规则：仅 `src/main/resources/application.yml` | 首次计算指纹 == 分析结束指纹 == Manifest 授权指纹（一致） |

原始配置快照位于 KnowledgeBase 外部（`/home/tester/work/snapshots/baseline-config`），全程只读且不复制。本索引不保存单文件内容哈希、重复文件哈希或敏感值哈希。

## 配置来源与加载顺序

| 来源稳定 ID | 来源类型 | 环境/Profile | 加载顺序 | 覆盖关系 | 适用服务 | 证据状态 | 证据 |
|--------------|----------|--------------|----------|----------|----------|----------|------|
| CONFIGSRC-user-application-yml | 快照 `application.yml`（工程内同名文件内容一致） | 开发 / 默认 Profile | 1（Spring Boot 默认 `classpath:/application.yml`） | 无覆盖来源 | SERVICE-user-service | 已确认 | 快照 `user-service-application.yml`；`user-service/src/main/resources/application.yml` |
| CONFIGSRC-account-application-yml | 快照 `application.yml`（工程内同名文件内容一致） | 开发 / 默认 Profile | 1 | 无覆盖来源 | SERVICE-account-service | 已确认 | 快照 `account-service-application.yml`；`account-service/src/main/resources/application.yml` |
| CONFIGSRC-order-application-yml | 快照 `application.yml`（工程内同名文件内容一致） | 开发 / 默认 Profile | 1 | 无覆盖来源 | SERVICE-order-service | 已确认 | 快照 `order-service-application.yml`；`order-service/src/main/resources/application.yml` |

未发现配置中心、外部化配置、`application-<profile>.yml`、命令行覆盖或环境变量覆盖证据。工程内三份 `application.yml` 与快照内容一致（本次运行内临时逐字节比对，未写入任何哈希）。

部署、发布和启动脚本只作为加载链路证据，禁止执行；本次分析未发现此类脚本。

## 环境与 Profile

| 环境 | Profile | 适用服务 | 基线来源 | 覆盖来源 | 状态 | 证据 |
|------|---------|----------|----------|----------|------|------|
| 开发（fixture 本地快照） | 未声明（Spring Boot 默认 default） | user-service、account-service、order-service | baseline-config-v1 | 无 | 已确认 | `manifest.yaml` `evidence.configuration_snapshots.baseline`；各服务 `application.yml` |
| 测试 / 预发 / 生产 | 未提供 | - | 未提供 | 未提供 | 待确认 | 未发现任何非开发环境配置或环境变量清单 |

## 服务配置导航

| 服务稳定 ID | 环境 | 配置来源 | 主要配置组 | 敏感级别摘要 | 文档链接 |
|--------------|------|----------|------------|----------------|----------|
| SERVICE-user-service | 开发 | CONFIGSRC-user-application-yml（5 键） | CONFIGGROUP-user-server、CONFIGGROUP-user-datasource | 高 2、中 1、低 2 | `configurations/SERVICE-user-service.md` |
| SERVICE-account-service | 开发 | CONFIGSRC-account-application-yml（7 键） | CONFIGGROUP-account-server、CONFIGGROUP-account-datasource、CONFIGGROUP-account-reconcile | 高 2、中 1、低 4 | `configurations/SERVICE-account-service.md` |
| SERVICE-order-service | 开发 | CONFIGSRC-order-application-yml（5 键） | CONFIGGROUP-order-server、CONFIGGROUP-order-datasource、CONFIGGROUP-order-rabbitmq | 高 2、中 1、低 2 | `configurations/SERVICE-order-service.md` |

> 敏感级别按“高→中→低”分组计数，“中”包含账号类键；逐键结果见各服务文档第 4、8 节。计数仅覆盖该服务授权文件内的键。

## 配置组与影响能力

| 配置组稳定 ID | 配置组 | 用途 | 影响服务 | 代码绑定 | 数据模型或中间件关系 | 状态 | 证据 |
|----------------|--------|------|----------|----------|----------------------|------|------|
| CONFIGGROUP-user-server | 用户服务端口与应用名 | HTTP 监听端口、应用标识 | SERVICE-user-service | 未发现显式绑定（Spring Boot 内置） | 未发现 | 存在 | `user-service/src/main/resources/application.yml:1-5` |
| CONFIGGROUP-user-datasource | 用户库数据源 | 连接 demo_user 库 | SERVICE-user-service | DataSource/MyBatis 自动配置 | DB-demo_user、MIDDLEWARE-mysql | 存在 | `user-service/src/main/resources/application.yml:6-9` |
| CONFIGGROUP-account-server | 账户服务端口与应用名 | HTTP 监听端口、应用标识 | SERVICE-account-service | 未发现显式绑定 | 未发现 | 存在 | `account-service/src/main/resources/application.yml:1-5` |
| CONFIGGROUP-account-datasource | 账户库数据源 | 连接 demo_account 库 | SERVICE-account-service | DataSource/MyBatis 自动配置 | DB-demo_account、MIDDLEWARE-mysql | 存在 | `account-service/src/main/resources/application.yml:6-9` |
| CONFIGGROUP-account-reconcile | 对账任务开关与重试 | 控制对账启用与重试次数 | SERVICE-account-service | 仅 `ReconcileJob` 类注释声明，未发现读取代码 | 未发现 | 待确认 | `account-service/src/main/resources/application.yml:10-12`；`ReconcileJob.java:8-9` |
| CONFIGGROUP-order-server | 订单服务端口与应用名 | HTTP 监听端口、应用标识 | SERVICE-order-service | 未发现显式绑定 | 未发现 | 存在 | `order-service/src/main/resources/application.yml:1-5` |
| CONFIGGROUP-order-datasource | 订单库数据源 | 连接 demo_order 库 | SERVICE-order-service | DataSource/MyBatis 自动配置 | DB-demo_order、MIDDLEWARE-mysql | 存在 | `order-service/src/main/resources/application.yml` 数据源键 |
| CONFIGGROUP-order-rabbitmq | RabbitMQ 连接 | 事件收发连接参数 | SERVICE-order-service | `RabbitTemplate` 注入与 `@RabbitListener` 装配 | MIDDLEWARE-rabbitmq | 存在 | `order-service/src/main/resources/application.yml:6-9`；`mq/OrderEventProducer.java:13-21`、`mq/OrderEventListener.java:13-19` |

## 敏感信息策略

- 密码、Token、AccessKey、Secret、密钥、私钥、完整连接串、内部域名、IP 和 URL 的实际值统一写为 `<redacted>`。
- 只记录敏感配置键、用途、值类型、敏感级别和证据位置，不保存敏感值哈希或其他可关联的确定性衍生物。
- 无法判断是否敏感时按敏感信息处理，并登记为 `待确认`；本次按此原则将数据源账号、MQ 账号一并脱敏。
- 逐键脱敏结果见各服务配置文档第 4 节与第 8 节；不存在以敏感为由省略的键。

## 快照差异摘要

| 对象稳定 ID | 对比基线 | 当前基线 | 变更类型 | 影响服务 | 影响能力 | 详情链接 |
|--------------|----------|----------|----------|----------|----------|----------|
| - | 无历史基线 | baseline-config-v1 | 不适用 | - | - | `open-questions.md`（无历史快照可比对，不得凭文件时间推断变更） |

## 来源冲突与待确认项

| 对象稳定 ID | 问题 | 来源一 | 来源二 | 影响 | 状态 | 详情链接 |
|--------------|------|--------|--------|------|------|----------|
| CONFIGGROUP-account-reconcile | 配置键无代码绑定，仅有类注释声明 | `account-service/src/main/resources/application.yml:10-12` | `job/ReconcileJob.java:8-9` | 配置是否生效无法确认 | 待确认 | `configurations/SERVICE-account-service.md` |
| CONFIGGROUP-order-rabbitmq | 未发现 exchange/queue 配置键（名称硬编码于代码常量） | `order-service/src/main/resources/application.yml:6-9` | `mq/OrderEventProducer.java:10-11`、`mq/OrderEventListener.java:14-16` | 队列绑定需在运行环境另行确认 | 已记录 | `configurations/SERVICE-order-service.md` |
| 三服务数据源 | 快照为开发 fixture，生产数据源未确认 | `manifest.yaml`（环境：开发） | 未提供生产配置 | 不能把开发连接信息升级为生产事实 | 待确认 | 各服务配置文档第 9 节 |
