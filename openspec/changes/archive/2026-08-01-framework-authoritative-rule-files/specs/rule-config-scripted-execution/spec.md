## MODIFIED Requirements

### Requirement: 合并与保护语义脚本内确定性实现
系统 MUST 在脚本内实现现行全部合并与保护语义，且按资产类别区分动作空间。框架受管规则文件（`.claude/rules/` 下的 `mcp-servers.md`、`code-reading.md`、`document-storage.md`、`language.md`、`markdown-format.md`、`code-usage.md`、`playwright.md`）MUST 采用框架权威全覆盖：内容与框架模板一致则幂等跳过，不一致时 MUST 先将原文件复制到 `cadence/legacy/` 归档，再以模板内容原子覆盖原位；MUST NOT 产生 `**项目补充**` 段落、保留项目独有章节或对这类文件调用章节级合并。`openspec-superpowers-workflow.md`（L1）MUST 保留基于完整内容的版本识别与升级语义，不纳入权威全覆盖。L0 受管区块的插入/升级/替换与双入口统一预检备份屏障、OpenSpec config.yaml 的保守合并去重、时间戳归档屏障与同文件系统原子发布 MUST 按现行语义执行。普通模式对框架受管规则文件 drift SHALL 询问用户，无响应或拒绝时 MUST NOT 覆盖，跳过并报告；no-interrupt 模式 MUST 直接权威覆盖并归档原文件。`**项目补充**` 标记仅对仍适用章节合并的非框架资产保留合并协议保留字语义。no-interrupt 下目标内容与现有文件逐字一致时 MUST 跳过写盘并在报告中标记 `unchanged`。任何必要归档失败时 MUST 整体终止且保持原文件不变；`atomic_write` 失败时原文件 MUST 因原子替换语义保持不变，无需回滚归档。

#### Scenario: no-interrupt 下框架规则文件权威覆盖
- **WHEN** 目标项目已存在与模板内容不一致的框架受管规则文件并以 no-interrupt 运行
- **THEN** 脚本 MUST 先将原文件复制到 `cadence/legacy/<时间戳>/<相对路径>` 归档
- **AND** 仅在归档成功后 SHALL 以模板内容原子覆盖原位
- **AND** 结果 MUST NOT 含 `**项目补充**` 段落或项目独有章节

#### Scenario: 框架规则文件幂等跳过
- **WHEN** 框架受管规则文件内容已与模板逐字一致
- **THEN** 脚本 MUST 跳过写盘且 MUST NOT 产生归档
- **AND** 报告 MUST 标记 `unchanged`

#### Scenario: 普通模式下冲突规则文件默认不覆盖
- **WHEN** 普通模式遇到与模板冲突的既有框架受管规则文件且用户无响应或拒绝覆盖
- **THEN** 脚本 MUST 保持原文件不变并在报告中标记跳过
- **AND** 缺失的规则文件 SHALL 照常创建

#### Scenario: Markdown 无法可靠解析的框架规则文件
- **WHEN** no-interrupt 模式下既有框架受管规则文件无法可靠解析
- **THEN** 脚本 MUST 先归档原文件，再以模板内容原子覆盖原位
- **AND** 归档失败时 MUST 终止且原文件不变

#### Scenario: 备份失败整体终止
- **WHEN** 任一动作需要归档但归档复制失败
- **THEN** 脚本 MUST 立即终止且原文件保持不变
- **AND** 报告 MUST 记录失败文件、原因与恢复建议

#### Scenario: 原子覆盖失败不破坏原文件
- **WHEN** 归档成功后 `atomic_write` 原子替换原位失败
- **THEN** 原文件 MUST 保持运行前内容不变
- **AND** 已归档副本 SHALL 保留在 `cadence/legacy/` 供恢复
- **AND** 报告 MUST 记录写入失败与归档恢复路径

#### Scenario: 入口文件单次处理
- **WHEN** 脚本处理 CLAUDE.md 与 AGENTS.md
- **THEN** L0 区块与全部摘要行 MUST 在一次运行内合并完成，每个入口至多写入一次
- **AND** 受管区块外的项目内容 MUST 原样保留
- **AND** 摘要编号与现有内容冲突时 MUST 保留原内容、仅追加缺失摘要并在报告中说明

### Requirement: dry-run 冲突报告标注 no-interrupt 真实动作
dry-run 计划中框架受管规则文件 drift 冲突条目在 no-interrupt 模式下 MUST 额外携带反映真实执行动作的字段（`no_interrupt_action: "authoritative-overwrite"`），使用户不被安全默认 `recommendation=keep` 误导；普通模式冲突条目 MUST 保持不变。

#### Scenario: no-interrupt drift 冲突标注真实动作
- **WHEN** no-interrupt 模式 dry-run 检测到框架受管规则文件 drift 冲突
- **THEN** 冲突条目 MUST 含 `no_interrupt_action: "authoritative-overwrite"` 字段
- **AND** `recommendation` 安全默认值保持不变

#### Scenario: 普通模式冲突条目不新增字段
- **WHEN** 普通模式 dry-run 检测到框架受管规则文件 drift 冲突
- **THEN** 冲突条目 MUST NOT 含 `no_interrupt_action` 字段
