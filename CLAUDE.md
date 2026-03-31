# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作提供指导。

## 强制规则

> **🔴 必须遵守 - 无例外**

### 1. 语言规则

- **必须使用中文回答** - 所有响应、解释、注释和文档必须使用中文。代码本身可以使用英文（变量名、函数名等），但所有与用户的交互必须使用中文。

### 2. 代码使用规则

> **🔴 Skills 项目特殊规定**

- **非必要不编写代码** - 这是一个 Skills/Commands 配置项目，主要工作对象是 Markdown 文档、YAML 配置、JSON 数据等非代码文件。
- **必须说明理由** - 如果确实需要编写代码（如脚本、验证工具等），必须先向用户说明为什么必须使用代码，以及代码的作用和必要性。
- **优先替代方案** - 在决定编写代码前，必须先考虑是否可以通过纯文档方式、现有工具或配置文件完成相同目标。

**适用场景判断**：
- ✅ **允许**：文档编写、配置文件编辑、结构设计、方案规划、需求分析
- ⚠️ **需说明**：辅助脚本、验证工具、自动化处理（必须先说明必要性）
- ❌ **避免**：功能开发、业务逻辑实现、应用程序编写

### 3. 文档存储规则

> **所有文档必须存放在 `.claude` 目录下，禁止在项目根目录或其他位置创建文档文件。**

#### 文档分类存储规范

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

#### README 文档存储规则

> **🔴 特殊规则 - README 文档分类存储**

README 文档根据内容和用途分为两类，存储位置不同：

| README 类型 | 存储位置 | 内容说明 | 示例 |
|------------|---------|---------|------|
| **项目介绍** | 根目录 `README.md` 或根目录 `readmes/` | 面向项目使用者的介绍性文档 | 项目简介、快速开始、功能说明、用户指南 |
| **开发相关** | `.claude/readmes/` | 面向开发者的技术文档 | 开发指南、API文档、架构说明、技术栈介绍 |

**详细说明**：

1. **项目介绍类 README**（存储在根目录）
   - 根目录 `README.md`：项目主入口文档，包含项目简介、安装步骤、快速使用指南
   - 根目录 `readmes/`：用户相关的详细文档，如用户手册、使用教程、FAQ等
   - 目标受众：项目使用者、最终用户

2. **开发相关类 README**（存储在 `.claude/readmes/`）
   - 开发环境搭建指南
   - 技术架构说明
   - API 接口文档
   - 开发规范和最佳实践
   - 目标受众：项目开发者、维护者

**判断标准**：
- ❓ **问自己**：这个文档是给谁看的？
  - 👤 **用户** → 根目录 `README.md` 或 `readmes/`
  - 👨‍💻 **开发者** → `.claude/readmes/`

**示例**：

```
项目根目录/
├── README.md                          # 项目主介绍（用户看）
├── readmes/                           # 用户文档目录
│   ├── user-guide.md                  # 用户使用指南
│   ├── faq.md                         # 常见问题
│   └── changelog.md                   # 版本更新日志
└── .claude/
    └── readmes/                       # 开发文档目录
        ├── 2025-12-03_README_开发环境搭建_v1.0.md
        ├── 2025-12-03_README_API文档_v1.0.md
        └── 2025-12-03_README_架构设计_v1.0.md
```

#### 文档命名规范

> **🔴 强制规则 - 必须遵守**

##### 标准格式

```
YYYY-MM-DD_文档类型_文档名称_v版本号.扩展名
```

##### Plan 文档格式

```
YYYY-MM-DD_计划文档_计划类型_具体内容_v版本号.md
```

> **🔴 强制规则**：所有 Plan 文档（计划文档）**必须**存储在 `.claude/plans/` 目录下，禁止存储在其他任何位置。

##### 临时笔记格式

```
YYYY-MM-DD_简短描述.md
```

##### 示例

```
# 普通文档
2025-12-03_技术方案_用户认证_v1.0.md
2025-11-15_需求文档_订单管理_v2.0.md
2025-10-20_分析报告_性能优化_v1.0.pdf

# Plan 文档（必须存储在 .claude/plans/ 目录）
.claude/plans/2025-12-03_计划文档_项目开发_用户认证模块_v1.0.md
.claude/plans/2025-12-01_计划文档_版本发布_v2.0.0发布计划.md

# 临时笔记
2025-12-03_当前任务.md
2025-11-30_调试记录.md
```

##### 命名规则

| 元素 | 规则 |
|------|------|
| 日期 | `YYYY-MM-DD` 格式，必须使用阿拉伯数字 |
| 文档类型 | 中文描述，如：`技术方案`、`需求文档`、`分析报告`、`计划文档` |
| 版本号 | `vX.Y` 格式，初版为 `v1.0`，更新为 `v1.1`、`v2.0` 等 |
| 扩展名 | 根据实际类型：`.md`、`.pdf`、`.png` 等 |
| 分隔符 | 使用 `_` 下划线连接各部分，`.` 用于扩展名 |

##### 版本号规则

- **首次创建**：`v1.0`
- **小更新**（错别字、格式调整）：`v1.1`、`v1.2`
- **重大更新**（内容大幅修改）：`v2.0`、`v3.0`

##### 检查清单

在创建任何文档前，必须确认：
- [ ] 文件名符合 `YYYY-MM-DD_类型_名称_v版本.扩展名` 格式
- [ ] 日期使用当日日期
- [ ] 版本号正确（首次为 v1.0）
- [ ] 文档存放在 `.claude/` 对应子目录
- [ ] **Plan 文档**：确认存储在 `.claude/plans/` 目录

#### 路径映射（跨平台）

根据当前系统自动适配：

| 系统 | 完整路径示例 |
|------|-------------|
| **macOS** | `/Users/michaelche/projects/myproject/.claude/docs/` |
| **Linux** | `/home/michaelche/projects/myproject/.claude/docs/` |
| **Windows** | `C:\Users\michaelche\projects\myproject\.claude\docs\` |

> **注意**：在 Claude Code 中使用相对路径 `.claude/` 即可，系统会自动解析。

#### 禁止行为

❌ **禁止** 在以下位置创建文档：
- 项目根目录（**例外**：`README.md` 主文件和 `readmes/` 用户文档目录）
- `docs/` 目录
- `documents/` 目录
- `files/` 目录
- 任何其他非 `.claude` 的目录（**例外**：根目录 `readmes/` 用于项目介绍文档）

❌ **禁止** 创建分散的文档文件，必须统一放在 `.claude/` 下的对应子目录（**例外**：项目介绍类 README 可放在根目录）。

#### 检查清单

在创建任何文档前，必须确认：
- [ ] 文档类型已明确
- [ ] 对应的 `.claude/` 子目录存在（若不存在则创建）
- [ ] 文件命名符合规范
- [ ] **Plan 文档强制路径**：计划类文档必须存储在 `.claude/plans/` 目录
- [ ] **README 文档路径**：
  - [ ] 项目介绍类 → 根目录 `README.md` 或 `readmes/`
  - [ ] 开发相关类 → `.claude/readmes/`

### 4. Markdown 格式规则

- **严格注意 Markdown 格式** - 在编写包含代码块的文档时，如果出现代码块嵌套冲突，必须使用以下解决方案：
  - **外层代码块**：使用 4 个反引号 (````)
  - **内层代码块**：使用 3 个反引号 (```)

**示例**：

```javascript
function example() {
  return "这是嵌套的代码示例";
}
```

### 5. Serena 使用规则

> **🔴 项目分析工具规范**

- **禁止分析 .git 目录** - 当使用 Serena MCP 工具分析项目时，必须跳过 `.git/` 目录及其所有内容。
- **使用 Git 命令获取版本信息** - 如果需要获取 Git 相关信息（如提交历史、分支信息、文件变更等），必须使用 Git 命令（如 `git log`、`git branch`、`git diff` 等），而不是通过 Serena 分析 `.git/` 目录。
- **原因说明**：
  - `.git/` 目录包含版本控制的元数据和对象文件，分析这些内容没有实际意义
  - 避免不必要的资源消耗和性能浪费
  - Git 命令提供了更高效、更准确的版本信息查询方式

**正确做法示例**：
```bash
# ✅ 正确：使用 git 命令获取提交历史
git log --oneline -10

# ✅ 正确：使用 git 命令查看分支信息
git branch -a

# ✅ 正确：使用 git 命令查看文件变更
git diff HEAD~1
```

**错误做法示例**：
```bash
# ❌ 错误：使用 Serena 分析 .git 目录
serena analyze .git/

# ❌ 错误：使用 Serena 读取 .git 目录下的文件
serena read .git/objects/...
```

### 6. MCP Server 使用规则

> **🔴 MCP 工具使用规范**

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
2. 再调用 `mcp__context7__get-library-docs` 获取文档

**示例**：
```json
// 步骤1：解析库
{"libraryName": "react"}
// 返回："/react/react"

// 步骤2：获取文档
{"context7CompatibleLibraryID": "/react/react", "topic": "hooks"}
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
- 禁止分析 `.git/` 目录（详见"### 5. Serena 使用规则"）
- 使用 Git 命令获取版本信息

#### 智普视觉理解 MCP（可选）

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

#### 智普联网搜索 MCP（可选）

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

#### 智普网页读取 MCP（可选）

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

#### 智普开源仓库 MCP — ZRead（可选）

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

#### MiniMax Token Plan MCP（可选）

**用途**：网络搜索和图片理解

**触发场景**：
- 需要网络搜索获取实时信息
- 需要理解和分析图片内容

**工具列表**：

| 工具名 | 功能 |
|--------|------|
| `web_search` | 网络搜索，获取实时信息 |
| `understand_image` | 图片理解和分析 |

**使用规则**：
1. 基于 uvx 运行的本地 MCP 服务
2. 验证配置：进入 Claude Code 后输入 `/mcp`，能看到 `web_search` 和 `understand_image` 说明配置成功

#### 智普/MiniMax API Key 安全提醒

> **🔴 安全警告**
> 1. 请自行前往对应平台获取 API Key，不要将真实密钥告诉 Claude Code
> 2. 配置文件中使用占位符，用户需自行替换为真实密钥
> 3. `.mcp.json` 已在 `.gitignore` 中排除，不会提交到版本控制
>
> - 智普 API Key 获取地址：https://open.bigmodel.cn/usercenter/apikeys
> - MiniMax API Key 获取地址：https://platform.minimaxi.com/subscribe/token-plan

### 7. 项目个性化规则

> **🔴 定制化能力**

- **规则目录**：`.claude/project-rules/`
- **使用方法**：
  1. 查看项目初始化时创建的示例文件（`examples/` 目录）
  2. 根据需要复制和修改示例文件到 `project-rules/` 目录
  3. 在本文件（CLAUDE.md）中添加规则，指导 Claude 使用您的定制文档

**示例规则**：

````markdown
## 项目个性化规则（示例）

> 以下是使用示例，默认不启用。
> 如果您创建了自定义规则，可以取消注释或添加类似规则：

<!--
### 需求文档格式
使用 `.claude/project-rules/requirement-template.md` 作为需求文档格式，
不要使用 requirement skill 中的通用格式。

### 设计文档格式
使用 `.claude/project-rules/design-template.md` 作为设计文档模板。

### 代码开发规范
所有代码开发必须遵循 `.claude/project-rules/coding-standards.md` 中的规范。
-->
````

**说明**：
- 个性化规则由用户主动启用
- Claude Code 会自动遵循 CLAUDE.md 中的规则
- 示例文件仅作参考，不强制使用
- 用户可以根据项目需求自由定制规则内容

---

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

---

## 项目信息

