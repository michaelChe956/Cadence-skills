## ADDED Requirements

### Requirement: OpenSpec 配置必须冗余职责和 artifact 边界
系统 SHALL 在 `openspec/config.yaml` 的公共 `context` 中声明 OpenSpec 管契约、Superpowers 管行为，并 SHALL 为 proposal、design、specs 和 tasks 配置各自的产物边界规则。

#### Scenario: 生成 design artifact
- **WHEN** Agent 创建或更新 OpenSpec design
- **THEN** OpenSpec 指令包含将 brainstorming 已确认架构、边界和权衡持久化的规则
- **AND** design 不承担精确文件级实施步骤

#### Scenario: 生成 tasks artifact
- **WHEN** Agent 创建或更新 OpenSpec tasks
- **THEN** tasks 只包含可跟踪的高层工作包
- **AND** 精确文件、命令、测试与提交步骤留给 Superpowers Plan

### Requirement: OpenSpec 配置不得使用无效的 apply artifact 规则
系统 MUST 只对当前 schema 的有效 artifact ID 配置规则，并 MUST NOT 将特殊命令 `apply` 当作 `rules.apply` artifact。

#### Scenario: 直接获取 apply 指令
- **WHEN** Agent 执行 `/opsx:apply` 或等价的 OpenSpec apply 流程
- **THEN** Plan 门禁来自 L0、L1 以及 apply 读取的 design/tasks 契约
- **AND** `openspec/config.yaml` 不包含无效的 `rules.apply`

### Requirement: OpenSpec 工作包与 Superpowers Plan 必须可追溯
系统 MUST 要求 Superpowers Plan 引用 OpenSpec change、工作包编号和相关 requirement；Plan SHALL 只能展开已确认契约，不得重新定义范围、架构边界或验收标准。

#### Scenario: writing-plans 展开工作包
- **WHEN** OpenSpec 书面契约获批并调用 `superpowers:writing-plans`
- **THEN** Plan 写入 `cadence/plans/`
- **AND** 每组实施步骤可以追溯到 OpenSpec 工作包和 requirement

#### Scenario: Plan 与 OpenSpec 冲突
- **WHEN** Plan 中的文件级方案需要改变 OpenSpec 的范围、架构边界或验收标准
- **THEN** Agent 停止确认该 Plan
- **AND** 先更新并重新审阅 OpenSpec，再重新生成或更新 Plan

### Requirement: 路由目标和版本必须通过静态检查
系统 MUST 提供可重复的静态检查，确认 L0 引用的规则文件与 Skill 名称存在、`CLAUDE.md` 和 `AGENTS.md` 的路由版本一致、L1 规范源与生成副本一致，并且 OpenSpec 配置只使用有效 artifact 规则键。

#### Scenario: 入口引用不存在的 Skill
- **WHEN** L0 引用当前项目应已安装但实际不存在的 Superpowers Skill
- **THEN** 静态检查失败并报告入口文件、任务信号和缺失名称

#### Scenario: OpenSpec 包含 rules.apply
- **WHEN** `openspec/config.yaml` 将 `apply` 配置为 artifact 规则键
- **THEN** 静态检查失败并指出 `apply` 是特殊命令而非有效 artifact

### Requirement: 必须验证跨客户端关键场景
系统 SHALL 对 Claude Code、Kimi Code 与 Codex 执行新功能、Bug、直接 apply、上下文恢复、纯问答和完工声明场景验证，并 MUST 记录路由回执、实际加载项、门禁结果和无关正文误加载项。

#### Scenario: Kimi Code 漏调 brainstorming
- **WHEN** Kimi Code 在新功能场景中未调用 brainstorming 就准备创建 OpenSpec 或实现文件
- **THEN** 场景验证判定失败
- **AND** 失败映射到 AGENTS L0 或完整协作规则的修复位置

#### Scenario: Claude Code 上下文恢复
- **WHEN** Claude Code 在 compact 或 resume 后继续已有 change
- **THEN** 它重新识别 change、Plan、当前阶段和必调 Skill
- **AND** 不因之前已经路由过而跳过门禁

#### Scenario: Codex 纯问答
- **WHEN** Codex 只回答不涉及仓库操作的概念问题
- **THEN** 它不加载实现、文档写入或完成验证正文
- **AND** 场景验证不把合理的轻量行为判定为失败

#### Scenario: 完工声明
- **WHEN** 任一客户端准备声称修改完成、Bug 已修复或测试通过
- **THEN** 它调用 verification-before-completion 并读取新鲜验证证据
- **AND** 缺少证据时拒绝完成声明

### Requirement: 验证结果必须可审计
系统 MUST 记录客户端、场景、期望阶段、期望规则与 Skill、实际路由、门禁结果、误加载项和结论，并 SHALL 将失败项映射到 L0、L1、L2 或具体 OpenSpec artifact 的修复位置。

#### Scenario: 直接 apply 越过 Plan
- **WHEN** 任一客户端在没有已确认 Plan 的情况下继续执行 OpenSpec 工作包
- **THEN** 验证记录判定失败
- **AND** 明确指出是入口路由、协作规则还是 artifacts 中的 Plan 门禁未生效
