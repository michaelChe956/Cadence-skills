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

3. **serena** - serena 项目目录确认（我只是单纯需要这个项目的源码，不需要验证 serena 是否可以正常使用）
   - 询问用户选择配置方式
   - 验证 `pyproject.toml` 文件
   - 提供三种配置选项：
     - 自动下载到默认目录（~/.cadence/serena/）
     - 指定下载目录
     - 使用已有的 serena 项目

4. **playwright-cli** - Playwright CLI with SKILLS
   - 检查是否全局安装 @playwright/cli
   - 自动安装缺失的 playwright-cli
   - 自动安装 Playwright skills

5. **ast-grep** - 代码结构化大纲工具
   - 检查是否全局安装 @ast-grep/cli
   - 自动安装缺失的 ast-grep
   - 用于 `ast-grep outline` 代码阅读规则

6. **API Key 配置提醒（可选）** - 智普/MiniMax MCP 密钥
   - 询问用户是否需要智普 AI MCP（视觉理解/联网搜索/网页读取/开源仓库）
   - 询问用户是否需要 MiniMax Token Plan MCP（网络搜索/图片理解）
   - 提醒用户自行获取 API Key，不验证密钥有效性
   - 安全提醒：不要将 API Key 直接告诉 Claude Code

## serena github地址
- https://github.com/oraios/serena.git

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
检查 npx → 检查 uvx → 检查 serena → 用户选择 → 验证配置 → 检查 playwright-cli → 检查 ast-grep → API Key 提醒（可选） → 完成
```

**重要**：前五个步骤（npx、uvx、serena、playwright-cli、ast-grep）必须完成，不允许跳过。第六步 API Key 提醒为可选。

## 输出

- ✅ 工具检查报告（已安装/已自动安装）
- ✅ serena 项目路径配置
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
- 必须完成所有五个基础步骤（npx、uvx、serena、playwright-cli、ast-grep）
- serena 配置必须询问用户选择，提供三个选项
- 验证失败必须重新选择，不能跳过
- 必须验证配置成功后才能继续
- playwright-cli 安装失败必须提供手动安装命令
- ast-grep 安装失败必须提供手动安装命令 `npm i @ast-grep/cli -g`
- API Key 配置提醒为可选步骤，不验证密钥有效性
- 安全提醒：不要将 API Key 直接告诉 Claude Code
