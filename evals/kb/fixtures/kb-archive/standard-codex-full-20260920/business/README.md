# 业务域索引

## 元数据

| 项目 | 内容 |
|------|------|
| 证据基线 | 1f867b9fcdf95f2e11808454898f333d7d512e90（分支 master） |
| 分析时间 | 2026-09-20（overview 阶段生成） |
| 来源优先级 | 用户资料与 `user-input/product.md` > 测试断言 > ADR（未提供）> 既有文档寄生规则迁移 > git 历史（仅 ai-draft） |
| 业务知识来源 | `user-input/product.md`（用户资料）；测试来源 `**/src/test/**`；ADR 未提供；git 历史范围 `54959c91e603b42092331bf5ba3d90107bdb2bf1..HEAD` |
| 计数摘要 | 规则 4（confirmed 1、ai-draft 3）；流程 6（confirmed 3、ai-draft 3） |
| 证据限制 | 未连接数据库与运行态中间件；未执行测试（测试依赖未声明，Q-H1）；git 历史仅两个提交 |

> 本索引只提供清单与计数，规则陈述、步骤链与证据明细见各规则卡与流程文档。

## 规则清单

| 规则稳定 ID | 名称 | 类型 | 条目状态 | 来源 | 明细 |
|-------------|------|------|----------|------|------|
| RULE-order-ship-constraint | 订单发货状态约束 | 状态迁移 | confirmed | 测试断言 + 代码 + 用户资料 | [`RULE-order-ship-constraint`](rules/RULE-order-ship-constraint.md) |
| RULE-order-status-transition | 订单状态迁移链 | 状态迁移 | ai-draft | 代码与 DDL 注释 | [`RULE-order-status-transition`](rules/RULE-order-status-transition.md) |
| RULE-account-balance-non-negative | 账户余额不可为负 | 约束 | ai-draft | DDL 表注释 | [`RULE-account-balance-non-negative`](rules/RULE-account-balance-non-negative.md) |
| RULE-order-export-retention | 订单导出文件保留 7 天 | 阈值 | ai-draft | 代码常量 + DDL 注释 + git 历史 | [`RULE-order-export-retention`](rules/RULE-order-export-retention.md) |

ai-draft 规则均登记待确认 Q-L9，不得作为确定业务定义使用。

## 流程清单

| 流程稳定 ID | 名称 | 条目状态 | 来源 | 稳定主链（摘要） | 明细 |
|-------------|------|----------|------|------------------|------|
| FLOW-user-basic-query | 用户基本信息查询 | confirmed | 用户资料 + 代码证据 | PAGE → API → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE | [`FLOW-user-basic-query`](flows/FLOW-user-basic-query.md) |
| FLOW-account-query | 账户信息查询 | confirmed | 用户资料 + 代码证据 | PAGE → API → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE | [`FLOW-account-query`](flows/FLOW-account-query.md) |
| FLOW-order-ship | 订单发货 | confirmed | 用户资料 + 测试断言 + 代码证据 | PAGE → ROUTE → API → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE | [`FLOW-order-ship`](flows/FLOW-order-ship.md) |
| FLOW-order-export | 订单导出 | ai-draft | 用户资料 + 代码存根证据 | PAGE → ROUTE → API → SERVICE/MODULE → TABLE → CONFIGURATION（端到端未实现） | [`FLOW-order-export`](flows/FLOW-order-export.md) |
| FLOW-order-paid-event | 订单已支付事件处理 | ai-draft | 代码与配置证据 | PAGE 不适用 → EVENT → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE | [`FLOW-order-paid-event`](flows/FLOW-order-paid-event.md) |
| FLOW-account-reconcile | 每日账户对账 | ai-draft | 代码与配置证据 | PAGE 不适用 → JOB → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE | [`FLOW-account-reconcile`](flows/FLOW-account-reconcile.md) |

## 来源限制与待确认

- 未提供 ADR（`evidence.business_knowledge_sources.adr_sources` 为空列表），业务设计意图只能依赖用户资料、测试断言与代码证据。
- git 历史范围内仅 `54959c9`（初始化）与 `1f867b9`（导出保留期修复）两个提交，只能支撑 RULE-order-export-retention 的历史意图，且证据为 ref 型（`ExportService.java:10@1f867b9...`）。
- 既有 API/表文档中的寄生规则已迁移为规则卡并在原位置追加链接，原文未删除。
- 业务规则实现缺口、事件不可达与对账未启用等风险见 `open-questions.md`（Q-H2、Q-M1、Q-M2、Q-M4、Q-M10、Q-L9）。

