# /develop - 代码实现+单元测试

调用 `subagent-development` skill 进行技术设计。

## 使用场景

使用 Subagent 实现代码，强制遵循 TDD 流程，同时编写单元测试，并进行两阶段审查。

## 功能描述

使用 Subagent 开发代码，包括：
- 读取 Plan skill 的任务清单
- 分配给 Implementer Subagent (8.1)
- Spec Reviewer Subagent (8.2) 审查规范合规
- Code Quality Reviewer Subagent (8.3) 审查代码质量
- 支持并行执行
- 自动进行代码质量审查和覆盖率检查（≥ 80%）

## 输出产物

- 代码实现
- 单元测试（覆盖率 ≥ 80%）
- 测试覆盖率报告
- 代码审查报告
- Git commits

## 相关命令

**前置命令**:
- `/plan` - 生成实现计划（必须）
- `/worktree` - 创建隔离环境（强烈建议）
- `/design` - 生成技术方案（可选）

**后续命令**:
- `/finish` - 完成开发分支

## 详细文档

查看完整 Skill 文档: [subagent-development](../skills/subagent-development/SKILL.md)

### Subagent 定义

- **Implementer (8.1)** - 代码实现 + 单元测试
- **Spec Reviewer (8.2)** - 规范合规审查
- **Code Quality Reviewer (8.3)** - 代码质量审查
