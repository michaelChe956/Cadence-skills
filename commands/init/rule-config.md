---
name: rule-config
description: "配置 Claude Code 规则：语言规则、文档规则、命名规则和目录结构"
---

# Claude Code 规则配置

## 概述

配置 Claude Code 的规则：语言规则、文档存储规则、命名规范和目录结构创建。

## 检查清单

你必须为以下每个项目创建任务并按顺序完成：

1. **语言规则配置** — 配置强制中文响应
2. **文档存储规则配置** — 配置 `.claude` 目录结构
3. **文档命名规则配置** — 配置 `YYYY-MM-DD_类型_名称_v版本.md` 格式
4. **包管理器规则** — 前端使用 pnpm，Python 使用 uv
5. **技术栈检测** — 自动检测语言、测试/检查/格式化命令，需要用户确认
6. **目录结构创建** — 创建 `.claude/` 子目录
7. **Playwright Skills 规则配置** — 配置 Playwright CLI 的使用规则（可选）
8. **智普/MiniMax MCP 使用规则配置** — 配置智普 AI 和 MiniMax MCP 的使用规则（可选）

**下一步**：将配置结果传递给 @mcp-configuration skill 进行 MCP 配置

## 处理流程

### 1. 语言规则配置

**添加以下规则到 CLAUDE.md**：

```markdown
## 语言规则

- **必须使用中文回答** - 所有响应、解释、注释和文档必须使用中文。代码本身可以使用英文（变量名、函数名等），但所有与用户的交互必须使用中文。
```

### 2. 文档存储规则配置

**添加以下规则到 CLAUDE.md**：

```markdown
## 文档存储规则

> **所有文档必须存放在 `.claude` 目录下，禁止在项目根目录或其他位置创建文档文件。**

### 文档分类存储规范

| 文档类型 | 存储路径 | 说明 |
|---------|---------|------|
| **计划文档** | **`.claude/plans/`** | **项目计划、开发计划、发布计划（🔴 强制路径）** |
| **概要需求** | **`.claude/prds/`** | **brainstorm skill 生成的概要需求方案（🔴 新增）** |
| 需求文档 | `.claude/docs/` | requirement skill 生成的详细需求文档 |
| 方案设计 | `.claude/designs/` | 技术方案、架构设计、API设计 |
| **设计评审** | **`.claude/designs-reviews/`** | **设计评审文档（🔴 新增）** |
| **分析报告** | **`.claude/analysis-docs/`** | **代码分析、调研报告、性能分析（🔴 路径调整）** |
| **进度报告** | **`.claude/reports/`** | **开发进度报告、阶段总结（🔴 新增）** |
| **个性化规则** | **`.claude/project-rules/`** | **项目个性化模板和规范（🔴 新增）** |
| **README文档** | **见下方详细规则** | **项目说明、安装指南、使用文档（🔴 特殊规则）** |
| 页面原型 | `.claude/modaos/` | 墨刀/Figma 原型截图、设计稿 |
| 数据模型 | `.claude/models/` | 数据库表模型、ER图、schema |
| 架构文档 | `.claude/architecture/` | 系统架构分析、技术选型 |
| 开发笔记 | `.claude/notes/` | 临时记录、开发心得、TODO |
| 开发日志 | `.claude/logs/` | 问题追踪、Bug记录、开发进度 |
```

### 3. 文档命名规则配置

**添加以下规则到 CLAUDE.md**：

```markdown
## 文档命名规范

### 标准格式

```
YYYY-MM-DD_文档类型_文档名称_v版本号.扩展名
```

### Plan 文档格式

```
YYYY-MM-DD_计划文档_计划类型_具体内容_v版本号.md
```

> **🔴 强制规则**：所有 Plan 文档（计划文档）**必须**存储在 `.claude/plans/` 目录下，禁止存储在其他任何位置。

### 临时笔记格式

```
YYYY-MM-DD_简短描述.md
```

### 版本号规则

- **首次创建**：`v1.0`
- **小更新**（错别字、格式调整）：`v1.1`、`v1.2`
- **重大更新**（内容大幅修改）：`v2.0`、`v3.0`
```

### 4. 包管理器规则

**添加以下规则到 CLAUDE.md**：

```markdown
## 包管理器规则

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

### 5. 技术栈检测

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
## 项目技术栈

- **语言**：[语言列表]
- **包管理器**：[pnpm/uv]
- **测试命令**：[命令]
- **检查命令**：[命令]
- **格式化命令**：[命令]
- **覆盖率阈值**：80%
```

### 6. 目录结构创建

**创建以下目录结构**：

```bash
mkdir -p .claude/{prds,analysis-docs,docs,designs,designs-reviews,plans,readmes,modaos,models,architecture,notes,logs,reports,project-rules/examples}
```

**目录用途说明**：

| 目录 | 用途 | 说明 |
|------|------|------|
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

### 7. Playwright Skills 规则配置

**检测条件**：
- 用户需要浏览器自动化功能
- 项目涉及 Web 测试、表单填写、截图、数据提取

**添加以下规则到 CLAUDE.md**：

````markdown
## Playwright CLI 使用规则

> **浏览器自动化工具规范**

### 用途

Playwright CLI 是一个 Token-efficient 的浏览器自动化工具，适合：
- Web 应用测试
- 表单自动填写
- 网页截图
- 数据提取
- 网站导航和交互

### 触发场景

- 用户需要测试 Web 应用
- 用户需要自动填写网页表单
- 用户需要截取网页截图
- 用户需要从网页提取数据
- 用户需要与网页进行交互

### 常用命令

#### 基础操作

```bash
# 打开浏览器
playwright-cli open
playwright-cli open https://example.com --headed

# 页面导航
playwright-cli goto https://playwright.dev
playwright-cli go-back
playwright-cli go-forward
playwright-cli reload

# 获取页面快照（用于获取元素 ref）
playwright-cli snapshot

# 元素交互（使用 snapshot 返回的 ref）
playwright-cli click e15
playwright-cli type "搜索内容"
playwright-cli fill e5 "user@example.com"
playwright-cli hover e4
playwright-cli check e12
playwright-cli uncheck e12
playwright-cli select e9 "option-value"

# 键盘操作
playwright-cli press Enter
playwright-cli press ArrowDown
playwright-cli keydown Shift
playwright-cli keyup Shift

# 截图
playwright-cli screenshot
playwright-cli screenshot --filename=page.png

# 关闭浏览器
playwright-cli close
```

#### 会话管理

```bash
# 列出所有会话
playwright-cli list

# 关闭所有浏览器
playwright-cli close-all

# 强制终止所有浏览器进程
playwright-cli kill-all
```

#### 存储操作

```bash
# 保存存储状态（cookies、localStorage 等）
playwright-cli state-save auth.json

# 加载存储状态
playwright-cli state-load auth.json

# Cookie 操作
playwright-cli cookie-list
playwright-cli cookie-set session_id abc123
playwright-cli cookie-delete session_id
```

### 使用规则

1. **必须使用 snapshot** - 在进行任何元素交互前，必须先执行 `playwright-cli snapshot` 获取元素 ref
2. **使用 ref 定位元素** - 不要使用选择器，使用 snapshot 返回的元素 ref（如 e15、e21）
3. **Headless 优先** - 默认使用 headless 模式，需要可视化调试时使用 `--headed`
4. **会话隔离** - 不同项目使用不同的会话（`-s=` 参数）
5. **状态管理** - 需要保持登录状态时，使用 `state-save` 和 `state-load`

### 典型工作流

```bash
# 1. 打开浏览器并导航
playwright-cli open https://example.com/login

# 2. 获取页面快照
playwright-cli snapshot

# 3. 填写表单（使用 snapshot 返回的 ref）
playwright-cli fill e5 "username"
playwright-cli fill e8 "password"

# 4. 点击登录
playwright-cli click e10

# 5. 验证结果
playwright-cli screenshot --filename=after-login.png

# 6. 保存登录状态（可选）
playwright-cli state-save auth.json

# 7. 关闭浏览器
playwright-cli close
```

### 重要规则

- 交互前必须先执行 snapshot 获取元素 ref
- 使用 `--headed` 参数可以看到浏览器界面
- 使用 `-s=session-name` 可以创建独立会话
- 截图保存到当前工作目录
````

**用户确认**：
- 添加规则前询问用户是否需要 Playwright 自动化功能
- 如果不需要，跳过此步骤
- 如果需要，写入 CLAUDE.md 前展示完整规则供确认

### 8. 智普/MiniMax MCP 使用规则配置（可选）

**检测条件**：
- 用户需要图像分析、视频理解、UI 截图转代码等视觉 AI 能力
- 用户需要网络搜索、网页内容抓取等联网能力
- 用户需要 GitHub 开源仓库文档搜索和代码读取能力
- 用户需要 MiniMax 的网络搜索和图片理解能力

**添加以下规则到 CLAUDE.md**：

````markdown
## 智普/MiniMax MCP 使用规则（可选）

> **⚠️ 可选配置** — 以下 MCP 需要对应平台的 API Key

### API Key 安全提醒

> **🔴 安全警告**
> 1. 请自行前往对应平台获取 API Key，不要将真实密钥告诉 Claude Code
> 2. 配置文件中使用占位符，用户需自行替换为真实密钥
> 3. `.mcp.json` 已在 `.gitignore` 中排除，不会提交到版本控制
>
> - 智普 API Key 获取地址：https://open.bigmodel.cn/usercenter/apikeys
> - MiniMax API Key 获取地址：https://platform.minimaxi.com/subscribe/token-plan

### 智普视觉理解 MCP

**用途**：图像分析、视频理解、UI 截图转代码、OCR 文字提取、错误截图诊断

**触发场景**：
- 需要分析本地图片或截图内容
- UI 截图转换为前端代码
- 从截图中提取文字（OCR）
- 分析错误弹窗、堆栈截图
- 解读架构图、流程图、UML 图
- 分析数据可视化图表
- 对比两张 UI 截图差异
- 视频内容理解

**工具列表**：

| 工具名 | 功能 |
|--------|------|
| `ui_to_artifact` | 将 UI 截图转换为代码、提示词、设计规范 |
| `extract_text_from_screenshot` | OCR 提取截图中的文字 |
| `diagnose_error_screenshot` | 解析错误弹窗/堆栈截图，给出修复建议 |
| `understand_technical_diagram` | 解读架构图、流程图、UML、ER 图 |
| `analyze_data_visualization` | 分析仪表盘、统计图表 |
| `ui_diff_check` | 对比两张 UI 截图差异 |
| `image_analysis` | 通用图像理解 |
| `video_analysis` | 视频场景解析（MP4/MOV/M4V，本地最大 8M） |

**使用规则**：
1. 图片建议放到本地目录，通过对话指定图片名称或路径来调用
2. 直接在客户端粘贴图片无法调用此 MCP（Claude Code 除外）
3. 需要安装最新版本（>= 0.1.2）

**典型工作流**：
```bash
# 分析本地截图
> 请分析 screenshot.png 的内容

# UI 截图转代码
> 请将 design.png 转换为 React 组件代码

# OCR 提取文字
> 提取 error-log.png 中的错误信息

# 视频分析
> 分析 demo.mp4 中的操作流程
```

### 智普联网搜索 MCP

**用途**：网络搜索、实时信息获取

**触发场景**：
- 需要搜索最新技术文档或解决方案
- 获取实时信息（新闻、更新日志等）
- 查找特定技术问题的最佳实践

**工具列表**：

| 工具名 | 功能 |
|--------|------|
| `webSearchPrime` | 搜索网络信息，返回网页标题、URL、摘要、网站名称等 |

**使用规则**：
1. 基于 HTTP 协议的远程服务，无需本地安装运行时
2. 搜索结果包含标题、URL、摘要等结构化信息

**典型工作流**：
```bash
# 搜索技术方案
> 帮我搜索 React Server Components 的最新最佳实践

# 查找解决方案
> 搜索 Node.js 内存泄漏的排查方法
```

### 智普网页读取 MCP

**用途**：网页内容抓取、结构化数据提取

**触发场景**：
- 需要读取指定 URL 的网页完整内容
- 提取 API 文档、技术文章的结构化内容
- 解析开源项目页面（README、Release Notes）

**工具列表**：

| 工具名 | 功能 |
|--------|------|
| `webReader` | 抓取指定 URL 的网页内容，返回标题、正文、元数据、链接列表 |

**使用规则**：
1. 基于 HTTP 协议的远程服务，无需本地安装运行时
2. 返回结构化数据，包含标题、正文、元数据等

**典型工作流**：
```bash
# 读取 API 文档
> 帮我读取 https://docs.example.com/api 的内容并总结要点

# 解析项目页面
> 读取这个 GitHub 仓库的 README 页面，提取安装步骤
```

### 智普开源仓库 MCP（ZRead）

**用途**：GitHub 开源仓库文档搜索、代码结构获取、代码读取

**触发场景**：
- 需要了解某个开源库的使用方法或实现原理
- 查看 GitHub 仓库的目录结构和文件列表
- 读取 GitHub 仓库中指定文件的代码内容
- 排查开源库的 Issue 和历史记录

**工具列表**：

| 工具名 | 功能 |
|--------|------|
| `search_doc` | 搜索 GitHub 仓库的知识文档、新闻、Issue、PR、贡献者等 |
| `get_repo_structure` | 获取 GitHub 仓库的目录结构和文件列表 |
| `read_file` | 读取 GitHub 仓库中指定文件的完整代码内容 |

**使用规则**：
1. 基于 HTTP 协议的远程服务（基于 zread.ai），无需本地安装运行时
2. 支持搜索文档、浏览结构、读取代码三种操作

**典型工作流**：
```bash
# 快速上手开源库
> 搜索 langchain 仓库的文档，了解如何使用 RAG 功能

# 查看仓库结构
> 获取 facebook/react 仓库的目录结构

# 读取源码
> 读取 vercel/next.js 仓库中 packages/next/src/server/app-render 目录的代码
```

### MiniMax Token Plan MCP

**用途**：网络搜索和图片理解

**触发场景**：
- 需要网络搜索获取实时信息
- 需要理解和分析图片内容

**前置条件**：需要 `uvx`（pre-check 已包含检查）

**工具列表**：

| 工具名 | 功能 |
|--------|------|
| `web_search` | 网络搜索，获取实时信息 |
| `understand_image` | 图片理解和分析 |

**环境变量**：

| 变量 | 说明 | 必需 |
|------|------|------|
| `MINIMAX_API_KEY` | MiniMax API 密钥 | 是 |
| `MINIMAX_API_HOST` | API 地址，固定为 `https://api.minimaxi.com` | 是 |
| `MINIMAX_MCP_BASE_PATH` | 本地输出目录路径（需有写入权限） | 否 |
| `MINIMAX_API_RESOURCE_MODE` | 资源提供方式：`url` 或 `local`，默认 `url` | 否 |

**使用规则**：
1. 基于 uvx 运行的本地 MCP 服务
2. 验证配置：进入 Claude Code 后输入 `/mcp`，能看到 `web_search` 和 `understand_image` 说明配置成功

**典型工作流**：
```bash
# 网络搜索
> 搜索 Python 3.12 的新特性有哪些

# 图片理解
> 分析 architecture.png 中的系统架构设计
```
````

**用户确认**：
- 添加规则前询问用户是否需要智普/MiniMax MCP 能力
- 如果不需要，跳过此步骤
- 如果需要，展示 API Key 安全提醒，写入 CLAUDE.md 前展示完整规则供确认
- 智普和 MiniMax 可以独立选择，不需要同时启用

## 核心原则

- **强制执行** — 规则必须严格执行
- **目录明确** — 每种文档类型有明确存储位置
- **命名统一** — 所有文档使用统一命名格式
- **用户确认** — 技术栈检测必须经过用户确认

