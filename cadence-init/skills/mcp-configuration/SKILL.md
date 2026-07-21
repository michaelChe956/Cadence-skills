---
name: mcp-configuration
description: "配置 MCP：创建 .mcp.json 配置文件和 MCP 使用规则"
disable-model-invocation: true
---

# MCP 配置

## 概述

配置 MCP 服务器：创建 `.mcp.json` 配置文件、同步 Codex `.codex/config.toml`，并添加 MCP 使用规则到 CLAUDE.md。pi 无原生 MCP，由 `/pre-check` 全局安装的 pi-mcp-adapter 扩展直接读取 `.mcp.json`（含 HTTP 类型 server），无需同步第二份配置。默认不需要人工交互即可完成基础 MCP 初始化。

## 参数模式

支持以下调用方式：

```text
/mcp-configuration
/mcp-configuration no-interrupt
/mcp-configuration --no-interrupt
```

- 命令参数包含完整 token `no-interrupt` 或 `--no-interrupt`：进入 `no-interrupt` 模式。
- 未携带上述参数：进入普通模式，完整遵循本 Skill 修改前的补齐缺失配置、同名冲突询问或跳过策略。
- 两种模式互斥；不得把 `no-interrupt` 深度合并规则应用到普通模式。

### no-interrupt 通用规则

- 禁止调用 `AskUserQuestion`、`request_user_input` 或等价用户提问工具。
- 禁止等待用户输入、设置交互超时或通过推荐默认值继续。
- 同名配置冲突必须按本节的确定性规则合并，不得保留冲突后跳过该 Server。
- 写入前必须验证 JSON/TOML 结构并保留必要备份；备份、合并或验证失败时立即报错终止。
- 失败报告不得输出 API Key、Token、Authorization Header 等真实私密值。

### no-interrupt MCP 集合合并

`mcp-configuration` 定义的必需 Server、传输类型、命令、URL 和必要参数是权威配置；当前项目配置作为补充保留。

| 场景 | 合并动作 |
|------|----------|
| Skill Server 缺失 | 新增 Skill Server |
| 项目额外 Server | 保留项目 Server |
| 同名 Server 的 `type`、`command`、`url` 冲突 | 使用 Skill 值 |
| 同名 Server 的必要参数冲突 | Skill 必需参数作为数组前缀，再追加不重复且不改变必需语义的项目参数 |
| 项目独有 `env`、`headers`、`http_headers` 或扩展字段 | 按键保留并合并 |
| 内容完全重复 | 只保留一份 |

Server 名称使用精确名称匹配，不进行大小写归一化。`.mcp.json` 按 `mcpServers` 子项合并；`.codex/config.toml` 按 `[mcp_servers.<name>]` 配置块合并。Codex 仍然只同步有 `command` 字段的 stdio Server，不同步 HTTP Server。

### no-interrupt 占位符与私密值

- `your_zhipu_api_key`、`your_minimax_api_key` 以及 `your_*_api_key` 形式的值视为占位符。
- Skill 占位符与项目非占位值冲突时，保留项目非占位值；这是“Skill 结构权威”的唯一值级例外。
- Skill 非占位值与项目值冲突时，使用 Skill 值。
- 执行报告只允许记录变量名和“已保留非占位值”，不得显示、截断显示或散列输出真实值。

### no-interrupt 解析失败与备份

1. 修改现有 `.mcp.json` 或 `.codex/config.toml` 前，先完成语法解析。
2. 无法解析时，将原文件备份为 `<原文件名>.cadence-backup-YYYYMMDDHHMMSS`。
3. 只允许恢复能够作为完整 JSON Server 对象或完整 TOML Server 配置块独立解析成功的项目配置。
4. 以 Skill 标准配置为基础重建目标文件，再按“MCP 集合合并”规则合并已恢复的完整配置块。
5. 无法安全识别项目补充配置时立即报错，不覆盖原文件；备份仅用于恢复，不代表初始化成功。
6. 合并完成后重新解析目标文件；验证失败时恢复备份并报错终止。

`no-interrupt` 模式下 `.gitignore` 使用集合合并，确保 `.worktrees/`、`.mcp.json`、`.codex/config.toml` 生效并去重。如果存在对应的精确反向规则 `!.worktrees/`、`!.mcp.json` 或 `!.codex/config.toml`，移除该反向规则；其他项目忽略规则保持不变。

## 无交互默认策略

> 本节仅适用于未携带 `no-interrupt` 或 `--no-interrupt` 的普通模式。

| 项 | 默认行为 |
|----|----------|
| 基础 MCP | 默认配置 `time`、`context7`、`sequential-thinking` |
| CodeGraph MCP | **仅 Coding 项目**：如果缺失，按 stdio 兜底配置补齐 `.mcp.json` 与 `.codex/config.toml`；非 Coding 项目跳过 |
| 智普 MCP | 默认写入 API Key 占位配置，用户后续自行替换真实密钥 |
| MiniMax MCP | 默认写入 API Key 占位配置，用户后续自行替换真实密钥 |
| Codex 同步 | 默认启用，只同步 stdio MCP |
| 已存在配置 | 不覆盖整文件，只补缺失 server 配置块；冲突配置跳过并报告 |
| `.gitignore` | 默认补齐 `.worktrees/`、`.mcp.json`、`.codex/config.toml` |

## 人工交互策略

> 本节仅适用于未携带 `no-interrupt` 或 `--no-interrupt` 的普通模式。

默认不向用户提问。只有出现以下情况才进入人工交互：

| 触发条件 | 处理方式 |
|----------|----------|
| `.mcp.json` 或 `.codex/config.toml` 中已有同名 MCP server 且配置不同 | 询问是否保留现有配置或追加新名称；无响应则保留现有配置并报告 |
| 用户明确要求禁用默认 MCP（如智普或 MiniMax） | 询问要禁用的具体 server；无响应则保留默认占位配置 |
| `.gitignore` 中存在相反规则（如显式允许 `.mcp.json`） | 询问是否调整；无响应则不修改该项 |
| 需要真实 API Key、Token 或私密信息 | 不询问真实密钥，只写占位符并提示用户自行替换 |

提问规则：
- 每次只问一个问题。
- 问题必须给出推荐默认选项。
- 如果运行环境支持自动超时，超时后采用推荐默认值。
- 如果无法等待用户输入，采用保守默认：不覆盖已有配置、不删除配置、不收集真实密钥。

## 检查清单

你必须为以下每个项目创建任务并按顺序完成：

1. **添加 MCP 使用规则** — 添加各 MCP server 的使用规则到 CLAUDE.md
2. **创建 MCP 配置文件** — 在项目根目录创建 `.mcp.json` 配置
3. **配置智普 MCP** — 默认写入智普 AI MCP 占位配置，包含四个专属 MCP
4. **配置 MiniMax MCP** — 默认写入 MiniMax Token Plan MCP 占位配置
5. **同步 MCP 配置到 Codex** — 默认同步为 Codex 的 `.codex/config.toml` 格式，仅同步 stdio MCP
6. **配置 .gitignore** — 添加 `.worktrees/`、`.mcp.json` 和 `.codex/config.toml` 到 .gitignore
7. **pi MCP 说明** — 说明 pi 经 pi-mcp-adapter 直接读取 `.mcp.json`（含 HTTP server），不维护第二份配置

**下一步**：将配置结果传递给 @project-rules-examples skill 创建个性化规则示例

## 处理流程

### 1. MCP 使用规则配置

**创建 `.claude/rules/mcp-servers.md` 规则文件**：

从 `rule-config` skill 的模板目录 `cadence-init/skills/rule-config/references/rules/mcp-servers.md` 读取模板内容（该文件也可通过 `rule-config` 步骤 1b 定位的模板根路径获取），写入项目的 `.claude/rules/mcp-servers.md` 文件。

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

#### 智普视觉理解 MCP

> **默认配置占位符** — 需要用户后续将 `your_zhipu_api_key` 替换为真实智普 GLM Coding Plan API Key

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

#### 智普联网搜索 MCP

> **默认配置占位符** — 需要用户后续将 `your_zhipu_api_key` 替换为真实智普 GLM Coding Plan API Key

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

#### 智普网页读取 MCP

> **默认配置占位符** — 需要用户后续将 `your_zhipu_api_key` 替换为真实智普 GLM Coding Plan API Key

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

#### 智普开源仓库 MCP — ZRead

> **默认配置占位符** — 需要用户后续将 `your_zhipu_api_key` 替换为真实智普 GLM Coding Plan API Key

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

#### MiniMax Token Plan MCP

> **默认配置占位符** — 需要用户后续将 `your_minimax_api_key` 替换为真实 MiniMax Token Plan API Key

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

### 4. 智普/MiniMax MCP 规则追加

> **默认添加规则说明与配置占位符** — 不需要用户提供真实 API Key，不阻塞初始化

**检测条件**：
- 默认启用智普 MCP 占位配置，用于图像分析、视频理解、UI 截图转代码、联网搜索、网页读取和开源仓库读取。
- 默认启用 MiniMax MCP 占位配置，用于网络搜索和图片理解。

**无交互行为**：
- 默认将智普/MiniMax 相关规则**追加到 `.claude/rules/mcp-servers.md` 文件末尾**。
- 默认将智普/MiniMax 配置块写入 `.mcp.json`，使用 `your_zhipu_api_key` 与 `your_minimax_api_key` 占位。
- Codex 同步时只同步 stdio MCP：智普仅同步 `zai-mcp-server`，不同步 HTTP 类型的 `web-search-prime`、`web-reader`、`zread`。
- 已存在对应规则段落时跳过，不重复追加。

**API Key 安全提醒**（必须展示）：

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
- 智普和 MiniMax MCP 默认包含占位配置，不要求用户在初始化时提供真实 API Key
- CodeGraph MCP 仅 Coding 项目启用；通常由 `rule-config` 执行 `codegraph install --target=claude,codex --location=local --yes` 自动配置；本节提供手动兜底配置

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
    }
  }
}
```

#### CodeGraph MCP 配置（仅 Coding 项目 — 缺失时自动补齐）

> **非 Coding 项目跳过此步骤**。将以下配置合并到 `.mcp.json` 的 `mcpServers` 中。CodeGraph 需要先通过 `/pre-check` 安装，并在项目根目录执行过 `codegraph init`。如果 `rule-config` 已完成 CodeGraph 配置，本步骤检测到已存在后直接跳过。

```json
{
  "codegraph": {
    "type": "stdio",
    "command": "codegraph",
    "args": [
      "serve",
      "--mcp"
    ],
    "env": {}
  }
}
```

#### 智普 MCP 配置（默认添加占位）

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

#### MiniMax MCP 配置（默认添加占位）

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

### 6. 同步 MCP 配置到 Codex

> **默认启用** — 无人工交互模式下自动生成或补齐 `.codex/config.toml`。只同步 stdio MCP。

**无交互行为**：
- 在 `.mcp.json` 创建完成后，默认同步到 Codex，生成或补齐 `.codex/config.toml`。
- 如果 `.codex/config.toml` 已存在，只追加缺失的 `[mcp_servers.<name>]` 配置块，不覆盖已有块。
- 如果已有同名 MCP server 但配置不同，跳过该 server 并在报告中标记为“需人工确认”。

**已存在文件处理**：

| 场景 | 处理方式 |
|------|---------|
| `.codex/` 目录和 `config.toml` 均不存在 | 创建目录和文件，写入完整 TOML 内容 |
| `.codex/config.toml` 已存在但不含 `[mcp_servers` | 保留原有内容，在文件末尾追加 MCP 配置 |
| `.codex/config.toml` 已存在且含 `[mcp_servers` | 只追加缺失的 server 配置块；同名不同配置跳过并报告 |

**TOML 写入规则**：
- 所有选中的 TOML 配置块合并写入同一个 `.codex/config.toml` 文件
- `[mcp_servers]` 表头只写一次，放在文件开头（或追加内容的最前面）
- 写入顺序：基础配置 → CodeGraph 配置（仅 Coding 项目） → 智普配置（默认占位）→ MiniMax 配置（默认占位）
- **Codex 不支持 HTTP 类型 MCP** — 同步时必须排除所有 `"type": "http"` 的 MCP servers，仅同步 stdio 类型（有 `command` 字段）的服务

**Codex 与 Claude Code 格式差异**：

| 特征 | Claude Code (`.mcp.json`) | Codex (`.codex/config.toml`) | pi（pi-mcp-adapter） |
|------|--------------------------|------------------------------|----------------------|
| 格式 | JSON | TOML | 复用 `.mcp.json`（JSON），无第二份配置 |
| 服务器定义 | `"mcpServers": { "name": {...} }` | `[mcp_servers.name]` | 同 `.mcp.json` |
| 传输类型 | `"type": "stdio"` / `"type": "http"` | 仅 stdio（有 `command`），**HTTP 类型不支持** | stdio 与 HTTP 均支持 |
| 环境变量 | `"env": { "KEY": "value" }` | `env = { "KEY" = "value" }` | 同 `.mcp.json` |
| HTTP 头 | `"headers": { "Authorization": "..." }` | `http_headers = { "Authorization" = "..." }` | 同 `.mcp.json` |
| type 字段 | 必须显式声明 | 不需要（自动推断） | 同 `.mcp.json` |

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
````

#### CodeGraph MCP 配置（仅 Coding 项目 — 缺失时自动补齐）

> **非 Coding 项目跳过此步骤**。将以下配置合并到 `.codex/config.toml` 的 `[mcp_servers]` 中。CodeGraph 是 stdio MCP，可同步到 Codex。如果 `rule-config` 已完成 CodeGraph 配置，本步骤检测到已存在后直接跳过。

````toml
[mcp_servers.codegraph]
command = "codegraph"
args = ["serve", "--mcp"]
````

#### 智普 MCP 配置（默认添加占位）

> 将以下配置合并到 `.codex/config.toml` 的 `[mcp_servers]` 中，`your_zhipu_api_key` 需用户自行替换

> **⚠️ Codex 不支持 HTTP 类型的 MCP servers** — 智普的 `web-search-prime`、`web-reader`、`zread` 为 HTTP 类型，不会同步到 Codex。仅同步 stdio 类型的 `zai-mcp-server`。

````toml
[mcp_servers.zai-mcp-server]
command = "npx"
args = ["-y", "@z_ai/mcp-server"]
env = { "Z_AI_API_KEY" = "your_zhipu_api_key", "Z_AI_MODE" = "ZHIPU" }
````

#### MiniMax MCP 配置（默认添加占位）

> 将以下配置合并到 `.codex/config.toml` 的 `[mcp_servers]` 中，`your_minimax_api_key` 需用户自行替换

````toml
[mcp_servers.MiniMax]
command = "uvx"
args = ["minimax-coding-plan-mcp", "-y"]
env = { "MINIMAX_API_KEY" = "your_minimax_api_key", "MINIMAX_API_HOST" = "https://api.minimaxi.com" }
````

### 7. pi MCP 说明

> **无需同步步骤** — pi 不维护第二份客户端配置文件。

- pi 官方不提供原生 MCP 支持；MCP 能力由第三方扩展 pi-mcp-adapter 提供，该扩展由 `/pre-check` 步骤 7 全局安装。
- pi-mcp-adapter 直接读取项目根目录 `.mcp.json`；本 Skill 维护的 `.mcp.json` 即 pi 的 MCP 配置来源，无需执行任何同步。
- 与 Codex 不同，pi-mcp-adapter 支持 HTTP 类型 server：智普的 `web-search-prime`、`web-reader`、`zread` 在 pi 下可用。
- `.gitignore` 无需新增条目：pi 复用的 `.mcp.json` 已在忽略清单内。

**pi 侧验证方式**：pi 会话中输入 `/mcp`（由 adapter 提供）查看 server 列表与连接状态。

### 8. 配置 .gitignore

**目的**：将 Cadence 工作目录和本地配置添加到 .gitignore，避免将临时文件、本地 MCP 配置和 Codex 项目配置提交到版本控制。无人工交互模式下默认执行。

**操作步骤**：

**1. 检查是否存在 .gitignore 文件**

```bash
ls -la .gitignore
```

**2. 添加 Cadence 相关配置**

如果 `.gitignore` 已存在，在文件末尾添加以下内容：

```gitignore
# Cadence 工作目录
.worktrees/
.mcp.json
.codex/config.toml
```

如果 `.gitignore` 不存在，创建文件并添加内容：

```bash
cat > .gitignore << 'EOF'
# Cadence 工作目录
.worktrees/
.mcp.json
.codex/config.toml
EOF
```

**说明**：

| 目录/文件 | 说明 | 排除原因 |
|----------|------|---------|
| `.worktrees/` | Git worktrees 隔离开发环境 | 包含临时的隔离开发环境，不应提交 |
| `.mcp.json` | MCP 配置文件 | 包含本地 MCP 路径配置，不应提交到版本控制 |
| `.codex/config.toml` | Codex CLI 项目级 MCP 配置 | 包含本地 MCP 路径和 API Key 占位符，不应提交 |

> pi 复用 `.mcp.json`（pi-mcp-adapter 直读），`.gitignore` 无需为 pi 新增条目。

**验证**：

```bash
git status
# 应该看不到 .worktrees/ 目录
```

**错误处理**：
- 如果项目不是 Git 仓库，提示用户稍后手动添加
- 如果配置已存在，跳过重复添加

## 核心原则

- **配置完整** — 确保所有必需的 MCP 服务器都配置
- **路径正确** — 确保路径在不同平台上都能正常工作
- **错误处理** — 提供清晰的错误信息和恢复建议
