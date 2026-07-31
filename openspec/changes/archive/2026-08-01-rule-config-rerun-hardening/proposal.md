# Proposal: rule-config-rerun-hardening

## Why

rule-config 脚本在 no-interrupt 重跑场景存在实证的正确性缺陷与两处信任/体验缺口：

1. **P0（已实证）**：`merge_markdown` 不幂等。合并注入的 `**项目补充**` 标记行无 marker pair，重跑时上一次合并产物被当作 existing 读入，标记行被判定为"项目独有行"保留后再注入新标记，导致每个含项目补充的同名章节多出一行重复标记（实证：mcp-servers.md 4 个段落 134/135、173/174、289/290、311/312 成对重复）。测试套件 35 处 merge_markdown 用例零重跑覆盖，bug 得以存活。
2. **P1**：dry-run 报告中普通规则 drift 冲突的 `recommendation` 恒为 `keep`，但 no-interrupt 实际执行 markdown-merge 并写盘，误导用户以为"会保留原文件不动"。
3. **P1**：SKILL.md 的脚本定位约定只覆盖仓库安装场景，未覆盖 plugin 安装场景，plugin 缓存缺少 scripts/ 时 Agent 定位成本高。
4. **RF-04 历史保守决策（codex 终审 I5）**：缺 CodeGraph 段落的 code-reading.md 两模式仅 report-only，与 no-interrupt "单次 apply 全自动"的承诺冲突，用户被要求手动合并；而 merge_markdown 天然支持"模板有、项目无的章节"合并，项目内容全保留且有备份屏障，自动合并风险可控。

## What Changes

- **merge_markdown 幂等修复（方案 A）**：项目独有行过滤中排除合并保留字 `**项目补充**` 标记行，使 `merge(t, merge(t, x)) == merge(t, x)`；已污染文件下次合并自动清除重复标记（自愈，无需人工恢复备份）。
- **unchanged 跳过写盘**：no-interrupt 合并结果与现有文件逐字一致时跳过写盘并报告 `unchanged`，避免幂等后重跑仍刷新文件。
- **dry-run 冲突报告模式感知**：no-interrupt 下普通规则 drift 冲突条目增加反映真实动作的字段（`no_interrupt_action: "markdown-merge"`），普通模式报告不变。
- **RF-04 去特判**：删除 `codegraph-section-missing` 报告型特判（compute_plan 与 step_s3 两处），缺 CodeGraph 段落的 code-reading.md 回归普通规则文件统一 drift 处理：普通模式照常询问、no-interrupt 自动章节合并。**BREAKING**：两模式 report-only 行为移除，no-interrupt 下此类文件将被自动合并写盘（有备份屏障）。
- **SKILL.md 定位规则补全**：补充 plugin 安装场景的脚本权威定位规则与"缓存缺 scripts/ 时重装 plugin"指引（纯文档）。
- **回归测试**：新增 merge_markdown 重跑幂等用例、unchanged 跳过写盘用例、no-interrupt 报告字段用例；删改 RF-04 report-only 旧断言，改为自动合并断言。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rule-config-scripted-execution`: 「合并与保护语义脚本内确定性实现」需求增加合并幂等性约束（项目补充标记为合并保留字、重跑幂等、unchanged 跳过写盘）；缺 CodeGraph 段落的规则文件 MUST 走统一 drift/合并路径，不再 report-only；dry-run 冲突报告在 no-interrupt 下 MUST 标注真实执行动作。

## Impact

- **代码**：`cadence-init/skills/rule-config/scripts/rule-config.py`（merge_markdown 过滤、step_s3 普通规则 no-interrupt 分支 unchanged 判定、compute_plan RF-04 特判与冲突报告字段、step_s3 RF-04 特判分支删除）
- **文档**：`cadence-init/skills/rule-config/references/merge-semantics.md`（NC-03 行补充幂等语义、RF-04 行改写为统一合并）、`cadence-init/skills/rule-config/SKILL.md`（脚本定位规则）
- **测试**：`cadence-init/skills/rule-config/tests/test_rule_config.py` 及 `tests/skill-clause-map.md` 映射更新
- **行为兼容**：no-interrupt 下缺 CodeGraph 段落的 code-reading.md 由"仅报告"变为"自动合并写盘"（BREAKING，有备份可回滚）；其余场景行为不变
- **非目标**：P2 增强项（脚本单文件拆分、近似行去重）不纳入；不改变普通模式冲突询问流程
