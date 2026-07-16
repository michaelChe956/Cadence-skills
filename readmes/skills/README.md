# Cadence Skills 使用指南

本目录包含所有 Cadence Skills 的详细使用文档。

## Skills 分类

### 核心节点 Skills（8个）

需求阶段：
- [brainstorming](brainstorming.md) - 需求探索，通过苏格拉底式对话明确需求
- [analyze](analyze.md) - 存量分析，使用 Serena MCP 分析现有代码库
- [requirement](requirement.md) - 需求分析，输出结构化需求文档

设计阶段：
- [design](design.md) - 技术设计，输出详细技术方案
- [design-review](design-review.md) - 设计审查，验证设计质量
- [plan](plan.md) - 实现计划，分解为具体任务

开发阶段：
- [using-git-worktrees](using-git-worktrees.md) - 创建隔离环境
- [subagent-development](subagent-development.md) - 代码实现 + 单元测试

### 流程 Skills（3个）

- [full-flow](full-flow.md) - 完整流程（8 个节点）
- [quick-flow](quick-flow.md) - 快速流程（4 个节点）
- [exploration-flow](exploration-flow.md) - 探索流程（4 个节点 + 迭代）

### 元 Skills（4个）

- [using-cadence](using-cadence.md) - Cadence Skills 系统使用指南
- [cadencing](cadencing.md) - 项目初始化，配置环境、规则、文档结构和技术栈
- [cad-load](cad-load.md) - 项目上下文加载
- [skill-creator](skill-creator.md) - 创建、校验、打包并优化 Claude Code skills

### KnowledgeBase Skills（7个）

- `knowledge-base-bootstrap` - 校验用户输入并初始化 Schema 3.0 KnowledgeBase
- `knowledge-base-base-info` - 生成工程、数据、中间件和开发方式信息
- `knowledge-base-api` - 分析对外能力和工程内对内能力
- `knowledge-base-pages` - 分析页面、路由、权限和 REST API 关联
- `knowledge-base-overview` - 生成知识库入口、导航和项目使用规则
- `knowledge-base-update` - 根据 Git 与增量资料更新 KnowledgeBase
- [knowledge-base-context](knowledge-base-context.md) - 从任务出发，同时读取 KnowledgeBase 与当前实现并生成最小上下文

## 快速导航

### 我是新手

1. 先阅读 [using-cadence](using-cadence.md) 了解如何使用 Cadence
2. 使用 [cadencing](cadencing.md) 初始化你的项目
3. 选择合适的流程模式开始开发

### 我要开发功能

- **复杂功能**（>2小时）→ [full-flow](full-flow.md)
- **简单功能**（<2小时）→ [quick-flow](quick-flow.md)
- **技术调研** → [exploration-flow](exploration-flow.md)
- **创建/维护技能** → [skill-creator](skill-creator.md)

### 我要使用现有项目知识

- **首次建立 KnowledgeBase** → `knowledge-base-bootstrap`
- **需求、设计、计划、编码、测试、评审或调试前获取上下文** → [knowledge-base-context](knowledge-base-context.md)
- **项目事实发生变化后更新 KnowledgeBase** → `knowledge-base-update`

### 我要单独使用某个节点

- 需求探索 → [brainstorming](brainstorming.md)
- 存量分析 → [analyze](analyze.md)
- 需求分析 → [requirement](requirement.md)
- 技术设计 → [design](design.md)
- 设计审查 → [design-review](design-review.md)
- 实现计划 → [plan](plan.md)
- 环境隔离 → [using-git-worktrees](using-git-worktrees.md)
- 代码实现 → [subagent-development](subagent-development.md)

## 流程模式对比

| 流程模式 | 节点数 | 适用场景 | 预估时间 | 关键特性 |
|---------|--------|---------|---------|---------|
| **Full Flow** | 8 | 复杂功能、企业级项目 | 1-2 天 | 完整流程、人工确认、两阶段审查 |
| **Quick Flow** | 4 | 简单功能、Bug 修复 | 1-2 小时 | 快速开发、保持 TDD |
| **Exploration Flow** | 4+ | 技术调研、POC | 2-4 小时 | 允许迭代、4 种结束方式 |

## 常见使用场景

### 场景 1：新项目开发

```
1. /pre-check          # 前置条件检查
2. /init               # 项目初始化
3. /project-analysis   # 项目分析
4. /rule-config        # 项目规则配置
5. /mcp-configuration  # MCP 配置
6. /project-rules-examples  # 项目个性化规则（可选）
7. /cad-load               # 加载项目上下文
8. /full-flow          # 使用完整流程
9. 依次完成 8 个节点
10. /status             # 查看进度
```

#### 场景 1A：强制无交互初始化

如果初始化过程不能等待用户回答，可以为四个支持的 Skill 增加 `no-interrupt`：

```text
1. /pre-check no-interrupt
2. /init
3. /project-analysis
4. /rule-config no-interrupt
5. /mcp-configuration no-interrupt
6. /project-rules-examples no-interrupt
7. /cad-load
8. /full-flow
```

- `--no-interrupt` 与 `no-interrupt` 等价。
- 不加参数时保持各 Skill 原有逻辑。
- 该参数只适用于 `pre-check`、`rule-config`、`mcp-configuration`、`project-rules-examples`，不用于 `/init` 或 `/project-analysis`。
- 严格模式无法自动完成时会直接报错终止，不会发起用户交互。

完整行为差异见[项目 README 的项目初始化章节](../../README.md#项目初始化cadence-init-插件)。

### 场景 2：快速 Bug 修复

```
1. /quick-flow         # 使用快速流程
2. Requirement → Plan → Worktree → Develop
3. /checkpoint         # 创建检查点
```

### 场景 3：技术选型

```
1. /exploration-flow   # 使用探索流程
2. Brainstorm → Analyze → Design → Plan
3. 选择：继续开发/回到设计/放弃方案/重新开始
```

### 场景 4：恢复之前的进度

```
1. /cad-load           # 加载项目上下文
2. /status             # 查看当前进度
3. /resume             # 恢复进度
```

## 最佳实践

### 1. 选择正确的流程模式

根据功能复杂度和时间预估选择合适的流程。

### 2. 充分利用断点续传

每个节点完成后会自动创建检查点，使用 `/resume` 恢复。

### 3. 保持 TDD 实践

Subagent Development 强制执行 TDD，测试覆盖率 ≥ 80%。

### 4. 利用 Serena MCP

使用 `analyze` Skill 分析现有代码库，避免重复造轮子。

### 5. 合理使用 Git Worktrees

每个功能开发在独立的 Worktree 中，避免主分支污染。

## 相关资源

- [Commands 使用指南](../commands/)
- [项目 README](../../README.md)
- [版本发布说明](../../RELEASE-NOTES.md)

## 获取帮助

- **问题反馈**: https://github.com/michaelChe956/Cadence-skills/issues
- **文档问题**: 提交 Issue 或 PR
