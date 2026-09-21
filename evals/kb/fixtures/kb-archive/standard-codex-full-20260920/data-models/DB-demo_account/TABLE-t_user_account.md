# t_user_account

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 逻辑表稳定 ID | TABLE-t_user_account |
| 数据库/Schema 稳定 ID | DB-demo_account |
| 逻辑表名称 | t_user_account |
| 物理表名称或规则 | `t_user_account`（未发现物理分片规则） |
| 业务域 | 用户账户 |
| 证据基线（必填） | 1f867b9fcdf95f2e11808454898f333d7d512e90 |
| 最后核验时间（必填） | 2026-09-20 |

> `证据基线`（本次分析 Git 基线提交）与 `最后核验时间`（本次分析日期）为必填字段；为空视为文档不完整，阶段不得完成。

## 2. 业务含义

用户账户表，保存账户号、余额与账户状态（`NORMAL`/`FROZEN`/`CLOSED`）；表注释声明余额不允许为负值的业务硬约束 [代码证据]（`db/init.sql:22`）。

## 3. 字段清单

| 字段 | 类型 | 可空 | 默认值 | 主键 | 含义 | 代码映射 | 证据状态 | 证据位置 |
|------|------|------|--------|------|------|----------|----------|----------|
| `id` | `BIGINT` | 否 | DDL 未声明 | 是 | 主键 | 未映射（`AccountEntity` 无对应字段，`SELECT *` 会返回该列） | DDL 已确认 | `db/init.sql:16`；`account-service/src/main/resources/mapper/AccountMapper.xml:6` |
| `user_id` | `BIGINT` | 否 | DDL 未声明 | 否 | 用户唯一标识，注释声明与 `t_user.user_id` 同源 | `AccountEntity.userId`（隐式映射，Q-M3） | DDL 已确认 | `db/init.sql:17`；`AccountMapper.xml:6` |
| `account_no` | `VARCHAR(32)` | 否 | DDL 未声明 | 否 | 账户号 | `AccountEntity.accountNo`（依赖驼峰隐式映射，Q-M3） | DDL 已确认 | `db/init.sql:18` |
| `balance` | `DECIMAL(18,2)` | 否 | `0` | 否 | 账户余额；表注释声明不可为负 | `AccountEntity.balance` | DDL 已确认 | `db/init.sql:19,22` |
| `status` | `VARCHAR(16)` | 否 | `'NORMAL'` | 否 | 账户状态：`NORMAL`/`FROZEN`/`CLOSED` | `AccountEntity.status` | DDL 已确认 | `db/init.sql:20` |

> 证据状态只允许 `DDL 已确认`、`迁移已确认`、`代码可推导`、`用户提供`、`来源冲突`、`待确认`。缺少证据的属性单独写 `待确认`；不得依据 Entity、Mapper 或 SQL 补造实际索引、默认值或数据库约束。

## 4. 索引与约束

| 名称 | 类型 | 字段与顺序 | 定义 | 证据状态 | 证据位置 |
|------|------|------------|------|----------|----------|
| PRIMARY | 主键 | `id` | `PRIMARY KEY` | DDL 已确认 | `db/init.sql:16` |
| `uk_account_no` | 唯一约束 | `account_no` | `UNIQUE KEY uk_account_no (account_no)` | DDL 已确认 | `db/init.sql:21` |

未发现外键、检查约束或触发器；`balance >= 0` 仅在表注释中作为业务约束描述，DDL 未提供 `CHECK` 约束（见第 9 节与第 10 节）。实际数据库中是否存在其他索引无法从授权证据确认。

## 5. 分库分表

| 项目 | 内容 | 证据状态 | 证据位置 |
|------|------|----------|----------|
| 分片键 | 未发现 | 待确认 | 未发现分片配置或路由代码 |
| 分片规则 | 未发现 | 待确认 | 同上 |
| 物理表规则 | 未发现（按单表 `t_user_account` 建模） | 待确认 | `db/init.sql:15` |
| 配置组稳定 ID | 不适用 | 已确认 | `configurations/SERVICE-account-service.md` |

> 一张逻辑表只生成本文件一份；物理分片只记录规则，不为每个物理表复制文档。

## 6. Entity、Mapper 与 SQL 映射

| 类型 | 稳定 ID 或符号 | 操作 | 字段范围 | 证据位置 | 完整性限制 |
|------|----------------|------|----------|----------|------------|
| Entity | `CODE-AccountEntity`（`com.demo.account.entity.AccountEntity`） | - | `userId`、`accountNo`、`balance`、`status` | `account-service/src/main/java/com/demo/account/entity/AccountEntity.java:3-12` | 无 `id` 字段；无映射注解 |
| Mapper 接口 | `CODE-AccountMapper`（`com.demo.account.mapper.AccountMapper`） | SELECT | `user_id` 条件 | `account-service/src/main/java/com/demo/account/mapper/AccountMapper.java:10` | 仅一个查询方法 |
| Mapper XML | `CODE-AccountMapperXml-selectByUserId`（`AccountMapper.xml#selectByUserId`） | SELECT | `SELECT *`（全部 5 列） | `account-service/src/main/resources/mapper/AccountMapper.xml:4-7` | 未维护 `resultMap`，字段映射依赖隐式约定，存在映射失效风险（Q-M3） |

未发现 `INSERT`、`UPDATE`、`DELETE` 语句，因此本表写入链路缺失（仅表示授权证据未覆盖）。

## 7. 读写服务

| 服务稳定 ID | 方法或入口 | 读/写 | 调用映射 | 证据位置 |
|-------------|------------|-------|----------|----------|
| SERVICE-account-service | `AccountService.queryAccount(Long)` | 读 | `AccountMapper.selectByUserId` | `account-service/src/main/java/com/demo/account/service/AccountService.java:17-20` |
| SERVICE-account-service（待确认） | `ReconcileJob.reconcile()`（无实现体） | 写（推断，未确认） | 未发现 Mapper 调用 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:14-17` |

## 8. 关联 API 与页面

| 类型 | 稳定 ID | 名称 | 关系 | 证据位置 |
|------|---------|------|------|----------|
| API | 未生成（`api` 阶段尚未执行，本阶段不扫描接口） | - | - | `open-questions.md` |
| 页面 | 未生成（`pages` 阶段尚未执行，本阶段不扫描页面） | - | - | `open-questions.md` |

## 9. 特殊字段与数据规则

| 字段 | 规则类型 | 规则说明 | 证据状态 | 证据位置 |
|------|----------|----------|----------|----------|
| `balance` | 业务硬约束 | 余额不允许出现负值（表注释声明） | DDL 已确认（注释证据，无 `CHECK` 约束） | `db/init.sql:19,22` |
| `status` | 枚举取值 | `NORMAL`/`FROZEN`/`CLOSED` | DDL 已确认 | `db/init.sql:20` |
| `account_no` | 唯一性 | 由 `uk_account_no` 保证唯一 | DDL 已确认 | `db/init.sql:21` |
| `user_id` | 标识关联 | 注释声明与 `t_user.user_id` 同源（候选关联） | 待确认 | `db/init.sql:17` |

## 10. 证据与来源冲突

| 对象或属性 | 来源 A | 来源 B | 冲突或限制 | 影响 | 处理状态 |
|------------|--------|--------|------------|------|----------|
| 字段映射方式 | `AccountMapper.xml:4-7`（`SELECT *`，无 `resultMap`） | `AccountEntity.java:3-12`（`accountNo` 等驼峰字段） | 依赖 `mapUnderscoreToCamelCase` 等隐式设置，工程配置中未声明该设置 | 账户字段可能映射失败（`accountNo`、`userId`） | 待确认（Q-M3） |
| `id` 字段 | `db/init.sql:16` | `AccountEntity` 未定义 `id` | `SELECT *` 会返回未映射列 | 无功能影响，但映射不完整 | 已记录 |
| `balance >= 0` | `db/init.sql:22` 表注释 | DDL 无 `CHECK` 约束 | 约束仅存在于业务注释 | 无法确认数据库层强制 | 待确认（Q-L9 业务规则候选）；规则卡 `business/rules/RULE-account-balance-non-negative.md` |
| `user_id` 引用 | `db/init.sql:17` 注释 | DDL 无 `FOREIGN KEY` | 注释不能证明约束 | 跨库关联不能作为数据库事实 | 待确认（Q-M5） |

## 11. 变更记录

| 日期 | 基线 | 变更内容 | 来源 |
|------|------|----------|------|
| 2026-09-20 | 1f867b9fcdf95f2e11808454898f333d7d512e90 | 首次生成字段级文档 | knowledge-base-base-info |
