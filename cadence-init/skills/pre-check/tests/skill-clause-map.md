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
| PC-GIT-01 | Superpowers 来源目录必须是 Git work tree；非 Git 立即失败，不做本地兜底 | `TestSuperpowersGitPhase.test_non_git_source_fails_without_local_fallback` | Task 3 |
| PC-GIT-02 | 候选在脚本内逐项解析，最多 3 项；clone 失败逐候选报告并清理临时目录 | `test_all_clone_candidates_fail_cleans_temp` | Task 3 |
| PC-GIT-03 | zsh 外层执行时每个候选保持独立 argv，不发生字符串拼接 | `test_candidates_are_each_argv_element_under_zsh` | Task 3 |
| PC-GIT-04 | Git 单候选超时返回结构化 124，失败不产生写入 | `test_single_candidate_timeout_is_structured` | Task 3 |
| PC-GIT-05 | 已有仓库使用 fetch + pull --ff-only；revision 不变记 skipped，并报告 Git 元数据 | `test_fetch_pull_revision_idempotence_and_metadata` | Task 3 |
| PC-GIT-06 | 当前 origin 命中第二候选时不重写 origin | `test_origin_matching_second_candidate_is_not_rewritten` | Task 3 |
| PC-GIT-07 | 连续延迟候选消耗 phase 预算，耗尽后停止并报告 phase-timeout | `test_delayed_candidates_consume_budget_and_stop_after_exhaustion` | Task 3 |


当前旧实现仅汇总六工具，报告没有 `phases[]`，因此阶段报告测试按预期失败。
