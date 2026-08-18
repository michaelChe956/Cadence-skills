# Cadence

Cadence 是一个基于 Claude Code Skills 的多 Agent 协作系统，为 AI 编码助手提供完整的软件开发工作流程。

## 如何工作

Cadence 从你启动编码助手的那一刻开始工作。当它发现你正在构建某样东西时，它不会直接跳进去写代码，而是退后一步，问你真正想做什么。

一旦通过对话明确了需求，它会分块展示设计，让你能够真正阅读和理解。

在你批准设计后，你的助手会制定一个清晰的实现计划，强调真正的红/绿 TDD、YAGNI（你不会需要它）和 DRY。

接下来，一旦你说"开始"，它会启动一个多 Agent 协作流程，让 Agents 通过每个工程任务，检查和审查他们的工作，继续前进。Claude 通常能够自主工作几个小时，而不会偏离你制定的计划。

还有更多功能，但这是系统的核心。而且因为 Skills 会自动触发，你不需要做任何特别的事情。你的编码助手就拥有了节奏（Cadence）。

## 写在安装之前

**模型使用说明**：本项目默认会使用 MiniMax 做测试，尽可能保证 MiniMax-M2.5-highspeed 模型可以基本使用。

**推荐优先级**：Claude Opus > GLM-5（速度较慢）> MiniMax-M2.5-highspeed

### 模型推荐

#### 国内模型（推荐）

**1. GLM-5（智谱 AI）**
- ✨ **开源 SOTA 表现**：Coding 和 Agent 能力达到开源模型顶尖水平
- 🚀 **逼近 Opus 性能**：真实编程场景使用体感逼近 Claude Opus 4.5
- 🎯 **擅长复杂工程**：专为复杂系统工程与长程 Agent 任务设计
- 💰 **高性价比**：744B MoE 架构，每次推理仅激活约 10B 参数，成本更低
- 🇨🇳 **国产芯片适配**：对国产芯片适配良好，摆脱海外算力依赖

**2. MiniMax M2.5**
- ⚡ **极速推理**：100 TPS 输出速度，是主流模型的 2 倍
- 💎 **顶尖编程能力**：核心编码能力与海外顶尖闭源模型持平
- 💸 **超高性价比**：价格仅为主流旗舰模型的十分之一，支持本地部署
- 🔧 **Agent 原生设计**：专为 Agent 场景和工程效率优化
- 🌍 **多语言优势**：在多语言编码、推理速度、使用成本上具备显著优势

#### 海外模型（可选）

**1. Claude Opus 4.6**
- 👑 **最强编程能力**：终端编码、代理搜索、抽象推理等极端复杂场景的王者
- 📚 **100 万 Token 上下文**：处理超大规模代码库和文档集（Beta）
- 🎯 **长时程 Agent**：为长时程自主任务设计，可工作数小时
- 🔍 **深度推理**：扩展思考模式，适合需要深度逻辑推理的任务

**2. Claude Sonnet 4.6**
- ⚖️ **最佳性价比**：性能接近 Opus 4.6，价格仅五分之一
- 🎨 **多模态能力强**：在多模态识别与办公任务中表现优异
- 💻 **编程能力出色**：代码修改更精准，支持 100 万 Token 上下文（Beta）
- 🚀 **全面升级**：编码、计算机使用、长上下文推理、代理规划全面增强


### Claude Code 安装方式

#### 方式 1：官网安装（海外用户推荐）
访问 Claude Code 官网：https://claude.com/product/claude-code

#### 方式 2：国内镜像安装（国内用户推荐）

**国内镜像站**
- Claude-CN：https://www.claude-cn.org/
- 提供详细的国内镜像使用指南

#### 方式 3：npm 安装
```bash
# 安装 Node.js（需要 18.0 以上版本）
# 然后全局安装 Claude Code
npm install -g @anthropic-ai/claude-code
```

#### 方式 4：macOS Homebrew 安装
```bash
brew install claude-code
```

#### 方式 5：Linux APT 安装
```bash
# 添加 Anthropic 仓库
curl -fsSL https://packages.anthropic.com/public/gpg.key | sudo apt-key add -
echo "deb https://packages.anthropic.com/public stable main" | sudo tee /etc/apt/sources.list.d/anthropic.list

# 安装 Claude Code
sudo apt update
sudo apt install claude-code
```

### 推荐模型代理工具

**1. CC-Switch（推荐）**
- 🎨 **图形化界面**：操作简单，无需手动编辑配置文件
- 🔄 **一键切换**：支持 GLM、Qwen、DeepSeek 等主流国产大模型
- 🛠️ **多工具支持**：支持 Claude Code、Codex、Gemini CLI 等主流 AI 编程工具
- 📦 **跨平台**：支持 macOS、Linux、Windows
- 🔗 **GitHub**：https://github.com/farion1231/cc-switch

**2. Claude Code Router（ccr）**
- 🚦 **智能路由**：根据任务类型自动选择最适合的 AI 模型
- 🎯 **灵活策略**：支持自定义默认路由模型、背景模型和思考链模型
- 💰 **成本优化**：使用高性价比模型，降低使用成本
- 🔓 **无需官方账号**：支持第三方模型服务商
- 🔗 **GitHub**：https://github.com/musistudio/claude-code-router

### 推荐 IDE

**Trae（字节跳动）**
- 🇨🇳 **国产 AI IDE**：字节跳动推出的 AI 原生集成开发环境
- 🎯 **中文优化**：深度适配中文开发者，技术术语精准解析
- 🔧 **Builder 模式**：支持端到端项目构建，设计稿直转前端代码
- 💡 **SOLO 模式**：2025 年 8 月新增，实现全流程自动化开发
- 🆓 **完全免费**：现阶段完全免费使用
- 🌐 **官网**：https://www.trae.ai/

## 安装

Cadence 当前提供以下插件：

| 插件 | 说明 |
|------|------|
| **cadence-init** | 项目初始化 — 环境检查、项目分析、规则配置、MCP 配置、Skill 创建及 KnowledgeBase 生成与消费 |

### 方式 1: 通过插件市场安装（推荐）

在 Claude Code 中，首先注册市场：

```bash
/plugin marketplace add michaelChe956/Cadence-skills
```

然后安装插件：

```bash
/plugin install cadence-init@cadence-skills-marketplace
```

### 方式 2: 离线安装

适用于无法访问 GitHub 或需要在内网环境部署的场景。

#### 步骤 1: 获取项目代码

**方式 A: 使用 Git 克隆（推荐）**
```bash
git clone https://github.com/michaelChe956/Cadence-skills.git
cd Cadence-skills
```

**方式 B: 下载压缩包**
- 从 GitHub 下载：`https://github.com/michaelChe956/Cadence-skills/archive/refs/heads/main.zip`
- 解压到本地目录
- 进入项目目录

#### 步骤 2: 运行安装脚本

项目提供了跨平台安装脚本（v2.1，已适配单插件结构）：

**Linux/macOS**：
```bash
chmod +x install-offline.sh
./install-offline.sh
```

**Windows**：
```cmd
# 双击运行或在命令行中执行
install-offline.bat
```

安装脚本会自动完成：
- 将 `cadence-init` 安装到 `~/.claude/plugins/marketplaces/cadence-skills-local/`
- 配置 `known_marketplaces.json` 注册本地 marketplace

#### 步骤 3: 配置项目启用插件

在需要使用 Cadence 插件的项目目录中：

1. **创建 `.claude/` 目录**：
```bash
mkdir -p .claude
```

2. **创建 `settings.json` 并启用插件**：
```json
{
  "enabledPlugins": {
    "cadence-init@cadence-skills-local": true
  }
}
```

完成后重启 Claude Code 即可使用。

#### 步骤 4: 更新插件

拉取最新代码后重新运行安装脚本即可：

```bash
git pull
./install-offline.sh  # 或 install-offline.bat
```

### 验证安装

开始一个新会话，请求一些应该触发 Skill 的内容（例如，"帮我规划这个功能"或"让我们调试这个问题"）。助手应该自动调用相关的 Cadence Skills。

## 项目初始化（cadence-init 插件）

> **重要**：安装完成后，强烈建议执行以下初始化步骤，确保项目环境正确配置。以下能力均来自 `cadence-init` 插件，并以 **Skill 形式**提供，直接输入 `/名称`（如 `/pre-check`）即可触发。
> 默认初始化流程尽量无人工交互：能自动检测和补齐的内容会直接执行；遇到覆盖、删除、密钥、同名冲突等高风险操作时，会采用保守默认值或提示人工处理。

### 初始化 Skill 说明

| Skill | 默认行为 | 需要显式启用的内容 |
|------|----------|--------------------|
| `/pre-check` | 一键检查并补齐六个基础工具 `npx`、`uvx`、`ast-grep`、`codegraph`、OpenSpec、pi-mcp-adapter（pi 存在时）：已装的工具秒级跳过，缺什么装什么，装完自动复验；支持**大陆镜像加速**与**一键升级已装工具**（见下方“大陆镜像与工具升级”）；OpenSpec 检查范围为 CLI 与 `claude,codex,pi,kimi` 四客户端指令产物，按缺失客户端精确补齐（缺哪个 init 哪个）；`openspec/config.yaml` 由 `/rule-config` 创建与合并，缺失时仅提示不影响判定；Superpowers 软链同步到 `~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills`、`~/.pi/agent/skills` 四层；支持 Superpowers 离线目录 `~/.agents/superpowers`；默认只写 API Key 占位提醒，不收集真实密钥 | Playwright 安装 |
| `/project-analysis` | 分析项目结构、技术栈和依赖，生成项目初始化分析摘要文档 | — |
| `/rule-config` | 自动检测项目类型和技术栈；创建 `.claude/rules/`、`CLAUDE.md`、`AGENTS.md`、`cadence/` 目录；创建或保守合并 `openspec/config.yaml`（含 Cadence 协作上下文）；生成并升级 OpenSpec × Superpowers L0/L1/L2 协作规则；Coding 项目默认启用代码阅读规则和 CodeGraph 初始化；普通规则已有文件不覆盖 | Playwright 规则；将 `cadence/` 加入 `.gitignore` |
| `/mcp-configuration` | 默认写入基础 MCP、CodeGraph MCP、智普 MCP 占位配置、MiniMax MCP 占位配置；默认同步 stdio MCP 到 `.codex/config.toml`；pi 无原生 MCP，经 pi-mcp-adapter 直接复用 `.mcp.json`（含 HTTP 类型 server），不维护第二份配置；Kimi Code 原生复用根目录 `.mcp.json`（含 HTTP server），不维护第二份配置；真实 API Key 由用户后续自行替换 | 禁用默认 MCP 或处理同名冲突 |
| `/project-rules-examples` | 创建 `cadence/project-rules/` 个性化规则模板，补齐 CLAUDE.md / AGENTS.md 引用；已有模板不覆盖 | 覆盖已有模板或深度定制项目事实 |

### KnowledgeBase Skills

`cadence-init` 可以根据用户提供的工程、DDL、中间件、对外能力和页面范围，为 Java 与 Vue/React 存量项目建立 Schema 4.0 KnowledgeBase，并在后续任务中渐进获取相关知识。

| Skill | 作用 |
|------|------|
| [`knowledge-base-bootstrap`](readmes/skills/knowledge-base-bootstrap.md) | 校验 `cadence/knowledge-base/user-input/`，自动生成 Manifest 4.0，按固定顺序编排领域分析并跟踪初始化进度；支持首次初始化、未完成续跑、已完成保护和显式重新初始化 |
| `knowledge-base-base-info` | 生成工程、服务索引与单服务文档、数据配置、中间件和开发方式信息 |
| `knowledge-base-api` | 按用户对外能力清单和工程范围分析对外、对内 API 及集成能力，并补齐服务文档的 API 导航 |
| `knowledge-base-pages` | 分析 Vue/React 页面、路由、权限、状态和 REST API 关联，并补齐服务文档的页面导航 |
| `knowledge-base-overview` | 生成 KnowledgeBase 入口、关系导航和 Coding Agent 使用规则 |
| [`knowledge-base-update`](readmes/skills/knowledge-base-update.md) | 在初始化已完成的知识库上，根据变更包与 Git 基线安全更新现有 KnowledgeBase |
| [`knowledge-base-context`](readmes/skills/knowledge-base-context.md) | 在需求、设计、计划、编码、测试、评审或调试前，同时读取 KnowledgeBase 与当前实现，生成最小任务上下文 |

#### Schema 4.0 Manifest

Manifest 是 KnowledgeBase 自动生成的目录卡、分析范围和 Git 基线，不是数据库 Schema，也不需要用户手工配置。

用户需要维护：

```text
cadence/knowledge-base/user-input/
├── base-info.md
├── project-scope.md
├── data-model-scope.md
├── configuration-scope.md
├── middleware-scope.md
├── api-scope.md
├── page-scope.md
└── database-ddl.sql（可选）
```

其中 `base-info.md` 是强制入口。`knowledge-base-bootstrap` 校验这些输入后自动生成：

```text
cadence/knowledge-base/input-inventory.md
cadence/knowledge-base/manifest.yaml
```

Manifest 不参与 Skill 自动触发，只在 Skill 触发后提供 Schema 版本、用户授权范围和 KnowledgeBase 基线。

#### 初始化生命周期

`knowledge-base-bootstrap` 根据 Manifest 的 `coverage.initialization` 进度自动判定当前状态：

- **首次初始化**：未发现任何 KnowledgeBase 产物时，按 `base-info → api → pages → overview → global-validation` 固定顺序编排执行；`api`、`pages` 不适用时登记跳过原因。
- **未完成续跑**：上次初始化中断（`status: in_progress`）时，从首个未完成阶段继续，已完成阶段直接复用，不重复扫描。
- **已完成保护**：初始化已完成（`status: complete`）时不再重复初始化，引导使用 `knowledge-base-context` 查询知识库，或使用 `knowledge-base-update` 处理变更。
- **显式重新初始化**：只有用户明确请求"重新初始化 Schema 4.0"时才清理旧产物全量重建；执行前会列出清理路径与风险并取得明确授权，普通初始化、修复或更新请求不会触发清理。

完整生命周期判定、状态不变量、配置快照安全和 user-input 填写案例见 [knowledge-base-bootstrap 使用指南](readmes/skills/knowledge-base-bootstrap.md)。

#### 变更更新（knowledge-base-update）

Update 只接受初始化已完成的知识库。变更前由用户在 `cadence/knowledge-base/user-input/updates/CHANGE-变更标识/` 准备完整变更包（五份固定文档），`knowledge-base-update` 校验变更包、Git 基线和影响链后统一更新各领域文档；任一环节失败时丢弃全部暂存结果，不产生部分写入。

五份文档字段说明、敏感信息红线和完整变更案例见 [knowledge-base-update 使用指南](readmes/skills/knowledge-base-update.md)。

#### KnowledgeBase 任务上下文

Claude Code 插件手动调用：

```text
/cadence-init:knowledge-base-context
```

Codex 在 Skill 已安装或被项目发现后手动调用：

```text
$knowledge-base-context
```

当目标项目已有 Schema 4.0 KnowledgeBase，并且项目规则已经接入时，需求澄清、Design、Plan、Coding、Testing、Review 和 Debug 任务可以通过自然语言自动触发该 Skill。

完整用法、任务画像、双轨读取和输出说明见 [knowledge-base-context 使用指南](readmes/skills/knowledge-base-context.md)。

### 强制无交互模式（no-interrupt）

`pre-check`、`rule-config`、`mcp-configuration`、`project-rules-examples` 支持显式的强制无交互参数：

```bash
/pre-check no-interrupt
/rule-config no-interrupt
/mcp-configuration no-interrupt
/project-rules-examples no-interrupt
```

`--no-interrupt` 与 `no-interrupt` 等价，例如：

```bash
/pre-check --no-interrupt
```

> **向后兼容**：不携带 `no-interrupt` 或 `--no-interrupt` 时，四个 Skill 完整保持原有逻辑，包括条件询问、保守默认、冲突跳过和历史文档迁移等行为。

| Skill | no-interrupt 模式行为 |
|------|------------------------|
| `/pre-check` | 除 Playwright 外，由脚本强制完成 npx、uvx、ast-grep、codegraph、OpenSpec（CLI 与四客户端指令产物；`openspec/config.yaml` 缺失不算失败，由 `/rule-config` 创建）、pi-mcp-adapter 的安装和验证；任一基础工具失败立即终止；Superpowers 同步四层软链（含 `~/.pi/agent/skills`）且固定离线目录无效时直接报错；同名冲突先备份再处理；PATH 中存在 pi 可执行文件但 `pi-mcp-adapter` 安装失败时立即终止，pi 不存在时跳过不算失败 |
| `/rule-config` | 冲突时以 `rule-config` 模板和强制规则为准，项目已有内容作为补充合并；只报告历史文档目录，不执行迁移 |
| `/mcp-configuration` | 冲突时以标准 MCP 结构和必需参数为准，保留项目额外 Server、扩展字段和已有非占位密钥；解析或验证失败时恢复备份并终止 |
| `/project-rules-examples` | 冲突时以标准模板骨架和强制约束为准，保留项目事实、真实占位值和额外章节；无法结构化合并时备份并保留原文 |

强制无交互模式不会调用用户提问工具，也不会等待确认或使用交互超时。无法自动完成严格结果时会直接报错终止，并报告失败步骤和恢复建议。

新项目可以使用以下全程强制无交互初始化流程。`/init` 和 `/project-analysis` 不支持该参数，仍按原方式调用：

```bash
/pre-check no-interrupt
/init
/project-analysis
/rule-config no-interrupt
/mcp-configuration no-interrupt
/project-rules-examples no-interrupt
```

> **职责边界**：`/pre-check` 负责 OpenSpec CLI 与四客户端指令产物；`openspec/config.yaml` 由 `/rule-config` 步骤 11 创建与合并（含 Cadence 协作上下文）。顺序保持 `/pre-check` 先、`/rule-config` 后；即使顺序颠倒，`/pre-check` 也会按缺失客户端补齐产物且保留已有 config.yaml。

如果需要 Playwright，请明确说明：

```bash
/pre-check 并启用 Playwright
/rule-config 并启用 Playwright 规则
```

智普和 MiniMax 默认会写入占位符：

```text
your_zhipu_api_key
your_minimax_api_key
```

请在初始化完成后自行替换为真实密钥，不要把真实 API Key 直接告诉 AI Agent。

### 步骤 1：前置条件检查

触发 `/pre-check` Skill，一键完成六个基础工具的检查与补齐：

```bash
/pre-check
```

该 Skill 会：
- ✅ 检查并补齐六个基础工具：`npx`、`uvx`、`ast-grep`、`codegraph`、OpenSpec、pi-mcp-adapter（pi 存在时）；已安装的工具**秒级跳过**，缺什么装什么，装完自动复验
- ✅ **大陆镜像加速**：国内网络可切换淘宝 npm 镜像、清华 pypi 镜像与国内 Git 镜像（见下方“大陆镜像与工具升级”）
- ✅ **一键升级**：可把 `ast-grep`、`codegraph`、OpenSpec、`uv` 升级到当前源最新版本（见下方“大陆镜像与工具升级”）
- ✅ OpenSpec 检查 CLI 与 `claude,codex,pi,kimi` 四客户端指令产物，缺失哪个客户端就先 `openspec init --tools <缺失客户端>` 再 `openspec update`；`openspec/config.yaml` 由 `/rule-config` 创建，缺失时仅提示
- ✅ Superpowers 软链同步到 `~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills`、`~/.pi/agent/skills` 四层，支持在线更新与离线目录同步
- ✅ 检测到 pi 可执行文件时条件检查并安装 `pi-mcp-adapter`（未安装 pi 时跳过）
- ✅ 默认跳过 Playwright，除非显式启用
- ✅ 默认提醒后续替换智普/MiniMax API Key 占位符

> **执行环境**：`/pre-check` 的所有产物都落在**当前项目根目录**——OpenSpec 的 `.claude/.codex/.pi` 写在项目根，Superpowers 装在 `~/.agents/`，不会改动 Cadence 自身的源码目录。

#### 大陆镜像与工具升级

`/pre-check` 内置两套下载源，可按网络环境切换：

- **大陆镜像**：淘宝 npm 镜像、清华 pypi 镜像、国内 Superpowers Git 镜像，适合国内网络，下载更快更稳。
- **通用源**：npmjs、pypi、GitHub 官方源（默认）。

**怎么用大陆镜像？** 直接用自然语言告诉 Agent 即可，不需要记命令参数。例如输入：

```text
/pre-check 用大陆镜像
```

或者说“用国内镜像跑 pre-check”“走淘宝镜像初始化”。Agent 会在执行时自动切换到大陆镜像源（内部对应脚本的 `--mirror cn`）。

**镜像的作用范围**：

- 只对**本次调用**生效，不会被记住；下次默认仍用通用源，需要时再说一次即可。
- 本次调用中，npm/pypi 包下载走淘宝/清华镜像，Superpowers 仓库也从国内 Git 镜像 clone/更新。
- **不修改你的全局配置**（`~/.npmrc`、uv 配置、git 全局配置都不动），镜像只在本次初始化过程内生效。

**怎么升级工具？** 同样用自然语言说明，例如：

```text
/pre-check 并升级这些工具
```

或“把 ast-grep、codegraph、openspec 升到最新版”。升级范围是 `ast-grep`、`codegraph`、OpenSpec、`uv`（`npx`/Node.js、`pi-mcp-adapter`、`uvx` 临时包不升级）。版本口径：用大陆镜像就以镜像最新版为准，用通用源就以官方最新版为准。升级也可以和镜像一起用，例如“用大陆镜像跑 pre-check 并升级工具”。

### 步骤 2：项目分析

触发 `/project-analysis` Skill，分析项目结构：

```bash
/project-analysis
```

该 Skill 会：
- ✅ 分析项目技术栈和依赖
- ✅ 生成项目初始化分析摘要文档

### 步骤 3：Claude Code 规则配置

触发 `/rule-config` Skill，配置项目规则：

```bash
/rule-config
```

该 Skill 会：
- ✅ 创建 `.claude/rules/` 规则目录
- ✅ 创建 `cadence/project-rules/` 用户规则目录
- ✅ 创建或保守合并 `openspec/config.yaml`（含 Cadence 协作上下文）
- ✅ 在 CLAUDE.md 和 AGENTS.md 中规范化生成/修复 `## 强制规则` 章节（权威 7 条、清理已退役规则如 Serena、重排编号、用户内容逐字保留）
- ✅ 配置目录结构
- ✅ 生成并升级 OpenSpec × Superpowers L0/L1/L2 协作规则（L0 v2 含产物路径覆盖表与自动提交开关条款）
- ✅ Coding 项目默认启用 CodeGraph 与代码阅读规则
- ✅ 默认不启用 Playwright 规则，除非显式要求
- ✅ 写入产物自动提交开关（默认关闭，见下文）

#### 入口文件规范化效果（v2 新增）

对已存在非 Cadence 风格入口文件的项目（如自带知识库内容的 AGENTS.md），重跑 `/rule-config` 后：

- 缺失的 `## 强制规则` 章节会被完整创建（L0 区块之后）；英文/自定义内容逐字保留；
- 已退役规则残留（如 Serena）被删除，编号 1-9 错乱重排为权威 1-7；
- 双入口写入同一份技术栈检测结果，用户已有真实值保留不变；
- L0 旧版（v1）确定性升级为 v2，不再弹用户决策；重跑幂等零变更。

#### 产物路径覆盖（v2 新增）

L0 v2 内核与 `document-storage.md` 内置显式路径映射表，优先级高于任何 Superpowers Skill 正文中的默认路径：

| Skill 默认路径 | 本项目强制路径 |
|---|---|
| `docs/superpowers/specs/`（design/spec） | `cadence/designs/` |
| `docs/superpowers/plans/`（plan） | `cadence/plans/` |

OpenSpec 产物仍存放在 `openspec/` 目录。设计文档、实施计划从此不再散落到 `docs/superpowers/` 下。

#### 产物自动提交开关（v2 新增）

初始化后入口文件 `## 项目配置` 章节会出现：

```markdown
- **产物自动提交（design/plan）**：关闭
```

**使用方法：**

- **默认关闭**：Superpowers 的 `brainstorming`/`writing-plans` 写完设计文档/实施计划后**禁止自动 `git commit`**，只汇报产物路径等待你确认——适合不想被 Agent 动 git 历史的项目；
- **开启自动提交**：把该行手改为 `：开启` 即可，之后 design/plan 写完会自动提交；
- **取值语义**：仅精确值 `开启` 视为启用，`关闭` 或任何其他值均按关闭处理；非法值保留原文不改写并在报告中告警；
- **开关位置**：脚本保证全文件恰好一行开关行且在 `## 项目配置` 章节内——即使你误把它挪到章节外，重跑 `/rule-config` 会自动归并回规范位置，开关不会失效；
- **读取顺序**：Agent 以 CLAUDE.md 为准、AGENTS.md 为兜底，双入口值不一致时按关闭处理；
- **修改后无需重跑初始化**，Agent 每次写产物前都会现读入口文件。

OpenSpec 管契约，Superpowers 管行为。规则模板同时定义 Claude/Kimi、Codex 与 pi 三类客户端的 Skill 调用与路由回执约定（pi 与 Codex 同类：显式选择 Skill → 用途并入首段回执 → 全文读取 `SKILL.md` → 读完后才允许仓库操作）。已初始化项目更新 Cadence 后重新运行 `/rule-config`，即可升级受管规则。普通模式遇到无法识别的本地修改且没有获得替换确认时会保留并报告；`no-interrupt` 模式会先备份，备份成功后再替换。

### 步骤 4：MCP 配置

触发 `/mcp-configuration` Skill，配置 MCP：

```bash
/mcp-configuration
```

该 Skill 会：
- ✅ 创建 `.mcp.json` 配置文件
- ✅ 配置 MCP 使用规则
- ✅ 默认写入智普/MiniMax API Key 占位配置
- ✅ 默认同步 stdio MCP 到 `.codex/config.toml`（Codex 不支持 HTTP 类型 MCP）
- ✅ pi 经 pi-mcp-adapter 直接复用 `.mcp.json`（含 HTTP 类型 server），不维护第二份配置
- ✅ Kimi Code 原生复用根目录 `.mcp.json`（含 HTTP server），不维护第二份配置
- ✅ 默认将 `.worktrees/`、`.mcp.json`、`.codex/` 加入 `.gitignore`

### 步骤 5（推荐）：项目个性化规则

触发 `/project-rules-examples` Skill，创建项目个性化规则：

```bash
/project-rules-examples
```

该 Skill 会：
- ✅ 创建需求文档模板
- ✅ 创建设计文档模板
- ✅ 创建代码开发规范
- ✅ 创建测试规范

**完成后**，您的项目就准备好使用 Cadence 的完整工作流程了！

## Skills 库

> **注**：Cadence 当前以 Skill 形式提供能力，核心为 `cadence-init` 插件下的以下 Skills。

### 元 Skills（1个）

- **skill-creator** - 创建、校验、打包并优化 Claude Code skills [📖 详细指南](readmes/skills/skill-creator.md)

### KnowledgeBase Skills（7个）

- **knowledge-base-bootstrap** - 校验用户输入、初始化 Schema 4.0 KnowledgeBase 并编排领域分析 [📖 详细指南](readmes/skills/knowledge-base-bootstrap.md)
- `knowledge-base-base-info` - 生成工程、服务、数据、中间件和开发方式信息
- `knowledge-base-api` - 分析对外能力和工程内对内能力
- `knowledge-base-pages` - 分析页面、路由、权限和 REST API 关联
- `knowledge-base-overview` - 生成知识库入口、导航和项目使用规则
- **knowledge-base-update** - 消费完整变更包，幂等更新已有 KnowledgeBase [📖 详细指南](readmes/skills/knowledge-base-update.md)
- **knowledge-base-context** - 从任务出发，同时读取 KnowledgeBase 与当前实现并生成最小上下文 [📖 详细指南](readmes/skills/knowledge-base-context.md)

**📖 [查看所有 Skills 详细指南](readmes/skills/README.md)**

## Commands 库

Cadence 当前以 Skill 形式提供能力，不再提供独立的 Command。其中 `skill-creator`、`pre-check` 等由 `cadence-init` 插件以 Skill 形式提供，直接输入 `/skill-creator`、`/pre-check` 即可触发。

**📖 [查看详细指南](readmes/commands/README.md)**

## 最佳实践

### 1. 规范化项目初始化

- 使用 `cadence-init` 完成环境检查、项目分析与规则配置
- 通过 KnowledgeBase 为后续开发提供经过校验的项目上下文

### 2. 基于知识库开展工作

- 首次建立 KnowledgeBase 后，在需求、设计、编码、评审等任务前使用 `knowledge-base-context` 获取最小上下文
- 项目事实变化时使用 `knowledge-base-update` 幂等更新

## 技术亮点

### 1. Schema 4.0 KnowledgeBase

- 覆盖工程、服务、数据、中间件与开发方式
- 字段级数据模型与配置快照
- 支持渐进式任务上下文生成

### 2. 智能项目初始化

- 自动检测项目类型和技术栈
- 跨平台兼容（macOS/Linux/Windows）
- 同时支持 Claude Code、Codex、pi 与 Kimi Code 四类客户端的环境初始化（OpenSpec 产物、Superpowers 软链、MCP 接入）
- 用户确认机制确保准确性

## 哲学

- **测试驱动开发** - 始终先写测试
- **系统化优于临时** - 流程优于猜测
- **降低复杂度** - 简单性是首要目标
- **证据优于声明** - 在声明成功前验证

## Skill Creator（生成可直接调用的 Skills）

仓库提供了元技能 [`cadence-init/skills/skill-creator/SKILL.md`](cadence-init/skills/skill-creator/SKILL.md)，用于在本仓库中持续创建和维护可直接调用的 Skills。

使用方式很简单：

1. 在 Claude Code / Codex 中明确提出你要创建或更新一个 Skill。
2. 说明 Skill 的目标、适用场景、触发方式，以及希望生成到哪个目录。
3. 让助手调用 `skill-creator`，它会按仓库约定补齐技能目录结构、`SKILL.md` 内容以及必要元数据。
4. 生成后，再让助手帮你检查描述是否清晰、触发条件是否准确，以及是否需要补充示例。

适合的指令示例：

- “帮我创建一个用于生成需求文档的 Skill”
- “基于现有模板，新建一个前端评审 Skill”
- “优化这个 Skill 的说明，让它更容易被正确触发”

如果你只是想快速开始，直接告诉助手“使用 `skill-creator` 帮我创建一个新 Skill”，再补充名称和用途即可。

## 贡献

Skills 直接存储在这个仓库中。要贡献：

1. Fork 仓库
2. 为你的 Skill 创建分支
3. 遵循 `cadence-init/skills/skill-creator/SKILL.md` 创建和测试新 Skills
4. 提交 PR

## 更新

### 市场安装更新

```bash
/plugin update cadence-init
```

### 离线安装更新

拉取最新代码后重新运行安装脚本：

```bash
git pull
./install-offline.sh  # 或 install-offline.bat
```

## 许可证

MIT License - 详见 LICENSE 文件

## 支持

- **问题反馈**: https://github.com/michaelChe956/Cadence-skills/issues
- **市场**: https://github.com/michaelChe956/Cadence-skills-marketplace

## 致谢

本项目受到 [Superpowers](https://github.com/obra/superpowers) 的启发，感谢 Jesse Vincent 创建了优秀的 Skills 系统。
