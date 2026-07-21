# Proposal: add-pi-agent-support

## Why

Cadence 框架当前的客户端支持矩阵只覆盖 Claude Code 与 Codex：Superpowers 软链只同步到 `~/.claude/skills` 与 `~/.codex/skills/skills`，OpenSpec 只用 `--tools claude,codex` 初始化，MCP 只维护 `.mcp.json` 与 `.codex/config.toml`，路由规则中的客户端行为约定也只有 "Claude/Kimi" 与 "Codex" 两类。用户已把 pi 作为日常 coding agent 使用（本机 `~/.pi/agent/skills` 中的软链为手工维护），框架缺少对 pi 的一等支持，导致 pi 用户需要手工补齐环境且路由规则对 pi 客户端无明确行为约束。

## What Changes

- `pre-check` Skill 的 Superpowers 软链同步增加第四个目标目录 `~/.pi/agent/skills`，与现有 claude/codex 目标共用同一套增量、冲突与失效清理规则。
- `pre-check` Skill 的 OpenSpec 初始化命令对新项目使用 `openspec init --tools claude,codex,pi`；对已有 `openspec/config.yaml` 的项目，若缺少 pi 产物则先执行 `openspec init --tools pi`，再执行 `openspec update`，若 pi 产物已存在则直接执行 `openspec update`。验证与增量说明同步覆盖 pi 产物（`.pi/prompts/opsx-*`、`.pi/skills/openspec-*`）。
- `pre-check` Skill 新增一项条件检查"pi MCP Adapter"：仅在检测到 pi 环境时检查/全局安装 `pi-mcp-adapter`（`pi install npm:pi-mcp-adapter`）；未安装 pi 的环境跳过且不算失败。
- `mcp-configuration` Skill 增加 pi 说明：pi 无原生 MCP，由 pi-mcp-adapter 直接读取项目 `.mcp.json`（含 HTTP 类型 server），不维护第二份客户端配置文件。
- `rule-config` 的路由规则模板（`agent-routing-kernel.md`、`openspec-superpowers-workflow.md`）增加 pi 客户端行为约定；`mcp-servers.md` 模板与 `rule-config` 的 codegraph 章节补充 pi 相关说明。

非目标：

- 不修改 `cadence-workflow`（legacy，后续废弃）。
- 不修改根目录 `install-offline.sh/.bat`（Claude marketplace 安装，与本变更无关）。
- 不自建 pi MCP 扩展，不维护 pi 专属 MCP 配置文件。
- 不升级本仓库根 `AGENTS.md`/`CLAUDE.md` 自身的受管区块（模板更新后另行重跑 rule-config 升级）。

## Capabilities

### New Capabilities

- `pi-agent-support`: cadence-init 对 pi coding agent 的环境支持，包括 Superpowers 软链的 pi 目标目录、OpenSpec 的 pi 工具初始化、pi MCP adapter 的条件检查与安装、MCP 配置的 pi 消费方式说明，以及路由规则中 pi 客户端的行为约定。

### Modified Capabilities

（无——现有 specs 均不涉及 pre-check/mcp-configuration/rule-config 的客户端支持矩阵。）

## Impact

- 受影响文件（全部位于 `cadence-init/` 内，均为 Markdown 文档）：
  - `cadence-init/skills/pre-check/SKILL.md`
  - `cadence-init/skills/mcp-configuration/SKILL.md`
  - `cadence-init/skills/rule-config/SKILL.md`
  - `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`
  - `cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md`
  - `cadence-init/skills/rule-config/references/rules/mcp-servers.md`
- 外部依赖：`openspec` CLI ≥ 1.4.1（原生支持 `--tools pi`，已实测）；npm 包 `pi-mcp-adapter`（第三方 pi 扩展，直接读取 `.mcp.json`）；pi 自带的 `pi install` 包管理命令。
- 行为影响：仅新增能力，对已有 claude/codex 流程无破坏；未安装 pi 的环境行为不变（条件跳过）。
