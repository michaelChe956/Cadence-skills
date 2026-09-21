# 订单生命周期

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 流程稳定 ID | FLOW-order-lifecycle |
| 条目状态 | ai-draft |
| 来源 | 测试断言 |

## 3. 步骤链

| 步骤 | 实体稳定 ID |
|------|-------------|
| 创建订单 | API-order-ship |

## 4. 状态流转

| 状态迁移 | 触发条件 | 证据（文件:行号） |
|----------|----------|-------------------|
| CREATED → PAID | 支付回调 | OrderService.java:41 |
| PAID → SHIPPED | 发货 | OrderService.java:33 |
