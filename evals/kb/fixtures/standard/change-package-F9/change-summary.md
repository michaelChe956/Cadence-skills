# 变更摘要

## 基本信息

- 变更标识：CHANGE-F9-REMOVE-ACCOUNT-API
- 变更目的：下线账户查询端点（业务迁移至新网关）
- 目标环境：开发
- 涉及服务：account-service
- 业务影响：依赖该端点的组合能力需要重新评估
- 风险：聚合能力断链

## 领域变更矩阵

| 领域 | 变更状态 | 摘要或无变更判断依据 |
|------|----------|----------------------|
| 代码 | 有变更 | 删除 AccountController 与 AccountService、AccountPage 改提示页、api/index.js 移除调用 |
| 数据模型 | 无变更 | 未触及表结构，DDL 与 Entity 无改动 |
| 配置 | 无变更 | application.yml 未改动 |
| 中间件 | 无变更 | 未触及 RabbitMQ/MySQL 依赖 |
| 接口 | 有变更 | 对内 REST 端点 GET /api/account/{userId} 删除 |
| 页面 | 有变更 | AccountPage.vue 改写为提示页（移除调用） |
| 业务知识 | 有变更 | 组合能力 CAP 输入失效，需重算 |

## 关联说明

- 负责人或确认人：fixture 维护者
