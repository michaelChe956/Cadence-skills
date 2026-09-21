# 账户余额不可为负

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 规则稳定 ID | RULE-account-balance-non-negative |
| 条目状态 | ai-draft |
| 规则类型 | 约束 |
| 来源 | DDL 表注释（无用户权威输入、无实现与测试） |

## 2. 规则陈述

用户账户余额（`t_user_account.balance`）不允许出现负值，属业务硬约束。

## 3. 适用范围

| 实体稳定 ID | 关系说明 |
|------------|----------|
| TABLE-t_user_account | `balance` 字段是该约束的作用对象 |
| API-account-query | 该接口读取并返回 `balance`，可能暴露违规数据 |
| FLOW-account-query | 只读流程，未包含校验步骤 |
| PAGE-account-query | 页面展示 `balance` |

## 4. 证据

| 证据类型 | 位置 | 说明 |
|----------|------|------|
| DDL 注释 | `db/init.sql:19` | 列注释“账户余额；业务规则：余额不可为负” |
| DDL 注释 | `db/init.sql:22` | 表注释“本表余额字段不允许出现负值（业务硬约束）” |
| 代码 | `account-service/src/main/resources/mapper/AccountMapper.xml:5-7` | 仅有 `SELECT *` 只读查询，未发现余额写入或校验代码 |

## 5. 关联与例外

- 关联规则：无（除本卡外未发现相关规则卡）。
- 已知例外与未确认：DDL 未声明 `CHECK` 约束，工程内无余额写入路径与校验代码，约束是否在数据库层或上游系统强制无法确认（Q-L9；`data-models/DB-demo_account/TABLE-t_user_account.md` 第 10 节）。

