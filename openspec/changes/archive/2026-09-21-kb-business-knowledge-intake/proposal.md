# Proposal

## Why

第一批（kb-matrix-contract-and-retrieval-fix）解决了结构契约；本变更解决**业务知识捕获面**——四 Agent 讨论裁决确认的核心缺口：业务规则/状态流转无一等实体（寄生正文、无法跨文档引用）、流程硬性封顶 3–5 条、测试/ADR/git 三类高价值意图证据源未进输入契约、业务目标无输入件（Kiro product.md 同构物缺失）、LLM 自动抽取与"不推测"铁律冲突（业内生产级解法为 AI 草稿→打标→人核准）、EVENT/JOB 是被 overview 引用却无定义的关系键。

## What Changes

- **业务知识证据声明（可选）**：`user-input/base-info.md` 新增可选章节，声明测试证据、存量 ADR、git 历史意图三源（git 默认关闭、range 必须本地可解析、路径不得越过 `scope.projects`）；Manifest 新增 `evidence.business_knowledge_sources`；定义 ref 型证据 `文件:行号@<commit>`，其只能支撑 `ai-draft` 条目。
- **product.md 可选输入件**：产品目的/目标用户/关键特性/业务目标四节；缺失记"未提供"不阻断；overview README 项目摘要与 base-information 项目定位优先引用（标 `[用户提供]`）。
- **AI 草稿→打标→人核准协议**：业务知识类文档元数据新增 `条目状态: ai-draft | confirmed`；判定规则（双证据要求）与转正通道（初始化期用户确认或 Update 变更包）落地；context 输出门禁强制对 ai-draft 标注"未经人工核准"。
- **business/ 新域**：`business/README.md`、`rules/RULE-*.md`（规则卡模板）、`flows/FLOW-*.md`（流程模板：步骤链+状态流转表）；overview 阶段内综合生成（不加新阶段）；流程封顶解除——README 保留 3–5 条导航摘要，FLOW 实体不设数量上限但逐条挂证据；寄生规则迁移采用"原文保留+追加指向 RULE 的链接"；Manifest 新增 `documents.business`。
- **EVENT-*/JOB-* 稳定 ID**：api Skill 为消息能力生成 `EVENT-*`、任务能力生成 `JOB-*`；base-info §8 ID 清单补全；词表纵向新增 `INVOLVES`（FLOW/RULE→实体）、`PRODUCES`/`CONSUMES`（SERVICE/MODULE↔EVENT）三类型；global-validation 检查 5 枚举随词表文件同步。
- **domain-glossary 增强**：模板新增"关联术语"与"证据位置"列；LLM 可自动采集候选术语（挂采集处行号、标 `[合理推断]`/`ai-draft`），词义裁决仍必须人工。

无 **BREAKING** 变更：全部新输入可选（存量初始化路径行为不变）、无新初始化阶段、`coverage.initialization` 枚举不变、Schema 保持 4.0；不触碰原子写入、变更包幂等、敏感脱敏、非可信输入边界。

## Capabilities

### New Capabilities

- `knowledge-base-business-intake`: KnowledgeBase 业务知识获取与治理——业务知识证据声明、product.md 输入、ai-draft/confirmed 条目状态协议、business/ 域（RULE/FLOW 实体）、EVENT/JOB 稳定 ID、术语候选采集与人工裁决边界。

### Modified Capabilities

（无——`knowledge-base-artifact-enforcement` 的既有 requirement 不变；本变更的验收检查扩展属新 capability 行为。）

## Impact

- `cadence-init/skills/knowledge-base-bootstrap/`：input-contract.md（新证据节+product.md 登记+固定产物/输出树扩 business/）、manifest-template.yaml（evidence.business_knowledge_sources + documents.business）、user-input/product.md（新模板）、global-validation（business 域与条目状态检查）。
- `cadence-init/skills/knowledge-base-overview/`：SKILL.md（§3 封顶解除、business/ 生成职责、glossary 列、product.md 消费、ai-draft 登记）、assets/rule-card-template.md 与 flow-template.md（新增）、domain-glossary-template.md（增列）。
- `cadence-init/skills/knowledge-base-api/SKILL.md`：EVENT-*/JOB-* ID 生成与矩阵登记。
- `cadence-init/skills/knowledge-base-base-info/SKILL.md`：§8 ID 清单补 EVENT/JOB；项目定位引用 product.md。
- `cadence-init/skills/knowledge-base-context/SKILL.md`：输出门禁 ai-draft 标注；第 1 层种子含测试/ADR。
- `cadence-init/skills/knowledge-base-update/SKILL.md`：变更包影响链含 business 域与条目状态转正路径。
- `cadence-init/skills/knowledge-base-base-info/assets/relation-types.md`：纵向新增 INVOLVES/PRODUCES/CONSUMES。
- 设计文档：`cadence/designs/2026-09-20_方案设计_KnowledgeBase业务知识输入面_v1.0.md`（已确认）。
