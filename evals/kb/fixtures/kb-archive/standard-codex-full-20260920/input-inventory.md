# KnowledgeBase 输入解析清单

## 基本信息

- Schema 版本：`4.0`
- 输入根：`cadence/knowledge-base/user-input/`
- Base Info：`cadence/knowledge-base/user-input/base-info.md`
- product.md（可选）：`cadence/knowledge-base/user-input/product.md`
- 业务知识证据（可选）：test_sources `**/src/test/**`；adr_sources `未声明`（空列表）；git_history `enabled: true`，range `54959c91e603b42092331bf5ba3d90107bdb2bf1..HEAD`
- Git 仓库与分支：`/home/tester/work/project`（单仓多模块），分支 `master`
- 基线提交：`1f867b9fcdf95f2e11808454898f333d7d512e90`（HEAD）
- 初始化判定：首次初始化
- 初始化状态：in_progress
- 已完成阶段：无（`completed_stages: []`）
- 已跳过阶段及原因：无（`skipped_stages: []`；工程、数据模型、配置、中间件、接口、页面六领域均适用）
- 全局验收：pending
- 续跑依据：不适用
- 重新初始化授权来源：不适用
- 已发现固定产物：无
- 既有 Manifest 检查：不存在且无固定产物
- 清理重建范围：不适用
- 清理重建风险：不适用
- 用户已授权上述范围与风险：不适用
- 校验结果：通过

## 六领域范围

| 领域 | 状态 | 引用文件 | 解析范围 | 校验结果 | 不适用原因或缺失影响 |
|------|------|----------|----------|----------|----------------------|
| 工程信息 | 全量 | `cadence/knowledge-base/user-input/project-scope.md` | user-service、account-service、order-service（Java 后端）、web-portal（Vue3 前端），本地路径均存在 | 通过 | 不适用 |
| 数据模型 | 全量 | `cadence/knowledge-base/user-input/data-model-scope.md` | demo_user、demo_account、demo_order 三库；DDL 与 Mapper XML 证据 | 通过 | 未提供 `user-input/database-ddl.sql`；已有 `db/init.sql` 与其他结构证据，非阻断 |
| 配置 | 全量 | `cadence/knowledge-base/user-input/configuration-scope.md` | 快照 `baseline-config-v1`，3 个服务 application.yml | 通过 | 不适用 |
| 中间件 | 全量 | `cadence/knowledge-base/user-input/middleware-scope.md` | MySQL（三服务）、RabbitMQ（order-service） | 通过 | 不适用 |
| 接口 | 全量 | `cadence/knowledge-base/user-input/api-scope.md` | 对外能力清单 2 条（API-user-basic、API-order-export）；另有 1 条能力组合诉求为声明输入，待 API/Overview 阶段核实 | 通过 | 不适用 |
| 页面 | 全量 | `cadence/knowledge-base/user-input/page-scope.md` | web-portal（路由来源 `src/main.js`，存在） | 通过 | 不适用 |

## 数据模型来源

| 证据类型 | 路径或来源 | 环境 | 更新时间 | 纳入分析 | 校验结果 | 备注 |
|----------|------------|------|----------|----------|----------|------|
| DDL（可选） | `db/init.sql` | 本地工程 | 2026-09-20 | 是 | 通过 | 单文件含 demo_user / demo_account / demo_order 三库 4 表 |
| Mapper XML | `user-service/src/main/resources/mapper/UserMapper.xml` | 本地工程 | 2026-09-20 | 是 | 通过 | demo_user |
| Mapper XML | `account-service/src/main/resources/mapper/AccountMapper.xml` | 本地工程 | 2026-09-20 | 是 | 通过 | demo_account |
| Mapper XML | `order-service/src/main/resources/mapper/OrderMapper.xml` | 本地工程 | 2026-09-20 | 是 | 通过 | demo_order |
| Entity / 迁移文件 / SQL / 人工资料 | 未声明 | - | - | 否 | 不适用 | 工程内存在 Entity 与 Mapper 接口，由 BaseInfo 阶段按授权范围识别 |

## 配置快照

- 快照标识：`baseline-config-v1`
- 环境：开发（fixture 本地快照）
- 发布批次：`fixture-batch-001`
- 外部目录：`/home/tester/work/snapshots/baseline-config`
- 生成或获取时间：由 runner 生成（输入声明值）
- 快照指纹：`92bb968da5721d10403cbe72a128a492ea6c5fa2220788b736f9adab743aa71b`
- 范围摘要：三服务 application.yml 全量纳入（3 文件）
- 纳入文件数量或文件清单摘要：3 个 → `account-service-application.yml`、`order-service-application.yml`、`user-service-application.yml`
- 服务摘要：user-service、account-service、order-service
- 文件规则摘要：仅 `src/main/resources/application.yml`
- 来源类型：工作区配置导出快照（锁定）
- 目录可读：是
- 快照标识、环境与目录映射一致：是（本批次仅一个映射）
- 处理方式：只读且不复制
- 校验说明：按契约固定算法（相对路径升序 → `相对路径 + 制表符 + 文件 SHA-256` 有序清单 → 清单 SHA-256）在本阶段开始与写入前独立计算两次，结果一致且与声明指纹相符；仅记录指纹与计数，未复制配置内容或敏感值

## 接口分类来源

- 对外能力清单：`cadence/knowledge-base/user-input/api-scope.md`（权威清单）
- 执行范围：全量
- 指定能力：无（全量模式）

## 缺失输入

| 缺失项 | 目标路径 | 模板路径 | 影响 | 处理状态 |
|--------|----------|----------|------|----------|
| 无 | - | - | 六领域输入、引用文件、数据模型结构证据、配置快照与工程路径均通过校验 | 不适用 |
