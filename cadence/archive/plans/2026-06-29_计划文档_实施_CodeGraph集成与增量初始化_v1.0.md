# 计划文档：实施 CodeGraph 集成与增量初始化

**日期**：2026-06-29
**版本**：v1.0
**目标分支**：feat-b-0629
**关联方案**：`cadence/designs/2026-06-29_方案设计_CodeGraph集成与Serena检查_v1.0.md`

## 目标

在 Cadence 初始化链路中实现 CodeGraph 支持，并确保 `/pre-check` 与 `/rule-config` 可以反复增量执行。

## 实施范围

| 文件 | 目标 |
|------|------|
| `cadence-init/skills/pre-check/SKILL.md` | 增加 CodeGraph 检查、安装、验证和增量说明 |
| `cadence-init/commands/pre-check.md` | 增加 CodeGraph 安装章节和强制规则 |
| `cadence-init/commands/rule-config.md` | 增加 CodeGraph 项目初始化与增量补齐逻辑 |
| `cadence-init/commands/mcp-configuration.md` | 增加 CodeGraph MCP 手动兜底配置 |
| `cadence-init/references/rules/code-reading.md` | 增加 CodeGraph 与 `ast-grep outline` 分工 |
| `cadence-init/references/rules/mcp-servers.md` | 增加 CodeGraph MCP 使用规则 |
| `.claude/rules/code-reading.md` | 同步当前项目代码阅读规则 |
| `.claude/rules/mcp-servers.md` | 同步当前项目 MCP 规则 |
| `CLAUDE.md` | 更新代码阅读规则摘要 |
| `AGENTS.md` | 更新代码阅读规则摘要 |

## 执行步骤

1. 更新 `/pre-check`：
   - 基础检查从四项改为五项。
   - 新增 `codegraph version` 检查。
   - 新增 `npm i -g @colbymchenry/codegraph` 安装命令。
   - 明确重复运行时只补装缺失工具。

2. 更新 `/rule-config`：
   - 在代码阅读规则后新增 CodeGraph 项目初始化。
   - 命令固定为 `codegraph install --target=claude,codex --location=local --yes` 与 `codegraph init`。
   - 明确 `.codegraph/` 加入 `.gitignore`，`codegraph.json` 不忽略。
   - 明确重复运行时只补缺失规则、摘要、MCP 配置和初始化状态。

3. 更新 MCP 配置说明：
   - 增加 Claude Code `.mcp.json` 兜底片段。
   - 增加 Codex `.codex/config.toml` 兜底片段。
   - 写明 CodeGraph 是 stdio MCP，可同步到 Codex。

4. 更新规则文件：
   - `code-reading.md` 明确大范围检索用 CodeGraph，精确结构阅读用 `ast-grep outline`。
   - `mcp-servers.md` 增加 CodeGraph MCP 章节。

5. 更新入口摘要：
   - `CLAUDE.md` 与 `AGENTS.md` 的代码阅读规则摘要同步改为 CodeGraph + `ast-grep outline` 分工。

## 验证命令

```bash
rg -n "codegraph|CodeGraph|\\.codegraph|@colbymchenry/codegraph" cadence-init .claude CLAUDE.md AGENTS.md
rg -n "serena|Serena|\\.serena|mcp__serena" cadence-init
rg -n "大范围检索|精确结构阅读|ast-grep outline|反复增量|只补" cadence-init .claude CLAUDE.md AGENTS.md
git diff --check
```

## 验收标准

1. `/pre-check` 文档明确包含 CodeGraph 安装与增量补装。
2. `/rule-config` 文档明确包含项目级 CodeGraph 初始化与增量补齐。
3. Claude Code 与 Codex 的 CodeGraph MCP 配置均有兜底说明。
4. 代码阅读规则明确 CodeGraph 与 `ast-grep outline` 的职责边界。
5. `cadence-init/` 中不重新引入 Serena。
