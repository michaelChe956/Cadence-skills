# 关系类型词表

> Owner：knowledge-base-base-info。写入 `evidence/traceability-matrix.md` 的关系类型闭合枚举。新增类型必须经 `knowledge-base-update` 变更包并同步本文件，不得私自扩展。

## 使用规则

- 写入矩阵的关系类型只允许取本词表枚举值；不命中的关系不得写入，登记待确认。
- 方向原则：与既有领域文档链路方向一致——调用/访问链取"消费方 → 提供方"（如 API → SERVICE/MODULE → TABLE）；表文档反查关联保持原方向 TABLE → API/PAGE。

## 纵向类型（第一批启用）

| 类型 | 语义 | 源 → 目标 | 对应 base-info §8 原表述 |
|------|------|-----------|--------------------------|
| `CONTAINS` | 服务包含模块 | SERVICE → MODULE | 服务 → 模块 |
| `READS` | 读取逻辑表 | SERVICE/MODULE、API → TABLE | 模块 → 逻辑表 / 逻辑表 → 读服务 |
| `WRITES` | 写入逻辑表 | SERVICE/MODULE、API → TABLE | 模块 → 逻辑表 / 逻辑表 → 写服务 |
| `MAPS_TO` | 逻辑表与 Entity/Mapper/SQL 映射 | TABLE → 代码符号位置 | 逻辑表 → Entity、Mapper 与 SQL |
| `CONSUMED_BY` | 逻辑表被 API/页面消费 | TABLE → API/PAGE | 逻辑表 → API 与页面 |
| `BINDS` | 配置组绑定数据源或分片规则 | CONFIGURATION → 数据源/分片规则 | 配置组 → 数据源或分片规则 |
| `DEPENDS_ON` | 服务/模块依赖中间件 | SERVICE/MODULE → MIDDLEWARE | SERVICE/MODULE → MIDDLEWARE |
| `IMPLEMENTED_BY` | 横切机制落位于配置与实现位置 | 横切机制 → CONFIGURATION/代码位置 | 横切机制 → 配置与实现位置 |
| `INVOLVES` | 流程/规则/作业涉及实体 | FLOW/RULE/JOB → API/PAGE/SERVICE/TABLE/CONFIGURATION | 业务域与异步任务影响链（第二批 2a 新增） |
| `PRODUCES` | 服务/模块生产领域事件 | SERVICE/MODULE → EVENT | 消息生产能力（第二批 2a 新增） |
| `CONSUMES` | 服务/模块消费领域事件 | SERVICE/MODULE → EVENT | 消息消费能力（第二批 2a 新增） |

## 横向类型（已启用（2b），唯一写入方为组合层）

| 类型 | 语义 | 源 → 目标 | 启用批次 |
|------|------|-----------|----------|
| `COMPOSES` | 组合能力由既有 API 组成 | CAPABILITY → API | 已启用（2b，能力组合层） |
| `JOIN_KEY` | 两个 API 的输出字段经同一表字段可关联 | API ↔ API | 已启用（2b，能力组合层） |
| `PROVIDES_FIELD` | API 提供某字段域 | API → 字段域 | 已启用（2b，字段域反向索引） |

自 2b（变更 kb-composition-and-index-layer）起横向类型启用，唯一合法写入方是组合层（knowledge-base-overview 生成 CAP 的通道）；api 与 pages 阶段的矩阵写入仍限纵向类型，写入横向边必须被拒绝并登记待确认。
