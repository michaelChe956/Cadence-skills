# KB 快照溯源

本目录是一份**知识库产物快照**，用作 kb-eval 配对实验中「有 KB 臂」的输入（`--restore-kb`）。
它不是评分标准（评分标准是 `evals/kb/cases.py` 的检查项），也不是答案。

## 来源

| 项 | 值 |
|----|----|
| 目录 | `standard-codex-full-20260920` |
| 生成方式 | `python3 evals/kb/run.py --agent codex --variant full`（一次完整六阶段建库） |
| 原始位置 | `evals/kb/results/2026-09-20/codex-full/knowledge-base/`（运行产物目录，不入库） |
| 规模 | 65 个文件 / 568 KB |
| 知识库 Schema | `4.0`（`manifest.yaml:generator.version`） |
| 生成时间 | `2026-09-20T14:30:45Z`（`manifest.yaml:generated_at`） |
| 构建端 | agent `codex`，model `deepseek-flash`，CLI `codex-cli 0.155.1` |
| 配置快照指纹 | `92bb968da5721d10403cbe72a128a492ea6c5fa2220788b73…`（同批 `results.json`） |
| 对应 fixture | `evals/kb/fixtures/standard/` |

## 已知差异（构建于 prepare 固定提交时间之前）

该快照的 `manifest.yaml:baseline_commit` 为 `1f867b9fcdf95f2e11808454898f333d7d512e90`，
是**当时** fixture 临时 git 仓库的首提交。`prepare()` 现已固定 `GIT_AUTHOR_DATE` /
`GIT_COMMITTER_DATE`，fixture 的提交 hash 变为确定值：

```text
首提交（init）      b0a9d750dcc434a85496b504de8ce79266ba3342
修复提交（retention） 9250c69c5a8d7eb368c19d5e15a5031b1b8a7040
```

两者**源码内容一致**，仅提交元数据不同；因此有 KB 臂的 agent 可能在核对「基线漂移」上
多花少量注意力（B1 实测出现过一次）。**重新生成一次 KB 即可消除该差异**。

> **重建时机（2026-09-21 决策）**：不单独为消除该差异重跑，**推迟到 KB 建库类 skill 下次
> 改动之后一并重生成**，避免重复花费。改动上述 skill 或 fixture 时，按下方判定表执行重建，
> 并把新产物换新目录名入库、更新本文件与文档中的 `--restore-kb` 路径。

## 何时必须重新生成

| 改动 | 是否需重新生成 |
|------|---------------|
| `knowledge-base-bootstrap` / `-base-info` / `-api` / `-pages` / `-overview` 中影响产物的部分 | **是**（新 skill 产出不同知识库） |
| `evals/kb/fixtures/standard/**`（fixture 源码/DDL） | **是**（KB 绑定 fixture 基线） |
| `knowledge-base-context`（只影响读取方式，不产出 KB） | 否 |
| 评测 harness（`run.py` / `cases.py` / 隔离逻辑） | 否 |

重新生成后：把新产物复制到本目录（换新目录名，带上生成日期），更新本文件的来源表与
`manifest.yaml` 差异段，并同步 `README.md` 与 `VALUE-TEST-PLAN.md` 中的 `--restore-kb` 路径。

## 隔离要求

本目录**不得进入容器**：`evals/kb/run.py` 的 `EXCLUDE_PATHS` 已将其与
`evals/kb/results` 一并排除（overlay 打包排除 + 容器内空目录覆盖）。新增同类快照时
必须同步加入该清单，否则无 KB 臂可直接读到知识库。
