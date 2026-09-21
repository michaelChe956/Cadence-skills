# Proposal

## Why

`knowledge-base-artifact-enforcement` 的「关系类型闭合词表」requirement 写于第一批（`kb-matrix-contract-and-retrieval-fix`），当时横向 3 类（`COMPOSES` / `JOIN_KEY` / `PROVIDES_FIELD`）标注为"第二批启用"。第二批（`kb-composition-and-index-layer`）已实施并归档，词表资产 `assets/relation-types.md` 实际已改标为「已启用（2b）」（唯一写入方限定为组合层），`knowledge-base-composition` 主 spec 也已记录该事实。

但 artifact-enforcement 主 spec 中该 requirement 的正文与 scenario 仍停留在"第二批启用 / 供第二批能力组合层启用"，与产物现状及另一主 spec 的陈述**互相矛盾**——两个主 spec 对同一词表状态给出相反的要求。归档核对时发现（见归档提交 a38e5715 的说明），属第一批 delta 未随第二批同步的口径漂移。

## What Changes

- 修订 `knowledge-base-artifact-enforcement` 的「关系类型闭合词表」requirement：横向 3 类的状态表述由"第二批启用"改为「已启用（2b）」，并写入**唯一合法写入方为组合层（Overview 通道）**；`knowledge-base-api` 与 `knowledge-base-pages` 的矩阵写入行 MUST 仍限定纵向类型。
- 同 requirement 的 scenario「横向类型在第一批不可用」名称保留（其含义仍成立：第一批写入方即 api/pages 不可写横向边），仅更新 WHEN/THEN 为当前口径：api/pages 尝试写入横向边 → 写入被拒绝并登记待确认；横向边只能由组合层（Overview 通道）生成。
- 纵向 8 类枚举、"词表外类型被拒绝" scenario、"新增关系类型经 update 变更包同步" 等其余内容**不变**。

无行为变更：该口径在第二批已实现并对齐 `knowledge-base-composition` 主 spec，本变更仅消除主 spec 之间的表述矛盾。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `knowledge-base-artifact-enforcement`：修订「关系类型闭合词表」requirement 的横向类型状态表述与对应 scenario，使其与已实施的第二批口径及 `knowledge-base-composition` 主 spec 一致。

## Impact

- `openspec/specs/knowledge-base-artifact-enforcement/spec.md`：一处 requirement 的正文与一条 scenario 名称/内容。
- 不触碰任何 skill 文本、脚本、fixture 或 CI；`knowledge-base-composition` 主 spec 无需改动（其表述已是正确口径）。
