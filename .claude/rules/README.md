# 框架内置规则目录

## 目录说明

本目录存放 Cadence 框架的内置规则文件。这些规则由框架维护者管理，在项目初始化时自动创建到用户项目的 `.claude/rules/` 目录。

## 文件列表

| 文件 | 内容概述 |
|------|---------|
| `language.md` | 语言规则（中文回答要求） |
| `code-usage-coding.md` | 代码使用规则（编码项目适用） |
| `code-usage-noncoding.md` | 代码使用规则（非编码项目适用） |
| `document-storage.md` | 文档存储规则（目录、命名、路径映射） |
| `markdown-format.md` | Markdown 格式规则（代码块嵌套） |
| `serena-usage.md` | Serena MCP 使用规则 |
| `mcp-servers.md` | MCP Server 使用规则（所有 MCP 工具） |
| `playwright.md` | Playwright CLI 使用规则 |

## 修改权限

- **仅框架维护者**可以修改本目录下的文件
- 用户自定义规则应放在 `cadence/project-rules/` 目录
- **禁止**用户直接修改 `.claude/rules/` 目录下的文件

## 从旧版迁移

如果你之前使用旧版 cadence-init 初始化了项目（CLAUDE.md 中包含完整规则文本），可以：

1. 重新运行 `/cadence:init:rule-config` 命令
2. 命令将自动创建 `.claude/rules/` 目录并写入规则文件
3. 手动将 CLAUDE.md 中的规则文本替换为摘要引用

## 相关目录

- 用户自定义规则：`cadence/project-rules/`
- 项目主配置：`CLAUDE.md`