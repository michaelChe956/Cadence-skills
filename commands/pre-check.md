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

## 检查流程

```dot
检查 npx → 检查 uvx → 检查 serena → 用户选择 → 验证配置 → 检查 playwright-cli → 完成
```

**重要**：所有四个步骤都必须完成，不允许跳过任何步骤。

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
- 必须完成所有四个步骤（npx、uvx、serena、playwright-cli）
- serena 配置必须询问用户选择，提供三个选项
- 验证失败必须重新选择，不能跳过
- 必须验证配置成功后才能继续
- playwright-cli 安装失败必须提供手动安装命令
