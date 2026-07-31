## MODIFIED Requirements

### Requirement: 合并与保护语义脚本内确定性实现
系统 MUST 在脚本内实现现行全部合并与保护语义，且普通模式与 no-interrupt 的动作空间不同：no-interrupt 对冲突规则文件按章节级权威规则合并（同名章节以标题级别加去编号标题文本识别、模板在前、项目独有章节按原序保留、同名章节项目内容去重后进入项目补充）；普通模式对冲突规则文件 SHALL 询问用户，无响应或拒绝时 MUST NOT 覆盖，跳过并报告。`**项目补充**` 标记行 MUST 视为合并协议保留字：章节合并的项目独有行判定 MUST 排除该标记行，使章节合并对同一输入重跑幂等（merge(t, merge(t, x)) == merge(t, x)），且已被重复标记污染的文件在下次合并时 MUST 自动清除多余标记。no-interrupt 下合并结果与现有文件逐字一致时 MUST 跳过写盘并在报告中标记 `unchanged`。缺少 CodeGraph 段落的规则文件 MUST 与其他普通规则文件走统一 drift 处理路径（普通模式询问、no-interrupt 自动章节合并），MUST NOT 再做报告型特判。L0 受管区块的插入/升级/替换与双入口统一预检备份屏障、L1 框架规则的完整内容比对与备份升级、OpenSpec config.yaml 的保守合并去重、时间戳备份屏障与同文件系统原子发布 MUST 按现行语义执行。任何必要备份失败时 MUST 整体终止且保持原文件不变。

#### Scenario: no-interrupt 下已有项目规则被合并而非覆盖
- **WHEN** 目标项目已存在与模板冲突的规则文件并以 no-interrupt 运行
- **THEN** 脚本 MUST 先创建时间戳备份再按章节级权威规则合并
- **AND** 项目独有章节和同名章节的项目补充内容 MUST 保留

#### Scenario: 章节合并重跑幂等
- **WHEN** no-interrupt 对同一规则文件重复运行章节合并（含上一次合并已注入 `**项目补充**` 标记的产物）
- **THEN** 第二次及以后合并结果 MUST 与第一次合并结果逐字一致
- **AND** 每个同名章节的项目补充区域 MUST 恰好含一个 `**项目补充**` 标记行

#### Scenario: 已污染文件合并自愈
- **WHEN** 既有规则文件因历史缺陷已含多个重复 `**项目补充**` 标记行并以 no-interrupt 运行
- **THEN** 合并结果 MUST 只保留一个标记行且项目独有内容行不丢失
- **AND** 脚本 MUST NOT 要求用户手动恢复备份

#### Scenario: 合并结果一致跳过写盘
- **WHEN** no-interrupt 下章节合并结果与现有文件逐字一致
- **THEN** 脚本 MUST 跳过写盘并在报告资产动作中标记 `unchanged`

#### Scenario: 缺 CodeGraph 段落统一合并
- **WHEN** 既有 code-reading.md 与模板 drift 且缺少 CodeGraph 段落并以 no-interrupt 运行
- **THEN** 脚本 MUST 按统一章节级权威规则自动合并写盘（模板 CodeGraph 段落并入、项目内容保留、先创建时间戳备份）
- **AND** MUST NOT 仅报告提示用户手动合并

#### Scenario: 普通模式下冲突规则文件默认不覆盖
- **WHEN** 普通模式遇到与模板冲突的既有规则文件且用户无响应或拒绝覆盖
- **THEN** 脚本 MUST 保持原文件不变并在报告中标记跳过
- **AND** 缺失的规则文件 SHALL 照常创建

#### Scenario: Markdown 无法可靠解析的回退
- **WHEN** no-interrupt 模式下既有规则文件无法可靠解析章节结构
- **THEN** 脚本 MUST 先创建时间戳备份，写入标准结构，并把原内容完整附加到"原项目补充"
- **AND** 备份失败时 MUST 终止且原文件不变

#### Scenario: 备份失败整体终止
- **WHEN** 任一动作需要备份但备份创建失败
- **THEN** 脚本 MUST 立即终止且原文件保持不变
- **AND** 报告 MUST 记录失败文件、原因与恢复建议

#### Scenario: 入口文件单次处理
- **WHEN** 脚本处理 CLAUDE.md 与 AGENTS.md
- **THEN** L0 区块与全部摘要行 MUST 在一次运行内合并完成，每个入口至多写入一次
- **AND** 受管区块外的项目内容 MUST 原样保留
- **AND** 摘要编号与现有内容冲突时 MUST 保留原内容、追加缺失摘要并在报告中说明

## ADDED Requirements

### Requirement: dry-run 冲突报告标注 no-interrupt 真实动作
dry-run 计划中普通规则文件 drift 冲突条目在 no-interrupt 模式下 MUST 额外携带反映真实执行动作的字段（`no_interrupt_action: "markdown-merge"`），使用户不被安全默认 `recommendation=keep` 误导；普通模式冲突条目 MUST 保持不变。

#### Scenario: no-interrupt drift 冲突标注真实动作
- **WHEN** no-interrupt 模式 dry-run 检测到普通规则文件 drift 冲突
- **THEN** 冲突条目 MUST 含 `no_interrupt_action: "markdown-merge"` 字段
- **AND** `recommendation` 安全默认值保持不变

#### Scenario: 普通模式冲突条目不新增字段
- **WHEN** 普通模式 dry-run 检测到普通规则文件 drift 冲突
- **THEN** 冲突条目 MUST NOT 含 `no_interrupt_action` 字段
