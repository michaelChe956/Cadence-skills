# Design

## Context

第一批（`kb-matrix-contract-and-retrieval-fix`）定义关系词表时，横向 3 类只做定义、禁写入，故 requirement 写作"MUST 标注'第二批启用'"。第二批（`kb-composition-and-index-layer`）启用横向类型并把唯一写入方限定为组合层，该决策已写进 `knowledge-base-composition` 主 spec 与词表资产。

契约层因此出现两处对同一事实的相反表述。本变更只做口径对齐，不引入新机制。

## Goals / Non-Goals

**Goals:**

- artifact-enforcement 主 spec 的横向类型状态与词表资产（「已启用（2b）」）及 composition 主 spec 一致。
- 保留第一批已在执行的约束：词表外类型拒写、纵向/横向写入方边界、新增类型经 update 变更包。

**Non-Goals:**

- 不新增、不删除任何关系类型，不改 `relation-types.md` 与任何 skill 文本。
- 不引入词表状态机或版本字段（"2b" 只是批次归属标注，非运行时状态）。
- 不改动 `knowledge-base-composition` 主 spec。

## Decisions

- **用 MODIFIED requirement 修订，而非新加一条**：矛盾点在原 requirement 正文内部，另立新 requirement 会让同一主题出现两条约束。MODIFIED 携带该 requirement 的完整正文与全部存活 scenario，符合合并语义。
- **保留 scenario 名、只改内容**：OpenSpec 的 MODIFIED 合并按 scenario 名匹配且无改名机制（`findMissingCurrentScenarios` 按名计数，缺名即 ERROR 拒绝归档）。因此保留「横向类型在第一批不可用」之名——其字面含义仍成立（第一批写入方 api/pages 依旧不可写横向边），仅把 WHEN/THEN 更新为当前口径，避免留下与现状矛盾的正文。
- **不追溯改写归档 delta**：已归档的 `2026-09-21-kb-matrix-contract-and-retrieval-fix` 保留当时评审原文，历史记录不篡改；口径修正由本变更在主 spec 上体现。

## Risks / Trade-offs

- 风险：读者可能误以为本次放宽了横向写入权限。缓解：正文明确"唯一合法写入方为组合层（Overview 通道）"，且 api/pages 仍限纵向。
- 权衡：批次标注（2a/2b）留存在词表资产里属历史归属说明，不在 spec 中固化批次号以外的语义，避免再次漂移。
