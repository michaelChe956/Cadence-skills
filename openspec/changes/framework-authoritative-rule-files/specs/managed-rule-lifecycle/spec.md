## MODIFIED Requirements

### Requirement: 完整协作规则必须有框架规范源
系统 SHALL 在 `cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md` 维护 OpenSpec 与 Superpowers 完整协作规则，并 MUST 由 `rule-config` 将其生成到业务项目的 `.claude/rules/openspec-superpowers-workflow.md`。系统 MUST 按检测到的项目类型选择唯一的代码使用规则来源模板，并 MUST 始终以 `code-usage.md` 作为落地文件名，SHALL NOT 同时生成多个代码使用规则文件或使用带项目类型后缀的落地名。L0 受管区块的规范源 MUST 仅用于插入 `CLAUDE.md` 与 `AGENTS.md`，MUST NOT 作为受管规则文件复制到 `.claude/rules/`。

#### Scenario: 初始化后的业务项目生成协作规则
- **WHEN** 已安装 OpenSpec 与 Superpowers 的业务项目运行 `rule-config`
- **THEN** 项目获得完整协作规则以及指向该规则的 L0 路由
- **AND** 该流程不重复安装 OpenSpec 或 Superpowers

#### Scenario: 当前仓库同步框架副本
- **WHEN** Cadence 维护者修改完整协作规则
- **THEN** 先修改 `cadence-init` 中的规范源
- **AND** 再从规范源同步当前仓库的 `.claude/rules/` 副本

#### Scenario: 非 Coding 项目仍获得代码阅读规则
- **WHEN** `rule-config` 将目标识别为非 Coding 项目
- **THEN** 系统仍 MUST 生成 `.claude/rules/code-reading.md` 和入口摘要，确保 L0 不产生悬空引用
- **AND** 系统 SHALL 只跳过 CodeGraph 安装与初始化，不得跳过代码阅读规则文件

#### Scenario: 代码使用规则按项目类型单选来源
- **WHEN** `rule-config` 完成项目类型检测并生成规则文件
- **THEN** 系统 MUST 只生成一个 `.claude/rules/code-usage.md`，其内容来自与该项目类型对应的来源模板
- **AND** `.claude/rules/` 下 MUST NOT 出现带项目类型后缀的代码使用规则文件
- **AND** 入口文件与 L0 受管区块对代码使用规则的引用 MUST 指向实际存在的 `code-usage.md`

#### Scenario: L0 插入源不复制为规则文件
- **WHEN** `rule-config` 在目标项目执行完成
- **THEN** `.claude/rules/` 下 MUST NOT 存在 L0 受管区块插入源的副本

### Requirement: L0 入口内容必须版本化且可安全升级
系统 MUST 使用稳定开始标记、结束标记和版本号维护 `CLAUDE.md` 与 `AGENTS.md` 中的 L0 受管区块；重复运行 `rule-config` 时 SHALL 只更新受管区块并保留区块外内容。当前 v1 开始和结束标记成对存在、但完整受管区块与规范源当前 v1 不一致时，系统 MUST 将其视为无法识别的本地修改，不得静默覆盖。一次 `rule-config` 处理两个入口时，系统 MUST 在写入任一入口前统一预检 `CLAUDE.md` 与 `AGENTS.md` 的状态和全部必要备份，并 MUST 仅在本次所需的全部 L0 备份成功后开始写入。本要求所述备份 MUST 采用复制原文件到 `cadence/legacy/<14 位时间戳>/<相对项目根路径>` 的形式，随后以 `atomic_write` 原子替换原位文件；备份复制失败时该入口 MUST 保持原样，`atomic_write` 失败时原文件 MUST 因原子替换语义保持运行前内容不变。

#### Scenario: 升级已有受管区块
- **WHEN** 已初始化项目重新运行包含新版路由的 `rule-config`
- **THEN** 系统将旧版 L0 替换为新版 L0
- **AND** 保留项目技术栈、命令、业务说明和用户自定义章节

#### Scenario: 重复运行同一版本
- **WHEN** 项目已包含当前版本 L0 且内容与规范源一致
- **THEN** 系统跳过写入
- **AND** 不重复插入或改写受管区块内容

#### Scenario: 当前 v1 受管区块存在内容漂移
- **WHEN** 入口文件包含成对的当前 v1 标记，但完整受管区块内容与规范源当前 v1 不一致
- **THEN** 系统 MUST 将该区块视为无法识别的本地修改
- **AND** 普通模式 SHALL 询问是否替换；无响应时 MUST 保留原区块并报告
- **AND** 普通模式确认替换时 MUST 将该入口纳入本次 L0 备份屏障，并 SHALL 仅在全部必要备份成功后替换
- **AND** `no-interrupt` 模式 MUST 先将原入口文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以规范源当前 v1 原子替换原位并报告
- **AND** 两种模式均 MUST 保持受管区块外内容原样

#### Scenario: L0 备份失败
- **WHEN** 任一入口的 L0 归档失败
- **THEN** 系统 MUST 立即终止本次 L0 更新
- **AND** 系统 SHALL NOT 写入 `CLAUDE.md` 或 `AGENTS.md` 中的任一 L0
- **AND** 两个入口的受管区块和区块外内容均 MUST 保持原样

#### Scenario: 双入口统一预检和备份屏障
- **WHEN** 一次 `rule-config` 需要同时处理 `CLAUDE.md` 与 `AGENTS.md`
- **THEN** 系统 MUST 在写入任一入口前识别两个入口各自的标记、版本、完整内容和备份需求
- **AND** 系统 MUST 在写入任一入口前成功创建本次所需的全部 L0 归档
- **AND** 仅在统一预检和全部必要归档成功后，系统 SHALL 按各入口对应分支执行写入
- **AND** 写入后两个入口 MUST 使用相同 L0 版本并保持语义等价

### Requirement: L1 框架规则升级必须保护无法识别的本地内容
系统 SHALL 为 L1 框架规则记录可识别版本并按完整文件内容识别已知框架版本。版本标记 MUST 只用于定位候选框架版本；系统 MUST 仅在完整文件内容与该候选已知版本规范逐字一致时，才将文件识别为当前或受支持旧版。当前 v1 标记存在但完整内容与当前框架 v1 不一致，或受支持旧版本标记存在但完整内容与对应已知旧版规范不一致时，系统 MUST 将其归入“与任何已知框架版本不匹配”。普通模式 SHALL 询问是否替换，无响应时 MUST 保留原文件并报告；无响应分支不覆盖原文件，因此不要求创建额外备份。`no-interrupt` 模式 MUST 先创建可恢复备份，备份成功后 SHALL 替换为当前框架 v1 并报告。任何需要 L1 备份的分支 MUST 在备份成功后才能替换；备份失败时 MUST 终止且 SHALL NOT 替换原文件。本要求所述可恢复备份 MUST 采用复制原文件到 `cadence/legacy/<14 位时间戳>/<相对项目根路径>` 的形式，随后以 `atomic_write` 原子替换原位文件；`atomic_write` 失败时原文件 MUST 因原子替换语义保持运行前内容不变。

#### Scenario: 识别到旧版框架规则
- **WHEN** 目标项目的协作规则具有受支持的旧版本标记，且完整文件内容与该受支持旧版规范逐字一致
- **THEN** `rule-config` MUST 先将原文件复制归档到 `cadence/legacy/`
- **AND** 仅在归档成功后 SHALL 以当前版本原子替换原位并报告

#### Scenario: 旧版本标记匹配但完整内容漂移
- **WHEN** 目标协作规则具有受支持的旧版本标记，但完整文件内容与该标记对应的已知旧版规范不一致
- **THEN** `rule-config` MUST 将其视为与任何已知框架版本不匹配的未知本地修改
- **AND** 普通模式 SHALL 询问是否替换；无响应时 MUST 保留原文件并报告
- **AND** `no-interrupt` 模式 MUST 先将原文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以当前框架 v1 原子替换原位并报告

#### Scenario: 当前 v1 标记存在但完整内容漂移
- **WHEN** 目标协作规则包含当前 v1 标记，但完整文件内容与当前框架 v1 不一致
- **THEN** `rule-config` MUST 将其视为与任何已知框架版本不匹配
- **AND** 普通模式 SHALL 询问是否替换；无响应时 MUST 保留原文件并报告
- **AND** `no-interrupt` 模式 MUST 先将原文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以当前框架 v1 原子替换原位并报告

#### Scenario: 发现其他未知本地修改
- **WHEN** 目标协作规则无标记、版本未知或完整内容与任何已知框架版本均不匹配
- **THEN** 普通模式 SHALL 询问是否替换；无响应时 MUST 保留原文件并报告
- **AND** `no-interrupt` 模式 MUST 先将原文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以当前框架 v1 原子替换原位并报告

#### Scenario: L1 备份失败
- **WHEN** 受支持旧版本升级或未知本地修改处理等任意 L1 分支要求创建归档，但归档失败
- **THEN** `rule-config` MUST 立即终止该次 L1 更新
- **AND** `rule-config` SHALL NOT 替换或改变原协作规则文件
