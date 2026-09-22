---
description: Subagent 角色指派与通道快照——仅 controller 需要（配置快照，随模型变更更新）
agents: main
---

# Subagent 角色指派快照

> **性质：配置快照，不是流程规范。** 随模型可用性变更而更新，频率高于其他规则。
> **可见性：仅主会话（controller）。** 子代理读不到本文件 —— 它们不需要知道派工链。
> 流程纪律见 `rule://subagent-protocol`。
>
> **最后更新：2026-09-22**

## 一、角色指派表

| 角色 | 指派 | 模型链（首位优先，其后为降级通道） | 全挂处置 |
|---|---|---|---|
| **实施（优先）** | **ds-task** | tydic-openai/deepseek-flash | 通知用户 |
| 实施（备选） | glm53-task | my-anthropic/glm-5.3 → tydic-openai/deepseek-flash | 通知用户 |
| **实施（最强）** | **max-task** | dihua-openai/gpt-6-astra | 等用户批准 |
| 实施（暂缓） | ter-task | dihua-openai/gpt-5.6-terra | 🟡 暂缓，等用户通知恢复 |
| 审查 | k3-reviewer | my-anthropic/kimi-for-coding → dihua-openai/gpt-5.6-sol | 通知用户 |
| 勘察 | glm5.3-f-scout | my-anthropic/glm-5.3-flash → bingqi/glm-5.3-flash | 通知用户 |
| 裁决 | oracle | my-anthropic/k3 → dihua-openai/gpt-6-astra → my-openai/gpt-5.6-sol | 分歧挂起等用户 |
| 联网调研 | researcher | bingqi/glm-5.3 | 通知用户 |

## 二、分层派工规则

- **大 / 多步实施** → `ds-task`（能力优先，当前首选 worker）。
- **机械小改 / 小任务** → `glm53-task`（快）。
- **过于复杂或繁琐的任务** → `max-task`。**不进常规派工链**：仅在 oracle 判定任务复杂度超出常规 worker 能力并给出建议后，由用户裁决是否使用。
- `ter-task` **当前暂缓派工**（用户裁定响应太慢），等用户通知恢复。
- 审查角色可多实例并行扩容；扩实例不等于换人。

## 三、通道运维

- **模型切换方式**：改 `~/.omp/agent/agents/<name>.md` 的 `model:` 列表（首位优先，降级通道留在其后）。
- **通道探针**：派工前可秒投一行探针，各角色一行回复即证健康。
- **通道故障表现**：`404 model_not_found` / `401 key disabled` / 挂起无响应。
- **降级纪律**：实施角色可按链自动降级；**审查与裁决角色不可自主换人**，不可用时通知用户。

## 四、维护说明

本文件由 `Cadence-skills/agent-rules/subagent-roster.md` 分发。
调整模型链时同时更新：本表 + 对应 `agent-defs/<name>.md` 的 `model:` 字段。
