<!-- 测试方案：KB 优化后复测用 -->
# KnowledgeBase 价值对比测试方案

> 目的：在**同一 coding agent**下，用配对实验证明「有无 KnowledgeBase」对任务结果的影响。
> 唯一变量 = 工作目录里是否提供 KB 环境；提问、源码、模型、超时全部一致。

## 一、测试目标与判定口径

| 维度 | 度量 | 目标 |
|------|------|------|
| 正确性/完整性 | 案例检查项通过数（25 项） | 有 KB 高于无 KB |
| 证据可靠性 | 回答中引用的不同文件数、行号定位数 | 有 KB 显著更高 |
| 耗时 | 每案例 `duration_s` | 有 KB 增加不超过 30% |
| 费用 | CLI 上报 `total_cost_usd` | 仅在 claude 端可得 |

**通过标准（建议）**：至少 **2 个案例**出现「无 KB 未达、有 KB 达到」的检查项，且**无任何案例退化**，且耗时增幅 ≤ 50%。否则判定「本轮未体现 KB 价值」。

## 二、固定实验条件（禁止变动）

1. **同一 agent + 同一 model**：两臂必须同端同模型，不得一边 claude 一边 codex。
2. **同一 fixture**：`evals/kb/fixtures/<standard|large>`，两臂逐字节相同源码 + 相同 git 两步历史。
3. **同一 prompt**：案例题面来自 `evals/kb/cases.py`，两臂共用，**禁止维护两套 prompt**。
4. **同一超时/轮次**：`--timeout-min`、`--max-turns` 两臂相同。
5. **每案例独立新会话 + 干净快照**：`setup_arms()` 每案例从 `BASE` 重建工作目录。
6. **KB 指纹留档**：`--restore-kb` 指向的 KB 快照，记录其 `manifest.yaml` 的版本/指纹与所在快照目录名；快照入库于 `evals/kb/fixtures/kb-archive/`，改动 KB 建库类 skill 或 fixture 后必须重新生成（见该目录 `PROVENANCE.md`）。

环境差异（唯一变量）：
- `arm=kb`：工作目录含 `cadence/knowledge-base/` + 根 `AGENTS.md`（KB 导航区块）
- `arm=nokb`：工作目录无 `cadence/`、无 `AGENTS.md`

## 三、已知隔离缺口（复测前建议加固）

- 容器内 `/opt/repo` 只读挂载含历史 `evals/kb/results/**/knowledge-base/`，理论上可被 agent 读到。
  当前靠「题面不涉及 evals 目录」缓解。**建议加固**：`run.py` 启动容器时不挂 `evals/kb/results`，或把 fixture 结果目录改名/加密。
- `arm=nokb` 的答案仍可能引用「遗留模块」等影子内容（正常，属噪声处理能力）。

## 四、执行命令

```bash
cd /home/michaelche/workspace/github/Cadence-skills

# ⓿ 若用 large fixture，先生成（确定性、幂等）
# python3 evals/kb/fixtures/gen_large.py

# ① 无 KB 臂
python3 evals/kb/run.py --agent <pi|codex|claude|kimi> --variant full \
  --fixture large --no-build --arm nokb --batch <批次号> \
  --cases S1-A,S1-B,S2-A,S3-A,S4-A,S5-A,S5-B --timeout-min 15

# ② 有 KB 臂（--restore-kb 收宿主路径，写 /opt/repo/... 会自动换算；入库快照见 fixtures/kb-archive/）
python3 evals/kb/run.py --agent <同一端> --variant full \
  --fixture large --no-build --arm kb --batch <批次号> \
  --restore-kb evals/kb/fixtures/kb-archive/standard-codex-full-20260920 \
  --cases S1-A,S1-B,S2-A,S3-A,S4-A,S5-A,S5-B --timeout-min 15
```

两臂**必须用同一批次号**，且**顺序执行**（容器名固定为 `kb-eval-<agent>`，不能并发）。

## 五、报告生成

```bash
python3 evals/kb/value_report.py --batch <批次号> --compare B1,B2 \
  --out evals/kb/reports/report-value-<批次号>.md
```

产物目录：`evals/kb/results/exp/<批次号>/<agent>-{kb,nokb}/`（运行产物，不入库）
- `value-{kb,nokb}-results.json`：结构化结果（prompt/回答/耗时/usage/检查项）
- `transcripts/<案例>.log`：原始回答全文（人工复核用）

价值报告入库于 `evals/kb/reports/`（`value_report.py` 默认输出该目录）；历史批次的结论以该目录报告为准。

## 六、案例集与判据

- 场景与案例：`evals/kb/cases.py` 的 `SCENARIOS` / `CASES`（5 场景 7 案例）
- 判据：声明式 `require_all` / `require_any` / `require_groups` / `forbid`，输出 `pass|fail|unknown` + 理由
- **报告渲染时用最新判据重新判定**（`value_report.rejudge`），因此改判据可回溯历史批次，无需重跑实验
- 判据为机械核验，报告同时附回答原文；结论必须人工抽检

## 七、KB 优化后建议追加的测试

| 追加项 | 目的 | 做法 |
|--------|------|------|
| 弱 agent 臂 | 强 agent 用 grep 就能弥补，弱 agent 才暴露「找不到」 | 同案例换 `--agent codex`（deepseek-flash） |
| 更大规模 | 线性扫描成本何时压不住 | `gen_large.py` 扩到千文件级 fixture |
| 词汇不通案例 | 测「域地图导航」价值而非关键词检索 | 新增案例：题面用词在代码中不出现 |
| 多轮重复 | 排除单轮偶然 | 同批次交错跑 2-3 轮，取中位数 |
| 费用维度 | 补上成本对比 | 用 `--agent claude`（唯一上报 `total_cost_usd` 的端） |

## 八、历史批次基线（供回归对比）

| 批次 | agent/model | fixture | 无 KB | 有 KB | 耗时倍数 | 引用文件数 |
|------|-------------|---------|-------|-------|---------|-----------|
| B1 | pi / glm-5.3 | standard（56 文件） | 25/25 | 25/25 | 2.30× | 54 → 114 |
| B2 | pi / glm-5.3 | large（172 文件） | 25/25 | 25/25 | 1.93× | 57 → 79 |

结论：强 agent + 该规模下**质量持平**；KB 的可测收益是**证据密度**，代价是约 2× 耗时。
复测时若出现「有 KB 提升」的检查项且无退化，即为 KB 优化见效的直接证据。
