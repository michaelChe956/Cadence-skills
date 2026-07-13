# 页面能力案例

## Vue 动态路由

- 页面 ID：`PAGE-order-list`
- 路由 ID：`ROUTE-admin-orders`
- 路径：`/admin/orders`
- 组件：`src/views/order/list.vue`
- 来源：后端菜单 API 经 `permissionStore.generateRoutes` 转换
- 权限：`order:view`
- 状态：组件存在、条件启用；生产菜单是否下发待确认
- API：`API-order-page`、`API-order-export`
- 数据：`TABLE-order`
- 可信度：中

## React 静态路由

- 页面 ID：`PAGE-user-detail`
- 路由 ID：`ROUTE-users-detail`
- 路径：`/users/:id`
- 组件：`UserDetailPage`
- 来源：`createBrowserRouter` 配置
- 权限包装：`RequirePermission("user:view")`
- API：通过 `useUserDetail` 调用 `API-user-detail`
- 状态：已声明、组件存在、已装配

## 异常项

- `src/views/legacy/report.vue` 存在，但路由和菜单均无引用。
- 标记：代码存在但不可达。
- 不写入活动页面清单，保留在异常项和待确认清单。

