# Tasks: extend-artifact-toggle-to-code

## 1. 失败测试先行（TDD）

- [x] 1.1 新增开关迁移单测：旧名 `design/plan` 开启行 → 迁移为新名且保留 `开启`；旧名非法值 → 迁移为新名、保留原文并 warning；旧名+新名并存 → 归并为恰好一行新名（首个值为准，冲突按关+warning）；运行 `python3 -m unittest tests.test_rule_config` 确认新用例失败（脚本仍只认旧名前缀）
- [x] 1.2 既有开关用例基准改新名（写入断言、非法值、去重、章节归并、双入口），先确认这些用例对新名失败（脚本未改）

## 2. 脚本与模板

- [x] 2.1 `scripts/rule-config.py`：新增 `TOGGLE_PREFIX_LEGACY`，`_ensure_commit_toggle` 匹配扩展为旧名或新名前缀、规范输出恒为新名；不改动归并/告警逻辑
- [x] 2.2 运行单测确认 1.1/1.2 全绿
- [x] 2.3 L0 v3 模板开关句按 design D2 文案更新（wc -c ≤2560），同步 `document-storage.md`、rule-config `SKILL.md`、`references/merge-semantics.md` 中开关引用；运行单测 + harness 全绿

## 3. 本仓库实测

- [x] 3.1 本仓库 rule-config dry-run + apply：确认入口开关行为新名（本仓库原本无开关行→写入默认 `关闭`）、L0 区块与模板逐字一致、harness 98 PASS + 单测全绿，记录输出
