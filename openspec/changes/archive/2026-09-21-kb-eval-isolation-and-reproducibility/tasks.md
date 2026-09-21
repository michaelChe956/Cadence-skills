# Tasks

> 高层工作包；本变更为契约补充（实现已完成），无独立 Plan 文档。

## WP1 契约化隔离要求 [R1 评测环境隔离]

在 `kb-eval-pipeline` 新增「评测环境隔离」requirement：KB 产物（运行产物目录与入库快照）与评测判据 MUST NOT 对被测 agent 可见；约束 MUST 以排除清单表达；MUST 同时覆盖 overlay 打包与容器内路径两处入口；装完 skills MUST 清除 skills 目录中的 harness 目录；新增同类产物 MUST 同步登记。

验收：requirement 含上述四项约束，且每条都有 WHEN/THEN scenario；与 `run.py` 的 `EXCLUDE_PATHS` 实现逐条对应。

## WP2 契约化可复现要求 [R2 可复现的 fixture 与 KB 快照]

新增「可复现的 fixture 与 KB 快照」requirement：fixture 临时 git 历史 MUST 固定提交时间使 hash 稳定；配对实验所用 KB MUST 以入库快照 + 溯源文件提供，MUST NOT 依赖未入库运行产物；`--restore-kb` MUST 以显式只读挂载注入；重建快照时 manifest 的 `baseline_commit` MUST 与确定性 fixture hash 一致。

验收：requirement 含上述四项约束与对应 scenario；与 `prepare()` 的 `GIT_FIXED_DATE`、`kb-archive/PROVENANCE.md` 逐条对应。

## WP3 同步并归档 [R1, R2]

把两条 requirement 同步进主 spec，核对与既有 5 条 requirement 无重叠或冲突，`openspec validate --specs` 全绿后归档本变更。

验收：主 spec 由 5 条 requirement 增至 7 条；validate 通过；归档目录就位。
