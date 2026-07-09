# /pre-check - 前置条件检查

调用 `pre-check` skill 自动检查和配置项目所需的工具、OpenSpec 指令文件和 Superpowers Skills。默认不需要人工交互即可完成初始化。

## 使用场景

- 首次使用 Cadence 前，确保环境正确配置
- 已初始化项目升级新版 Cadence 后，增量补齐新增工具（如 codegraph、OpenSpec、Superpowers）
- 网络受限环境中，识别用户手动复制的 Superpowers 离线安装目录并完成本地软链同步

## 人工交互策略

默认不向用户提问。只有出现以下情况才进入人工交互：

| 触发条件 | 处理方式 |
|----------|----------|
| 在线安装失败且存在离线安装路径选择 | 询问用户是否已准备离线目录；无法等待时报告离线复制路径并继续其他检查 |
| Superpowers 目标目录存在同名非软链 | 不覆盖；如用户明确要求替换，再询问并执行 |
| 用户明确要求安装 Playwright | 检查并安装；安装失败时提供手动命令 |
| 需要真实 API Key、Token 或私密信息 | 不询问真实密钥，只提醒后续替换占位符 |

提问规则：
- 每次只问一个问题。
- 问题必须给出推荐默认选项。
- 如果运行环境支持自动超时，超时后采用推荐默认值。
- 如果无法等待用户输入，采用保守默认：不覆盖、不删除、不收集真实密钥、不启用 Playwright。

## 功能

自动检查以下工具和资源：

1. **npx** - Node.js 包执行器
   - 检查是否安装
   - 自动安装缺失的 npx

2. **uvx** - Python 包执行器
   - 检查是否安装
   - 自动安装缺失的 uvx

3. **ast-grep** - 代码结构化大纲工具
   - 检查是否全局安装 @ast-grep/cli
   - 自动安装缺失的 ast-grep
   - 用于 `ast-grep outline` 代码阅读规则

4. **codegraph** - 代码图谱与大范围代码检索工具
   - 检查是否全局安装 @colbymchenry/codegraph
   - 自动安装缺失的 codegraph
   - 用于 CodeGraph MCP、项目级代码图初始化和大范围检索

5. **OpenSpec** - spec-driven development 指令系统
   - 检查是否全局安装 @fission-ai/openspec
   - 自动安装缺失的 openspec CLI
   - 首次项目执行 `openspec init --tools claude,codex`
   - 已初始化项目执行 `openspec update`，增量补齐 Claude Code / Codex 指令文件

6. **Superpowers** - 通用 agent skills
   - 检查 `~/.agents/superpowers/skills`
   - 支持在线 clone/update `https://github.com/obra/superpowers`
   - 支持用户手动复制到 `~/.agents/superpowers` 的离线安装
   - 同步到 `~/.agents/skills` 统一目录
   - 从统一目录软链到 `~/.codex/skills/skills` 和 `~/.claude/skills`

7. **playwright-cli（可选，默认跳过）** - Playwright CLI with SKILLS
   - 仅在用户明确要求浏览器自动化能力时检查和安装
   - 默认不安装 playwright-cli，不安装 Playwright skills

8. **API Key 配置提醒（默认占位）** - 智普/MiniMax MCP 密钥
   - 默认不询问、不收集真实密钥
   - `mcp-configuration` 默认写入 `your_zhipu_api_key` 与 `your_minimax_api_key` 占位符
   - 提醒用户后续自行获取并替换 API Key
   - 安全提醒：不要将 API Key 直接告诉 Claude Code

## playwright-cli 安装

> 默认不执行。仅在用户明确要求浏览器自动化、截图、表单填写、端到端测试能力时执行。

### 检查命令

```bash
# 检查 playwright-cli 是否已安装
which playwright-cli || npm list -g @playwright/cli
```

### 安装命令

```bash
# 全局安装 Playwright CLI
npm install -g @playwright/cli@latest

# 安装 Playwright Skills（供 Claude Code 等 coding agents 使用）
playwright-cli install --skills
```

### 验证安装

```bash
# 验证 playwright-cli 安装成功
playwright-cli --help

# 验证 skills 安装成功（检查全局 skills 目录）
ls ~/.claude/skills/playwright-cli 2>/dev/null || echo "Skills not found"
```

### 说明

- **用途**：浏览器自动化测试、表单填写、截图、数据提取
- **特点**：Token-efficient，不会强制将页面数据加载到 LLM
- **Skills**：安装后 Claude Code 可自动识别并使用 Playwright skills
- **默认行为**：不安装、不启用；需要时由用户显式要求

## ast-grep 安装

### 检查命令

```bash
# 检查 ast-grep 是否已安装
ast-grep --version
```

### 安装命令

```bash
# 全局安装 ast-grep CLI
npm i @ast-grep/cli -g
```

### 验证安装

```bash
# 验证 ast-grep 安装成功
ast-grep --version
```

### 说明

- **用途**：生成代码结构化大纲，辅助代码阅读与符号定位
- **典型用法**：`ast-grep outline src/parser.ts`、`ast-grep outline src --items imports`
- **与 rule-config 的关系**：`rule-config` 会为 Coding 项目配置 `code-reading.md` 规则，要求优先使用 `ast-grep outline`

## CodeGraph 安装

### 检查命令

```bash
# 检查 codegraph 是否已安装
codegraph version
```

### 安装命令

```bash
# 全局安装 CodeGraph CLI
npm i -g @colbymchenry/codegraph
```

### 验证安装

```bash
# 验证 codegraph 安装成功
codegraph version
```

### 说明

- **用途**：生成项目代码图，支持大范围代码检索、架构理解、调用链分析和影响面分析
- **典型初始化**：`rule-config` 会在项目内执行 `codegraph install --target=claude,codex --location=local --yes` 与 `codegraph init`
- **增量行为**：老项目重新运行 `/pre-check` 时，已安装工具会跳过，只会补装缺失的 codegraph

## OpenSpec 安装与初始化

### 检查命令

```bash
# 检查 OpenSpec CLI 是否已安装
openspec --version
```

### 安装命令

```bash
# 全局安装 OpenSpec CLI
npm install -g @fission-ai/openspec@latest
```

### 初始化与更新命令

```bash
# 当前项目尚未初始化 OpenSpec 时
openspec init --tools claude,codex

# 当前项目已存在 openspec/config.yaml 时
openspec update
```

### 验证安装

```bash
# 验证 CLI
openspec --version

# 验证项目配置和指令文件
test -f openspec/config.yaml
test -f .codex/skills/openspec-propose/SKILL.md
test -f .claude/commands/opsx/propose.md -o -f .claude/skills/openspec-propose/SKILL.md
```

### 说明

- **用途**：为 Claude Code 和 Codex 提供 OpenSpec change proposal、design、tasks、apply、archive 等流程支持
- **Codex 目录**：`.codex/skills/openspec-*`
- **Claude Code 目录**：`.claude/commands/opsx/`、`.claude/skills/openspec-*`
- **增量行为**：已存在 `openspec/config.yaml` 时不重新初始化，只执行 `openspec update` 补齐或刷新指令文件

## Superpowers 安装与同步

### 目录结构

| 用途 | 路径 |
|------|------|
| Superpowers 源目录 | `~/.agents/superpowers` |
| 统一 Skills 目录 | `~/.agents/skills` |
| Codex 目标目录 | `~/.codex/skills/skills` |
| Claude Code 目标目录 | `~/.claude/skills` |

> **注意**：Claude Code 和 Codex 的软链目标目录结构不同。Codex 使用 `~/.codex/skills/skills`，Claude Code 使用 `~/.claude/skills`。

### 在线安装命令

```bash
# 首次在线安装
git clone https://github.com/obra/superpowers "$HOME/.agents/superpowers"
```

### 离线安装方式

如果网络无法访问 GitHub，用户可以自行下载或复制 Superpowers 到：

```bash
$HOME/.agents/superpowers
```

只要存在以下目录，`/pre-check` 就将其识别为有效离线安装：

```bash
$HOME/.agents/superpowers/skills
```

### 更新与同步规则

1. 如果 `~/.agents/superpowers/.git` 存在：
   - 执行 `git fetch --all`
   - 有上游分支时执行 `git pull --ff-only`
   - 无上游分支时跳过 pull 并警告

2. 如果 `~/.agents/superpowers/.git` 不存在但 `~/.agents/superpowers/skills` 存在：
   - 视为离线安装
   - 跳过 Git 更新
   - 继续执行软链同步

3. 如果 `~/.agents/superpowers/skills` 不存在：
   - 优先尝试在线 clone
   - clone 失败时提示用户离线复制 Superpowers 到 `~/.agents/superpowers`

4. 软链同步必须按三层执行：
   - `~/.agents/superpowers/skills/*` → `~/.agents/skills/*`
   - `~/.agents/skills/*` → `~/.codex/skills/skills/*`
   - `~/.agents/skills/*` → `~/.claude/skills/*`

5. 增量处理规则：
   - 已存在正确软链：跳过
   - 已存在旧软链但指向不同 Superpowers 来源：更新软链
   - 已存在同名非软链文件或目录：跳过并警告，不覆盖
   - 清理失效软链时，只清理指向 Superpowers 来源或统一目录中 Superpowers 条目的失效链接

### 验证同步

```bash
test -d "$HOME/.agents/superpowers/skills"
test -d "$HOME/.agents/skills"
test -d "$HOME/.codex/skills/skills"
test -d "$HOME/.claude/skills"
```

## 检查流程

```dot
检查 npx → 检查 uvx → 检查 ast-grep → 检查 codegraph → 检查 OpenSpec → 同步 Superpowers → 默认跳过 Playwright → 默认展示 API Key 占位提醒 → 完成
```

**重要**：前六个步骤（npx、uvx、ast-grep、codegraph、OpenSpec、Superpowers）必须完成，不允许跳过。Playwright 默认跳过，仅用户明确要求时执行；API Key 提醒默认执行但不收集真实密钥。

## 增量运行

`/pre-check` 支持重复执行，具有幂等性：

- 已安装的工具会跳过安装，仅报告状态。
- 缺失或未成功安装的工具会自动重新安装。
- 不会默认安装 Playwright。
- 不会重复安装已存在的 codegraph。
- 不会重复初始化已存在的 OpenSpec 项目；只执行 `openspec update` 补齐指令文件。
- 不会覆盖已有的 OpenSpec skills、commands 或用户改动。
- 不会覆盖 Superpowers 目标目录中的同名非软链文件或目录。
- 会补齐缺失的 `~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills` 软链。

适用场景：
- 新版 Cadence 新增工具（如 `ast-grep`、`codegraph`、OpenSpec、Superpowers）后，老项目重新运行即可补齐。
- 之前某一步安装失败后环境问题已修复，重新运行会再次尝试。
- 用户先离线复制 Superpowers，再重新运行 `/pre-check` 完成软链同步。

## 输出

- ✅ 工具检查报告（已安装/已自动安装/默认跳过/默认占位）
- ✅ OpenSpec 初始化或更新报告
- ✅ Superpowers 在线更新、离线识别和软链同步报告
- ✅ 环境验证成功确认

## 下一步

环境检查完成后，可以执行项目初始化命令：

```bash
/init # 初始化项目
/cadence:init:project-analysis  # 分析项目结构
/cadence:init:project-rules     # 配置项目规则
/cadence:init:mcp-configuration # 配置 MCP
```

OpenSpec 可通过以下命令继续使用：

```bash
/opsx:propose
/opsx:apply
/opsx:archive
```

## 相关命令

- `/init` - 初始化项目
- `/cadence:init:project-analysis` - 分析项目结构、技术栈和依赖
- `/cadence:init:project-rules` - 创建项目个性化规则模板
- `/cadence:init:mcp-configuration` - 配置 MCP
- `/opsx:propose` - 创建 OpenSpec change proposal
- `/opsx:apply` - 实施 OpenSpec change
- `/opsx:archive` - 归档完成的 OpenSpec change
- `/cad-load` - 加载项目上下文

## 强制规则

- 所有与用户的交互必须使用中文。
- 必须完成所有六个基础步骤（npx、uvx、ast-grep、codegraph、OpenSpec、Superpowers）。
- playwright-cli 默认跳过；仅用户明确要求时安装，安装失败必须提供手动安装命令。
- ast-grep 安装失败必须提供手动安装命令 `npm i @ast-grep/cli -g`。
- codegraph 安装失败必须提供手动安装命令 `npm i -g @colbymchenry/codegraph`。
- OpenSpec 安装失败必须提供手动安装命令 `npm install -g @fission-ai/openspec@latest`。
- OpenSpec 已初始化项目必须执行增量更新，不得重新初始化覆盖。
- Superpowers 必须支持在线更新和离线安装两种路径。
- Superpowers 同名非软链冲突必须跳过，不得覆盖用户文件。
- Codex 与 Claude Code 的 Superpowers 软链目录必须区分：`~/.codex/skills/skills` 与 `~/.claude/skills`。
- API Key 配置提醒默认执行，占位符由 `mcp-configuration` 写入，不验证密钥有效性。
- 安全提醒：不要将 API Key 直接告诉 Claude Code。
