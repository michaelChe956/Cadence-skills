# 页面能力 PAGE-user-list 用户列表

## 文档元数据

- 生成时间：2026-09-20
- Git 分支：master
- 基线提交：1f867b9fcdf95f2e11808454898f333d7d512e90
- 执行模式：初始化续跑（`coverage.initialization.status: in_progress`，本次执行 `pages` 阶段）
- 前端应用：`SERVICE-web-portal`（`MODULE-web-portal-app`、`MODULE-web-portal-api`、`MODULE-web-portal-views`）
- 页面稳定 ID：`PAGE-user-list`；路由稳定 ID：`ROUTE-web-portal-users`
- 动态路由限制：本页为代码静态路由（`web-portal/src/main.js:11`）；未发现后端菜单下发、运行时 `addRoute` 或权限路由转换，生产入口与菜单未提供

## 1. 前端应用与路由来源

- 应用装配：`web-portal/src/main.js:8-15`（`createRouter` + `createWebHistory`），`web-portal/src/main.js:16` 挂载 `#app`。
- 路由声明：`web-portal/src/main.js:11` → `{ path: '/users', component: UserList }`；无 `name`、`meta`、`redirect`、`alias`、动态参数、懒加载与嵌套。
- 组件：`web-portal/src/views/UserList.vue:1-13`，由 `web-portal/src/main.js:4` 静态导入。
- 路由来源分类：代码静态路由；未发现其他来源（`user-input/page-scope.md:6` 声明与代码一致）。

## 2. 路由树

```text
（无父级与 Layout；本路由为平级静态路由）
/users → ROUTE-web-portal-users → PAGE-user-list → views/UserList.vue
```

- 无父子关系、无重定向、无别名、无动态参数。
- 应用未定义根路由 `/`、通配路由与 404 视图，未匹配路径不渲染任何业务视图。

## 3. 页面能力清单

| PAGE ID | ROUTE ID | 路径 | 页面用途 | 组件 | 权限 | 状态 | API 主文件 | 证据 |
|---------|----------|------|----------|------|------|------|------------|------|
| PAGE-user-list | ROUTE-web-portal-users | `/users` | 按用户标识查询并展示用户基本信息（姓名、手机号） | `web-portal/src/views/UserList.vue` | 未发现（无 `meta`、无守卫、无权限码） | 已声明、组件存在、已装配；可达性待确认（无菜单入口、应用入口 HTML 缺失） | [`API-user-basic`](../interfaces/API-user-basic_查询用户基本信息_queryBasic.md) | `web-portal/src/main.js:4,11`、`web-portal/src/views/UserList.vue:1-13` |

- 页面操作：无自动请求；点击“查询用户信息”按钮触发 `load()`（`web-portal/src/views/UserList.vue:5,12`）。
- 展示字段：`u.userName`、`u.mobile`（`web-portal/src/views/UserList.vue:4`）。
- 输入参数：未发现表单或筛选条件；请求参数为硬编码 `1`（`web-portal/src/views/UserList.vue:12`），登记 Q-L7。
- 状态来源：组件内 `users` ref（`web-portal/src/views/UserList.vue:11`），无 Store/Hook/Composable。
- 上传、下载、WebSocket 与消息能力：未发现。
- 生命周期与缓存：无 `onMounted` 自动加载、无 KeepAlive；无 Feature Flag 与环境分支。

## 4. 页面与 API 映射

### 4.1 已匹配接口

| PAGE ID | API ID | 分类 | 方法与标准路径 | 调用位置 | 请求封装、Store 或 Hook | 接口主文件 | SERVICE/MODULE | 状态 | 可信度 | 证据 |
|---------|--------|------|----------------|----------|-------------------------|------------|----------------|------|--------|------|
| PAGE-user-list | API-user-basic | 对外 | `GET /api/user/basic/{userId}` | `web-portal/src/views/UserList.vue:12`（`queryUserBasic(1)`） | 页面 → `api/index.js#queryUserBasic`（`web-portal/src/api/index.js:2`）→ `api/request.js` axios 实例（`baseURL: '/api'`）→ 开发代理 `/api` | [`API-user-basic_查询用户基本信息_queryBasic.md`](../interfaces/API-user-basic_查询用户基本信息_queryBasic.md) | `SERVICE-user-service` / `MODULE-user-basic` | 已声明、已实现、已装配、已暴露 | 高 | `web-portal/src/api/index.js:2`、`web-portal/src/views/UserList.vue:12`；接口主文件声明前端访问路径 `/api/user/basic/{userId}` |
| PAGE-user-list | 未发现其他调用 | - | - | - | - | 未登记 | - | - | - | 页面组件内仅一处请求调用 |

对外关联说明：调用链实际请求地址与 `API-user-basic` 接口主文件登记的“前端访问路径”逐字一致（Method + 路径），因此允许关联对外能力，未按页面文案或业务名称相似度匹配。

### 4.2 页面字段与数据模型影响

| PAGE/ROUTE ID | API ID | SERVICE/MODULE | TABLE 稳定 ID | 页面字段 | API 字段来源 | 表字段 | 读写 | Mapper/SQL 或后端映射 | 证据状态 | 表文档链接 |
|---------------|--------|----------------|---------------|----------|------------|--------|------|----------------------|----------|------------|
| PAGE-user-list | API-user-basic | SERVICE-user-service / MODULE-user-basic | TABLE-t_user | 展示 `userName`、`mobile`；列表 key `userId` | 响应为 `UserEntity` 直接序列化（`userId`、`userName`、`mobile`、`email`） | `user_name`、`mobile`、`user_id` | R | `CODE-UserMapperXml-selectById`（`user_id AS userId`、`user_name AS userName`、`mobile AS mobile`） | 已确认 | [`TABLE-t_user`](../data-models/DB-demo_user/TABLE-t_user.md) |

- 逐跳证据：页面展示绑定 `web-portal/src/views/UserList.vue:4` → 接口响应模型（`API-user-basic` 参数与报文）→ 接口主文件登记只读表 `TABLE-t_user` → `user-service/src/main/resources/mapper/UserMapper.xml:4-7`。
- 页面未展示 `email`，因此不登记该字段的页面影响；响应中的 `email` 仍由同一 SQL 返回。

### 4.3 后端服务配置依赖

| PAGE/ROUTE ID | API ID | SERVICE/MODULE | 配置组稳定 ID | 服务配置实体 | 配置键 | 页面影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|---------------|--------|----------------|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| PAGE-user-list | API-user-basic | SERVICE-user-service | CONFIGGROUP-user-server | SERVICE-user-service | `server.port` | 页面请求目标可达性（服务监听端口） | 开发（fixture 快照）/ default | 服务监听端口为 8081，而前端开发代理仅指向单一目标端点（值 `<redacted>`），两者对应关系未确认；未发现生产网关路径 | 待确认 | [`SERVICE-user-service`](../configurations/SERVICE-user-service.md) |

- 未登记 `CONFIGGROUP-user-datasource`：该组控制服务端数据访问，页面行为仅经 API 响应间接受影响，不满足“直接控制页面/路由/权限/请求/展示行为”的记录条件。
- 未发现后端 Feature Flag 或开关：`user-service` 授权配置键为 5 个（端口、应用名、数据源三项），未发现经 API 响应或错误控制页面行为的配置项。

### 4.4 前端直接配置

| PAGE/ROUTE ID | 前端应用或模块 | 配置键 | 页面影响 | 环境/构建模式 | 前端绑定与生效条件 | 证据状态 | 来源 |
|---------------|----------------|--------|----------|---------------|--------------------|----------|------|
| PAGE-user-list | MODULE-web-portal-api（SERVICE-web-portal） | axios `baseURL`（值 `/api`） | 本页及全部页面请求的统一前缀 | 全部模式（开发/构建产物） | `web-portal/src/api/request.js:3` 创建实例时注入，所有 `api/index.js` 函数继承 | 已确认 | `web-portal/src/api/request.js:1-4` |
| PAGE-user-list | SERVICE-web-portal（构建配置，非配置基线） | `server.proxy['/api'].target` | 开发模式下本页请求的转发目标 | 开发服务器（`npm run dev`） | `web-portal/vite.config.js:3` 声明 `/api` 代理且不重写前缀；生产构建不包含该代理 | 已确认 | `web-portal/vite.config.js:1-4` |

> 本表仅记录前端代码直接读取的配置，不链接 `configurations/` 后端服务配置实体，也不用于推导后端 SERVICE/MODULE 或 CONFIGURATION。`web-portal` 不在配置授权范围内（`scope.configurations.selected` 为三个后端服务）。

### 4.5 未匹配接口候选

| PAGE ID | 候选 API ID | 已知方法与路径 | 调用位置 | 接口主文件 | 状态 | 可信度 | 待确认项 |
|---------|-------------|----------------|----------|------------|------|--------|----------|
| PAGE-user-list | 无 | - | - | 未登记 | 不适用 | - | 本页 1 个 REST 调用已按 Method + 标准路径唯一匹配 `API-user-basic`，无候选 |

## 5. 权限与导航

- 路由元数据：无 `meta`、无 `roles`/`permissions`/`hidden`（`web-portal/src/main.js:11`）。
- 路由守卫：未发现 `beforeEach`/`beforeResolve`/`afterEach`（`web-portal/src/main.js:8-15`）。
- 登录状态与 Token 恢复：未发现登录页、Token 存储、刷新或恢复流程。
- 菜单与导航：根组件仅 `<router-view />`（`web-portal/src/App.vue:1`），未发现导航菜单或跳转链接，本页只能通过直接输入 URL（`/users`）进入。
- 按钮与操作级权限：查询按钮无权限判断或禁用条件（`web-portal/src/views/UserList.vue:5`）。
- 结论：前端未做访问控制，且未发现后端鉴权实现（Q-M8）；页面可访问性是否由部署层或网关保护未提供证据（Q-M12）。

## 6. 状态管理与请求封装

```text
PAGE-user-list（/users）
→ UserList.vue#load（web-portal/src/views/UserList.vue:12）
→ api/index.js#queryUserBasic（web-portal/src/api/index.js:2）
→ api/request.js axios 实例（baseURL: '/api'，web-portal/src/api/request.js:3）
→ 开发代理 /api（web-portal/vite.config.js:3，前缀不重写）
→ GET /api/user/basic/{userId}
→ API-user-basic（../interfaces/API-user-basic_查询用户基本信息_queryBasic.md）
```

- 规范化：源码模板字符串 `/user/basic/${userId}` 不能直接与后端路径比较，合并 `baseURL: '/api'` 后为 `GET /api/user/basic/{userId}`；运行时 `userId = 1` 规范化为路径模板 `{userId}`。
- 无 Store、Hook、Composable 或 Service 层；响应写入组件内 `users` ref，无缓存与全局状态。
- 生产环境网关路径未提供，生产标准路径按开发链路记录。

## 7. 动态路由和运行时限制

- 本页路由在构建时确定，无后端菜单或权限转换参与，不存在动态路由解析。
- 未执行前端构建与开发服务器（只读离线分析，依赖需联网解析，Q-L3）；仓库内未发现 Vite 入口 `index.html` 与 `#app` 挂载点，应用能否构建/启动未确认（Q-H3），因此“浏览器可实际访问 `/users`”待确认。
- 生产环境入口、菜单与访问控制未提供。

## 8. 孤立与不可达页面

- 本页不是孤立页面：存在静态路由声明与静态导入组件（`web-portal/src/main.js:4,11`）。
- 无菜单、无重定向、无其他页面跳转入口（`web-portal/src/App.vue:1`）。
- 未发现同一组件被其他路由引用，未发现被注释或废弃的路由。
- 运行时不可达风险：应用入口 HTML 缺失（Q-H3），本页可达性不能由静态证据证明。

## 9. 来源冲突

- `user-input/page-scope.md:6` 声明路由来源为“代码静态路由（src/main.js）”，与代码证据一致，无冲突。
- `interfaces/API-user-basic_查询用户基本信息_queryBasic.md` 登记调用方包含 `web-portal` 用户列表页并引用 `web-portal/src/api/index.js:2`、`web-portal/src/views/UserList.vue:12`，与本页证据一致。
- `interfaces/README.md` 中 `TABLE-t_user` 的读服务为 `SERVICE-user-service`，与本页 4.2 链路一致。

## 10. 待人工确认

- Q-H3：`web-portal` 缺少 Vite 入口 `index.html`，应用能否构建/启动未确认，影响本页可达性。
- Q-M12：前端无鉴权与导航入口，生产环境可达性与访问控制未确认。
- Q-L7：页面硬编码 `userId = 1`，是否应支持用户输入或参数化未确认。
- Q-L4：开发代理单一目标端点与三个后端服务端口的对应关系未确认。
- Q-L1：依赖为 caret 范围且无锁文件，页面实际渲染行为对应版本未确认。

## 11. 完整追溯关系

```text
ROUTE-web-portal-users（/users）
→ PAGE-user-list（web-portal/src/views/UserList.vue）
→ API-user-basic（GET /api/user/basic/{userId}）→ ../interfaces/API-user-basic_查询用户基本信息_queryBasic.md
→ SERVICE-user-service / MODULE-user-basic
├─ TABLE-t_user（R：user_id、user_name、mobile）→ CODE-UserMapperXml-selectById → ../data-models/DB-demo_user/TABLE-t_user.md
└─ CONFIGURATION：CONFIGGROUP-user-server（server.port；生效条件与代理对应关系待确认）→ ../configurations/SERVICE-user-service.md
```

- 页面侧前端配置（axios `baseURL`、开发代理）见 4.4，不链接后端配置实体。
