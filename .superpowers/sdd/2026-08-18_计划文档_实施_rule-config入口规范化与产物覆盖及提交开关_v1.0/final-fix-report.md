# 全分支终审修复报告

## 修复范围

本轮仅处理终审指出的两项问题：

1. dry-run 报告缺少入口规范化 warnings，导致 dry-run/apply 三态诊断不一致；
2. 修正文档中对 L0-04 报告字段的过度声称。

## 实现修复

`rule-config.py` 新增 `_planned_entry_warnings` 只读预演：

- 复用 `_compose_entry`、`_normalize_mandatory_rules`、`_ensure_commit_toggle` 等纯函数；
- 以 `compute_plan` 的入口资产和技术栈检测结果在内存中合成，不创建文件、不写入目标项目、不执行备份；
- 模拟 S3 已按 CLI 意图启用 Playwright 的条件文件，确保 S4 条件清单与 apply 一致；
- 在 dry-run 模板定位成功后将 warnings 写入顶层报告；模板定位失败仍保持 fail-closed 路径。

同时将 `merge-semantics.md` 的 L0-04 报告要求从“旧版来源/例外及升级到 v2”修正为实际产出的“备份路径、处理动作与分支”。

## TDD 与验证

先新增 RED 回归 `TestEndToEndRegression.test_dry_run_warnings_match_apply`，构造重复 `## 强制规则` 与孤立规则 6，确认修复前 dry-run 为 `[]` 而 apply 含 `DUPLICATE_H2` / `ORPHAN_RULE6`。随后实现只读 planned warnings，测试转绿。

验证结果：

- `python3 -m unittest cadence-init.skills.rule-config.tests.test_rule_config.TestEndToEndRegression cadence-init.skills.rule-config.tests.test_rule_config.TestNormalizeMandatoryRules -v`：18/18 通过；
- `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -v`：216/216 通过；
- `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`：`SUMMARY pass=104 fail=0`；
- 干净临时项目 dry-run/apply warnings 均为空，保持幂等语义；含诊断入口的临时项目两份 warnings 列表及 code/file 集合相等。

## 风险评估

本轮未改变 apply 发布路径、入口规范化语义或备份屏障；新增逻辑只在 dry-run 中进行内存预演。唯一残余假设是 dry-run 后至 apply 前目标项目和模板不发生外部变化，符合任务契约中“无用户干预、无外部修改”条件。

## 章节外孤儿开关行修复追加

依据 change spec `superpowers-artifact-governance` 的“章节外孤儿开关行归并”场景，`_ensure_commit_toggle` 现先全文收集 `TOGGLE_PREFIX` 行，再将所有开关行收敛到首个 `## 项目配置` 章节的规范位置：

- 章节外孤儿行被删除并归并；全文件最终恰好一行开关行；
- 孤儿值与章节值一致且合法时保留该值；
- 孤儿/章节值冲突或归并集合含非法值时按 `关闭` 处理，并发出 `INVALID_TOGGLE`，detail 含原因和值集合；
- 章节内仅一行时保持既有用户值语义，非法值原文保留并告警；既有重复章节内开关测试继续保留首行；
- 归并结果二次运行逐字幂等。

新增四个回归测试覆盖孤儿单独归并、同值去重、冲突关闭告警和幂等；同时同步收紧 change spec 对既有章节内单一非法值保留语义的表述。

验证结果：

- `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -v`：221/221 通过；
- `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`：`SUMMARY pass=104 fail=0`。
