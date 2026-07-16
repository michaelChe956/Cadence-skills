# API-order-page 订单分页查询接口（对内 REST） - 参数与报文

> **主文件**：`API-order-page_订单分页查询_orderPageQuery.md`
> **能力 ID**：`API-order-page`
> **HTTP 方法与路径**：`POST /api/admin/orders/query`
> **数据来源**：用户接口资料、请求响应模型和虚构示例工程代码
>
> **案例声明**：本文字段、取值和报文均为虚构示例，只展示生成格式。实际字段必须来自用户资料或代码证据；资料未提供的字段应填写“未提供”，不得套用本案例。

## 一、输入参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| `traceId` | 请求头 | 否 | String | 1~64 | 调用链标识；未传时由网关生成 | `gateway-tracing.md`、`TraceHeaderFilter.java:21-46` |
| `tenantId` | 请求头 | 是 | String | 1~32 | 当前租户标识，必须与登录态授权范围一致 | `OrderQueryController.java:31-38` |
| `operatorId` | 请求头 | 否 | String | 1~64 | 操作人标识；优先从登录态读取 | `CurrentOperatorArgumentResolver.java:18-52` |
| `pageNo` | 根节点 | 是 | Integer | ≥1 | 页码，从 1 开始 | `OrderPageQueryRequest.java:18-20` |
| `pageSize` | 根节点 | 是 | Integer | 1~200 | 每页数量 | `OrderPageQueryRequest.java:22-25` |
| `filters` | 根节点 | 否 | Object | - | 订单筛选条件 | `OrderPageQueryRequest.java:27` |
| `orderStatus` | `filters` | 否 | Array&lt;String&gt; | 最多 10 项 | 订单状态集合，如 `CREATED`、`PAID`、`SHIPPED`、`CLOSED` | `OrderStatus.java:8-19` |
| `createdFrom` | `filters` | 否 | String | ISO 8601 | 创建时间起点，含边界 | `OrderQueryCriteria.java:24` |
| `createdTo` | `filters` | 否 | String | ISO 8601 | 创建时间终点，不含边界；必须晚于 `createdFrom` | `OrderQueryCriteria.java:25` |
| `buyerKeyword` | `filters` | 否 | String | 1~64 | 买家 ID、脱敏手机号或昵称关键字 | `OrderPageQueryRequest.java:36` |
| `productKeyword` | `filters` | 否 | String | 1~128 | 商品名称或 SKU 关键字 | `OrderPageQueryRequest.java:38` |
| `minAmount` | `filters` | 否 | Decimal | ≥0，最多 2 位小数 | 最小订单金额，单位为元 | `OrderPageQueryRequest.java:40` |
| `maxAmount` | `filters` | 否 | Decimal | ≥0，最多 2 位小数 | 最大订单金额，必须大于等于 `minAmount` | `OrderPageQueryRequest.java:42` |
| `searchMode` | 根节点 | 是 | String | `EXACT`/`FULL_TEXT` | 精确筛选或全文检索 | `SearchMode.java:5-8` |
| `sorts` | 根节点 | 否 | Array&lt;Object&gt; | 最多 3 项 | 排序字段列表，按数组顺序组合 | `OrderPageQueryRequest.java:47` |
| `field` | `sorts[]` | 是 | String | 枚举 | 允许 `createdAt`、`totalAmount`、`orderStatus` | `OrderSortField.java:6-12` |
| `direction` | `sorts[]` | 是 | String | `ASC`/`DESC` | 排序方向 | `SortDirection.java:5-8` |
| `include` | 根节点 | 否 | Object | - | 可选补充信息开关 | `OrderPageQueryRequest.java:50` |
| `customerProfile` | `include` | 否 | Boolean | 默认 `false` | 是否补充客户等级与标签 | `OrderPageQueryRequest.java:53` |
| `fulfillment` | `include` | 否 | Boolean | 默认 `false` | 是否补充履约状态 | `OrderPageQueryRequest.java:55` |
| `riskSummary` | `include` | 否 | Boolean | 默认 `true` | 是否返回风险摘要 | `OrderPageQueryRequest.java:57` |

### 条件约束

- `searchMode=FULL_TEXT` 时，`buyerKeyword` 或 `productKeyword` 至少提供一个。
- `createdFrom` 与 `createdTo` 同时提供时，时间跨度不得超过 180 天。
- `pageSize` 最大为 200；接口不会静默截断非法值。
- `tenantId` 由请求头与登录态共同校验，不接受请求体覆盖。
- 排序字段只能使用白名单枚举，不能直接传数据库字段名。

## 二、输出参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| `code` | 根节点 | 是 | String | 1~32 | 业务结果码；成功为 `SUCCESS` | `ApiResponse.java:12-18` |
| `message` | 根节点 | 是 | String | 0~256 | 结果描述 | `ApiResponse.java:20` |
| `traceId` | 根节点 | 是 | String | 1~64 | 调用链标识 | `ApiResponseAdvice.java:30-44` |
| `data` | 根节点 | 条件 | Object | - | 成功时的分页数据 | `PageResult.java:10-26` |
| `pageNo` | `data` | 是 | Integer | ≥1 | 当前页码 | `PageResult.java:12` |
| `pageSize` | `data` | 是 | Integer | 1~200 | 当前分页大小 | `PageResult.java:14` |
| `total` | `data` | 是 | Long | ≥0 | 满足条件的总记录数 | `PageResult.java:16` |
| `hasNext` | `data` | 是 | Boolean | - | 是否存在下一页 | `PageResult.java:18` |
| `list` | `data` | 是 | Array&lt;Object&gt; | 可为空数组 | 订单摘要列表 | `OrderSummaryResponse.java:14-71` |
| `orderId` | `list[]` | 是 | String | 1~40 | 订单唯一标识 | `OrderSummaryResponse.java:16` |
| `orderNo` | `list[]` | 是 | String | 1~40 | 对用户展示的订单编号 | `OrderSummaryResponse.java:18` |
| `orderStatus` | `list[]` | 是 | String | 枚举 | 订单状态 | `OrderSummaryResponse.java:20` |
| `buyer` | `list[]` | 是 | Object | - | 买家摘要 | `OrderSummaryResponse.java:22` |
| `customerId` | `buyer` | 是 | String | 1~40 | 客户标识 | `BuyerSummaryResponse.java:12` |
| `displayName` | `buyer` | 否 | String | 0~64 | 脱敏展示名称 | `BuyerSummaryResponse.java:14` |
| `maskedMobile` | `buyer` | 否 | String | 0~32 | 脱敏手机号 | `BuyerSummaryResponse.java:16` |
| `customerLevel` | `buyer` | 否 | String | 0~32 | 客户等级；未请求或降级时为空 | `BuyerSummaryResponse.java:18` |
| `items` | `list[]` | 是 | Array&lt;Object&gt; | 至少 1 项 | 订单商品摘要 | `OrderSummaryResponse.java:25` |
| `skuId` | `items[]` | 是 | String | 1~40 | SKU 标识 | `OrderItemSummaryResponse.java:12` |
| `productName` | `items[]` | 是 | String | 1~128 | 商品名称 | `OrderItemSummaryResponse.java:14` |
| `quantity` | `items[]` | 是 | Integer | ≥1 | 商品数量 | `OrderItemSummaryResponse.java:16` |
| `amount` | `list[]` | 是 | Object | - | 金额摘要 | `OrderAmountResponse.java:10-22` |
| `currency` | `amount` | 是 | String | ISO 4217 | 币种 | `OrderAmountResponse.java:12` |
| `totalAmount` | `amount` | 是 | Decimal | 2 位小数 | 订单总金额，单位为元 | `OrderAmountResponse.java:14` |
| `paidAmount` | `amount` | 是 | Decimal | 2 位小数 | 已支付金额 | `OrderAmountResponse.java:16` |
| `paymentStatus` | `amount` | 是 | String | 枚举 | 支付状态 | `OrderAmountResponse.java:18` |
| `fulfillmentStatus` | `list[]` | 否 | String | 枚举 | 履约状态；未请求时为空，降级时为 `UNKNOWN` | `OrderSummaryResponse.java:32` |
| `riskSummary` | `list[]` | 否 | Object | - | 风险摘要 | `OrderRiskSummaryResponse.java:10-21` |
| `riskLevel` | `riskSummary` | 是 | String | `LOW`/`MEDIUM`/`HIGH` | 风险等级 | `OrderRiskSummaryResponse.java:12` |
| `riskTags` | `riskSummary` | 是 | Array&lt;String&gt; | 可为空数组 | 风险标签 | `OrderRiskSummaryResponse.java:14` |
| `createdAt` | `list[]` | 是 | String | ISO 8601 | 订单创建时间 | `OrderSummaryResponse.java:36` |
| `updatedAt` | `list[]` | 是 | String | ISO 8601 | 订单最后更新时间 | `OrderSummaryResponse.java:38` |
| `degradation` | `data` | 是 | Object | - | 补充能力降级信息 | `OrderQueryDegradationResponse.java:10-26` |
| `profileDegraded` | `degradation` | 是 | Boolean | - | 客户资料是否降级 | `OrderQueryDegradationResponse.java:12` |
| `fulfillmentDegraded` | `degradation` | 是 | Boolean | - | 履约状态是否降级 | `OrderQueryDegradationResponse.java:14` |
| `riskDegraded` | `degradation` | 是 | Boolean | - | 风险摘要是否降级 | `OrderQueryDegradationResponse.java:16` |
| `warnings` | `degradation` | 是 | Array&lt;String&gt; | 可为空数组 | 降级原因摘要，不包含内部异常栈 | `OrderQueryDegradationResponse.java:18` |

## 三、请求报文示例

```http
POST /api/admin/orders/query HTTP/1.1
Host: api.example.invalid
Content-Type: application/json
Authorization: Bearer <redacted>
X-Tenant-Id: tenant-demo
X-Trace-Id: trace-demo-20260716-0001
```

```json
{
  "pageNo": 1,
  "pageSize": 20,
  "filters": {
    "orderStatus": [
      "PAID",
      "SHIPPED"
    ],
    "createdFrom": "2026-07-01T00:00:00+08:00",
    "createdTo": "2026-07-17T00:00:00+08:00",
    "buyerKeyword": "demo-buyer",
    "productKeyword": "示例商品",
    "minAmount": 100.00,
    "maxAmount": 5000.00
  },
  "searchMode": "EXACT",
  "sorts": [
    {
      "field": "createdAt",
      "direction": "DESC"
    }
  ],
  "include": {
    "customerProfile": true,
    "fulfillment": true,
    "riskSummary": true
  }
}
```

## 四、响应报文示例

```json
{
  "code": "SUCCESS",
  "message": "成功",
  "traceId": "trace-demo-20260716-0001",
  "data": {
    "pageNo": 1,
    "pageSize": 20,
    "total": 2,
    "hasNext": false,
    "list": [
      {
        "orderId": "order-demo-0001",
        "orderNo": "D202607160001",
        "orderStatus": "SHIPPED",
        "buyer": {
          "customerId": "customer-demo-01",
          "displayName": "示例买家",
          "maskedMobile": "138****0000",
          "customerLevel": "GOLD"
        },
        "items": [
          {
            "skuId": "sku-demo-01",
            "productName": "示例商品 A",
            "quantity": 2
          }
        ],
        "amount": {
          "currency": "CNY",
          "totalAmount": 299.00,
          "paidAmount": 299.00,
          "paymentStatus": "PAID"
        },
        "fulfillmentStatus": "IN_TRANSIT",
        "riskSummary": {
          "riskLevel": "LOW",
          "riskTags": []
        },
        "createdAt": "2026-07-15T10:20:30+08:00",
        "updatedAt": "2026-07-16T09:15:00+08:00"
      }
    ],
    "degradation": {
      "profileDegraded": false,
      "fulfillmentDegraded": false,
      "riskDegraded": false,
      "warnings": []
    }
  }
}
```

## 五、错误或异常载荷

| 错误码或类型 | 触发条件 | 含义 | HTTP 状态 | 来源 |
|--------------|----------|------|-----------|------|
| `INVALID_ARGUMENT` | 页码、时间范围、排序字段或条件组合非法 | 请求参数校验失败 | 400 | `GlobalExceptionHandler.java:26-48` |
| `TENANT_ACCESS_DENIED` | 登录态无权访问请求头中的租户 | 租户数据权限不足 | 403 | `PermissionContext.java:30-57` |
| `FULL_TEXT_DISABLED` | 请求全文检索但运行时开关关闭 | 当前环境未启用全文搜索 | 409 | `OrderQueryService.java:31-38` |
| `REGION_QUERY_TIMEOUT` | 远端单元 RPC 超时 | 无法从租户归属单元获取订单 | 504 | `RemoteOrderQueryClient.java:42-68` |
| `QUERY_LIMIT_EXCEEDED` | 查询跨度或结果窗口超过限制 | 需要缩小查询范围 | 422 | `OrderQueryPolicy.java:20-51` |
| `INTERNAL_ERROR` | 未分类服务端异常 | 服务内部错误，不返回异常栈 | 500 | `GlobalExceptionHandler.java:72-89` |

### 参数错误示例

```json
{
  "code": "INVALID_ARGUMENT",
  "message": "createdTo 必须晚于 createdFrom",
  "traceId": "trace-demo-20260716-0002",
  "details": [
    {
      "field": "filters.createdTo",
      "reason": "INVALID_TIME_RANGE"
    }
  ]
}
```

### 下游补充降级示例

下游客户或履约服务失败但订单主查询成功时，HTTP 状态和 `code` 仍表示查询成功，并通过 `degradation` 字段明确表达缺口：

```json
{
  "code": "SUCCESS",
  "message": "成功，部分补充信息已降级",
  "traceId": "trace-demo-20260716-0003",
  "data": {
    "pageNo": 1,
    "pageSize": 20,
    "total": 0,
    "hasNext": false,
    "list": [],
    "degradation": {
      "profileDegraded": true,
      "fulfillmentDegraded": false,
      "riskDegraded": false,
      "warnings": [
        "客户资料暂不可用"
      ]
    }
  }
}
```
