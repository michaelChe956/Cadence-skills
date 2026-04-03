---
name: project-analysis
description: "分析项目结构、技术栈和依赖，生成项目初始化分析摘要文档"
---

# 项目分析

## 概述

分析项目结构、依赖、Git 历史，生成项目初始化分析摘要文档。

## 检查清单

你必须为以下每个项目创建任务并按顺序完成：

1. **收集项目信息** — 统计文件/目录数量，识别主要编程语言
2. **分析目录结构** — 获取主要目录结构
3. **分析依赖关系** — 读取 package.json、requirements.txt 等
4. **分析 Git 历史** — 获取最近提交和统计信息
5. **检测项目类型** — 识别前端/后端/全栈/其他，需要用户确认
6. **生成分析报告** — 创建项目初始化分析摘要文档

**下一步**：将分析结果传递给 @rule-config skill 进行规则配置

## 处理流程

### 1. 收集项目信息

**执行命令**：

```bash
# 统计文件和目录数量
find . -type f -not -path '*/\.*' | wc -l  # 文件数
find . -type d -not -path '*/\.*' | wc -l  # 目录数

# 识别主要编程语言
find . -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.java" | head -20

# 检测项目类型标识文件
ls -la | grep -E "package.json|requirements.txt|pom.xml|go.mod|Cargo.toml|pyproject.toml"
```

### 2. 分析目录结构

**执行命令**：

```bash
# 获取主要目录
find . -maxdepth 2 -type d -not -path '*/\.*' | head -20
```

### 3. 分析依赖关系

**读取配置文件**：

- 前端项目：`package.json`
- Python 项目：`requirements.txt`、`pyproject.toml`
- Java 项目：`pom.xml`、`build.gradle`
- Go 项目：`go.mod`
- Rust 项目：`Cargo.toml`

**提取关键信息**：
- 项目名称
- 版本号
- 主要依赖
- 脚本命令（test、lint、build 等）

### 4. 分析 Git 历史

**执行命令**：

```bash
# 最近 10 条提交
git log --oneline -10

# 提交统计
git log --oneline --since="30 days ago" | wc -l
```

**注意**：如果项目不是 Git 仓库，跳过此步骤

### 5. 检测项目类型

**检测规则**：

| 项目类型 | 检测条件 |
|----------|----------|
| 前端 | 存在 `package.json` + 前端框架配置（如 `vite.config.js`、`next.config.js`、`vue.config.js`） |
| 后端 | 存在后端语言文件 + 框架（如 `requirements.txt` + FastAPI/Django，`go.mod` + Gin） |
| 全栈 | 同时包含前端和后端特征 |
| 其他 | 文档、配置或工具项目 |

**检测命令**：

```bash
# 检测前端特征
ls -la | grep -E "package.json"
ls -la | grep -E "vite.config|next.config|vue.config|astro.config"

# 检测后端特征
ls -la | grep -E "requirements.txt|pom.xml|go.mod|Cargo.toml|pyproject.toml"
```

**用户确认**：
- 检测到项目类型后，必须展示给用户确认
- 如果检测不准确，允许用户手动指定
- 使用参数 `--project-type` 可以手动指定项目类型

### 6. 生成分析报告

**文件路径**：`.claude/analysis-docs/YYYY-MM-DD_分析报告_项目初始化摘要_v1.0.md`

**文件内容模板**：

```markdown
# 项目初始化分析摘要

**生成时间**：[当前时间]
**项目路径**：[项目路径]

## 1. 项目基本信息

- **项目类型**：[前端/后端/全栈/其他]
- **主要语言**：[语言列表]
- **项目规模**：
  - 文件总数：[数量]
  - 目录总数：[数量]
  - 估算代码行数：[数量]

## 2. 目录结构

```
[主要目录树]
```

**目录说明**：
- `src/`：[说明]
- `tests/`：[说明]

## 3. 依赖关系

**主要依赖**：
- [依赖名称]：[版本]

## 4. 主要模块

- **模块 1**：[说明]
- **模块 2**：[说明]

## 5. Git 历史

**最近提交**：
```
[最近 10 条提交]
```

**提交统计**：
- 最近 30 天提交数：[数量]

## 6. 下一步建议

[基于分析的建议]
```

**错误处理**：
- 如果不是 Git 仓库，跳过 Git 历史分析
- 如果文件过多（>10000），显示进度提示
- 超时限制：30 秒

## 核心原则

- **信息完整** — 收集项目尽可能多的信息
- **结构清晰** — 分析报告结构清晰易读
- **可操作性** — 提供有意义的下一步建议
- **用户确认** — 项目类型检测必须经过用户确认
