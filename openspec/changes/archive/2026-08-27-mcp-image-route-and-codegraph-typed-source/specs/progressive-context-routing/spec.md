# progressive-context-routing 变更提案

## MODIFIED Requirements

### Requirement: 入口必须常驻动作型路由内核
系统 MUST 在生成的 `CLAUDE.md` 与 `AGENTS.md` 中直接内嵌短小的动作型路由内核，将任务和阶段信号映射到必读规则、必调 Superpowers Skill 和后续门禁；系统 MUST NOT 仅使用"按需查看规则"或文件列表代替触发映射。路由内核中的代码阅读摘要条目 MUST 与目标项目类型一致：Coding 项目引导代码图与结构化大纲工具链，非 Coding 项目引导文档与配置的结构化定向阅读且不包含默认代码图要求。

#### Scenario: 新功能先进入 brainstorming
- **WHEN** 用户要求新增功能、改变既有行为或讨论实施方案
- **THEN** Agent 在创建实现文件或 OpenSpec artifacts 前调用 `superpowers:brainstorming`
- **AND** 仅在用户确认设计后把结论持久化到 OpenSpec

#### Scenario: 架构摸底先加载代码阅读规则
- **WHEN** 用户要求进行架构摸底、调用链分析或影响面分析
- **THEN** Agent 大范围读取前加载 `.claude/rules/code-reading.md`
- **AND** Coding 项目按该规则在 CodeGraph、`ast-grep outline` 与精确文本检索间选择；非 Coding 项目遵循该规则的文档与配置阅读指引，MUST NOT 因此初始化或构建代码图

#### Scenario: 非 Coding 项目不受代码工具摘要误导
- **WHEN** 非 Coding 项目的 Agent 读取入口文件的代码阅读条目
- **THEN** 该条目 MUST 呈现文档结构化阅读语义而非代码检索工具链
- **AND** 条目顺序 MUST NOT 被解读为代码工具适用于该项目

#### Scenario: 直接 apply 不得跳过 Plan
- **WHEN** 用户或 Agent 准备执行 `/opsx:apply`
- **THEN** Agent 重新加载协作规则并检查当前 OpenSpec change 是否存在已确认的 Superpowers Plan
- **AND** 没有 Plan 时停止实施并先调用 `superpowers:writing-plans`
