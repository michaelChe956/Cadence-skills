# Vue 与 React 页面分析指南

## Schema 4.0 前置契约

只接受 Manifest `schema_version: "4.0"`，并以页面、API、工程、数据模型和配置授权范围为边界。Manifest 缺失、版本不是 4.0 或页面领域未授权时停止，不兼容旧版，也不回退全仓扫描。

分析前读取 Base Info 关系矩阵、接口索引与目标接口主文件、`data-models/README.md` 与目标 TABLE 文档、`configurations/README.md` 与目标服务配置实体。

## 目录

- Vue 路由模式
- React 路由模式
- 动态路由与权限
- API 映射
- 页面状态
- 常见误判

## Vue 路由模式

关注：

- `new VueRouter`、`createRouter`
- `routes` 数组和模块合并
- `router.addRoute`、`addRoutes`
- `beforeEach`、`beforeResolve`、`afterEach`
- `meta.roles`、`meta.permissions`、`meta.hidden`
- 动态 Import、Layout 和路径别名
- Pinia、Vuex 中的菜单和权限路由生成

Vue 2 与 Vue 3 的 API 不同，但分析目标相同：找到路由来源、装配位置、权限条件和实际组件。

## React 路由模式

关注：

- React Router 配置对象和 JSX Route
- `createBrowserRouter`、`useRoutes`
- 嵌套路由、Outlet、Navigate 和 Loader
- Lazy、Suspense 和代码分割
- 权限包装组件和路由守卫替代模式
- Redux、Zustand、Context 中的权限和菜单状态
- Next.js 等文件系统路由仅在目标项目实际使用时分析

## 动态路由与权限

动态路由可能来自：

- 登录后菜单 API
- 角色或权限码转换
- Feature Flag
- 租户配置
- 微前端注册
- 环境配置

静态代码只能证明转换算法和候选组件，不能证明某个用户在生产环境最终获得的完整路由树。

## API 映射

优先追踪：

1. 页面组件直接调用 API 模块
2. Hook、Composable、Service 层调用
3. Store Action 或异步 Thunk 调用
4. 请求客户端添加的 Base URL 和前缀
5. 开发代理和网关重写

规范化并匹配：

1. 确认实际 HTTP Method，不能从函数名推断。
2. 合并请求客户端 `baseURL`、统一前缀和环境变量。
3. 应用开发代理、BFF 和网关路径重写规则。
4. 把实际 ID、查询串和动态片段规范化为路径模板，例如 `/orders/123` 转为 `/orders/{orderId}`。
5. 使用 `HTTP Method + 标准 Path` 在 `cadence/knowledge-base/interfaces/README.md` 中查找稳定 API ID。
6. 读取对应接口主文件，核对分类、状态、后端服务、数据实体和中间件。
7. 页面文档使用稳定 API ID，并以相对链接指向 `../interfaces/` 下的接口主文件。

请求函数名与后端方法名相似不能视为关联证据，必须结合方法、标准路径和完整调用链。同一页面调用多个 API 时逐条记录。

未在接口索引中找到唯一匹配项时：

- 使用 `API-CANDIDATE-*` 保存前端调用证据。
- 记录已知 Method、Path、调用位置和请求封装链路。
- 接口主文件填写“未登记”，不创建虚假链接。
- 将核实事项写入待确认清单，交由 API 分析补录。

## 页面到数据模型

固定沿以下关系取证：

```text
PAGE/ROUTE → API → SERVICE/MODULE → TABLE → 字段/Mapper/SQL
```

1. 页面到 API 使用实际请求代码、HTTP Method、标准 Path 和接口主文件证明。
2. API 到 SERVICE/MODULE、TABLE、字段、Mapper/SQL 使用接口主文件和后端证据证明。
3. 页面字段到 API 字段使用组件绑定、Store/Hook、请求 DTO 或响应转换证明。
4. 记录 TABLE 稳定 ID、页面字段、API 字段、表字段、读写、证据状态和 `data-models/` 链接。
5. 页面字段、API 字段与表字段名称相同仍不能直接建立关系；缺少模型、请求代码或后端映射时写 `待确认`。

## 页面配置依赖

固定沿以下关系取证：

```text
PAGE/ROUTE → API → SERVICE/MODULE → CONFIGURATION → 配置键/生效条件
```

前端 Feature Flag、环境变量、菜单配置或后端开关只有在直接控制页面、路由、权限、请求或展示行为时才记录。每项依赖包含配置组稳定 ID、服务配置实体、配置键、环境/Profile、绑定位置、生效条件、证据状态和 `configurations/` 链接。

配置键存在不等于页面当前可用；只有默认值或键名、但缺少加载与生效证据时写 `待确认`。密码、Token、密钥、完整连接串、内部域名、IP 和 URL 等敏感值统一写 `<redacted>`。

## 页面状态

区分：

- 路由声明
- 组件文件存在
- 路由已装配
- 菜单或导航可达
- 用户权限可访问
- Feature Flag 或环境条件启用

## 常见误判

- `views/` 目录下每个文件都是页面
- 页面组件存在即用户可访问
- 前端角色判断即完整安全边界
- API 方法名相同即调用对应后端接口
- 页面字段、API 字段与表字段同名即存在数据映射
- 页面业务名称相似即可跳过 API 直接关联 TABLE
- Feature Flag 配置键存在即目标环境已启用
- 开发代理路径即生产网关路径
- 动态菜单转换表即生产菜单结果
- 被注释或废弃路由仍是活动能力
