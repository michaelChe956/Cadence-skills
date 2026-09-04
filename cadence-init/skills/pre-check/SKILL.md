---
name: pre-check
description: Use when setting up development environments or incrementally configuring npx/uvx/ast-grep/codegraph/openspec/superpowers tools without requiring user interaction. IMPORTANT - All user interactions MUST be in Chinese (中文) - triggers when tools need installation.
disable-model-invocation: true
---

# 前置条件检查

## 概述

本 Skill 通过关联脚本完成前置条件检查、OpenSpec 客户端产物补齐、Superpowers 同步和结构化复核。模型侧只负责定位脚本、在项目根调用一次脚本，以及读取报告并向用户呈现结果；确定性的安装、写入、同步和验证均由脚本处理。

脚本默认不收集任何私密信息，也不修改用户全局配置。`run` 可能在项目根写入 OpenSpec 客户端产物，并在需要时准备 Superpowers 来源及其技能链接；`check` 仅探测，不执行写入。Playwright 默认不启用，只有用户明确要求时才可选择。

## 参数边界

- 参数中的完整 token `no-interrupt` 或 `--no-interrupt` 表示无人工中断模式。
- 普通模式和 `--no-interrupt` 模式的失败语义不同，不能混用。
- 不询问、不收集、不验证 API Key、Token 或密码；真实密钥由用户自行在后续配置中替换占位符。
- `unsupported` 必须明确报告为需要人工处理，不静默改由模型自由编排。

## 执行契约

### 步骤 1：定位 skill 目录与绝对路径

在项目根执行 `pwd -P`，记为 `<PROJECT_ROOT>`；从当前 skill 目录拼出 `<PRE_CHECK_SH>=<skill-dir>/scripts/pre-check.sh`。不要进入 skill 目录或复制脚本；脚本依赖同目录 `scripts/mirrors/{default,cn}.sh`。

### 步骤 2：在项目根一次调用脚本

仅执行一次与参数相符的命令：

```bash
cd "<PROJECT_ROOT>" && bash "<PRE_CHECK_SH>" run [--mirror cn] [--no-interrupt]
```

仅探测用 `check`；升级只在明确要求时添加 `--upgrade`。stdout 为一份 JSON，stderr 为中文摘要；不得自行改写安装、OpenSpec、Git 或软链命令。

脚本调用必须保持项目根 cwd。除显式传入的 `--mirror cn`、`--no-interrupt` 和 `--upgrade` 外，不自行拼接额外流程；报告文件由调用方按既有生命周期管理。

### 步骤 3：读取 JSON 报告并呈现

读取 `overall`、原有 `steps[]` 和五项 `phases[]`，呈现 `result/action/duration_ms/created/updated/skipped/conflicts`；Superpowers phase 呈现 `origin/branch/before_revision/after_revision`。`overall=success` 且五阶段通过才报告完成；重跑以 phase `skipped`/`all-skipped` 和产物无变化证明幂等。

`--no-interrupt` 任一 phase failed 或脚本非零立即停止，报告失败原因、已完成 phase 和恢复建议；普通模式也不自行执行未覆盖写入。`unsupported` 必须报告人工处理，不静默回退模型自由编排。

Playwright 仅用户明确要求时 opt-in，未要求不安装、不写入。API Key 只展示 `your_zhipu_api_key`、`your_minimax_api_key` 占位符和安全提醒，不询问、不收集、不验证真实密钥。

## 报告与边界说明

脚本报告保留兼容的 `steps[]`，并提供固定顺序的五项 `phases[]`：`base-tools`、`openspec`、`superpowers-git`、`superpowers-links`、`verify`。呈现 phase 时以脚本返回的 `result` 和计数为准，不根据模型侧猜测补写状态。

普通模式下，失败 phase 可被记录为 `partial` 并继续脚本规定的后续阶段，最终必须如实报告整体状态；这不表示成功，也不允许自行补做脚本未覆盖的写入。`--no-interrupt` 下失败立即阻断下游写入。阶段错误应说明失败原因、已完成 phase 和恢复建议。

软链拓扑以解析后最终等价为准：现网直连源路径、兼容中转链均视为同一有效拓扑；已有正确链接应保持幂等，非目标用户内容不得被触碰。冲突和不可支持的布局按报告语义转人工处理。

默认 Playwright 行为是跳过，不安装、不写入；只有用户明确提出浏览器自动化需求时才执行 opt-in。API Key 仅保留以下安全提醒：

- 智普配置使用 `your_zhipu_api_key` 占位符。
- MiniMax 配置使用 `your_minimax_api_key` 占位符。
- 不收集真实密钥，用户应自行替换占位符。

🔴 安全提醒：请不要将 API Key 直接告诉 Claude Code。稍后在 MCP 配置步骤中，配置文件会使用占位符，您需要自行替换为真实密钥。

## 失败处理

- 基础工具 phase 失败时，按当前模式遵循脚本报告：无人工中断模式停止并返回非零；普通模式保留 `partial`/`failed` 状态和恢复建议。
- OpenSpec、Superpowers 或复核 phase 失败时，不将失败降级为成功，也不执行脚本之外的替代写入。
- `unsupported`、冲突、来源不可用或验证失败均须明确标注人工处理边界。
- 任何完成声明都必须同时满足 `overall=success`、五项 phase 通过和报告中的产物状态要求。
