## MODIFIED Requirements

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
