# 追溯矩阵模板

> Owner：knowledge-base-base-info。本文件是 `evidence/traceability-matrix.md` 的唯一格式契约；knowledge-base-api、knowledge-base-pages、knowledge-base-overview 追加矩阵行时必须遵循同一结构。

## 表头（固定六列）

| 来源稳定 ID | 关系类型 | 目标稳定 ID | 关系证据（文件:行号） | 证据状态 | 详情链接 |
|------------|----------|------------|----------------------|----------|----------|

## 示例行

| 来源稳定 ID | 关系类型 | 目标稳定 ID | 关系证据（文件:行号） | 证据状态 | 详情链接 |
|------------|----------|------------|----------------------|----------|----------|
| API-internal-order-export | READS | TABLE-order | services/order/OrderMapper.java:88 | 已确认 | interfaces/API-internal-order-export.md#7.1 |
| SERVICE-order-service | CONTAINS | MODULE-order-core | services/SERVICE-order-service.md#模块与入口 | 已确认 | services/SERVICE-order-service.md |
| TABLE-user | CONSUMED_BY | API-USER-BASIC-QUERY | data-models/TABLE-user.md#8 | 已确认 | data-models/TABLE-user.md |

## 规则

1. `关系类型` 只允许取 `relation-types.md` 词表枚举值；不命中词表的关系不得写入矩阵，登记 `open-questions.md` 待确认。
2. `证据状态` 只允许 `已确认`、`来源冲突`、`待确认`、`已失效`；`已失效` 仅允许由 knowledge-base-update 的删除流程产生，初始化阶段不得使用。
3. `关系证据` 必须可定位（文件:行号）；`详情链接` 指向承载该关系的领域文档锚点。
4. 行按来源稳定 ID 字典序排列，同源行按关系类型分组；追加行保持排序，不重排既有行。
5. 同一（来源, 关系类型, 目标）三元组只保留一行；证据冲突时保留一行，证据状态写 `来源冲突`，证据位置列出全部来源。
6. 墓碑行（删除实体）：实体被 Update 删除后，其稳定 ID 保持原样（禁止"（已删除）"等任何注记），历史行原位保留、关系类型不变，证据状态写 `已失效`，关系证据列可追加删除提交（如 `删除提交 <sha>`）。
