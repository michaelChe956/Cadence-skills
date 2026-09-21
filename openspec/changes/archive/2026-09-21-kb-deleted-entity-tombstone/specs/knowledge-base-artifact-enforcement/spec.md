# knowledge-base-artifact-enforcement 变更增量（墓碑保留制）

## ADDED Requirements

### Requirement: 删除实体的墓碑表示

`knowledge-base-update` 删除实体时 MUST 采用墓碑保留制：实体的稳定 ID MUST 保持原样（MUST NOT 附加"（已删除）"等任何注记）；追溯矩阵中涉及该实体的历史行 MUST 原位保留，`关系类型` 不变，`证据状态` MUST 写 `已失效`，`关系证据` 列 MAY 追加删除提交；`evidence/relation-graph.yaml` MUST 保留该实体的墓碑节点（id/kind/label/doc 不变，`status: deleted`）及其全部失效边。证据状态枚举 MUST 扩为 `已确认 / 来源冲突 / 待确认 / 已失效`，其中 `已失效` 仅允许由 Update 删除流程产生，初始化阶段 MUST NOT 使用。等值校验口径不变：图边数等于矩阵全部数据行数（含已失效行）、图节点集包含矩阵两端（含墓碑节点）。

#### Scenario: 删除输入 API 后矩阵与图保持一致

- **WHEN** Update 删除 API-account-query（CAP 的输入 API）
- **THEN** 矩阵保留其历史行且 ID 无注记、证据状态为 `已失效`；图保留其墓碑节点与失效边；等值校验通过

#### Scenario: 初始化不得使用已失效

- **WHEN** 任一初始化领域 Skill 写入矩阵
- **THEN** 证据状态只允许 `已确认 / 来源冲突 / 待确认`，出现 `已失效` 判违规

#### Scenario: ID 注记被拒绝

- **WHEN** 更新后的矩阵行 ID 含"（已删除）"等注记
- **THEN** 违反稳定 ID 不可变规则，global-validation 判失败
