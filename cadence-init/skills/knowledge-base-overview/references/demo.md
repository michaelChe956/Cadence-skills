# 项目概览案例

## 项目入口摘要

该项目是订单管理 B/S 系统，由 `admin-web`、`order-service` 和 `user-service` 组成。订单创建通过内部管理页面发起，也向合作方提供受限外部 API。订单创建后写入订单库并发布 Kafka 事件。

入口只保留上述摘要和导航，不复制订单字段清单或全部配置键。

## 一级导航

- [`base-information.md`](base-information.md)
- [`development-guide.md`](development-guide.md)
- [`interfaces/README.md`](interfaces/README.md)
- [`pages/README.md`](pages/README.md)
- [`services/`](services/)
- [`data-models/README.md`](data-models/README.md)
- [`configurations/README.md`](configurations/README.md)
- [`evidence/`](evidence/)
- [`change-history.md`](change-history.md)
- [`open-questions.md`](open-questions.md)

## 核心流程

```text
PAGE-order-create
→ API-order-create
→ SERVICE-order-service/MODULE-order-write
→ TABLE-order
→ CONFIGURATION-order-write/PROFILE-production
→ MIDDLEWARE-kafka
```

每个 ID 链接到对应领域文档和证据索引。

## 修改示例

订单状态字段调整前，先使用 `knowledge-base-context`，再读取字段级订单表文档、API 与页面字段映射及当前结构证据。若同时调整 Kafka Topic 配置，还需读取订单服务配置文档和当前配置快照。

实现与验证完成后，用户显式指定唯一变更标识 `order-status-field`，完整变更包只能写入：

```text
cadence/knowledge-base/user-input/updates/CHANGE-order-status-field/
├── change-summary.md
├── code-change.md
├── database-change.md
├── configuration-change.md
└── verification.md
```

五份固定文件不得合并或省略，附件不能替代它们。本例若数据库结构没有变化，`database-change.md` 仍保留并记录“无数据库变更”及当前结构证据；若配置没有变化，`configuration-change.md` 仍保留并记录“无配置变更”及当前快照依据。契约完整后，使用 `knowledge-base-update` 执行 Update。

## 术语示例

- ATP `[用户提供]` `[可信度：高]`
  - 项目含义：可承诺库存
  - 适用模块：库存与订单校验
  - 通用含义差异：不是自动化测试平台

- 冻结订单 `[合理推断]` `[可信度：中]`
  - 候选含义：禁止继续履约但保留查询
  - 证据：状态枚举和两个 Service 分支
  - 待确认：是否允许人工解冻

## 规则合并示例

已有 `AGENTS.md` 包含测试和提交规则。技能保留原文，只在文件末尾追加一个 KnowledgeBase 管理区块。再次执行时只更新该区块，不产生第二份内容。
