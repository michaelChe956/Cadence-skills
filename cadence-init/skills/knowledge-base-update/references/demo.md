# 增量更新案例

## 变更范围

- Git：`abc1234..def5678`
- `OrderController#create` 路径从 `/orders` 改为 `/v2/orders`
- `t_order.remark` 字段删除
- Vue 页面从 `views/order/create.vue` 移动到 `views/order/form.vue`
- Kafka 新增订单取消事件

## 影响处理

### API 路径变化

- 保留 `API-order-create`。
- 更新路径、网关映射和页面调用证据。
- 检查旧路径是否保留兼容路由。
- 更新 API 文档和关系矩阵。

### DDL 字段删除

- 更新 `TABLE-order` 字段清单。
- 检查 Entity、DTO、Mapper 和页面表单是否仍引用 `remark`。
- 未同步引用写入高优先级待确认项。

### 页面移动

- 保留 `PAGE-order-create` 和路由 ID。
- 只更新组件来源路径。
- 不记录为页面删除和新增。

### 新增 Kafka 事件

- 新增 `EVENT-order-cancelled`。
- 记录 Producer、Topic 配置键、消息模型和 Consumer 状态。
- 当前仓库未发现 Consumer 时标记外部消费者待确认。

## 幂等结果

再次使用相同起止提交执行时，不重复追加同一变更历史，也不生成第二组稳定 ID。

