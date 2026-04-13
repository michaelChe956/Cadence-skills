# AGENTS.md

本文件为 Codex 及其他 AI Agents 在此仓库中工作提供指导。

## 强制规则

> **必须遵守 - 无例外**
> 详细规则见 `.claude/rules/` 目录下的各规则文件。
> 用户自定义规则见 `.claude/project-rules/` 目录。

### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 2. 代码使用规则
- **非必要不编写代码**（Skills 项目特殊规定） → 详见 `.claude/rules/code-usage.md`
- 如确实需要编写脚本、验证工具或自动化代码，必须先说明必要性与用途。

### 3. 文档存储规则
- **除本文件 `AGENTS.md` 外，所有文档必须存放在 `.claude` 目录下** → 详见 `.claude/rules/document-storage.md`
- 本文件 `AGENTS.md` 作为仓库根目录的代理入口说明文件，按用户要求放置于项目根目录。

### 4. Markdown 格式规则
- **Markdown 编写必须遵循项目格式规范** → 详见 `.claude/rules/markdown-format.md`

### 5. 仓库分析规则
- **禁止分析 `.git` 目录** → 详见 `.claude/rules/serena-usage.md`

### 6. MCP Server 与工具使用规则
- **各 MCP 工具及相关自动化工具的使用必须遵循项目规范** → 详见 `.claude/rules/mcp-servers.md`

### 7. 项目个性化规则
- **用户自定义规则只能存放在 `.claude/project-rules/` 目录**
- 禁止在 `.claude/rules/` 目录中添加用户自定义规则
- 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件
- 详见 `.claude/project-rules/README.md`

### 8. Playwright CLI 使用规则
- **浏览器自动化工具必须遵循项目规范** → 详见 `.claude/rules/playwright.md`

## 与 CLAUDE.md 的关系

- 用户在当前任务中的明确指令优先级最高。
- `CLAUDE.md` 面向 Claude Code。
- `AGENTS.md` 面向 Codex 及其他通用 AI Agents。
- 两者如有表述差异，应优先遵循本仓库中的实际规则文件，即 `.claude/rules/` 与 `.claude/project-rules/`。

## 项目信息

- 本仓库是一个以 Markdown、YAML、JSON 等文档和配置为主要工作对象的 Skills 项目。
- Agent 在执行任务时，应优先修改文档、规则、配置与说明文件，避免不必要的代码实现。

## Agent 执行要求

- 开始任务前，应先读取 `CLAUDE.md`，并按需查看 `.claude/rules/` 与 `.claude/project-rules/` 中的相关规则文件。
- 修改文档时，应优先沿用现有目录结构、命名规范与 Markdown 格式约定。
- 未经用户明确要求，不得直接修改 `.claude/rules/` 目录下的框架内置规则文件。
