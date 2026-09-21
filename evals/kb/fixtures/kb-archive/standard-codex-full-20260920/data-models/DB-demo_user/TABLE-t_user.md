# t_user

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 逻辑表稳定 ID | TABLE-t_user |
| 数据库/Schema 稳定 ID | DB-demo_user |
| 逻辑表名称 | t_user |
| 物理表名称或规则 | `t_user`（未发现物理分片规则） |
| 业务域 | 用户基本信息 |
| 证据基线（必填） | 1f867b9fcdf95f2e11808454898f333d7d512e90 |
| 最后核验时间（必填） | 2026-09-20 |

> `证据基线`（本次分析 Git 基线提交）与 `最后核验时间`（本次分析日期）为必填字段；为空视为文档不完整，阶段不得完成。

## 2. 业务含义

用户基本信息表，保存用户唯一标识、姓名、手机号、邮箱与创建时间 [代码证据]（`db/init.sql:10` 表注释“用户基本信息表”；`user-service/src/main/java/com/demo/user/UserApplication.java:6` 服务注释“维护用户基本信息”）。对外由用户基本信息查询能力读取。

## 3. 字段清单

| 字段 | 类型 | 可空 | 默认值 | 主键 | 含义 | 代码映射 | 证据状态 | 证据位置 |
|------|------|------|--------|------|------|----------|----------|----------|
| `user_id` | `BIGINT` | 否 | DDL 未声明 | 是 | 用户唯一标识 | `UserEntity.userId`；`UserMapper.xml#selectById`（`user_id AS userId`） | DDL 已确认 | `db/init.sql:5`；`user-service/src/main/resources/mapper/UserMapper.xml:5` |
| `user_name` | `VARCHAR(64)` | 否 | DDL 未声明 | 否 | 用户姓名 | `UserEntity.userName`（`user_name AS userName`） | DDL 已确认 | `db/init.sql:6`；`UserMapper.xml:5` |
| `mobile` | `VARCHAR(20)` | 是（DDL 未声明 `NOT NULL`） | DDL 未声明 | 否 | 手机号 | `UserEntity.mobile` | DDL 已确认 | `db/init.sql:7`；`UserMapper.xml:5` |
| `email` | `VARCHAR(128)` | 是（DDL 未声明 `NOT NULL`） | DDL 未声明 | 否 | 邮箱 | `UserEntity.email` | DDL 已确认 | `db/init.sql:8`；`UserMapper.xml:5` |
| `created_at` | `DATETIME` | 是（DDL 未声明 `NOT NULL`） | `CURRENT_TIMESTAMP` | 否 | 创建时间 | 未映射（代码未使用该字段） | DDL 已确认 | `db/init.sql:9` |

> 证据状态只允许 `DDL 已确认`、`迁移已确认`、`代码可推导`、`用户提供`、`来源冲突`、`待确认`。缺少证据的属性单独写 `待确认`；不得依据 Entity、Mapper 或 SQL 补造实际索引、默认值或数据库约束。

## 4. 索引与约束

| 名称 | 类型 | 字段与顺序 | 定义 | 证据状态 | 证据位置 |
|------|------|------------|------|----------|----------|
| PRIMARY | 主键 | `user_id` | `PRIMARY KEY` | DDL 已确认 | `db/init.sql:5` |

除主键外未发现二级索引、唯一约束、外键、检查约束或触发器；实际数据库中是否存在其他索引无法从授权证据确认（未发现迁移或数据库导出）。

## 5. 分库分表

| 项目 | 内容 | 证据状态 | 证据位置 |
|------|------|----------|----------|
| 分片键 | 未发现 | 待确认 | 未发现分片配置或路由代码 |
| 分片规则 | 未发现 | 待确认 | 同上 |
| 物理表规则 | 未发现（按单表 `t_user` 建模） | 待确认 | `db/init.sql:4` |
| 配置组稳定 ID | 不适用 | 已确认 | `configurations/SERVICE-user-service.md` |

> 一张逻辑表只生成本文件一份；物理分片只记录规则，不为每个物理表复制文档。

## 6. Entity、Mapper 与 SQL 映射

| 类型 | 稳定 ID 或符号 | 操作 | 字段范围 | 证据位置 | 完整性限制 |
|------|----------------|------|----------|----------|------------|
| Entity | `CODE-UserEntity`（`com.demo.user.entity.UserEntity`） | - | `userId`、`userName`、`mobile`、`email` | `user-service/src/main/java/com/demo/user/entity/UserEntity.java:4-9` | 无 getter/setter 与注解；`created_at` 未建模 |
| Mapper 接口 | `CODE-UserMapper`（`com.demo.user.mapper.UserMapper`） | SELECT | `user_id` 条件 | `user-service/src/main/java/com/demo/user/mapper/UserMapper.java:10` | 仅一个查询方法 |
| Mapper XML | `CODE-UserMapperXml-selectById`（`UserMapper.xml#selectById`） | SELECT | `user_id`、`user_name`、`mobile`、`email` | `user-service/src/main/resources/mapper/UserMapper.xml:4-7` | 显式 `AS` 映射；无动态 SQL 分支 |

未发现 `INSERT`、`UPDATE`、`DELETE` 语句，因此本表写入链路缺失（不作为“数据库无写入”的事实，仅表示授权证据未覆盖）。

## 7. 读写服务

| 服务稳定 ID | 方法或入口 | 读/写 | 调用映射 | 证据位置 |
|-------------|------------|-------|----------|----------|
| SERVICE-user-service | `UserBasicService.queryBasic(Long)` | 读 | `UserMapper.selectById` | `user-service/src/main/java/com/demo/user/service/UserBasicService.java:18-20` |
| 未发现 | - | 写 | - | 未发现 `INSERT`/`UPDATE`/`DELETE` |

## 8. 关联 API 与页面

| 类型 | 稳定 ID | 名称 | 关系 | 证据位置 |
|------|---------|------|------|----------|
| API | 未生成（`api` 阶段尚未执行，本阶段不扫描接口） | - | - | `open-questions.md` |
| 页面 | 未生成（`pages` 阶段尚未执行，本阶段不扫描页面） | - | - | `open-questions.md` |

## 9. 特殊字段与数据规则

| 字段 | 规则类型 | 规则说明 | 证据状态 | 证据位置 |
|------|----------|----------|----------|----------|
| `user_id` | 标识 | 用户唯一标识，被 `t_user_account.user_id`、`t_order.user_id` 引用（候选关联，未确认外键） | 代码可推导 | `db/init.sql:5,17,28` |
| `created_at` | 默认值 | 未显式赋值时按数据库默认 `CURRENT_TIMESTAMP` | DDL 已确认 | `db/init.sql:9` |

## 10. 证据与来源冲突

| 对象或属性 | 来源 A | 来源 B | 冲突或限制 | 影响 | 处理状态 |
|------------|--------|--------|------------|------|----------|
| `user_id` 跨表引用 | `db/init.sql` 字段注释 | `AccountEntity.java:5-6`、`OrderEntity.java:6-7` 注释 | 均为注释/命名证据，DDL 无 `FOREIGN KEY` | 不能作为数据库约束事实 | 待确认（Q-M5） |
| 字段全集 | `db/init.sql:4-10` | 未发现迁移、数据库导出或人工资料 | 无法确认生产库结构是否与 DDL 一致 | 结构完整性有限 | 待确认（证据限制） |

## 11. 变更记录

| 日期 | 基线 | 变更内容 | 来源 |
|------|------|----------|------|
| 2026-09-20 | 1f867b9fcdf95f2e11808454898f333d7d512e90 | 首次生成字段级文档 | knowledge-base-base-info |
