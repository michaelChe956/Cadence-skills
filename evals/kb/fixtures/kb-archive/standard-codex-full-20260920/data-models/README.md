# 数据模型索引

## 当前范围与基线

| 项目 | 内容 |
|------|------|
| Manifest Schema | `4.0` |
| 数据模型状态 | 全量（来源 `user-input/data-model-scope.md`） |
| 不适用原因 | 不适用（数据模型领域适用） |
| 数据模型范围 | demo_user、demo_account、demo_order 三库，共 4 张逻辑表 |
| 基线提交 | 1f867b9fcdf95f2e11808454898f333d7d512e90 |
| 证据基线 | 1f867b9fcdf95f2e11808454898f333d7d512e90 |
| 排除范围 | 未纳入其他数据库/Schema；未发现分库分表物理分片；未发现迁移文件 |

## 数据库与 Schema

| 稳定 ID | 数据源 | 数据库/Schema | 数据库类型 | 业务域 | 逻辑表数 | 索引链接 |
|---------|--------|-------------|------------|--------|----------|----------|
| DB-demo_user | 用户服务数据源（`spring.datasource.*`） | demo_user | MySQL（方言由 DDL 与驱动推断） | 用户基本信息 | 1 | `data-models/DB-demo_user/README.md` |
| DB-demo_account | 账户服务数据源 | demo_account | MySQL | 用户账户 | 1 | `data-models/DB-demo_account/README.md` |
| DB-demo_order | 订单服务数据源 | demo_order | MySQL | 订单与导出文件 | 2 | `data-models/DB-demo_order/README.md` |

## 业务域、服务与数据源映射

| 业务域 | 服务稳定 ID | 数据源/Schema 稳定 ID | 配置组稳定 ID | 证据状态 | 证据位置 |
|--------|-------------|-------------------------|-----------------|----------|----------|
| 用户基本信息 | SERVICE-user-service | DB-demo_user | CONFIGGROUP-user-datasource | 已确认 | `user-service/src/main/resources/application.yml:6-9`、`db/init.sql:1-11` |
| 用户账户 | SERVICE-account-service | DB-demo_account | CONFIGGROUP-account-datasource | 已确认 | `account-service/src/main/resources/application.yml:6-9`、`db/init.sql:13-24` |
| 订单与导出文件 | SERVICE-order-service | DB-demo_order | CONFIGGROUP-order-datasource | 已确认 | `order-service/src/main/resources/application.yml`（数据源键）、`db/init.sql:26-38` |

## 逻辑表清单

| 稳定 ID | 数据库/Schema | 逻辑表 | 业务含义 | 读服务 | 写服务 | 证据状态 | 文档链接 |
|---------|---------------|--------|----------|--------|--------|----------|----------|
| TABLE-t_user | DB-demo_user | t_user | 用户基本信息 | SERVICE-user-service | 未发现 | DDL 已确认 | `data-models/DB-demo_user/TABLE-t_user.md` |
| TABLE-t_user_account | DB-demo_account | t_user_account | 用户账户（余额与状态） | SERVICE-account-service | 未发现（对账实现未提供） | DDL 已确认 | `data-models/DB-demo_account/TABLE-t_user_account.md` |
| TABLE-t_order | DB-demo_order | t_order | 订单（状态与金额） | SERVICE-order-service | SERVICE-order-service | DDL 已确认 | `data-models/DB-demo_order/TABLE-t_order.md` |
| TABLE-t_export_file | DB-demo_order | t_export_file | 订单导出文件登记 | 未发现 | 未发现 | DDL 已确认（读写链路未确认） | `data-models/DB-demo_order/TABLE-t_export_file.md` |

## 表关系导航

| 来源表稳定 ID | 关系 | 目标表稳定 ID | 关系证据 | 证据状态 | 详情链接 |
|---------------|------|---------------|----------|----------|----------|
| TABLE-t_user_account | 候选关联 `user_id` → `user_id`（未确认数据库外键） | TABLE-t_user | `db/init.sql:17` 字段注释“同 t_user.user_id”；`AccountEntity.java:5-6` 注释 | 待确认 | `data-models/DB-demo_account/TABLE-t_user_account.md` |
| TABLE-t_order | 候选关联 `user_id` → `user_id`（未确认数据库外键） | TABLE-t_user | `db/init.sql:31` 字段注释“同 t_user.user_id”；`OrderEntity.java:6-7` 注释 | 待确认 | `data-models/DB-demo_order/TABLE-t_order.md` |
| TABLE-t_export_file | 候选关联 `order_id` → `order_id`（无语义约束证据） | TABLE-t_order | `db/init.sql:36` 字段注释“关联订单” | 待确认 | `data-models/DB-demo_order/TABLE-t_export_file.md` |

> 同名字段不能单独证明数据库外键；上述关系仅作为候选关联记录，DDL 中未声明任何 `FOREIGN KEY` 约束（见 `open-questions.md` Q-M5）。关系类型词表中无表间关系枚举，故不写入追溯矩阵。

## 分库分表摘要

| 逻辑表稳定 ID | 分片键 | 分片规则 | 物理表规则 | 配置组稳定 ID | 证据状态 | 文档链接 |
|----------------|--------|----------|------------|-----------------|----------|----------|
| 全部 4 张逻辑表 | 未发现 | 未发现 | 未发现 | 不适用 | 待确认（未发现任何分片证据） | 各逻辑表文档“分库分表”章节 |

未发现分片中间件、路由规则或物理分片表；4 张表均按单一逻辑表建模，未重复建模任何物理分片。

## 覆盖率与证据新鲜度

| 数据库/Schema 稳定 ID | 范围内逻辑表 | 已生成字段级文档 | DDL/迁移确认 | 仅代码推导 | 待确认 | 最新证据时间 |
|------------------------|--------------|------------------|--------------|------------|--------|--------------|
| DB-demo_user | 1 | 1 | 1 | 0 | 0 | 2026-09-20 |
| DB-demo_account | 1 | 1 | 1 | 0 | 0 | 2026-09-20 |
| DB-demo_order | 2 | 2 | 2 | 0 | 1（读写链路） | 2026-09-20 |

## 来源冲突与待确认项

| 对象稳定 ID | 问题 | 来源 | 影响 | 处理状态 | 详情链接 |
|-------------|------|------|------|----------|----------|
| TABLE-t_user_account | `SELECT *` + 无 `resultMap`，`account_no` 到 `accountNo` 依赖未确认的驼峰映射设置 | `AccountMapper.xml:4-7`；配置中无 mybatis 设置 | 账户查询字段可能映射失败 | 待确认（Q-M3） | `data-models/DB-demo_account/TABLE-t_user_account.md` |
| TABLE-t_export_file | 仅有 DDL 与保留期常量，未发现写入/读取代码 | `db/init.sql:22-28`、`ExportService.java:9-10` | 导出登记链路不可确认 | 待确认（Q-M4） | `data-models/DB-demo_order/TABLE-t_export_file.md` |
| TABLE-t_user / TABLE-t_user_account / TABLE-t_order | 跨库 `user_id` 同源仅为注释与命名证据 | `db/init.sql`、各 Entity 注释 | 跨库关系不能作为数据库约束事实 | 待确认（Q-M5） | 本文件“表关系导航” |
