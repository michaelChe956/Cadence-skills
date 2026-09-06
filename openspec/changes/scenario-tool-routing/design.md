## Context

详版设计见 `cadence/designs/2026-09-06_方案设计_场景化工具路由与gate分层_v1.0.md`（已用户批准），本文件为决策摘要。背景链：夜测 denial 取证（trust 失效/❌文案不可见/headless 无授权出口）→ 测试架构分析（主指标从未被度量）→ gate 误伤分析（5 项高误伤）→ 场景路由调研（九场景矩阵）。根本约束：Claude Code 权限系统无法表达任务场景，场景判断只有模型自身可做。

## Goals / Non-Goals

**Goals:** 工具选择准确率最大化（首次工具选择正确率主指标）；消除物理拦截误伤（默认零 deny）；规则文本与拦截价值可分别度量（三组夜测矩阵）。

**Non-Goals:** 权限系统实现任务场景门控（Claude Code 能力边界）；本期实现 PreToolUse hook（仅预留，协议未实测）；改动 MCP server 配置内容。

## Decisions

- **D1 九场景矩阵为规范源**（Markdown 表格置规则文件顶部；CLAUDE.md 投影 ≤12 行决策卡；YAML 元数据仅稳定字段）。理由：场景判断只有模型能做→语义必须常驻上下文；Markdown 人模型两读；单源+快照校验防漂移。备选"独立 skill 载体"被否：skill 是任务级触发，管不了每次工具选择的微决策。
- **D2 gate 三模式**：text 默认（零 deny）/safe opt-in（仅危险命令形态 deny）/strict opt-in（现行全量，实验回归用）。理由：5 项代码 deny 高误伤（规则正文明确允许的场景被拦）；WebSearch/WebFetch 不 deny（R 场景它们是首选）；危险命令形态是唯一"参数可识别且无合法场景"的窄面。备选"仅收窄不反转默认"被否：主指标数据显示文本有效性前，默认拦截无依据。
- **D3 ❌ 文案条目废除**。实证（2026-09-06 夜测 raw denial）：模型看到的只有 Claude 通用拒绝文案，引导职责回归规则正文矩阵。
- **D4 元数据 schema v2**：解析器兼容读 v1 不产生 deny（旧项目无破坏）。
- **D5 夜测三组矩阵+场景化探针**：control 裸/installed-text（主指标）/installed-gate-safe（对照）；探针按 D/R/C/M/S/G/T/F/U 重编，每场景≥3 正反例（反例断言不误伤，如 M 场景 rg 不被拦）；五指标（first_tool_accuracy 主/task_completion/route_recovery/false_positive_block/denial_count）。
- **D6 夜测 trust 修复为前置**：fixture 写入 `hasTrustDialogAccepted` + 启动断言 stderr 无 `Ignoring ... permissions.allow`；探针 argv 白名单补 `mcp__codegraph`。否则 allow 失效继续污染 gate 组结果。

## Risks / Trade-offs

- 路由表注意力稀释 → 决策卡 ≤12 行置顶+矩阵置顶；夜测 first_tool_accuracy 度量迭代
- 默认零 deny 后无物理兜底 → 主指标数据先证明文本有效；strict 保留 opt-in；后续 hook 补参数级兜底
- 九场景边界模糊（C vs M）→ 判断信号操作化+正反例探针校准
- 旧 gate 区块迁移 → 检测无模式标记旧区块时提示用户显式选择，不静默沿用

## Migration Plan

1. 规则文件重构+元数据 v2（rule-config 分发幂等覆盖）
2. gate 生成器三模式+迁移提示；`--remove-permission-gate` 不变
3. 夜测 fixture/探针/评分三层改造（trust 修复先行）
4. 既有业务项目升级：apply 幂等重分发新规则；检测旧区块提示选择模式

## Open Questions

- PreToolUse hook 的 allow/deny/ask 协议与软提示模型可见性（期 4 实测后再定，前三期不依赖）
