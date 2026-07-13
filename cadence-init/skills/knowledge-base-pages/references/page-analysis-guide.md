# Vue 与 React 页面分析指南

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

请求函数名与后端方法名相似不能视为关联证据，必须结合路径、方法或调用链。

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
- 开发代理路径即生产网关路径
- 动态菜单转换表即生产菜单结果
- 被注释或废弃路由仍是活动能力

