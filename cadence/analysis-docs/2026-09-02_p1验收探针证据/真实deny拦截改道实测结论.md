# p1 真实 deny 拦截-改道实测（2026-09-02）

- 场景：本仓库（已 apply：deny 区块 + codegraph MCP）headless Claude Code（glm-5.3-flash），任务"定位 run_verify 函数"
- 完整轨迹：① 模型首选 `Bash(grep -n ...)` → **被受管 deny 拦截**（tool_result："Permission to use Bash with command grep..."）
- ② 模型被拦后转 `Read`（命中 :4209 区域）→ ③ `mcp__codegraph__codegraph_explore`（拿调用方与影响面）→ ④ 答案精确（rule-config.py:4209，且主动区分了同名 run_eval）
- 结论：**"模型撞墙后自动改道"Spec 场景通过真实运行时验证**（此前交付边界中该场景仅机制级，本次补齐）；全程零人工介入，deny 未误伤任务完成
