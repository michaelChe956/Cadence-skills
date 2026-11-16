## Purpose

定义 cadence-init 对 Kimi Code coding agent 的环境初始化、MCP 接入与项目类型扫描支持要求，使 Kimi Code 成为与 Claude Code、Codex、pi 并列的第四客户端。

## Requirements

### Requirement: OpenSpec 初始化包含 kimi 工具

pre-check MUST 按 `init-skill-sequencing` 的四客户端缺失集合执行增量 init/update，其中包含 kimi。共享marker列出kimi时，MUST验证 `.agents/skills/` 六项核心技能的可读非空SKILL.md，不要求 `.kimi-code/skills` 副本；未登记kimi时允许完整旧版六项客户端技能。已登记但shared损坏不得回退旧目录。不以config.yaml存在性代替投影就绪。

#### Scenario: 新项目初始化生成 kimi 产物

- **WHEN** 新项目缺少kimi客户端产物并执行OpenSpec初始化
- **THEN** 缺失工具集合包含kimi，验证共享布局或旧版客户端布局，不手工重建上游已退役副本

#### Scenario: 老项目缺少 kimi 产物时增量初始化

- **WHEN** kimi共享登记/技能或未登记时的旧布局不完整
- **THEN** 先执行包含kimi的增量init，复核可用后执行update

#### Scenario: 老项目已有 kimi 产物时更新

- **WHEN** kimi有效共享布局或未登记时的完整旧版布局已存在
- **THEN** pre-check直接执行update，不因旧客户端目录消失重复初始化

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
