---
name: rule-config
description: "配置 Claude Code 与 Codex 规则：创建 rules 规则文件、配置目录结构和项目技术栈"
---

# Claude Code 与 Codex 规则配置

## 概述

配置 Claude Code 与 Codex 的规则：创建 `.claude/rules/` 目录下的规则文件，在 CLAUDE.md 中添加摘要引用，并参考 CLAUDE.md 同步生成 AGENTS.md。

## 检查清单

你必须为以下每个项目创建任务并按顺序完成：

1. **创建 rules 目录和规则文件** — 检测项目类型，定位模板目录，复制规则文件到 `.claude/rules/`
2. **添加 CLAUDE.md 与 AGENTS.md 规则引用** — 在 CLAUDE.md 中添加全部 9 条规则的摘要引用，并参考 CLAUDE.md 同步生成 Codex 所需的 AGENTS.md（规则 2 根据步骤 1a 检测结果选择对应文本；Coding 项目默认角色为执行者）
3. **包管理器规则** — 前端使用 pnpm，Python 使用 uv
4. **技术栈检测** — 自动检测语言、测试/检查/格式化命令，需要用户确认
5. **目录结构创建** — 创建 `.claude/rules` 与 `cadence/` 产物目录
6. **历史产物迁移** — 检测旧 `.claude/` 产物目录，用户确认后迁移到 `cadence/`
7. **cadence gitignore 决策** — 询问用户是否将 `cadence/` 加入 `.gitignore`，默认不忽略
8. **代码阅读规则配置** — 配置 `ast-grep outline` 的使用规则（可选，Coding 项目默认建议启用）
9. **CodeGraph 项目初始化** — 项目级安装 CodeGraph 到 Claude Code/Codex，核验 `.mcp.json` 与 `.codex/config.toml` 均包含 CodeGraph MCP，并初始化 `.codegraph/`（可选，Coding 项目默认建议启用）
10. **Playwright Skills 规则配置** — 配置 Playwright CLI 的使用规则（可选）

**下一步**：将配置结果传递给 @mcp-configuration skill 进行 MCP 配置

## 处理流程

### 1. 创建 rules 目录和规则文件

**步骤 1a：项目类型检测**

使用 Glob 工具搜索常见源代码文件，**排除框架内部目录**：

先使用 Glob 搜索：
```
**/*.{java,js,ts,py,go,php,rs,rb,swift,kt,c,cpp,cs}
```

从搜索结果中**排除**路径包含以下关键词的匹配：
- `cadence-init/`
- `Cadence-skills/`
- `.claude-plugin/`
- `node_modules/`

排除后：
- 如果仍有匹配结果 → **Coding 项目**
- 如果没有匹配结果或所有结果都被排除 → 可能是**非 Coding 项目**，也可能是**全新 Coding 项目**

检测结果需**展示给用户确认**：向用户说明检测结果和依据，允许用户手动修正。

如果没有检测到常见源代码文件，必须让用户选择项目类型：
- **Coding 项目**：适用于全新编码项目；选择后使用 Coding 项目规则，默认角色为**执行者**
- **非 Coding 项目**：适用于文档、配置、Skills/Commands 等非编码项目；选择后使用非 Coding 项目规则

**步骤 1b：定位模板目录**

按以下优先级顺序查找模板目录：

1. **在线安装路径**：
   - 检查 `~/.claude/plugins/marketplaces/cadence-skills-marketplace/cadence-init/references/rules/language.md` 是否存在
   - 如果存在，取该路径（去掉末尾 `language.md`）作为**模板根路径**

2. **离线安装路径**：
   - 检查 `~/.claude/plugins/marketplaces/cadence-skills-local/cadence-init/references/rules/language.md` 是否存在
   - 如果存在，取该路径（去掉末尾 `language.md`）作为**模板根路径**

3. **回退搜索**（开发环境）：
   - 使用 Glob 工具搜索标识文件：
   ```
   **/cadence-init/references/rules/language.md
   ```
   从返回结果中提取目录路径（去掉末尾 `language.md`），作为**模板根路径**。
   如果匹配多个，验证每个路径下是否同时存在 `document-storage.md`，
   从通过验证的结果中取修改时间最新的。

> **重要**：此模板根路径需在后续所有步骤中复用（包括步骤 8 的 code-reading.md 和步骤 10 的 playwright.md）。

**步骤 1c：创建目标目录**

```bash
mkdir -p .claude/rules
```

**步骤 1d：从模板根路径复制规则文件**

将以下文件从 [步骤 1b 定位的模板根路径] 读取内容，写入项目的 `.claude/rules/` 目录：

| 源文件名 | 目标文件 | 条件 |
|----------|---------|------|
| `README.md` | `.claude/rules/README.md` | 必选 |
| `language.md` | `.claude/rules/language.md` | 必选 |
| `document-storage.md` | `.claude/rules/document-storage.md` | 必选 |
| `markdown-format.md` | `.claude/rules/markdown-format.md` | 必选 |
| `mcp-servers.md` | `.claude/rules/mcp-servers.md` | 必选 |
| `code-usage-coding.md` | `.claude/rules/code-usage.md` | Coding 项目 |
| `code-usage-noncoding.md` | `.claude/rules/code-usage.md` | 非 Coding 项目 |

### 2. 添加 CLAUDE.md 与 AGENTS.md 规则引用

**在 CLAUDE.md 中添加以下结构**：

````markdown
# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作提供指导。

## 强制规则

> **🔴 必须遵守 - 无例外**
> 详细规则见 `.claude/rules/` 目录下的各规则文件。
> 用户自定义规则见 `cadence/project-rules/` 目录。

### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 2. 代码使用规则
- **Coding 项目**：`- **遵循 TDD 和代码规范** → 详见 .claude/rules/code-usage.md`
- **非 Coding 项目**：`- **非必要不编写代码** → 详见 .claude/rules/code-usage.md`

### 3. 文档存储规则
- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules` 目录下** → 详见 `.claude/rules/document-storage.md`

### 4. Markdown 格式规则
- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`

### 5. MCP Server 使用规则
- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`

### 6. 项目个性化规则（强制规则）
- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**
- 禁止在 `rules/` 目录中添加用户自定义规则
- 禁止直接修改 `rules/` 目录下的框架内置规则文件
- 详见 `cadence/project-rules/README.md`

### 7. 代码阅读规则
- **大范围检索使用 CodeGraph，精确结构阅读优先使用 `ast-grep outline`** → 详见 `.claude/rules/code-reading.md`

## 项目信息
# currentDate
Today's date is {当前日期}。
````

**注意**：
- 规则 5（MCP Server）由 `mcp-configuration` command 添加，此处先写入引用行
- 规则 6（项目个性化规则）由 `project-rules-examples` command 添加详细内容
- 规则 7（代码阅读）由步骤 8 添加（如用户选择启用）
- CodeGraph 项目初始化由步骤 9 执行（如用户选择启用）
- 规则 8（Playwright）由步骤 10 添加（如用户选择启用）
- 规则 2（代码使用规则）根据步骤 1a 的项目类型检测结果选择对应摘要行

**参考 CLAUDE.md 同步添加 AGENTS.md**：

````markdown
# AGENTS.md

本文件为 Codex 及其他 AI Agents 在此仓库中工作提供指导。

## 默认角色

- **Coding 项目**：默认角色为**谨慎执行者**，优先阅读 issue、现有代码和约束，再按指令完成实现、验证与结果汇报。
- **非 Coding 项目**：默认遵循文档、配置、规则维护职责，非必要不编写代码。

## 强制规则

> **🔴 必须遵守 - 无例外**
> 详细规则见 `.claude/rules/` 目录下的各规则文件。
> 用户自定义规则见 `cadence/project-rules/` 目录。

### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 2. 代码使用规则
- **Coding 项目**：`- **遵循 TDD 和代码规范** → 详见 .claude/rules/code-usage.md`
- **非 Coding 项目**：`- **非必要不编写代码** → 详见 .claude/rules/code-usage.md`

### 3. 文档存储规则
- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules` 目录下** → 详见 `.claude/rules/document-storage.md`

### 4. Markdown 格式规则
- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`

### 5. MCP Server 与工具使用规则
- **各 MCP 工具及相关自动化工具的使用必须遵循项目规范** → 详见 `.claude/rules/mcp-servers.md`

### 6. 项目个性化规则
- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**
- 禁止在 `.claude/rules/` 目录中添加用户自定义规则
- 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件
- 详见 `cadence/project-rules/README.md`

### 7. 代码阅读规则
- **大范围检索使用 CodeGraph，精确结构阅读优先使用 `ast-grep outline`** → 详见 `.claude/rules/code-reading.md`

### 8. Playwright CLI 使用规则
- **浏览器自动化工具规范** → 详见 `.claude/rules/playwright.md`

## 与 CLAUDE.md 的关系

- 用户在当前任务中的明确指令优先级最高。
- `CLAUDE.md` 面向 Claude Code。
- `AGENTS.md` 面向 Codex 及其他通用 AI Agents。
- 两者如有表述差异，应优先遵循本仓库中的实际规则文件，即 `.claude/rules/` 与 `cadence/project-rules/`。

## Agent 执行要求

- 开始任务前，应先读取 `CLAUDE.md`，并按需查看 `.claude/rules/` 与 `cadence/project-rules/` 中的相关规则文件。
- 执行 issue 时，应先读取 issue 与相关上下文，再修改文件。
- 完成任务后，必须汇报测试或验证结果。
````

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
mkdir -p .claude/rules
mkdir -p cadence/{prds,analysis,analysis-docs,docs,designs,designs-reviews,plans,readmes,modaos,models,architecture,notes,logs,reports,project-rules/examples,cache}
```

**目录用途说明**：

| 目录 | 用途 | 说明 |
|------|------|------|
| `.claude/rules/` | 框架规则 | 内置规则文件（维护者管理） |
| `cadence/prds/` | 概要需求 | @brainstorming skill 生成的早期需求方案 |
| `cadence/analysis/` | 旧版分析报告 | 兼容旧版 Cadence analysis 输出目录 |
| `cadence/analysis-docs/` | 分析报告 | @analyze skill 生成的代码分析、调研报告 |
| `cadence/docs/` | 详细需求 | @requirement skill 生成的详细需求文档 |
| `cadence/designs/` | 设计文档 | @design skill 生成的技术方案、架构设计 |
| `cadence/designs-reviews/` | 设计评审 | @design-review skill 的评审文档 |
| `cadence/plans/` | 计划文档 | @plan skill 生成的实施计划 |
| `cadence/readmes/` | README 文档 | 开发相关的技术文档（API 文档、开发指南等） |
| `cadence/modaos/` | 界面原型 | 墨刀/Figma 原型截图、设计稿 |
| `cadence/models/` | 数据模型 | 数据库表模型、ER 图、schema 定义 |
| `cadence/architecture/` | 架构文档 | 系统架构分析、技术选型 |
| `cadence/notes/` | 开发笔记 | 临时记录、开发心得、TODO 列表 |
| `cadence/logs/` | 开发日志 | 问题追踪、Bug 记录、开发进度 |
| `cadence/reports/` | 进度报告 | @report skill 生成的开发进度报告 |
| `cadence/project-rules/` | 个性化规则 | 用户定制的模板和规范 |
| `cadence/cache/` | 分析缓存 | @git-review 等流程生成的 Cadence 缓存 |

### 6. 历史产物迁移

**检测旧目录**：

检查以下旧目录是否存在：

```bash
for dir in prds analysis analysis-docs docs designs designs-reviews plans readmes modaos models architecture notes logs reports project-rules cache; do
  test -e ".claude/$dir" && echo ".claude/$dir -> cadence/$dir"
done
```

**用户确认**：
- 如果没有检测到旧目录，提示无需迁移并继续
- 如果检测到旧目录，展示迁移清单，并询问用户是否迁移到 `cadence/`
- 默认建议迁移

**迁移规则**：

| 场景 | 处理方式 |
|------|----------|
| `cadence/<dir>` 不存在 | 将 `.claude/<dir>` 移动到 `cadence/<dir>` |
| `cadence/<dir>` 已存在且为空 | 将 `.claude/<dir>` 的内容移动到 `cadence/<dir>` |
| `cadence/<dir>` 已存在且非空 | 跳过该目录并报告冲突，要求用户手动处理 |

**禁止迁移**：
- `.claude/rules`
- `.claude/commands`
- `.claude/skills`

**迁移命令示例**：

```bash
mkdir -p cadence
for dir in prds analysis analysis-docs docs designs designs-reviews plans readmes modaos models architecture notes logs reports project-rules cache; do
  if [ -e ".claude/$dir" ]; then
    if [ ! -e "cadence/$dir" ]; then
      mv ".claude/$dir" "cadence/$dir"
    elif [ -d "cadence/$dir" ] && [ -z "$(find "cadence/$dir" -mindepth 1 -maxdepth 1 2>/dev/null)" ]; then
      find ".claude/$dir" -mindepth 1 -maxdepth 1 -exec mv {} "cadence/$dir/" \;
      rmdir ".claude/$dir" 2>/dev/null || true
    else
      echo "跳过冲突目录: .claude/$dir -> cadence/$dir"
    fi
  fi
done
```

**完成报告**：

迁移完成后，向用户报告已迁移目录、跳过目录和需要手动处理的冲突目录。

### 7. cadence gitignore 决策

**目的**：让用户决定是否将 `cadence/` 作为本地工作目录忽略。

**用户确认**：
- 询问用户：“是否将 `cadence/` 加入 `.gitignore`？”
- 默认选择：不忽略
- 默认不忽略的原因：PRD、设计、计划、用户项目规则等产物通常需要团队协作和版本管理

**如果用户选择忽略**：

检查 `.gitignore` 是否已包含 `cadence/`：

```bash
grep -qxF 'cadence/' .gitignore 2>/dev/null || printf '\n# Cadence 产物目录\ncadence/\n' >> .gitignore
```

**如果用户选择不忽略**：

不修改 `.gitignore`。

### 8. 代码阅读规则配置

**检测条件**：
- 项目为 **Coding 项目**（基于步骤 1a 检测结果）
- 用户需要代码阅读辅助（对 Coding 项目默认建议启用）

**创建规则文件**：将 [步骤 1b 定位的模板根路径] 中的 `code-reading.md` 读取内容，写入 `.claude/rules/code-reading.md`

**在 CLAUDE.md 和 AGENTS.md 中添加**：

```markdown
### 8. 代码阅读规则
- **大范围检索使用 CodeGraph，精确结构阅读优先使用 `ast-grep outline`** → 详见 `.claude/rules/code-reading.md`
```

**用户确认**：
- 对 Coding 项目：询问用户是否启用代码阅读规则，默认选项为“启用”。
- 对非 Coding 项目：默认跳过，仅提示“非 Coding 项目跳过代码阅读规则”。
- 如果用户选择启用，写入 CLAUDE.md 和 AGENTS.md 前展示完整规则供确认。

### 9. CodeGraph 项目初始化

**检测条件**：
- 项目为 **Coding 项目**（基于步骤 1a 检测结果）
- 用户需要大范围代码检索、调用链分析、架构理解或影响面分析
- 对 Coding 项目默认建议启用，非 Coding 项目默认跳过

**前置条件**：
- `/pre-check` 已完成 `codegraph` 安装检查
- `codegraph version` 可输出版本号

**用户确认**：
- 对 Coding 项目：询问用户是否启用 CodeGraph 项目初始化，默认选项为“启用”。
- 对非 Coding 项目：默认跳过，仅提示“非 Coding 项目跳过 CodeGraph 初始化”。
- 如果用户手动要求启用，即使未检测到源代码，也允许继续执行。

**项目级安装命令**：

```bash
codegraph install --target=claude,codex --location=local --yes
```

**安装后强制核验**：

执行 `codegraph install --target=claude,codex --location=local --yes` 后，不能只根据命令成功判断完成，必须分别检查：

1. `.mcp.json` 的 `mcpServers` 中是否包含 `codegraph`
2. `.codex/config.toml` 中是否包含 `[mcp_servers.codegraph]`

如果 `.mcp.json` 已包含 CodeGraph MCP，但 `.codex/config.toml` 缺少 CodeGraph MCP，说明 CodeGraph 未通过自身安装流程完成 Codex 本地配置。此时必须参考 `.mcp.json` 中的 `codegraph` 配置，手动补齐 `.codex/config.toml`：

````toml
[mcp_servers.codegraph]
command = "codegraph"
args = ["serve", "--mcp"]
````

如果 `.mcp.json` 也缺少 CodeGraph MCP，则按 `mcp-configuration.md` 的 CodeGraph MCP 兜底配置先补齐 `.mcp.json`，再同步补齐 `.codex/config.toml`。

**初始化命令**：

```bash
codegraph init
```

**验证命令**：

```bash
test -d .codegraph && codegraph status
```

**配置范围**：
- `--target=claude,codex`：只支持 Claude Code 和 Codex。
- `--location=local`：只写入当前项目配置，不写入全局 Agent 配置。
- `.codegraph/`：本地代码图索引目录，应加入 `.gitignore`。
- `codegraph.json`：团队共享配置文件，不应加入 `.gitignore`。

**已存在状态处理**：

| 场景 | 行为 |
|------|------|
| `.codegraph/` 不存在 | 用户确认后执行 `codegraph install` 与 `codegraph init` |
| `.codegraph/` 已存在 | 运行 `codegraph status`，报告已初始化，不重复 `codegraph init` |
| `.mcp.json` 与 `.codex/config.toml` 均已有 CodeGraph MCP server | 跳过，不重复写入 |
| `.mcp.json` 有 CodeGraph MCP，但 `.codex/config.toml` 缺少 `[mcp_servers.codegraph]` | 参考 `.mcp.json` 手动补齐 `.codex/config.toml` |
| `.mcp.json` 缺少 CodeGraph MCP | 按 `mcp-configuration.md` 的兜底配置补齐 `.mcp.json`，再同步补齐 `.codex/config.toml` |
| Claude/Codex 缺少 CodeGraph MCP server | 执行 `codegraph install --target=claude,codex --location=local --yes` 后必须再次核验两个配置文件 |
| `codegraph install` 失败 | 提供 `mcp-configuration.md` 中的手动兜底配置，并分别补齐 `.mcp.json` 与 `.codex/config.toml` |
| `codegraph init` 失败 | 提示用户确认项目语言、目录规模或是否需要配置 `codegraph.json` |

**.gitignore 增量处理**：

检查 `.gitignore` 是否已包含 `.codegraph/`：

```bash
grep -qxF '.codegraph/' .gitignore 2>/dev/null || printf '\n# CodeGraph 本地索引\n.codegraph/\n' >> .gitignore
```

**增量要求**：
- `/rule-config` 重复运行时，只补齐缺失的 CodeGraph 规则、摘要、MCP 配置、`.codegraph/` 初始化和 `.gitignore` 项。
- 不直接覆盖用户已经存在的规则文件或 Agent 配置。
- 写入前向用户展示本次将新增或更新的内容清单。

### 10. Playwright Skills 规则配置

**检测条件**：
- 用户需要浏览器自动化功能
- 项目涉及 Web 测试、表单填写、截图、数据提取

**创建规则文件**：将 [步骤 1b 定位的模板根路径] 中的 `playwright.md` 读取内容，写入 `.claude/rules/playwright.md`

**在 CLAUDE.md 和 AGENTS.md 中添加**：

```markdown
### 9. Playwright CLI 使用规则
- **浏览器自动化工具规范** → 详见 `.claude/rules/playwright.md`
```

**用户确认**：
- 添加规则前询问用户是否需要 Playwright 自动化功能
- 如果不需要，跳过此步骤
- 如果需要，写入 CLAUDE.md 和 AGENTS.md 前展示完整规则供确认

## 增量运行

`/cadence:init:rule-config` 支持在已初始化项目中重复执行。重复运行时应遵循“只新增缺失项，不覆盖已确认内容”的原则。

### 规则文件增量处理

复制规则文件到 `.claude/rules/` 前，先检查目标文件是否存在：

| 场景 | 行为 |
|------|------|
| 文件不存在 | 从模板根路径读取并创建 |
| 文件已存在 | **不自动覆盖**，向用户展示差异并询问是否更新 |
| 新增规则模板（如 `code-reading.md`） | 检测为缺失项，询问用户是否需要新增 |
| 规则文件已存在但缺少 CodeGraph 段落 | 不自动覆盖，展示差异并询问是否追加 |

**检测命令示例**：

```bash
for rule in README.md language.md document-storage.md markdown-format.md mcp-servers.md code-usage.md code-reading.md playwright.md; do
  if [ -e ".claude/rules/$rule" ]; then
    echo "已存在: .claude/rules/$rule"
  else
    echo "缺失: .claude/rules/$rule"
  fi
done
```

### CLAUDE.md / AGENTS.md 摘要增量处理

写入摘要引用前，先读取现有文件并检查每条规则摘要是否已存在：

| 场景 | 行为 |
|------|------|
| 摘要行已存在 | 跳过，不重复写入 |
| 摘要行缺失 | 追加到 `## 强制规则` 章节末尾 |
| 规则编号与现有内容冲突 | 按最新规范重新编号，并提示用户确认 |

### 可选规则增量处理

对于代码阅读规则、Playwright 规则等可选步骤：

| 场景 | 行为 |
|------|------|
| 规则文件和摘要均已存在 | 视为已启用，仅检查完整性，不再询问 |
| 规则文件或摘要缺失 | 作为新增可选项询问用户 |
| 无法判断历史选择 | 默认按新增项询问 |

### CodeGraph 增量处理

对于 CodeGraph 项目初始化：

| 场景 | 行为 |
|------|------|
| 老项目已执行过 `/rule-config`，但缺少 CodeGraph | 只补 CodeGraph 相关规则、摘要、MCP 配置、`.codegraph/` 初始化和 `.gitignore` |
| `.codegraph/` 已存在 | 运行 `codegraph status` 并跳过初始化 |
| `.codegraph/` 不存在 | 用户确认后执行 `codegraph init` |
| `.mcp.json` 与 `.codex/config.toml` 均已有 CodeGraph MCP server | 跳过，不重复写入 |
| `.mcp.json` 已有 CodeGraph MCP，但 `.codex/config.toml` 缺少 `[mcp_servers.codegraph]` | 参考 `.mcp.json` 手动补齐 Codex 本地 MCP 配置 |
| 任一配置文件缺少 CodeGraph MCP server | 先执行 `codegraph install --target=claude,codex --location=local --yes`，再核验并补齐缺失文件 |
| `.gitignore` 已有 `.codegraph/` | 跳过 |
| `codegraph.json` 存在 | 保留，不加入 `.gitignore` |

### 建议

- 新版 Cadence 发布或框架规则更新后，可重新运行 `/cadence:init:rule-config` 补齐新增规则。
- 重复运行前，先向用户展示本次将要新增/更新的内容清单，获取确认后再执行写入。

## 核心原则

- **规则分离** — 框架规则放 `.claude/rules/`，用户规则放 `cadence/project-rules/`
- **摘要引用** — CLAUDE.md 和 AGENTS.md 只保留摘要和引用，详细内容在规则文件中
- **目录明确** — Claude Code 配置保留在 `.claude/`，Cadence 产物放在 `cadence/`
- **用户确认** — 技术栈检测必须经过用户确认
