# API-partner-order-query 合作方订单查询接口 - 参数与报文

> **主文件**：`API-partner-order-query_合作方订单查询_partnerOrderQuery.md`
> **能力 ID**：`API-partner-order-query`
> **分类**：对外
> **HTTP 方法与路径**：`POST /openapi/order-center/partnerOrderQuery/v1`
> **数据来源**：用户接口资料、网关注册、请求响应模型和虚构示例工程代码
>
> **案例声明**：本文字段、取值和报文均为虚构示例，只展示对外 API 的公共报文头、签名字段和业务模型格式。实际字段必须来自用户资料或代码证据。

## 一、输入参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| `X-Partner-Code` | 请求头 | 是 | String | 1~32 | 开放平台分配的合作方编码 | `order-center-apis.yaml:12` |
| `X-Request-Time` | 请求头 | 是 | String | ISO 8601 | 请求时间；必须处于网关允许时间窗 | `SignatureVerifyFilter.java:41-56` |
| `X-Nonce` | 请求头 | 是 | String | 16~64 | 单次请求随机值，用于防重放 | `NonceReplayGuard.java:26-61` |
| `X-Signature-Algorithm` | 请求头 | 是 | String | 枚举 | 示例为 `HMAC-SHA256`；以用户规范为准 | `order-center-apis.yaml:15` |
| `X-Signature` | 请求头 | 是 | String | 1~512 | 签名结果；文档不得记录真实密钥或完整签名原文 | `SignatureVerifyFilter.java:58-92` |
| `X-Request-Id` | 请求头 | 是 | String | 1~64 | 合作方请求唯一标识 | `PartnerRequestHeader.java:12` |
| `request` | 根节点 | 是 | Object | - | 业务请求节点 | `PartnerOrderQueryRequest.java:16-48` |
| `regionCode` | `request` | 是 | String | 1~16 | 用户接口规范中的区域编码 | `PartnerOrderQueryRequest.java:18` |
| `operatorId` | `request` | 否 | String | 0~64 | 合作方操作人标识 | `PartnerOrderQueryRequest.java:20` |
| `query` | `request` | 是 | Object | - | 订单查询条件 | `PartnerOrderQueryRequest.java:22` |
| `externalOrderNo` | `query` | 否 | String | 1~64 | 合作方侧订单号 | `PartnerOrderCriteria.java:18` |
| `platformOrderNo` | `query` | 否 | String | 1~40 | 平台订单号；只能查询当前合作方授权订单 | `PartnerOrderCriteria.java:20` |
| `customerToken` | `query` | 否 | String | 1~128 | 合作方客户 Token，不接受明文敏感身份信息 | `PartnerOrderCriteria.java:22` |
| `productCode` | `query` | 否 | String | 1~40 | 合作方可见的商品编码 | `PartnerOrderCriteria.java:24` |
| `orderStatus` | `query` | 否 | Array&lt;String&gt; | 最多 10 项 | 对外订单状态集合 | `ExternalOrderStatus.java:8-20` |
| `createdFrom` | `query` | 否 | String | ISO 8601 | 创建时间起点，含边界 | `PartnerOrderCriteria.java:28` |
| `createdTo` | `query` | 否 | String | ISO 8601 | 创建时间终点，不含边界 | `PartnerOrderCriteria.java:30` |
| `searchMode` | `query` | 是 | String | `EXACT`/`FULL_TEXT` | 精确查询或已授权的全文检索 | `PartnerSearchMode.java:5-8` |
| `pageNo` | `query` | 是 | Integer | ≥1 | 页码，从 1 开始 | `PartnerOrderCriteria.java:34` |
| `pageSize` | `query` | 是 | Integer | 1~100 | 每页数量 | `PartnerOrderCriteria.java:36` |
| `include` | `request` | 否 | Object | - | 可选补充字段开关 | `PartnerOrderQueryRequest.java:25` |
| `items` | `include` | 否 | Boolean | 默认 `true` | 是否返回商品摘要 | `PartnerOrderQueryRequest.java:28` |
| `paymentSummary` | `include` | 否 | Boolean | 默认 `false` | 是否返回合作方已授权的支付摘要 | `PartnerOrderQueryRequest.java:30` |
| `fulfillmentStatus` | `include` | 否 | Boolean | 默认 `false` | 是否补充履约状态 | `PartnerOrderQueryRequest.java:32` |

### 条件约束

- `externalOrderNo`、`platformOrderNo`、`customerToken`、`productCode` 或创建时间范围至少提供一项。
- `createdFrom` 与 `createdTo` 同时提供时，时间跨度不得超过合作方授权策略中的最大值，示例为 90 天。
- `searchMode=FULL_TEXT` 必须同时满足能力开通和至少一个全文字段非空。
- 合作方、区域和数据范围由请求头及服务端授权信息决定，不能由请求体覆盖。
- `X-Nonce` 在有效时间窗内只能使用一次。

## 二、输出参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| `responseCode` | 根节点 | 是 | String | 1~32 | 对外响应码；成功为 `SUCCESS` | `PartnerApiResponse.java:12-18` |
| `responseMessage` | 根节点 | 是 | String | 0~256 | 对外响应描述，不包含内部异常栈 | `PartnerApiResponse.java:20` |
| `requestId` | 根节点 | 是 | String | 1~64 | 回传请求唯一标识 | `PartnerApiResponse.java:22` |
| `responseTime` | 根节点 | 是 | String | ISO 8601 | 网关或 Provider 响应时间 | `PartnerApiResponse.java:24` |
| `data` | 根节点 | 条件 | Object | - | 成功时的分页数据 | `PartnerOrderPageResponse.java:12-34` |
| `pageNo` | `data` | 是 | Integer | ≥1 | 当前页码 | `PartnerOrderPageResponse.java:14` |
| `pageSize` | `data` | 是 | Integer | 1~100 | 当前分页大小 | `PartnerOrderPageResponse.java:16` |
| `total` | `data` | 是 | Long | ≥0 | 当前合作方授权范围内的总记录数 | `PartnerOrderPageResponse.java:18` |
| `hasNext` | `data` | 是 | Boolean | - | 是否存在下一页 | `PartnerOrderPageResponse.java:20` |
| `orders` | `data` | 是 | Array&lt;Object&gt; | 可为空数组 | 合作方订单摘要列表 | `PartnerOrderSummary.java:14-68` |
| `externalOrderNo` | `orders[]` | 否 | String | 0~64 | 合作方侧订单号 | `PartnerOrderSummary.java:16` |
| `platformOrderNo` | `orders[]` | 是 | String | 1~40 | 平台订单号 | `PartnerOrderSummary.java:18` |
| `orderStatus` | `orders[]` | 是 | String | 对外枚举 | 对外订单状态 | `PartnerOrderSummary.java:20` |
| `productSummary` | `orders[]` | 否 | Array&lt;Object&gt; | 可为空数组 | 商品摘要 | `PartnerOrderSummary.java:22` |
| `productCode` | `productSummary[]` | 是 | String | 1~40 | 合作方可见商品编码 | `PartnerProductSummary.java:12` |
| `productName` | `productSummary[]` | 是 | String | 1~128 | 商品名称 | `PartnerProductSummary.java:14` |
| `quantity` | `productSummary[]` | 是 | Integer | ≥1 | 商品数量 | `PartnerProductSummary.java:16` |
| `amount` | `orders[]` | 是 | Object | - | 对外金额摘要 | `PartnerOrderAmount.java:10-22` |
| `currency` | `amount` | 是 | String | ISO 4217 | 币种 | `PartnerOrderAmount.java:12` |
| `totalAmount` | `amount` | 是 | Decimal | 2 位小数 | 订单总金额 | `PartnerOrderAmount.java:14` |
| `paymentStatus` | `amount` | 条件 | String | 对外枚举 | 开通支付摘要字段时返回 | `PartnerOrderAmount.java:16` |
| `fulfillmentStatus` | `orders[]` | 条件 | String | 对外枚举 | 开通并请求履约状态时返回 | `PartnerOrderSummary.java:28` |
| `createdAt` | `orders[]` | 是 | String | ISO 8601 | 订单创建时间 | `PartnerOrderSummary.java:30` |
| `updatedAt` | `orders[]` | 是 | String | ISO 8601 | 订单最后更新时间 | `PartnerOrderSummary.java:32` |
| `degradation` | `data` | 是 | Object | - | 可选补充能力降级信息 | `PartnerDegradationResponse.java:10-22` |
| `fulfillmentDegraded` | `degradation` | 是 | Boolean | - | 履约状态是否降级 | `PartnerDegradationResponse.java:12` |
| `warnings` | `degradation` | 是 | Array&lt;String&gt; | 可为空数组 | 对外可见的降级说明 | `PartnerDegradationResponse.java:14` |

## 三、请求报文示例

```http
POST /openapi/order-center/partnerOrderQuery/v1 HTTP/1.1
Host: open.example.invalid
Content-Type: application/json
X-Partner-Code: partner-demo
X-Request-Time: 2026-07-16T10:30:00+08:00
X-Nonce: nonce-demo-20260716-0001
X-Signature-Algorithm: HMAC-SHA256
X-Signature: <redacted>
X-Request-Id: request-demo-20260716-0001
```

```json
{
  "request": {
    "regionCode": "region-demo",
    "operatorId": "operator-demo",
    "query": {
      "externalOrderNo": "external-demo-0001",
      "platformOrderNo": "P202607160001",
      "orderStatus": [
        "PAID",
        "FULFILLING"
      ],
      "createdFrom": "2026-07-01T00:00:00+08:00",
      "createdTo": "2026-07-17T00:00:00+08:00",
      "searchMode": "EXACT",
      "pageNo": 1,
      "pageSize": 20
    },
    "include": {
      "items": true,
      "paymentSummary": true,
      "fulfillmentStatus": true
    }
  }
}
```

## 四、响应报文示例

```json
{
  "responseCode": "SUCCESS",
  "responseMessage": "成功",
  "requestId": "request-demo-20260716-0001",
  "responseTime": "2026-07-16T10:30:00.125+08:00",
  "data": {
    "pageNo": 1,
    "pageSize": 20,
    "total": 1,
    "hasNext": false,
    "orders": [
      {
        "externalOrderNo": "external-demo-0001",
        "platformOrderNo": "P202607160001",
        "orderStatus": "FULFILLING",
        "productSummary": [
          {
            "productCode": "product-demo-01",
            "productName": "示例商品 A",
            "quantity": 2
          }
        ],
        "amount": {
          "currency": "CNY",
          "totalAmount": 299.00,
          "paymentStatus": "PAID"
        },
        "fulfillmentStatus": "IN_TRANSIT",
        "createdAt": "2026-07-15T10:20:30+08:00",
        "updatedAt": "2026-07-16T09:15:00+08:00"
      }
    ],
    "degradation": {
      "fulfillmentDegraded": false,
      "warnings": []
    }
  }
}
```

## 五、错误或异常载荷

| 错误码或类型 | 触发条件 | 含义 | HTTP 状态 | 来源 |
|--------------|----------|------|-----------|------|
| `SIGNATURE_INVALID` | 签名不匹配 | 请求签名无效 | 401 | `SignatureVerifyFilter.java:58-92` |
| `REQUEST_EXPIRED` | 请求时间超出允许时间窗 | 请求已过期 | 401 | `SignatureVerifyFilter.java:41-56` |
| `NONCE_REPLAYED` | 相同合作方在时间窗内重复使用 Nonce | 检测到重放请求 | 409 | `NonceReplayGuard.java:26-61` |
| `PARTNER_PERMISSION_DENIED` | 合作方未授权该能力或数据范围 | 无权调用或查询目标订单 | 403 | `PartnerPermissionService.java:30-65` |
| `RATE_LIMITED` | 超过合作方与能力维度配额 | 请求过于频繁 | 429 | `PartnerRateLimitFilter.java:24-58` |
| `INVALID_ARGUMENT` | 查询条件、时间范围或分页参数非法 | 请求参数校验失败 | 400 | `PartnerApiExceptionMapper.java:26-48` |
| `FULL_TEXT_DISABLED` | 未开通全文搜索却请求该模式 | 合作方未开通全文检索 | 403 | `PartnerOrderQueryService.java:42-51` |
| `REGION_QUERY_TIMEOUT` | 授权区域 RPC 超时 | 暂时无法查询目标区域订单 | 504 | `PartnerOrderRegionBridge.java:52-68` |
| `INTERNAL_ERROR` | 未分类服务端异常 | 服务内部错误，不返回异常栈 | 500 | `PartnerApiExceptionMapper.java:70-89` |

### 签名错误示例

```json
{
  "responseCode": "SIGNATURE_INVALID",
  "responseMessage": "请求签名无效",
  "requestId": "request-demo-20260716-0002",
  "responseTime": "2026-07-16T10:31:00.020+08:00"
}
```

### 下游补充降级示例

履约服务失败但订单主查询成功时，接口仍返回订单主数据，并通过 `degradation` 表达缺口：

```json
{
  "responseCode": "SUCCESS",
  "responseMessage": "成功，部分补充信息已降级",
  "requestId": "request-demo-20260716-0003",
  "responseTime": "2026-07-16T10:32:00.115+08:00",
  "data": {
    "pageNo": 1,
    "pageSize": 20,
    "total": 0,
    "hasNext": false,
    "orders": [],
    "degradation": {
      "fulfillmentDegraded": true,
      "warnings": [
        "履约状态暂不可用"
      ]
    }
  }
}
```
