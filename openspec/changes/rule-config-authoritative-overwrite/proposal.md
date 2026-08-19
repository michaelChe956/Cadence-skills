# Proposal: rule-config-authoritative-overwrite

## Why

当前 `rule-config` 普通模式对全部框架受管内容的 drift 一律询问 keep/replace 且默认 keep（§11.6 A 类安全默认），与"框架受管内容以 Cadence-skills 模板为权威"的治理意图相悖。用户在 naruto 项目实测：规则文件保持旧定制内容（Serena 版 `mcp-servers.md`、TDD 版 `code-usage.md`），必须逐条人工裁决才能对齐模板，且推荐默认方向是保留而非对齐。同时普通模式与 no-interrupt 对同一 drift 的处理方向相反（keep vs 权威覆盖），语义不一致。

用户裁决：所有框架受管内容两模式统一"备份 + 权威覆盖/处理"，不再提问；归档到 `cadence/legacy/` 提供可恢复性，替代"保留原状"成为安全兜底。

## What Changes

- **框架受管规则文件 drift（RF-05）**：普通模式从"询问 keep/replace、默认 keep"改为与 no-interrupt 一致的"屏障归档 + 模板原子覆盖"，不再产生冲突条目、不再提问。**BREAKING**（普通模式行为变化）
- **L1 协作规则 drift/unmarked（L1-04/05/06）**：两模式统一"归档 + 当前框架版本替换"，不再询问；基于完整内容的版本识别语义保留（skip/upgrade 分支不变）。**BREAKING**
- **L0 受管区块 drift（L0-03）与标记单侧/顺序错误（L0-06 子分支）**：两模式统一"归档 + 规范源当前版本替换 / 确定性安全归并"，不再询问；区块外项目内容保持原样。**BREAKING**
- **OpenSpec `rules.apply` 禁用键（OS-04）**：普通模式对齐 no-interrupt 现状——归档 + 移除该键 + 继续保守合并，不再询问。**BREAKING**
- **OpenSpec config.yaml 无法解析/结构类型不兼容（OS-03/05）**：从"普通模式保留并报告 / no-interrupt 备份后终止（失败关闭）"改为两模式"归档 + 模板整体替换"，不再失败关闭。**BREAKING**
- **决策机制休眠**：上述六类是 §11.6 A 类的全部成员，改动后系统不再有任何活跃冲突类型；普通模式"逐条提问 + 决策文件"流程抽空，`--decisions` / `validate_decisions` / `default_keep` 机制代码保留为兜底，供未来新冲突类型复用。
- **文档同步**：`SKILL.md`、`references/merge-semantics.md`（RF/L1/L0/OS 表与 §11.6）、`references/rules/README.md`、`tests/skill-clause-map.md` 按新语义对账更新。

### 非目标

- 不改变备份归档路径结构、L0 双入口屏障、原子发布等既有保护机制（它们是本次改动的安全前提）。
- 不删除 `merge_markdown`、`default_keep`、`validate_decisions` 等休眠机制代码（NC 表当前零调用，按"保留行 ID 对账"原则管理）。
- 不触碰项目自建的非受管文件（`.claude/rules/` 清单外文件、`cadence/project-rules/`、入口文件受管区块外内容、`config.yaml` 可解析时的项目字段）。
- 不改变普通模式与 no-interrupt 的剩余差异：历史目录迁移（HM 表）与 `--project-type` 提升权。

## Capabilities

### New Capabilities

（无新 capability；本次为既有 capability 的需求变更。）

### Modified Capabilities

- `framework-authoritative-rule-files`：三类策略划分保留，但"版本化特例类"的 drift/未知状态从"询问"转为"归档+替换"；"保留原语义类"增加例外——`openspec/config.yaml` 无法解析或结构不兼容时改为归档+模板整体替换。
- `managed-rule-lifecycle`：L0 当前版本区块 drift 从"视为本地修改、不得静默覆盖、普通模式询问"改为两模式归档+规范源替换；L1 各 drift/unmarked 场景从"普通模式询问、无响应保留"改为两模式归档+当前版本替换。
- `rule-config-scripted-execution`：普通模式不再就受管内容 drift 提问（无活跃冲突类型）；框架规则文件 drift 两模式统一权威覆盖；config.yaml 结构不兼容/无法解析从失败关闭改为归档+模板替换；决策文件机制转为休眠兜底。
- `routing-conformance`：受管生命周期静态检查中"不可解析 YAML/目标字段类型冲突"从失败关闭场景改为归档+模板替换场景；"内容漂移保护"措辞调整为"漂移归档+权威覆盖"。

## Impact

- **代码**：`cadence-init/skills/rule-config/scripts/rule-config.py`（`compute_plan` 的 S3/S4/S7 冲突生成逻辑、`step_s3_rules_files`/`step_s4`/S7 apply 的 decision 分支）。
- **测试**：`tests/test_rule_config.py`（普通模式 keep/replace 决策用例改写为自动覆盖断言）、`tests/verify-managed-lifecycle.sh`、`tests/skill-clause-map.md`（条款对账）。
- **文档**：`SKILL.md`（普通模式流程、冲突汇报规则）、`references/merge-semantics.md`（RF/L1/L0/OS 表行、§11.6 A 类清单）、`references/rules/README.md`。
- **行为**：两模式对受管内容 drift 的处理方向统一为权威覆盖；目标项目中被本地改过的受管内容将被自动替换（均有 `cadence/legacy/` 备份可恢复）；普通模式执行全程无需用户决策输入。
- **不影响**：SM 章节规范化（本就不提问）、CS/CG/OP 补齐语义、HM 迁移模式差异、项目类型判定规则、报告 schema（`warnings` 五码、`hints.next` 等）。
