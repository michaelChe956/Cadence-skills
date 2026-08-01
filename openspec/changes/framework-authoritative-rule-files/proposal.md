## Why

`rule-config` 当前对 `.claude/rules/` 下的框架规则文件采用章节级保守合并（NC-02/NC-03），把"被模板取代的旧内容"当作"项目独有内容"追加到 `**项目补充**`。实测（naruto 项目执行 `rule-config no-interrupt`）产生三类污染：已被框架移除的 Serena MCP 整段复活、模板已更新措辞的旧行重复出现、入口文件摘要块被重复追加。

同时发现一个引用断链 bug：`ORDINARY_RULE_FILES` 同时复制 `code-usage-coding.md` 与 `code-usage-noncoding.md` 两个互斥模板，而 L0 规范源与入口摘要引用的却是 `code-usage.md`——该文件从未被创建，全新初始化后 L0 路由表指向死链。

根因是把框架规则文件当作"可承载项目定制的资产"来保守合并。实际上项目定制早已规定必须写在 `cadence/project-rules/`，框架规则文件不允许项目改写。用错误的资产定位导致了合并复杂度与全部污染。

## What Changes

- **BREAKING** `.claude/rules/` 下框架受管规则文件改为**框架权威全覆盖**：不再按章节合并、不再产生 `**项目补充**`。内容与模板一致则幂等跳过，不一致则复制原文件到 `cadence/legacy/` 后以模板原子覆盖原位。
- **BREAKING** 备份机制由同目录 `<原文件名>.cadence-backup-<时间戳>` 改为**复制**原文件到 `cadence/legacy/<时间戳>/<相对路径>`（原位文件由 `atomic_write` 原子替换覆盖，失败时原文件不变），该目录内置 `.gitignore` 不纳入版本控制。适用于规则文件、L0 入口、L1 规则与 `openspec/config.yaml` 全部备份分支。
- **BREAKING** 修复 `code-usage` 引用断链：按检测到的 `project_type` 单选来源模板，落地文件名恒为 `code-usage.md`；项目类型变化时按类型权威覆盖（两个来源模板语义互斥，不得合并）。历史遗留的 `code-usage-coding.md`/`code-usage-noncoding.md` 归档后从 `.claude/rules/` 移除。
- **BREAKING** 修正 `agent-routing-kernel.md` 定位矛盾：从受管规则文件清单移除，仅作为 L0 受管区块插入源，不再复制到 `.claude/rules/`。依赖该副本的下游引用应改指 L0 受管区块。
- 修复入口文件摘要重复：摘要缺失判据由"整行精确措辞匹配"改为"是否已存在指向该规则文件的引用"，已存在则不追加。
- 修复技术栈占位卡死：`### 项目技术栈` 逐项判断，占位值（`待确认`/`未检测到`）替换为检测值，用户手填的真实值保留不覆盖。
- 强化幂等契约：所有受管资产写入语义统一为"归一化到目标态后比对再写"，保证任意次数执行结果一致，且不重复堆积 `cadence/legacy/` 备份。
- L1 `openspec-superpowers-workflow.md` 保持版本化特例（不纳入全覆盖），保留跨版本升级能力。

## Capabilities

### New Capabilities

- `framework-authoritative-rule-files`: 框架受管规则文件的权威全覆盖语义、资产范围三分法（全覆盖／版本化特例／保留原语义）、`cadence/legacy/` 备份归档机制，以及"执行 N 次等于执行 1 次"的幂等契约。

### Modified Capabilities

- `managed-rule-lifecycle`: 备份语义由"同目录时间戳副本"改为"复制到 `cadence/legacy/` 后原子覆盖原位"；规则文件处理由章节级合并改为框架权威全覆盖；新增 `code-usage.md` 按项目类型单选来源与恒定落地名的要求；`agent-routing-kernel.md` 不再作为复制到 `.claude/rules/` 的受管规则文件。
- `rule-config-scripted-execution`: 脚本内合并语义 requirement 收窄--框架受管规则文件不再走章节级合并与 `**项目补充**`，改为框架权威全覆盖；备份语义改为复制到 `cadence/legacy/` + 原子覆盖；dry-run 的 no-interrupt drift 动作标注由 `markdown-merge` 改为 `authoritative-overwrite`；技术栈写入改为占位替换不覆盖用户值。

## Impact

- `cadence-init/skills/rule-config/scripts/rule-config.py`：`ORDINARY_RULE_FILES` 清单、S3 规则文件步骤、`backup_file`、`merge_markdown` 适用范围、`_ensure_summary_lines`、`_ensure_techstack_block`。
- `cadence-init/skills/rule-config/references/merge-semantics.md`：NC-02/NC-03 适用范围收窄、RF 表新增权威覆盖行、SM 表摘要判据、§11.1 备份命名与 §11.2 备份屏障。
- `cadence-init/skills/rule-config/SKILL.md`：概述与合并语义引用同步。
- `cadence-init/skills/rule-config/tests/`：`test_rule_config.py`、`skill-clause-map.md` 对账与幂等回归用例。
- 业务项目产物：新增 `cadence/legacy/` 目录；`.claude/rules/` 不再出现 `code-usage-coding.md`/`code-usage-noncoding.md`/`agent-routing-kernel.md`。
- 不影响 `pre-check`（校对未发现其产物问题），本次不改动该 skill。
