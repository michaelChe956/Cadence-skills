# KnowledgeBase 初始化案例

## 完整模式案例

用户提供：

- `inputs/ddl/order.sql`：MySQL 生产结构导出
- `inputs/config/`：开发与生产配置的脱敏副本
- `inputs/api/openapi.yaml`
- `inputs/routes/admin-routes.md`
- `inputs/middleware.md`：Kafka 3.7、Redis 7、Nacos 2.4
- `inputs/glossary.md`

处理结果：

1. 确认 `order-service`、`user-service` 和 `admin-web` 三个边界。
2. 将资料状态标记为已提供。
3. 记录当前分支和 Git 基线。
4. 依次执行基础信息、API、页面和概览分析。
5. 将 OpenAPI 与 Controller、网关配置交叉核对。
6. 将页面路由关联到 API、服务和数据表。
7. 生成完整模式知识库和待确认清单。

## 有限证据模式案例

用户只能提供代码和开发配置，无法提供生产 DDL、API 文档和动态菜单配置。

处理方式：

- DDL：根据迁移文件、Entity、Mapper 和 SQL 生成候选模型，标记数据库结构不完整。
- API：根据 Controller、Feign 和网关配置生成代码清单，标记待人工校对。
- 页面：分析静态路由和请求模块，动态菜单页面标记未覆盖。
- 中间件：只有依赖但无 Producer、Listener 或有效配置的组件标记为候选，不认定实际使用。
- 最终报告明确有限证据模式，不给出虚构覆盖率。

