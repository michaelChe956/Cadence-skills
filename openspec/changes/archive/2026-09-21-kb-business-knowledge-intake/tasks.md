# Tasks

> 高层工作包；精确文件、命令与实施顺序由 writing-plans 写入 `cadence/plans/`。

## WP1 输入面扩展：业务知识证据 + product.md [R1 业务知识证据声明, R2 product.md]

`input-contract.md` 新增"业务知识证据（可选）"节（三键定义、越界与 range 校验、ref 型证据格式）；登记 product.md 可选输入；新增 `user-input/product.md` 模板；`manifest-template.yaml` 增 `evidence.business_knowledge_sources` 与 `documents.business`。

验收：三键语义与失败处理明确；product.md 模板四节存在；Manifest 域存在。

## WP2 business/ 域与模板 [R4 business 业务域实体]

新增 `knowledge-base-overview/assets/rule-card-template.md` 与 `flow-template.md`；overview SKILL.md：§3 封顶解除（README 3–5 条导航 + FLOW 不设限）、business/ 生成职责与源优先级、寄生规则迁移规则（原文保留+链接）；bootstrap 固定输出树与检测集合扩 `business/`。

验收：两模板存在且元数据含条目状态；封顶解除表述生效；bootstrap 产物清单含 business/。

## WP3 条目状态协议 [R3 AI 草稿与人核准]

判定规则与转正通道写入 overview（业务域）与 glossary（候选术语）；context SKILL.md 输出门禁增 ai-draft 标注、第 1 层种子含测试/ADR；update SKILL.md 影响链含 business 域与转正路径。

验收：三处（overview/context/update）均含条目状态语义；context 门禁含"未经人工核准"标注要求。

## WP4 EVENT/JOB 与词表扩展 [R5 EVENT 与 JOB 稳定 ID]

api SKILL.md：消息能力 EVENT-*、任务能力 JOB-* ID 生成与主文件登记；base-info §8 ID 清单补全；`relation-types.md` 纵向新增 `INVOLVES`/`PRODUCES`/`CONSUMES`；bootstrap 检查 5 确认以词表文件为枚举源。

验收：三类 ID/边有定义；词表闭合且横向仍禁写；检查 5 措辞引用词表文件。

## WP5 术语增强 [R6 领域术语候选采集与裁决]

`domain-glossary-template.md` 增"关联术语"与"证据位置"两列；overview SKILL.md §4 补候选采集规则（挂行号、[合理推断]、ai-draft、裁决人工）。

验收：模板两列存在；采集与裁决边界明确。

## WP6 变更验证 [全部]

机械核对（grep 逐项）+ `openspec validate`；对照设计文档验收标准 5 条逐条核对；确认无阶段枚举/Schema/不变量改动、无越界文件；存量路径行为不变的推演记录（无新输入时六个 Skill 行为不变）。

验收：验证汇报含全部检查输出。
