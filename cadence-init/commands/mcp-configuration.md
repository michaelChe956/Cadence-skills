---
name: mcp-configuration
description: "配置 MCP：创建 .mcp.json 配置文件和 MCP 使用规则"
---

# MCP 配置

## 概述

配置 MCP 服务器：创建 `.mcp.json` 配置文件和添加 MCP 使用规则到 CLAUDE.md。

## 检查清单

你必须为以下每个项目创建任务并按顺序完成：

1. **添加 MCP 使用规则** — 添加各 MCP server 的使用规则到 CLAUDE.md
2. **创建 MCP 配置文件** — 在项目根目录创建 `.mcp.json` 配置
3. **配置智普 MCP（可选）** — 询问用户是否需要智普 AI 的四个专属 MCP
4. **配置 MiniMax MCP（可选）** — 询问用户是否需要 MiniMax Token Plan MCP
5. **同步 MCP 配置到 Codex（可选）** — 询问用户是否将 MCP 配置同步为 Codex 的 `.codex/config.toml` 格式
6. **配置 .gitignore** — 添加 `.serena/`、`.worktrees/`、`.mcp.json` 和 `.codex/` 到 .gitignore

**下一步**：将配置结果传递给 @project-rules-examples skill 创建个性化规则示例

## 处理流程

### 1. MCP 使用规则配置

**创建 `.claude/rules/mcp-servers.md` 规则文件**：

从 `references/rules/mcp-servers.md` 读取模板内容，写入项目的 `.claude/rules/mcp-servers.md` 文件。

**在 CLAUDE.md 中添加摘要引用行**：

```markdown
### 6. MCP Server 使用规则
- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`
```

> 以下为各 MCP 的配置说明，供配置时参考。详细使用规则见 `.claude/rules/mcp-servers.md`。

#### Time MCP

**用途**：获取当前时间和时区转换

**触发场景**：
- 需要获取当前日期时间
- 需要进行时区转换
- 用户询问"现在几点"、"今天日期"等

**使用方式**：
```json
{
  "tool": "mcp__time__get_current_time",
  "timezone": "Asia/Shanghai"
}
```

#### Context7 MCP

**用途**：获取官方技术文档和代码示例

**触发场景**：
- 遇到 import/require 语句
- 使用框架特定功能（React、Vue、Next.js 等）
- 需要官方 API 文档而非通用解决方案
- 版本特定实现要求

**使用方式**：
1. 先调用 `mcp__context7__resolve-library-id` 解析库 ID
2. 再调用 `mcp__context7__query-docs` 获取文档

**示例**：
```json
// 步骤1：解析库
{"libraryName": "react"}
// 返回："/react/react"

// 步骤2：获取文档
{"libraryId": "/react/react", "query": "hooks"}
```

#### Sequential Thinking MCP

**用途**：复杂问题的多步骤推理

**触发场景**：
- 复杂调试场景（多层级）
- 架构分析和系统设计
- 使用 `--think`、`--think-hard`、`--ultrathink` 标志
- 需要假设测试和验证的问题
- 多组件故障调查

**使用方式**：
```json
{
  "tool": "mcp__sequential-thinking__sequentialthinking",
  "thought": "当前思考内容",
  "thoughtNumber": 1,
  "totalThoughts": 5,
  "nextThoughtNeeded": true
}
```

#### Serena MCP

**用途**：语义代码理解和项目内存

**触发场景**：
- 符号操作：重命名、提取、移动函数/类
- 项目级代码导航和探索
- 多语言项目
- 会话生命周期管理（`/cad-load`、`/cad-save`）
- 大型代码库分析（>50 文件）

**常用命令**：
- `mcp__serena__activate_project` - 激活项目
- `mcp__serena__list_memories` - 列出记忆
- `mcp__serena__find_symbol` - 查找符号
- `mcp__serena__get_symbols_overview` - 获取符号概览

**重要规则**：
- 禁止分析 `.git/` 目录
- 使用 Git 命令获取版本信息
```

#### 智普视觉理解 MCP（可选）

> **⚠️ 可选配置** — 添加前必须询问用户是否需要，需要智普 GLM Coding Plan API Key

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
```
# 分析本地截图
> 请分析 screenshot.png 的内容

# UI 截图转代码
> 请将 design.png 转换为 React 组件代码

# OCR 提取文字
> 提取 error-log.png 中的错误信息

# 视频分析
> 分析 demo.mp4 中的操作流程
```

#### 智普联网搜索 MCP（可选）

> **⚠️ 可选配置** — 添加前必须询问用户是否需要，需要智普 GLM Coding Plan API Key

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
```
# 搜索技术方案
> 帮我搜索 React Server Components 的最新最佳实践

# 查找解决方案
> 搜索 Node.js 内存泄漏的排查方法

# 获取实时信息
> 搜索 TypeScript 最新版本的新特性
```

#### 智普网页读取 MCP（可选）

> **⚠️ 可选配置** — 添加前必须询问用户是否需要，需要智普 GLM Coding Plan API Key

**用途**：网页内容抓取、结构化数据提取

**触发场景**：
- 需要读取指定 URL 的网页完整内容
- 提取 API 文档、技术文章的结构化内容
- 解析开源项目页面（README、Release Notes）
- 参考外部文档修复 Bug

**工具列表**：

| 工具名 | 功能 |
|--------|------|
| `webReader` | 抓取指定 URL 的网页内容，返回标题、正文、元数据、链接列表 |

**使用规则**：
1. 基于 HTTP 协议的远程服务，无需本地安装运行时
2. 返回结构化数据，包含标题、正文、元数据等

**典型工作流**：
```
# 读取 API 文档
> 帮我读取 https://docs.example.com/api 的内容并总结要点

# 解析项目页面
> 读取这个 GitHub 仓库的 README 页面，提取安装步骤

# 参考文档修复 Bug
> 读取这个 Stack Overflow 链接，参考解决方案修复当前 Bug
```

#### 智普开源仓库 MCP — ZRead（可选）

> **⚠️ 可选配置** — 添加前必须询问用户是否需要，需要智普 GLM Coding Plan API Key

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
```
# 快速上手开源库
> 搜索 langchain 仓库的文档，了解如何使用 RAG 功能

# 查看仓库结构
> 获取 facebook/react 仓库的目录结构

# 读取源码
> 读取 vercel/next.js 仓库中 packages/next/src/server/app-render 目录的代码

# 排查 Issue
> 搜索 prisma/prisma 仓库中关于连接池超时的 Issue
```

#### MiniMax Token Plan MCP（可选）

> **⚠️ 可选配置** — 添加前必须询问用户是否需要，需要 MiniMax Token Plan API Key

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
```
# 网络搜索
> 搜索 Python 3.12 的新特性有哪些

# 图片理解
> 分析 architecture.png 中的系统架构设计
```

### 4. 智普/MiniMax MCP 规则追加（可选）

> **⚠️ 可选配置** — 添加前必须询问用户是否需要

**检测条件**：
- 用户需要图像分析、视频理解、UI 截图转代码等视觉 AI 能力
- 用户需要网络搜索、网页内容抓取等联网能力
- 用户需要 GitHub 开源仓库文档搜索和代码读取能力
- 用户需要 MiniMax 的网络搜索和图片理解能力

**用户确认**：
- 添加规则前询问用户是否需要智普/MiniMax MCP 能力
- 如果不需要，跳过此步骤
- 如果需要，展示 API Key 安全提醒，将智普/MiniMax 相关规则**追加到 `.claude/rules/mcp-servers.md` 文件末尾**
- 智普和 MiniMax 可以独立选择，不需要同时启用

**API Key 安全提醒**（如果用户选择启用，**必须**展示）：

```
⚠️ API Key 安全提醒：
1. 请自行前往对应平台获取 API Key，不要将真实密钥告诉 Claude Code
2. 配置文件中使用占位符（如 your_zhipu_api_key），用户需自行替换为真实密钥
3. .mcp.json 已在 .gitignore 中排除，不会提交到版本控制
4. 建议使用环境变量管理密钥，避免明文存储

智普 API Key 获取地址：https://open.bigmodel.cn/usercenter/apikeys
MiniMax API Key 获取地址：https://platform.minimaxi.com/subscribe/token-plan
```

### 5. MCP 配置文件创建
**说明**：
- `{{SERENA_PATH}}` 需要替换为用户提供的 Serena 本地路径。必须是全路径，默认路径为：`/Users/username/.cadence/serena`。**不可以使用`~/.cadence/serena`等相对路径**
- windows和linux的默认路径分别为：`C:\Users\username\.cadence\serena`和`/home/username/.cadence/serena`
- Windows 路径需要处理反斜杠（使用 `\\` 或转换为正斜杠 `/`）
- 智普和 MiniMax MCP 为**可选配置**，根据用户选择决定是否包含

**在项目根目录创建 `.mcp.json`**：

#### 基础配置（必选）

```json
{
  "mcpServers": {
    "time": {
      "command": "uvx",
      "args": [
        "mcp-server-time",
        "--local-timezone=Asia/Shanghai"
      ]
    },
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@upstash/context7-mcp"
      ],
      "env": {}
    },
    "sequential-thinking": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sequential-thinking"
      ],
      "env": {}
    },
    "serena": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "{{SERENA_PATH}}",
        "serena",
        "start-mcp-server",
        "--context",
        "ide-assistant",
        "--enable-web-dashboard",
        "false",
        "--enable-gui-log-window",
        "false"
      ],
      "env": {}
    }
  }
}
```

#### 智普 MCP 配置（可选 — 用户确认后添加）

> 将以下配置合并到 `.mcp.json` 的 `mcpServers` 中，`your_zhipu_api_key` 需用户自行替换

```json
{
  "zai-mcp-server": {
    "type": "stdio",
    "command": "npx",
    "args": [
      "-y",
      "@z_ai/mcp-server"
    ],
    "env": {
      "Z_AI_API_KEY": "your_zhipu_api_key",
      "Z_AI_MODE": "ZHIPU"
    }
  },
  "web-search-prime": {
    "type": "http",
    "url": "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp",
    "headers": {
      "Authorization": "Bearer your_zhipu_api_key"
    }
  },
  "web-reader": {
    "type": "http",
    "url": "https://open.bigmodel.cn/api/mcp/web_reader/mcp",
    "headers": {
      "Authorization": "Bearer your_zhipu_api_key"
    }
  },
  "zread": {
    "type": "http",
    "url": "https://open.bigmodel.cn/api/mcp/zread/mcp",
    "headers": {
      "Authorization": "Bearer your_zhipu_api_key"
    }
  }
}
```

#### MiniMax MCP 配置（可选 — 用户确认后添加）

> 将以下配置合并到 `.mcp.json` 的 `mcpServers` 中，`your_minimax_api_key` 需用户自行替换

```json
{
  "MiniMax": {
    "command": "uvx",
    "args": [
      "minimax-coding-plan-mcp",
      "-y"
    ],
    "env": {
      "MINIMAX_API_KEY": "your_minimax_api_key",
      "MINIMAX_API_HOST": "https://api.minimaxi.com"
    }
  }
}
```

### 6. 同步 MCP 配置到 Codex（可选）

> **⚠️ 可选配置** — 添加前必须询问用户是否需要

**用户确认**：
- 在 `.mcp.json` 创建完成后，询问用户："是否将 MCP 配置同步到 Codex（生成 `.codex/config.toml`）？"
- 如果不需要，跳过此步骤
- 如果需要，根据下方模板生成 `.codex/config.toml`

**已存在文件处理**：

| 场景 | 处理方式 |
|------|---------|
| `.codex/` 目录和 `config.toml` 均不存在 | 创建目录和文件，写入完整 TOML 内容 |
| `.codex/config.toml` 已存在但不含 `[mcp_servers` | 保留原有内容，在文件末尾追加 MCP 配置 |
| `.codex/config.toml` 已存在且含 `[mcp_servers` | 询问用户是否覆盖 MCP 配置部分 |

**TOML 写入规则**：
- 所有选中的 TOML 配置块合并写入同一个 `.codex/config.toml` 文件
- `[mcp_servers]` 表头只写一次，放在文件开头（或追加内容的最前面）
- 写入顺序：基础配置 → 智普配置（如果选中）→ MiniMax 配置（如果选中）
- **Codex 不支持 HTTP 类型 MCP** — 同步时必须排除所有 `"type": "http"` 的 MCP servers，仅同步 stdio 类型（有 `command` 字段）的服务

**Codex 与 Claude Code 格式差异**：

| 特征 | Claude Code (`.mcp.json`) | Codex (`.codex/config.toml`) |
|------|--------------------------|------------------------------|
| 格式 | JSON | TOML |
| 服务器定义 | `"mcpServers": { "name": {...} }` | `[mcp_servers.name]` |
| 传输类型 | `"type": "stdio"` / `"type": "http"` | 仅 stdio（有 `command`），**HTTP 类型不支持** |
| 环境变量 | `"env": { "KEY": "value" }` | `env = { "KEY" = "value" }` |
| HTTP 头 | `"headers": { "Authorization": "..." }` | `http_headers = { "Authorization" = "..." }` |
| type 字段 | 必须显式声明 | 不需要（自动推断） |

**`{{SERENA_PATH}}` 替换规则与 `.mcp.json` 相同**。

**信任提醒**：
- 提醒用户：首次在 Codex 中打开项目时需确认信任项目，否则 `.codex/config.toml` 不会被加载

**在项目根目录创建 `.codex/config.toml`**：

#### 基础配置（必选）

````toml
[mcp_servers]

[mcp_servers.time]
command = "uvx"
args = ["mcp-server-time", "--local-timezone=Asia/Shanghai"]

[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]

[mcp_servers.sequential-thinking]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]

[mcp_servers.serena]
command = "uvx"
args = ["--from", "{{SERENA_PATH}}", "serena", "start-mcp-server", "--context", "ide-assistant", "--enable-web-dashboard", "false", "--enable-gui-log-window", "false"]
````

#### 智普 MCP 配置（可选 — 用户确认后添加）

> 将以下配置合并到 `.codex/config.toml` 的 `[mcp_servers]` 中，`your_zhipu_api_key` 需用户自行替换

> **⚠️ Codex 不支持 HTTP 类型的 MCP servers** — 智普的 `web-search-prime`、`web-reader`、`zread` 为 HTTP 类型，不会同步到 Codex。仅同步 stdio 类型的 `zai-mcp-server`。

````toml
[mcp_servers.zai-mcp-server]
command = "npx"
args = ["-y", "@z_ai/mcp-server"]
env = { "Z_AI_API_KEY" = "your_zhipu_api_key", "Z_AI_MODE" = "ZHIPU" }
````

#### MiniMax MCP 配置（可选 — 用户确认后添加）

> 将以下配置合并到 `.codex/config.toml` 的 `[mcp_servers]` 中，`your_minimax_api_key` 需用户自行替换

````toml
[mcp_servers.MiniMax]
command = "uvx"
args = ["minimax-coding-plan-mcp", "-y"]
env = { "MINIMAX_API_KEY" = "your_minimax_api_key", "MINIMAX_API_HOST" = "https://api.minimaxi.com" }
````

### 7. 配置 .gitignore

**目的**：将 Cadence 工作目录添加到 .gitignore，避免将临时文件和本地配置提交到版本控制。

**操作步骤**：

**1. 检查是否存在 .gitignore 文件**

```bash
ls -la .gitignore
```

**2. 添加 Cadence 相关配置**

如果 `.gitignore` 已存在，在文件末尾添加以下内容：

```gitignore
# Cadence 工作目录
.serena/
.worktrees/
.mcp.json
.codex/
```

如果 `.gitignore` 不存在，创建文件并添加内容：

```bash
cat > .gitignore << 'EOF'
# Cadence 工作目录
.serena/
.worktrees/
.mcp.json
.codex/
EOF
```

**说明**：

| 目录/文件 | 说明 | 排除原因 |
|----------|------|---------|
| `.serena/` | Serena MCP 本地记忆和会话数据 | 包含用户本地的会话记录和项目记忆，不应共享 |
| `.worktrees/` | Git worktrees 隔离开发环境 | 包含临时的隔离开发环境，不应提交 |
| `.mcp.json` | MCP 配置文件 | 包含本地 MCP 路径配置，不应提交到版本控制 |
| `.codex/` | Codex CLI 项目级配置 | 包含本地 MCP 路径和 API Key 占位符，不应提交 |

**验证**：

```bash
git status
# 应该看不到 .serena/ 和 .worktrees/ 目录
```

**错误处理**：
- 如果项目不是 Git 仓库，提示用户稍后手动添加
- 如果配置已存在，跳过重复添加

## 核心原则

- **配置完整** — 确保所有必需的 MCP 服务器都配置
- **路径正确** — 确保路径在不同平台上都能正常工作
- **错误处理** — 提供清晰的错误信息和恢复建议
