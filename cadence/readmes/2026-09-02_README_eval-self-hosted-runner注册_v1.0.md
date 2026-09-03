# eval 体系 self-hosted runner 注册与告警（rule-eval-p0 / tasks 4.5）

## 一次性注册（维护者操作）

1. GitHub 仓库 Settings → Actions → Runners → New self-hosted runner，按平台
   下载配置脚本在本机执行；注册名建议 `cadence-eval-runner`。
2. 给 runner 打标签 **`cadence-eval`**（Tier-1 job 以
   `runs-on: [self-hosted, cadence-eval]` 路由）。
3. 生成 fine-grained PAT（仅本仓库、Actions 只读），配为仓库 secret
   **`EVAL_RUNNER_CHECK_TOKEN`**——云端探活 job 用它查询 runner 在线状态；
   不配置时探活默认放行，由 Tier-1 首步 mock 自检兜底。
4. 确认四端 CLI 已在本机登录：`claude --version && codex --version &&
   pi --version && kimi --version`；以
   `python3 -m eval.runner.cli pins-audit` 回填 `eval/config/agents.json`
   的 `cli_version` 后提交（版本锁生效）。
5. Kimi 入矩阵前置：在 self-hosted 上执行
   `python3 -m eval.runner.cli verify-kimi --base /tmp/kimi-verify`，
   全绿后把 `agents.json` 的 `kimi.enabled` 置 `true` 提交。

## 持久化目录

Tier-1 workflow 的 `EVAL_BASE` 固定为 **`$HOME/eval-runs`**，不要使用
`${{ runner.temp }}`；self-hosted runner 的 HOME 跨 job/夜间保留结果，支持断点续跑、
滚动 7 夜聚合和审计追溯。

## 告警通道

- **连续 ≥3 夜失败端**：每夜 report.md 置顶告警 + job summary 展示；
  端级失败不阻塞其余端（矩阵该列标 unavailable / 缺测，不误红）。
- **runner 离线**：cron 触发时探活失败 → Tier-1 skip 结束，主干 CI 不受影响。

## 手动补跑与 Tier-2

- 断点续跑：直接重跑同一日期 `python3 -m eval.runner.cli night --date <日期>
  --base <同基目录>`，已有结果 JSON 自动跳过。
- 手动触发：Actions 页面选 `Eval CI` → Run workflow（`workflow_dispatch`）。
  runner-probe 与 eval-tier1-nightly 均允许手动触发（探活默认放行规则不变：
  未配 token 时默认 true，Tier-1 首步 mock 自检兜底）；手动触发时 Tier-0
  也会一并执行（零真实 CLI，无害）——即 Tier-2 手动车道入口（同一矩阵，
  白天补跑）；夜日期按北京时间（Asia/Shanghai）判定，手动补跑请传当夜日期。
- Tier-2 可选 judge（LLM 过程评审，~$5–15/次）：不在本体系交付内，另行手动执行。
