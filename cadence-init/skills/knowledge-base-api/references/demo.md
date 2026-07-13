# API 能力案例

## REST 对外能力

- ID：`API-order-create`
- 分类：合作方受限外部 REST API
- 状态：已声明、已实现、已装配、已暴露
- 方法：`POST /partner/v1/orders`
- 鉴权：合作方签名与时间戳
- 实现：`PartnerOrderController#create`
- 下游：`OrderApplicationService#create`
- 副作用：写入 `TABLE-order`，生产 `EVENT-order-created`
- 证据：OpenAPI、Gateway 路由、Security 配置、Controller
- 可信度：高

## 内部 REST 能力

- ID：`API-order-page`
- 分类：内部前端 REST API
- 状态：已实现、已装配
- 方法：`GET /admin/orders`
- 调用方：`PAGE-order-list`
- 外部暴露：未发现公网或合作方网关证据
- 可信度：中

## Dubbo 能力

- Provider：`OrderQueryService`
- Consumer：`report-service`
- 版本：来自 Dubbo 注解和配置
- 状态：Provider 已装配；Consumer 调用存在
- 注意：接口模块本身不被记录为独立运行服务

## Kafka 能力

- ID：`EVENT-order-created`
- Producer：`OrderEventPublisher`
- Consumer：当前仓库未发现
- Topic：使用逻辑配置键表示，实际环境值脱敏
- 重试与 DLQ：代码和配置未发现，标记高优先级待确认

