# FILE-order-export-file 订单导出文件

> **能力 ID**：`FILE-order-export-file`
> **分类**：对内
> **能力类型**：文件
> **数据来源**：工程扫描（`order-service` 代码、`db/init.sql`、git 提交 `1f867b9`）
> **梳理日期**：2026-09-20
> **参数与报文**：不适用（文件能力不生成配套参数与报文文件）

## 一、能力基础信息

| 项目 | 值 |
|------|----|
| 能力名称 | 订单导出文件 |
| API 名称或逻辑标识 | 未提供（无接口或客户端标识） |
| 分类 | 对内（用户对外能力清单未登记；清单中 `API-order-export` 为对应对外设计能力） |
| 能力类型 | 文件 |
| 协议与方法 | 未发现（无 FTP/SFTP/对象存储/HTTP 下载实现） |
| 路径或逻辑地址 | 未发现（`t_export_file.file_path` 为登记字段，未发现实际位置或命名规则） |
| 文件格式 | 未提供 |
| 是否需授权 | 不适用（未发现文件访问入口） |
| 版本 | 不适用 |
| 触发方或生产者 | 预期为 `SERVICE-order-service` / `MODULE-order-export`（无实现证据） |
| 接收方或消费者 | 未发现 |
| 生命周期状态 | 状态未知（仅存在 DDL 与保留期常量，无文件生成、登记、下载或清理实现） |

## 二、业务需求描述

- 保留期规则：导出文件保留 7 天后清理（`ExportService.RETENTION_DAYS = 7`，`ExportService.java:9-10`；`db/init.sql:39` 注释“导出时间；保留 7 天后清理”；git 提交 `1f867b9` 记录历史误配 30 天后修复为 7 天）；规则卡 `business/rules/RULE-order-export-retention.md`。
- 导出内容、文件命名、交付方式（下载链接、推送、对象存储）与清理执行者：未提供。
- 登记表 `t_export_file` 语义：记录导出文件与订单的关联（`order_id`）及文件路径（`file_path`）（`db/init.sql:35-40`）。

## 三、输入参数

不适用（未发现文件生成入口、上传或下载参数）。

## 四、输出参数

不适用（未发现文件产出实现）。

## 五、代码实现定位

### 5.1 用户清单与代码映射

| 来源 | 标识 | 结论 | 证据 |
|------|------|------|------|
| 用户对外能力清单 | 未登记文件类能力；仅有 `API-order-export`（REST） | 按规则归为对内能力 | `cadence/knowledge-base/user-input/api-scope.md:13` |
| 当前代码 | `ExportService`（仅保留期常量）、`ExportController.export()`（返回字面量） | 入口存在，文件能力未实现 | `order-service/src/main/java/com/demo/order/service/ExportService.java:5-11`、`controller/ExportController.java:10-13` |

### 5.2 实现清单

| 层级 | 符号 | 文件路径 | 状态 | 说明 |
|------|------|----------|------|------|
| 常量 | `ExportService.RETENTION_DAYS` | `order-service/src/main/java/com/demo/order/service/ExportService.java:9-10` | 已确认 | 值为 7，无任何调用方 |
| 表定义 | `t_export_file` | `db/init.sql:35-40` | DDL 已确认 | 字段 `id`/`order_id`/`file_path`/`created_at` |
| 生成实现 | 未发现 | - | 未发现 | 无文件写出、无对象存储客户端、无导出内容组装 |
| 登记实现 | 未发现 | - | 未发现 | 无 Entity、Mapper 或 SQL 引用 `t_export_file` |
| 交付实现 | 未发现 | - | 未发现 | 无下载接口、无上传/推送、无对象存储 SDK 依赖（`order-service/pom.xml:13-18`） |
| 清理实现 | 未发现 | - | 未发现 | 无调度任务或删除语句 |

## 六、调用链路

### 6.1 调用树

```text
FILE-order-export-file
└─ SERVICE-order-service / MODULE-order-export
   ├─ ExportService.RETENTION_DAYS = 7（ExportService.java:9-10）[无调用方]
   ├─ ExportController.export（ExportController.java:10-13）[返回字面量 "taskId"，不生成文件]
   └─ TABLE-t_export_file
      ├─ R/W：未发现（无 Entity/Mapper/SQL）
      └─ 字段 → order_id / file_path / created_at（仅 DDL 定义）
   └─ 链路状态：断开（设计意图存在，实现缺失）
```

### 6.2 分支与触发条件

| 条件 | 路径 | 结果 | 证据 |
|------|------|------|------|
| 调用 `POST /api/order/export` | `ExportController#export` | 仅返回字面量 `taskId`，不产生文件与登记记录 | `ExportController.java:10-13` |
| 保留期到期（7 天） | 期望触发清理 | 未发现任何清理实现或调度 | `ExportService.java:9-10`、`db/init.sql:39`；待确认 |
| 未发现其他触发点 | - | 文件能力不可达 | 全工程未发现文件读写代码 |

### 6.3 逐层调用明细

| 层级 | 符号 | 职责 | 下游 | 证据 |
|------|------|------|------|------|
| 常量 | `ExportService.RETENTION_DAYS` | 定义保留期 | 无（无引用） | `ExportService.java:9-10` |
| 入口 | `ExportController#export` | 返回字面量 | 无 | `ExportController.java:10-13` |
| 数据访问 | 未发现 | - | - | `order-service/src/main/resources/mapper/OrderMapper.xml` 仅 `t_order` |

## 七、数据模型与配置依赖

### 7.1 数据模型影响

| TABLE 稳定 ID | Schema/逻辑表 | 读写 | 涉及字段 | API 模型映射 | Mapper/DAO/SQL | 表字段证据状态 | 端到端映射状态 | 表文档链接 |
|---------------|---------------|------|----------|--------------|----------------|------------------|------------------|------------|
| TABLE-t_export_file | `DB-demo_order` / `t_export_file` | 待确认（推断应包含 W 与 R，无代码证据） | `order_id`、`file_path`、`created_at`（`id` 主键无生成方式） | 未发现（无文件模型或 DTO 与表字段的转换证据） | 未发现（无 Entity/Mapper/SQL） | DDL 已确认（`db/init.sql:35-40`） | 待确认（全链路缺失） | [`TABLE-t_export_file`](../data-models/DB-demo_order/TABLE-t_export_file.md) |

### 7.2 配置依赖

| 配置组稳定 ID | 服务配置实体 | 配置键 | 直接影响 | 环境/Profile | 生效条件与绑定 | 证据状态 | 配置文档链接 |
|----------------|--------------|--------|----------|--------------|--------------|----------|--------------|
| 未发现 | - | - | - | - | 未发现文件存储路径、对象存储凭证、FTP/SFTP 连接等配置键；`order-service` 授权快照仅 5 键（server/application/rabbitmq） | 不适用 | [`SERVICE-order-service`](../configurations/SERVICE-order-service.md) |

> 未发现任何存储端点凭证或路径配置，进一步表明文件能力未实现（不得以服务文件中的其他配置推断）。

## 八、中间件使用明细

### 8.1 缓存与队列

| 类型 | 名称或 Key 模式 | 读写方向 | 触发时机 | 证据 |
|------|-----------------|----------|----------|------|
| 未发现 | - | - | - | `order-service/pom.xml:13-18` |

### 8.2 消息

| Topic/Queue/Group | 方向 | 消息模型 | 重试与幂等 | 证据 |
|-------------------|------|----------|------------|------|
| 未发现（导出未发布消息） | - | - | - | `ExportService.java:5-11` |

### 8.3 搜索与本地缓存

未发现。

### 8.4 RPC 与下游 HTTP

| 服务 | 协议 | 版本或分组 | 触发条件 | 证据 |
|------|------|----------|------------|------|
| 未发现 | - | - | - | 未发现 HTTP 客户端或 RPC 依赖 |

### 8.5 文件与对象存储

| 协议或存储 | 逻辑位置 | 文件格式 | 触发方 | 接收方 | 证据 |
|------------|----------|----------|--------|--------|------|
| 未发现（无 FTP/SFTP/对象存储/本地文件写出） | 未发现 | 未发现 | 未发现 | 未发现 | `db/init.sql:35-40`（仅登记表）、`ExportService.java:9-10`（仅保留期） |

### 8.6 定时任务与批处理

| 任务 | 触发方式 | 并发与锁 | 重试与补偿 | 证据 |
|------|----------|----------|------------|------|
| 保留期清理（推断） | 未发现（无 `@Scheduled`、无调度框架） | 未发现 | 未发现 | `db/init.sql:39`、`ExportService.java:9-10` |

## 九、数据源与副作用分析

- 主数据来源：未发现（无文件生成与读取代码）。
- 实时查询或补充路径：无。
- 写入、副作用或异步结果：未发现（导出接口返回字面量，不写文件、不登记 `t_export_file`）。
- 事务、一致性和失败处理：未发现 `@Transactional`、重试或补偿；保留期清理无执行者，`t_export_file` 数据将无界增长（若未来启用写入）。

## 十、关键证据引用

| 引用 | 文件或资料位置 |
|------|----------------|
| 用户对外能力清单（未登记文件能力） | `cadence/knowledge-base/user-input/api-scope.md:10-13` |
| 保留期常量 | `order-service/src/main/java/com/demo/order/service/ExportService.java:9-10` |
| 入口（存根） | `order-service/src/main/java/com/demo/order/controller/ExportController.java:10-13` |
| 数据访问 | 未发现；表文档 `data-models/DB-demo_order/TABLE-t_export_file.md`、DDL `db/init.sql:35-40` |
| 配置依赖 | 未发现 |
| 中间件与外部调用 | 未发现 |
| 业务规则来源 | git 提交 `1f867b9`（保留期 30→7 天修复） |

## 十一、请求、响应或载荷示例

未提供（未发现文件格式、生成逻辑或交付方式）。
