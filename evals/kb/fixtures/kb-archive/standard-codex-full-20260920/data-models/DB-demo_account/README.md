# demo_account

## 当前数据库/Schema

| 项目 | 内容 |
|------|------|
| 稳定 ID | DB-demo_account |
| 数据源 | SERVICE-account-service 的 `spring.datasource.*` 配置键（值已脱敏，见 `configurations/SERVICE-account-service.md`） |
| 数据库类型 | MySQL（由 DDL 方言与 mysql-connector-java 8.0.33 推断） |
| 数据库/Schema | demo_account |
| 业务域 | 用户账户 |
| 范围与排除项 | 范围：`t_user_account` 单表；排除：未发现视图、函数、触发器、分区与分片表 |
| 证据基线 | 1f867b9fcdf95f2e11808454898f333d7d512e90 |

## 表清单

| 逻辑表稳定 ID | 逻辑表 | 业务含义 | 读服务 | 写服务 | 证据状态 | 字段级文档 |
|----------------|--------|----------|--------|--------|----------|------------|
| TABLE-t_user_account | t_user_account | 用户账户（账户号、余额、状态） | SERVICE-account-service | 未发现（对账实现未提供） | DDL 已确认 | `data-models/DB-demo_account/TABLE-t_user_account.md` |

## 主要关系

| 来源表稳定 ID | 关系 | 目标表稳定 ID | 关系证据 | 证据状态 | 详情链接 |
|---------------|------|---------------|----------|----------|----------|
| TABLE-t_user_account | 候选关联 `user_id` → `user_id`（本库外，未确认外键） | TABLE-t_user | `db/init.sql:17` 注释“同 t_user.user_id”；`AccountEntity.java:5-6` | 待确认 | `data-models/DB-demo_account/TABLE-t_user_account.md` |

## 读写服务

| 服务稳定 ID | 读逻辑表 | 写逻辑表 | Mapper/SQL 入口 | 证据位置 |
|-------------|----------|----------|-----------------|----------|
| SERVICE-account-service | TABLE-t_user_account | 未发现 | `AccountMapper.selectByUserId`（`AccountMapper.xml#selectByUserId`） | `account-service/src/main/resources/mapper/AccountMapper.xml:5-7` |

## 分片规则

| 逻辑表稳定 ID | 分片键 | 分片规则 | 物理表规则 | 配置组稳定 ID | 证据状态 |
|----------------|--------|----------|------------|-----------------|----------|
| TABLE-t_user_account | 未发现 | 未发现 | 未发现 | 不适用 | 待确认（未发现分片证据） |

## 未覆盖对象

| 对象 | 未覆盖原因 | 影响 | 所需证据 | 跟踪项 |
|------|------------|------|----------|--------|
| 对账任务涉及的写路径 | `ReconcileJob` 无实现体，未发现持久化调用 | 余额变更与对账写入链路不可确认 | 对账实现代码或人工资料 | Q-M4（写服务未确认） |
| 视图/函数/触发器/二级索引 | 工程内 DDL 与代码均未涉及 | 无法确认实际数据库对象全集 | 数据库导出或迁移脚本 | 无（当前范围内未发现） |
