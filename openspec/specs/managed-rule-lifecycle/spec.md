# managed-rule-lifecycle Specification

## Purpose
TBD - created by archiving change improve-progressive-disclosure-routing. Update Purpose after archive.

## Requirements

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

系统 MUST 使用稳定开始标记、结束标记和版本号维护 `CLAUDE.md` 与 `AGENTS.md` 中的 L0 受管区块；重复运行 `rule-config` 时 SHALL 只更新受管区块并保留区块外内容。当前版本开始和结束标记成对存在、但完整受管区块与规范源当前版本不一致时，系统 MUST 将其视为本地修改，并在归档成功后以规范源当前版本原子替换，普通模式与 no-interrupt 模式同动作、不经用户决策；归档副本使本地修改可回滚。受支持旧版本（含 v0 与 v1）标记成对存在且完整内容与对应旧版规范一致时，系统 MUST 执行确定性升级：两模式同动作、不经用户决策，将旧版区块替换为规范源当前版本并保留区块外内容。任何插入/升级/替换完成后，入口文件 MUST 恰好包含一个当前版本受管区块：成对旧版区块与孤立单侧标记 MUST 先移除再插入规范区块；存在多个完整当前版本区块时 MUST 保留首个并归并其余，且记录 warning。一次 `rule-config` 处理两个入口时，系统 MUST 在写入任一入口前统一预检 `CLAUDE.md` 与 `AGENTS.md` 的状态和全部必要备份，并 MUST 仅在本次所需的全部 L0 备份成功后开始写入。本要求所述备份 MUST 采用复制原文件到 `cadence/legacy/<14 位时间戳>/<相对项目根路径>` 的形式，随后以 `atomic_write` 原子替换原位文件；备份复制失败时该入口 MUST 保持原样，`atomic_write` 失败时原文件 MUST 因原子替换语义保持运行前内容不变。

#### Scenario: 升级已有受管区块

- **WHEN** 已初始化项目重新运行包含新版路由的 `rule-config`
- **THEN** 系统将旧版 L0 替换为新版 L0
- **AND** 保留项目配置、命令、业务说明和用户自定义章节

#### Scenario: v1 区块确定性升级为 v2

- **WHEN** 入口文件包含成对 v1 标记且完整区块内容与 v1 规范源一致，而框架当前版本为 v2
- **THEN** 系统 MUST 不经用户决策将区块升级为 v2 规范源
- **AND** 普通模式与 no-interrupt 模式 MUST 执行相同升级动作
- **AND** 升级后入口文件 MUST 恰好包含一个 v2 受管区块

#### Scenario: 混合标记迁移

- **WHEN** 入口文件同时存在成对旧版区块与孤立的当前版本单侧标记
- **THEN** 系统 MUST 先移除旧版区块对并剥离孤立单侧标记行，再插入一个规范当前版本区块
- **AND** MUST NOT 因检测到当前版本 begin 标记而幂等返回导致区块残留 broken

#### Scenario: 重复当前版本区块归并

- **WHEN** 入口文件存在多个完整当前版本受管区块
- **THEN** 系统 MUST 保留与规范源一致的首个区块并移除其余
- **AND** 记录 warning 报告归并结果

#### Scenario: 重复运行同一版本

- **WHEN** 项目已包含当前版本 L0 且内容与规范源一致
- **THEN** 系统跳过写入
- **AND** 不重复插入或改写受管区块内容

#### Scenario: 当前 v1 受管区块存在内容漂移

（标题为历史命名，「当前版本」现为 v2。语义更新：原「询问、无响应保留」行为废止，两模式统一归档+替换。）

- **WHEN** 入口文件包含成对的当前版本标记，但完整受管区块内容与规范源当前版本不一致
- **THEN** 系统 MUST 将该区块视为本地修改
- **AND** 系统 MUST 将该入口纳入本次 L0 备份屏障，并 SHALL 仅在全部必要备份成功后以规范源当前版本原子替换原位
- **AND** 普通模式与 no-interrupt 模式 MUST 执行相同替换动作，不经用户决策
- **AND** 两种模式均 MUST 保持受管区块外内容原样

#### Scenario: 单侧或顺序错误标记确定性归并

- **WHEN** 入口文件的 L0 标记处于单侧、顺序错误等可安全归并的异常状态
- **THEN** 系统 MUST 在归档成功后将其安全归并为恰好一个当前版本受管区块
- **AND** 普通模式与 no-interrupt 模式 MUST 执行相同归并动作，不经用户决策
- **AND** 归并 MUST NOT 吞掉受管区块内外的用户正文，无法安全归并的内容 MUST 保留并报告

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

系统 SHALL 为 L1 框架规则记录可识别版本并按完整文件内容识别已知框架版本。版本标记 MUST 只用于定位候选框架版本；系统 MUST 仅在完整文件内容与该候选已知版本规范逐字一致时，才将文件识别为当前或受支持旧版。当前 v1 标记存在但完整内容与当前框架 v1 不一致，或受支持旧版本标记存在但完整内容与对应已知旧版规范不一致时，系统 MUST 将其归入"与任何已知框架版本不匹配"。对归入不匹配或无标记的未知本地修改，普通模式与 no-interrupt 模式 MUST 执行相同动作：先创建可恢复备份，备份成功后 SHALL 替换为当前框架 v1 并报告，处理 MUST 不经用户决策；可恢复备份使本地内容可回滚。任何需要 L1 备份的分支 MUST 在备份成功后才能替换；备份失败时 MUST 终止且 SHALL NOT 替换原文件。本要求所述可恢复备份 MUST 采用复制原文件到 `cadence/legacy/<14 位时间戳>/<相对项目根路径>` 的形式，随后以 `atomic_write` 原子替换原位文件；`atomic_write` 失败时原文件 MUST 因原子替换语义保持运行前内容不变。

#### Scenario: 识别到旧版框架规则

- **WHEN** 目标项目的协作规则具有受支持的旧版本标记，且完整文件内容与该受支持旧版规范逐字一致
- **THEN** `rule-config` MUST 先将原文件复制归档到 `cadence/legacy/`
- **AND** 仅在归档成功后 SHALL 以当前版本原子替换原位并报告

#### Scenario: 旧版本标记匹配但完整内容漂移

- **WHEN** 目标协作规则具有受支持的旧版本标记，但完整文件内容与该标记对应的已知旧版规范不一致
- **THEN** `rule-config` MUST 将其视为与任何已知框架版本不匹配的未知本地修改
- **AND** 普通模式与 no-interrupt 模式 MUST 执行相同动作：先将原文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以当前框架 v1 原子替换原位并报告
- **AND** 处理 MUST 不经用户决策

#### Scenario: 当前 v1 标记存在但完整内容漂移

- **WHEN** 目标协作规则包含当前 v1 标记，但完整文件内容与当前框架 v1 不一致
- **THEN** `rule-config` MUST 将其视为与任何已知框架版本不匹配
- **AND** 普通模式与 no-interrupt 模式 MUST 执行相同动作：先将原文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以当前框架 v1 原子替换原位并报告
- **AND** 处理 MUST 不经用户决策

#### Scenario: 发现其他未知本地修改

- **WHEN** 目标协作规则无标记、版本未知或完整内容与任何已知框架版本均不匹配
- **THEN** 普通模式与 no-interrupt 模式 MUST 执行相同动作：先将原文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以当前框架 v1 原子替换原位并报告
- **AND** 处理 MUST 不经用户决策

#### Scenario: L1 备份失败

- **WHEN** 受支持旧版本升级或未知本地修改处理等任意 L1 分支要求创建归档，但归档失败
- **THEN** `rule-config` MUST 立即终止该次 L1 更新
- **AND** `rule-config` SHALL NOT 替换或改变原协作规则文件

### Requirement: Claude Code、Kimi Code 与 Codex 入口必须语义等价
系统 SHALL 允许针对客户端入口语法进行适配，但 MUST 保持任务信号、Skill 顺序、阶段门禁、失败关闭和轻量豁免语义等价。

#### Scenario: Kimi Code 使用 AGENTS 入口
- **WHEN** Kimi Code 读取项目 `AGENTS.md`
- **THEN** 它获得与 Claude Code 从 `CLAUDE.md` 获得的等价路由语义
- **AND** 新功能、直接 apply 和完工声明使用相同门禁

#### Scenario: 客户端语法不同
- **WHEN** 某客户端调用 Skill 的语法与其他客户端不同
- **THEN** 生成入口可以使用该客户端支持的语法
- **AND** 不得删除或改变规范 Skill 的触发顺序

### Requirement: 规则层集成不得依赖 legacy 或运行时状态机
系统 MUST NOT 依赖任何 legacy 工作流插件、Hook、守护进程或“规则是否已读”状态来实现本协作流程。

#### Scenario: 客户端没有 Hook 能力
- **WHEN** 目标客户端没有可用的 SessionStart 或编辑前 Hook
- **THEN** L0、L1 和 L2 仍独立表达完整的路由和门禁

#### Scenario: legacy 工作流插件被移除
- **WHEN** 业务项目不存在或移除任何 legacy 工作流插件
- **THEN** OpenSpec 与 Superpowers 协作规则仍可正常使用
