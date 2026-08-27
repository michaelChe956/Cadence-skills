# progressive-context-routing Specification

## Purpose
TBD - created by archiving change improve-progressive-disclosure-routing. Update Purpose after archive.

## Requirements

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

### Requirement: 关键阶段必须重新路由
系统 SHALL 要求 Agent 在新任务、从讨论转为修改文件、OpenSpec 契约获批、开始或恢复 apply、上下文恢复和完工声明前重新判断当前阶段，不得依赖更早阶段的隐含路由结果。

#### Scenario: 上下文压缩后恢复实施
- **WHEN** 会话发生 resume、clear、compact 或 Agent 无法确认之前的路由状态
- **THEN** Agent 根据当前 change、Plan 和待办工作包重新输出路由结果
- **AND** 在门禁恢复前不继续修改实现文件

#### Scenario: 从分析转为修改文件
- **WHEN** Agent 完成只读调查并准备首次创建或修改文件
- **THEN** Agent 重新判断任务是否需要 OpenSpec、Plan、TDD 或文档规则
- **AND** 满足对应前置条件后才开始写入

### Requirement: 有操作的任务必须输出路由回执

对于需要读取仓库、创建或修改文件、调用 OpenSpec 命令、执行命令或声称完成的任务，系统 SHALL 要求 Agent 通过客户端原生机制选择 `using-superpowers` 和当前阶段全部必调 Skill，并将包含阶段、change、Plan、Skill 与用途的简短路由回执作为首个用户可见段落；系统 MUST 要求回执先于仓库规则读取和仓库工具调用。L0 路由内核对客户端调用方式差异 MUST 仅保留中性短说明（Claude/Kimi 使用原生 Skill 调用；Codex/pi 从清单显式选择后全文读取对应 `SKILL.md` 作为调用），MUST NOT 包含静默要求、引导句禁令、事件间隙约束或重试静默等不可验证的姿态类条款。

#### Scenario: 开始实施已有 change

- **WHEN** Agent 准备实施名为 `sample-change` 的 OpenSpec change
- **THEN** Agent 按客户端原生机制选择 `using-superpowers` 和执行类 Skill
- **AND** 首个用户可见段落的路由回执明确显示阶段为实施、change 名称、Plan 路径、执行类 Skill 和用途
- **AND** Skill 调用完成后才读取仓库规则或使用仓库工具

#### Scenario: 纯概念问答

- **WHEN** 用户只要求解释概念且不需要读取仓库、创建文件、执行命令或声称完成
- **THEN** Agent 只选择并调用全局 `using-superpowers` 后直接回答且不输出仓库路由回执
- **AND** 不加载仓库规则、其他无关 Skill、代码修改、文档存储或验证正文

#### Scenario: L0 内核不含姿态类条款

- **WHEN** 比对 L0 路由内核 v3 模板全文
- **THEN** 模板包含客户端调用方式的中性短说明
- **AND** 不包含"保持静默""禁止输出引导句""事件之间""重试静默"类姿态条款

### Requirement: 路由门禁必须失败关闭
系统 MUST 要求 Agent 在必调 Skill 不可用、强制 OpenSpec 未确认、已有 change 缺少 Plan、实施发现契约变化或缺少完成证据时停止当前阶段，而不是静默降级或模拟已完成的流程。

#### Scenario: 必调 Skill 未加载
- **WHEN** 当前任务命中必调 Skill 但 Agent 未加载或无法调用该 Skill
- **THEN** Agent 报告缺失项并停止依赖该 Skill 的后续动作
- **AND** 不得用普通回答声称已经执行该 Skill

#### Scenario: 实施发现验收标准变化
- **WHEN** 实施过程中发现需要改变 OpenSpec 中的范围、架构边界或验收标准
- **THEN** Agent 停止当前实施
- **AND** 先更新并重新确认 OpenSpec，再更新 Plan 后继续

#### Scenario: 缺少新鲜验证证据
- **WHEN** Agent 准备声称任务完成、Bug 已修复或测试通过，但没有读取与声明对应的新鲜验证输出
- **THEN** Agent 不作完成声明并调用 `superpowers:verification-before-completion`

### Requirement: 流程必须支持明确的轻量豁免
系统 SHALL 对纯问答、只读调查、无语义文档修正和恢复既有明确契约的小型 Bug 提供明确的 OpenSpec 豁免，同时 MUST 要求新行为、公共接口或数据变化、跨模块重构和架构或验收边界变化使用 OpenSpec。

#### Scenario: 恢复既有契约的小型 Bug
- **WHEN** Bug 修复只恢复已有且明确的行为，不改变公共契约或验收边界
- **THEN** Agent 可以不创建新 OpenSpec change
- **AND** 仍按 systematic-debugging、TDD 和完成前验证流程执行

#### Scenario: 新增公共行为
- **WHEN** 变更新增公共行为、修改接口或数据结构，或改变验收标准
- **THEN** Agent 不得使用轻量豁免
- **AND** 必须完成 brainstorming、OpenSpec 契约审阅和 writing-plans 门禁
