# web-portal

## 职责与边界

- 稳定 ID：`SERVICE-web-portal`；类型：Vue3 单页应用（Vite 构建）。
- 职责：运营门户页面与统一请求封装，覆盖用户、账户、订单三个视图 [代码证据]（`web-portal/src/main.js:8-15`、`web-portal/src/api/index.js:1-4`）。
- 边界内：前端路由、页面渲染、对后端 HTTP 调用封装。
- 边界外：业务规则实现、数据存储、鉴权逻辑（未发现）。
- 数据存储：前端不直接访问数据库。

## 模块与入口

| 模块 ID | 职责 | 关键文件 | 证据 |
|---------|------|----------|------|
| MODULE-web-portal-app | 应用装配与静态路由 | `main.js`、`App.vue` | `web-portal/src/main.js:1-16`、`web-portal/src/App.vue:1` |
| MODULE-web-portal-api | 统一请求封装与接口封装 | `api/request.js`、`api/index.js` | `web-portal/src/api/request.js:1-4`、`web-portal/src/api/index.js:1-4` |
| MODULE-web-portal-views | 页面视图 | `views/UserList.vue`、`views/AccountPage.vue`、`views/OrderPage.vue` | `web-portal/src/views/*.vue` |

| 入口类型 | 入口 | 说明 | 证据 |
|----------|------|------|------|
| 应用入口 | `web-portal/src/main.js` | `createApp(App).use(router).mount('#app')` | `web-portal/src/main.js:16` |
| 路由 | `/users`、`/orders`、`/accounts` | 代码静态路由（`createWebHistory`），路由来源 `src/main.js` | `web-portal/src/main.js:10-14`、`user-input/page-scope.md` |
| 构建入口 | `package.json` scripts：`dev`/`build`（vite） | 未声明锁文件，依赖为 caret 范围 | `web-portal/package.json:4-6` |

## 数据模型

- 未发现前端直接的数据模型实体；前端通过 HTTP 调用后端服务获取数据。
- 页面使用的字段（`userId`、`userName`、`mobile`、`accountNo`、`balance`、`orderId`）来源于后端实体，字段级事实见 `data-models/` 下对应逻辑表文档。
- 前端字段与后端逻辑表的关联证据：`web-portal/src/views/UserList.vue:4`、`AccountPage.vue:4`、`api/index.js:2-4`。

## 配置

- 配置状态：不在授权范围。`scope.configurations.selected` 为 user-service、account-service、order-service，`file_rule_summary` 为“仅 `src/main/resources/application.yml`”，未授权本工程。
- 因此本工程不生成配置文档，也不读取其构建配置文件内容作为配置基线。
- 已观察到的构建期证据（非配置基线）：`web-portal/vite.config.js` 定义开发服务器代理路径前缀（目标为内部端点，值 `<redacted>`），`web-portal/package.json:4-6` 定义脚本与依赖范围；相关风险见 `open-questions.md` Q-L4。

## 中间件

- 未发现前端直接依赖的中间件或客户端库（`web-portal/package.json:5-6` 仅列 vue、vue-router、axios、vite）。
- 通过 HTTP 间接依赖后端服务与其中间件，见 `services/SERVICE-order-service.md`、`services/SERVICE-account-service.md`。

## API

- 阶段状态：已验证为空（api）
- 原因：本工程为前端 SPA（Vite + Vue3），不暴露 REST/RPC/消息/文件/任务能力；`web-portal/package.json` 仅声明 vue、vue-router、axios、vite，未发现服务端框架依赖。
- 调用关系（本工程为调用方，非提供方）：`GET /api/user/basic/{userId}`（`API-user-basic`）、`GET /api/account/{userId}`（`API-account-query`）、`POST /api/order/{orderId}/ship`（`API-order-ship`）、`POST /api/order/export`（`API-order-export`）。
- 证据：`web-portal/src/api/request.js:3`、`web-portal/src/api/index.js:1-4`、`web-portal/package.json:4-6`；总索引 `interfaces/README.md`。

## 页面

- 阶段状态：已分析（pages）
- 页面导航（本应用承载）：

| PAGE 稳定 ID | ROUTE 稳定 ID | 路由路径 | 组件 | 页面主文件 |
|--------------|---------------|----------|------|------------|
| `PAGE-user-list` | `ROUTE-web-portal-users` | `/users` | `views/UserList.vue` | [`PAGE-user-list`](../pages/PAGE-user-list.md) |
| `PAGE-order-manage` | `ROUTE-web-portal-orders` | `/orders` | `views/OrderPage.vue` | [`PAGE-order-manage`](../pages/PAGE-order-manage.md) |
| `PAGE-account-query` | `ROUTE-web-portal-accounts` | `/accounts` | `views/AccountPage.vue` | [`PAGE-account-query`](../pages/PAGE-account-query.md) |

- 路由来源：代码静态路由（`web-portal/src/main.js:10-14`）；未发现动态路由、菜单下发、懒加载与路由守卫。
- 限制：未发现鉴权与导航入口（Q-M12）；仓库内未发现 Vite 入口 `index.html`，应用可构建/可启动未确认（Q-H3）。
- 证据：`web-portal/src/main.js:8-16`、`web-portal/src/views/UserList.vue:1-13`、`web-portal/src/views/AccountPage.vue:1-13`、`web-portal/src/views/OrderPage.vue:1-12`；页面索引 `pages/README.md`。

## 横切机制

| 机制 | 状态 | 证据 |
|------|------|------|
| 统一请求封装 | 已确认（axios 实例统一 baseURL 与超时） | `web-portal/src/api/request.js:1-4` |
| 前端路由守卫/鉴权 | 未发现 | `web-portal/src/main.js:8-15` |
| 全局错误处理 | 未发现（无拦截器） | `web-portal/src/api/request.js` |
| 状态管理 | 未发现（无 Pinia/Vuex 依赖） | `web-portal/package.json:5-6` |

## 构建验证

| 场景 | 命令 | 状态 | 来源 |
|------|------|------|------|
| 开发服务器 | `npm run dev`（工作目录 `web-portal`） | 未执行（只读分析；需联网安装依赖） | `web-portal/package.json:4` |
| 构建 | `npm run build`（工作目录 `web-portal`） | 未执行（同上） | `web-portal/package.json:4` |
| 测试/静态检查 | 未发现测试脚本或 lint 配置 | 不适用 | `web-portal/package.json` |

## 证据导航

- 应用装配与路由：`web-portal/src/main.js:8-16`
- 请求封装：`web-portal/src/api/request.js`、`web-portal/src/api/index.js`
- 页面：`web-portal/src/views/UserList.vue`、`AccountPage.vue`、`OrderPage.vue`
- 构建配置：`web-portal/package.json`、`web-portal/vite.config.js`
- 相关文档：`services/README.md`、`development-guide.md`、`open-questions.md`
