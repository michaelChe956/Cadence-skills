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

### Requirement: L0 入口内容必须版本化且可安全升级
系统 MUST 使用稳定开始标记、结束标记和版本号维护 `CLAUDE.md` 与 `AGENTS.md` 中的 L0 受管区块；重复运行 `rule-config` 时 SHALL 只更新受管区块并保留区块外内容。

#### Scenario: 升级已有受管区块
- **WHEN** 已初始化项目重新运行包含新版路由的 `rule-config`
- **THEN** 系统将旧版 L0 替换为新版 L0
- **AND** 保留项目技术栈、命令、业务说明和用户自定义章节

#### Scenario: 重复运行同一版本
- **WHEN** 同一版本的 `rule-config` 连续运行两次
- **THEN** 第二次运行不产生重复路由、重复引用或额外内容变更

### Requirement: L1 框架规则升级必须保护无法识别的本地内容
系统 SHALL 为 L1 框架规则记录可识别版本；识别到旧版框架内容时 MUST 更新，发现无法识别的本地修改时 MUST 先保留备份并报告，不能静默覆盖。

#### Scenario: 识别到旧版框架规则
- **WHEN** 目标项目的协作规则具有受支持的旧版本标识且没有未知本地修改
- **THEN** `rule-config` 将其升级到当前版本

#### Scenario: 发现未知本地修改
- **WHEN** 目标协作规则与任何已知框架版本均不匹配
- **THEN** `rule-config` 保留可恢复备份并报告冲突
- **AND** 不静默丢弃原内容

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
