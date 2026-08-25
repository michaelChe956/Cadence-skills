## Purpose

定义 cadence-init 对 Kimi Code coding agent 的环境初始化、MCP 接入与项目类型扫描支持要求，使 Kimi Code 成为与 Claude Code、Codex、pi 并列的第四客户端。

## Requirements

### Requirement: OpenSpec 初始化包含 kimi 工具

pre-check 对新项目的 OpenSpec 初始化 MUST 使用 `openspec init --tools claude,codex,pi,kimi`。对已存在 `openspec/config.yaml` 的项目，若 kimi 产物缺失，MUST 先执行 `openspec init --tools kimi`，再执行 `openspec update`；若 kimi 产物已存在，MUST 直接执行 `openspec update`。kimi 产物就绪判定为 `.kimi-code/skills/` 下存在 5 个 `openspec-*` 目录。pre-check MUST NOT 声称 `openspec update` 单独执行会为未选择过 kimi 工具的老项目新增 `.kimi-code/skills/openspec-*`。

#### Scenario: 新项目初始化生成 kimi 产物

- **WHEN** 项目不存在 `openspec/config.yaml` 且 pre-check 执行 OpenSpec 初始化
- **THEN** 执行 `openspec init --tools claude,codex,pi,kimi`，且验证 `test -f .kimi-code/skills/openspec-propose/SKILL.md` 通过

#### Scenario: 老项目缺少 kimi 产物时增量初始化

- **WHEN** 项目已存在 `openspec/config.yaml` 但缺少 `.kimi-code/skills/openspec-*`
- **THEN** pre-check 先执行 `openspec init --tools kimi`，确认生成 5 个 kimi skills，再执行 `openspec update`

#### Scenario: 老项目已有 kimi 产物时更新

- **WHEN** 项目已存在 `openspec/config.yaml` 且 `.kimi-code/skills/` 下 5 个 `openspec-*` 目录已存在
- **THEN** pre-check 直接执行 `openspec update` 刷新已有工具产物

### Requirement: Superpowers 说明 kimi 消费方式

pre-check 的 Superpowers 四层软链 MUST 保持不变（`~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills`、`~/.pi/agent/skills`），MUST NOT 为 kimi 新增 `~/.kimi-code/skills` 软链层。文档 MUST 说明 Kimi Code 扫描用户级通用目录 `~/.agents/skills`，经该层获得 Superpowers skills，无需额外同步。

#### Scenario: kimi 经通用层获得 Superpowers skills

- **WHEN** 项目已按 pre-check 同步 `~/.agents/skills` 且 Kimi Code 在项目内启动
- **THEN** 文档指明 Kimi 直接使用 `~/.agents/skills` 中的 Superpowers skills，无需额外同步层

#### Scenario: 不新增 kimi 专属软链层

- **WHEN** 读者查阅 pre-check 的 Superpowers 目录约定
- **THEN** 文档不包含 `~/.kimi-code/skills` 作为软链同步目标

### Requirement: MCP 配置说明 kimi 消费方式

mcp-configuration MUST 说明 Kimi Code 原生读取项目根 `.mcp.json`（含 stdio/HTTP/SSE server），复用本 Skill 已生成的文件，MUST NOT 为 kimi 生成 `.kimi-code/mcp.json` 副本或在 `.gitignore` 中新增 kimi 专属条目。客户端格式差异表 MUST 覆盖 Kimi 列。

#### Scenario: kimi 复用项目根 .mcp.json

- **WHEN** 项目已按 mcp-configuration 生成 `.mcp.json` 且 Kimi Code 在项目内启动
- **THEN** 文档指明 Kimi Code 原生读取该 `.mcp.json`（含 stdio 与 HTTP/SSE server），无需执行任何同步步骤

#### Scenario: 不生成 kimi 专属 MCP 配置副本

- **WHEN** 读者查阅 mcp-configuration 的检查清单与客户端格式差异表
- **THEN** 文档不含生成 `.kimi-code/mcp.json` 的步骤，且格式差异表同时覆盖 Claude Code、Codex、pi、Kimi 四者

#### Scenario: gitignore 不新增 kimi 条目

- **WHEN** mcp-configuration 配置 `.gitignore`
- **THEN** 不新增 `.kimi-code/mcp.json` 条目（`.mcp.json` 已在忽略清单内，Kimi 复用同一文件）

### Requirement: 项目类型扫描剪枝 kimi 目录

rule-config 的项目类型有界扫描 MUST 在脚本 `PRUNE_DIRS` 常量与 SKILL.md 中的 find 剪枝目录清单同步增加 `.kimi-code`，且二者逐项一致（受 harness 断言核对）。

#### Scenario: 扫描剪枝 kimi 目录

- **WHEN** rule-config 执行项目类型有界扫描且项目含 `.kimi-code/` 目录
- **THEN** 该目录被剪枝，不参与源码扩展名检测

#### Scenario: 剪枝清单一致性

- **WHEN** 对照 rule-config SKILL.md 的 find 块与脚本 `PRUNE_DIRS` 常量
- **THEN** 两者均包含 `.kimi-code` 且逐项一致

### Requirement: README 与文档四客户端表述

README MUST 以四客户端口径描述 pre-check 的 OpenSpec 检查范围（claude/codex/pi/kimi），与 pre-check SKILL.md 一致；MUST 在 skills 表格中更新 `/pre-check` 与 `/mcp-configuration` 的 Kimi 相关说明。

#### Scenario: README 口径一致

- **WHEN** 对照阅读 README 初始化章节与 pre-check SKILL.md 的 OpenSpec 检查条款
- **THEN** 两处对客户端列表与 OpenSpec 检查范围的表述一致，均为四客户端

#### Scenario: skills 表格更新

- **WHEN** 查阅 README 的 skills 表格
- **THEN** `/pre-check` 行包含 kimi 客户端产物说明，`/mcp-configuration` 行包含 `.kimi-code/mcp.json` 说明
