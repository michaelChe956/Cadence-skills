# kb-eval-pipeline 变更增量（隔离与可复现契约）

## ADDED Requirements

### Requirement: 评测环境隔离

kb-eval 的容器 MUST NOT 向被测 agent 暴露任何知识库产物或评测判据：历史 KB 归档（`evals/kb/results/**`）、入库的 KB 快照（`evals/kb/fixtures/kb-archive/**`）与评测自身的 harness 目录（含 `evals/kb/cases.py` 判据）均 MUST 不可读。该约束 MUST 以**排除清单**表达，MUST NOT 只登记单一路径；对清单中每个路径 MUST 同时封堵两处入口——overlay 打包排除，以及容器内该路径被空目录覆盖。安装 skills 完成后 MUST 清除 skills 目录中的 harness 目录。新增任何同类产物 MUST 同步加入排除清单。

#### Scenario: 无 KB 臂读不到知识库产物

- **WHEN** 无 KB 臂的 agent 在容器内按绝对路径或工作目录检索知识库产物
- **THEN** 运行产物目录与入库快照目录均不存在或为空，agent 无法取得任何知识库内容

#### Scenario: 判据不随 skills 安装进入环境

- **WHEN** 容器完成 skills 安装
- **THEN** skills 目录中不含 harness 目录，agent 读不到案例判据文件

#### Scenario: 新增同类产物必须登记

- **WHEN** 有新的评测产物目录需要随仓库分发（如新的 KB 快照）
- **THEN** 该路径被加入排除清单，overlay 与容器内两处入口均不暴露；未登记即视为违反本要求

### Requirement: 可复现的 fixture 与 KB 快照

fixture 的临时 git 历史 MUST 使用固定的提交时间（`GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE`），使首提交与修复提交的 hash 跨运行稳定。配对实验使用的知识库 MUST 以**入库快照**提供，并附溯源文件记录来源（构建端、模型、CLI 版本、配置快照指纹、Schema 版本、`baseline_commit`）与重建条件；MUST NOT 依赖未入库的运行产物。`--restore-kb` MUST 以显式只读挂载把快照注入容器，MUST NOT 经由仓库整体挂载暴露。重新生成快照时，其 `manifest.yaml` 记录的 `baseline_commit` MUST 与确定性 fixture 的提交 hash 一致。

#### Scenario: fixture 提交 hash 跨运行稳定

- **WHEN** 两次独立执行 fixture 准备流程
- **THEN** 首提交与修复提交的 hash 完全相同

#### Scenario: 有 KB 臂经显式挂载取得快照

- **WHEN** 有 KB 臂启动
- **THEN** 入库快照经单独的只读挂载进入工作目录，其溯源文件可查，且不依赖任何未入库目录

#### Scenario: 重建快照后基线一致

- **WHEN** 重新生成 KB 快照并入库
- **THEN** 其 `baseline_commit` 等于确定性 fixture 的首提交 hash，有 KB 臂不再需要核对基线漂移
