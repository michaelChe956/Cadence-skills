# Design: 支持 Kimi Code 第四客户端

## Context

动机见 proposal.md（Why）。当前 cadence-init 只覆盖 Claude Code、Codex、pi 三客户端：pre-check 步骤 5 对 OpenSpec 做三客户端产物补齐、mcp-configuration 只同步 `.mcp.json` 与 `.codex/config.toml`、rule-config 项目类型扫描剪枝 `.claude/.codex/.pi`。经勘察确认：OpenSpec CLI 1.8.0 已原生支持 `--tools kimi`（生成 `.kimi-code/skills/openspec-*` 5 个 SKILL.md，无 commands/adapter）；Kimi Code 读取项目根 `AGENTS.md`（rule-config 已生成且路由规则已含 "Claude/Kimi" 表述）、项目级 `.kimi-code/skills/` 与 `.kimi-code/mcp.json`（JSON `mcpServers` 结构，支持 stdio/HTTP/SSE）、并扫描用户级通用 `~/.agents/skills`。

## Goals / Non-Goals

**Goals**
- pre-check 将 OpenSpec 产物检查扩为四客户端，老项目重跑自动补齐 kimi 产物。
- mcp-configuration 补充 Kimi 消费方式说明（Kimi 原生读取根目录 `.mcp.json`），不生成第二份配置，不新增 `.gitignore` 条目。
- rule-config 项目类型扫描剪枝 `.kimi-code`。
- README 与 skills 文档以四客户端口径更新。

**Non-Goals**
- 不为 Kimi 新增 Superpowers 软链层（复用 `~/.agents/skills` 通用层）。
- 不修改路由规则模板的 "Claude/Kimi" 表述（Kimi 与 Claude 同为原生 Skill 调用机制，已被现有规则覆盖）。
- 不复制 `.claude/rules/` 规则文件到 `.kimi-code/`（Kimi 读 AGENTS.md，经摘要引用可达，与 Codex 同处境）。
- 不为 Kimi 生成 `.kimi-code/mcp.json` 副本（Kimi 原生读取根目录 `.mcp.json`，与 pi 同源复用但无需 adapter）。
- 不改动 install-offline.sh/.bat（仅 Claude Code 插件安装，与客户端无关）。

## Decisions

### D1: OpenSpec 四客户端"始终补齐"策略
新项目 `openspec init --tools claude,codex,pi,kimi`；按客户端增量检测，缺失 kimi 时 `openspec init --tools kimi` 再 `update`。
- **理由**：与现有 claude/codex/pi 三客户端"始终 init"策略一致；kimi 产物是否生成不依赖本机是否安装 Kimi CLI，保证任意环境产物完整、老项目重跑自动补齐。
- **替代方案（否决）**：检测 `command -v kimi` 才 init——产物完整性依赖本机环境，后续安装 Kimi 需重跑，且与三客户端现有语义不一致。

### D2: Superpowers 不加第五层
四层软链不变，文档注明 `~/.agents/skills` 通用层已被 Kimi 扫描。
- **理由**：Kimi 默认 `merge_all_available_skills=true` 合并所有目录，若再软链到 `~/.kimi-code/skills` 会造成同名 skill 双目录注册冗余；且 `~/.kimi-code/skills` 语义是 Kimi 专属用户 skills，放通用 superpowers 会污染其语义。
- **替代方案（否决）**：类比 pi 的显式第五层——对 Kimi 产生双目录扫描冗余，风险大于收益。

### D3: MCP 配置复用根目录 `.mcp.json`，不生成第二份配置
- **理由**：Kimi Code 原生三层加载 MCP 配置——`~/.kimi-code/mcp.json`（用户级）、`<项目根>/.mcp.json`（Claude 兼容根目录文件）、`<cwd>/.kimi-code/mcp.json`（Kimi 专属层，优先级最高）。mcp-configuration 已生成根目录 `.mcp.json`，Kimi 直接消费（含 stdio/HTTP/SSE），无需 `.kimi-code/mcp.json` 副本，`.gitignore` 也无需新增条目。
- **字段兼容**：Kimi 的 `McpServerConfigSchema` 为非严格 zod object（preprocess 按 `command`/`url` 推断 transport），`.mcp.json` 中 pi 扩展的 `directTools` 等未知字段被静默剥离，对 Kimi 无害，无需专门处理。
- **替代方案（否决）**：生成 `.kimi-code/mcp.json` 副本——冗余，且与用户确认的"Kimi 直接读根目录 mcp.json"事实不符。

### D4: 规则文件不复制、路由规则不改
- Kimi Code 读取项目根 `AGENTS.md`，rule-config 已生成；AGENTS.md 的摘要引用指向 `.claude/rules/*.md`，Kimi 可经文件工具读取（与 Codex 同处境）。
- 路由规则模板 `agent-routing-kernel.md` / `openspec-superpowers-workflow.md` 已用 "Claude/Kimi" 类别定义原生 Skill 调用行为，本次不动。

### D5: PRUNE_DIRS 加 `.kimi-code`
- 与 `.claude/.codex/.pi` 同模式，`scripts/rule-config.py` 的 `PRUNE_DIRS` 常量与 SKILL.md find 块两处同步，受 `assert_bounded_source_scan_contract` 断言核对。

## Risks / Trade-offs

- **OpenSpec `--tools kimi` 最低版本未知** → 实现时查证 changelog，在 SKILL.md 标注与 pi 的 ">= 1.4.1" 同款版本注记；pre-check 脚本始终安装 `@fission-ai/openspec@latest`，版本不足时按现有逻辑升级。
- **Kimi 解析 OpenSpec 生成 SKILL.md 的非标准 frontmatter 字段**（`allowed-tools`/`license`/`metadata`）→ Kimi 目录形式仅强制 `name`/`description`，未知字段忽略；OpenSpec 官方支持 kimi 工具即保证兼容；实现时对生成的 5 个 SKILL.md 做一次解析冒烟验证。
- **`.mcp.json` 含 API Key 占位** → 已入 `.gitignore`；Kimi 与 pi 均复用同一文件，无需额外配置副本或忽略条目。
- **老项目三客户端产物齐全但无 kimi 产物** → 重跑 `/pre-check` 按增量逻辑仅 `init --tools kimi`，不触碰既有产物。

## Migration Plan

- 老项目：重跑 `/pre-check`（自动补齐 `.kimi-code/skills/openspec-*`）；MCP 配置无需额外动作（Kimi 与 pi 均原生复用已有根目录 `.mcp.json`）。
- 回滚：改动均为增量补写，不覆盖既有文件；删除新增条目即回退，无需专门回滚流程。

## Open Questions

无（`--tools kimi` 最低版本属实现时查证项，不影响契约、方案或任务拆分）。
