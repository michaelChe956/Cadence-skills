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

Cadence 由两个独立插件组成：

| 插件 | 说明 |
|------|------|
| **cadence-init** | 项目初始化 — 环境检查、项目分析、规则配置、MCP 配置、Skill 创建 |
| **cadence-workflow** | 开发工作流 — 完整/快速/探索流程、TDD、代码审查、进度追踪 |

### 方式 1: 通过插件市场安装（推荐）

在 Claude Code 中，首先注册市场：

```bash
/plugin marketplace add michaelChe956/Cadence-skills
```

然后分别安装两个插件：

```bash
/plugin install cadence-init@cadence-skills-marketplace
/plugin install cadence-workflow@cadence-skills-marketplace
```

> 两个插件可以独立安装。如果只需要项目初始化功能，安装 `cadence-init` 即可；如果只需要开发工作流，安装 `cadence-workflow` 即可。推荐同时安装以获得完整体验。

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

项目提供了跨平台安装脚本（v2.0，已适配双插件结构）：

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
- 将 `cadence-init` 和 `cadence-workflow` 安装到 `~/.claude/plugins/marketplaces/cadence-skills-local/`
- 配置 `known_marketplaces.json` 注册本地 marketplace
- 设置 `cadence-workflow/hooks/session-start` 的执行权限（macOS/Linux）

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
    "cadence-init@cadence-skills-local": true,
    "cadence-workflow@cadence-skills-local": true
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

> **重要**：安装完成后，强烈建议执行以下初始化步骤，确保项目环境正确配置。以下命令均来自 `cadence-init` 插件。

### 步骤 1：前置条件检查

执行 `/pre-check` 命令，自动检查和配置必要的工具：

```bash
/pre-check
```

该命令会：
- ✅ 检查 npx 是否安装（Node.js 包执行器）
- ✅ 检查 uvx 是否安装（Python 包执行器）
- ✅ 检查 serena 项目是否配置（用于代码分析）
- ✅ 自动安装缺失的工具
- ✅ 引导您完成 serena 项目配置

### 步骤 2：项目分析

执行 `/project-analysis` 命令，分析项目结构：

```bash
/project-analysis
```

该命令会：
- ✅ 分析项目技术栈和依赖
- ✅ 生成项目初始化分析摘要文档

### 步骤 3：Claude Code 规则配置

执行 `/rule-config` 命令，配置项目规则：

```bash
/rule-config
```

该命令会：
- ✅ 创建 `.claude/rules/` 规则目录（8 个框架内置规则文件）
- ✅ 创建 `cadence/project-rules/` 用户规则目录
- ✅ 在 CLAUDE.md 中添加规则摘要引用
- ✅ 配置目录结构

### 步骤 4：MCP 配置

执行 `/mcp-configuration` 命令，配置 MCP：

```bash
/mcp-configuration
```

该命令会：
- ✅ 创建 `.mcp.json` 配置文件
- ✅ 配置 MCP 使用规则

### 步骤 5（可选）：项目个性化规则

执行 `/project-rules-examples` 命令，创建项目个性化规则：

```bash
/project-rules-examples
```

该命令会：
- ✅ 创建需求文档模板
- ✅ 创建设计文档模板
- ✅ 创建代码开发规范
- ✅ 创建测试规范

**完成后**，您的项目就准备好使用 Cadence 的完整工作流程了！

## 基本工作流程（cadence-workflow 插件）

Cadence 提供 3 种流程模式，适应不同的开发场景：

### 1. 完整流程（Full Flow）

**适用场景**：复杂功能开发（预估>2小时）、团队协作项目、企业级应用

**流程节点**：
1. **Brainstorm** - 需求探索，通过苏格拉底式对话明确需求
2. **Analyze** - 存量分析，分析现有代码库
3. **Requirement** - 需求分析，输出结构化需求文档
4. **Design** - 技术设计，输出详细技术方案
5. **Design Review** - 设计审查，验证设计质量
6. **Plan** - 实现计划，分解为具体任务
7. **Git Worktrees** - 创建隔离环境，避免冲突
8. **Subagent Development** - 代码实现 + 单元测试

**关键特性**：
- 每个节点完成后人工确认
- 支持断点续传
- 两阶段审查（规范审查 + 代码质量审查）

### 2. 快速流程（Quick Flow）

**适用场景**：简单功能开发（预估<2小时）、原型验证、Bug 修复

**流程节点**：
1. **Requirement** - 需求分析
2. **Plan** - 实现计划
3. **Git Worktrees** - 创建隔离环境
4. **Subagent Development** - 代码实现

**关键特性**：
- 跳过探索和分析阶段
- 快速进入开发
- 仍然保持 TDD 和审查机制

### 3. 探索流程（Exploration Flow）

**适用场景**：新技术验证、技术选型、创新功能、原型开发、POC 验证

**流程节点**：
1. **Brainstorm** - 需求探索（探索性 PRD）
2. **Analyze** - 存量分析（简化分析）
3. **Git Worktrees** - 创建隔离环境（poc/ 分支）
4. **Subagent Development** - 原型开发 + 测试（质量要求较低）

**关键特性**：
- 允许失败和迭代，可从任何节点回到之前的节点
- 原型代码质量要求较低，但必须能验证核心想法
- Subagent Development 完成后进入**评估阶段**，有 4 种结局：
  - ✅ **结局1: 转标准流程** - 功能可行 + 需要正式实现 → 清理 POC 代码，从 Design 开始正式实现
  - 🔄 **结局2: 继续探索** - 功能可行但需要调整 → 再次循环 Subagent Development
  - 📚 **结局3: 技术储备完成** - 功能可行但暂不需要 → 清理 POC 代码，记录技术方案
  - ❌ **结局4: 记录教训** - 功能不可行 → 清理 POC 代码，记录失败原因
- 探索成功后建议从 Design 节点开始正式实现（不直接使用 POC 代码）
- 产物可能是技术验证报告而非最终代码

**助手会在任何任务前检查相关的 Skills。** 这是强制性工作流程，不是建议。

## Skills 库

> **注**：Cadence 包含 14 个核心 Skills（下文列出）和 5 个从 [superpowers](https://github.com/obra/superpowers) 继承的 Skills（test-driven-development, verification-before-completion, requesting-code-review, receiving-code-review, finishing-a-development-branch）。

### 核心节点 Skills（8个）

**需求阶段**
- **brainstorming** - 需求探索，通过苏格拉底式对话明确需求 [📖 详细指南](readmes/skills/brainstorming.md)
- **analyze** - 存量分析，使用 Serena MCP 分析现有代码库
- **requirement** - 需求分析，输出结构化需求文档

**设计阶段**
- **design** - 技术设计，输出详细技术方案（支持带着审查报告重新设计）
- **design-review** - 设计审查，验证设计质量（4 个维度）
- **plan** - 实现计划，分解为具体任务（每个任务 2-5 分钟）

**开发阶段**
- **using-git-worktrees** - 创建隔离环境，避免冲突
- **subagent-development** - 代码实现 + 单元测试（3 个 Subagent 角色）

**进度追踪阶段**
- **status** - 查看项目进度，计算完成百分比，显示时间统计 [📖 详细指南](readmes/skills/status.md)
- **checkpoint** - 创建检查点，保存完整上下文，支持恢复 [📖 详细指南](readmes/skills/checkpoint.md)
- **resume** - 恢复中断的工作流程，重建上下文 [📖 详细指南](readmes/skills/resume.md)
- **report** - 生成进度报告，支持日报和周报 [📖 详细指南](readmes/skills/report.md)
- **monitor** - 查看状态快照（一次性，非实时）[📖 详细指南](readmes/skills/monitor.md)

**数据管理阶段**
- **data-validation** - 数据验证，写入前验证数据格式和必填字段 [📖 详细指南](readmes/skills/data-validation.md)
- **data-cleanup** - 数据清理，归档旧数据并删除过期数据 [📖 详细指南](readmes/skills/data-cleanup.md)
- **version-migration** - 版本迁移，升级旧版本数据到当前版本 [📖 详细指南](readmes/skills/version-migration.md)

**📖 [查看所有 Skills 详细指南](readmes/skills/README.md)**

### 流程 Skills（3个）

- **full-flow** - 完整流程（8 个节点），适用于复杂功能开发 [📖 详细指南](readmes/skills/full-flow.md)
- **quick-flow** - 快速流程（4 个节点），适用于简单功能开发 [📖 详细指南](readmes/skills/quick-flow.md)
- **exploration-flow** - 探索流程（4 个节点 + 迭代），适用于新技术验证 [📖 详细指南](readmes/skills/exploration-flow.md)

**📖 [查看所有 Skills 详细指南](readmes/skills/README.md)**

### 元 Skills（3个）

- **using-cadence** - Cadence Skills 系统使用指南 [📖 详细指南](readmes/skills/using-cadence.md)
- **cad-load** - 项目上下文加载 [📖 详细指南](readmes/skills/cad-load.md)
- **skill-creator** - 创建、校验、打包并优化 Claude Code skills [📖 详细指南](readmes/skills/skill-creator.md)

**📖 [查看所有 Skills 详细指南](readmes/skills/README.md)**

## Commands 库

> **注**：Cadence 包含 15 个核心 Commands（下文列出）和 5 个从 [superpowers](https://github.com/obra/superpowers) 继承的 Commands（/tdd, /verify, /request-review, /receive-review, /finish）。

### 节点 Commands（7个）

- `/brainstorm` - 启动需求探索
- `/analyze` - 启动存量分析
- `/requirement` - 启动需求分析
- `/design` - 启动技术设计
- `/design-review` - 启动设计审查
- `/plan` - 启动实现计划
- `/develop` - 启动代码实现

**📖 [查看所有 Commands 详细指南](readmes/commands/README.md)**

### 流程 Commands（6个）

- `/worktree` - 创建 Git Worktree 隔离环境
- `/status` - 查看当前进度 [📖 详细指南](readmes/skills/status.md)
- `/resume` - 恢复之前的进度 [📖 详细指南](readmes/skills/resume.md)
- `/checkpoint` - 创建检查点 [📖 详细指南](readmes/skills/checkpoint.md)
- `/report` - 生成进度报告 [📖 详细指南](readmes/skills/report.md)
- `/monitor` - 状态快照（非实时）[📖 详细指南](readmes/skills/monitor.md)

**📖 [查看所有 Commands 详细指南](readmes/skills/README.md)**

### 元 Commands（3个）

- `/pre-check` - 前置条件检查，确保环境正确配置
- `/cad-load` - 加载项目上下文（支持 quick/standard/full 三种模式）
- `/skill-create` - 创建和优化 Skills（创建模板、打包、触发率优化）

**📖 [查看所有 Commands 详细指南](readmes/commands/README.md)**

## 最佳实践

### 1. 选择正确的流程模式

- **复杂功能** → 使用完整流程（Full Flow）
- **简单功能** → 使用快速流程（Quick Flow）
- **技术调研** → 使用探索流程（Exploration Flow）

### 2. 充分利用断点续传

- 每个节点完成后会自动创建检查点
- 使用 `/resume` 恢复之前的进度
- 使用 `/status` 查看当前进度

### 3. 保持 TDD 实践

- Subagent Development 强制执行 TDD
- 测试覆盖率 ≥ 80%
- 两阶段审查确保质量

### 4. 利用 Serena MCP 进行存量分析

- 使用 `analyze` Skill 分析现有代码库
- 识别可复用的组件和模式
- 避免重复造轮子

### 5. 合理使用 Git Worktrees

- 每个功能开发在独立的 Worktree 中
- 避免主分支污染
- 方便并行开发

## 技术亮点

### 1. 完整的开发流程

- 8 个核心节点覆盖完整开发生命周期
- 3 种流程模式适应不同场景
- 支持断点续传和会话恢复

### 2. 智能进度追踪

- 使用 Serena memory 实现跨会话持久化
- 自动创建检查点
- 实时监控和报告生成

### 3. 两阶段审查机制

- **Spec Reviewer**: 验证规范符合性（4 个维度）
- **Code Quality Reviewer**: 验证代码质量（5 个维度）
- **TDD 强制执行**: 测试覆盖率 ≥ 80%

### 4. 灵活的流程模式

- **完整流程**: 确保质量和可追溯性
- **快速流程**: 提高小功能开发效率
- **探索流程**: 支持技术调研和 POC

### 5. 智能项目初始化

- 自动检测项目类型和技术栈
- 跨平台兼容（macOS/Linux/Windows）
- 用户确认机制确保准确性

## 哲学

- **测试驱动开发** - 始终先写测试
- **系统化优于临时** - 流程优于猜测
- **降低复杂度** - 简单性是首要目标
- **证据优于声明** - 在声明成功前验证

## Skill Creator（生成可直接调用的 Skills）

仓库提供了元技能 [`skills/skill-creator/SKILL.md`](skills/skill-creator/SKILL.md)，用于在本仓库中持续创建和维护可直接调用的 Skills。

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
3. 遵循 `skills/skill-creator/SKILL.md` 创建和测试新 Skills
4. 提交 PR

## 更新

### 市场安装更新

```bash
/plugin update cadence-init
/plugin update cadence-workflow
```

### 离线安装更新

拉取最新代码后重新运行安装脚本：

```bash
git pull
./install-offline.sh  # 或 install-offline.bat
```

## 版本历史

### v2.4 MVP（2026-03-02）

**已完成功能**：
- ✅ 8 个核心节点 Skills
- ✅ 3 个流程 Skills
- ✅ 3 个元 Skills（using-cadence, cad-load, pre-check）
- ✅ 15 个 Commands
- ✅ 3 个 Subagent Prompts
- ✅ 智能进度追踪系统
- ✅ 两阶段审查机制

**统计数据**：
- 20 个 Skills（15 个 Cadence 核心 + 5 个 superpowers 继承）
- 20 个 Commands（15 个 Cadence 核心 + 5 个 superpowers 继承）
- 3 个 Subagent Prompts
- 约 50 个文件，约 150KB 代码

**Cadence 核心 Skills（15个）**：
- 8 个核心节点：brainstorming, analyze, requirement, design, design-review, plan, using-git-worktrees, subagent-development
- 3 个流程：full-flow, quick-flow, exploration-flow
- 3 个元 Skills：using-cadence, cad-load, pre-check

**从 superpowers 继承（5个）**：
- test-driven-development, verification-before-completion, requesting-code-review, receiving-code-review, finishing-a-development-branch

**详细发布说明**：[RELEASE-NOTES.md](RELEASE-NOTES.md)

## 许可证

MIT License - 详见 LICENSE 文件

## 支持

- **问题反馈**: https://github.com/michaelChe956/Cadence-skills/issues
- **市场**: https://github.com/michaelChe956/Cadence-skills-marketplace

## 致谢

本项目受到 [Superpowers](https://github.com/obra/superpowers) 的启发，感谢 Jesse Vincent 创建了优秀的 Skills 系统。
