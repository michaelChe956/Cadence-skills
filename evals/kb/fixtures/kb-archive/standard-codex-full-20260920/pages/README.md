# 页面能力索引

## 元数据

| 项目 | 内容 |
|------|------|
| 执行模式 | 全量（`scope.pages.status: 全量`，来源 `user-input/page-scope.md`） |
| 前端应用范围 | `SERVICE-web-portal`（Vue 3 单页应用：vue ^3.4.0、vue-router ^4.3.0、axios ^1.6.0、vite ^5.2.0） |
| 路由来源 | 代码静态路由（`web-portal/src/main.js:8-15`）；未发现后端菜单下发、运行时注入、文件系统路由与微前端注册 |
| 页面粒度 | 应用级（`scope.pages.selected: ["web-portal"]`）：应用概览 + 路由树 + 路由清单 + 全部页面实体 |
| 基线提交 | 1f867b9fcdf95f2e11808454898f333d7d512e90（分支 `master`） |
| 分析时间 | 2026-09-20 |
| 页面与路由数量 | 页面 3、路由 3（`PAGE-user-list`/`ROUTE-web-portal-users`、`PAGE-order-manage`/`ROUTE-web-portal-orders`、`PAGE-account-query`/`ROUTE-web-portal-accounts`） |
| API 关联 | 页面发起 4 个 REST 调用，全部匹配已登记稳定 API ID；`API-CANDIDATE-*` 候选 0 |
| 阶段状态 | 本阶段（`pages`）分析完成；`overview`、`global-validation` 未执行 |
| 工具与边界 | 只读文本检索与定向阅读；未运行前端构建、开发服务器或任何后端进程；未连接数据库、中间件或远程环境；敏感值统一 `<redacted>` |

> 本索引只保存路由树、稳定 ID、状态、证据与文档链接，不复制页面组件源码或接口明细；单页面能力见 `pages/PAGE-*.md`。

## 1. 前端应用与路由来源

- 应用稳定 ID：`SERVICE-web-portal`；相关模块：`MODULE-web-portal-app`（应用装配与静态路由）、`MODULE-web-portal-api`（统一请求封装）、`MODULE-web-portal-views`（页面视图）。
- 应用形态：单入口单页应用，入口 `web-portal/src/main.js`（`main.js:16` 执行 `createApp(App).use(router).mount('#app')`），根组件 `web-portal/src/App.vue:1` 仅含 `<router-view />`。
- 路由库与装配：vue-router 4，`main.js:8-15` 使用 `createRouter({ history: createWebHistory(), routes: [...] })` 定义并装配；三条路由组件均为静态 `import`（`main.js:4-6`），无懒加载、无嵌套路由、无 Layout 出口。
- 请求封装：`web-portal/src/api/request.js:3` 创建 axios 实例（`baseURL: '/api'`、`timeout: 10000`），`web-portal/src/api/index.js:2-4` 导出 4 个接口函数；无拦截器、无全局错误处理、无 Token 注入。
- 状态管理：未发现 Pinia/Vuex 或全局 Store（`web-portal/package.json:5-6`），页面状态由组件内 `ref` 持有。
- 环境与代理：`web-portal/vite.config.js:3` 仅声明开发服务器 `/api` 代理（目标端点值 `<redacted>`）；未发现 `.env*`、构建时 Feature Flag、生产网关或反向代理配置。
- 路由来源分类结论：全部为“代码静态路由”；未发现后端菜单/权限接口、`router.addRoute`/`addRoutes`、文件系统路由或微前端基座注册，因此不存在运行时路由解析算法可分析。
- 用户输入核对：`user-input/page-scope.md:6` 声明路由来源为“代码静态路由（src/main.js）”，与代码证据一致。

## 2. 路由树

```text
（无父级、无 Layout、无嵌套出口；三条平级静态路由）
├─ /users    → ROUTE-web-portal-users    → PAGE-user-list     → views/UserList.vue
├─ /orders   → ROUTE-web-portal-orders   → PAGE-order-manage  → views/OrderPage.vue
└─ /accounts → ROUTE-web-portal-accounts → PAGE-account-query → views/AccountPage.vue
```

- 无根路由 `/`、无通配路由、无 404 视图、无 `redirect`、无路由别名、无动态参数与可选参数。
- 路由未声明 `name` 与 `meta`，因此无路由名称寻址、无 KeepAlive/缓存元数据、无路由级权限声明。
- 未匹配路径不会渲染任何业务视图（`App.vue:1` 仅有 `router-view`）。

## 3. 路由清单

| ROUTE 稳定 ID | 路径 | 来源 | 父级或 Layout | 组件 | 懒加载 | meta/权限 | 装配状态 | 可达性 | 证据 |
|---------------|------|------|----------------|------|--------|-----------|----------|--------|------|
| ROUTE-web-portal-users | `/users` | 代码静态路由 | 无 | `views/UserList.vue` | 否（静态 import） | 无 `meta`、无权限声明 | 已装配（`router` 已 `use`） | 待确认：无菜单/导航入口，仅 URL 直达；应用入口 HTML 缺失 | `web-portal/src/main.js:4,11`、`web-portal/src/App.vue:1` |
| ROUTE-web-portal-orders | `/orders` | 代码静态路由 | 无 | `views/OrderPage.vue` | 否 | 无 `meta`、无权限声明 | 已装配 | 同上 | `web-portal/src/main.js:5,12` |
| ROUTE-web-portal-accounts | `/accounts` | 代码静态路由 | 无 | `views/AccountPage.vue` | 否 | 无 `meta`、无权限声明 | 已装配 | 同上 | `web-portal/src/main.js:6,13` |

- 未发现被注释、废弃或重复声明的路由；未发现指向缺失组件的路由；未发现菜单指向未知路由（无菜单来源）。
- 路由守卫：未发现 `beforeEach`/`beforeResolve`/`afterEach`（`main.js:8-15`）。

## 4. 页面清单

| PAGE 稳定 ID | 页面名称 | ROUTE 稳定 ID | 路径 | 组件 | 状态 | 主文件 | 证据 |
|--------------|----------|---------------|------|------|------|--------|------|
| PAGE-user-list | 用户列表 | ROUTE-web-portal-users | `/users` | `web-portal/src/views/UserList.vue` | 已声明、组件存在、已装配；可达性待确认 | [`PAGE-user-list`](./PAGE-user-list.md) | `web-portal/src/main.js:11`、`web-portal/src/views/UserList.vue:1-13` |
| PAGE-order-manage | 订单管理 | ROUTE-web-portal-orders | `/orders` | `web-portal/src/views/OrderPage.vue` | 已声明、组件存在、已装配；可达性待确认 | [`PAGE-order-manage`](./PAGE-order-manage.md) | `web-portal/src/main.js:12`、`web-portal/src/views/OrderPage.vue:1-12` |
| PAGE-account-query | 账户查询 | ROUTE-web-portal-accounts | `/accounts` | `web-portal/src/views/AccountPage.vue` | 已声明、组件存在、已装配；可达性待确认 | [`PAGE-account-query`](./PAGE-account-query.md) | `web-portal/src/main.js:13`、`web-portal/src/views/AccountPage.vue:1-13` |

> “可达”只表示存在路由与组件装配；“用户有权访问”未得到任何前端或后端鉴权证据（见第 6 节、Q-M8、Q-M12）。应用入口 HTML（`index.html` 与 `#app` 挂载点）在仓库内未发现，运行时可达性据此标记待确认（Q-H3）。

## 5. 页面与 API 概览

| PAGE 稳定 ID | API 稳定 ID | 分类 | 方法与标准路径 | 接口主文件 | SERVICE/MODULE | 状态 | 可信度 |
|--------------|-------------|------|----------------|------------|----------------|------|--------|
| PAGE-user-list | API-user-basic | 对外 | `GET /api/user/basic/{userId}` | [`API-user-basic`](../interfaces/API-user-basic_查询用户基本信息_queryBasic.md) | `SERVICE-user-service` / `MODULE-user-basic` | 已登记、已实现、已装配、已暴露 | 高 |
| PAGE-order-manage | API-order-ship | 对内 | `POST /api/order/{orderId}/ship` | [`API-order-ship`](../interfaces/API-order-ship_订单发货_ship.md) | `SERVICE-order-service` / `MODULE-order-core` | 已登记、已实现、已装配、已暴露 | 高 |
| PAGE-order-manage | API-order-export | 对外 | `POST /api/order/export` | [`API-order-export`](../interfaces/API-order-export_订单导出_export.md) | `SERVICE-order-service` / `MODULE-order-export` | 已登记、已实现（存根）、已装配、已暴露；端到端导出链路未实现（Q-H2） | 低 |
| PAGE-account-query | API-account-query | 对内 | `GET /api/account/{userId}` | [`API-account-query`](../interfaces/API-account-query_账户信息查询_queryAccount.md) | `SERVICE-account-service` / `MODULE-account-core` | 已登记、已实现、已装配、已暴露 | 中（响应字段映射依赖隐式驼峰，Q-M3） |

- 4 个页面调用全部在接口索引中按 Method + 标准路径唯一匹配，未登记候选 `API-CANDIDATE-*`。
- 对外分类沿用接口知识库登记（`interfaces/README.md`）；页面调用链实际指向的地址与接口主文件登记的“前端访问路径”一致，故可关联对外能力（未按业务名称相似度匹配）。

## 6. 权限与导航

| 机制 | 结论 | 证据 |
|------|------|------|
| 登录状态与 Token 恢复 | 未发现登录页、Token 存储或恢复流程 | `web-portal/src/main.js:1-16`、`web-portal/package.json:5` |
| 全局/局部路由守卫 | 未发现 | `web-portal/src/main.js:8-15` |
| 角色、权限码、菜单码、数据权限 | 未发现（无 `meta.roles`/`meta.permissions`） | `web-portal/src/main.js:11-13` |
| 白名单、免登录页、错误页 | 未发现（无 404/403 路由） | `web-portal/src/main.js:10-14` |
| 后端菜单转换逻辑 | 未发现（无菜单接口调用） | `web-portal/src/api/index.js:1-4` |
| 按钮/操作级权限 | 未发现（按钮无 `disabled` 或权限判断） | `web-portal/src/views/OrderPage.vue:4-5`、`web-portal/src/views/UserList.vue:5` |
| 菜单与导航入口 | 未发现菜单、链接或重定向入口 | `web-portal/src/App.vue:1` |

- 前端未实现任何访问控制，三个页面在浏览器中均可通过直接输入 URL 触发；这不构成后端鉴权的证明，也不代表未授权用户在生产环境可访问（部署层保护未提供证据，见 Q-M12、Q-M8）。

## 7. 状态管理与请求封装

三个页面的调用链与规范化结果（完整链路见各页面文档第 6 节）：

```text
用户点击按钮
→ 页面组件事件（views/UserList.vue:12、views/AccountPage.vue:12、views/OrderPage.vue:10-11）
→ api/index.js 接口函数（web-portal/src/api/index.js:2-4）
→ api/request.js axios 实例（baseURL: '/api'，web-portal/src/api/request.js:3）
→ 开发代理 /api（web-portal/vite.config.js:3，前缀不重写）
→ HTTP Method + 标准 Path
→ 接口稳定 API ID（interfaces/README.md）与接口主文件
```

| 页面 | 源码调用 | 合并 baseURL 后 | 规范化标准路径 |
|------|----------|------------------|----------------|
| PAGE-user-list | `request.get('/user/basic/${userId}')` | `GET /api/user/basic/1` | `GET /api/user/basic/{userId}` |
| PAGE-account-query | `request.get('/account/${userId}')` | `GET /api/account/1` | `GET /api/account/{userId}` |
| PAGE-order-manage | `request.post('/order/${orderId}/ship')` | `POST /api/order/1/ship` | `POST /api/order/{orderId}/ship` |
| PAGE-order-manage | `request.post('/order/export')` | `POST /api/order/export` | `POST /api/order/export` |

- 未发现 Store、Hook、Composable、Thunk 或 Service 层；页面组件直接调用 `api/index.js` 导出的函数。
- 开发代理把 `/api` 转发到单一目标端点（值 `<redacted>`）且不重写前缀，因此匹配接口知识库时保留 `/api`；三个后端服务监听端口不同（8081/8082/8083）而代理仅一个目标，映射关系未确认（Q-L4）。
- 生产环境网关或反向代理路径未提供，生产标准路径按开发链路记录。

## 8. 动态路由和运行时限制

- 无动态路由来源，无运行时路由注入算法，因此不存在“静态代码无法还原的动态路由表”。
- 未执行前端构建与开发服务器（只读离线分析，依赖需联网安装，Q-L3）；`web-portal` 未发现 Vite 入口 `index.html` 与 `#app` 挂载点（全仓未发现 `index.html`），应用能否构建/启动未确认（Q-H3）。
- 生产环境菜单、部署入口、访问控制与网关路径未提供，页面在目标环境的实际可达性无法由静态代码证明。

## 9. 孤立与不可达页面

- 未发现仅存在组件而无路由的视图文件：`views/` 下 3 个视图均有对应静态路由（`web-portal/src/main.js:11-13`）。
- 未发现被注释或废弃的路由，未发现指向缺失组件的路由，未发现同一组件被多路由复用。
- 未发现 Demo、Storybook、开发工具页面（`web-portal/package.json:5-6` 无相关依赖）。

## 10. 来源冲突

| 对象 | 来源 A | 来源 B | 冲突或限制 | 处理 |
|------|--------|--------|------------|------|
| 路由来源声明 | `user-input/page-scope.md:6`（代码静态路由，src/main.js） | `web-portal/src/main.js:10-14` | 一致，无冲突 | 按代码证据登记 3 条路由 |
| 页面调用方登记 | `interfaces/README.md`（`API-user-basic`、`API-order-export`、`API-account-query`、`API-order-ship` 调用方含 web-portal 页面） | `web-portal/src/views/UserList.vue:12`、`OrderPage.vue:10-11`、`AccountPage.vue:12`、`src/api/index.js:2-4` | 一致，函数与行号可对应 | 直接关联稳定 API ID |
| 应用入口 | `web-portal/package.json:4`（存在 `dev`/`build` 脚本） | 仓库内未发现 `index.html`、`#app` 挂载点 | 无法确认应用可构建/可启动 | 标记待确认（Q-H3），不补造入口文件 |

## 11. 待人工确认

- Q-H3：`web-portal` 缺少 Vite 入口 `index.html`（无 `#app` 挂载点），应用能否构建/启动未确认。
- Q-M8、Q-M12：后端与前端均未发现鉴权实现，页面访问控制边界未确认。
- Q-M3：账户页面响应字段依赖隐式驼峰映射，展示字段可能为空。
- Q-L1、Q-L4、Q-L7：依赖版本未锁定、开发代理目标与三服务端口映射未确认、页面硬编码资源 ID 未确认。
- 完整清单见 `open-questions.md`。

## 12. 证据导航

- 应用装配与路由：`web-portal/src/main.js:8-16`、`web-portal/src/App.vue:1`
- 请求封装与接口函数：`web-portal/src/api/request.js:1-4`、`web-portal/src/api/index.js:1-4`
- 页面视图：`web-portal/src/views/UserList.vue:1-13`、`web-portal/src/views/OrderPage.vue:1-12`、`web-portal/src/views/AccountPage.vue:1-13`
- 构建配置：`web-portal/package.json:4-6`、`web-portal/vite.config.js:1-4`
- 相关文档：`interfaces/README.md`、`services/SERVICE-web-portal.md`、`services/README.md`、`evidence/traceability-matrix.md`、`open-questions.md`
