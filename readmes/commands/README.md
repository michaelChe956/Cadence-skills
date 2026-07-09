# Cadence Commands 使用指南

本目录包含所有 Cadence Commands 的详细使用文档。

## Commands 分类

### 节点 Commands（7个）

需求阶段：
- [brainstorm](brainstorm.md) - 启动需求探索
- [analyze](analyze.md) - 启动存量分析
- [requirement](requirement.md) - 启动需求分析

设计阶段：
- [design](design.md) - 启动技术设计
- [design-review](design-review.md) - 启动设计审查
- [plan](plan.md) - 启动实现计划

开发阶段：
- [develop](develop.md) - 启动代码实现

### 流程 Commands（6个）

- [worktree](worktree.md) - 创建 Git Worktree 隔离环境
- [status](status.md) - 查看当前进度
- [resume](resume.md) - 恢复之前的进度
- [checkpoint](checkpoint.md) - 创建检查点
- [report](report.md) - 生成进度报告
- [monitor](monitor.md) - 实时监控进度

### 元能力（2个）

- [cad-load](cad-load.md) - 加载项目上下文（cadence-workflow Command）
- [skill-creator](../skills/skill-creator.md) - 创建和优化 skills（cadence-init Skill，输入 `/skill-creator` 触发）

> **说明**：`skill-creator` 由 `cadence-init` 插件以 Skill 形式提供，已不再是 Command。

## 快速导航

### 我要开始开发

1. **复杂功能**（>2小时）→ `/brainstorm` 或 `/full-flow`
2. **简单功能**（<2小时）→ `/requirement` 或 `/quick-flow`
3. **技术调研** → `/brainstorm` 或 `/exploration-flow`

### 我要管理进度

- 查看进度 → `/status`
- 恢复进度 → `/resume`
- 创建检查点 → `/checkpoint`
- 生成报告 → `/report`
- 实时监控 → `/monitor`

### 我要单独运行某个节点

- 需求探索 → `/brainstorm`
- 存量分析 → `/analyze`
- 需求分析 → `/requirement`
- 技术设计 → `/design`
- 设计审查 → `/design-review`
- 实现计划 → `/plan`
- 环境隔离 → `/worktree`
- 代码实现 → `/develop`

## 常用命令组合

### 组合 1：新项目开始

```bash
# 项目初始化（首次使用时，均为 cadence-init 插件的 Skill）
/pre-check               # 前置条件检查
/init                    # 项目初始化（Claude Code 内建）
/project-analysis        # 项目分析
/rule-config             # 项目规则配置
/mcp-configuration       # MCP 配置
/project-rules-examples  # 项目个性化规则（可选）

# 开始开发
/cad-load           # 加载项目上下文
/full-flow          # 开始完整流程
```

> **说明**：`pre-check`、`project-analysis`、`rule-config`、`mcp-configuration`、`project-rules-examples` 均由 `cadence-init` 插件以 Skill 形式提供，直接输入 `/名称` 触发。

### 组合 2：快速开发

```bash
/cad-load           # 加载项目上下文
/quick-flow         # 开始快速流程
```

### 组合 3：恢复进度

```bash
/cad-load           # 加载项目上下文
/status             # 查看进度
/resume             # 恢复进度
```

### 组合 4：单独运行节点

```bash
/cad-load           # 加载项目上下文
/brainstorm         # 需求探索
# 完成后
/design             # 技术设计
# 完成后
/plan               # 实现计划
# 完成后
/develop            # 代码实现
```

### 组合 5：进度管理

```bash
/status             # 查看进度
/checkpoint         # 创建检查点
/report             # 生成报告
```

## Commands 与 Skills 的关系

cadence-workflow 的每个 Command 对应一个 Skill（cadence-init 已全部改为纯 Skill，无对应 Command）：

| Command | Skill | 说明 |
|---------|-------|------|
| `/brainstorm` | brainstorming | 需求探索 |
| `/analyze` | analyze | 存量分析 |
| `/requirement` | requirement | 需求分析 |
| `/design` | design | 技术设计 |
| `/design-review` | design-review | 设计审查 |
| `/plan` | plan | 实现计划 |
| `/worktree` | using-git-worktrees | 环境隔离 |
| `/develop` | subagent-development | 代码实现 |
| `/status` | full-flow/quick-flow/exploration-flow | 查看进度 |
| `/resume` | full-flow/quick-flow/exploration-flow | 恢复进度 |
| `/checkpoint` | full-flow/quick-flow/exploration-flow | 创建检查点 |
| `/report` | full-flow/quick-flow/exploration-flow | 生成报告 |
| `/monitor` | full-flow/quick-flow/exploration-flow | 实时监控 |
| `/cad-load` | cad-load | 加载上下文 |
| `/skill-creator` | skill-creator | 创建与优化 skills（cadence-init Skill，无 Command） |

## 快速参考

### 流程命令

```bash
# 完整流程（8节点）
/full-flow

# 快速流程（4节点）
/quick-flow

# 探索流程（4节点+迭代）
/exploration-flow
```

### 单节点命令

```bash
/brainstorm        # 需求探索
/analyze           # 存量分析
/requirement       # 需求分析
/design            # 技术设计
/design-review     # 设计审查
/plan              # 实现计划
/worktree          # 环境隔离
/develop           # 代码实现
```

### 进度管理命令

```bash
/status            # 查看进度
/resume            # 恢复进度
/checkpoint        # 创建检查点
/report            # 生成报告
/monitor           # 实时监控
```

### 上下文命令

```bash
/cad-load          # 快速加载
/cad-load standard # 标准加载（推荐）
/cad-load full     # 完整加载
```

## 最佳实践

### 1. 先加载上下文

任何操作前先使用 `/cad-load` 加载项目上下文。

### 2. 选择正确的流程

根据任务复杂度选择合适的流程命令。

### 3. 定期检查进度

使用 `/status` 定期检查进度，使用 `/checkpoint` 创建检查点。

### 4. 充分利用断点续传

使用 `/resume` 恢复之前的进度，避免重复工作。

### 5. 生成报告

使用 `/report` 生成进度报告，便于团队协作。

## 相关资源

- [Skills 使用指南](../skills/)
- [项目 README](../../README.md)
- [版本发布说明](../../RELEASE-NOTES.md)

## 获取帮助

- **问题反馈**: https://github.com/michaelChe956/Cadence-skills/issues
- **文档问题**: 提交 Issue 或 PR
