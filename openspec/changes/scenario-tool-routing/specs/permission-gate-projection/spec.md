## MODIFIED Requirements

### Requirement: 规则模板必须携带机器可读工具元数据

规则模板受管注释区 MUST 声明 schema v2 元数据，仅含稳定字段：`schema_version`（版本标识）、`default_mode`（默认 gate 模式，MUST 为 `text`）、`recommended_profile`（推荐 profile，默认 `safe`）。旧 v1 三字段（preferred/fallback/when）MUST NOT 再用于 deny 生成；解析器 MUST 兼容读取 v1 元数据（向后兼容旧项目）但仅作展示，MUST NOT 据其产生权限条目。工具优先级语义由 scenario-tool-routing 的九场景矩阵承载，元数据与矩阵 MUST 不漂移。

#### Scenario: v1 旧项目兼容

- **WHEN** 含 v1 元数据（preferred/fallback/when）的既有项目重新 apply
- **THEN** 解析成功且不因 v1 元数据产生任何 deny 条目；报告提示元数据 schema 已升级

#### Scenario: 元数据驱动拦截集合

- **WHEN** 维护者修改规则元数据 v2 字段（如 recommended_profile）并重新 apply
- **THEN** 报告与校验随新元数据同步变化；权限条目仅由 gate 模式决定，元数据不再直接驱动拦截集合

### Requirement: apply 必须按 gate 模式生成权限区块

`rule-config apply` 的权限区块生成 MUST 按显式模式分流，默认模式为 `text`：

- **text（默认）**：MUST NOT 生成任何 deny 条目（权限区块整体不写入）
- **safe（opt-in，`--enable-permission-gate=safe`）**：MUST 仅生成参数可识别的危险命令形态 deny（递归删除类/敏感路径覆盖类）；MUST NOT 包含按工具名的全局 deny（Grep/Glob/WebSearch/WebFetch 等）
- **strict（opt-in，`--enable-permission-gate=strict`）**：保留现行全量 deny 集合，仅供实验与回归；启用时报告 MUST 明示误伤风险

写入仍 MUST 限定在 `cadence-managed:permission-gate` 标记区块内；`when` 类项目条件仅对 safe/strict 模式的条目求值。dry-run MUST 展示将写入的完整区块预览与所用模式。

#### Scenario: 默认安装零 deny

- **WHEN** 用户未显式启用 gate 运行 apply（默认 text 模式）
- **THEN** settings.json 不产生任何受管 deny 条目；规则文本（含路由矩阵）正常分发

#### Scenario: safe 模式仅含危险命令

- **WHEN** 用户以 `--enable-permission-gate=safe` 运行 apply
- **THEN** 受管区块仅含危险命令形态条目，不含 Grep/Glob/Bash(grep:*) 等按工具名的全局 deny

#### Scenario: 旧无标记区块迁移提示

- **WHEN** apply 检测到 v1 时期生成的受管 deny 区块且无模式标记
- **THEN** 报告 MUST 提示用户显式选择模式（text 清除/safe 收窄/strict 保留），MUST NOT 静默沿用旧区块

### Requirement: 规则正文必须常驻路由矩阵供自主路由

模型自主路由的依据 MUST 是规则正文中常驻的九场景路由矩阵与 CLAUDE.md 决策卡（见 scenario-tool-routing）；deny 区块内 MUST NOT 再写入 ❌ 引导文案条目（实证模型不可见）；strict 模式下模型被拦后 MUST 能从规则正文矩阵查到首选链并改道。

#### Scenario: 被拦后从矩阵改道

- **WHEN** strict 模式会话尝试使用被 deny 的 Grep 而任务属 C 场景
- **THEN** 拦截反馈为 Claude 通用文案；模型从规则正文路由矩阵查到 C 场景首选链（CodeGraph→ast-grep）并改道，全程无人工介入

### Requirement: 必须提供逃逸阀与整体撤销

`rule-config --remove-permission-gate` MUST 整体移除受管权限区块且不影响用户自定义内容（三模式通用）；strict 模式下 Bash 域 MUST 可凭 `CADENCE_BYPASS=1` 命令前缀绕开 `Bash(<tool>:*)` 前缀匹配（命令字符串改变的天然结果）。PreToolUse hook 运行时放行为后续切片交付物，本期 MUST NOT 声称生效。

#### Scenario: 整体撤销

- **WHEN** 用户运行 `rule-config --remove-permission-gate`
- **THEN** 受管权限区块整体移除，区块外用户自定义内容逐字不变

#### Scenario: Bash 前缀绕开（本期逃逸路径）

- **WHEN** strict 模式会话以 `CADENCE_BYPASS=1 <命令>` 前缀执行原本命中 `Bash(grep:*)` 的命令
- **THEN** 命令不再以被拦前缀开头，实际放行执行（命令字符串改变的天然结果，非环境变量读取）

#### Scenario: 环境变量全量放行（切片 2 交付物，本期不实现）

- **WHEN** 会话环境中 `CADENCE_BYPASS=1` 且模型调用被 deny 的裸工具
- **THEN** 本期不声称放行生效；运行时放行由后续 PreToolUse hook 切片交付

### Requirement: no-interrupt 模式下合并必须保守

no-interrupt 模式下，权限区块合并 MUST 仅写入受管区块内条目，与用户已有条目取并集；用户已显式 allow 的工具 MUST NOT 被覆盖为 deny；无法安全合并的条目 MUST 保守跳过并在报告中标明。

#### Scenario: 用户显式 allow 不被降级

- **WHEN** 用户已在 settings.json 显式 allow 某工具且该工具命中 strict 模式 fallback 集合
- **THEN** apply 保守跳过该条 deny 写入并在报告中标明，用户 allow 条目保持不变
