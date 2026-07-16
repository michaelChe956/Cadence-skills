# API-partner-order-query 合作方订单查询接口

> **能力 ID**：`API-partner-order-query`
> **分类**：对外
> **能力类型**：REST
> **数据来源**：用户提供的对外能力清单、DDL 与虚构示例工程代码
> **梳理日期**：2026-07-16
> **参数与报文**：见同目录 `demo_参数与报文.md`
>
> **案例声明**：本文所有组织、域名、地址、包名、库表、Topic、Key、配置和代码路径均为虚构示例，仅用于展示完整的对外能力分析格式。实际执行必须以用户输入文档、DDL 和工程代码为准。

## 一、能力基础信息

| 项目 | 值 |
|------|----|
| 能力名称 | 合作方订单查询接口 |
| API 名称或逻辑标识 | `partnerOrderQuery` |
| 分类 | 对外 |
| 能力类型 | REST |
| 协议与方法 | HTTPS POST |
| 路径或逻辑地址 | `/openapi/order-center/partnerOrderQuery/v1` |
| 数据格式 | JSON |
| 是否需授权 | 是，合作方身份、签名、时间窗、Nonce 和能力权限 |
| 版本 | v1 |
| 调用方或生产者 | 已签约合作方系统 |
| 落地方或消费者 | 开放能力网关、`order-openapi-service` |
| 生命周期状态 | 已声明、已实现、已装配、已暴露 |
| 入参压缩 | 否 |
| 出参压缩 | 否 |

### 调用入口

| 环境 | URL | 证据状态 |
|------|-----|----------|
| 生产 | `https://open.example.invalid/openapi/order-center/partnerOrderQuery/v1` | 用户接口资料中的脱敏逻辑地址 |
| 联调 | `https://sandbox-open.example.invalid/openapi/order-center/partnerOrderQuery/v1` | 用户接口资料中的脱敏逻辑地址 |
| 内部回归 | `http://localhost:9080/openapi/order-center/partnerOrderQuery/v1` | 网关回归配置默认值 |

> `.invalid` 是保留的无效顶级域名，示例地址不可用于真实访问。

## 二、业务需求描述

- 已签约合作方按照外部订单号、平台订单号、订单状态和创建时间查询其授权范围内的订单。
- 开放网关负责合作方身份识别、签名校验、防重放、限流和能力授权。
- 网关根据能力编码将 HTTP 报文转换为 RPC 请求，调用订单开放能力 Provider。
- Provider 根据合作方映射关系过滤数据，不允许合作方通过请求参数扩大租户或订单范围。
- 订单主数据来自订单库；全文搜索只负责候选订单召回，最终响应字段回查数据库。
- 主查询链路只读；请求审计通过消息异步记录，不影响订单查询事务。

## 三、输入参数

详见 `demo_参数与报文.md` 第一节。

## 四、输出参数

详见 `demo_参数与报文.md` 第二节。

## 五、代码实现定位

### 5.1 用户清单与代码映射

**结论：`API-partner-order-query` 已登记在用户提供的对外能力清单中，因此始终归类为对外能力；代码只用于核实实现、装配、网关发布和运行状态，不能因实现暂时无法定位而改判为对内。**

**对外能力清单映射**：

| 字段 | 值 | 证据 |
|------|----|------|
| 稳定 ID | `API-partner-order-query` | `cadence/knowledge-base/user-input/api-scope.md` |
| 能力编码 | `json_orderCenter_partnerOrderQuery` | 用户提供的接口注册清单 |
| 接口名称 | 合作方订单查询接口 | 用户提供的接口注册清单 |
| API 名称 | `partnerOrderQuery` | 用户提供的接口注册清单 |
| 实现接口 | `PartnerOrderQueryFacade` | 接口注册清单的实现映射字段 |
| 实现方法 | `queryOrders` | 接口注册清单的实现映射字段 |
| 能力集 | `order-openapi` | 接口注册清单的能力集字段 |

| 来源 | 标识 | 结论 | 证据 |
|------|------|------|------|
| 用户对外能力清单 | `API-partner-order-query` | 对外分类的权威依据 | `cadence/knowledge-base/user-input/api-scope.md` |
| 开放网关注册 | `json_orderCenter_partnerOrderQuery` | 能力已声明、已发布 | `open-gateway/config/order-center-apis.yaml:8-26` |
| RPC 接口 | `PartnerOrderQueryFacade#queryOrders` | 网关协议转换后的目标接口 | `order-openapi-api/src/main/java/com/example/order/openapi/PartnerOrderQueryFacade.java:12-21` |
| RPC Provider | `PartnerOrderQueryFacadeImpl#queryOrders` | 能力实现存在 | `order-openapi-service/src/main/java/com/example/order/openapi/impl/PartnerOrderQueryFacadeImpl.java:28-57` |
| Provider 装配 | `@DubboService` 与应用扫描 | 已装配、已注册 | `PartnerOrderQueryFacadeImpl.java:24-27`、`OrderOpenApiApplication.java:10-15` |

**网关路由机制**：开放网关接收 `POST /openapi/order-center/partnerOrderQuery/v1`，根据能力编码 `json_orderCenter_partnerOrderQuery` 完成合作方鉴权、报文解包和 HTTP → Dubbo 协议转换，再调用 `PartnerOrderQueryFacade#queryOrders`。URL 中的 API 名称只用于定位网关注册项，不能仅凭名称猜测实现类。

**容易混淆的入口**：

- `OrderQueryController#queryPage()` 是管理页面使用的对内 REST `API-order-page`，不是本对外能力。
- `OrderQueryFacade#queryPage()` 是内部服务间 RPC，未登记在对外清单时仍属于对内能力。
- `PartnerOrderExportFacade#exportOrders()` 对应独立的合作方订单导出能力，不是本查询接口。

### 5.2 实现清单

| 层级 | 符号 | 文件路径 | 状态 | 说明 |
|------|------|----------|------|------|
| 对外注册 | `json_orderCenter_partnerOrderQuery` | `open-gateway/config/order-center-apis.yaml` | 已声明、已暴露 | 路径、版本、签名和目标 Provider 映射 |
| RPC 接口 | `PartnerOrderQueryFacade#queryOrders` | `order-openapi-api/src/main/java/com/example/order/openapi/PartnerOrderQueryFacade.java` | 已声明 | 网关协议转换后的调用契约 |
| RPC Provider | `PartnerOrderQueryFacadeImpl#queryOrders` | `order-openapi-service/src/main/java/com/example/order/openapi/impl/PartnerOrderQueryFacadeImpl.java` | 已实现、已装配 | 请求校验、区域路由和响应组装 |
| 多区域桥接 | `PartnerOrderRegionBridge#queryRemote` | `order-openapi-service/src/main/java/com/example/order/openapi/routing/PartnerOrderRegionBridge.java` | 条件启用 | 跨区域调用订单开放能力 |
| 开放业务服务 | `PartnerOrderQueryService#query` | `order-openapi-domain/src/main/java/com/example/order/openapi/domain/PartnerOrderQueryService.java` | 已实现 | 合作方范围校验和订单查询 |
| 合作方权限 | `PartnerPermissionService#requireOrderQuery` | `order-openapi-service/src/main/java/com/example/order/openapi/security/PartnerPermissionService.java` | 已实现 | 核对合作方、能力和数据范围 |
| 数据访问 | `PartnerOrderRepository#findPage` | `order-openapi-infrastructure/src/main/java/com/example/order/openapi/repository/PartnerOrderRepository.java` | 已实现 | 合作方映射、订单、订单项查询 |
| MyBatis Mapper | `PartnerOrderQueryMapper#selectPage` | `order-openapi-infrastructure/src/main/resources/mapper/PartnerOrderQueryMapper.xml` | 已实现 | 按授权合作方和订单条件查询 |
| 请求审计 | `PartnerApiAuditPublisher#publish` | `order-openapi-infrastructure/src/main/java/com/example/order/openapi/messaging/PartnerApiAuditPublisher.java` | 条件启用 | 异步发送开放 API 审计事件 |

## 六、调用链路

### 6.1 调用树

```text
外部合作方系统
└─ POST /openapi/order-center/partnerOrderQuery/v1
   └─ 开放能力网关
      ├─ PartnerIdentityFilter：合作方身份与能力权限
      ├─ SignatureVerifyFilter：签名、时间窗、Nonce 防重放
      ├─ PartnerRateLimitFilter：合作方 + 能力维度限流
      └─ HTTP → Dubbo 协议转换
         └─ PartnerOrderQueryFacade.queryOrders(request)
            └─ PartnerOrderQueryFacadeImpl.queryOrders(request)
               ├─ PartnerPermissionService.requireOrderQuery(partnerCode)
               │  ├─ Redis PARTNER_API_PERMISSION:{partnerCode}
               │  └─ miss → partner_db.t_partner_api_permission
               ├─ PartnerOrderRegionRouter.route(partnerCode, regionCode)
               │  ├─ [远端区域] PartnerOrderRegionBridge.queryRemote(request) → Dubbo
               │  └─ [本地区域] PartnerOrderQueryService.query(criteria)
               │     └─ PartnerOrderRepository.findPage(criteria)
               │        ├─ Redis PARTNER_ORDER_QUERY:{partnerCode}:{digest}
               │        ├─ [精确查询] PartnerOrderQueryMapper.selectPage(criteria)
               │        │  ├─ order_db.t_partner_order_mapping
               │        │  ├─ order_db.t_order
               │        │  └─ order_db.t_order_item
               │        └─ [全文条件] Elasticsearch partner_order_index
               │           └─ 候选 orderId → Mapper 回查数据库
               ├─ PartnerOrderAssembler.maskAndConvert(page)
               └─ PartnerApiAuditPublisher.publish(event) → Kafka
```

### 6.2 分支与触发条件

| 条件 | 路径 | 结果 | 证据 |
|------|------|------|------|
| 对外清单有该能力，但代码未定位 | 保留对外分类，状态标记待确认 | 不自动改判对内 | `api-scope.md` 与 API 分类规则 |
| 签名无效、时间戳过期或 Nonce 重复 | 网关直接拒绝 | 不进入 Provider | `SignatureVerifyFilter.java:36-92` |
| 合作方未授权 `API-partner-order-query` | 网关或 Provider 权限校验拒绝 | 返回 `PARTNER_PERMISSION_DENIED` | `PartnerPermissionService.java:30-65` |
| `PARTNER_ORDER_REGION:{partnerCode}` 指向远端且全局开关开启 | Provider → RegionBridge → 远端 Dubbo | 在授权区域查询 | `PartnerOrderRegionRouter.java:28-61` |
| 区域开关关闭或目标为本地 | Provider → PartnerOrderQueryService | 本地查询 | `PartnerOrderRegionRouter.java:48-57` |
| `searchMode=FULL_TEXT` 且合作方已开通搜索能力 | Repository → Elasticsearch → 数据库回查 | 搜索召回后返回权威数据 | `PartnerOrderRepository.java:76-105` |
| Redis 查询缓存命中 | Repository → Redis | 返回脱敏后的合作方响应模型 | `PartnerOrderQueryCache.java:25-47` |
| Redis 查询缓存未命中 | Repository → Mapper → Redis | 查库并回填短期缓存 | `PartnerOrderRepository.java:48-73` |
| 审计开关开启 | Provider → Kafka | 异步记录调用结果和耗时 | `PartnerOrderQueryFacadeImpl.java:49-55` |

### 6.3 逐层调用明细

#### 第 1 层：开放能力网关

- 注册文件：`open-gateway/config/order-center-apis.yaml:8-26`
- 职责：路径匹配、版本校验、合作方认证、签名、防重放、限流、报文解包和协议转换。
- 映射目标：`com.example.order.openapi.PartnerOrderQueryFacade#queryOrders`。
- 网关发布证据只证明能力已配置；仍需结合实际路由装载和 Provider 注册判断当前环境是否可用。

#### 第 2 层：RPC Provider 与区域路由

- 类与方法：`PartnerOrderQueryFacadeImpl#queryOrders(PartnerOrderQueryRequest)`
- 文件：`order-openapi-service/src/main/java/com/example/order/openapi/impl/PartnerOrderQueryFacadeImpl.java:28-57`
- 职责：二次参数校验、合作方数据权限、区域路由、领域调用、脱敏和统一响应。

```java
@DubboService(version = "1.0.0", group = "order-openapi")
public PartnerOrderQueryResponse queryOrders(PartnerOrderQueryRequest request) {
    partnerPermissionService.requireOrderQuery(request.getPartnerCode());
    RegionTarget target = partnerOrderRegionRouter.route(
            request.getPartnerCode(), request.getRegionCode());
    return target.isRemote()
            ? partnerOrderRegionBridge.queryRemote(target, request)
            : partnerOrderQueryService.query(request.toCriteria());
}
```

#### 第 3 层：开放业务服务

- 类与方法：`PartnerOrderQueryService#query(PartnerOrderCriteria)`
- 文件：`order-openapi-domain/src/main/java/com/example/order/openapi/domain/PartnerOrderQueryService.java:31-88`
- 职责：校验合作方查询跨度、分页窗口和允许字段；将外部订单号映射为内部订单范围；调用仓储。
- 数据边界：查询条件必须包含由服务端注入的 `partnerCode`，不能信任请求体中的租户或商户字段。

#### 第 4 层：仓储、搜索与响应组装

- `PartnerOrderRepository#findPage` 选择精确查询或全文召回路径。
- `PartnerOrderQueryMapper#selectPage` 先关联 `t_partner_order_mapping`，再读取订单和订单项。
- Elasticsearch 只返回候选订单 ID；最终金额、状态和时间均回查 MySQL。
- `PartnerOrderAssembler` 将内部状态转换为对外枚举，移除内部备注、风控明细和未授权字段。

## 七、数据库与表

本案例的数据库结论只使用用户提供的 DDL、Mapper SQL、Entity 和数据源配置，不连接数据库，也不查询在线元数据。

| 数据库或 Schema | 表名 | 用途 | 操作 | Mapper/DAO/SQL | 证据 |
|------------------|------|------|------|----------------|------|
| `partner_db` | `t_partner_api_permission` | 合作方能力授权和数据范围 | R | `PartnerPermissionMapper.selectPermission` | `inputs/ddl/partner_api_permission.sql`、`PartnerPermissionMapper.xml:12-48` |
| `order_db` | `t_partner_order_mapping` | 外部订单号、合作方与内部订单映射 | R | `PartnerOrderQueryMapper.selectPage` | `inputs/ddl/partner_order_mapping.sql`、`PartnerOrderQueryMapper.xml:18-97` |
| `order_db` | `t_order` | 订单主数据、状态、金额和时间 | R | `PartnerOrderQueryMapper.selectPage/selectByIds` | `inputs/ddl/order.sql`、`PartnerOrderQueryMapper.xml:18-132` |
| `order_db` | `t_order_item` | 对外允许展示的商品摘要 | R | `PartnerOrderItemMapper.selectByOrderIds` | `inputs/ddl/order_item.sql`、`PartnerOrderItemMapper.xml:10-45` |
| `order_db` | `t_order_payment` | 对外支付状态摘要 | 条件 R | `PartnerOrderPaymentMapper.selectByOrderIds` | `inputs/ddl/order_payment.sql`、`PartnerOrderPaymentMapper.xml:12-39` |
| 待确认 | `t_partner_api_call_log` | 审计落库候选 | 主链路未直写 | 当前工程未发现 Mapper | 用户 DDL 存在，但审计消费者不在当前工程范围 |

> 不能仅因 DDL 中存在 `t_partner_api_call_log` 就认定本接口同步写表；当前证据只能证明 Kafka 审计事件已生产。

## 八、中间件使用明细

### 8.1 缓存与队列

| 类型 | 名称或 Key 模式 | 读写方向 | TTL | 触发时机 | 证据 |
|------|-----------------|----------|-----|----------|------|
| Redis KV | `PARTNER_API_PERMISSION:{partnerCode}` | 读/写 | 300 秒 | 网关和 Provider 核对能力授权 | `PartnerPermissionCache.java:22-58` |
| Redis KV | `PARTNER_API_NONCE:{partnerCode}:{nonce}` | 写 | 300 秒 | 网关防重放；写入失败时拒绝请求 | `NonceReplayGuard.java:26-61` |
| Redis KV | `PARTNER_ORDER_REGION:{partnerCode}` | 读 | 无固定 TTL | 决定订单查询区域 | `PartnerOrderRegionRouter.java:28-45` |
| Redis KV | `PARTNER_ORDER_QUERY:{partnerCode}:{criteriaDigest}` | 读/写 | 60 秒 | 缓存脱敏后的对外查询结果 | `PartnerOrderQueryCache.java:25-62` |
| Redis Stream | `PARTNER_ORDER_INDEX_REBUILD` | 消费 | 按 Stream 策略 | 搜索索引异常时触发分区重建 | `PartnerOrderIndexRebuildConsumer.java:30-75` |

### 8.2 消息

| Topic/Queue/Group | 方向 | 消息模型 | 重试与幂等 | 证据 |
|-------------------|------|----------|------------|------|
| `partner.api.audit.v1` | 生产 | `PartnerApiAuditEvent` | 主链路不重试；发送失败记录指标 | `PartnerApiAuditPublisher.java:28-59` |
| `order.changed.v1` / `partner-order-cache-group` | 消费 | `OrderChangedEvent` | `eventId` 去重，删除合作方查询缓存 | `PartnerOrderChangedConsumer.java:24-71` |
| `partner.permission.changed.v1` / `partner-permission-cache-group` | 消费 | `PartnerPermissionChangedEvent` | 按版本覆盖权限缓存 | `PartnerPermissionChangedConsumer.java:20-58` |
| `partner.order.index.dlq` | 消费 | `PartnerOrderIndexFailedEvent` | 人工确认后重新投递 | `PartnerOrderIndexDlqConsumer.java:18-46` |

### 8.3 搜索与本地缓存

| 组件 | 数据结构或索引 | 初始化/加载方式 | 刷新机制 | 证据 |
|------|----------------|---------------|----------|------|
| Elasticsearch | `partner_order_index_v1`，别名 `partner_order_index` | 离线全量构建 | 订单事件增量更新；每日校准任务补偿 | `PartnerOrderSearchRepository.java:30-112` |
| Caffeine | `partnerCapabilityCache<partnerCode, CapabilitySet>` | 首次请求加载 | 权限变更事件和 5 分钟过期刷新 | `PartnerCapabilityLocalCache.java:18-63` |
| Caffeine | `externalStatusDictionary<internalStatus, externalStatus>` | 启动时加载配置 | 配置变更事件整体刷新 | `PartnerOrderStatusDictionary.java:20-55` |

### 8.4 RPC 与下游 HTTP

| 服务 | 协议 | 版本或分组 | 触发条件 | 失败处理 | 证据 |
|------|------|------------|----------|----------|------|
| `PartnerOrderQueryFacade#queryOrders` | Dubbo Provider | `1.0.0` / `order-openapi` | 开放网关协议转换 | Provider 异常转换为对外错误码 | `PartnerOrderQueryFacadeImpl.java:24-57` |
| `PartnerOrderRegionFacade#queryOrders` | Dubbo Consumer | `1.0.0` / `order-openapi-region` | 合作方路由到远端区域 | 超时返回 `REGION_QUERY_TIMEOUT`，不回查本地库 | `PartnerOrderRegionBridge.java:32-68` |
| `CustomerTokenFacade#resolveBatch` | Dubbo Consumer | `1.1.0` / `customer-token` | 请求包含客户 Token | 无法解析的 Token 不参与查询 | `CustomerTokenClient.java:22-61` |
| `POST /internal/fulfillment/partner-status/batch` | HTTP | v1 | 合作方开通履约状态字段 | 超时后字段为空并返回降级标记 | `PartnerFulfillmentClient.java:25-69` |

### 8.5 文件与对象存储

本查询接口不直接上传、下载或生成文件。合作方批量导出属于独立能力 `API-partner-order-export`，不得合并到本接口副作用中。

### 8.6 定时任务与批处理

| 任务 | 触发方式 | 并发与锁 | 重试与补偿 | 证据 |
|------|----------|----------|------------|------|
| `PartnerOrderIndexReconcileJob` | 每日 03:00 | Redis 分布式锁，按合作方分片 | 失败分片进入重建 Stream | `PartnerOrderIndexReconcileJob.java:30-84` |
| `PartnerPermissionCacheRefreshJob` | 每 5 分钟 | 单实例本地任务 | 下次周期重试 | `PartnerPermissionCacheRefreshJob.java:18-49` |
| `PartnerApiRegistrationCheckJob` | 每小时 | 单实例执行 | 发现网关注册与 Provider 不一致时告警 | `PartnerApiRegistrationCheckJob.java:22-67` |

### 8.7 网关安全与运行时限制

- 合作方密钥只通过安全配置引用，文档不得输出密钥、完整签名原文或未脱敏连接信息。
- 网关限流维度为 `partnerCode + capabilityCode`，不能把全局限流误写成单合作方配额。
- Provider 二次校验合作方数据范围，不能只依赖网关鉴权作为数据权限证明。
- 未发现 FTP、SFTP、WebSocket 或浏览器页面直接参与本对外能力主链路。

## 九、数据源与副作用分析

### 9.1 主路径数据源

- 对外分类的权威来源是用户 `api-scope.md`，不是 Controller、Provider 或 URL 命名。
- 合作方能力权限来自 `partner_db.t_partner_api_permission`，Redis 和 Caffeine 只提供缓存。
- 合作方订单范围由 `order_db.t_partner_order_mapping` 与服务端注入的 `partnerCode` 共同约束。
- 订单权威字段来自 `t_order`、`t_order_item` 和条件使用的 `t_order_payment`。
- Elasticsearch 只负责全文召回，最终响应字段必须回查数据库并经过对外脱敏转换。

### 9.2 实时查询与补充路径

| 调用 | 实现 | 验证结论 | 返回字段 | 证据 |
|------|------|----------|----------|------|
| `PartnerPermissionService.requireOrderQuery` | Redis → MyBatis | 核对合作方能力和数据范围 | capability、regionScope、fieldScope | `PartnerPermissionService.java:30-65` |
| `PartnerOrderQueryMapper.selectPage` | MyBatis XML | 按合作方映射关联订单主表 | 订单号、状态、金额、时间 | `PartnerOrderQueryMapper.xml:18-97` |
| `PartnerOrderItemMapper.selectByOrderIds` | MyBatis XML | 批量查询允许对外展示的商品摘要 | productCode、productName、quantity | `PartnerOrderItemMapper.xml:10-45` |
| `PartnerOrderSearchRepository.searchIds` | Elasticsearch Client | 全文条件下召回候选订单 ID | orderId、score | `PartnerOrderSearchRepository.java:52-92` |
| `CustomerTokenClient.resolveBatch` | Dubbo Client | 将合作方客户 Token 解析为授权客户 ID | customerId | `CustomerTokenClient.java:22-61` |
| `PartnerFulfillmentClient.getStatusBatch` | HTTP Client | 条件补充对外履约状态 | fulfillmentStatus | `PartnerFulfillmentClient.java:25-69` |

### 9.3 写入、副作用和一致性

- 订单查询不写业务数据库。
- Redis Nonce 是防重放状态，写入失败时必须拒绝请求，不能放行后补。
- 查询结果缓存是可丢失派生数据，由订单变更消息删除或 TTL 自动过期。
- 审计事件是异步副作用；事件发送失败不改变查询结果，但必须记录指标和告警。
- 远端区域查询失败时不自动回查本地库，避免越权和跨区域数据不一致。
- 下游履约补充失败时保留订单主数据，并通过响应降级字段表达缺口。

### 9.4 分层结论

- **分类证据**：用户对外能力清单，代码不得覆盖其对外属性。
- **入口证据**：开放网关注册、路径、版本、签名策略和 Provider 映射。
- **实现证据**：Dubbo 接口、Provider、装配和区域路由。
- **权威业务数据**：合作方映射和订单 MySQL 表。
- **派生查询数据**：Redis 查询缓存、Elasticsearch 索引和 Caffeine 字典。
- **异步副作用**：Kafka 开放 API 审计及缓存刷新事件。
- **页面边界**：管理页面使用的 `API-order-page` 是独立对内 REST，不因业务名称相似归入本能力。

## 十、关键证据引用

| 引用 | 文件或资料位置 |
|------|----------------|
| 用户对外能力清单 | `cadence/knowledge-base/user-input/api-scope.md`，登记 `API-partner-order-query` |
| 开放网关注册 | `open-gateway/config/order-center-apis.yaml:8-26` |
| RPC 接口定义 | `order-openapi-api/src/main/java/com/example/order/openapi/PartnerOrderQueryFacade.java:12-21` |
| RPC Provider | `order-openapi-service/src/main/java/com/example/order/openapi/impl/PartnerOrderQueryFacadeImpl.java:24-57` |
| 合作方权限 | `order-openapi-service/src/main/java/com/example/order/openapi/security/PartnerPermissionService.java:30-65` |
| 区域路由 | `order-openapi-service/src/main/java/com/example/order/openapi/routing/PartnerOrderRegionRouter.java:28-61` |
| 开放业务服务 | `order-openapi-domain/src/main/java/com/example/order/openapi/domain/PartnerOrderQueryService.java:31-88` |
| 仓储分支 | `order-openapi-infrastructure/src/main/java/com/example/order/openapi/repository/PartnerOrderRepository.java:48-105` |
| MyBatis SQL | `order-openapi-infrastructure/src/main/resources/mapper/PartnerOrderQueryMapper.xml:18-132` |
| 用户 DDL | `inputs/ddl/partner_api_permission.sql`、`inputs/ddl/partner_order_mapping.sql`、`inputs/ddl/order.sql` |
| Redis 与防重放 | `PartnerPermissionCache.java:22-58`、`NonceReplayGuard.java:26-61` |
| Elasticsearch | `PartnerOrderSearchRepository.java:30-112` |
| Kafka 审计 | `PartnerApiAuditPublisher.java:28-59` |
| 区域 RPC 配置 | `order-openapi-service/src/main/resources/dubbo-consumer.yaml:8-18` |
| 履约 HTTP 配置 | `order-openapi-service/src/main/resources/http-client.yaml:12-24` |

## 十一、请求、响应或载荷示例

详见 `demo_参数与报文.md` 第三至第五节。
