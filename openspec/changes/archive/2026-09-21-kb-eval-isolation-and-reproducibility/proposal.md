# Proposal

## Why

kb-eval 的配对实验把「无 KB」作为对照臂，其结论成立的前提是**无 KB 臂真的看不到知识库**。这个前提此前只靠约定维持，实现上有两条泄漏路径，均在近期实测中被发现并修复：

1. 容器把宿主仓库只读挂在 `/opt/repo`，其中 `evals/kb/results/**` 含历史 KB 归档（包括实验所用 fixture 的知识库）；`install.sh` 经 `git clone` + overlay 把仓库装进 `~/.agents/Cadence-skills`，该目录同样对 agent 可读，其中 `evals/kb/cases.py` 即案例判据。
2. 把 KB 快照入库供复用时（本变更前的 PR #105），快照本身又经由上述两条路径进入容器——修复若不覆盖新增产物就会立刻失效。

另一处可复现性缺口：`prepare()` 造 fixture 临时 git 历史时未固定提交时间，每次 commit hash 都不同，与知识库 `manifest.yaml` 记录的 `baseline_commit` 对不上（B1 有 KB 臂实测出现过一次多余的基线核对）。

这两类约束目前只存在于实现与注释里，**未写入契约**：改 `run.py` 的人看不到「排除清单是契约」，新增同类产物时不会同步更新，泄漏会静默复发。

## What Changes

- 新增 requirement「评测环境隔离」：KB 产物与评测判据 MUST NOT 进入容器；约束 MUST 以**排除清单**表达（而非单一路径），且 MUST 同时覆盖 overlay 打包与容器内路径两处入口；装完 skills MUST 清除 skills 目录中的 harness 目录；新增同类产物 MUST 同步加入清单。
- 新增 requirement「可复现的 fixture 与 KB 快照」：fixture 临时 git 历史 MUST 固定提交时间（GIT_AUTHOR_DATE / GIT_COMMITTER_DATE），使提交 hash 跨运行稳定；配对实验所用 KB MUST 以**入库快照 + 溯源文件**提供，MUST NOT 依赖未入库的运行产物；`--restore-kb` MUST 以显式只读挂载注入快照，且重建快照时其 manifest 的 `baseline_commit` MUST 与确定性 fixture hash 一致。

两条 requirement 描述的是**已实现并已验证的行为**（本轮补写入契约），不引入新机制。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `kb-eval-pipeline`：新增「评测环境隔离」与「可复现的 fixture 与 KB 快照」两条 requirement。

## Impact

- `openspec/specs/kb-eval-pipeline/spec.md`：新增 2 条 requirement。
- 关联实现（已存在）：`evals/kb/run.py` 的 `EXCLUDE_PATHS` 与空目录覆盖、`evals/kb/runner/kb_runner.py` 的 `install_skills` 清除与 `prepare()` 固定提交时间、`evals/kb/fixtures/kb-archive/PROVENANCE.md`。
- 不触碰任何 skill、fixture 内容、CI 与既有 requirement。
