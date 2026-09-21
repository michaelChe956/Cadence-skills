# 订单导出流程

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 流程稳定 ID | FLOW-order-export |
| 条目状态 | ai-draft |
| 来源 | 用户资料（`user-input/product.md:15`、`user-input/api-scope.md:13`）+ 接口与代码存根证据 |

## 2. 目的与边界

运营人员在订单管理页触发订单导出，期望生成导出文件并向调用方提供结果。不覆盖：导出内容定义、文件命名、交付方式与清理执行者（均未提供）；不覆盖自定义条件导出（`ExportController#export` 无入参）。

## 3. 步骤链

| 步骤 | 实体稳定 ID | 证据（文件:行号） | 说明 |
|------|-------------|-------------------|------|
| 1 | PAGE-order-manage | `web-portal/src/views/OrderPage.vue:5,11` | 点击“导出订单”按钮触发 `exportOrder()` |
| 2 | ROUTE-web-portal-orders | `web-portal/src/main.js:5,12` | `/orders` 静态路由装配到 `views/OrderPage.vue` |
| 3 | MODULE-web-portal-api | `web-portal/src/api/index.js:5` | 调用 `request.post('/order/export')`，无请求参数 |
| 4 | API-order-export | `order-service/src/main/java/com/demo/order/controller/ExportController.java:36-44` | `POST /api/order/export` 返回字面量 `taskId`，为存根实现（Q-H2） |
| 5 | SERVICE-order-service / MODULE-order-export | `order-service/src/main/java/com/demo/order/service/ExportService.java:5-11` | 仅声明保留期常量，控制器未调用该服务，无导出逻辑 |
| 6 | TABLE-t_export_file | `db/init.sql:35-40` | 登记表 DDL 存在（`order_id`、`file_path`、`created_at`），未发现 Mapper 或写入调用（Q-M4） |
| 7 | CONFIGGROUP-order-server | `order-service/src/main/resources/application.yml:1-5` | 仅端口与应用名键；未发现导出相关配置键（无存储路径、无清理任务配置） |

```text
PAGE-order-manage → ROUTE-web-portal-orders → API-order-export
→ SERVICE-order-service/MODULE-order-export → TABLE-t_export_file
→ CONFIGGROUP-order-server
```

## 4. 状态流转

| 状态迁移 | 触发条件 | 证据（文件:行号） |
|----------|----------|-------------------|
| 不适用（未实现状态字段） | - | `db/init.sql:35-40`（登记表无状态列） |

## 5. 关联规则

| 规则稳定 ID | 关系说明 |
|-------------|----------|
| RULE-order-export-retention | 导出文件保留 7 天的阈值约束（仅有常量与注释证据） |

## 6. 失败处理与异步边界

- 端到端链路未实现：无文件生成、无登记表写入、无结果查询方式、无失败与重试处理（Q-H2）。
- 接口同步返回纯文本 `taskId`，未发现异步任务、消息或文件交付通道（`FILE-order-export-file` 状态未知，Q-M4）。
- 用户对外清单声明该能力“使用中”，与代码仅存根冲突；对外分类仍以用户清单为权威（Q-H2）。

