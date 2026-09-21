# knowledge-base-artifact-enforcement 变更增量（横向关系类型口径对齐）

## MODIFIED Requirements

### Requirement: 关系类型闭合词表

`knowledge-base-base-info` MUST 提供 `assets/relation-types.md` 闭合枚举词表；写入矩阵的关系类型 MUST 取词表枚举值，不命中词表时 MUST 拒绝写入该行并登记待确认项。词表 MUST 含纵向 8 类（`CONTAINS`、`READS`、`WRITES`、`MAPS_TO`、`CONSUMED_BY`、`BINDS`、`DEPENDS_ON`、`IMPLEMENTED_BY`）与横向 3 类（`COMPOSES`、`JOIN_KEY`、`PROVIDES_FIELD`）；横向 3 类 MUST 标注"已启用（2b）"，且 MUST 限定组合层（Overview 通道）为其唯一合法写入方，`knowledge-base-api` 与 `knowledge-base-pages` 的矩阵写入行 MUST 仍限定纵向类型。新增关系类型 MUST 经 `knowledge-base-update` 变更包并同步词表文件。

#### Scenario: 词表外类型被拒绝

- **WHEN** 领域 Skill 尝试写入关系类型不在词表枚举内的矩阵行
- **THEN** 该行不被写入，对应关系进入 `open-questions.md` 待确认

#### Scenario: 横向类型在第一批不可用

- **WHEN** `knowledge-base-api` 或 `knowledge-base-pages`（第一批写入方）尝试写入 `COMPOSES`/`JOIN_KEY`/`PROVIDES_FIELD` 边
- **THEN** 写入被拒绝并登记待确认；横向边只能由组合层（Overview 通道）生成
