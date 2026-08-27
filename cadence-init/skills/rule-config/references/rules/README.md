# 框架内置规则目录

## 目录说明

本目录存放 Cadence 框架的内置规则模板。这些模板由框架维护者管理：`agent-routing-kernel.md` 仅作为 L0 受管区块插入业务项目的 `CLAUDE.md`/`AGENTS.md`，不复制到 `.claude/rules/`；`openspec-superpowers-workflow.md` 走 L1 版本化特例；其余模板用于生成 `.claude/rules/` 下 7 个框架受管规则文件。

## 文件列表

| 文件 | 内容概述 |
|------|---------|
| `agent-routing-kernel.md` | L0 入口受管区块插入源，仅插入 CLAUDE.md/AGENTS.md，不复制到 `.claude/rules/` |
| `openspec-superpowers-workflow.md` | OpenSpec 契约层与 Superpowers 行为层协作规则（L1 版本化特例） |
| `language.md` | 语言规则（中文回答要求）；受管落地名 `language.md` |
| `code-usage-coding.md` | 代码使用规则来源模板（按项目类型单选，落地为 `.claude/rules/code-usage.md`） |
| `code-usage-noncoding.md` | 代码使用规则来源模板（按项目类型单选，落地为 `.claude/rules/code-usage.md`） |
| `code-usage.md`（落地名） | 受管落地名；本模板目录不预存同名源文件，按项目类型从 coding/noncoding 来源模板单选生成 |
| `document-storage.md` | 文档存储规则（目录、命名、路径映射）；受管落地名 `document-storage.md` |
| `markdown-format.md` | Markdown 格式规则（代码块嵌套）；受管落地名 `markdown-format.md` |
| `mcp-servers.md` | MCP Server 使用规则（所有 MCP 工具）；受管落地名 `mcp-servers.md` |
| `code-reading-coding.md` | 代码阅读规则来源模板（coding 项目阅读工作流，落地名为 `code-reading.md`） |
| `code-reading-noncoding.md` | 代码阅读规则来源模板（non-coding 项目文档结构化阅读指引，落地名为 `code-reading.md`） |
| `code-reading.md`（落地名） | 受管落地名；本模板目录不预存同名源文件，按项目类型从 coding/noncoding 来源模板单选生成 |
| `playwright.md` | Playwright CLI 使用规则；启用或已存在时受管落地名 `playwright.md` |

## `.claude/rules/` 受管清单

框架权威全覆盖的落地文件固定为 7 个（不含 `agent-routing-kernel.md`，也不含走 L1 特例的 `openspec-superpowers-workflow.md`）：

1. `mcp-servers.md`
2. `code-reading.md`
3. `document-storage.md`
4. `language.md`
5. `markdown-format.md`
6. `code-usage.md`
7. `playwright.md`

## 修改权限

- **仅框架维护者**可以修改本目录下的文件
- 用户自定义规则应放在 `cadence/project-rules/` 目录
- **禁止**用户直接修改 `.claude/rules/` 目录下的文件

## 从旧版迁移

重新运行 `/cadence:init:rule-config` 会更新 L0 受管路由、L1 已知版本和上述框架受管规则文件。脚本以 dry-run / apply 两阶段执行，两模式均在 dry-run/apply 两阶段内完成：drift 文件先统一复制归档到 `cadence/legacy/`，归档成功后按模板权威全覆盖，不经用户决策；不执行章节合并。

## 相关目录

- 用户自定义规则：`cadence/project-rules/`
- 项目主配置：`CLAUDE.md`
