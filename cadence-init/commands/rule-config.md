---
name: rule-config
description: "配置 Claude Code 规则：创建 rules 规则文件、配置目录结构和项目技术栈"
---

# Claude Code 规则配置

## 概述

配置 Claude Code 的规则：创建 `.claude/rules/` 目录下的规则文件，在 CLAUDE.md 中添加摘要引用。

## 检查清单

你必须为以下每个项目创建任务并按顺序完成：

1. **创建 rules 目录和规则文件** — 从 `references/rules/` 读取模板，创建到 `.claude/rules/`
2. **添加 CLAUDE.md 规则引用** — 在 CLAUDE.md 中添加全部 8 条规则的摘要引用
3. **包管理器规则** — 前端使用 pnpm，Python 使用 uv
4. **技术栈检测** — 自动检测语言、测试/检查/格式化命令，需要用户确认
5. **目录结构创建** — 创建 `.claude/` 子目录
6. **Playwright Skills 规则配置** — 配置 Playwright CLI 的使用规则（可选）

**下一步**：将配置结果传递给 @mcp-configuration skill 进行 MCP 配置

## 处理流程

### 1. 创建 rules 目录和规则文件

**创建 rules 目录**：

```bash
mkdir -p .claude/rules
```

**从 references/rules/ 读取模板并写入规则文件**：

将以下模板文件从 `cadence-init/references/rules/` 复制到项目的 `.claude/rules/` 目录：

| 源文件 | 目标文件 |
|--------|---------|
| `references/rules/README.md` | `.claude/rules/README.md` |
| `references/rules/language.md` | `.claude/rules/language.md` |
| `references/rules/code-usage.md` | `.claude/rules/code-usage.md` |
| `references/rules/document-storage.md` | `.claude/rules/document-storage.md` |
| `references/rules/markdown-format.md` | `.claude/rules/markdown-format.md` |
| `references/rules/serena-usage.md` | `.claude/rules/serena-usage.md` |

### 2. 添加 CLAUDE.md 规则引用

**在 CLAUDE.md 中添加以下结构**：

````markdown
# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作提供指导。

## 强制规则

> **🔴 必须遵守 - 无例外**
> 详细规则见 `.claude/rules/` 目录下的各规则文件。
> 用户自定义规则见 `.claude/project-rules/` 目录。

### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 2. 代码使用规则
- **非必要不编写代码**（Skills 项目特殊规定） → 详见 `.claude/rules/code-usage.md`

### 3. 文档存储规则
- **所有文档必须存放在 `.claude` 目录下** → 详见 `.claude/rules/document-storage.md`

### 4. Markdown 格式规则
- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`

### 5. Serena 使用规则
- **禁止分析 .git 目录** → 详见 `.claude/rules/serena-usage.md`

### 6. MCP Server 使用规则
- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`

### 7. 项目个性化规则（强制规则）
- **用户自定义规则只能存放在 `.claude/project-rules/` 目录**
- 禁止在 `rules/` 目录中添加用户自定义规则
- 禁止直接修改 `rules/` 目录下的框架内置规则文件
- 详见 `.claude/project-rules/README.md`

## 项目信息
# currentDate
Today's date is {当前日期}。
````

**注意**：
- 规则 6（MCP Server）由 `mcp-configuration` command 添加，此处先写入引用行
- 规则 7（项目个性化规则）由 `project-rules-examples` command 添加详细内容
- 规则 8（Playwright）由步骤 6 添加（如用户选择启用）

### 3. 包管理器规则

**检测并添加到 CLAUDE.md**：

```markdown
## 项目配置

> 以下内容由初始化脚本根据项目环境自动检测生成，非通用规则。

### 包管理器规则
- **前端项目**：必须使用 `pnpm` 作为包管理器
- **Python 项目**：必须使用 `uv` 作为包管理器
- **禁止使用**：npm（前端）、pip（Python）、yarn（前端）
```

**检测命令**：

```bash
# 检测前端项目
ls -la | grep "package.json"

# 检测 Python 项目
ls -la | grep -E "requirements.txt|pyproject.toml"
```

### 4. 技术栈检测

**检测内容**：

| 类型 | 检测方法 |
|------|----------|
| 语言 | 读取 package.json、requirements.txt 等获取主要语言 |
| 测试命令 | 从配置文件提取 test 脚本 |
| 检查命令 | 从配置文件提取 lint 脚本 |
| 格式化命令 | 从配置文件提取 format 脚本 |
| 覆盖率阈值 | 默认为 80% |

**检测命令**：

```bash
# 提取 package.json 中的脚本
cat package.json | grep -A 10 '"scripts"'

# 提取 requirements.txt
cat requirements.txt

# 检测 Python 测试框架
grep -E "pytest|unittest" requirements.txt
```

**用户确认**：
- 检测到技术栈后，必须展示给用户确认
- 如果检测不准确，允许用户手动修改
- 写入 CLAUDE.md 前必须获取用户确认

**添加到 CLAUDE.md**：

```markdown
### 项目技术栈
- **语言**：[语言列表]
- **包管理器**：[pnpm/uv]
- **测试命令**：[命令]
- **检查命令**：[命令]
- **格式化命令**：[命令]
- **覆盖率阈值**：80%
```

### 5. 目录结构创建

**创建以下目录结构**：

```bash
mkdir -p .claude/{rules,prds,analysis-docs,docs,designs,designs-reviews,plans,readmes,modaos,models,architecture,notes,logs,reports,project-rules/examples}
```

**目录用途说明**：

| 目录 | 用途 | 说明 |
|------|------|------|
| `rules/` | 框架规则 | 内置规则文件（维护者管理） |
| `prds/` | 概要需求 | @brainstorming skill 生成的早期需求方案 |
| `analysis-docs/` | 分析报告 | @analyze skill 生成的代码分析、调研报告 |
| `docs/` | 详细需求 | @requirement skill 生成的详细需求文档 |
| `designs/` | 设计文档 | @design skill 生成的技术方案、架构设计 |
| `designs-reviews/` | 设计评审 | @design-review skill 的评审文档 |
| `plans/` | 计划文档 | @plan skill 生成的实施计划 |
| `readmes/` | README 文档 | 开发相关的技术文档（API 文档、开发指南等） |
| `modaos/` | 界面原型 | 墨刀/Figma 原型截图、设计稿 |
| `models/` | 数据模型 | 数据库表模型、ER 图、schema 定义 |
| `architecture/` | 架构文档 | 系统架构分析、技术选型 |
| `notes/` | 开发笔记 | 临时记录、开发心得、TODO 列表 |
| `logs/` | 开发日志 | 问题追踪、Bug 记录、开发进度 |
| `reports/` | 进度报告 | @report skill 生成的开发进度报告 |
| `project-rules/` | 个性化规则 | 用户定制的模板和规范 |

### 6. Playwright Skills 规则配置

**检测条件**：
- 用户需要浏览器自动化功能
- 项目涉及 Web 测试、表单填写、截图、数据提取

**创建规则文件**：将 `references/rules/playwright.md` 复制到 `.claude/rules/playwright.md`

**在 CLAUDE.md 中添加**：

```markdown
### 8. Playwright CLI 使用规则
- **浏览器自动化工具规范** → 详见 `.claude/rules/playwright.md`
```

**用户确认**：
- 添加规则前询问用户是否需要 Playwright 自动化功能
- 如果不需要，跳过此步骤
- 如果需要，写入 CLAUDE.md 前展示完整规则供确认

## 核心原则

- **规则分离** — 框架规则放 `.claude/rules/`，用户规则放 `.claude/project-rules/`
- **摘要引用** — CLAUDE.md 只保留摘要和引用，详细内容在规则文件中
- **目录明确** — 每种文档类型有明确存储位置
- **用户确认** — 技术栈检测必须经过用户确认
