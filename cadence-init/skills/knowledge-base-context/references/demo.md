# 订单导出任务上下文案例

> 本案例完全虚构，只演示文档结构、双轨证据和渐进读取方式，不提供目标项目事实。

## 1. 任务识别

- 原始请求：实现订单列表批量导出；空结果也生成仅含表头的文件，并补充权限、空结果和对象存储失败测试。
- 主画像：Coding
- 辅助画像：Testing
- Manifest 基线：`8f31c2a`
- 当前提交：`b64d910`
- 工作区状态：存在 `OrderExportService.java` 未提交修改
- 读取范围：`admin-web`、`order-service`，页面、对内 REST、订单表和对象存储领域

## 2. 任务理解

在现有订单列表页增加异步导出能力，复用已有查询条件和对象存储下载模式。任务不改变对外能力清单，不设计新的导出中心，也不修改存储桶配置。

## 3. 核心实体

| 稳定 ID / 符号 | 类型 | 名称 | 位置 | 与任务关系 |
|-----------------|------|------|------|------------|
| `PAGE-ORDER-LIST` | 页面 | 订单列表 | `pages/PAGE-ORDER-LIST_订单列表.md` | 发起导出 |
| `API-INTERNAL-ORDER-EXPORT` | 对内 REST | 创建订单导出任务 | `interfaces/API-INTERNAL-ORDER-EXPORT_创建导出任务.md` | 目标接口 |
| `OrderExportService#createTask` | Service | 创建导出任务 | `order-service/.../OrderExportService.java` | 主要修改入口 |
| `TABLE-ORDER` | 表 | 订单表 | `data-models/TABLE-ORDER_订单表.md` | 查询来源 |
| `OBJ-EXPORT-BUCKET` | 中间件 | 导出对象存储 | `base-information.md` | 文件落点 |

## 4. 双轨证据矩阵

| 结论 | KnowledgeBase 证据 | 源码/DDL/配置证据 | 状态 | 对任务影响 |
|------|--------------------|-------------------|------|------------|
| 订单页通过对内 REST 创建导出任务 | `PAGE-ORDER-LIST`、`API-INTERNAL-ORDER-EXPORT` | `order.ts#exportOrders` → `OrderExportController#create` | `一致` | 可沿用现有页面到 API 链路 |
| 导出只允许 `ORDER_EXPORT` 权限 | API 主文件权限章节 | `@PreAuthorize("hasAuthority('ORDER_EXPORT')")` | `一致` | 必须覆盖无权限测试 |
| 空结果返回成功且文件只含表头 | 参数与报文文档 | 当前 `createTask` 对空列表抛出 `NO_DATA` | `来源冲突` | 实现前必须确认预期，当前任务暂按用户明确要求返回表头 |
| 对象存储失败写任务失败状态 | 关系矩阵记录 `SERVICE → OBJ-EXPORT-BUCKET` | `git diff 8f31c2a..b64d910 -- OrderExportService.java` 显示 `upload()` 异常处理改为只记录日志，未更新状态 | `基线漂移` | 需补偿状态更新和失败断言 |
| 导出查询使用订单创建时间索引 | `TABLE-ORDER` 索引说明 | DDL 中存在 `idx_order_created_at`，Mapper 查询条件匹配 | `一致` | 不需要新增索引 |

## 5. 关系与影响面

```text
ROUTE-ORDER-LIST
→ PAGE-ORDER-LIST
→ API-INTERNAL-ORDER-EXPORT
→ OrderExportController#create
→ OrderExportService#createTask
├── OrderMapper#selectForExport
│   └── TABLE-ORDER
└── ObjectStorageClient#upload
    └── OBJ-EXPORT-BUCKET
```

一跳关系已覆盖页面、API、Service、表和对象存储。公共鉴权工具、日志框架和对象存储 SDK 内部调用不再扩展。

## 6. 画像专属上下文

### Coding

- 精确入口：`OrderExportService#createTask`。
- 复用模式：同模块 `InvoiceExportService` 使用“创建任务 → 上传 → 更新成功/失败状态”的事务外补偿模式。
- 边界条件：空结果、最大批量 10,000 条、重复点击幂等键、对象存储异常。
- 直接调用方：`OrderExportController#create`；未发现其他调用方。

### Testing

- 正常：有权限且查询有结果，返回任务 ID，最终状态为成功。
- 边界：空结果生成仅含表头文件；10,001 条被拒绝。
- 权限：缺少 `ORDER_EXPORT` 返回 403。
- 异常：对象存储抛错后任务状态为失败，不返回可下载地址。
- 回归：订单列表查询条件序列化、已有发票导出补偿流程。
- 执行入口：`./mvnw -pl order-service -Dtest=OrderExportServiceTest,OrderExportControllerTest test`。

## 7. 约束与现有模式

- 对外能力清单不包含该接口，保持对内 REST 分类。
- 只使用用户提供的 DDL 与仓库 SQL，不查询数据库。
- 对象存储配置值不得输出，只记录配置键 `storage.export.bucket`。
- 未提交修改是当前实现证据，不能覆盖或恢复。

## 8. 冲突、缺口与待确认项

| 优先级 | 类型 | 内容 | 影响 | 建议补证方式 |
|--------|------|------|------|--------------|
| 高 | 来源冲突 | 空结果行为在文档与实现中不一致 | 改变接口响应和测试断言 | 以本次用户明确要求为任务假设，并在 Review 时再次核对 |
| 中 | 基线漂移 | 基线后导出失败处理被修改 | KnowledgeBase 未覆盖当前失败路径 | 实现后执行 `knowledge-base-update` |
| 低 | 缺口 | 未发现对象存储集成测试 | 不阻断单元与接口测试 | 后续评估是否增加 Testcontainer 或 Fake Server |

## 9. 下游使用建议

Coding 应复用 `InvoiceExportService` 的状态补偿结构，只修改订单导出链路；Testing 应先用失败用例固定空结果和上传异常行为，再实施最小变更。完成后 Review 重点检查权限、幂等、状态补偿和页面请求映射。

## 10. 就绪状态

- 状态：有条件就绪
- 条件：以“空结果生成表头文件”为本次明确假设；其余入口、关系、约束和验证方式已具备。
