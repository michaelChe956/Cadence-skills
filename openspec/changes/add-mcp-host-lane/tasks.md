# Tasks: add-mcp-host-lane

> 任务号与实施计划（cadence/plans/）对齐；每项验收指向 spec Requirement。

- [ ] T0 前置检查：基准事实复现入口（用户本机签名）、五端 transcript 路径宿主版确认
- [ ] T1 判定态词表常量与 schema 扩展（五态）+ 单测 → R1
- [ ] T2 curl 全序列前置门（initialize+initialized+鉴权；不过=ENV_FAIL 整轮不入表）+ 单测 → R2
- [ ] T3 PTY 交互驱动器（五端会话启动/发送/超时/退出 + 挂载清单先行固化）→ R3
- [ ] T4 run_user_mcp_probe 入口（M1-M3 自然语言 → 宿主 transcript 定位 → adapter → 五态路由；run_id=host- 前缀）→ R4
- [ ] T5 night.py M 组路由分流（M 组走宿主车道，P/R/D 不变）→ R5
- [ ] T6 report_matrix 五态符号与「M 组（宿主车道）」独立分组，不计健康度分母 → R6
- [ ] T7 首轮五端实测：复现基准签名（codex ⚙×3 / 其余 ✅ 或有因 ⛔⊘）+ 透视快照落档 → R7
- [ ] T8 文档收尾：README/手册同步 + 快照归档 → R7
