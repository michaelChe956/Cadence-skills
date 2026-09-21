# JOB-reconcile 每日账户对账任务

> **能力 ID**：`JOB-reconcile`
> **分类**：对内
> **能力类型**：任务（定时任务）
> **数据来源**：工程扫描（`account-service` 代码、配置快照 `baseline-config-v1`）
> **梳理日期**：2026-09-20
> **参数与报文**：不适用（任务能力不生成配套参数与报文文件）

## 一、能力基础信息

| 项目 | 值 |
|------|----|
| 能力名称 | 每日账户对账任务 |
| API 名称或逻辑标识 | `reconcile`（类注释：每日账户对账定时任务） |
| 分类 | 对内（用户对外能力清单未登记） |
| 能力类型 | 任务（定时任务） |
| 协议与方法 | Spring `@Scheduled`，cron `0 0 2 * * ?`（每日 02:00） |
| 路径或逻辑地址 | 不适用（无网络入口） |
| 数据格式 | 不适用 |
| 是否需授权 | 不适用（进程内调度） |
| 版本 | 未提供 |
| 生产者或触发方 | Spring 调度器（触发依据待确认） |
| 消费者或落地方 | `SERVICE-account-service` / `MODULE-account-reconcile` |
| 生命周期状态 | 代码存在但不可达（实现为空体；未发现 `@EnableScheduling`；`reconcile.enabled` 无绑定代码） |

## 二、业务需求描述

- 每日对账户执行对账（类注释 `ReconcileJob.java:6-10`）。
- 对账口径、对账对象、差异处理与产出：未提供。
- 启用说明（仅注释声明）：`@Scheduled` 注解 + `application.yml` 的 `reconcile.enabled=true`；重试次数取 `reconcile.retry-times`（`ReconcileJob.java:7-9`）。该声明无代码实现证据（Q-M2）。

## 三、输入参数

不适用（无方法参数、无外部触发载荷）。

## 四、输出参数

不适用（方法返回 `void`，未发现返回值、状态上报或产出物）。

## 五、代码实现定位

### 5.1 用户清单与代码映射

| 来源 | 标识 | 结论 | 证据 |
|------|------|------|------|
| 用户对外能力清单 | 未登记（`api-scope.md` 无任务类能力） | 按规则归为对内能力 | `cadence/knowledge-base/user-input/api-scope.md:10-13` |
| 当前代码 | `ReconcileJob#reconcile` | 已定位；实现为空体，启用条件未闭合 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:11-17` |

### 5.2 实现清单

| 层级 | 符号 | 文件路径 | 状态 | 说明 |
|------|------|----------|------|------|
| 任务注册 | `com.demo.account.job.ReconcileJob` | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:11-12` | 已确认 | `@Component`，由组件扫描注册 Bean |
| 调度入口 | `ReconcileJob#reconcile` | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:14-17` | 代码存在但不可达 | `@Scheduled(cron = "0 0 2 * * ?")`，方法体为空 |
| 启用装配 | 未发现 `@EnableScheduling` | `account-service/src/main/java/com/demo/account/AccountApplication.java:7-11` | 未发现 | 缺少启用证据，`@Scheduled` 可能未注册（Q-M1） |
| 配置绑定 | 未发现 | `account-service/src/main/resources/application.yml:10-12` | 待确认 | `reconcile.enabled`、`reconcile.retry-times` 无读取代码（Q-M2） |

## 六、调用链路

### 6.1 调用树

```text
JOB-reconcile（@Scheduled cron 0 0 2 * * ?）
└─ SERVICE-account-service / MODULE-account-reconcile
   └─ ReconcileJob.reconcile（ReconcileJob.java:14-17）[空实现，无下游]
      └─ CONFIGURATION CONFIGGROUP-account-reconcile
         ├─ reconcile.enabled（期望启用条件，无绑定代码）
         └─ reconcile.retry-times（期望重试次数，无绑定代码与实现）
   └─ [未发现] TABLE 访问、下游服务、消息或文件产出
```

### 6.2 分支与触发条件

| 条件 | 路径 | 结果 | 证据 |
|------|------|------|------|
| `@Scheduled` 被调度框架注册 | 调度器 → `reconcile()` | 执行空方法体，无任何副作用 | `ReconcileJob.java:14-17` |
| 未发现 `@EnableScheduling` | 调度框架可能未启用 | 任务可能根本不执行（待确认） | `AccountApplication.java:7-11`；全工程未发现该注解（Q-M1） |
| 注释声明 `reconcile.enabled=true` | 期望作为启用开关 | 无绑定代码，无法确认实际生效 | `application.yml:10-11`、`ReconcileJob.java:8`（Q-M2） |
| 注释声明重试 `reconcile.retry-times` | 期望作为重试次数 | 无读取代码，`reconcile()` 无重试实现 | `application.yml:12`、`ReconcileJob.java:9`（Q-M2） |

### 6.3 逐层调用明细

| 层级 | 符号 | 职责 | 下游 | 证据 |
|------|------|------|------|------|
| 调度触发 | `@Scheduled(cron = "0 0 2 * * ?")` | 每日 02:00 触发 | `reconcile()` | `ReconcileJob.java:14` |
| 任务实现 | `ReconcileJob#reconcile()` | 未实现（空体） | 无 | `ReconcileJob.java:15-17` |
| 装配 | `@Component` | Bean 注册 | 无 | `ReconcileJob.java:11-12` |

## 七、数据模型与配置依赖

### 7.1 数据模型影响

| TABLE 稳定 ID | Schema/逻辑表 | 读写 | 涉及字段 | API 模型映射 | Mapper/DAO/SQL | 表字段证据状态 | 端到端映射状态 | 表文档链接 |
|---------------|---------------|------|----------|--------------|----------------|------------------|------------------|------------|
| 未发现（不得据任务名称推断对账目标表） | 待确认 | 待确认 | 未发现 | 不适用 | 未发现（`reconcile()` 无方法体，无 Mapper/SQL 调用） | 不适用 | 待确认 | - |

> 对账业务上预期涉及账户余额/状态（`TABLE-t_user_account`），但本阶段无任何代码或 SQL 证据，按规则不建立映射，登记 Q-M4 关联待确认。

### 7.2 配置依赖

| 配置组稳定 ID | 服务配置实体 | 配置键 | 直接影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| CONFIGGROUP-account-reconcile | `CONFIG-SERVICE-account-service` | `reconcile.enabled` | 副作用/触发：按注释声明决定任务是否执行 | 开发（default Profile） | 未发现绑定代码（无 `@Value`/`@ConfigurationProperties`/读取路径）；仅类注释声明 | 待确认（Q-M2） | [`SERVICE-account-service`](../configurations/SERVICE-account-service.md) |
| CONFIGGROUP-account-reconcile | `CONFIG-SERVICE-account-service` | `reconcile.retry-times` | 副作用：按注释声明决定失败重试次数 | 开发（default Profile） | 未发现绑定代码与重试实现 | 待确认（Q-M2） | [`SERVICE-account-service`](../configurations/SERVICE-account-service.md) |

> `CONFIGGROUP-account-datasource` 与 `CONFIGGROUP-account-server` 对本任务无直接证据支持的行为影响（任务无数据访问与网络入口），不纳入本节。

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
| 未发现 | - | - | - | `job/ReconcileJob.java` 无下游调用 |

### 8.5 文件与对象存储

| 协议或存储 | 逻辑位置 | 文件格式 | 触发方 | 接收方 | 证据 |
|------------|----------|----------|--------|--------|------|
| 未发现（未发现对账结果文件交换） | - | - | - | - | `job/ReconcileJob.java:11-17` |

### 8.6 定时任务与批处理

| 任务 | 触发方式 | 并发与锁 | 重试与补偿 | 证据 |
|------|----------|----------|------------|------|
| `JOB-reconcile` 每日账户对账 | `@Scheduled(cron = "0 0 2 * * ?")`（每日 02:00） | 未发现（无分布式锁、无并发控制配置） | 未发现（`reconcile.retry-times` 无读取代码，方法体无重试） | `ReconcileJob.java:14-17`、`application.yml:10-12` |

## 九、数据源与副作用分析

- 主数据来源：未发现（任务无数据访问代码）。
- 实时查询或补充路径：无。
- 写入、副作用或异步结果：未发现（方法体为空）；设计上应对账户数据对账并可能修正余额/状态，但无实现证据。
- 事务、一致性和失败处理：未发现 `@Transactional`、幂等控制、锁或补偿逻辑；多实例部署下的重复执行风险未得到控制（未发现调度锁配置）。

## 十、关键证据引用

| 引用 | 文件或资料位置 |
|------|----------------|
| 用户对外能力清单（未登记本能力） | `cadence/knowledge-base/user-input/api-scope.md:10-13` |
| 任务定义 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:11-17` |
| 启用装配 | `account-service/src/main/java/com/demo/account/AccountApplication.java:7-11`（未发现 `@EnableScheduling`） |
| 数据访问 | 未发现 |
| 配置依赖 | `CONFIG-SERVICE-account-service`、`reconcile.enabled`、`reconcile.retry-times`、`configurations/SERVICE-account-service.md`（Q-M1、Q-M2） |
| 中间件与外部调用 | 未发现 |

## 十一、请求、响应或载荷示例

未提供（任务无入参、无返回值、无产出物）。
