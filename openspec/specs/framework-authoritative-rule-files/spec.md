# framework-authoritative-rule-files Specification

## Purpose
定义框架受管规则文件的权威覆盖语义：哪些资产由框架模板整体决定内容、哪些保留原有合并语义、被替换的原文件如何归档到 `cadence/legacy/`，以及重复执行 `rule-config` 必须产出一致结果的幂等契约。

术语定义：`cadence/legacy/` 是 rule-config 产生的被动恢复归档目录，仅用于存放被覆盖前的原文件副本，不属于 legacy 工作流插件遗留框架；协作路由与运行不依赖其中内容，与 `managed-rule-lifecycle` 中“规则层集成不得依赖 legacy”的 legacy（指任何 legacy 工作流插件）无关。

## Requirements

### Requirement: 受管资产必须按三类策略分别处理

系统 MUST 将 `rule-config` 处理的资产划分为三类并按对应策略处理，SHALL NOT 对不同类别混用策略。框架受管规则文件类 MUST 按框架模板权威覆盖，不保留项目改写内容；版本化特例类 MUST 保留基于完整内容的版本识别与升级语义，其内容 drift 或与任何已知框架版本不匹配的状态 MUST 在归档后替换为当前框架版本，普通模式与 no-interrupt 模式同动作、不经用户决策；保留原语义类 MUST 保持受管区块替换或保守合并语义，`openspec/config.yaml` 可解析且结构兼容时 MUST NOT 整体覆盖，无法可靠解析或目标字段结构/类型不兼容、无法无损规范化时 MUST 归档原文件后以模板整体替换，两模式同动作、不经用户决策。

框架权威全覆盖适用于且仅适用于 `.claude/rules/` 下以下文件：`mcp-servers.md`、`code-reading.md`、`document-storage.md`、`language.md`、`markdown-format.md`、`code-usage.md`、`playwright.md`（其中 `playwright.md` 仅在用户启用 Playwright 时创建，已存在时 drift 按全覆盖处理）。系统 MUST NOT 对项目自定义规则文件、`openspec-superpowers-workflow.md`（L1）、`agent-routing-kernel.md`（L0 插入源）或 `cadence/project-rules/` 下任何文件执行权威全覆盖。

#### Scenario: 框架受管规则文件按权威覆盖处理

- **WHEN** `rule-config` 处理 `.claude/rules/` 下的框架受管规则文件
- **THEN** 系统 MUST 以框架模板内容为该文件的目标内容
- **AND** 系统 SHALL NOT 产生 `**项目补充**` 段落或保留项目独有章节
- **AND** 系统 SHALL NOT 因项目侧存在改写而放弃覆盖

#### Scenario: 项目自定义规则不被覆盖

- **WHEN** `.claude/rules/` 下存在不在框架受管清单内的文件（如项目自建规则）
- **THEN** 系统 MUST NOT 对其执行权威全覆盖
- **AND** 该文件 MUST 保持原样

#### Scenario: 协作规则保持版本化特例

- **WHEN** `rule-config` 处理 `.claude/rules/openspec-superpowers-workflow.md`
- **THEN** 系统 MUST 保留按完整文件内容识别已知框架版本的语义
- **AND** 系统 MUST NOT 在未完成版本识别的情况下将其降级为无版本识别的整体覆盖
- **AND** 识别为内容 drift 或与任何已知版本不匹配时，系统 MUST 归档后替换为当前框架版本，普通模式与 no-interrupt 模式同动作、不经用户决策

#### Scenario: 入口文件与 OpenSpec 配置不被整体覆盖

- **WHEN** `rule-config` 处理 `CLAUDE.md`、`AGENTS.md` 或可解析且结构兼容的 `openspec/config.yaml`
- **THEN** 系统 MUST 只更新受管区块或按保守合并语义处理
- **AND** 系统 MUST 保留受管区块外的项目内容与配置中的项目自定义字段
- **AND** `openspec/config.yaml` 无法可靠解析或结构/类型不兼容的情形 MUST 按下述独立场景处理，不适用本场景

#### Scenario: 无法无损规范化的 OpenSpec 配置归档后整体替换

- **WHEN** 既有 `openspec/config.yaml` 无法可靠解析，或目标字段结构/类型不兼容导致无法无损规范化
- **THEN** 系统 MUST 先将原文件复制归档到 `cadence/legacy/`
- **AND** 归档成功后 SHALL 以模板内容原子替换原位并报告
- **AND** 归档失败时 MUST 终止且原文件保持不变
- **AND** 普通模式与 no-interrupt 模式 MUST 执行相同动作，不经用户决策

### Requirement: 被替换的原文件必须归档到 cadence/legacy 且不纳入版本控制
系统 MUST 在覆盖或替换受管文件前，将原文件复制到 `cadence/legacy/<14 位时间戳>/<相对项目根路径>`，随后以 `atomic_write` 原子替换原位文件。归档路径 MUST 保留原文件的相对路径结构，使同一文件的多次归档互不覆盖。同秒内同一文件的重复归档 MUST 通过在时间戳目录后追加 `-2`/`-3` 后缀（形如 `<时间戳>-2/<相对路径>`）唯一化。系统 MUST 在 `cadence/legacy/` 内创建 `.gitignore`，内容为忽略该目录全部条目但显式保留 `.gitignore` 自身（`*` 换行 `!.gitignore`）。每次运行归档前系统 MUST 验证该 `.gitignore` 存在且内容正确，缺失或损坏时 MUST 修复。归档复制失败时系统 MUST 终止本次写入且 SHALL NOT 修改原文件；`atomic_write` 失败时原文件 MUST 因原子替换语义保持运行前内容不变，已归档副本保留供恢复，此时系统 MUST NOT 称成功。归档文件不纳入版本控制，`.gitignore` 本身可纳入版本控制。

#### Scenario: 覆盖前归档原文件
- **WHEN** 某受管规则文件内容与框架模板不一致，系统准备以模板覆盖
- **THEN** 系统 MUST 先将原文件复制到 `cadence/legacy/<时间戳>/` 下的对应相对路径
- **AND** 仅在复制成功后 SHALL 以模板内容 `atomic_write` 原子替换原位
- **AND** 归档结果 MUST 出现在执行报告中

#### Scenario: 归档目录不纳入版本控制
- **WHEN** 系统首次创建 `cadence/legacy/`
- **THEN** 系统 MUST 在该目录内创建 `.gitignore`，内容忽略全部条目但保留 `.gitignore` 自身
- **AND** 该归档目录 SHALL NOT 因后续运行被纳入版本控制

#### Scenario: 归档 .gitignore 损坏时修复
- **WHEN** 运行时发现 `cadence/legacy/.gitignore` 缺失或内容不符合规范
- **THEN** 系统 MUST 在归档前修复为规范内容
- **AND** 修复 MUST NOT 删除已存在的归档文件

#### Scenario: 同一文件多次归档互不覆盖
- **WHEN** 同一受管文件在不同时间的多次运行中均被覆盖
- **THEN** 每次归档 MUST 位于各自时间戳目录下，彼此不覆盖
- **AND** 同一秒内的重复归档 MUST 通过 `-2`/`-3` 后缀区分，不丢失先前归档

#### Scenario: 归档失败即终止
- **WHEN** 归档复制因权限或文件系统错误失败
- **THEN** 系统 MUST 立即终止该文件的写入
- **AND** 原文件 MUST 保持原样
- **AND** 报告 MUST 包含失败路径、失败原因与恢复建议

#### Scenario: 原子覆盖失败不破坏原文件
- **WHEN** 归档成功后 `atomic_write` 原子替换原位失败
- **THEN** 原文件 MUST 保持运行前内容不变
- **AND** 已归档副本 SHALL 保留在 `cadence/legacy/` 供恢复
- **AND** 系统 MUST NOT 称该文件处理成功

### Requirement: 代码使用规则必须按项目类型单选来源且落地名恒定
系统 MUST 依据检测到的项目类型选择唯一的代码使用规则来源模板，并 MUST 始终以 `code-usage.md` 作为落地文件名。系统 SHALL NOT 同时生成多个代码使用规则文件，也 SHALL NOT 使用带项目类型后缀的落地文件名。两个来源模板语义互斥，系统 MUST NOT 将其内容相互合并。执行完成后 `.claude/rules/` 下 MUST NOT 存在历史框架产物 `code-usage-coding.md` 或 `code-usage-noncoding.md`；对运行时发现这两个精确文件名的既有文件，系统 MUST 先归档到 `cadence/legacy/` 再从原位移除，归档失败时 MUST 终止且不删除原文件。系统 MUST NOT 移除或归档这两个精确文件名以外的任何 `code-usage-*` 文件（项目自定义规则不在迁移范围）。

#### Scenario: Coding 项目生成编码规范
- **WHEN** `rule-config` 将目标识别为 Coding 项目
- **THEN** 系统 MUST 以编码项目模板内容生成 `.claude/rules/code-usage.md`
- **AND** 系统 SHALL NOT 生成非 Coding 项目的代码使用规则文件

#### Scenario: 非 Coding 项目生成非必要不编写代码规范
- **WHEN** `rule-config` 将目标识别为非 Coding 项目
- **THEN** 系统 MUST 以非 Coding 模板内容生成 `.claude/rules/code-usage.md`
- **AND** 系统 SHALL NOT 生成编码项目的代码使用规则文件

#### Scenario: 项目类型变化时按类型权威覆盖
- **WHEN** 已存在的 `code-usage.md` 内容来自与当前检测类型不符的来源模板
- **THEN** 系统 MUST 归档原文件后以当前类型对应模板原子覆盖原位
- **AND** 系统 SHALL NOT 将两类互斥规则合并进同一文件

#### Scenario: 迁移历史带后缀文件
- **WHEN** 运行时发现 `.claude/rules/` 下存在精确文件名 `code-usage-coding.md` 或 `code-usage-noncoding.md` 的历史框架产物
- **THEN** 系统 MUST 先将其归档到 `cadence/legacy/`
- **AND** 仅在归档成功后 SHALL 从原位移除
- **AND** 归档或移除失败时 MUST 终止该文件处理且原文件保持原样

#### Scenario: 项目自定义 code-usage 文件不被迁移
- **WHEN** `.claude/rules/` 下存在这两个精确文件名以外的 `code-usage-*` 文件（如项目自建的 `code-usage-extra.md`）
- **THEN** 系统 MUST NOT 对其归档或移除
- **AND** 该文件 MUST 保持原样

#### Scenario: 入口引用不产生悬空链接
- **WHEN** `rule-config` 完成执行
- **THEN** 入口文件与 L0 受管区块中对代码使用规则的引用 MUST 指向实际存在的 `.claude/rules/code-usage.md`

### Requirement: L0 受管区块插入源不得作为规则文件复制
系统 MUST 将 L0 受管区块的规范源仅用于插入 `CLAUDE.md` 与 `AGENTS.md`，并 MUST NOT 将其作为受管规则文件复制到 `.claude/rules/`。

#### Scenario: 初始化后不产生多余规则文件
- **WHEN** `rule-config` 在目标项目执行完成
- **THEN** `.claude/rules/` 下 MUST NOT 存在 L0 受管区块插入源的副本
- **AND** `CLAUDE.md` 与 `AGENTS.md` 中的 L0 受管区块内容 MUST 与规范源一致

### Requirement: 重复执行必须产出一致结果
系统 MUST 保证在项目输入未变化的前提下，连续多次执行 `rule-config` 的产物完全一致。所有受管资产的写入 MUST 采用"先归一化到目标内容再比对"的语义，MUST NOT 采用无条件追加。当资产内容已等于目标内容时，系统 MUST 跳过写入且 MUST NOT 产生归档。

#### Scenario: 第二次执行不改变任何产物
- **WHEN** 在同一项目连续执行 `rule-config` 两次且期间项目未被修改
- **THEN** 第二次执行后全部受管文件内容 MUST 与第一次执行后逐字一致
- **AND** 第二次执行 MUST NOT 在 `cadence/legacy/` 产生新的归档目录或条目
- **AND** 报告 MUST 将未变化的资产标记为跳过

#### Scenario: drift 覆盖后重跑不归档
- **WHEN** 首次执行对某框架规则文件 drift 进行了权威覆盖并归档，随后在内容未变时第二次执行
- **THEN** 第二次执行 MUST 跳过该文件写入
- **AND** 第二次执行 MUST NOT 为该文件产生新归档

#### Scenario: 项目类型切换后重跑稳定
- **WHEN** 项目类型从 A 切换到 B 触发 `code-usage.md` 权威覆盖，随后类型稳定在 B 时再次执行
- **THEN** 再次执行 MUST 跳过 `code-usage.md` 写入
- **AND** MUST NOT 产生新归档

#### Scenario: 摘要引用不重复追加
- **WHEN** 入口文件的强制规则章节已存在指向某规则文件的摘要引用（无论措辞是否与模板一致，只要指向同一规则文件名即视为已存在）
- **THEN** 系统 MUST 判定该摘要已存在并跳过追加
- **AND** 系统 MUST NOT 因措辞与模板不同而重复追加同一规则文件的摘要
- **AND** 同一规则文件在强制规则章节中 MUST 只被引用一次

#### Scenario: 受管区块重复执行保持稳定
- **WHEN** 入口文件的 L0 受管区块内容已与规范源一致
- **THEN** 系统 MUST 跳过该区块写入
- **AND** 受管区块外的项目内容 MUST 保持逐字不变

### Requirement: 技术栈信息必须补全占位而不覆盖用户填写内容
系统 MUST 逐项处理入口文件中的项目技术栈信息。占位值集合固定为 `{"待确认", "未检测到"}`，空值视为占位。当某项为占位值时，系统 MUST 以当前检测值替换；当某项为用户填写的非占位真实值时，系统 MUST 保留该值且 MUST NOT 以检测值覆盖。技术栈区块整体缺失时系统 MUST 写入完整区块。未检测到的项系统 MUST 写为"未检测到"，重复执行时该值与检测值一致 MUST 保持不变。

#### Scenario: 占位值被替换为检测值
- **WHEN** 入口文件技术栈某项为占位值（`待确认`、`未检测到` 或空），且系统检测到该项的具体值
- **THEN** 系统 MUST 将该项替换为检测值

#### Scenario: 用户填写的值被保留
- **WHEN** 入口文件技术栈某项为用户填写的非占位真实值
- **THEN** 系统 MUST 保留该值不变
- **AND** 当检测值与该值不同时，系统 SHALL 仅在报告中提示差异

#### Scenario: 未检测到的项保持占位
- **WHEN** 系统无法检测某技术栈项且该项当前为占位值
- **THEN** 该项 MUST 保持为"未检测到"
- **AND** 重复执行 MUST NOT 反复改写该项
