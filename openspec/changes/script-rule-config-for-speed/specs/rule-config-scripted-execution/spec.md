## Purpose

将 rule-config 的全部确定性文件操作收敛到一个 python 脚本中两阶段执行，Agent 只负责调用脚本、中转普通模式提问和解读 JSON 报告，使端到端初始化在保留全部合并、备份与失败关闭语义的前提下达到分钟级耗时。

## ADDED Requirements

### Requirement: 脚本两阶段执行与模式衔接
系统 MUST 提供单一脚本执行体，支持 `dry-run` 与 `apply` 两个阶段。`dry-run` SHALL 只读检测并输出包含每资产动作、冲突清单和备份需求的 JSON 计划，不得写入任何目标文件；`apply` SHALL 执行全部动作并输出 JSON 报告。no-interrupt 模式 MUST 在一次 `apply` 调用内完成检测、冲突的权威规则自动决策与执行；普通模式存在冲突时，Agent MUST 在 `dry-run` 之后按现行提问规则逐条询问用户（每次一问、给推荐默认项），并将决策以决策文件传入 `apply`。脚本 CLI MUST 提供用户意图参数：显式项目类型指定、要求忽略 `cadence/`、要求启用 Playwright、要求启用 CodeGraph，分别对应现行 SKILL 中用户明确指定或要求的分支。

#### Scenario: no-interrupt 一把执行
- **WHEN** Agent 以 no-interrupt 模式调用脚本 `apply`
- **THEN** 脚本内部完成检测与冲突自动决策并执行全部动作
- **AND** Agent 全程不 Read/Write 任何目标项目文件，只调用脚本并解读报告

#### Scenario: 普通模式冲突经用户决策
- **WHEN** 普通模式 `dry-run` 计划中存在需用户决策的冲突
- **THEN** Agent SHALL 逐条询问用户（每次一问、给推荐默认项）
- **AND** 用户决策 MUST 以决策文件传入 `apply`，脚本按决策执行
- **AND** 决策缺失、包含未知或重复冲突标识、或与 `apply` 时新鲜计划不符时，脚本 MUST 失败关闭、非零退出、写出报告且零写入，不得按默认猜测执行
- **AND** 上述「决策缺失即失败关闭」仅适用于无安全默认的冲突（如规则文件 drift、L0 drift 等必须显式决策方可继续的类型）；对具备安全默认的冲突（`rules.apply` / `structure` / `unparseable` 这类「无响应则保留并报告」的合并矩阵条目），决策缺失时脚本 SHALL 按安全默认（keep / 保留原文件并报告）继续，不视为失败关闭；该例外 MUST 在计划冲突条目以 `default_keep: true` 显式标注，未标注的冲突缺失仍 MUST 失败关闭

#### Scenario: dry-run 零写入
- **WHEN** 脚本以 `dry-run` 运行
- **THEN** 目标项目任何文件 MUST 保持运行前后内容一致
- **AND** 输出的计划 MUST 列出每个资产的动作类型、冲突项和备份需求

#### Scenario: 用户意图参数透传
- **WHEN** 用户在命令中明确指定项目类型、要求忽略 `cadence/` 或要求启用 Playwright
- **THEN** Agent MUST 将对应意图作为 CLI 参数传给脚本
- **AND** 显式项目类型 MUST 优先于自动检测结果，`--ignore-cadence` 时 SHALL 将 `cadence/` 追加到 `.gitignore`，`--enable-playwright` 时 SHALL 创建 Playwright 规则与摘要

#### Scenario: 检测结果矛盾的保守默认
- **WHEN** 项目类型检测结果互相矛盾且会影响规则选择
- **THEN** 普通模式 SHALL 询问用户；无响应时 Agent MUST 将 `non-coding` 决策写入决策文件再 apply
- **AND** 该冲突 SHALL 仅在普通模式以冲突标识 `s1:project-type-conflict` 进入决策文件，枚举值为 `coding|non-coding`
- **AND** no-interrupt 模式 MUST 内部按 `non-coding` 保守决策继续，并在报告中记录该冲突标识与所采用的决策

#### Scenario: 非 Coding 项目显式启用 CodeGraph
- **WHEN** 用户明确要求启用 CodeGraph 但项目未检测到源码
- **THEN** Agent SHALL 以 `--enable-codegraph` 传入脚本，脚本 MUST 执行 codegraph 步骤
- **AND** 项目类型相关的其他语义（规则 2 文本、默认角色等）MUST 保持非 Coding 项目取值不变

### Requirement: 合并与保护语义脚本内确定性实现
系统 MUST 在脚本内实现现行全部合并与保护语义，且普通模式与 no-interrupt 的动作空间不同：no-interrupt 对冲突规则文件按章节级权威规则合并（同名章节以标题级别加去编号标题文本识别、模板在前、项目独有章节按原序保留、同名章节项目内容去重后进入项目补充）；普通模式对冲突规则文件 SHALL 询问用户，无响应或拒绝时 MUST NOT 覆盖，跳过并报告。L0 受管区块的插入/升级/替换与双入口统一预检备份屏障、L1 框架规则的完整内容比对与备份升级、OpenSpec config.yaml 的保守合并去重、时间戳备份屏障与同文件系统原子发布 MUST 按现行语义执行。任何必要备份失败时 MUST 整体终止且保持原文件不变。

#### Scenario: no-interrupt 下已有项目规则被合并而非覆盖
- **WHEN** 目标项目已存在与模板冲突的规则文件并以 no-interrupt 运行
- **THEN** 脚本 MUST 先创建时间戳备份再按章节级权威规则合并
- **AND** 项目独有章节和同名章节的项目补充内容 MUST 保留

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

### Requirement: 项目配置产物与现行语义一致
脚本 MUST 保留现行项目配置相关产物语义：技术栈与包管理器检测（语言、测试/检查/格式化命令，未检出写"未检测到"）并写入口文件项目配置章节；入口文件 MUST 写入包管理器规则（前端使用 pnpm、Python 使用 uv，禁止 npm/pip/yarn）与默认覆盖率阈值 80%；历史产物目录仅检测现行精确目录集合，no-interrupt 模式 MUST 只写入报告且 SHALL NOT 执行移动、合并、删除或清理，普通模式 SHALL 按现行迁移表处理且目标目录非空时跳过并报告冲突；`cadence/` 默认不加入 `.gitignore`；`.codegraph/` 在 Coding 项目或 `--enable-codegraph` 时 SHALL 加入 `.gitignore`，`codegraph.json` MUST NOT 加入；Playwright 规则默认跳过。

#### Scenario: 技术栈检测写入入口
- **WHEN** 项目存在 package.json 等主工程配置
- **THEN** 脚本 SHALL 提取语言与可用脚本命令写入口文件项目配置章节
- **AND** 未检测到的命令 MUST 写为"未检测到"，不阻塞初始化

#### Scenario: no-interrupt 历史目录只报告
- **WHEN** no-interrupt 模式检测到历史产物目录
- **THEN** 脚本 MUST 仅在报告中列出检测到的目录
- **AND** SHALL NOT 执行 `mv`、目录内容合并、目录删除或空目录清理

#### Scenario: 普通模式历史目录无冲突迁移
- **WHEN** 普通模式检测到历史目录且目标 `cadence/<dir>` 不存在或为空
- **THEN** 脚本 SHALL 按现行迁移表迁移
- **AND** 目标非空时 MUST 跳过该目录并报告冲突，不覆盖、不合并

### Requirement: OpenSpec 配置验证以结构预检取代 instructions 验证
系统 MUST NOT 再创建临时验证工作区、临时 Change 或执行 `openspec instructions` 来验证候选配置。候选 config.yaml 发布前 MUST 通过真实 YAML parser 的语法解析与结构预检：根必须为映射、`schema` 必须缺失或为标量、`context` 必须缺失或为字符串、`rules` 必须缺失或为映射、四个 artifact 规则必须分别缺失或为字符串数组。OpenSpec CLI 健康门禁 SHALL 归属 pre-check，rule-config 不重复验证 CLI。

#### Scenario: 空项目直接发布候选
- **WHEN** 目标项目不存在 openspec/config.yaml 且不存在任何 OpenSpec change
- **THEN** 脚本 MUST 以模板构建候选，经解析与结构预检通过后原子创建
- **AND** 全程 SHALL NOT 创建临时 Change 或调用 `openspec instructions`

#### Scenario: 结构不兼容失败关闭
- **WHEN** 已有 config.yaml 的目标字段结构或类型不兼容
- **THEN** 普通模式 MUST 保留原文件并报告字段路径与实际类型
- **AND** no-interrupt 模式 MUST 先备份，无法证明可无损规范化时终止且原文件不变

### Requirement: JSON 报告与失败关闭
脚本 MUST 输出结构化 JSON 报告，包含总体状态、模式、项目类型、各步骤状态与耗时、每资产动作明细、备份路径、冲突处理结果和失败恢复建议；codegraph 步骤耗时 MUST 单独列出并标注不计入初始化预算；报告 MUST 包含规范字段 `hints.next: "mcp-configuration"`，Agent 汇报后 MUST 据此将配置结果交接给 mcp-configuration 流程。任一步骤失败 MUST 使报告停在失败项并附失败文件、原因与恢复建议；**唯一例外**是 codegraph 步骤中 `install`/`init`/`status` 子命令失败，可按 degraded 降级继续，但 S8 内的配置补写、备份与原子写失败仍 MUST 终止。PyYAML 缺失时脚本 MUST 以专属退出码退出并仍写出报告，供 Agent 以 uvx 兜底重跑。Agent MUST 依据报告如实汇报，缺少成功证据时不得声称完成。

#### Scenario: 报告区分幂等跳过与实际变更
- **WHEN** 在已初始化项目上重复运行脚本
- **THEN** 报告 MUST 将未变化资产标记为幂等跳过
- **AND** Agent 汇报时 MUST NOT 把跳过说成新建或合并

#### Scenario: codegraph 已初始化状态幂等
- **WHEN** `.codegraph/` 已存在，或 `.mcp.json` 与 `.codex/config.toml` 均已包含 CodeGraph MCP
- **THEN** 脚本 MUST 按现行 CodeGraph 增量状态矩阵处理：`.codegraph/` 已存在时只运行 `codegraph status` 不重复 init，双配置齐全时不重复写入
- **AND** 任一配置文件缺少 CodeGraph MCP 时 MUST 先执行 `codegraph install --target=claude,codex --location=local --yes`，再核验并仅补齐仍缺失的一方
- **AND** `.codegraph/` 不存在时 MUST 执行 install 与 init

#### Scenario: codegraph install 失败仍补齐双配置
- **WHEN** `codegraph install` 失败
- **THEN** 脚本 MUST 按兜底配置自动补齐 `.mcp.json` 与 `.codex/config.toml` 的 CodeGraph MCP 配置
- **AND** 该步骤 MUST 标记为 degraded 且整体流程继续

#### Scenario: codegraph init/status 失败不阻断
- **WHEN** `codegraph init` 或 `codegraph status` 失败
- **THEN** 该步骤 MUST 标记为 degraded 且整体流程继续
- **AND** 报告 SHALL 给出项目语言、目录规模提示与手动兜底配置

### Requirement: 端到端耗时预算
在 Claude Code 真实环境的空项目上，以 no-interrupt 模式执行完整 rule-config 流程，从 Skill 触发到最终汇报完成的端到端耗时 MUST 不超过 5 分钟，计算时 SHALL 只扣除 codegraph 步骤（S8，含 install 与 init）的实际耗时区间；codegraph 初始化 MUST 保持同步执行不得异步化。脚本报告 MUST 另提供脚本级代理指标 `budget_seconds_excluding_codegraph`（计时起点为脚本入口、终点为 OpenSpec 配置步骤完成），用于 CI 中的预算回归断言。

#### Scenario: 空项目预算验收
- **WHEN** 在空项目上以 no-interrupt 模式执行完整 rule-config 流程
- **THEN** 从 Skill 触发到最终汇报完成、扣除 S8 实际耗时后的端到端耗时 MUST 在 5 分钟内
- **AND** 报告 MUST 分别给出脚本级预算计时与 codegraph 步骤计时
