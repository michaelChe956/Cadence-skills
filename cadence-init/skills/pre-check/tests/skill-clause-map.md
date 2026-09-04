# pre-check 条款对账表

| 条款 ID | 约束 | 测试/证据 | 状态 |
|---|---|---|---|
| PC-REPORT-01 | 五阶段顺序为 `base-tools,openspec,superpowers-git,superpowers-links,verify` | `TestPhaseReport.test_check_has_five_timed_phases_and_legacy_steps` | Task 1 Step 1 |
| PC-REPORT-02 | phase 含非负整数 `duration_ms` 与计数项 | 同上 | Task 1 Step 1 |
| PC-REPORT-03 | `steps[]` 保留五个旧字段，顶层保留 `hints` | 同上 | Task 1 Step 1 |
| PC-REPORT-04 | stdout 只输出一份 JSON | `test_pre_check.py` 报告解析 | Task 1 Step 1 |

## Step 2 失败登记

当前旧实现仅汇总六工具，报告没有 `phases[]`，因此阶段报告测试按预期失败。
