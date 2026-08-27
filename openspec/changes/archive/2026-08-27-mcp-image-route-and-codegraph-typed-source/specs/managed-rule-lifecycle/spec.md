# managed-rule-lifecycle 变更提案

## MODIFIED Requirements

### Requirement: 完整协作规则必须有框架规范源
系统 SHALL 在 `cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md` 维护 OpenSpec 与 Superpowers 完整协作规则，并 MUST 由 `rule-config` 将其生成到业务项目的 `.claude/rules/openspec-superpowers-workflow.md`。系统 MUST 按最终项目类型分别为代码使用规则与代码阅读规则各选择唯一的来源模板，并 MUST 始终以 `code-usage.md` 与 `code-reading.md` 作为两者对应的落地文件名，SHALL NOT 同时生成多个同名规则文件或使用带项目类型后缀的落地名；两类规则的来源模板选择及其入口摘要文案 MUST 仅消费最终项目类型裁决结果，MUST NOT 旁路读取原始检测结果或其他信号。non-coding 项目生成的代码阅读规则及其摘要 MUST NOT 包含对 CodeGraph 的默认初始化或优先使用要求。L0 受管区块的规范源 MUST 仅用于插入 `CLAUDE.md` 与 `AGENTS.md`，MUST NOT 作为受管规则文件复制到 `.claude/rules/`。

#### Scenario: 初始化后的业务项目生成协作规则
- **WHEN** 已安装 OpenSpec 与 Superpowers 的业务项目运行 `rule-config`
- **THEN** 项目获得完整协作规则以及指向该规则的 L0 路由
- **AND** 该流程不重复安装 OpenSpec 或 Superpowers

#### Scenario: 当前仓库同步框架副本
- **WHEN** Cadence 维护者修改完整协作规则
- **THEN** 先修改 `cadence-init` 中的规范源
- **AND** 再从规范源同步当前仓库的 `.claude/rules/` 副本

#### Scenario: 非 Coding 项目仍获得代码阅读规则
- **WHEN** 最终项目类型裁决为非 Coding 且用户未显式启用 CodeGraph 开关
- **THEN** 系统 MUST 继续生成 `.claude/rules/code-reading.md` 与对应入口摘要以确保 L0 引用不悬空，其内容来自非 Coding 来源模板
- **AND** 该规则与摘要 MUST NOT 要求初始化、构建或优先使用 CodeGraph，MUST NOT 将结构化大纲命令设为 Markdown/YAML/JSON 等文档配置阅读的前置步骤
- **AND** 系统 SHALL 跳过 CodeGraph 安装与初始化，SHALL NOT 跳过代码阅读规则文件的生成

#### Scenario: 入口摘要随项目类型同步
- **WHEN** `rule-config` 渲染入口文件的代码阅读摘要条目
- **THEN** Coding 项目获得包含代码图与大范围检索语义的摘要文案
- **AND** 非 Coding 项目获得面向文档与配置定向阅读的摘要文案，两条文案 MUST 使用与所选规则来源一致的项目类型信号

#### Scenario: 代码使用规则按项目类型单选来源
- **WHEN** `rule-config` 完成项目类型检测并生成规则文件
- **THEN** 系统 MUST 只生成一个 `.claude/rules/code-usage.md`，其内容来自与该项目类型对应的来源模板
- **AND** `.claude/rules/` 下 MUST NOT 出现带项目类型后缀的代码使用规则文件
- **AND** 入口文件与 L0 受管区块对代码使用规则的引用 MUST 指向实际存在的 `code-usage.md`

#### Scenario: L0 插入源不复制为规则文件
- **WHEN** `rule-config` 在目标项目执行完成
- **THEN** `.claude/rules/` 下 MUST NOT 存在 L0 受管区块插入源的副本
