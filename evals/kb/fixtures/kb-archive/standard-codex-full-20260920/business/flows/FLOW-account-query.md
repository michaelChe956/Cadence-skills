# 账户信息查询流程

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 流程稳定 ID | FLOW-account-query |
| 条目状态 | confirmed |
| 来源 | 用户资料（`user-input/product.md:14` 关键特性“账户查询”）+ 页面、接口与代码证据 |

## 2. 目的与边界

运营人员在账户查询页按用户标识查询并查看账户号与余额。不覆盖：账户开立、余额调整、状态变更（未发现写入实现）；不覆盖对外暴露（该接口未登记为用户对外能力，Q-M7）与页面鉴权（Q-M12）。

## 3. 步骤链

| 步骤 | 实体稳定 ID | 证据（文件:行号） | 说明 |
|------|-------------|-------------------|------|
| 1 | PAGE-account-query | `web-portal/src/views/AccountPage.vue:12` | 触发 `queryAccount(1)`；`userId` 为硬编码常量（Q-L7） |
| 2 | ROUTE-web-portal-accounts | `web-portal/src/main.js:6,13` | `/accounts` 静态路由装配到 `views/AccountPage.vue` |
| 3 | MODULE-web-portal-api | `web-portal/src/api/index.js:3`、`web-portal/src/api/request.js:3` | axios 实例拼接 `GET /account/{userId}` |
| 4 | API-account-query | `account-service/src/main/java/com/demo/account/controller/AccountController.java:26-30` | `GET /api/account/{userId}` → `AccountService#queryAccount` |
| 5 | SERVICE-account-service / MODULE-account-core | `account-service/src/main/java/com/demo/account/service/AccountService.java:17-20` | 服务层直接委托 Mapper，无附加业务校验 |
| 6 | TABLE-t_user_account | `account-service/src/main/resources/mapper/AccountMapper.xml:5-7` | `SELECT * FROM t_user_account WHERE user_id = #{userId}`；响应字段依赖隐式驼峰映射（Q-M3） |
| 7 | CONFIGGROUP-account-datasource / MIDDLEWARE-mysql / DB-demo_account | `account-service/src/main/resources/application.yml:6-9`、`account-service/pom.xml:16` | 数据源键与 MySQL 驱动决定实际连接（连接值 `<redacted>`）；`server.port` 键见 `application.yml:1-2` |

```text
PAGE-account-query → ROUTE-web-portal-accounts → API-account-query
→ SERVICE-account-service/MODULE-account-core → TABLE-t_user_account
→ CONFIGGROUP-account-datasource/MIDDLEWARE-mysql
```

## 4. 状态流转

| 状态迁移 | 触发条件 | 证据（文件:行号） |
|----------|----------|-------------------|
| 不适用（只读查询，无状态变更） | - | `account-service/src/main/resources/mapper/AccountMapper.xml:5-7`（仅 `SELECT`） |

## 5. 关联规则

| 规则稳定 ID | 关系说明 |
|-------------|----------|
| RULE-account-balance-non-negative | 页面展示的 `balance` 受该约束影响，但流程未执行该约束校验 |

## 6. 失败处理与异步边界

- 同步 HTTP 调用，无消息、事件、任务或重试边界。
- 未发现异常处理与降级逻辑；账户不存在时返回空响应体，无 404 分支证据。
- 字段映射风险：`SELECT *` 与无 `resultMap` 依赖隐式驼峰映射，`accountNo`、`userId` 可能为空（Q-M3）。
- 配置快照仅覆盖开发环境；`account-service` 的数据源指向内部地址与口令均为 `<redacted>`，非开发环境配置未知（Q-M6）。

