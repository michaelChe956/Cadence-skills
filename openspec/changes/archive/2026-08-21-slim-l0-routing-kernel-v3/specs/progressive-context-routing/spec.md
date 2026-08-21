# progressive-context-routing Delta

## MODIFIED Requirements

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
