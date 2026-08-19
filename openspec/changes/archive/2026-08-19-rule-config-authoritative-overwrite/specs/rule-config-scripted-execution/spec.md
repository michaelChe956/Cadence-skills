## MODIFIED Requirements

### Requirement: 脚本两阶段执行与模式衔接

系统 MUST 提供单一脚本执行体，支持 `dry-run` 与 `apply` 两个阶段。`dry-run` SHALL 只读检测并输出包含每资产动作、冲突清单和备份需求的 JSON 计划，不得写入任何目标文件；`apply` SHALL 执行全部动作并输出 JSON 报告。no-interrupt 模式 MUST 在一次 `apply` 调用内完成检测与执行；框架受管内容 drift 全部转为确定性动作后，系统当前无活跃冲突类型，普通模式与 no-interrupt 模式均 MUST 不经用户决策完成执行。决策文件机制 MUST 保留为休眠兜底：未来引入需用户决策的冲突类型时，普通模式存在冲突的 `apply` MUST 经决策文件传入用户决策。脚本 CLI MUST 提供用户意图参数：显式项目类型指定、要求忽略 `cadence/`、要求启用 Playwright、要求启用 CodeGraph，分别对应现行 SKILL 中用户明确指定或要求的分支。

#### Scenario: no-interrupt 一把执行

- **WHEN** Agent 以 no-interrupt 模式调用脚本 `apply`
- **THEN** 脚本内部完成检测与全部确定性动作的执行
- **AND** Agent 全程不 Read/Write 任何目标项目文件，只调用脚本并解读报告

#### Scenario: 普通模式冲突经用户决策

（语义更新：六类受管内容冲突全部转为确定性动作，当前系统无活跃冲突类型；本场景保留为决策机制的休眠契约。）

- **WHEN** 普通模式 `dry-run` 生成计划
- **THEN** 框架受管内容 drift MUST NOT 产生需用户决策的冲突条目，计划无冲突时不要求决策文件，`apply` SHALL 直接执行全部确定性动作
- **AND** 未来引入需用户决策的冲突类型时，Agent SHALL 逐条询问用户（每次一问、给推荐默认项），并将决策以决策文件传入 `apply`
- **AND** 决策缺失、包含未知或重复冲突标识、或与 `apply` 时新鲜计划不符时，脚本 MUST 失败关闭、非零退出、写出报告且零写入，不得按默认猜测执行

#### Scenario: dry-run 零写入

- **WHEN** 脚本以 `dry-run` 运行
- **THEN** 目标项目任何文件 MUST 保持运行前后内容一致
- **AND** 输出的计划 MUST 列出每个资产的动作类型、冲突项和备份需求

#### Scenario: 项目类型判定两模式规则

- **WHEN** 脚本检测项目类型（检测结果为 `coding` 或 `non-coding`）
- **THEN** no-interrupt 模式下最终 `project_type` MUST 等于检测结果，CLI `--project-type` 完全忽略
- **AND** 普通模式下最终 `project_type` 按以下唯⼀规则确定：检测为 `coding` 时为 `coding`（无论 CLI）；检测为 `non-coding` 且 CLI `--project-type coding` 时提升为 `coding`；检测为 `non-coding` 且 CLI 不写或为 `non-coding` 时为 `non-coding`
- **AND** 任一检测+CLI 组合都有唯⼀确定结果，不产生项目类型冲突，无需决策文件响应
- **AND** 项目类型相关的其他语义（规则 2 文本、默认角色、CodeGraph 启用等）MUST 保持以最终 `project_type` 为准；非 Coding 项目取值不变

#### Scenario: 用户意图参数透传

- **WHEN** 用户在命令中明确指定项目类型、要求忽略 `cadence/` 或要求启用 Playwright
- **THEN** Agent MUST 将对应意图作为 CLI 参数传给脚本
- **AND** 显式项目类型在普通模式下仅能把检测为 non-coding 的项目提升为 coding；检测为 coding 时无论 CLI 取何值均为 coding；no-interrupt 模式下 CLI `--project-type` 完全忽略，以检测结果为准（见上「项目类型判定两模式规则」）；`--ignore-cadence` 时 SHALL 将 `cadence/` 追加到 `.gitignore`，`--enable-playwright` 时 SHALL 创建 Playwright 规则与摘要

#### Scenario: 非 Coding 项目显式启用 CodeGraph

- **WHEN** 用户明确要求启用 CodeGraph 但项目未检测到源码
- **THEN** Agent SHALL 以 `--enable-codegraph` 传入脚本，脚本 MUST 执行 codegraph 步骤
- **AND** 项目类型相关的其他语义（规则 2 文本、默认角色等）MUST 保持非 Coding 项目取值不变

### Requirement: 合并与保护语义脚本内确定性实现

系统 MUST 在脚本内实现现行全部合并与保护语义，且按资产类别区分动作空间。框架受管规则文件（`.claude/rules/` 下的 `mcp-servers.md`、`code-reading.md`、`document-storage.md`、`language.md`、`markdown-format.md`、`code-usage.md`、`playwright.md`）MUST 采用框架权威全覆盖：内容与框架模板一致则幂等跳过，不一致时 MUST 先将原文件复制到 `cadence/legacy/` 归档，再以模板内容原子覆盖原位；MUST NOT 产生 `**项目补充**` 段落、保留项目独有章节或对这类文件调用章节级合并。普通模式与 no-interrupt 模式对框架受管规则文件 drift MUST 执行相同动作：直接权威覆盖并归档原文件，不经用户决策。`openspec-superpowers-workflow.md`（L1）MUST 保留基于完整内容的版本识别与升级语义；其内容 drift 或与任何已知框架版本不匹配的状态 MUST 归档后替换为当前框架版本，两模式同动作、不经用户决策。L0 受管区块的插入/升级/替换与双入口统一预检备份屏障、OpenSpec config.yaml 的保守合并去重、时间戳归档屏障与同文件系统原子发布 MUST 按现行语义执行。入口文件 `## 强制规则` 章节的规范化（缺失创建、失效引用清理、重排编号、用户内容保留）MUST 按 entry-file-normalization 能力契约在脚本内确定性实现，两模式同动作且不经用户决策；规范化 MUST NOT 修改受管区块外的项目内容。`**项目补充**` 标记仅对仍适用章节合并的非框架资产保留合并协议保留字语义。no-interrupt 下目标内容与现有文件逐字一致时 MUST 跳过写盘并在报告中标记 `unchanged`。任何必要归档失败时 MUST 整体终止且保持原文件不变；`atomic_write` 失败时原文件 MUST 因原子替换语义保持不变，无需回滚归档。

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

（语义更新：原"询问、无响应或拒绝时保留"行为废止；普通模式与 no-interrupt 统一为归档+权威覆盖。）

- **WHEN** 普通模式遇到与模板内容不一致的既有框架受管规则文件
- **THEN** 脚本 MUST 先将原文件复制到 `cadence/legacy/<时间戳>/<相对路径>` 归档，仅在归档成功后 SHALL 以模板内容原子覆盖原位
- **AND** 处理 MUST 不经用户决策，与 no-interrupt 模式执行相同动作
- **AND** 结果 MUST NOT 含 `**项目补充**` 段落或项目独有章节
- **AND** 缺失的规则文件 SHALL 照常创建

#### Scenario: Markdown 无法可靠解析的框架规则文件

- **WHEN** 既有框架受管规则文件无法可靠解析（内容与模板不一致）
- **THEN** 两模式 MUST 先归档原文件，再以模板内容原子覆盖原位
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
- **THEN** L0 区块与强制规则章节规范化 MUST 在一次运行内合并完成，每个入口至多写入一次
- **AND** 受管区块外的项目内容 MUST 原样保留
- **AND** 章节规范化 MUST 按权威清单重排编号、清理退役引用并保留用户内容，不再仅追加缺失摘要

### Requirement: OpenSpec 配置验证以结构预检取代 instructions 验证

系统 MUST NOT 再创建临时验证工作区、临时 Change 或执行 `openspec instructions` 来验证候选配置。候选 config.yaml 发布前 MUST 通过真实 YAML parser 的语法解析与结构预检：根必须为映射、`schema` 必须缺失或为标量、`context` 必须缺失或为字符串、`rules` 必须缺失或为映射、四个 artifact 规则必须分别缺失或为字符串数组。OpenSpec CLI 健康门禁 SHALL 归属 pre-check，rule-config 不重复验证 CLI。既有 `openspec/config.yaml` 无法可靠解析或目标字段结构/类型不兼容、无法无损规范化时，两模式 MUST 先归档原文件，归档成功后以模板内容原子替换原位并报告，不经用户决策；归档失败时 MUST 终止且原文件保持不变。

#### Scenario: 空项目直接发布候选

- **WHEN** 目标项目不存在 openspec/config.yaml 且不存在任何 OpenSpec change
- **THEN** 脚本 MUST 以模板构建候选，经解析与结构预检通过后原子创建
- **AND** 全程 SHALL NOT 创建临时 Change 或调用 `openspec instructions`

#### Scenario: 结构不兼容失败关闭

（语义更新：原"普通模式保留并报告 / no-interrupt 备份后终止"行为废止；两模式统一为归档+模板整体替换，仅归档失败保持失败关闭。）

- **WHEN** 已有 config.yaml 的目标字段结构或类型不兼容，或 YAML 无法可靠解析
- **THEN** 两模式 MUST 先将原文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以模板内容原子替换原位，并在报告中记录该替换
- **AND** 归档失败时 MUST 终止且原文件保持不变
- **AND** 处理 MUST 不经用户决策

## REMOVED Requirements

### Requirement: dry-run 冲突报告标注 no-interrupt 真实动作

**Reason**: 框架受管内容 drift 全部转为两模式确定性动作后，dry-run 计划不再产生 drift 冲突条目，`no_interrupt_action` 标注失去载体。

**Migration**: 实际执行动作以报告 `steps[].actions[]` 的 `overwritten` / `authoritative-overwrite` / `replaced` 等条目为准；Agent 汇报 drift 处理结果时 SHALL 依据这些动作条目而非冲突条目。
