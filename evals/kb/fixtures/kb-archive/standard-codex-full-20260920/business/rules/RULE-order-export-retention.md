# 订单导出文件保留 7 天

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 规则稳定 ID | RULE-order-export-retention |
| 条目状态 | ai-draft |
| 规则类型 | 阈值 |
| 来源 | 代码常量 + DDL 注释 + git 历史（无用户权威输入与测试断言） |

## 2. 规则陈述

订单导出文件自导出之日起保留 7 天，到期后应被清理。

## 3. 适用范围

| 实体稳定 ID | 关系说明 |
|------------|----------|
| FILE-order-export-file | 该能力是规则的直接作用对象 |
| TABLE-t_export_file | `created_at` 是保留期起算字段，登记表是清理对象 |
| MODULE-order-export | 保留期常量与导出入口所在模块 |
| FLOW-order-export | 导出流程的保留期约束 |
| API-order-export | 导出接口声明该约束但未实现清理 |

## 4. 证据

| 证据类型 | 位置 | 说明 |
|----------|------|------|
| 代码 | `order-service/src/main/java/com/demo/order/service/ExportService.java:9-10` | `RETENTION_DAYS = 7`，注释记录历史误配 30 天后修复 |
| DDL 注释 | `db/init.sql:39` | 列注释“导出时间；保留 7 天后清理” |
| git 历史 | `order-service/src/main/java/com/demo/order/service/ExportService.java:10@1f867b9fcdf95f2e11808454898f333d7d512e90` | 提交 `1f867b9` 将保留期由 30 天改为 7 天 |
| 接口文档 | `cadence/knowledge-base/interfaces/API-order-export_订单导出_export.md:174` | 登记业务规则来源为上述提交与常量 |

## 5. 关联与例外

- 关联规则：无。
- 已知例外与未确认：未发现文件生成、登记、交付与清理实现，保留期仅以常量与注释声明（Q-H2、Q-M4）；`t_export_file` 无写入路径。条目状态为 `ai-draft`，登记待确认 Q-L9。
