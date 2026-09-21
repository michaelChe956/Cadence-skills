# demo_order

## 当前数据库/Schema

| 项目 | 内容 |
|------|------|
| 稳定 ID | DB-demo_order |
| 数据源 | SERVICE-order-service 的 `spring.datasource.*` 配置键（值已脱敏，见 `configurations/SERVICE-order-service.md`） |
| 数据库类型 | MySQL（由 DDL 方言与 mysql-connector-java 8.0.33 推断） |
| 数据库/Schema | demo_order |
| 业务域 | 订单与导出文件 |
| 范围与排除项 | 范围：`t_order`、`t_export_file` 两张逻辑表；排除：未发现视图、函数、触发器、分区与分片表 |
| 证据基线 | 1f867b9fcdf95f2e11808454898f333d7d512e90 |

## 表清单

| 逻辑表稳定 ID | 逻辑表 | 业务含义 | 读服务 | 写服务 | 证据状态 | 字段级文档 |
|----------------|--------|----------|--------|--------|----------|------------|
| TABLE-t_order | t_order | 订单（状态与金额） | SERVICE-order-service | SERVICE-order-service | DDL 已确认 | `data-models/DB-demo_order/TABLE-t_order.md` |
| TABLE-t_export_file | t_export_file | 订单导出文件登记 | 未发现 | 未发现 | DDL 已确认（读写链路未确认） | `data-models/DB-demo_order/TABLE-t_export_file.md` |

## 主要关系

| 来源表稳定 ID | 关系 | 目标表稳定 ID | 关系证据 | 证据状态 | 详情链接 |
|---------------|------|---------------|----------|----------|----------|
| TABLE-t_order | 候选关联 `user_id` → `user_id`（本库外，未确认外键） | TABLE-t_user | `db/init.sql:28` 注释“同 t_user.user_id”；`OrderEntity.java:6-7` | 待确认 | `data-models/DB-demo_order/TABLE-t_order.md` |
| TABLE-t_export_file | 候选关联 `order_id` → `order_id`（未确认外键） | TABLE-t_order | `db/init.sql:37` 注释“关联订单” | 待确认 | `data-models/DB-demo_order/TABLE-t_export_file.md` |

## 读写服务

| 服务稳定 ID | 读逻辑表 | 写逻辑表 | Mapper/SQL 入口 | 证据位置 |
|-------------|----------|----------|-----------------|----------|
| SERVICE-order-service | TABLE-t_order | TABLE-t_order | `OrderMapper.selectById`、`OrderMapper.updateStatus` | `order-service/src/main/resources/mapper/OrderMapper.xml:4-9` |
| SERVICE-order-service | 未发现 | 未发现（`t_export_file`） | 未发现 Mapper 或 SQL | `order-service/src/main/java/com/demo/order/service/ExportService.java:5-11` |

## 分片规则

| 逻辑表稳定 ID | 分片键 | 分片规则 | 物理表规则 | 配置组稳定 ID | 证据状态 |
|----------------|--------|----------|------------|-----------------|----------|
| TABLE-t_order | 未发现 | 未发现 | 未发现 | 不适用 | 待确认（未发现分片证据） |
| TABLE-t_export_file | 未发现 | 未发现 | 未发现 | 不适用 | 待确认（未发现分片证据） |

## 未覆盖对象

| 对象 | 未覆盖原因 | 影响 | 所需证据 | 跟踪项 |
|------|------------|------|----------|--------|
| `t_export_file` 读写链路 | 未发现 Mapper、SQL 或服务调用 | 导出文件登记流程不可确认 | 持久化实现代码或人工资料 | Q-M4 |
| 订单其他写入路径 | 未发现创建订单、取消订单、支付标记的对外入口（`markPaid` 无调用方） | 订单状态迁移链路不完整 | 调用方代码或接口资料 | Q-M4 关联项 |
| 视图/函数/触发器/二级索引 | 工程内 DDL 与代码均未涉及 | 无法确认实际数据库对象全集 | 数据库导出或迁移脚本 | 无（当前范围内未发现） |
