# Proposal

## Why

kb-eval 四端 P3 专项验证发现规约空白：update skill 要求"删除实体：从活动清单移除，保留删除证据、旧关系和历史"，但未规定删除实体在追溯矩阵与关系图中的标准表示。codex 端按合理理解实现（矩阵历史行 ID 加"（已删除）"注记、图剔除节点）后，"图节点⊇矩阵两端"等值校验失败——删除语义与矩阵/图契约之间存在未定义地带，各端表示法必然发散。

## What Changes

- **墓碑保留制**：删除实体的稳定 ID 保持原样（禁止注记后缀）；矩阵历史行原位保留、`证据状态` 使用新枚举值 `已失效`、证据列可追加删除提交；关系图保留墓碑节点（`status: deleted`）与失效边。
- 证据状态枚举：矩阵模板与 base-info 门禁的合法值由 `已确认/来源冲突/待确认` 扩为含 `已失效`（仅 Update 删除流程产生，初始化不得使用）。
- update skill 删除实体条目展开为五条墓碑规则；base-info 图契约 nodes 增补墓碑语义。
- 等值校验口径不变（行/边/节点三者同保留，`图边数==矩阵行数`、`节点⊇两端` 天然成立）。

无 BREAKING：`已失效` 为新增枚举值；存量知识库无该状态不受影响。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `knowledge-base-artifact-enforcement`: 追溯矩阵证据状态枚举扩充 `已失效`（仅 Update 产生）+ 墓碑行规范 + 关系图墓碑节点契约。

## Impact

- `cadence-init/skills/knowledge-base-base-info/assets/traceability-matrix-template.md`（枚举+规则 6）
- `cadence-init/skills/knowledge-base-base-info/SKILL.md`（§8 门禁 1/4）
- `cadence-init/skills/knowledge-base-update/SKILL.md`（§4 删除实体条目展开）
- 设计文档：`cadence/designs/2026-09-21_方案设计_删除实体的矩阵与图表示_v1.0.md`
