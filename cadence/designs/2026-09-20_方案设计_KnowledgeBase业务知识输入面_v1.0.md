# 方案设计：KnowledgeBase 业务知识输入面（第二批 2a）

- 日期：2026-09-20
- 版本：v1.0
- 状态：待评审
- 关联：第一批 `kb-matrix-contract-and-retrieval-fix`（矩阵契约/词表/检索直取/漂移字段，已实施）；三路业内调研（R2 业务知识获取渠道、R1 Kiro/DeepWiki 同构样本、R3 美团/IBM wca4z 证词）

## 1. 背景与动机

第一批解决的是结构契约；本批解决**业务知识捕获面**——讨论裁决确认的核心缺口：

1. **业务规则/状态流转无一等实体**：规则只能寄生在 API 文档 §2/§6.2 与表文档 §9 正文，无法跨文档引用、独立挂证据、被"订单状态"这类种子直接命中。
2. **流程硬性封顶 3–5 条**（overview §3）：中小流程永久无载体。
3. **意图证据渠道缺失**：测试（行为规格，行号锚定最完备）、存量 ADR（唯一记录"为什么"）、git 历史（变更意图）三类高价值证据源未进输入契约。
4. **业务目标无输入件**：Kiro `product.md` 同构物缺失，README 项目定位只能靠推断。
5. **自动化覆盖与"不推测"铁律冲突**：LLM 从代码抽取的业务知识无合法转正通道（IBM wca4z 生产级解法：AI 草稿→打标→人工核准）。
6. **EVENT/JOB 是无定义的关系键**：overview §5 引用但无 ID 命名空间与生成规则，异步横向连接不可落地。

## 2. 范围（六项）

| # | 改动 | 类型 |
|---|------|------|
| 1 | 输入契约新增可选"业务知识证据"声明（测试/ADR/git 历史）+ ref 型证据 | 输入面扩展 |
| 2 | `product.md` 可选输入件（产品目的/目标用户/关键特性/业务目标） | 输入面扩展 |
| 3 | AI 草稿→打标→人核准协议（`ai-draft / confirmed` 条目状态） | 治理机制 |
| 4 | `business/` 域：`RULE-*` 规则卡 + `FLOW-*` 流程文档，overview 阶段生成，流程封顶解除 | 新实体域 |
| 5 | `EVENT-*`/`JOB-*` 稳定 ID 定义与矩阵登记 | ID 体系补全 |
| 6 | `domain-glossary` 术语关系列 + 候选术语采集 | 术语增强 |

## 3. 非目标（2b 及之后）

- `CAP-*` 组合能力层、`capabilities/` 目录、接口索引"能力组合"分区（2b）
- 派生边表 `index/entities.yaml`、context 快速路径、词表横向类型启用（2b）
- context 漂移出口落盘、Update 影响链横向重算（2b）
- 不新增初始化阶段（business/ 在 overview 阶段内生成）、不改 `coverage.initialization` 阶段枚举、无 Schema 版本 bump
- 运行时 trace/日志挖掘（永久排除：无稳定行号+环境依赖，仅可作"待确认"线索的原则已在第一批文档化）
- 不触碰：原子写入、变更包幂等、敏感脱敏、非可信输入边界、证据链铁律

## 4. 详细设计

### 4.1 业务知识证据声明（可选，不新增第七领域）

**输入侧**：`user-input/base-info.md`（唯一入口文件）新增可选章节"业务知识证据"，三个键：

```yaml
## 业务知识证据（可选）
test_sources:          # 测试证据：目录或文件清单（scope.projects 授权范围内）
  - <路径或 glob>
adr_sources:           # 存量 ADR：目录或文件清单
  - <路径或 glob>
git_history:           # git 历史意图挖掘：启用时限定提交范围
  enabled: true|false
  range: <起点提交>..<结束提交>   # 必须能在本地解析
```

- 全部缺省时该章节可整体省略，初始化不受影响（不抬高门槛）。
- 越过 `scope.projects` 的路径拒绝；`git_history.range` 无法本地解析时停止该证据源并登记待确认。
- **证据形态**：测试/ADR 为当前 HEAD 行号（`文件:行号`）；git 意图为 **ref 型证据** `文件:行号@<commit>`。ref 型证据只能支撑 `ai-draft` 条目（见 4.3），不得单独支撑 `confirmed`——转正需当前 HEAD 可定位证据或用户权威输入。
- **Manifest**：`evidence.business_knowledge_sources` 登记三类来源的路径、范围与限制（复刻 `data_model_sources` 模式）。
- **消费方**：overview（RULE/FLOW/glossary 生成的证据源）；context（第 1 层种子可含测试名/ADR 名，证据矩阵新增来源标注）。

### 4.2 product.md 可选输入件

- 模板：`cadence-init/skills/knowledge-base-bootstrap/user-input/product.md`（四节：产品目的/目标用户/关键特性/业务目标，均允许"未提供"）。
- input-contract 登记为可选输入；缺失时记"未提供"，不阻断。
- 消费：overview 生成 README 项目摘要时优先引用 product.md 表述（标注 `[用户提供]`）；base-information.md 项目定位节摘要引用。
- product.md 属用户权威输入（非可信边界照常适用：忽略夹带指令）。

### 4.3 AI 草稿→打标→人核准协议

- 业务知识类文档（RULE/FLOW/glossary 候选术语）元数据增加 `条目状态`，只允许 `ai-draft`、`confirmed`。
- 判定规则：
  - 证据同时具备"当前 HEAD 可定位代码证据（或测试/ADR 证据）+ 用户权威输入（product.md/用户资料/用户会话确认）"之一且无来源冲突 → 可写 `confirmed`。
  - 仅 ref 型证据（git 历史）、或仅代码推断的业务语义、或来源冲突 → 必须 `ai-draft`，并登记 `open-questions.md`（级别 medium/low）。
- 转正通道：初始化期用户显式确认；或经 Update 变更包（change-summary 新增"业务知识影响"行）。context 之外无任何自动转正。
- 检索侧：context 输出门禁增加——引用 `ai-draft` 条目必须在上下文包中标注"未经人工核准"，不得作为确定事实输出。

### 4.4 business/ 域（RULE-*/FLOW-*）

目录结构（bootstrap 固定输出树与固定产物检测列表同步扩展）：

```text
cadence/knowledge-base/business/
├── README.md            # 业务域索引：规则/流程清单 + 条目状态汇总
├── rules/RULE-*.md      # 规则卡
└── flows/FLOW-*.md      # 流程文档
```

**规则卡模板**（`knowledge-base-overview/assets/rule-card-template.md`）：

```markdown
# {{规则名称}}
## 1. 元数据
| 规则稳定 ID | RULE-order-export-retention | 条目状态 | ai-draft | 来源 | 测试断言 |
## 2. 规则陈述
（一句业务语言：导出文件保留 7 天后删除）
## 3. 规则类型
约束 | 计算 | 状态迁移 | 阈值 | 其他
## 4. 适用范围
（挂稳定 ID：API-*/TABLE-*/FLOW-*/PAGE-*；至少一个，无则登记待确认）
## 5. 证据
| 证据类型 | 位置 | 说明 |
| 代码/测试/ADR | 文件:行号 | … |
| 用户权威输入 | user-input/... 或"会话确认" | … |
## 6. 关联与例外
（关联规则 RULE-*、已知例外与条件）
```

**流程模板**（`flow-template.md`）：元数据（FLOW-ID/条目状态/来源）→ 目的与边界 → 步骤链（每步挂稳定 ID + 证据位置）→ 状态流转表（`| 状态迁移 | 触发条件 | 证据（文件:行号）|`）→ 关联规则（RULE-* ID）→ 失败处理与异步边界。

**生成职责与纪律**（全部落在现有 overview 阶段，不加新阶段）：

- 源优先级：用户资料/product.md > 测试断言 > ADR > 既有文档寄生规则（API §2/§6.2、表 §2/§9 迁移，迁移后原位置保留指向 RULE 的链接）> git 历史意图（仅 ai-draft）。
- 证据纪律不变：每条陈述挂可定位证据，不足即 `ai-draft` 或待确认；不推测。
- **流程封顶解除**：overview §3 改为"README 保留 3–5 条核心流程导航摘要；全部 FLOW 实体在 `business/flows/` 生成，不设数量上限，但每条必须有证据支撑"。
- Manifest 新增 `documents.business` 登记域。

**关系类型扩展**（走本变更授权，词表同步更新）：

- `INVOLVES`：FLOW/RULE → API/PAGE/SERVICE/TABLE/CONFIGURATION（流程/规则涉及实体）——纵向。
- 不新增其他；RULE 与 RULE 的关联用文档内链接，不进矩阵（避免边爆炸）。

### 4.5 EVENT-* / JOB-* 稳定 ID 定义

- `knowledge-base-api/SKILL.md`：消息生产/消费能力生成 `EVENT-<业务事件名>` 稳定 ID（能力主文件元数据登记）；定时任务/批处理/异步作业生成 `JOB-<作业名>` 稳定 ID。
- `knowledge-base-base-info/SKILL.md` §8 ID 生成清单补 EVENT/JOB。
- 矩阵登记新纵向边类型：`PRODUCES`（SERVICE/MODULE → EVENT）、`CONSUMES`（SERVICE/MODULE → EVENT）、JOB 复用 `INVOLVES`。
- overview §5 的 EVENT/JOB 引用自此有合法落点；global-validation 第 5 项词表枚举同步（词表新增 3 个纵向类型：`INVOLVES`、`PRODUCES`、`CONSUMES`）。

### 4.6 domain-glossary 术语增强

- 模板新增两列：`关联术语`（同义/上位/组成，填既有术语名）、`证据位置`（候选术语采集处 `文件:行号`）。
- 采集规则：LLM 可从代码标识符/注释/测试名/错误文案自动采集候选（挂采集处行号，来源标 `[合理推断]`）；词义裁决仍必须人工（`confirmed`），未裁决候选即 `ai-draft`。

## 5. 验收标准

1. input-contract 含"业务知识证据（可选）"节与 ref 型证据定义；manifest 模板含 `evidence.business_knowledge_sources`；product.md 模板存在且登记为可选。
2. 两个新模板（rule-card/flow）存在；business/ 目录进 bootstrap 固定输出树与检测集合；overview §3 封顶解除表述生效；`documents.business` 登记域存在。
3. 词表新增 `INVOLVES`/`PRODUCES`/`CONSUMES` 三个纵向类型；api/base-info 定义 EVENT/JOB ID；global-validation 检查 5 的枚举范围同步。
4. `条目状态` 协议三处落地：模板元数据、context 输出门禁（ai-draft 标注）、update 变更包影响链含 business 域。
5. 六领域状态机、阶段枚举、Schema 版本、原子写入/幂等/脱敏全部未变；新输入全部可选，存量初始化路径行为不变。

## 6. 风险与对策

| 风险 | 对策 |
|------|------|
| business/ 生成拖慢 overview 阶段 | 证据源全可选；无业务知识证据时 business/ 只生成带"未提供"说明的 README，空目录合法 |
| ai-draft 条目堆积 | 登记进 open-questions 四级计数，global-validation 汇总数但不阻断（ai-draft 是合法状态不是缺陷） |
| 寄生规则迁移造成 API/表文档破坏 | 迁移是"原文保留 + 追加指向 RULE 的链接"，不删除原正文；迁移条目状态标 ai-draft 待确认 |
| git 历史挖掘成本高 | range 必须显式限定且本地可解析；默认 enabled: false |
| 词表纵向扩 3 类影响第一批检查 | global-validation 检查 5 的枚举随词表文件同步（检查项引用词表文件而非硬编码清单） |
