# Spec: pi-agent-support

## ADDED Requirements

### Requirement: Superpowers 软链同步覆盖 pi 目标目录

pre-check 的 Superpowers 软链同步 MUST 在现有 `~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills` 之外，将 `~/.agents/skills/*` 中指向 Superpowers 的软链逐项同步到 `~/.pi/agent/skills`，并对全部目标目录复用同一套增量跳过、同名非软链冲突处理和失效软链清理规则。

#### Scenario: pi 目标目录补齐软链

- **WHEN** `~/.agents/superpowers/skills` 为有效来源且 `~/.pi/agent/skills` 缺少指向 Superpowers 的软链
- **THEN** pre-check 在 `~/.pi/agent/skills` 中逐项创建软链并验证 `test -d "$HOME/.pi/agent/skills"` 通过

#### Scenario: 已存在正确软链时增量跳过

- **WHEN** `~/.pi/agent/skills` 中已存在指向正确 Superpowers 来源的软链
- **THEN** pre-check 跳过该项，不重复创建、不覆盖

#### Scenario: 同名非软链冲突

- **WHEN** `~/.pi/agent/skills` 中存在与 Superpowers skill 同名的非软链文件或目录
- **THEN** 普通模式跳过该项并中文警告；no-interrupt 模式将冲突内容重命名为 `<原名称>.cadence-backup-YYYYMMDDHHMMSS` 后创建软链，任一步失败立即终止

### Requirement: OpenSpec 初始化包含 pi 工具

pre-check 对新项目的 OpenSpec 初始化 MUST 使用 `openspec init --tools claude,codex,pi`。对已存在 `openspec/config.yaml` 的项目，若 pi 产物缺失，MUST 先执行 `openspec init --tools pi`，再执行 `openspec update`；若 pi 产物已存在，MUST 直接执行 `openspec update`。pre-check MUST NOT 声称 `openspec update` 单独执行会为未选择过 pi 工具的老项目新增 `.pi/prompts/opsx-*.md` 与 `.pi/skills/openspec-*`。

#### Scenario: 新项目初始化生成 pi 产物

- **WHEN** 项目不存在 `openspec/config.yaml` 且 pre-check 执行 OpenSpec 初始化
- **THEN** 执行 `openspec init --tools claude,codex,pi`，且验证 `test -f .pi/skills/openspec-propose/SKILL.md` 通过

#### Scenario: 老项目缺少 pi 产物时增量初始化

- **WHEN** 项目已存在 `openspec/config.yaml` 但缺少 `.pi/skills/openspec-*` 或 `.pi/prompts/opsx-*`
- **THEN** pre-check 先执行 `openspec init --tools pi`，确认生成 5 个 pi skills 与 5 个 pi prompts，再执行 `openspec update`

#### Scenario: 老项目已有 pi 产物时更新

- **WHEN** 项目已存在 `openspec/config.yaml` 且 pi skills 与 prompts 已存在
- **THEN** pre-check 直接执行 `openspec update` 刷新已有工具产物

### Requirement: pi MCP adapter 条件检查与安装

pre-check MUST 提供一项"pi MCP Adapter"条件检查：仅当 `command -v pi >/dev/null 2>&1` 成功，即 PATH 中存在 pi 可执行文件时，检查并按需全局安装 `pi-mcp-adapter`（`pi install npm:pi-mcp-adapter`）。`~/.pi/agent` 或其子目录存在 MUST NOT 作为 pi 已安装的信号。pi 可执行文件不存在时 MUST 跳过，不调用 `pi list` 或 `pi install`，且不计为失败。

#### Scenario: pi 存在且 adapter 缺失时自动安装

- **WHEN** `command -v pi >/dev/null 2>&1` 成功，且 `pi list` 输出不含 `pi-mcp-adapter`，且 `~/.pi/agent/npm/node_modules/pi-mcp-adapter` 不存在
- **THEN** pre-check 执行 `pi install npm:pi-mcp-adapter` 并验证安装结果

#### Scenario: 未安装 pi 的环境条件跳过

- **WHEN** `command -v pi >/dev/null 2>&1` 失败，即使 cadence 已创建 `~/.pi/agent/skills`
- **THEN** pre-check 报告"未检测到 pi 可执行文件，跳过 pi MCP Adapter 检查"，不调用 `pi list` 或 `pi install`，继续后续检查，no-interrupt 模式下不因此失败关闭

#### Scenario: pi 存在但 adapter 安装失败

- **WHEN** `command -v pi >/dev/null 2>&1` 成功且 `pi install npm:pi-mcp-adapter` 执行失败
- **THEN** 普通模式报告失败原因与手动安装命令；no-interrupt 模式终止并给出恢复建议，不得宣称初始化成功

### Requirement: MCP 配置文档说明 pi 消费方式

mcp-configuration MUST 说明 pi 无原生 MCP、由 pi-mcp-adapter 直接读取项目 `.mcp.json`（含 HTTP 类型 server），且 MUST NOT 为 pi 维护第二份客户端配置文件或在 `.gitignore` 中新增 pi 专属条目。

#### Scenario: pi 复用项目 .mcp.json

- **WHEN** 项目已按 mcp-configuration 生成 `.mcp.json` 且 pi 环境已安装 pi-mcp-adapter
- **THEN** 文档指明 pi 经 adapter 直接使用该 `.mcp.json`，无需执行任何同步步骤

#### Scenario: 三客户端对比完整

- **WHEN** 读者查阅 mcp-configuration 中的客户端格式差异说明
- **THEN** 文档同时覆盖 Claude Code、Codex、pi 三者的配置格式与传输类型支持差异

### Requirement: 路由规则包含 pi 客户端行为约定

rule-config 的路由规则模板（`agent-routing-kernel.md` 与 `openspec-superpowers-workflow.md`）MUST 在 "Claude/Kimi" 与 "Codex" 之外定义 pi 客户端的 Skill 调用与回执行为：pi 以显式选择并全文读取对应 SKILL.md 作为 Skill 调用，Skill 用途并入首段路由回执，Skill 未读完前不得读取仓库规则或使用仓库工具。

#### Scenario: pi 客户端按约定路由

- **WHEN** pi 客户端执行需要仓库操作的任务并按规则模板生成的路由规则工作
- **THEN** 规则文本中存在针对 pi 的明确约定：显式选择 Skill、用途并入首段路由回执、立即全文读取 SKILL.md、读完后才允许仓库操作

#### Scenario: codegraph 与 MCP 规则说明 pi 差异

- **WHEN** 读者查阅 rule-config 的 codegraph 章节或 `mcp-servers.md` 模板
- **THEN** 文档注明 `codegraph install --target` 不支持 pi（pi 经 `.mcp.json` + adapter 消费），且 MCP 使用规则中的客户端特定表述覆盖 pi 或改为中性表述
