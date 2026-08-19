## Purpose

治理 Superpowers 工作流产物：以入口文件 L0 受管区块中的显式路径映射覆盖表压制 Skill 正文默认路径，并提供项目级"产物自动提交"开关控制 design/plan 文档写完后的 git commit 行为。

## ADDED Requirements

### Requirement: 产物路径映射必须显式覆盖 Skill 默认路径
系统 MUST 在 L0 路由内核与 `.claude/rules/document-storage.md` 中维护同一张产物路径映射覆盖表：`docs/superpowers/specs/`（design/spec）映射为 `cadence/designs/`，`docs/superpowers/plans/`（plan）映射为 `cadence/plans/`；并 MUST 声明该表优先级高于任何 Skill 正文中的路径指示。OpenSpec 产物 MUST 保持存放于 `openspec/` 目录。映射表 MUST 在脚本内定义单一事实源，L0 内核与 document-storage.md 的内容 MUST 与该事实源逐字一致。系统 MUST NOT 改写全局 Superpowers Skill 本体。

#### Scenario: Skill 默认路径被项目路径覆盖
- **WHEN** Superpowers 的 brainstorming/writing-plans Skill 正文指示写入 `docs/superpowers/` 下路径
- **THEN** Agent 必须以覆盖表为准写入 `cadence/designs/` 或 `cadence/plans/`

#### Scenario: 三源映射表逐字一致
- **WHEN** 校验 L0 内核、document-storage.md 与脚本内映射常量
- **THEN** 三者的路径映射与优先级声明 MUST 逐字一致

### Requirement: 产物自动提交开关必须项目级可控
系统 MUST 在入口文件 `## 项目配置` 章节维护开关行 `- **产物自动提交（design/plan）**：<值>`，双入口均写入。首次写入默认值 MUST 为 `关闭`；之后 MUST 保留用户手改值不受框架覆盖。仅精确值 `开启` 视为启用；`关闭` 或任何其他值 MUST 按关闭处理，非法值 MUST 保留原文不改写并记录 warning。开关行 MUST 位于 `## 项目配置` 章节内；章节缺失时 MUST 在文件末尾创建；多个同名章节 MUST 仅处理首个并记录 warning；重复开关行 MUST 保留首个并归并。`## 项目配置` 章节仅维护开关行，系统 MUST NOT 在入口文件中检测或写入项目技术栈信息。

#### Scenario: 首次初始化写入默认值
- **WHEN** 入口文件不存在开关行
- **THEN** 系统 MUST 写入默认值 `关闭`

#### Scenario: 用户手改值保留
- **WHEN** 用户已将开关改为 `开启` 后重跑 rule-config
- **THEN** 系统 MUST 保留 `开启` 不覆盖

#### Scenario: 非法值按关闭处理
- **WHEN** 开关值为 `开启`/`关闭` 以外的值
- **THEN** 系统 MUST 保留原文、记录 warning，且行为按关闭处理

#### Scenario: 章节外孤儿开关行归并
- **WHEN** 开关前缀行出现在 `## 项目配置` 章节之外，或章节外孤儿行与章节内开关行同时存在
- **THEN** 系统 MUST 将相关开关行归并到章节内规范位置并保证全文件恰好一行开关行
- **AND** 在孤儿行/多行归并场景中，值一致且合法时 MUST 保留该值；值冲突或含非法值时 MUST 按关闭处理并记录 warning
- **AND** 章节内仅有一行开关时，既有语义保持不变：合法值保留，非法值原文保留并记录 warning

#### Scenario: 入口文件不含技术栈信息
- **WHEN** rule-config 处理任一入口文件
- **THEN** 系统 MUST NOT 写入 `### 项目技术栈` 或技术栈字段行
- **AND** 用户既有的技术栈内容 MUST 逐字保留

### Requirement: 开关行为读取必须有确定性顺序
Agent 行为层读取开关时 MUST 以 `CLAUDE.md` 为准、`AGENTS.md` 为兜底（CLAUDE.md 缺失时）；双入口值不一致时 MUST 按 `关闭` 处理并记录 warning。L0 内核 MUST 包含强制条款：调用 brainstorming / writing-plans 完成文档写入后必须读取该开关，为 `关闭` 时禁止 `git commit`，只汇报产物路径并等待用户确认。

#### Scenario: 关闭时禁止自动提交
- **WHEN** 开关为 `关闭` 且 brainstorming/writing-plans 完成文档写入
- **THEN** Agent MUST NOT 执行 `git commit`
- **AND** 只汇报产物路径并等待用户确认

#### Scenario: 双入口不一致按关闭
- **WHEN** CLAUDE.md 开关为 `开启` 而 AGENTS.md 为 `关闭`
- **THEN** 行为 MUST 按关闭处理并记录 warning
