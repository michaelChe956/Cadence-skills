# API-order-page 订单分页查询接口

> **能力 ID**：`API-order-page`
> **分类**：对内
> **能力类型**：REST
> **数据来源**：用户提供的接口清单、DDL 与虚构示例工程代码
> **梳理日期**：2026-07-16
> **参数与报文**：见同目录 `demo_参数与报文.md`
>
> **案例声明**：本文所有组织、域名、地址、包名、库表、Topic、Key、配置和代码路径均为虚构示例，仅用于展示完整分析格式。实际执行必须以用户输入文档、DDL 和工程代码为准。

## 一、能力基础信息

| 项目 | 值 |
|------|----|
| 能力名称 | 订单分页查询接口 |
| API 名称或逻辑标识 | `orderPageQuery` |
| 分类 | 对内 |
| 能力类型 | REST |
| 协议与方法 | HTTPS POST |
| 路径或逻辑地址 | `/api/admin/orders/query` |
| 数据格式 | JSON |
| 是否需授权 | 是，要求登录态及 `order:view` 权限 |
| 版本 | v1 |
| 调用方或生产者 | 订单管理页面、内部运营工具 |
| 落地方或消费者 | `order-query-service` |
| 生命周期状态 | 已声明、已实现、已装配、已暴露 |
| 入参压缩 | 否 |
| 出参压缩 | 否 |

### 调用入口

| 环境 | URL | 证据状态 |
|------|-----|----------|
| 生产 | `https://api.example.invalid/api/admin/orders/query` | 用户接口资料中的脱敏逻辑地址 |
| 联调 | `https://sandbox.example.invalid/api/admin/orders/query` | 用户接口资料中的脱敏逻辑地址 |
| 本地 | `http://localhost:8080/api/admin/orders/query` | 工程配置默认值 |

> `.invalid` 是保留的无效顶级域名，示例地址不可用于真实访问。

## 二、业务需求描述

- 订单管理页面根据租户、订单状态、创建时间、买家关键字和商品关键字分页查询订单。
- 查询成功时返回分页信息、订单摘要、金额、履约状态和风险标记。
- 默认路径读取订单库，并通过缓存或下游服务补充客户等级、风险摘要和配送状态。
- 全文搜索条件启用时使用搜索索引召回订单 ID，再回查订单库获得权威数据。
- 主业务链路只读；启用查询审计时异步发送审计事件，不影响主响应。
- 参数校验、权限校验或下游补充失败时返回明确错误或降级标记。

## 三、输入参数

详见 `demo_参数与报文.md` 第一节。

## 四、输出参数

详见 `demo_参数与报文.md` 第二节。

## 五、代码实现定位

### 5.1 用户清单与代码映射

**结论：接口未登记在用户提供的对外能力清单中，因此分类为对内；REST 入口能够从路由、Controller、权限注解和应用装配配置形成完整证据链。**

| 来源 | 标识 | 结论 | 证据 |
|------|------|------|------|
| 用户对外能力清单 | 未登记 `API-order-page` | 保持对内分类 | `cadence/knowledge-base/user-input/api-scope.md` |
| 页面调用 | `orderApi.queryPage` | 管理端页面实际调用 | `admin-web/src/api/order.ts:18-26` |
| REST 路由 | `POST /api/admin/orders/query` | 入口已声明 | `order-query-service/src/main/java/com/example/order/interfaces/rest/OrderQueryController.java:28-45` |
| 权限装配 | `@PreAuthorize("hasAuthority('order:view')")` | 接口受权限保护 | `OrderQueryController.java:31` |
| 应用装配 | `OrderQueryApplication` 扫描 `com.example.order` | Controller 已装配 | `order-query-service/src/main/java/com/example/order/OrderQueryApplication.java:9-13` |
| 网关路由 | `/api/admin/orders/**` → `order-query-service` | 接口已暴露 | `gateway/src/main/resources/routes/order-query.yaml:4-12` |

**URL 路由机制**：管理页面调用 `/api/admin/orders/query`，请求封装添加 `/api` 前缀；开发代理只重写主机，不修改路径。网关按 `/api/admin/orders/**` 路由到 `order-query-service`，Spring MVC 再由类级 `/api/admin/orders` 与方法级 `/query` 合成最终路径。

**容易混淆的同名入口**：

- `OrderCommandController#createOrder()` 对应 `API-order-create`，不是本接口。
- `PartnerOrderController#queryOrders()` 对应合作方对外接口 `API-partner-order-page`，路径、鉴权和响应模型均不同。
- `OrderQueryFacade#queryPage()` 是服务间 RPC Provider，不是浏览器直接访问的 REST 入口。

### 5.2 实现清单

| 层级 | 符号 | 文件路径 | 状态 | 说明 |
|------|------|----------|------|------|
| 页面请求 | `orderApi.queryPage` | `admin-web/src/api/order.ts` | 已实现 | 通过统一请求封装发起 REST 请求 |
| REST 入口 | `OrderQueryController#queryPage` | `order-query-service/src/main/java/com/example/order/interfaces/rest/OrderQueryController.java` | 已实现、已装配 | 参数校验、权限校验、调用应用服务 |
| 应用服务 | `OrderQueryApplicationService#queryPage` | `order-query-service/src/main/java/com/example/order/application/OrderQueryApplicationService.java` | 已实现 | 编排查询、降级和审计 |
| 多单元路由 | `OrderRegionRouter#route` | `order-query-service/src/main/java/com/example/order/infrastructure/routing/OrderRegionRouter.java` | 条件启用 | 根据租户与开关选择本地或远端单元 |
| 领域查询 | `OrderQueryService#query` | `order-query-domain/src/main/java/com/example/order/domain/query/OrderQueryService.java` | 已实现 | 规范化条件并执行核心查询 |
| 数据访问 | `OrderQueryRepository#findPage` | `order-query-infrastructure/src/main/java/com/example/order/infrastructure/repository/OrderQueryRepository.java` | 已实现 | 缓存、搜索索引和数据库查询 |
| MyBatis Mapper | `OrderQueryMapper#selectPage` | `order-query-infrastructure/src/main/resources/mapper/OrderQueryMapper.xml` | 已实现 | 查询订单与订单项摘要 |
| 客户补充 | `CustomerProfileClient#getProfiles` | `order-query-infrastructure/src/main/java/com/example/order/infrastructure/client/CustomerProfileClient.java` | 条件调用 | Dubbo 批量查询客户等级 |
| 履约补充 | `FulfillmentClient#getStatusBatch` | `order-query-infrastructure/src/main/java/com/example/order/infrastructure/client/FulfillmentClient.java` | 条件调用 | HTTP 批量查询配送状态 |
| 查询审计 | `OrderQueryAuditPublisher#publish` | `order-query-infrastructure/src/main/java/com/example/order/infrastructure/messaging/OrderQueryAuditPublisher.java` | 条件启用 | 异步发送查询审计事件 |

## 六、调用链路

### 6.1 调用树

```text
PAGE-order-list
└─ orderApi.queryPage(request)
   └─ POST /api/admin/orders/query
      └─ API Gateway → order-query-service
         └─ OrderQueryController.queryPage(request)
            └─ OrderQueryApplicationService.queryPage(command)
               ├─ PermissionContext.requireTenantAccess(tenantId)
               ├─ OrderRegionRouter.route(tenantId)
               │  ├─ [远端单元] OrderQueryFacade.queryPage(command) → Dubbo RPC
               │  └─ [本地单元] OrderQueryService.query(criteria)
               │     └─ OrderQueryRepository.findPage(criteria)
               │        ├─ [精确筛选] Redis 查询缓存
               │        │  └─ miss → OrderQueryMapper.selectPage(criteria)
               │        │           ├─ order_db.t_order
               │        │           └─ order_db.t_order_item
               │        └─ [全文搜索] Elasticsearch order_index
               │           └─ 订单 ID 列表 → OrderQueryMapper.selectByIds(ids)
               ├─ CustomerProfileClient.getProfiles(customerIds) → Dubbo RPC
               ├─ FulfillmentClient.getStatusBatch(orderIds) → HTTP
               ├─ OrderRiskCache.getBatch(orderIds) → Caffeine 本地缓存
               └─ [审计开启] OrderQueryAuditPublisher.publish(event) → Kafka
```

### 6.2 分支与触发条件

| 条件 | 路径 | 结果 | 证据 |
|------|------|------|------|
| `ORDER_QUERY_REGION_ROUTE:{tenantId}` 为 `REMOTE` 且全局多单元开关开启 | Controller → ApplicationService → RegionRouter → Dubbo `OrderQueryFacade` | 请求路由到租户归属单元 | `OrderRegionRouter.java:34-61`、`application.yaml:48-52` |
| 多单元开关关闭或租户归属本地 | Controller → ApplicationService → OrderQueryService | 本地查询 | `OrderRegionRouter.java:48-57` |
| `searchMode=FULL_TEXT` 且关键字非空 | Repository → Elasticsearch → Mapper 回查 | 搜索索引负责召回，数据库负责最终数据 | `OrderQueryRepository.java:73-98` |
| 非全文搜索 | Repository → Redis → MyBatis | 精确筛选与分页 | `OrderQueryRepository.java:42-71` |
| Redis 命中 | Repository → Redis | 返回缓存分页结果 | `OrderQueryCache.java:25-43` |
| Redis 未命中 | Repository → MyBatis → Redis | 查库并回填缓存 | `OrderQueryRepository.java:53-67` |
| `includeCustomerProfile=true` | CustomerProfileClient | 补充客户等级；失败时标记 `profileDegraded=true` | `OrderQueryApplicationService.java:82-104` |
| `includeFulfillment=true` | FulfillmentClient | 补充履约状态；超时后保留订单主数据 | `OrderQueryApplicationService.java:106-128` |
| `order.query.audit-enabled=true` | AuditPublisher → Kafka | 异步记录查询审计 | `OrderQueryApplicationService.java:135-143` |

### 6.3 逐层调用明细

#### 第 1 层：REST 入口

- 类与方法：`OrderQueryController#queryPage(OrderPageQueryRequest)`
- 文件：`order-query-service/src/main/java/com/example/order/interfaces/rest/OrderQueryController.java:28-45`
- 职责：权限校验、Bean Validation、请求模型转换、统一响应包装。
- 关键行为：

```java
@PostMapping("/query")
@PreAuthorize("hasAuthority('order:view')")
public ApiResponse<PageResult<OrderSummaryResponse>> queryPage(
        @Valid @RequestBody OrderPageQueryRequest request) {
    return ApiResponse.success(orderQueryApplicationService.queryPage(request.toCommand()));
}
```

#### 第 2 层：应用服务与多单元路由

- 类与方法：`OrderQueryApplicationService#queryPage(OrderPageQueryCommand)`
- 文件：`order-query-service/src/main/java/com/example/order/application/OrderQueryApplicationService.java:45-145`
- 职责：租户访问校验、单元路由、数据补充、降级标记和审计事件。
- 路由规则：先读取 Redis 租户路由 Key；未配置时使用本地单元，不根据租户名称猜测归属。

```java
RegionTarget target = orderRegionRouter.route(command.tenantId());
PageResult<OrderSummary> page = target.isRemote()
        ? remoteOrderQueryFacade.queryPage(command)
        : orderQueryService.query(command.toCriteria());
return orderSummaryAssembler.enrich(page, command);
```

#### 第 3 层：领域查询与仓储

- 类与方法：`OrderQueryService#query(OrderQueryCriteria)`
- 文件：`order-query-domain/src/main/java/com/example/order/domain/query/OrderQueryService.java:22-58`
- 职责：标准化时间范围、限制最大分页大小、校验状态组合并调用仓储。
- 仓储：`OrderQueryRepository#findPage` 负责选择精确筛选或全文检索路径。
- 缓存：仅缓存不包含敏感关键字的精确查询，缓存 Key 使用条件摘要，不写入明文手机号或姓名。

#### 第 4 层：数据访问和数据补充

- MyBatis：`OrderQueryMapper#selectPage` 查询订单主表并汇总订单项。
- Elasticsearch：只返回候选订单 ID 和匹配分值，最终字段回查数据库。
- Customer RPC：批量查询客户等级，不改变订单主数据。
- Fulfillment HTTP：批量查询配送状态，超时降级为 `UNKNOWN`。
- Risk Caffeine：读取本地风险摘要；本地缓存由 Kafka 和定时任务刷新。

## 七、数据库与表

本案例的数据库结论仅来自用户提供的 DDL、Mapper SQL 和数据源配置，不连接数据库，也不查询在线元数据。

| 数据库或 Schema | 表名 | 用途 | 操作 | Mapper/DAO/SQL | 证据 |
|------------------|------|------|------|----------------|------|
| `order_db` | `t_order` | 订单主数据、状态、金额、客户和创建时间 | R | `OrderQueryMapper.selectPage/selectByIds` | `inputs/ddl/order.sql`、`OrderQueryMapper.xml:18-96` |
| `order_db` | `t_order_item` | 商品名称、数量和订单商品摘要 | R | `OrderQueryMapper.selectItemSummary` | `inputs/ddl/order_item.sql`、`OrderQueryMapper.xml:98-131` |
| `order_db` | `t_order_payment` | 支付方式与支付状态 | R | `OrderPaymentMapper.selectByOrderIds` | `inputs/ddl/order_payment.sql`、`OrderPaymentMapper.xml:12-39` |
| `customer_db` | `t_customer_profile` | 客户等级与客户标签 | 间接 R | 由 `customer-profile-service` 访问，本工程不直连 | `inputs/ddl/customer_profile.sql`、`CustomerProfileClient.java:20-37` |
| 待确认 | `t_order_risk_snapshot` | 风险快照的离线来源候选 | 未发现本接口直查 | 无当前工程 Mapper | 用户 DDL 存在该表，但当前调用链未发现引用 |

> `t_order_risk_snapshot` 不能仅因名称相似就认定为本接口数据源；当前只记录为待确认候选。

## 八、中间件使用明细

### 8.1 缓存与队列

| 类型 | 名称或 Key 模式 | 读写方向 | TTL | 触发时机 | 证据 |
|------|-----------------|----------|-----|----------|------|
| Redis KV | `ORDER_QUERY_REGION_ROUTE:{tenantId}` | 读 | 无固定 TTL | 每次查询决定本地或远端单元 | `OrderRegionRouter.java:34-44` |
| Redis KV | `ORDER_QUERY_PAGE:{tenantId}:{criteriaDigest}` | 读/写 | 120 秒 | 精确查询缓存；miss 后回填 | `OrderQueryCache.java:25-58` |
| Redis KV | `ORDER_QUERY_AUDIT_SWITCH` | 读 | 无固定 TTL | 判断是否发送查询审计事件 | `OrderQueryAuditProperties.java:16-29` |
| Redis Stream | `ORDER_QUERY_REBUILD_STREAM` | 消费 | 按 Stream 策略 | 管理端触发索引重建时消费任务 | `OrderIndexRebuildConsumer.java:31-74` |

### 8.2 消息

主查询链路不依赖消息返回结果，但使用消息刷新本地缓存并可选记录审计。

| Topic/Queue/Group | 方向 | 消息模型 | 重试与幂等 | 证据 |
|-------------------|------|----------|------------|------|
| `order.changed.v1` / `order-query-cache-group` | 消费 | `OrderChangedEvent` | 以 `eventId` 去重；失败进入重试 Topic | `OrderChangedConsumer.java:24-79` |
| `order.risk.changed.v1` / `order-query-risk-group` | 消费 | `OrderRiskChangedEvent` | 以 `orderId + version` 覆盖更新 | `OrderRiskChangedConsumer.java:21-63` |
| `order.query.audit.v1` | 生产 | `OrderQueryAuditEvent` | 主链路不重试；发送失败只记录指标 | `OrderQueryAuditPublisher.java:28-55` |
| `order.index.rebuild.dlq` | 消费 | `OrderIndexRebuildFailedEvent` | 人工确认后重新投递 | `OrderIndexRebuildDlqConsumer.java:19-47` |

### 8.3 搜索与本地缓存

| 组件 | 数据结构或索引 | 初始化/加载方式 | 刷新机制 | 证据 |
|------|----------------|---------------|----------|------|
| Elasticsearch | `order_index_v1`，别名 `order_index` | 离线全量任务首次构建 | `order.changed.v1` 增量更新；每日校准任务补偿 | `OrderSearchRepository.java:30-106`、`OrderIndexReconcileJob.java:33-81` |
| Caffeine | `orderRiskCache<orderId, RiskSummary>` | 启动时加载最近活跃订单风险摘要 | Kafka 增量刷新；每 10 分钟校准 | `OrderRiskCache.java:18-66` |
| Caffeine | `orderStatusDictionary<code, label>` | 启动时读取配置文件 | 配置变更事件触发整体刷新 | `OrderDictionaryCache.java:21-58` |

全文检索只负责候选 ID 召回。数据库回查结果为空时丢弃对应候选，不使用索引旧值补造订单数据。

### 8.4 RPC 与下游 HTTP

| 服务 | 协议 | 版本或分组 | 触发条件 | 失败处理 | 证据 |
|------|------|------------|----------|----------|------|
| `OrderQueryFacade#queryPage` | Dubbo | `1.0.0` / `order-query` | 租户被路由到远端单元 | 超时返回 `REGION_QUERY_TIMEOUT`，不自动改查本地库 | `OrderRegionRouter.java:55-61`、`dubbo-consumer.yaml:8-17` |
| `CustomerProfileFacade#getProfiles` | Dubbo | `1.2.0` / `customer-profile` | `includeCustomerProfile=true` | 返回空补充数据并设置降级标记 | `CustomerProfileClient.java:20-52` |
| `POST /internal/fulfillment/status/batch` | HTTP | v1 | `includeFulfillment=true` | 300 ms 超时后状态为 `UNKNOWN` | `FulfillmentClient.java:26-67`、`http-client.yaml:12-23` |
| `POST /internal/risk/orders/query` | HTTP | v1 | 本地风险缓存 miss 且允许实时补查 | 熔断开启时仅返回缓存结果 | `OrderRiskClient.java:30-79` |

### 8.5 文件与对象存储

| 协议或存储 | 逻辑位置 | 文件格式 | 触发方 | 接收方 | 证据 |
|------------|----------|----------|--------|--------|------|
| 对象存储 | `exports/orders/{tenantId}/{taskId}.xlsx` | XLSX | `API-order-export` 异步任务 | 管理页面下载 | `OrderExportService.java:40-88` |

> 文件导出属于 `API-order-export`，不是本查询接口的直接副作用；在此记录是为了说明同一页面的关联能力边界。

### 8.6 定时任务与批处理

| 任务 | 触发方式 | 并发与锁 | 重试与补偿 | 证据 |
|------|----------|----------|------------|------|
| `OrderIndexReconcileJob` | 每日 02:30 | Redis 锁，单租户串行 | 失败分片写入重建 Stream | `OrderIndexReconcileJob.java:33-81`、`scheduler.yaml:8-15` |
| `OrderRiskCacheRefreshJob` | 每 10 分钟 | 单实例本地任务 | 下次周期重试 | `OrderRiskCacheRefreshJob.java:20-57` |
| `OrderQueryCacheCleanupJob` | 每小时 | 各实例独立执行 | 无，Redis TTL 为主要清理机制 | `OrderQueryCacheCleanupJob.java:18-42` |

### 8.7 其他下游与运行时开关

- `order.query.full-text-enabled` 控制全文搜索分支；关闭时包含全文条件的请求返回明确能力未启用错误，不退化为模糊 SQL。
- `order.query.enrichment-enabled` 控制客户、履约和风险补充；关闭时仍返回订单主数据。
- `ORDER_QUERY_REGION_ROUTE:{tenantId}` 只影响查询落点，不改变 API 分类、路径或权限。
- 未发现 FTP、SFTP 或 WebSocket 参与本接口主链路。

## 九、数据源与副作用分析

### 9.1 主路径数据源

- 权威订单数据来自用户 DDL 和 Mapper 指向的 `order_db.t_order`、`t_order_item`、`t_order_payment`。
- Redis 只缓存精确查询结果和路由开关，不是订单权威数据源。
- Elasticsearch 只负责全文搜索召回，不作为响应字段的最终依据。
- Caffeine 保存风险摘要和字典数据，均可由消息或配置重新构建。

### 9.2 实时查询与补充路径

| 调用 | 实现 | 验证结论 | 返回字段 | 证据 |
|------|------|----------|----------|------|
| `OrderQueryMapper.selectPage` | MyBatis XML | 直接查询订单主表并分页 | 订单 ID、状态、金额、客户、时间 | `OrderQueryMapper.xml:18-96` |
| `OrderQueryMapper.selectItemSummary` | MyBatis XML | 根据订单 ID 批量汇总订单项 | 商品摘要、商品数量 | `OrderQueryMapper.xml:98-131` |
| `OrderSearchRepository.searchIds` | Elasticsearch Client | 全文条件下召回订单 ID | orderId、score | `OrderSearchRepository.java:52-87` |
| `CustomerProfileClient.getProfiles` | Dubbo Client | 条件补充，非订单权威数据 | customerLevel、tags | `CustomerProfileClient.java:20-52` |
| `FulfillmentClient.getStatusBatch` | HTTP Client | 条件补充，可降级 | fulfillmentStatus | `FulfillmentClient.java:26-67` |
| `OrderRiskCache.getBatch` | Caffeine | 本地缓存优先，允许 HTTP 补查 | riskLevel、riskTags | `OrderRiskCache.java:42-66` |

### 9.3 写入、副作用和一致性

- 订单查询本身不写业务数据库。
- Redis 查询缓存是可丢失派生数据，数据库提交后由订单变更事件删除相关缓存。
- 查询审计事件是可选副作用，发送失败不会回滚查询，也不会向用户返回成功审计的错误结论。
- 远端单元路由失败时不自动查询本地数据库，避免跨单元数据不一致或越权读取。
- 下游补充失败时保留订单主数据，并通过降级字段表达缺口。

### 9.4 分层结论

- **订单权威数据**：MySQL 订单表，由 DDL、Mapper 和数据源配置共同证明。
- **全文召回数据**：Elasticsearch 索引，只用于候选 ID。
- **查询与路由缓存**：Redis，负责短期结果缓存、开关和单元路由。
- **本地派生数据**：Caffeine 风险摘要与字典，依赖 Kafka 和定时任务刷新。
- **跨服务补充**：客户资料使用 Dubbo，履约和风险实时补查使用 HTTP。
- **异步副作用**：Kafka 查询审计；不影响主链路成功与否。
- **文件能力边界**：XLSX 对象存储属于订单导出接口，不属于分页查询主链路。

## 十、关键证据引用

| 引用 | 文件或资料位置 |
|------|----------------|
| 用户对外能力清单 | `cadence/knowledge-base/user-input/api-scope.md`，未登记本接口 |
| 页面 API 调用 | `admin-web/src/api/order.ts:18-26` |
| REST 入口定义 | `order-query-service/src/main/java/com/example/order/interfaces/rest/OrderQueryController.java:28-45` |
| 应用服务 | `order-query-service/src/main/java/com/example/order/application/OrderQueryApplicationService.java:45-145` |
| 多单元路由 | `order-query-service/src/main/java/com/example/order/infrastructure/routing/OrderRegionRouter.java:34-61` |
| 领域查询 | `order-query-domain/src/main/java/com/example/order/domain/query/OrderQueryService.java:22-58` |
| 仓储分支 | `order-query-infrastructure/src/main/java/com/example/order/infrastructure/repository/OrderQueryRepository.java:42-98` |
| MyBatis SQL | `order-query-infrastructure/src/main/resources/mapper/OrderQueryMapper.xml:18-131` |
| 用户 DDL | `inputs/ddl/order.sql`、`inputs/ddl/order_item.sql`、`inputs/ddl/order_payment.sql` |
| Redis 缓存 | `order-query-infrastructure/src/main/java/com/example/order/infrastructure/cache/OrderQueryCache.java:25-58` |
| 搜索索引 | `order-query-infrastructure/src/main/java/com/example/order/infrastructure/search/OrderSearchRepository.java:30-106` |
| Kafka 消费 | `order-query-infrastructure/src/main/java/com/example/order/infrastructure/messaging/OrderChangedConsumer.java:24-79` |
| 查询审计生产 | `order-query-infrastructure/src/main/java/com/example/order/infrastructure/messaging/OrderQueryAuditPublisher.java:28-55` |
| Dubbo 配置 | `order-query-service/src/main/resources/dubbo-consumer.yaml:8-17` |
| HTTP Client 配置 | `order-query-service/src/main/resources/http-client.yaml:12-23` |
| 定时任务 | `order-query-service/src/main/java/com/example/order/jobs/OrderIndexReconcileJob.java:33-81` |
| 网关路由 | `gateway/src/main/resources/routes/order-query.yaml:4-12` |

## 十一、请求、响应或载荷示例

详见 `demo_参数与报文.md` 第三至第五节。
