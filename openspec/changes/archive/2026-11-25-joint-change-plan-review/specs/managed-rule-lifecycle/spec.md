## MODIFIED Requirements

### Requirement: L1 框架规则升级必须保护无法识别的本地内容

系统 SHALL 为 L1 框架规则记录可识别版本并按完整文件内容识别已知框架版本。版本标记 MUST 只用于定位候选框架版本；系统 MUST 仅在完整文件内容与该候选已知版本规范逐字一致时，才将文件识别为当前或受支持旧版。当前版本标记存在但完整内容与当前框架版本不一致，或受支持旧版本标记存在但完整内容与对应已知旧版规范不一致时，系统 MUST 将其归入"与任何已知框架版本不匹配"。对归入不匹配或无标记的未知本地修改，普通模式与 no-interrupt 模式 MUST 执行相同动作：先创建可恢复备份，备份成功后 SHALL 替换为当前框架版本 并报告，处理 MUST 不经用户决策；可恢复备份使本地内容可回滚。任何需要 L1 备份的分支 MUST 在备份成功后才能替换；备份失败时 MUST 终止且 SHALL NOT 替换原文件。本要求所述可恢复备份 MUST 采用复制原文件到 `cadence/legacy/<14 位时间戳>/<相对项目根路径>` 的形式，随后以 `atomic_write` 原子替换原位文件；`atomic_write` 失败时原文件 MUST 因原子替换语义保持运行前内容不变。

#### Scenario: 识别到旧版框架规则

- **WHEN** 目标项目的协作规则具有受支持的旧版本标记，且完整文件内容与该受支持旧版规范逐字一致
- **THEN** `rule-config` MUST 先将原文件复制归档到 `cadence/legacy/`
- **AND** 仅在归档成功后 SHALL 以当前版本原子替换原位并报告

#### Scenario: 旧版本标记匹配但完整内容漂移

- **WHEN** 目标协作规则具有受支持的旧版本标记，但完整文件内容与该标记对应的已知旧版规范不一致
- **THEN** `rule-config` MUST 将其视为与任何已知框架版本不匹配的未知本地修改
- **AND** 普通模式与 no-interrupt 模式 MUST 执行相同动作：先将原文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以当前框架版本原子替换原位并报告
- **AND** 处理 MUST 不经用户决策

#### Scenario: 当前 v1 标记存在但完整内容漂移

- **WHEN** 项目从 v1 升级，目标含 v1 标记但与任何已知 v1 正文不同
- **THEN** `rule-config` MUST 将其视为与任何已知框架版本不匹配
- **AND** 普通模式与 no-interrupt 模式 MUST 执行相同动作：先将原文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以当前框架版本原子替换原位并报告
- **AND** 处理 MUST 不经用户决策

#### Scenario: 发现其他未知本地修改

- **WHEN** 目标协作规则无标记、版本未知或完整内容与任何已知框架版本均不匹配
- **THEN** 普通模式与 no-interrupt 模式 MUST 执行相同动作：先将原文件复制归档到 `cadence/legacy/`，归档成功后 SHALL 以当前框架版本原子替换原位并报告
- **AND** 处理 MUST 不经用户决策

#### Scenario: L1 备份失败

- **WHEN** 受支持旧版本升级或未知本地修改处理等任意 L1 分支要求创建归档，但归档失败
- **THEN** `rule-config` MUST 立即终止该次 L1 更新
- **AND** `rule-config` SHALL NOT 替换或改变原协作规则文件

#### Scenario: 无基线项目升级旧工作流
- **WHEN** 项目缺少本地基线，旧 v1 工作流混有项目自定义
- **THEN** 仅将无法归属历史框架的用户差异保留为覆盖，独立覆盖内容保留，旧门禁不会被提升为用户规则

### Requirement: L0 区块必须包含可见文本版本行

自 v4 起,L0 受管区块首行 MUST 包含可见文本版本标识(如 `Cadence L0 路由内核 v6`),与既有 HTML 注释标记并存:注释标记供脚本解析与受管识别,可见文本供 agent 在上下文中自报版本;v6 延续该要求。当前版本的 Skill 调用客户端语义 MUST 覆盖五端(omp 归 pi 同类:经 `skill://` 全文读取)。既有确定性升级机制 MUST 将 v5 及更早版本升级为 v6;历史版本规范 MUST 归档进 `l0-history/`。框架升级 L0 版本时,eval 断言层(`eval/install/assertions.py` 的 L0 标记常量、当前标记对应的断言名、升级文案与其测试 fixture)MUST 同步升版,不得留旧版断言名并行。

动机:Claude Code 注入上下文时剥离 HTML 注释(2026-09-02 实测);omp 调用 skill=全文读取 `skill://`(2026-09-09 omp 内置文档与实测)。

#### Scenario: v3 确定性升级为 v4

- **WHEN** 入口文件包含成对 v3 标记且完整区块内容与 v3 规范源一致,而框架当前版本为 v4
- **THEN** 系统 MUST 不经用户决策将区块升级为 v4 规范源,普通模式与 no-interrupt 模式同动作

#### Scenario: v4 确定性升级为 v5

- **WHEN** 入口文件包含成对 v4 标记且完整区块内容与 v4 规范源一致,而框架当前版本为 v5
- **THEN** 系统 MUST 不经用户决策将区块升级为 v5 规范源,普通模式与 no-interrupt 模式同动作

#### Scenario: eval 断言层随版本同步

- **WHEN** 框架 L0 当前版本为 v6
- **THEN** eval stage1 断言以 v6 标记判定入口区块，断言名为 `l0.v6`，退役 `l0.v5`

#### Scenario: Claude Code 回执可自报版本

- **WHEN** Claude Code 会话被要求复述当前生效的 L0 版本
- **THEN** 其可从上下文中的可见文本版本行读出版本号 v6,不依赖 HTML 注释标记

#### Scenario: v5 项目升级工作流
- **WHEN** 旧项目的双入口使用 v5 内核
- **THEN** 两个入口都升级为唯一 v6 区块，保留区块内用户追加、区块外内容和项目提交开关
