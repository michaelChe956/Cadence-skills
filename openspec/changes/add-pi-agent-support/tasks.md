# Tasks: add-pi-agent-support

## 1. pre-check：Superpowers 软链增加 pi 目标

- [x] 1.1 更新 `cadence-init/skills/pre-check/SKILL.md` 步骤 6：目录约定表、软链同步逻辑、验证命令增加 `~/.pi/agent/skills`，并注明 pi 原生读 `~/.agents/skills` 但保持显式软链对齐（映射：Superpowers 软链同步覆盖 pi 目标目录）
- [x] 1.2 同步更新 no-interrupt 完成条件（三层→四层软链）、增量运行典型场景、检查流程图与快速参考表（映射：Superpowers 软链同步覆盖 pi 目标目录）

## 2. pre-check：OpenSpec 增加 pi

- [x] 2.1 更新初始化命令为 `openspec init --tools claude,codex,pi`，补充 pi 产物结构说明与验证命令（映射：OpenSpec 初始化包含 pi 工具）
- [x] 2.2 更新增量要求：老项目 `openspec update` 补齐 pi 产物；注明 pi 支持需 openspec ≥ 1.4.1（映射：OpenSpec 初始化包含 pi 工具）

## 3. pre-check：新增 pi MCP Adapter 条件检查

- [x] 3.1 在 Superpowers 之后、Playwright 之前新增"pi MCP Adapter"检查步骤：触发条件、就绪判定、安装命令、失败处理（映射：pi MCP adapter 条件检查与安装）
- [x] 3.2 更新 no-interrupt 强制完成策略表、检查流程图、快速参考表与常见错误表（映射：pi MCP adapter 条件检查与安装）

## 4. mcp-configuration：pi 消费方式说明

- [x] 4.1 增加 pi 段落：无原生 MCP、pi-mcp-adapter 直读 `.mcp.json`（含 HTTP server）、不维护第二份配置、`.gitignore` 无新增条目（映射：MCP 配置文档说明 pi 消费方式）
- [x] 4.2 "Codex 与 Claude Code 格式差异"对比表扩展为三客户端对比（映射：MCP 配置文档说明 pi 消费方式）

## 5. rule-config：规则模板补 pi 行为约定

- [x] 5.1 `references/rules/agent-routing-kernel.md` 与 `references/rules/openspec-superpowers-workflow.md` 增加 pi 客户端 Skill 调用与回执约定（映射：路由规则包含 pi 客户端行为约定）
- [x] 5.2 `references/rules/mcp-servers.md` 客户端特定表述中性化或补充 pi；`rule-config/SKILL.md` codegraph 章节注明 `--target` 不支持 pi（映射：路由规则包含 pi 客户端行为约定）

## 6. 验证

- [x] 6.1 运行 `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh` 确认模板改动不破坏受管区块生命周期测试
- [x] 6.2 对照本机环境逐项核对文档描述：`~/.pi/agent/skills` 软链形态、openspec `--tools pi` 产物、pi-mcp-adapter 安装与 `.mcp.json` 读取行为
