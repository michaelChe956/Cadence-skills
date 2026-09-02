## Purpose

规则元数据驱动的 Claude Code 权限投影：把"规则要求优先使用什么工具"翻译为 settings.json 中 deny 级强制拦截；优先级链文本随规则正文（.claude/rules/ 与 AGENTS.md 内联区块）常驻上下文，模型被通用 deny 拦截后从上下文查链自动改道，零人工介入。

## ADDED Requirements

### Requirement: 规则模板必须携带机器可读工具元数据

规则模板（code-reading-coding、mcp-servers 等受管源）MUST 在受管注释区声明工具优先级元数据，每条包含 `preferred`（优先工具列表）、`fallback`（被限制的替代工具列表）与 `when`（生效条件，如 `project_type=coding AND codegraph_enabled`、`context7_configured`）三字段。元数据 MUST 与规则人话正文同源同义；规则修改后元数据 MUST 同步更新。

#### Scenario: 元数据驱动拦截集合

- **WHEN** 维护者将某规则的 preferred 从 codegraph 改为其他工具并重新 apply
- **THEN** 生成的权限条目与优先级链文本 MUST 随新元数据同步变化，不残留旧工具名

### Requirement: apply 必须按元数据生成 deny 权限区块

`rule-config apply` MUST 读取元数据，对 `when` 条件成立的条目将其 `fallback` 工具写入业务项目 `.claude/settings.json` 的 `permissions.deny`；写入 MUST 限定在 `cadence-managed:permission-gate` 标记包裹的区块内，MUST NOT 覆盖区块外任何用户自定义内容。`when` 条件不成立的条目 MUST NOT 产生任何权限条目。dry-run MUST 先展示将写入的完整区块预览。

#### Scenario: coding 项目启用 codegraph 时生成检索拦截

- **WHEN** `project_type=coding` 且 codegraph 已启用的业务项目运行 apply
- **THEN** cadence-managed 区块内出现 Grep/Glob/Bash 检索类的 deny 条目
- **AND** 区块外用户已有的 permissions 条目逐字不变

#### Scenario: 未启用条件不产生拦截

- **WHEN** 非 coding 项目或未启用 codegraph 的项目运行 apply
- **THEN** 权限区块不生成任何检索类 deny 条目

### Requirement: 规则正文必须常驻优先级链供拦截后改道

Claude Code 原生 deny 拦截只返回通用文案（不携带规则信息）；完整优先级链文本 MUST 从规则元数据同源渲染并随规则正文常驻上下文——`.claude/rules/` 规则正文与 AGENTS.md codex-rules-inline 内联区块均 MUST 可查到按序列出的 preferred 工具、次选工具与兜底出口（deny 区块内另以惰性条目留存，`/permissions` 面板可读）；模型被 deny 拦截后 MUST 能在上下文规则正文中查到完整优先级链并按链改道，无需人工介入。

#### Scenario: 模型撞墙后自动改道

- **WHEN** Claude Code 会话尝试使用被 deny 的 Grep
- **THEN** 工具调用被通用 deny 文案拦截（拦截反馈不携带链）
- **AND** 模型从上下文规则正文（`.claude/rules/` 正文或 AGENTS.md 内联区块）查到完整优先级链（如 codegraph → ast-grep outline → rg 定向搜索）
- **AND** 模型按链改用 preferred 工具后任务继续，全程无人工弹窗

### Requirement: 必须提供逃逸阀与整体撤销

本期出口：`rule-config --remove-permission-gate` MUST 整体移除受管权限区块且不影响用户自定义内容；Bash 域 MUST 可凭 `CADENCE_BYPASS=1` 命令前缀绕开 `Bash(<tool>:*)` 前缀匹配（命令字符串改变的天然结果，非环境变量读取）。环境变量 `CADENCE_BYPASS=1` 的运行时全量放行为切片 2 PreToolUse hook 交付物：本期 settings.json deny 机制不读环境变量，MUST NOT 声称该行为在本期生效。

#### Scenario: 整体撤销

- **WHEN** 用户运行 `rule-config --remove-permission-gate`
- **THEN** 受管权限区块整体移除，区块外用户自定义内容逐字不变

#### Scenario: Bash 前缀绕开（本期逃逸路径）

- **WHEN** 会话以 `CADENCE_BYPASS=1 <命令>` 前缀执行原本命中 `Bash(grep:*)` 的命令
- **THEN** 命令不再以被拦前缀开头，实际放行执行

#### Scenario: 环境变量全量放行（切片 2 交付物，本期不实现）

- **WHEN** 会话环境中 `CADENCE_BYPASS=1` 且模型调用被 deny 的裸工具（如 Grep/WebSearch）
- **THEN** 本期不声称放行生效；运行时放行由切片 2 PreToolUse hook 交付

### Requirement: no-interrupt 模式下合并必须保守

no-interrupt 模式下，权限区块合并 MUST 仅写入受管区块内条目，与用户已有条目取并集；用户已显式 allow 的工具 MUST NOT 被覆盖为 deny；无法安全合并的条目 MUST 保守跳过并在报告中标明。

#### Scenario: 用户显式 allow 不被降级

- **WHEN** 用户已在 settings.json 显式 allow 某工具且该工具命中 fallback 集合
- **THEN** apply 保守跳过该条 deny 写入并在报告中标明，用户 allow 条目保持不变
