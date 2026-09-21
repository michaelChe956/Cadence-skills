# 用户基本信息查询流程

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 流程稳定 ID | FLOW-user-basic-query |
| 条目状态 | confirmed |
| 来源 | 用户资料（`user-input/product.md:13` 关键特性“用户信息查询”）+ 页面、接口与代码证据 |

## 2. 目的与边界

运营人员在用户列表页按用户标识查询并查看用户基本信息（姓名、手机号、邮箱）。不覆盖：用户创建、修改、删除与批量查询（未发现对应实现）；不覆盖页面权限控制（未发现鉴权实现，Q-M8/Q-M12）。

## 3. 步骤链

| 步骤 | 实体稳定 ID | 证据（文件:行号） | 说明 |
|------|-------------|-------------------|------|
| 1 | PAGE-user-list | `web-portal/src/views/UserList.vue:12` | 触发 `queryUserBasic(1)`；`userId` 为硬编码常量（Q-L7） |
| 2 | ROUTE-web-portal-users | `web-portal/src/main.js:4,11` | `/users` 静态路由装配到 `views/UserList.vue` |
| 3 | MODULE-web-portal-api | `web-portal/src/api/index.js:2`、`web-portal/src/api/request.js:3` | axios 实例（`baseURL: '/api'`）拼接 `GET /user/basic/{userId}`；开发代理前缀 `/api`（`web-portal/vite.config.js:3`，目标值 `<redacted>`） |
| 4 | API-user-basic | `user-service/src/main/java/com/demo/user/controller/UserBasicController.java:26-30` | `GET /api/user/basic/{userId}` → `UserBasicService#queryBasic` |
| 5 | SERVICE-user-service / MODULE-user-basic | `user-service/src/main/java/com/demo/user/service/UserBasicService.java:17-20` | 服务层直接委托 Mapper，无附加业务校验 |
| 6 | TABLE-t_user | `user-service/src/main/resources/mapper/UserMapper.xml:4-7` | `SELECT user_id AS userId, user_name AS userName, mobile, email FROM t_user WHERE user_id = #{userId}` |
| 7 | CONFIGGROUP-user-datasource / MIDDLEWARE-mysql / DB-demo_user | `user-service/src/main/resources/application.yml:6-9`、`user-service/pom.xml:16` | 数据源键与 MySQL 驱动决定实际连接（连接值 `<redacted>`）；`server.port` 键见 `application.yml:1-2` |

```text
PAGE-user-list → ROUTE-web-portal-users → API-user-basic
→ SERVICE-user-service/MODULE-user-basic → TABLE-t_user
→ CONFIGGROUP-user-datasource/MIDDLEWARE-mysql
```

## 4. 状态流转

| 状态迁移 | 触发条件 | 证据（文件:行号） |
|----------|----------|-------------------|
| 不适用（只读查询，无状态变更） | - | `user-service/src/main/resources/mapper/UserMapper.xml:4-7`（仅 `SELECT`） |

## 5. 关联规则

| 规则稳定 ID | 关系说明 |
|-------------|----------|
| 无 | 未发现约束、计算或阈值类规则作用于该查询流程 |

## 6. 失败处理与异步边界

- 同步 HTTP 调用，无消息、事件、任务或重试边界。
- 未发现异常处理与降级逻辑（页面组件无 `try/catch`，`api/request.js` 无响应拦截器）；查询无结果时返回空响应体，无 404 分支证据。
- 响应为标准 `UserEntity` 直接序列化（`userId`、`userName`、`mobile`、`email`）；无字段级脱敏（Q-M8）。
- 前端可达性受应用入口缺失影响（Q-H3）；前端开发代理目标与 `user-service` 端口 `8081` 的对应关系未确认（Q-L4）。

