# knowledge-base-artifact-enforcement 变更增量

## ADDED Requirements

### Requirement: 追溯矩阵格式契约

`knowledge-base-base-info` MUST 按 `assets/traceability-matrix-template.md` 的固定六列结构（来源稳定 ID、关系类型、目标稳定 ID、关系证据(文件:行号)、证据状态、详情链接）写入 `evidence/traceability-matrix.md`；证据状态 MUST 只允许 `已确认`、`来源冲突`、`待确认`。`knowledge-base-api` 与 `knowledge-base-pages` 追加矩阵行时 MUST 遵循同一模板格式。

#### Scenario: base-info 按模板建立关系矩阵

- **WHEN** `knowledge-base-base-info` 执行 §8 关系建立
- **THEN** `evidence/traceability-matrix.md` 表头为模板六列，每行关系均带可定位证据（文件:行号）与证据状态

#### Scenario: 下游领域追加矩阵行

- **WHEN** `knowledge-base-api` 或 `knowledge-base-pages` 更新清单触达 `evidence/traceability-matrix.md`
- **THEN** 追加行与既有表头列结构一致，不产生第二种行形状

### Requirement: 关系类型闭合词表

`knowledge-base-base-info` MUST 提供 `assets/relation-types.md` 闭合枚举词表；写入矩阵的关系类型 MUST 取词表枚举值，不命中词表时 MUST 拒绝写入该行并登记待确认项。词表 MUST 含纵向 8 类（`CONTAINS`、`READS`、`WRITES`、`MAPS_TO`、`CONSUMED_BY`、`BINDS`、`DEPENDS_ON`、`IMPLEMENTED_BY`）与横向 3 类（`COMPOSES`、`JOIN_KEY`、`PROVIDES_FIELD`）；横向 3 类 MUST 标注"第二批启用"，初始化与 Update 之外的任何写入 MUST NOT 使用横向类型。新增关系类型 MUST 经 `knowledge-base-update` 变更包并同步词表文件。

#### Scenario: 词表外类型被拒绝

- **WHEN** 领域 Skill 尝试写入关系类型不在词表枚举内的矩阵行
- **THEN** 该行不被写入，对应关系进入 `open-questions.md` 待确认

#### Scenario: 横向类型在第一批不可用

- **WHEN** 初始化或本批范围内的任何 Skill 尝试写入 `COMPOSES`/`JOIN_KEY`/`PROVIDES_FIELD` 边
- **THEN** 写入被拒绝；横向类型仅作为词表定义存在，供第二批能力组合层启用

### Requirement: global-validation 矩阵机械检查

`knowledge-base-bootstrap` 的 global-validation 内容完整性检查 MUST 新增第 5 项：`evidence/traceability-matrix.md` 存在时，表头列数与列名 MUST 等于模板六列，逐行关系类型 MUST 属于词表枚举；任一不符 MUST 判 `failed` 并保持 `status: in_progress` 与空 `completed_at`。

#### Scenario: 矩阵格式不合格阻断验收

- **WHEN** global-validation 发现矩阵表头非六列或存在词表外关系类型
- **THEN** 验收判 `failed`，只报告缺失项，不删除产物

### Requirement: 检索精确种子直取

`knowledge-base-context` 的渐进检索 MUST 支持精确种子直取：种子已含精确稳定 ID、精确文件路径或 Method+Path 时，MUST 直接定位该实体主文件并跳过总入口与领域索引读取，且 MUST 在本层证据摘要中记录"精确种子直取"与种子值；候选无法唯一定位时 MUST 回退完整索引路径。`references/progressive-retrieval-guide.md` 第 2 层与 `knowledge-base-context/SKILL.md` §2 MUST 保持一致，不得再出现"种子精度优先"与"索引优先"的矛盾。

#### Scenario: 精确种子跳过索引层

- **WHEN** 任务种子是精确稳定 ID（如 `API-internal-order-export`）
- **THEN** 知识库语义路径直接读取该实体主文件与一跳关系，不读总入口 README 与领域索引，证据摘要含直取留痕

#### Scenario: 直取失败回退

- **WHEN** 精确种子对应的实体文档缺失或无法唯一定位
- **THEN** 回退"总入口 → 铆域索引 → 稳定 ID"完整路径并记录回退原因

### Requirement: 漂移字段激活与陈旧度暴露

`knowledge-base-base-info` 的表文档模板 §1 元数据中`证据基线`与`最后核验时间` MUST 为必填，base-info 完成条件 MUST 校验两字段非空。`knowledge-base-overview` MUST 在 README 覆盖范围处暴露知识库 Git 基线与各领域最后核验时间（取该领域文档元数据最大核验时间）。本变更 MUST NOT 引入自动失效或自动更新机制；`knowledge-base-update` 变更包仍是唯一刷新入口。

#### Scenario: 表文档缺漂移字段不得完成阶段

- **WHEN** 范围内任一逻辑表文档的`证据基线`或`最后核验时间`为空
- **THEN** base-info 完成条件不满足，阶段不得标记完成

#### Scenario: 陈旧度对 Agent 可见

- **WHEN** Coding Agent 读取知识库 README
- **THEN** 可见知识库 Git 基线与各领域最后核验时间，无需逐文档翻查元数据
