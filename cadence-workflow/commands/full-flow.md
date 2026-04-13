# /full-flow - 完整开发流程

调用 `full-flow` skill 执行完整的8节点开发流程。

## 使用场景

- 复杂功能开发（预估 >2小时）
- 团队协作项目（需要完整文档）
- 企业级应用（需要设计审查）
- 涉及存量代码改造（需要 Analyze 节点）
- 需要完整追溯（需要所有产物）

## 功能

执行完整的8节点开发流程：Brainstorm → Analyze → Requirement → Design → Design Review → Plan → Git Worktrees → Subagent Development

每个节点完成后需要人工确认，支持断点续传。

## 输出

- PRD 文档：`.claude/docs/{date}_PRD_{功能名称}_v1.0.md`
- 存量分析报告：`.claude/analysis/{date}_存量分析_{功能名称}_v1.0.md`
- 需求文档：`.claude/docs/{date}_需求文档_{功能名称}_v1.0.md`
- 技术方案：`.claude/designs/{date}_技术方案_{功能名称}_v1.0.md`
- 审查报告：`.claude/docs/{date}_设计审查_{功能名称}_v1.0.md`
- 实现计划：`.claude/designs/{date}_实现计划_{功能名称}_v1.0.md`
- 代码实现 + 单元测试（覆盖率 ≥ 80%）

## 相关命令

- `/quick-flow` - 快速开发流程（4节点，适合简单功能）
- `/exploration-flow` - 技术探索流程（4节点，适合研究）
- `/status` - 查看进度
- `/resume` - 恢复进度
- `/checkpoint` - 创建检查点
