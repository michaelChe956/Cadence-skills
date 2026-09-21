# 页面能力 PAGE-account-query 账户查询

## 文档元数据

- 生成时间：2026-09-20
- Git 分支：master
- 基线提交：1f867b9fcdf95f2e11808454898f333d7d512e90
- 执行模式：初始化续跑（`coverage.initialization.status: in_progress`，本次执行 `pages` 阶段）
- 前端应用：`SERVICE-web-portal`（`MODULE-web-portal-app`、`MODULE-web-portal-api`、`MODULE-web-portal-views`）
- 页面稳定 ID：`PAGE-account-query`；路由稳定 ID：`ROUTE-web-portal-accounts`
- 动态路由限制：本页为代码静态路由（`web-portal/src/main.js:13`）；未发现后端菜单下发、运行时 `addRoute` 或权限路由转换，生产入口与菜单未提供

## 1. 前端应用与路由来源

- 应用装配：`web-portal/src/main.js:8-15`（`createRouter` + `createWebHistory`），`web-portal/src/main.js:16` 挂载 `#app`。
- 路由声明：`web-portal/src/main.js:13` → `{ path: '/accounts', component: AccountPage }`；无 `name`、`meta`、`redirect`、`alias`、动态参数、懒加载与嵌套。
- 组件：`web-portal/src/views/AccountPage.vue:1-13`，由 `web-portal/src/main.js:6` 静态导入。
- 路由来源分类：代码静态路由；未发现其他来源（`user-input/page-scope.md:6` 声明与代码一致）。

## 2. 路由树

```text
（无父级与 Layout；本路由为平级静态路由）
/accounts → ROUTE-web-portal-accounts → PAGE-account-query → views/AccountPage.vue
```

- 无父子关系、无重定向、无别名、无动态参数。
- 应用未定义根路由 `/`、通配路由与 404 视图，未匹配路径不渲染任何业务视图。

## 3. 页面能力清单

| PAGE ID | ROUTE ID | 路径 | 页面用途 | 组件 | 权限 | 状态 | API 主文件 | 证据 |
|---------|----------|------|----------|------|------|------|------------|------|
| PAGE-account-query | ROUTE-web-portal-accounts | `/accounts` | 按用户标识查询并展示账户号与余额 | `web-portal/src/views/AccountPage.vue` | 未发现（无 `meta`、无守卫、无权限码） | 已声明、组件存在、已装配；可达性待确认（无菜单入口、应用入口 HTML 缺失） | [`API-account-query`](../interfaces/API-account-query_账户信息查询_queryAccount.md) | `web-portal/src/main.js:6,13`、`web-portal/src/views/AccountPage.vue:1-13` |

- 页面操作：无自动请求；点击“查询账户”按钮触发 `load()`（`web-portal/src/views/AccountPage.vue:5,12`）。
- 展示字段：`acct.accountNo`、`acct.balance`（`web-portal/src/views/AccountPage.vue:4`）；账户状态 `status` 未展示。
- 输入参数：未发现表单或筛选条件；请求参数为硬编码 `1`（`web-portal/src/views/AccountPage.vue:12`），登记 Q-L7。
- 状态来源：组件内 `acct` ref（`web-portal/src/views/AccountPage.vue:11`），无 Store/Hook/Composable。
- 上传、下载、WebSocket 与消息能力：未发现。
- 生命周期与缓存：无 `onMounted` 自动加载、无 KeepAlive；无 Feature Flag 与环境分支。

## 4. 页面与 API 映射

### 4.1 已匹配接口

| PAGE ID | API ID | 分类 | 方法与标准路径 | 调用位置 | 请求封装、Store 或 Hook | 接口主文件 | SERVICE/MODULE | 状态 | 可信度 | 证据 |
|---------|--------|------|----------------|----------|-------------------------|------------|----------------|------|--------|------|
| PAGE-account-query | API-account-query | 对内 | `GET /api/account/{userId}` | `web-portal/src/views/AccountPage.vue:12`（`queryAccount(1)`） | 页面 → `api/index.js#queryAccount`（`web-portal/src/api/index.js:3`）→ `api/request.js` axios 实例（`baseURL: '/api'`）→ 开发代理 `/api` | [`API-account-query_账户信息查询_queryAccount.md`](../interfaces/API-account-query_账户信息查询_queryAccount.md) | `SERVICE-account-service` / `MODULE-account-core` | 已实现、已装配、已暴露 | 中（响应字段映射依赖隐式驼峰，Q-M3） | `web-portal/src/api/index.js:3`、`web-portal/src/views/AccountPage.vue:12` |
| PAGE-account-query | 未发现其他调用 | - | - | - | - | 未登记 | - | - | - | 页面组件内仅一处请求调用 |

分类说明：`API-account-query` 在接口知识库中登记为对内能力（用户对外清单未登记，Q-M7）；本页按接口索引分类关联，未因业务名称相似而升级为对外能力。

### 4.2 页面字段与数据模型影响

| PAGE/ROUTE ID | API ID | SERVICE/MODULE | TABLE 稳定 ID | 页面字段 | API 字段来源 | 表字段 | 读写 | Mapper/SQL 或后端映射 | 证据状态 | 表文档链接 |
|---------------|--------|----------------|---------------|----------|------------|--------|------|----------------------|----------|------------|
| PAGE-account-query | API-account-query | SERVICE-account-service / MODULE-account-core | TABLE-t_user_account | 展示 `accountNo`、`balance` | 响应为 `AccountEntity` 直接序列化（`userId`、`accountNo`、`balance`、`status`）；字段映射依赖隐式驼峰约定 | `account_no`、`balance` | R | `CODE-AccountMapperXml-selectByUserId`（`SELECT *`，未维护 `resultMap`） | 待确认（`account_no → accountNo` 隐式映射无显式证据，Q-M3） | [`TABLE-t_user_account`](../data-models/DB-demo_account/TABLE-t_user_account.md) |

- 逐跳证据：页面展示绑定 `web-portal/src/views/AccountPage.vue:4` → 接口响应模型（`API-account-query` 参数与报文）→ 接口主文件登记只读表 `TABLE-t_user_account` → `account-service/src/main/resources/mapper/AccountMapper.xml:4-7`。
- 页面未展示 `status`，不登记该字段的页面影响；`balance` 的展示受表注释业务规则（余额不可为负）影响，但该规则未在代码中实现（`data-models/DB-demo_account/TABLE-t_user_account.md` 第 9 节）；规则卡 `business/rules/RULE-account-balance-non-negative.md`。

### 4.3 后端服务配置依赖

| PAGE/ROUTE ID | API ID | SERVICE/MODULE | 配置组稳定 ID | 服务配置实体 | 配置键 | 页面影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|---------------|--------|----------------|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| PAGE-account-query | API-account-query | SERVICE-account-service | CONFIGGROUP-account-server | SERVICE-account-service | `server.port` | 页面请求目标可达性（服务监听端口） | 开发（fixture 快照）/ default | 服务监听端口为 8082，而前端开发代理仅指向单一目标端点（值 `<redacted>`），两者对应关系未确认；未发现生产网关路径 | 待确认 | [`SERVICE-account-service`](../configurations/SERVICE-account-service.md) |

- 未登记 `CONFIGGROUP-account-datasource` 与 `CONFIGGROUP-account-reconcile`：前者控制服务端数据访问（页面仅经 API 响应间接受影响），后者属对账定时任务（与本页无调用链证据），均不满足“直接控制页面/路由/权限/请求/展示行为”的记录条件。
- 未发现后端 Feature Flag 或开关经 API 响应控制本页展示或启用条件。

### 4.4 前端直接配置

| PAGE/ROUTE ID | 前端应用或模块 | 配置键 | 页面影响 | 环境/构建模式 | 前端绑定与生效条件 | 证据状态 | 来源 |
|---------------|----------------|--------|----------|---------------|--------------------|----------|------|
| PAGE-account-query | MODULE-web-portal-api（SERVICE-web-portal） | axios `baseURL`（值 `/api`） | 本页请求的统一前缀 | 全部模式（开发/构建产物） | `web-portal/src/api/request.js:3` 创建实例时注入 | 已确认 | `web-portal/src/api/request.js:1-4` |
| PAGE-account-query | SERVICE-web-portal（构建配置，非配置基线） | `server.proxy['/api'].target` | 开发模式下本页请求的转发目标 | 开发服务器（`npm run dev`） | `web-portal/vite.config.js:3` 声明 `/api` 代理且不重写前缀；生产构建不包含该代理 | 已确认 | `web-portal/vite.config.js:1-4` |

> 本表仅记录前端代码直接读取的配置，不链接 `configurations/` 后端服务配置实体。`web-portal` 不在配置授权范围内。

### 4.5 未匹配接口候选

| PAGE ID | 候选 API ID | 已知方法与路径 | 调用位置 | 接口主文件 | 状态 | 可信度 | 待确认项 |
|---------|-------------|----------------|----------|------------|------|--------|----------|
| PAGE-account-query | 无 | - | - | 未登记 | 不适用 | - | 本页 1 个 REST 调用已按 Method + 标准路径唯一匹配 `API-account-query`，无候选 |

## 5. 权限与导航

- 路由元数据：无 `meta`、无 `roles`/`permissions`/`hidden`（`web-portal/src/main.js:13`）。
- 路由守卫：未发现 `beforeEach`/`beforeResolve`/`afterEach`（`web-portal/src/main.js:8-15`）。
- 登录状态与 Token 恢复：未发现登录页、Token 存储或恢复流程。
- 菜单与导航：根组件仅 `<router-view />`（`web-portal/src/App.vue:1`），本页只能通过直接输入 URL（`/accounts`）进入。
- 按钮与操作级权限：查询按钮无权限判断或禁用条件（`web-portal/src/views/AccountPage.vue:5`）。
- 结论：账户余额属敏感数据，页面无任何前端访问控制，且未发现后端鉴权实现（Q-M8、Q-M12）；访问控制是否由部署层提供未提供证据。

## 6. 状态管理与请求封装

```text
PAGE-account-query（/accounts）
→ AccountPage.vue#load（web-portal/src/views/AccountPage.vue:12）
→ api/index.js#queryAccount（web-portal/src/api/index.js:3）
→ api/request.js axios 实例（baseURL: '/api'，web-portal/src/api/request.js:3）
→ 开发代理 /api（web-portal/vite.config.js:3，前缀不重写）
→ GET /api/account/{userId}
→ API-account-query（../interfaces/API-account-query_账户信息查询_queryAccount.md）
```

- 规范化：源码模板字符串 `/account/${userId}` 不能直接与后端路径比较，合并 `baseURL: '/api'` 后为 `GET /api/account/{userId}`；运行时 `userId = 1` 规范化为路径模板 `{userId}`。
- 无 Store、Hook、Composable 或 Service 层；响应写入组件内 `acct` ref，无缓存与全局状态。
- 生产环境网关路径未提供，生产标准路径按开发链路记录。

## 7. 动态路由和运行时限制

- 本页路由在构建时确定，无后端菜单或权限转换参与，不存在动态路由解析。
- 未执行前端构建与开发服务器（只读离线分析，依赖需联网解析，Q-L3）；仓库内未发现 Vite 入口 `index.html` 与 `#app` 挂载点，应用能否构建/启动未确认（Q-H3）。
- `API-account-query` 响应字段依赖隐式驼峰映射，运行时页面字段是否为空无法由静态代码确认（Q-M3）。

## 8. 孤立与不可达页面

- 本页不是孤立页面：存在静态路由声明与静态导入组件（`web-portal/src/main.js:6,13`）。
- 无菜单、无重定向、无其他页面跳转入口（`web-portal/src/App.vue:1`）。
- 未发现同一组件被其他路由引用，未发现被注释或废弃的路由。
- 运行时不可达风险：应用入口 HTML 缺失（Q-H3），本页可达性不能由静态证据证明。

## 9. 来源冲突

- `user-input/page-scope.md:6` 声明路由来源为“代码静态路由（src/main.js）”，与代码证据一致，无冲突。
- `user-input/api-scope.md:19-22` 将 `GET /api/account/{userId}` 描述为组合能力来源能力（预期登记为对内能力），与接口知识库对内分类一致；`AccountController` 类注释自称“对外能力 API-B”的冲突由接口阶段登记为 Q-M7。
- `interfaces/README.md` 中 `TABLE-t_user_account` 的读服务为 `SERVICE-account-service`，与本页 4.2 链路一致。

## 10. 待人工确认

- Q-H3：`web-portal` 缺少 Vite 入口 `index.html`，应用能否构建/启动未确认，影响本页可达性。
- Q-M3：账户响应字段依赖隐式驼峰映射，`accountNo`/`balance` 展示可能为空。
- Q-M9：组合诉求“全部用户信息”的连接键端到端映射未闭合（本页与用户列表页为组合的两个来源页面）。
- Q-M12：前端无鉴权与导航入口，账户敏感数据的访问控制未确认。
- Q-L7：页面硬编码 `userId = 1`，是否应支持用户输入未确认。
- Q-L4：开发代理单一目标端点与三个后端服务端口的对应关系未确认。

## 11. 完整追溯关系

```text
ROUTE-web-portal-accounts（/accounts）
→ PAGE-account-query（web-portal/src/views/AccountPage.vue）
→ API-account-query（GET /api/account/{userId}）→ ../interfaces/API-account-query_账户信息查询_queryAccount.md
→ SERVICE-account-service / MODULE-account-core
├─ TABLE-t_user_account（R：account_no、balance）→ CODE-AccountMapperXml-selectByUserId → ../data-models/DB-demo_account/TABLE-t_user_account.md
└─ CONFIGURATION：CONFIGGROUP-account-server（server.port；生效条件与代理对应关系待确认）→ ../configurations/SERVICE-account-service.md
```

- 页面侧前端配置（axios `baseURL`、开发代理）见 4.4，不链接后端配置实体。
