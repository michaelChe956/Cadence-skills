# 框架内置规则目录

## 目录说明

本目录存放 Cadence 框架的内置规则文件。这些规则由框架维护者管理；除 `agent-routing-kernel.md` 仅作为受管区块插入业务项目的 `CLAUDE.md`/`AGENTS.md` 外，其余规则在项目初始化时自动创建到 `.claude/rules/`。

## 文件列表

| 文件 | 内容概述 |
|------|---------|
| `agent-routing-kernel.md` | L0 Agent 入口受管区块模板，仅插入 CLAUDE.md/AGENTS.md，不复制到 `.claude/rules/` |
| `openspec-superpowers-workflow.md` | OpenSpec 契约层与 Superpowers 行为层协作规则 |
| `language.md` | 语言规则（中文回答要求） |
| `code-usage-coding.md` | 代码使用规则（编码项目适用） |
| `code-usage-noncoding.md` | 代码使用规则（非编码项目适用） |
| `document-storage.md` | 文档存储规则（目录、命名、路径映射） |
| `markdown-format.md` | Markdown 格式规则（代码块嵌套） |
| `mcp-servers.md` | MCP Server 使用规则（所有 MCP 工具） |
| `code-reading.md` | 代码阅读规则（CodeGraph 与 ast-grep outline 使用规范） |
| `playwright.md` | Playwright CLI 使用规则 |

## 修改权限

- **仅框架维护者**可以修改本目录下的文件
- 用户自定义规则应放在 `cadence/project-rules/` 目录
- **禁止**用户直接修改 `.claude/rules/` 目录下的文件

## 从旧版迁移

重新运行 `/cadence:init:rule-config` 会更新受管路由和已知版本框架规则；无法识别的本地修改会先备份并报告。

## 相关目录

- 用户自定义规则：`cadence/project-rules/`
- 项目主配置：`CLAUDE.md`
