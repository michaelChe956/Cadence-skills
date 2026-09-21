# 每日账户对账流程

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 流程稳定 ID | FLOW-account-reconcile |
| 条目状态 | ai-draft |
| 来源 | 代码与配置证据（用户资料未描述对账流程） |

## 2. 目的与边界

每日 02:00 触发账户对账任务，按配置的启用开关与重试次数执行账户数据核对。不覆盖：对账规则、口径、差异处理与结果输出（均未实现）。

## 3. 步骤链

| 步骤 | 实体稳定 ID | 证据（文件:行号） | 说明 |
|------|-------------|-------------------|------|
| 1 | PAGE 不适用（批处理任务，无页面入口） | - | 任务为后台调度，无页面与 REST 触发入口 |
| 2 | API（任务旁路节点）JOB-reconcile | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:49-59` | `@Scheduled(cron = "0 0 2 * * ?")`，方法体为空实现 |
| 3 | SERVICE-account-service / MODULE-account-reconcile | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:49-59` | 任务组件归属该服务；未发现 `@EnableScheduling` 启用证据（Q-M1） |
| 4 | TABLE-t_user_account | `data-models/DB-demo_account/TABLE-t_user_account.md:19-22`、`db/init.sql:15-22` | 对账目标表为账户表；任务代码未访问该表（无 Mapper 调用证据） |
| 5 | CONFIGGROUP-account-reconcile | `account-service/src/main/resources/application.yml:10-12` | `reconcile.enabled`、`reconcile.retry-times` 键存在，但未发现代码读取（Q-M2） |
| 6 | MIDDLEWARE-mysql / DB-demo_account | `account-service/src/main/resources/application.yml:6-9`、`account-service/pom.xml:16` | 账户库数据源与驱动（连接值 `<redacted>`） |

```text
PAGE（不适用，无入口）→ JOB-reconcile → SERVICE-account-service/MODULE-account-reconcile
→ TABLE-t_user_account → CONFIGGROUP-account-reconcile/MIDDLEWARE-mysql
```

## 4. 状态流转

| 状态迁移 | 触发条件 | 证据（文件:行号） |
|----------|----------|-------------------|
| 不适用（未实现状态字段） | - | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:49-59`（空实现） |

## 5. 关联规则

| 规则稳定 ID | 关系说明 |
|-------------|----------|
| RULE-account-balance-non-negative | 对账预期核对余额合规性，但任务未实现该检查 |

## 6. 失败处理与异步边界

- 异步边界：Spring `@Scheduled` 单机调度；未发现分布式调度、任务锁或幂等控制。
- 重试：配置声明 `reconcile.retry-times`，但无绑定代码与失败重试实现（Q-M2）。
- 启用状态未确认：`application.yml` 声明 `reconcile.enabled: true`，工程内未发现 `@EnableScheduling`，任务是否注册执行无法确认（Q-M1）。
- 无失败告警、无对账结果输出与差异处理证据。
