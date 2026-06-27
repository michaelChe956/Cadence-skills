# /pre-check - 前置条件检查

调用 `pre-check` skill 自动检查和配置项目所需的工具和依赖项。

## 使用场景

- 首次使用 Cadence 前，确保环境正确配置

## 功能

自动检查以下工具：

1. **npx** - Node.js 包执行器
   - 检查是否安装
   - 自动安装缺失的 npx

2. **uvx** - Python 包执行器
   - 检查是否安装
   - 自动安装缺失的 uvx

3. **playwright-cli** - Playwright CLI with SKILLS
   - 检查是否全局安装 @playwright/cli
   - 自动安装缺失的 playwright-cli
   - 自动安装 Playwright skills

4. **ast-grep** - 代码结构化大纲工具
   - 检查是否全局安装 @ast-grep/cli
   - 自动安装缺失的 ast-grep
   - 用于 `ast-grep outline` 代码阅读规则

5. **API Key 配置提醒（可选）** - 智普/MiniMax MCP 密钥
   - 询问用户是否需要智普 AI MCP（视觉理解/联网搜索/网页读取/开源仓库）
   - 询问用户是否需要 MiniMax Token Plan MCP（网络搜索/图片理解）
   - 提醒用户自行获取 API Key，不验证密钥有效性
   - 安全提醒：不要将 API Key 直接告诉 Claude Code

## playwright-cli 安装

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

## 检查流程

```dot
检查 npx → 检查 uvx → 检查 playwright-cli → 检查 ast-grep → API Key 提醒（可选） → 完成
```

**重要**：前四个步骤（npx、uvx、playwright-cli、ast-grep）必须完成，不允许跳过。第五步 API Key 提醒为可选。

## 增量运行

`/pre-check` 支持重复执行，具有幂等性：

- 已安装的工具会跳过安装，仅报告状态。
- 缺失或未成功安装的工具会自动重新安装。
- 不会重复安装已存在的 Playwright skills。

适用场景：
- 新版 Cadence 新增工具（如 `ast-grep`）后，老项目重新运行即可补齐。
- 之前某一步安装失败后环境问题已修复，重新运行会再次尝试。

## 输出

- ✅ 工具检查报告（已安装/已自动安装）
- ✅ 环境验证成功确认

## 下一步

环境检查完成后，可以执行项目初始化命令：

```bash
/init # 初始化项目
/cadence:init:project-analysis  # 分析项目结构
/cadence:init:project-rules     # 配置项目规则
/cadence:init:mcp-configuration # 配置 MCP
```

## 相关命令

- `/init` - 初始化项目
- `/cadence:init:project-analysis` - 分析项目结构、技术栈和依赖
- `/cadence:init:project-rules` - 创建项目个性化规则模板
- `/cadence:init:mcp-configuration` - 配置 MCP
- `/cad-load` - 加载项目上下文

## 强制规则

- 所有与用户的交互必须使用中文
- 必须完成所有四个基础步骤（npx、uvx、playwright-cli、ast-grep）
- playwright-cli 安装失败必须提供手动安装命令
- ast-grep 安装失败必须提供手动安装命令 `npm i @ast-grep/cli -g`
- API Key 配置提醒为可选步骤，不验证密钥有效性
- 安全提醒：不要将 API Key 直接告诉 Claude Code
