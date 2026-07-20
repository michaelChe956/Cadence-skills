## ADDED Requirements

### Requirement: 完整协作规则必须有框架规范源
系统 SHALL 在 `cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md` 维护 OpenSpec 与 Superpowers 完整协作规则，并 MUST 由 `rule-config` 将其生成到业务项目的 `.claude/rules/openspec-superpowers-workflow.md`。

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

### Requirement: L0 入口内容必须版本化且可安全升级
系统 MUST 使用稳定开始标记、结束标记和版本号维护 `CLAUDE.md` 与 `AGENTS.md` 中的 L0 受管区块；重复运行 `rule-config` 时 SHALL 只更新受管区块并保留区块外内容。当前 v1 开始和结束标记成对存在、但完整受管区块与规范源当前 v1 不一致时，系统 MUST 将其视为无法识别的本地修改，不得静默覆盖。一次 `rule-config` 处理两个入口时，系统 MUST 在写入任一入口前统一预检 `CLAUDE.md` 与 `AGENTS.md` 的状态和全部必要备份，并 MUST 仅在本次所需的全部 L0 备份成功后开始写入。

#### Scenario: 升级已有受管区块
- **WHEN** 已初始化项目重新运行包含新版路由的 `rule-config`
- **THEN** 系统将旧版 L0 替换为新版 L0
- **AND** 保留项目技术栈、命令、业务说明和用户自定义章节

#### Scenario: 重复运行同一版本
- **WHEN** 同一版本的 `rule-config` 连续运行两次
- **THEN** 第二次运行不产生重复路由、重复引用或额外内容变更

#### Scenario: 当前 v1 受管区块存在内容漂移
- **WHEN** L0 当前 v1 开始和结束标记成对存在，但完整受管区块与规范源当前 v1 不一致
- **THEN** 系统 MUST 将该区块视为无法识别的本地修改
- **AND** 普通模式 SHALL 询问是否替换；无响应时 MUST 保留原区块并报告
- **AND** 普通模式确认替换时 MUST 将该入口纳入本次 L0 备份屏障，并 SHALL 仅在全部必要备份成功后替换
- **AND** `no-interrupt` 模式 MUST 先创建可恢复的时间戳备份，备份成功后 SHALL 替换为规范源当前 v1 并报告
- **AND** 两种模式均 MUST 保持受管区块外内容原样

#### Scenario: L0 备份失败
- **WHEN** 旧版本升级、单侧或乱序标记修复、同版本内容漂移处理等任意 L0 操作要求创建备份，但备份失败
- **THEN** 系统 MUST 立即终止本次 L0 更新
- **AND** 系统 SHALL NOT 写入 `CLAUDE.md` 或 `AGENTS.md` 中的任一 L0
- **AND** 两个入口的受管区块和区块外内容均 MUST 保持原样

#### Scenario: 双入口统一预检和备份屏障
- **WHEN** `rule-config` 准备在同一次运行中处理 `CLAUDE.md` 与 `AGENTS.md` 的 L0
- **THEN** 系统 MUST 在写入任一入口前识别两个入口各自的标记、版本、完整内容和备份需求
- **AND** 系统 MUST 在写入任一入口前成功创建本次所需的全部 L0 备份
- **AND** 仅在统一预检和全部必要备份成功后，系统 SHALL 按各入口对应分支执行写入
- **AND** 写入后两个入口 MUST 使用相同 L0 版本并保持语义等价

### Requirement: L1 框架规则升级必须保护无法识别的本地内容
系统 SHALL 为 L1 框架规则记录可识别版本并按完整文件内容识别已知框架版本。版本标记 MUST 只用于定位候选框架版本；系统 MUST 仅在完整文件内容与该候选已知版本规范逐字一致时，才将文件识别为当前或受支持旧版。当前 v1 标记存在但完整内容与当前框架 v1 不一致，或受支持旧版本标记存在但完整内容与对应已知旧版规范不一致时，系统 MUST 将其归入“与任何已知框架版本不匹配”。普通模式 SHALL 询问是否替换，无响应时 MUST 保留原文件并报告；无响应分支不覆盖原文件，因此不要求创建额外备份。`no-interrupt` 模式 MUST 先创建可恢复备份，备份成功后 SHALL 替换为当前框架 v1 并报告。任何需要 L1 备份的分支 MUST 在备份成功后才能替换；备份失败时 MUST 终止且 SHALL NOT 替换原文件。

#### Scenario: 识别到旧版框架规则
- **WHEN** 目标项目的协作规则具有受支持的旧版本标记，且完整文件内容与该受支持旧版规范逐字一致
- **THEN** `rule-config` MUST 先创建可恢复备份
- **AND** 仅在备份成功后 SHALL 将其升级到当前版本并报告

#### Scenario: 旧版本标记匹配但完整内容漂移
- **WHEN** 目标协作规则具有受支持的旧版本标记，但完整文件内容与该标记对应的已知旧版规范不一致
- **THEN** `rule-config` MUST 将其视为与任何已知框架版本不匹配的未知本地修改
- **AND** 普通模式 SHALL 询问是否替换；无响应时 MUST 保留原文件并报告
- **AND** `no-interrupt` 模式 MUST 先创建可恢复备份，备份成功后 SHALL 以当前框架 v1 替换并报告

#### Scenario: 当前 v1 标记存在但完整内容漂移
- **WHEN** 目标协作规则包含当前 v1 标记，但完整文件内容与当前框架 v1 不一致
- **THEN** `rule-config` MUST 将其视为与任何已知框架版本不匹配
- **AND** 普通模式 SHALL 询问是否替换；无响应时 MUST 保留原文件并报告
- **AND** `no-interrupt` 模式 MUST 先创建可恢复备份，备份成功后 SHALL 以当前框架 v1 替换并报告

#### Scenario: 发现其他未知本地修改
- **WHEN** 目标协作规则无标记、版本未知或完整内容与任何已知框架版本均不匹配
- **THEN** 普通模式 SHALL 询问是否替换；无响应时 MUST 保留原文件并报告
- **AND** `no-interrupt` 模式 MUST 先创建可恢复备份，备份成功后 SHALL 以当前框架 v1 替换并报告

#### Scenario: L1 备份失败
- **WHEN** 受支持旧版本升级或未知本地修改处理等任意 L1 分支要求创建备份，但备份失败
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
系统 MUST NOT 依赖 `cadence-workflow`、Hook、守护进程或“规则是否已读”状态来实现本协作流程。

#### Scenario: 客户端没有 Hook 能力
- **WHEN** 目标客户端没有可用的 SessionStart 或编辑前 Hook
- **THEN** L0、L1 和 L2 仍独立表达完整的路由和门禁

#### Scenario: cadence-workflow 被移除
- **WHEN** 业务项目不存在或移除 legacy 的 `cadence-workflow`
- **THEN** OpenSpec 与 Superpowers 协作规则仍可正常使用
