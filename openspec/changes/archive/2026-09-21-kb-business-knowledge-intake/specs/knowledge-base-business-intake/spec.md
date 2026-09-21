# knowledge-base-business-intake 规格

## ADDED Requirements

### Requirement: 业务知识证据声明

`knowledge-base-bootstrap` 的输入契约 MUST 支持在 `user-input/base-info.md` 声明可选"业务知识证据"：`test_sources`（目录或文件清单）、`adr_sources`（目录或文件清单）、`git_history`（`enabled` + 本地可解析的 `range`）。全部缺省时初始化 MUST 正常继续；声明的路径越出 `scope.projects` 授权范围、或 git range 无法在本地解析时 MUST 停止该证据源并登记待确认，不得阻断其他领域。测试与 ADR 证据 MUST 使用当前 HEAD 行号定位；git 历史意图 MUST 使用 ref 型证据 `文件:行号@<commit>`。Manifest MUST 在 `evidence.business_knowledge_sources` 登记三类来源的路径、范围与限制。

#### Scenario: 声明三源后初始化

- **WHEN** `base-info.md` 声明了 test_sources、adr_sources 与可解析的 git range
- **THEN** Manifest 的 `evidence.business_knowledge_sources` 登记三类来源，overview 生成业务知识文档时可引用对应证据

#### Scenario: 未声明任何证据源

- **WHEN** `base-info.md` 省略"业务知识证据"章节
- **THEN** 初始化正常继续，business/ 域生成带"未提供"说明的 README，不产生待确认项

#### Scenario: git range 不可解析

- **WHEN** 声明的 git range 在本地仓库无法解析
- **THEN** git 证据源停止并登记待确认，测试/ADR 证据源与其他领域不受影响

### Requirement: product.md 可选输入件

`knowledge-base-bootstrap` MUST 提供 `user-input/product.md` 模板（产品目的/目标用户/关键特性/业务目标四节，各节允许"未提供"），并在输入契约登记为可选输入。缺失时 MUST 记"未提供"且不阻断初始化。`knowledge-base-overview` 生成 README 项目摘要与 `knowledge-base-base-info` 项目定位时 MUST 优先引用 product.md 表述并标注 `[用户提供]`。

#### Scenario: 提供 product.md

- **WHEN** 用户填写 product.md 后初始化
- **THEN** README 项目摘要与 base-information 项目定位引用其表述并标注 `[用户提供]`

#### Scenario: 未提供 product.md

- **WHEN** user-input/ 无 product.md
- **THEN** 初始化不阻断，相关位置记"未提供"，不凭推测补写业务目标

### Requirement: AI 草稿与人核准条目状态协议

业务知识类文档（RULE/FLOW/术语候选）元数据 MUST 含 `条目状态`，取值只允许 `ai-draft`、`confirmed`。仅具备 ref 型证据、或仅代码推断的业务语义、或存在来源冲突时 MUST 写 `ai-draft` 并登记 `open-questions.md`；写 `confirmed` MUST 同时具备可定位证据与用户权威输入（product.md/用户资料/用户会话确认）之一。条目转正 MUST 经初始化期用户显式确认或 Update 变更包，MUST NOT 自动转正。`knowledge-base-context` 的输出 MUST 对引用的 `ai-draft` 条目标注"未经人工核准"，MUST NOT 将其作为确定事实输出。

#### Scenario: 仅 git 历史证据的规则

- **WHEN** 一条规则只有 `文件:行号@<commit>` 的 ref 型证据支撑
- **THEN** 规则卡条目状态为 `ai-draft` 且进入待确认清单；用户核准前不得转正

#### Scenario: context 引用 ai-draft 条目

- **WHEN** 上下文包引用了条目状态为 `ai-draft` 的规则或流程
- **THEN** 输出中该条目带"未经人工核准"标注，不与 confirmed 条目混同为事实

#### Scenario: 用户核准转正

- **WHEN** 用户在会话中显式确认某 ai-draft 条目并经 Update 变更包提交
- **THEN** 条目状态更新为 `confirmed`，变更历史记录转正事件

### Requirement: business 业务域实体

`knowledge-base-bootstrap` 固定输出树与固定产物检测集合 MUST 包含 `business/`（README、rules/、flows/）。`knowledge-base-overview` MUST 在现有 overview 阶段内生成业务域：规则卡遵循 `assets/rule-card-template.md`（元数据含稳定 ID 与条目状态/规则陈述/规则类型/适用范围挂稳定 ID/证据/关联与例外），流程文档遵循 `assets/flow-template.md`（步骤链逐跳挂稳定 ID 与证据、状态流转表、关联规则）。源优先级 MUST 为：用户资料与 product.md > 测试断言 > ADR > 既有文档寄生规则 > git 历史意图（仅 ai-draft）。既有 API/表文档中的寄生规则迁移 MUST 保留原文并追加指向 RULE 的链接，MUST NOT 删除原正文，迁移条目初始状态为 `ai-draft`。`knowledge-base-overview` 的核心业务流程章节 MUST 解除 3–5 条封顶：README 保留 3–5 条导航摘要，全部 FLOW 实体在 `business/flows/` 生成且不设数量上限，但每条 MUST 有可定位证据支撑。Manifest MUST 新增 `documents.business` 登记域。

#### Scenario: 从测试断言生成规则卡

- **WHEN** 测试证据中存在可定位的业务规则断言（如文件保留期校验）
- **THEN** 生成对应 `RULE-*` 规则卡，证据挂测试文件行号，适用范围挂相关稳定 ID

#### Scenario: 流程数量不再受限

- **WHEN** 项目存在 8 条有证据支撑的业务流程
- **THEN** `business/flows/` 生成 8 个 FLOW 实体，README 只保留 3–5 条核心流程导航摘要

#### Scenario: 寄生规则迁移不破坏原文

- **WHEN** API 文档 §6.2 的分支规则被迁移为 RULE 实体
- **THEN** API 文档原正文保留，仅追加指向该 RULE 的链接；RULE 条目状态为 `ai-draft`

#### Scenario: 无证据流程被拒绝

- **WHEN** 某业务流程没有任何可定位证据
- **THEN** 不生成 FLOW 实体，进入待确认清单而非推测补齐

### Requirement: EVENT 与 JOB 稳定 ID

`knowledge-base-api` MUST 为消息生产/消费能力生成 `EVENT-<业务事件名>` 稳定 ID（登记于能力主文件元数据），为定时任务/批处理/异步作业能力生成 `JOB-<作业名>` 稳定 ID。`knowledge-base-base-info` §8 的稳定 ID 生成清单 MUST 包含 EVENT 与 JOB。追溯矩阵 MUST 支持纵向边 `PRODUCES`（SERVICE/MODULE → EVENT）、`CONSUMES`（SERVICE/MODULE → EVENT）与 `INVOLVES`（FLOW/RULE/JOB → API/PAGE/SERVICE/TABLE/CONFIGURATION）；`relation-types.md` 词表 MUST 同步这三个纵向类型并保持闭合。

#### Scenario: 消息能力获得 EVENT ID

- **WHEN** api 阶段分析到订单已发布事件的 Producer/Listener
- **THEN** 生成 `EVENT-*` 稳定 ID，矩阵登记 `SERVICE/MODULE --PRODUCES--> EVENT` 与消费方 `CONSUMES` 边

#### Scenario: overview 的 EVENT/JOB 引用可落地

- **WHEN** overview 常见修改场景要求使用 API/EVENT/JOB 稳定 ID 检查消息与异步任务影响
- **THEN** 引用的 EVENT/JOB ID 均有定义与文档落点，不再是无定义的关系键

### Requirement: 领域术语候选采集与裁决

`domain-glossary-template.md` MUST 新增"关联术语"与"证据位置"两列。LLM MUST 允许从代码标识符、注释、测试名、错误文案自动采集候选术语，每个候选 MUST 挂采集处 `文件:行号` 并标注 `[合理推断]` 与 `ai-draft`；术语词义裁决 MUST 保持人工，未裁决候选 MUST NOT 写为正式定义。

#### Scenario: 自动采集候选术语

- **WHEN** 代码中出现高频业务标识符（如 `REVERSAL`）且术语表未收录
- **THEN** 生成候选条目，挂采集处行号，标注 `[合理推断]` 与 `ai-draft`

#### Scenario: 未裁决候选不作正式定义

- **WHEN** 候选术语未经人工裁决即被下游引用
- **THEN** 引用处必须标注候选与 ai-draft 状态，术语表不将其列为正式定义
