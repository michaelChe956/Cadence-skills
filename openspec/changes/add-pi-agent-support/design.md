# Design: add-pi-agent-support

## Context

cadence-init 是 Cadence 框架的环境初始化插件，以 Markdown Skill 文档形式描述安装与配置逻辑（不写代码）。当前客户端支持矩阵：

- Superpowers 软链：`~/.agents/superpowers/skills/*` → `~/.agents/skills` → 分发到 `~/.claude/skills` 与 `~/.codex/skills/skills`（三层）。
- OpenSpec：`openspec init --tools claude,codex`，生成 `.claude/commands/opsx/`+`.claude/skills/openspec-*` 与 `.codex/skills/openspec-*`。
- MCP：项目级 `.mcp.json`（Claude Code 消费）+ 同步 `.codex/config.toml`（仅 stdio，Codex 不支持 HTTP MCP）。
- 路由规则：客户端行为约定只有 "Claude/Kimi"（连续工具事件+静默）与 "Codex"（显式选择+全文读取）两类。

pi 侧已确认的事实（勘察证据）：

- pi 全局 skills 目录为 `~/.pi/agent/skills/`（项目级为 `.pi/skills/`）；pi 原生也会读 `~/.agents/skills/`，但显式软链与 claude/codex 模式对齐，且用户本机已是此形态并正常工作。
- openspec CLI 1.4.1 原生支持 `--tools pi`，生成 `.pi/prompts/opsx-*.md` 与 `.pi/skills/openspec-*`（已在 /tmp 实测）。
- pi 官方不做原生 MCP（README: "No MCP"），只能通过扩展接入。npm 包 `pi-mcp-adapter`（v2.11.0，持续维护）安装后自动读取项目 `.mcp.json`，支持标准 stdio 与 HTTP 配置；全局安装位置 `~/.pi/agent/npm/node_modules/pi-mcp-adapter`，由 `pi install npm:pi-mcp-adapter` 写入 `~/.pi/agent/settings.json`，可执行文件软链位于 `~/.pi/agent/npm/node_modules/.bin/pi-mcp-adapter`。
- `codegraph install --target` 仅支持 claude/cursor/codex/opencode/hermes，不支持 pi；pi 经 `.mcp.json` + adapter 消费 codegraph MCP，无需额外动作。
- pi 调用 Skill 的机制是全文读取 SKILL.md（harness 在系统提示中列出可用 Skill 及其路径），行为特征与 Codex 类似。

约束：范围只在 `cadence-init/` 内；全部为 Markdown 文档改动；遵守仓库"非必要不编写代码"原则；pre-check 的 no-interrupt 硬性完成门槛不得因 pi 缺失而失败关闭。

## Goals / Non-Goals

**Goals:**

- pi 用户运行 `/pre-check` 后获得与 claude/codex 对等的 Superpowers、OpenSpec 环境。
- pi 环境存在时自动具备 MCP 能力（经 pi-mcp-adapter 读取 `.mcp.json`）；pi 不存在时不影响初始化结果。
- 路由规则对 pi 客户端有明确、可执行的行为约定。
- 所有改动保持增量语义：老项目重跑只补齐缺失项。

**Non-Goals:**

- 不修改 `cadence-workflow`（legacy）。
- 不修改 `install-offline.sh/.bat`。
- 不自建 pi MCP 扩展，不维护 pi 专属 MCP 配置文件（不引入 `.pi/mcp.json`）。
- 不升级本仓库根 `AGENTS.md`/`CLAUDE.md` 自身受管区块（后续重跑 rule-config 处理）。

## Decisions

### D1：Superpowers 软链第四目标为 `~/.pi/agent/skills`

- 选择：`~/.pi/agent/skills`（pi 官方全局 skills 目录）。
- 备选：`~/.pi/skills`——不是 pi 的目录约定，排除；仅依赖 pi 原生读取 `~/.agents/skills` 而不建软链——可行但与 claude/codex 的显式布局不一致，且用户本机已采用显式软链形态，排除。
- 同步、冲突（同名非软链跳过并警告 / no-interrupt 下备份重命名）、失效清理规则与现有三项目录完全复用。

### D2：OpenSpec 工具列表追加 `pi`

- 新项目使用 `openspec init --tools claude,codex,pi`。
- 已有 `openspec/config.yaml` 的项目不能依赖 `openspec update` 引入新的工具集：若 `.pi/skills/openspec-*` 或 `.pi/prompts/opsx-*` 缺失，先执行 `openspec init --tools pi` 生成 5 个 pi skills 与 5 个 pi prompts，再执行 `openspec update`；若 pi 产物已存在，则直接执行 `openspec update`。
- 验证增加 `test -f .pi/skills/openspec-propose/SKILL.md`。

### D3：pi MCP 走第三方扩展 pi-mcp-adapter，全局安装，检查归 pre-check

- 方案选型（已经用户确认）：安装 `pi-mcp-adapter` 扩展，pi 直接复用项目 `.mcp.json`；不自建扩展（违背"非必要不编写代码"且维护成本高），不做"仅文档说明"（目标 3 落空）。
- 安装位置（已经用户确认）：全局（`pi install npm:pi-mcp-adapter` → `~/.pi/agent/settings.json`），adapter 属于 pi 运行环境而非项目配置；不做项目级 `.pi/settings.json` 安装。
- 检查归属：pre-check 新增第 7 项**条件检查**，位于 Superpowers 之后、Playwright 之前：
  - 触发条件：`pi --version` 可用或 `~/.pi/agent` 目录存在；否则报告跳过且**不算失败**（语义同 Playwright 的条件跳过，不违反 no-interrupt 完成门槛）。
  - 就绪判定：`pi list` 输出含 `pi-mcp-adapter`，或实际包目录 `~/.pi/agent/npm/node_modules/pi-mcp-adapter` 存在。
  - 失败处理：pi 存在但安装失败时报告失败原因与手动命令；no-interrupt 模式下终止并给出恢复建议。
- mcp-configuration 不新增"同步到 pi"步骤（无第二份配置文件可同步），只增加 pi 消费方式说明，并把"Claude Code、Codex 与 pi 格式差异"对比表覆盖三客户端；`.gitignore` 无新增条目（pi 复用的 `.mcp.json` 已在忽略清单）。

### D4：pi 客户端行为约定并入路由规则模板

- 在 `agent-routing-kernel.md` 与 `openspec-superpowers-workflow.md` 的客户端差异段落增加第三类 "pi"：pi 经原生 skills 发现机制获得 Skill 清单，以**显式选择并全文读取对应 SKILL.md** 作为调用（与 Codex 同类：用途并入首段路由回执 → 立即全文读取 → 之后才能读取仓库规则/使用仓库工具）；Skill 未读完前不得进行仓库操作；调用失败按已注册清单重试，未成功加载则失败关闭。
- `mcp-servers.md` 模板中 "Claude Code 除外"、"进入 Claude Code 后输入 `/mcp`" 等客户端特定表述改为中性表述或补充 pi 对应行为（pi 的 `/mcp` 由 adapter 提供）。
- `rule-config/SKILL.md` codegraph 章节注明 `--target` 不支持 pi，pi 只要 `.mcp.json` 含 codegraph server 即可经 adapter 使用。

### D5：改动载体为 Skill 文档而非脚本

- pre-check / mcp-configuration / rule-config 均为 instructive Skill 文档，本次改动全部是文档段落、表格、流程图与验证命令的更新，不新增任何脚本，符合仓库"非必要不编写代码"原则。

## Risks / Trade-offs

- [pi-mcp-adapter 是第三方包，存在停更或行为变化风险] → pre-check 的就绪判定以安装结果为准并给出手动命令；mcp-configuration 文档注明该依赖来源与回退方式（用户可自行选择其他 pi MCP 扩展）；版本不锁定，与框架对 npx/uvx 等工具的"安装稳定版本"策略一致。
- [pi 同时从 `~/.agents/skills` 与 `~/.pi/agent/skills` 发现同名 Skill 可能重复] → 用户本机已是该形态且 pi 按名称去重正常工作；文档中注明显式软链的理由。
- [openspec 旧版本不支持 `--tools pi`] → pre-check 的安装命令本就要求 `@fission-ai/openspec@latest`；文档注明 pi 支持需要 ≥ 1.4.1。
- [规则模板更新后，已初始化项目的 AGENTS.md/CLAUDE.md 受管区块滞后] → 属于既有增量语义（重跑 rule-config 升级），本变更不扩大该问题；在本仓库自身升级根入口文件列为后续事项。

## Migration Plan

- 纯文档变更，无数据迁移。发布后即生效：新运行 `/pre-check` 的项目自动获得 pi 支持；已初始化项目重跑 `/pre-check` 时，若缺少 pi OpenSpec 产物则先执行 `openspec init --tools pi`、再执行 `openspec update`，并增量补齐 pi 软链与（如装 pi）adapter；已有 pi 产物时直接执行 `openspec update`。重跑 rule-config 的项目获得含 pi 约定的路由区块。

## Open Questions

（无——方案选型与安装位置均已在 brainstorming 阶段经用户确认。）
