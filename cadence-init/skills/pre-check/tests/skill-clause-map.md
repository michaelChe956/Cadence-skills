# pre-check 条款对账表

| 条款 ID | 约束 | 测试/证据 | 状态 |
|---|---|---|---|
| PC-REPORT-01 | 五阶段顺序为 `base-tools,openspec,superpowers-git,superpowers-links,verify` | `TestPhaseReport.test_check_has_five_timed_phases_and_legacy_steps` | Task 1 Step 1 |
| PC-REPORT-02 | phase 含非负整数 `duration_ms` 与计数项 | 同上 | Task 1 Step 1 |
| PC-REPORT-03 | `steps[]` 保留五个旧字段，顶层保留 `hints` | 同上 | Task 1 Step 1 |
| PC-REPORT-04 | stdout 只输出一份 JSON | `test_pre_check.py` 报告解析 | Task 1 Step 1 |

| PC-OS-01 | 检测四端 OpenSpec 投影，并按 `claude→codex→pi→kimi` 顺序形成缺失列表 | `TestOpenSpecPhase.test_only_missing_pi_kimi_are_initialized` | Task 2 Step 2 |
| PC-OS-02 | OpenSpec 仅初始化缺失客户端，`init --tools` 参数精确为缺失列表 | `TestOpenSpecPhase.test_only_missing_pi_kimi_are_initialized` | Task 2 Step 1/3 |
| PC-OS-03 | 部分缺失时最多执行一次 `openspec update`，并复核四端投影数量/路径 | `TestOpenSpecPhase.test_only_missing_pi_kimi_are_initialized` | Task 2 Step 3 |
| PC-OS-04 | 四端齐全时不执行 init/update，phase 记 skipped 且跳过数为 4 | `TestOpenSpecPhase.test_ready_projection_skips_update` | Task 2 Step 3/4 |
| PC-OS-05 | Claude/Codex 就绪投影内容保持不变 | `TestOpenSpecPhase.test_ready_projection_content_unchanged` | Task 2 Step 4 |
| PC-OS-06 | Pi/Kimi 投影数量不满足 sentinel 时 phase failed 且 conflicts 非零 | `TestOpenSpecPhase.test_wrong_pi_count_fails` | Task 2 Step 2/4 |


当前旧实现仅汇总六工具，报告没有 `phases[]`，因此阶段报告测试按预期失败。
