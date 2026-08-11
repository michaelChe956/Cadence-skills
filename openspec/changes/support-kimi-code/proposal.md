## Why

Cadence 目前只对 Claude Code、Codex、pi 三客户端做环境初始化（OpenSpec 产物、Superpowers 软链、MCP 接入），尚不支持 Kimi Code。OpenSpec CLI 1.8.0 已原生支持 `--tools kimi`（生成 `.kimi-code/skills/openspec-*`），且 Kimi Code 读取项目根 `AGENTS.md`、`.kimi-code/skills/` 与 `.kimi-code/mcp.json`，补齐第四客户端支持的时机已成熟。

## What Changes

- **pre-check**：OpenSpec 检查从三客户端（`claude,codex,pi`）扩为四客户端（`claude,codex,pi,kimi`）。新项目初始化使用 `openspec init --tools claude,codex,pi,kimi`；按客户端增量补齐含 kimi（就绪判定为 `.kimi-code/skills/` 下存在 5 个 `openspec-*` 目录）；验证命令、no-interrupt 门槛、流程与快速参考同步更新。同时纠正 codex 就绪判定、目录结构说明与验证命令的产物路径：最新 OpenSpec 为 skills-only，codex 产物落项目根 `.agents/skills/openspec-*`（不再产生 `.codex/`），故 codex 判定从 `.codex/skills/` 改为 `.agents/skills/`。Superpowers 四层软链不变，文档明确 `~/.agents/skills` 通用层已被 Kimi Code 扫描，Kimi 无需新增软链层。
- **mcp-configuration**：Kimi Code 原生读取项目根 `.mcp.json`（源码与测试证实三层加载：`~/.kimi-code/mcp.json`、`<项目根>/.mcp.json`、`<cwd>/.kimi-code/mcp.json`，其中根目录 `.mcp.json` 即本 Skill 已生成的文件），无需第二份配置；仅需在客户端格式差异表新增 Kimi 列并补充 Kimi 消费方式说明，`.gitignore` 无需新增条目。
- **rule-config**：项目类型有界扫描的 `PRUNE_DIRS` 常量与 SKILL.md find 块同步增加 `.kimi-code`；路由规则模板已含 "Claude/Kimi" 表述，保持不变。
- **README 与文档**：全篇"三客户端"表述更新为四客户端，并补充 Kimi Code 支持说明。

## Capabilities

### New Capabilities
- `kimi-code-support`: Kimi Code 客户端在 cadence-init 的 OpenSpec 产物、Superpowers 说明、MCP 配置与项目类型扫描中的支持行为。

### Modified Capabilities
- `init-skill-sequencing`: pre-check 的 OpenSpec 检查完成门槛、按客户端检测的增量补齐与 README 口径从 claude/codex/pi 三客户端扩为 claude/codex/pi/kimi 四客户端。

## Impact

- `cadence-init/skills/pre-check/SKILL.md`（步骤 5、no-interrupt 门槛、增量、快速参考、验证命令）与 `scripts/pre-check.sh`（职责边界注释）
- `cadence-init/skills/mcp-configuration/SKILL.md`（Kimi 消费方式说明、格式差异表 Kimi 列）
- `cadence-init/skills/rule-config/SKILL.md` 与 `scripts/rule-config.py`（PRUNE_DIRS 有界扫描剪枝）
- `README.md`（客户端表述与 skills 表格）
- OpenSpec specs：`init-skill-sequencing`（修改）、`kimi-code-support`（新增）
- 依赖：OpenSpec CLI 需支持 `--tools kimi`（1.8.0 已支持；实现时确认最低版本注记）
