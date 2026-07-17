# 订单导出测试环境超时上下文案例

> 本案例完全虚构，只演示 Schema 4.0 四类证据、表与配置关系检查和渐进停止方式，不执行实际调试或推测修复。

## 1. 任务识别

- 原始请求：调试订单导出在测试环境超时；已知 API、订单逻辑表、超时配置键和未处理变更包 `CHANGE-order-export-timeout`。
- Schema：`4.0`
- 主画像：Debug
- 辅助画像：无
- Manifest Git 基线：`8f31c2a`
- 当前提交：`b64d910`
- 数据模型来源：订单表无完整 DDL，有字段级文档、迁移、Mapper XML 和 Entity。
- 配置授权快照：`test-release-20260715`，测试环境，授权指纹校验通过，外部目录只读且可读。
- 最近处理变更包：`CHANGE-order-export-batch`。
- 用户点名变更包：`CHANGE-order-export-timeout`，未登记在 `processed_packages`。
- 读取范围：`admin-web`、`order-service` 及授权的订单数据模型和测试配置快照。

## 2. 任务理解

目标是为后续 Debug 准备最小上下文：确认页面到导出 API 的失败链、订单查询的数据源与 SQL、测试环境超时键的绑定和生效条件，以及未处理变更包是否导致基线漂移。本阶段不连接数据库或配置中心，不运行服务，也不提出修复方案。

## 3. 核心实体

| 稳定 ID / 符号 | 类型 | 名称 | 位置 | 与任务关系 |
|-----------------|------|------|------|------------|
| `PAGE-order-list` | 页面 | 订单列表 | `pages/PAGE-order-list.md` | 发起导出 |
| `API-internal-order-export` | API | 创建导出任务 | `interfaces/API-internal-order-export.md` | 已知超时入口 |
| `OrderExportService#createTask` | Service | 创建导出任务 | `order-service/.../OrderExportService.java` | 失败链核心 |
| `TABLE-order` | 逻辑表 | 订单表 | `data-models/SCHEMA-commerce/TABLE-order.md` | 导出查询来源 |
| `CONFIG-order-export` | 配置组 | 订单导出配置 | `configurations/SERVICE-order.md` | 包含超时键 |
| `acme.order.export.timeout-ms` | 配置键 | 导出超时 | 外部测试快照与 `OrderExportProperties` | 控制客户端等待条件 |

## 4. 四类证据矩阵

| 结论 | KnowledgeBase | 当前代码 | DDL/数据模型证据 | 配置快照证据 | 状态 | 任务影响 |
|------|---------------|----------|------------------|--------------|------|----------|
| 页面经 API 调用订单导出服务 | 页面、API 和服务关系矩阵 | `order.ts#exportOrders → OrderExportController#create → OrderExportService#createTask` | 无直接结构结论 | 无直接配置结论 | `一致` | 可限定失败调用链 |
| 导出查询读取订单逻辑表 | `TABLE-order` 与服务读关系 | `OrderMapper#selectForExport` | 字段级文档、`OrderMapper.xml#selectForExport`、迁移 `V214__order_export_index.sql`；无完整 DDL | 数据源组绑定 `SCHEMA-commerce` | `一致` | 后续需检查 SQL、索引与数据源路由 |
| 测试环境超时键进入导出客户端 | 服务配置文档记录配置组 | `OrderExportProperties#timeoutMs → ExportClientFactory` | 与表字段无直接关系 | `application-test.yml` 中键存在；用途为导出等待；状态为存在；绑定位置为 `OrderExportProperties#timeoutMs`；值 `<redacted>`；`test` Profile 生效 | `一致` | 后续可验证客户端超时位置 |
| 用户点名变更包调整超时和查询字段 | KnowledgeBase 尚未登记该包 | 当前提交包含包声明的两个相关符号 | `database-change.md` 声明字段无变化，但代码新增 `finished_at` 查询 | `configuration-change.md` 声明测试快照变化 | `基线漂移` | Review/Debug 必须保留声明与代码差异，不能视为已纳入基线 |
| `finished_at` 的数据库类型和可空性 | 字段级文档只登记字段名 | Mapper SQL 引用 `finished_at` | 无 DDL；迁移未定义该字段属性，Entity 只能证明映射 | 无直接配置关系 | `数据模型证据缺失` | 不能据此断言真实类型或可空性 |

## 5. 关系与影响面

```text
PAGE-order-list
→ API-internal-order-export
→ OrderExportController#create
→ OrderExportService#createTask
├── OrderMapper#selectForExport
│   ├── DATA-SOURCE-order-test
│   └── TABLE-order
└── ExportClientFactory
    └── CONFIG-order-export
        └── acme.order.export.timeout-ms
```

- 表关系检查：发现 `OrderMapper#selectForExport → TABLE-order`，只读取该逻辑表、相关字段和 SQL；`TABLE-order-audit` 无直接关系，记录后停止，不扫描其他订单表。
- 配置关系检查：发现导出客户端与 `CONFIG-order-export` 的直接关系，只读取服务配置文档、目标键所在快照文件、绑定和生效条件。

## 6. 数据模型上下文

- 逻辑表：`TABLE-order`。
- 任务相关字段：`id`、`status`、`created_at`、`finished_at`。
- Mapper / SQL：`OrderMapper.xml#selectForExport` 使用 `status` 和 `created_at` 过滤，并新增读取 `finished_at`。
- 数据源路由：测试 Profile 的订单数据源组映射到 `SCHEMA-commerce`；路由配置不能证明数据库真实结构。
- DDL / 迁移：无完整 DDL；使用字段级文档、迁移、Mapper 和 Entity 继续。`finished_at` 的类型、可空性和默认值为 `数据模型证据缺失`。

## 7. 配置上下文

- 配置组：`CONFIG-order-export`，适用 `order-service` 测试环境。
- 当前快照：`test-release-20260715`；授权指纹匹配；目录可读且只读。
- 配置键：`acme.order.export.timeout-ms`；用途为导出客户端等待；状态为存在；绑定位置为 `OrderExportProperties#timeoutMs`；值 `<redacted>`。
- 生效条件：`test` Profile 加载 `application-test.yml`，由 `ExportClientFactory` 在属性绑定成功时创建客户端。
- 数据源关系：订单数据源组与 `TABLE-order` 有直接关系；超时键本身与表字段无直接关系。

## 8. 相关变更包

| 变更包 | 处理状态 | MR / 提交 | 数据库文档 | 配置文档 | 与任务关系 | 基线影响 |
|--------|----------|-----------|------------|----------|------------|----------|
| `CHANGE-order-export-batch` | 已处理 | `MR-101` / `8f31c2a` | 无相关变化 | 无相关变化 | 与当前超时无直接关系 | 无 |
| `CHANGE-order-export-timeout` | 未处理 | `MR-118` / `b64d910` | 声明无字段变化，但代码查询字段变化 | 声明测试快照变化 | 直接相关 | `基线漂移` |

本 Skill 只读取用户点名的未处理包并报告漂移，不把它写入 `processed_packages`。

## 9. Debug 画像专属上下文

- 症状事实：测试环境调用订单导出 API 超时。
- 配置生效链：当前快照键 → `OrderExportProperties#timeoutMs` → `ExportClientFactory`。
- 数据访问链：`OrderExportService#createTask → OrderMapper#selectForExport → DATA-SOURCE-order-test → TABLE-order`。
- SQL / 字段状态：查询新增 `finished_at`，但数据库属性证据不足。
- 变更包状态：配置变化已声明，数据库“无变化”声明与代码字段使用存在冲突，且包未处理。
- 安全验证入口：检查现有单元/集成测试、脱敏日志和只读 SQL 计划资料；不执行应用、迁移或远程配置查询。

## 10. 约束与现有模式

- 配置快照只读，不输出敏感值或完整内部地址。
- 无完整 DDL 不阻断上下文收集，但不得补造字段属性。
- 未处理变更包不能替代 KnowledgeBase 基线。
- 当前工作区证据不清理、不覆盖。

## 11. 冲突、缺口与待确认项

| 优先级 | 类型 | 内容 | 影响 | 建议补证方式 |
|--------|------|------|------|--------------|
| 高 | 基线漂移 | `CHANGE-order-export-timeout` 未进入 `processed_packages` | KnowledgeBase 与当前发布候选不一致 | 完成 Debug 后由用户显式调用 Update 处理完整变更包 |
| 高 | 来源冲突 | 数据库文档声明无变化，代码新增查询 `finished_at` | 可能影响 SQL 可用性和性能判断 | 补充字段级数据库资料或修正变更包声明 |
| 中 | 数据模型证据缺失 | 无法确认 `finished_at` 类型、可空性和索引状态 | 不能断言 SQL 与真实结构兼容 | 提供 DDL、迁移或权威数据库文档 |

## 12. 下游使用建议

Debug 应先验证测试 Profile 的配置生效链和数据源路由，再核对 `selectForExport` 的 SQL 与字段状态；Review 应同步检查 MR、数据库文档、配置文档和完整变更包的一致性。本上下文不提供根因或修复方案。

## 13. 就绪状态

- 状态：有条件就绪
- 条件：调用链、配置生效链和数据源路由已定位；`finished_at` 的结构证据及未处理变更包冲突仍需补证。

## 异常分支

- 若测试配置外部目录不存在、不可读、越界或授权指纹失配，由于本任务依赖实际配置，状态改为 `阻断`，且不读取配置内容。
- 若未发现订单导出与任何配置的直接关系，则记录“无直接配置关系”并停止配置方向，不遍历全部配置快照。
- 若未发现订单导出与任何逻辑表的直接关系，则记录“无直接表关系”并停止数据模型方向，不扫描全部数据模型。
