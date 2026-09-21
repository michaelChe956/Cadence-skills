# 页面能力 PAGE-order-manage 订单管理

## 文档元数据

- 生成时间：2026-09-20
- Git 分支：master
- 基线提交：1f867b9fcdf95f2e11808454898f333d7d512e90
- 执行模式：初始化续跑（`coverage.initialization.status: in_progress`，本次执行 `pages` 阶段）
- 前端应用：`SERVICE-web-portal`（`MODULE-web-portal-app`、`MODULE-web-portal-api`、`MODULE-web-portal-views`）
- 页面稳定 ID：`PAGE-order-manage`；路由稳定 ID：`ROUTE-web-portal-orders`
- 动态路由限制：本页为代码静态路由（`web-portal/src/main.js:12`）；未发现后端菜单下发、运行时 `addRoute` 或权限路由转换，生产入口与菜单未提供

## 1. 前端应用与路由来源

- 应用装配：`web-portal/src/main.js:8-15`（`createRouter` + `createWebHistory`），`web-portal/src/main.js:16` 挂载 `#app`。
- 路由声明：`web-portal/src/main.js:12` → `{ path: '/orders', component: OrderPage }`；无 `name`、`meta`、`redirect`、`alias`、动态参数、懒加载与嵌套。
- 组件：`web-portal/src/views/OrderPage.vue:1-12`，由 `web-portal/src/main.js:5` 静态导入。
- 路由来源分类：代码静态路由；未发现其他来源（`user-input/page-scope.md:6` 声明与代码一致）。

## 2. 路由树

```text
（无父级与 Layout；本路由为平级静态路由）
/orders → ROUTE-web-portal-orders → PAGE-order-manage → views/OrderPage.vue
```

- 无父子关系、无重定向、无别名、无动态参数（订单号未作为路由参数）。
- 应用未定义根路由 `/`、通配路由与 404 视图，未匹配路径不渲染任何业务视图。

## 3. 页面能力清单

| PAGE ID | ROUTE ID | 路径 | 页面用途 | 组件 | 权限 | 状态 | API 主文件 | 证据 |
|---------|----------|------|----------|------|------|------|------------|------|
| PAGE-order-manage | ROUTE-web-portal-orders | `/orders` | 订单管理操作：触发指定订单发货、触发订单导出 | `web-portal/src/views/OrderPage.vue` | 未发现（无 `meta`、无守卫、无权限码） | 已声明、组件存在、已装配；可达性待确认（无菜单入口、应用入口 HTML 缺失） | [`API-order-ship`](../interfaces/API-order-ship_订单发货_ship.md)、[`API-order-export`](../interfaces/API-order-export_订单导出_export.md) | `web-portal/src/main.js:5,12`、`web-portal/src/views/OrderPage.vue:1-12` |

- 页面操作：两个按钮分别触发 `ship()` 与 `exportAll()`（`web-portal/src/views/OrderPage.vue:4-5,10-11`）；无自动请求。
- 展示字段：页面未展示任何订单数据字段（无列表、无详情、无状态显示，`web-portal/src/views/OrderPage.vue:1-7`）。
- 输入参数：未发现表单、筛选或选择控件；发货请求参数为硬编码 `1`（`web-portal/src/views/OrderPage.vue:10`），登记 Q-L7。
- 状态来源：未发现 `ref`/Store 持有响应；两个操作丢弃返回结果（`web-portal/src/views/OrderPage.vue:10-11`），无成功/失败提示。
- 上传、下载、WebSocket 与消息能力：未发现（导出按钮未产出或下载文件，见 4.5）。
- 生命周期与缓存：无 `onMounted` 自动加载、无 KeepAlive；无 Feature Flag 与环境分支。

## 4. 页面与 API 映射

### 4.1 已匹配接口

| PAGE ID | API ID | 分类 | 方法与标准路径 | 调用位置 | 请求封装、Store 或 Hook | 接口主文件 | SERVICE/MODULE | 状态 | 可信度 | 证据 |
|---------|--------|------|----------------|----------|-------------------------|------------|----------------|------|--------|------|
| PAGE-order-manage | API-order-ship | 对内 | `POST /api/order/{orderId}/ship` | `web-portal/src/views/OrderPage.vue:10`（`shipOrder(1)`） | 页面 → `api/index.js#shipOrder`（`web-portal/src/api/index.js:4`）→ `api/request.js` axios 实例（`baseURL: '/api'`）→ 开发代理 `/api` | [`API-order-ship_订单发货_ship.md`](../interfaces/API-order-ship_订单发货_ship.md) | `SERVICE-order-service` / `MODULE-order-core` | 已实现、已装配、已暴露 | 高 | `web-portal/src/api/index.js:4`、`web-portal/src/views/OrderPage.vue:10` |
| PAGE-order-manage | API-order-export | 对外 | `POST /api/order/export` | `web-portal/src/views/OrderPage.vue:11`（`exportOrder()`） | 页面 → `api/index.js#exportOrder`（`web-portal/src/api/index.js:4`）→ `api/request.js` axios 实例（`baseURL: '/api'`）→ 开发代理 `/api` | [`API-order-export_订单导出_export.md`](../interfaces/API-order-export_订单导出_export.md) | `SERVICE-order-service` / `MODULE-order-export` | 已声明、已实现（存根）、已装配、已暴露；端到端导出链路未实现（Q-H2） | 低（与用户清单“使用中”冲突，Q-H2） | `web-portal/src/api/index.js:4`、`web-portal/src/views/OrderPage.vue:11`；接口主文件登记前端访问路径 `/api/order/export` |

对外关联说明：`API-order-export` 分类沿用接口知识库（用户清单为唯一权威）；调用链实际请求地址与接口主文件登记的前端访问路径一致，故关联对外能力。

### 4.2 页面字段与数据模型影响

| PAGE/ROUTE ID | API ID | SERVICE/MODULE | TABLE 稳定 ID | 页面字段 | API 字段来源 | 表字段 | 读写 | Mapper/SQL 或后端映射 | 证据状态 | 表文档链接 |
|---------------|--------|----------------|---------------|----------|------------|--------|------|----------------------|----------|------------|
| PAGE-order-manage | API-order-ship | SERVICE-order-service / MODULE-order-core | TABLE-t_order | 无展示字段；唯一页面输入为硬编码 `orderId = 1`（路径参数） | 路径参数 `orderId` → `OrderMapper.selectById` 读取状态 → `OrderMapper.updateStatus` 写入 `SHIPPED` | `order_id`、`status` | R + W | `CODE-OrderMapperXml-selectById`（`order_id` 条件）、`CODE-OrderMapperXml-updateStatus`（`status` 更新） | 待确认（页面未展示订单字段，写入链路经 API 后端证据；状态机并发问题见 Q-M11） | [`TABLE-t_order`](../data-models/DB-demo_order/TABLE-t_order.md) |
| PAGE-order-manage | API-order-export | SERVICE-order-service / MODULE-order-export | 未建立（`TABLE-t_export_file` 无读写实现） | 无（页面未传递任何筛选或导出参数） | 接口实现返回字面量 `taskId`，无请求模型与数据访问 | 待确认 | 待确认 | 未发现 Mapper/SQL 访问 `t_export_file`（Q-M4） | 待确认 | 不适用（`TABLE-t_export_file` 读写链路未确认，不为页面建立表关系） |

- 逐跳证据（发货）：页面 `web-portal/src/views/OrderPage.vue:10` → `API-order-ship` 参数与报文（路径参数 `orderId`）→ 接口主文件登记读写 `TABLE-t_order` → `order-service/src/main/resources/mapper/OrderMapper.xml:4-9`。
- 不得由页面按钮名“发货”直接关联表；上表 R+W 关系仅来自接口主文件与 Mapper 证据。
- `TABLE-t_export_file` 未被导出接口访问（`ExportController#export` 未调用 `ExportService`、无 Mapper），因此不为本页建立该表关系，登记待确认（Q-H2、Q-M4）。

### 4.3 后端服务配置依赖

| PAGE/ROUTE ID | API ID | SERVICE/MODULE | 配置组稳定 ID | 服务配置实体 | 配置键 | 页面影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|---------------|--------|----------------|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| PAGE-order-manage | API-order-ship | SERVICE-order-service | CONFIGGROUP-order-server | SERVICE-order-service | `server.port` | 页面请求目标可达性（服务监听端口） | 开发（fixture 快照）/ default | 服务监听端口为 8083，而前端开发代理仅指向单一目标端点（值 `<redacted>`），两者对应关系未确认；未发现生产网关路径 | 待确认 | [`SERVICE-order-service`](../configurations/SERVICE-order-service.md) |
| PAGE-order-manage | API-order-ship | SERVICE-order-service | CONFIGGROUP-order-datasource | SERVICE-order-service | `spring.datasource.*`（授权快照中缺失） | 发货写入是否具备数据源绑定（影响页面操作结果） | 开发（fixture 快照）/ default | 授权配置中未发现数据源键，仅 `pom.xml` 声明 MySQL 驱动与 Mapper 访问 `t_order`，绑定与生效条件无法证明 | 待确认（Q-M6） | [`SERVICE-order-service`](../configurations/SERVICE-order-service.md) |

- 未发现后端 Feature Flag 或开关经 API 响应控制本页按钮显隐或启用条件；两个按钮始终渲染（`web-portal/src/views/OrderPage.vue:4-5`）。
- `CONFIGGROUP-order-rabbitmq` 与订单事件（`EVENT-order-paid`）不参与本页调用链（页面未触发支付或事件），不建立页面配置依赖。

### 4.4 前端直接配置

| PAGE/ROUTE ID | 前端应用或模块 | 配置键 | 页面影响 | 环境/构建模式 | 前端绑定与生效条件 | 证据状态 | 来源 |
|---------------|----------------|--------|----------|---------------|--------------------|----------|------|
| PAGE-order-manage | MODULE-web-portal-api（SERVICE-web-portal） | axios `baseURL`（值 `/api`） | 本页两个请求的统一前缀 | 全部模式（开发/构建产物） | `web-portal/src/api/request.js:3` 创建实例时注入 | 已确认 | `web-portal/src/api/request.js:1-4` |
| PAGE-order-manage | SERVICE-web-portal（构建配置，非配置基线） | `server.proxy['/api'].target` | 开发模式下本页请求的转发目标 | 开发服务器（`npm run dev`） | `web-portal/vite.config.js:3` 声明 `/api` 代理且不重写前缀；生产构建不包含该代理 | 已确认 | `web-portal/vite.config.js:1-4` |

> 本表仅记录前端代码直接读取的配置，不链接 `configurations/` 后端服务配置实体。`web-portal` 不在配置授权范围内。

### 4.5 未匹配接口候选

| PAGE ID | 候选 API ID | 已知方法与路径 | 调用位置 | 接口主文件 | 状态 | 可信度 | 待确认项 |
|---------|-------------|----------------|----------|------------|------|--------|----------|
| PAGE-order-manage | 无 | - | - | 未登记 | 不适用 | - | 本页 2 个 REST 调用已按 Method + 标准路径唯一匹配 `API-order-ship`、`API-order-export`，无候选 |

- 待确认（非候选）：`API-order-export` 端到端导出链路未实现（无文件生成、无 `t_export_file` 登记、无结果查询方式），页面点击“导出订单”后的业务结果不可确定（Q-H2）。该缺口属已登记能力的实现问题，不作为页面侧未登记接口候选。

## 5. 权限与导航

- 路由元数据：无 `meta`、无 `roles`/`permissions`/`hidden`（`web-portal/src/main.js:12`）。
- 路由守卫：未发现 `beforeEach`/`beforeResolve`/`afterEach`（`web-portal/src/main.js:8-15`）。
- 登录状态与 Token 恢复：未发现登录页、Token 存储或恢复流程。
- 菜单与导航：根组件仅 `<router-view />`（`web-portal/src/App.vue:1`），本页只能通过直接输入 URL（`/orders`）进入。
- 按钮与操作级权限：两个按钮均为原生 `button` + `@click`，无权限判断、禁用条件或二次确认（`web-portal/src/views/OrderPage.vue:4-5`）；发货与导出属高影响操作，前端未见权限控制。
- 结论：前端未做访问控制；`用户有权发货` 属权限候选，必须由后端鉴权证据确认，而当前未发现任何后端鉴权实现（Q-M8、Q-M12）。

## 6. 状态管理与请求封装

```text
PAGE-order-manage（/orders）
→ OrderPage.vue#ship（web-portal/src/views/OrderPage.vue:10）
→ api/index.js#shipOrder（web-portal/src/api/index.js:4）
→ api/request.js axios 实例（baseURL: '/api'，web-portal/src/api/request.js:3）
→ 开发代理 /api（web-portal/vite.config.js:3，前缀不重写）
→ POST /api/order/{orderId}/ship → API-order-ship

PAGE-order-manage（/orders）
→ OrderPage.vue#exportAll（web-portal/src/views/OrderPage.vue:11）
→ api/index.js#exportOrder（web-portal/src/api/index.js:4）
→ api/request.js axios 实例（同上）
→ POST /api/order/export → API-order-export
```

- 规范化：`/order/${orderId}/ship` 合并 `baseURL: '/api'` 后为 `POST /api/order/1/ship`，规范化为 `POST /api/order/{orderId}/ship`；`/order/export` 合并后为 `POST /api/order/export`。
- 无 Store、Hook、Composable 或 Service 层，无拦截器；两个请求的响应与异常均未被页面处理（无 `try/catch`、无提示）。
- 生产环境网关路径未提供，生产标准路径按开发链路记录。

## 7. 动态路由和运行时限制

- 本页路由在构建时确定，无后端菜单或权限转换参与，不存在动态路由解析。
- 未执行前端构建与开发服务器（只读离线分析，依赖需联网解析，Q-L3）；仓库内未发现 Vite 入口 `index.html` 与 `#app` 挂载点，应用能否构建/启动未确认（Q-H3）。
- 页面仅触发操作、不展示结果，运营人员无法在本页判断发货或导出结果（无响应处理），实际行为待运行时确认。

## 8. 孤立与不可达页面

- 本页不是孤立页面：存在静态路由声明与静态导入组件（`web-portal/src/main.js:5,12`）。
- 无菜单、无重定向、无其他页面跳转入口（`web-portal/src/App.vue:1`）。
- 未发现同一组件被其他路由引用，未发现被注释或废弃的路由。
- 运行时不可达风险：应用入口 HTML 缺失（Q-H3），本页可达性不能由静态证据证明。

## 9. 来源冲突

- `user-input/page-scope.md:6` 声明路由来源为“代码静态路由（src/main.js）”，与代码证据一致，无冲突。
- `user-input/api-scope.md:13` 声明 `API-order-export` 状态“使用中”、调用方“客户端”，本页确实调用该接口（`web-portal/src/api/index.js:4`），但代码侧仅有存根实现；冲突已由接口阶段登记为 Q-H2，本页沿用该结论并标记可信度低。
- `interfaces/` 中 `API-order-ship`、`API-order-export` 均登记调用方含 `web-portal` 订单管理页，与本页证据一致。

## 10. 待人工确认

- Q-H2：`API-order-export` 端到端导出链路未实现，导出按钮的业务结果不可确定。
- Q-H3：`web-portal` 缺少 Vite 入口 `index.html`，应用能否构建/启动未确认，影响本页可达性。
- Q-M6：`order-service` 授权配置缺数据源键，发货写入的绑定与生效条件未确认。
- Q-M11：发货读状态与写状态非事务、无乐观锁，并发重复发货风险未确认。
- Q-M12：前端无鉴权与导航入口，高影响操作（发货/导出）的访问控制未确认。
- Q-L7：页面硬编码 `orderId = 1`，是否应支持订单选择未确认。
- Q-L4：开发代理单一目标端点与三个后端服务端口的对应关系未确认。

## 11. 完整追溯关系

```text
ROUTE-web-portal-orders（/orders）
→ PAGE-order-manage（web-portal/src/views/OrderPage.vue）
→ API-order-ship（POST /api/order/{orderId}/ship）→ ../interfaces/API-order-ship_订单发货_ship.md
→ SERVICE-order-service / MODULE-order-core
├─ TABLE-t_order（R+W：order_id、status）→ CODE-OrderMapperXml-selectById / CODE-OrderMapperXml-updateStatus → ../data-models/DB-demo_order/TABLE-t_order.md
└─ CONFIGURATION：CONFIGGROUP-order-server（server.port）、CONFIGGROUP-order-datasource（授权配置缺键，待确认）→ ../configurations/SERVICE-order-service.md

→ API-order-export（POST /api/order/export）→ ../interfaces/API-order-export_订单导出_export.md
→ SERVICE-order-service / MODULE-order-export
└─ TABLE：未建立（t_export_file 无读写实现，Q-H2/Q-M4）
```

- 页面侧前端配置（axios `baseURL`、开发代理）见 4.4，不链接后端配置实体。
