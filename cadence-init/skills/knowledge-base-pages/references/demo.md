# 页面能力案例

> **案例范围**：虚构订单管理前端，展示 Vue 动态路由、React 静态路由、页面到 REST API 主文件、字段级 TABLE 和配置实体的关联，以及未登记接口的候选处理。
>
> **链接说明**：接口链接按最终产物位于 `cadence/knowledge-base/pages/` 时的相对路径编写，目标是 `cadence/knowledge-base/interfaces/` 下由 `knowledge-base-api` 生成的接口主文件。
>
> **分类说明**：本案例中的 `API-order-page` 是工程扫描发现的对内 REST，格式参考 [`knowledge-base-api/references/demo_对内REST.md`](../../knowledge-base-api/references/demo_对内REST.md)。页面只有在代码实际调用开放地址时才关联对外 API，不能因“订单查询”名称相似而关联 `API-partner-order-query`。

## 一、前端应用与路由来源

| 应用 | 技术栈 | 路由来源 | 请求封装 | 运行时限制 |
|------|--------|----------|----------|------------|
| `APP-admin-web` | Vue 3、Vue Router、Pinia | 后端菜单 API 经 `permissionStore.generateRoutes` 转换 | `src/utils/request.ts`，统一添加 `/api` 前缀 | 代码只能证明转换逻辑；生产菜单是否下发待确认 |
| `APP-ops-console` | React、React Router、TanStack Query | `createBrowserRouter` 静态配置 | `src/lib/httpClient.ts`，使用 `VITE_API_BASE_URL` | Feature Flag 可能隐藏部分操作 |

## 二、路由树

```text
APP-admin-web
└─ ROUTE-admin-orders          /admin/orders
   └─ PAGE-order-list          src/views/order/list.vue

APP-ops-console
└─ ROUTE-orders-detail         /orders/:orderId
   └─ PAGE-order-detail        OrderDetailPage
```

## 三、页面能力清单

| PAGE ID | ROUTE ID | 路径 | 页面用途 | 组件 | 权限 | 状态 | API | 证据 |
|---------|----------|------|----------|------|------|------|-----|------|
| `PAGE-order-list` | `ROUTE-admin-orders` | `/admin/orders` | 查询、筛选和导出订单 | `src/views/order/list.vue` | `order:view`；导出要求 `order:export` | 组件存在、条件启用；生产菜单待确认 | [`API-order-page`](../interfaces/API-order-page_订单分页查询_orderPageQuery.md)、[`API-order-export`](../interfaces/API-order-export_订单导出_orderExport.md)、`API-CANDIDATE-order-batch-retry` | `src/router/modules/order.ts:8-24`、`src/views/order/list.vue:45-162` |
| `PAGE-order-detail` | `ROUTE-orders-detail` | `/orders/:orderId` | 查看订单明细、支付与履约状态 | `src/pages/orders/OrderDetailPage.tsx` | `RequirePermission("order:view")` | 已声明、组件存在、已装配 | [`API-order-detail`](../interfaces/API-order-detail_订单详情查询_orderDetailQuery.md) | `src/router.tsx:28-41`、`OrderDetailPage.tsx:18-66` |

## 四、页面与 API 映射

### 4.1 已匹配接口

| PAGE ID | API ID | 分类 | 方法与标准路径 | 调用位置 | 请求封装、Store 或 Hook | 接口主文件 | SERVICE/MODULE | 状态 | 可信度 | 证据 |
|---------|--------|------|----------------|----------|-------------------------|------------|----------------|------|--------|------|
| `PAGE-order-list` | `API-order-page` | 对内 | `POST /api/admin/orders/query` | `src/api/order.ts:18-26` | 页面 → `orderStore.fetchPage` → `orderApi.queryPage` → `request` | [订单分页查询](../interfaces/API-order-page_订单分页查询_orderPageQuery.md) | `SERVICE-order-query` | 已登记、已实现、已暴露 | 高 | 前端调用方法与规范化路径匹配接口索引；Controller 路由一致 |
| `PAGE-order-list` | `API-order-export` | 对内 | `POST /api/admin/orders/export` | `src/api/order.ts:28-36` | 页面 → `useOrderExport` → `orderApi.exportOrders` → `request` | [订单导出](../interfaces/API-order-export_订单导出_orderExport.md) | `SERVICE-order-export` | 已登记、条件启用 | 高 | API ID、Method、Path 和导出 Hook 均可对应 |
| `PAGE-order-detail` | `API-order-detail` | 对内 | `GET /api/admin/orders/{orderId}` | `src/api/orderDetail.ts:12-18` | 页面 → `useOrderDetail` → `orderDetailApi.get` → `httpClient` | [订单详情查询](../interfaces/API-order-detail_订单详情查询_orderDetailQuery.md) | `SERVICE-order-query` | 已登记、已实现 | 高 | React Hook 最终调用的 Method + Path 与接口主文件一致 |

### 4.2 页面字段与数据模型影响

| PAGE/ROUTE ID | API ID | SERVICE/MODULE | TABLE 稳定 ID | 页面字段 | API 字段来源 | 表字段 | 读写 | Mapper/SQL 或后端映射 | 证据状态 | 表文档链接 |
|---------------|--------|----------------|---------------|----------|------------|--------|------|----------------------|----------|------------|
| `PAGE-order-list` | `API-order-page` | `SERVICE-order-query` | `TABLE-order` | 状态筛选、订单状态列 | 请求 `filters.status` → `OrderPageQueryRequest.status`；响应 `row.status` → `OrderSummaryResponse.status` | `status` | R | `OrderQueryMapper.selectPage` 与 `OrderSummaryAssembler` | 已确认 | [`TABLE-order`](../data-models/SCHEMA-order/TABLE-order.md) |
| `PAGE-order-list` | `API-order-page` | `SERVICE-order-query` | `TABLE-order` | 金额列、创建时间列 | `OrderSummaryResponse.amount/createdAt` → Store 行模型 | `total_amount`、`created_at` | R | Mapper resultMap 与响应 Assembler | 已确认 | [`TABLE-order`](../data-models/SCHEMA-order/TABLE-order.md) |
| `PAGE-order-list` | `API-order-page` | `SERVICE-order-query` | `TABLE-order-item` | 商品摘要、商品数量 | `OrderSummaryResponse.itemSummary/itemCount` → 表格列 | `sku_name`、`quantity` | R | `OrderQueryMapper.selectItemSummary` 聚合 SQL | 已确认 | [`TABLE-order-item`](../data-models/SCHEMA-order/TABLE-order-item.md) |
| `PAGE-order-list` | `API-order-export` | `SERVICE-order-export` | `TABLE-order` | 导出筛选条件与导出字段 | 页面导出 DTO → `OrderExportRequest` → 导出查询模型 | `status`、`created_at`、导出字段集合 | R | `OrderMapper.selectForExport` | 已确认 | [`TABLE-order`](../data-models/SCHEMA-order/TABLE-order.md) |
| `PAGE-order-detail` | `API-order-detail` | `SERVICE-order-query` | `TABLE-order-payment` | 支付状态、支付方式 | `OrderDetailResponse.paymentStatus/paymentMethod` → 详情卡片 | `payment_status`、`payment_method` | R | `OrderPaymentMapper.selectByOrderId` 与详情 Assembler | 已确认 | [`TABLE-order-payment`](../data-models/SCHEMA-order/TABLE-order-payment.md) |
| `PAGE-order-detail` | `API-order-detail` | `SERVICE-order-query` | 待确认 | 页面字段 `riskStatus` | 仅发现响应字段，接口主文件未提供 TABLE 或后端映射 | 待确认 | 待确认 | 待确认 | 待确认 | 待确认 |

> `riskStatus` 即使与某个表字段同名，也不能直接关联 TABLE；当前缺少 API 模型到 Mapper/SQL 的后端证据，因此保留待确认。

### 4.3 页面配置依赖

| PAGE/ROUTE ID | API ID 或前端绑定 | 配置组稳定 ID | 服务配置实体 | 配置键 | 页面影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|---------------|-------------------|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| `PAGE-order-list` | `API-order-page` | `CONFIG-order-query` | `SERVICE-order-query` | `order.query.full-text-enabled` | 全文检索条件是否可提交；关闭时 API 返回能力未启用错误 | 生产、测试；具体值不记录 | `OrderQueryProperties#fullTextEnabled` 被查询分支读取，页面按接口能力错误禁用条件 | 已确认 | [`SERVICE-order-query`](../configurations/SERVICE-order-query.md) |
| `PAGE-order-list` | `API-order-export` | `CONFIG-order-export` | `SERVICE-order-export` | `order.export.enabled` | 导出按钮对应能力是否可执行 | 生产 Profile | `OrderExportProperties#enabled` 参与 Controller 条件装配；页面能力清单读取 API 状态 | 已确认 | [`SERVICE-order-export`](../configurations/SERVICE-order-export.md) |
| `PAGE-order-detail` | `API-order-detail` | `CONFIG-order-detail` | `SERVICE-order-query` | `order.detail.manual-retry-enabled` | 控制“人工重试”操作是否展示 | 生产、测试；具体值不记录 | `OrderDetailProperties#manualRetryEnabled` → `OrderDetailResponse.features.manualRetry` → `useOrderDetail` | 已确认 | [`SERVICE-order-query`](../configurations/SERVICE-order-query.md) |

Feature Flag 证据链：`PAGE-order-detail → API-order-detail → SERVICE-order-query → CONFIG-order-detail → order.detail.manual-retry-enabled → OrderDetailResponse.features.manualRetry → useOrderDetail → 页面操作显隐`。该链证明页面能力受开关控制，但不记录真实环境值。

### 4.4 未匹配接口候选

| PAGE ID | 候选 API ID | 已知方法与路径 | 调用位置 | 接口主文件 | 状态 | 可信度 | 待确认项 |
|---------|-------------|----------------|----------|------------|------|--------|----------|
| `PAGE-order-list` | `API-CANDIDATE-order-batch-retry` | `POST /api/admin/orders/batch-retry` | `src/api/order.ts:38-44` | 未登记，不生成虚假链接 | 前端调用存在；接口索引未发现匹配项 | 中 | 使用 `knowledge-base-api` 在当前工程范围内核实 Controller、网关路由和能力分类 |

> 候选接口不能因为页面按钮名为“批量重试”就直接命名为正式 API。候选 ID 只用于追踪缺口，后续由 API 分析确认稳定 ID、分类和接口主文件。

## 五、权限与导航

### Vue 动态路由

- 路由 ID：`ROUTE-admin-orders`
- 路径：`/admin/orders`
- 来源：后端菜单 API 经 `permissionStore.generateRoutes` 转换。
- 页面权限：`order:view`。
- 导出按钮权限：`order:export`，只证明前端展示控制；后端接口是否完成相同鉴权需要读取接口主文件和服务代码。
- 状态：组件存在、动态路由转换已实现；生产环境是否下发菜单无法由静态代码证明。

### React 静态路由

- 路由 ID：`ROUTE-orders-detail`
- 路径：`/orders/:orderId`
- 来源：`createBrowserRouter` 配置。
- 权限包装：`RequirePermission("order:view")`。
- 状态：已声明、组件存在、已装配；已发现订单列表页跳转入口。

## 六、状态管理与请求封装

### Vue 调用链

```text
PAGE-order-list
└─ orderStore.fetchPage(filters)
   └─ orderApi.queryPage(request)
      └─ request.post("/admin/orders/query")
         └─ baseURL="/api"
            └─ POST /api/admin/orders/query
               └─ API-order-page
```

开发代理把 `/api` 转发到网关但不删除前缀，因此匹配接口知识库时保留 `/api`。不能直接拿源码中的 `"/admin/orders/query"` 与后端路径比较。

### React 调用链

```text
PAGE-order-detail
└─ useOrderDetail(orderId)
   └─ orderDetailApi.get(orderId)
      └─ httpClient.get(`/api/admin/orders/${orderId}`)
         └─ GET /api/admin/orders/{orderId}
            └─ API-order-detail
```

实际订单 ID 必须规范化为路径模板 `{orderId}` 后再与接口索引匹配。

## 七、动态路由和运行时限制

- Vue 路由的转换函数和组件映射可以由代码证明。
- 生产环境实际返回的菜单、租户功能开关和用户权限集合未提供，因此 `PAGE-order-list` 标记为条件启用。
- React 详情页是静态路由，但页面内“人工重试”操作受 Feature Flag 控制；静态路由存在不等于该操作可用。

## 八、完整追溯关系

```text
ROUTE-admin-orders
→ PAGE-order-list
→ API-order-page
→ SERVICE-order-query
├─ TABLE-order / TABLE-order-item → 字段/Mapper SQL → data-models/ 文档
└─ CONFIG-order-query → order.query.full-text-enabled → configurations/SERVICE-order-query.md

ROUTE-admin-orders
→ PAGE-order-list
→ API-order-export
→ SERVICE-order-export
├─ TABLE-order → 导出字段/OrderMapper.selectForExport → data-models/ 文档
└─ CONFIG-order-export → order.export.enabled → configurations/SERVICE-order-export.md

ROUTE-orders-detail
→ PAGE-order-detail
→ API-order-detail
→ SERVICE-order-query
├─ TABLE-order / TABLE-order-item / TABLE-order-payment → 字段/Mapper SQL → data-models/ 文档
└─ CONFIG-order-detail → order.detail.manual-retry-enabled → configurations/SERVICE-order-query.md
```

上述 API 节点在实际产物中必须链接到 `cadence/knowledge-base/interfaces/` 下的对应主文件，TABLE 节点链接字段级 `data-models/` 文档，CONFIGURATION 节点链接 `configurations/` 服务配置实体，关系矩阵使用相同稳定 ID。

## 九、孤立、不可达和冲突项

- `src/views/legacy/report.vue` 存在，但路由、菜单和其他页面均无引用。
- 标记：代码存在但不可达。
- 不写入有效页面清单，保留在异常项和待确认清单。
- `API-CANDIDATE-order-batch-retry` 仅有前端调用证据，不得写成“后端已实现”。

## 十、待人工确认

- 生产菜单是否向目标角色下发 `ROUTE-admin-orders`。
- `API-CANDIDATE-order-batch-retry` 是否在当前后端工程范围内实现。
- 导出对象存储下载地址是否由 `API-order-export` 直接返回，还是通过独立下载接口获取。
