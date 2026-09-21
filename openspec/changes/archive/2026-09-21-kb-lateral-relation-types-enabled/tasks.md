# Tasks

> 高层工作包；本变更为单点口径修订，无独立 Plan 文档。

## WP1 修订主 spec 的横向类型口径 [R1 关系类型闭合词表]

以 MODIFIED requirement 修订 `knowledge-base-artifact-enforcement` 的「关系类型闭合词表」：横向 3 类改标「已启用（2b）」并限定组合层为唯一写入方；api/pages 写入行仍限纵向；scenario「横向类型在第一批不可用」改名为「横向类型仅组合层可写」并更新 WHEN/THEN；纵向 8 类与"词表外类型拒写"保持不变。

验收：同步后主 spec 该 requirement 正文不再出现"第二批启用"，且 scenario 名与内容与词表资产、`knowledge-base-composition` 主 spec 三者一致。

## WP2 漂移复核与回归 [R1]

复核 `openspec/specs/` 全域：同一事实不得存在相反表述（横向类型状态、写入方边界）；确认词表资产与两个主 spec 的口径一致；`openspec validate --specs` 全绿。

验收：全域 grep 无"第二批启用"残留；validate 通过；归档后 `--archived` 本变更通过。
