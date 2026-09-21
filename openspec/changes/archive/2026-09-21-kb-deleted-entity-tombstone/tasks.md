# Tasks

> 高层工作包；精确文件步骤由 writing-plans 展开（本变更极小，四文件各一处编辑+回归）。

## WP1 模板与门禁枚举扩充 [R 删除实体的墓碑表示]

traceability-matrix-template.md 规则 2 枚举 + 新规则 6（墓碑行规范）；base-info §8 门禁 1 枚举（含"仅 Update 产生"）；门禁 4 nodes 墓碑语义。

验收：三处枚举一致含 `已失效`；规则 6 与门禁 4 写明墓碑语义。

## WP2 update skill 删除条目展开 [R]

§4 "删除实体"条目展开为五条墓碑规则（ID 不注记/行保留+已失效/墓碑节点+失效边/删除证据/等值校验不变）。

验收：条目五规则齐全且与模板规则 6 一致。

## WP3 回归与 codex P3 复验 [R]

Tier-0 三件套回归绿；codex 端 P3 重放（--restore-kb + --probes P3）：矩阵 ID 无注记、证据状态含已失效、图含墓碑、等值通过。

验收：codex P3 PASS 或暴露新真实缺陷。
