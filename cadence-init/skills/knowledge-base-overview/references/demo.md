# 项目概览案例

## 项目入口摘要

该项目是订单管理 B/S 系统，由 `admin-web`、`order-service` 和 `user-service` 组成。订单创建通过内部管理页面发起，也向合作方提供受限外部 API。订单创建后写入订单库并发布 Kafka 事件。

## 核心流程

```text
ROUTE-admin-orders-create
→ PAGE-order-create
→ API-order-create
→ SERVICE-order-service
→ TABLE-order
→ EVENT-order-created
```

每个 ID 链接到对应领域文档和证据索引。

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

