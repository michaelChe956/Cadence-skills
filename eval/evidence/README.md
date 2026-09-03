# 取证证据目录

- `denial-fields-claude-<日期>.json`：fixture 人造真实 denial 的原始事件结构
  （本机 242 个真实会话中 permission_denial 出现 0 次，无自然样本；self-hosted 上以
  `python3 -m eval.runner.cli forensics-denial` 生成后提交入库）。
- 用途：校准 `eval/adapters/claude.py` 的 `DENIAL_MARKERS`；对应离线回放断言
  防止适配器回归。
- 该证据来自隔离 fixture，不含业务数据，可入库。
