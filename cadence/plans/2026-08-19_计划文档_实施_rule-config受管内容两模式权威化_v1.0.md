# rule-config 受管内容两模式权威化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 rule-config 六类框架受管内容 drift 的普通模式处理从"询问 keep/replace、默认保留"统一为与 no-interrupt 一致的"归档 + 权威覆盖/归并/移除"，两模式全程不经用户决策。

**Architecture:** 计划层（`compute_plan`）不再为受管 drift 生成决策冲突条目，资产以确定性动作 + 备份需求表达；执行层（`step_s3/s4/s7`）删除普通模式 decision 分支，合流到现有 no-interrupt 权威路径；全局备份屏障与原子发布机制不变；决策文件机制（`--decisions`/`validate_decisions`/`default_keep`）保留为休眠兜底。

**Tech Stack:** Python 3（标准库 + PyYAML）、pytest（`tests/test_rule_config.py`）、bash 生命周期测试（`tests/verify-managed-lifecycle.sh`）。

**Spec:** `openspec/changes/rule-config-authoritative-overwrite/`（proposal.md / design.md / specs/ / tasks.md —— 本计划只展开该契约，不重定义范围）

**OpenSpec 工作包映射：** Task 1~5 ↔ tasks.md 工作包 1（测试先行）与 2（脚本实现）；Task 6~8 ↔ 工作包 3（文档与对账）；Task 9 ↔ 工作包 4（全量验证）。

## Global Constraints

- 备份路径结构不变：`cadence/legacy/<14位时间戳[-N]>/<相对项目根路径>`，归档失败即终止且原文件不变。
- 幂等契约不变：内容与目标一致时跳过写盘、零归档，报告标记 `unchanged`/幂等跳过。
- 普通模式与 no-interrupt 的剩余差异仅两处：HM 历史目录迁移、`--project-type` 提升权。不得新增第三处差异。
- 框架受管规则文件 MUST NOT 产生 `**项目补充**`/`原项目补充` 段落，MUST NOT 调用 `merge_markdown`。
- L1 版本识别逻辑（`classify_l1`）不得改动；只有 replace 类状态的决策权变更。
- `merge_markdown`、`validate_decisions`、`default_keep`、`--decisions` 机制代码保留（休眠兜底），不得删除。
- 报告 schema 不变：顶层 `warnings` 五码枚举、`hints.next: "mcp-configuration"`、`overall` 三值。
- 新分支命名：S3 非 L1 → `authoritative-overwrite`；S3 L1 → `l1-authoritative-<state>`；S4 → `authoritative-<state>`；S7 rules.apply → `rules-apply-removed`；S7 模板替换 → `template-replace`。退役 `rules-keep`/`rules-replace`/`l1-keep`/`l1-replace`/`keep-<state>`/`replace-<state>`/`no-interrupt-<state>`/`<kind>-preserve`/`<kind>-terminate`。
- S7 资产动作新取值：`rules.apply` → `remove-apply`；`structure`/`unparseable`/`unreadable` → `replace`。退役 `keep` 动作取值。
- 测试运行目录：`cadence-init/skills/rule-config/`；pytest 命令 `python3 -m pytest tests/test_rule_config.py -q`；生命周期命令 `bash tests/verify-managed-lifecycle.sh`。
- 提交信息遵循仓库既有风格（参照 `git log --oneline -5`）。

## 任务间状态说明（执行者必读）

Task 1 完成后：step 函数尚未合流，普通模式 CLI 对 drift 资产因决策缺失走旧 keep 分支（不写入），故 shell 的 B2/B6/B7/C4 旧断言（"普通模式保留"）仍然通过；仅四个**决策编排**用例（B2b/B6b/C2b/C2c，依赖计划层冲突条目）在本任务内删除，C17f 同步改写。Task 2~4 每完成一个，对应 shell 用例同步翻转为新语义。每个 Task 结束态：pytest 全量 PASS + shell 全量 pass。

---

### Task 1: compute_plan 移除四类冲突生成 + `_backup_required_for` 适配 + 计划层测试改写

计划层语义锚点：drift 资产保留 `action`/`conflict`/`backup_needed` 与 `backup_needs` 登记，仅删除决策队列条目（`plan["conflicts"]` 及 step 级 `conflicts`）。S7 资产动作同步改名（`keep` → `remove-apply`/`replace`），`_backup_required_for` 必须同任务适配（新动作名不被旧过滤逻辑识别会导致 B8 的"备份后终止"失去备份）。

**映射：** tasks.md 1.1/1.2/1.3/1.4（计划侧）+ 2.1 + 2.5（备份过滤部分）；requirement「脚本两阶段执行与模式衔接」之「当前无活跃冲突类型」scenario。

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（S3 L1 冲突块 ~1490-1511；S3 非 L1 冲突块 ~1529-1555；S4 drift/broken 冲突块 ~1610-1624；S7 冲突块 ~1723-1766；`_backup_required_for` ~3474-3552）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`
- Test: `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`（删除 B2b/B6b/C2b/C2c；改写 C17f）

**Interfaces:**
- Consumes: 现有 `compute_plan(root, intents) -> plan`、`rc.STEP_RULES_FILES/STEP_ENTRY_FILES/STEP_OPENSPEC_CONFIG`、测试模块级常量 `V2_START`/`V2_END`/`L0_SOURCE`、helper `_intents()`。
- Produces: `plan["conflicts"]` 对受管 drift 恒为空；S7 资产 `action` 新枚举 `remove-apply`/`replace`（Task 4 的消费方）；`_backup_required_for` 对 S3 冲突资产/S4 `upgrade|dedup|replace`/S7 `remove-apply|replace` 两模式恒返回 True。

- [ ] **Step 1: 改写 `TestComputePlanFinalReview::test_recommendations_are_conservative_keep` 为无冲突断言（红）**

整个方法替换为：

```python
    def test_managed_drift_produces_no_conflicts(self):
        """ut-compute-plan-managed-no-conflict / 契约「当前无活跃冲突类型」
        （s3 普通 drift / s3 L1 / s4 L0 drift / s7 rules.apply 均不产冲突条目，
        资产以确定性动作 + 备份需求表达）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "language.md").write_text("本地漂移\n", encoding="utf-8")
        (rules_dir / rc.L1_RULE_FILENAME).write_text("L1 本地漂移\n", encoding="utf-8")
        (self.root / "CLAUDE.md").write_text(
            "# CLAUDE.md\n\n" + V2_START + "\n漂移\n" + V2_END + "\n", encoding="utf-8"
        )
        (self.root / "AGENTS.md").write_text("# AGENTS.md\n无标记\n", encoding="utf-8")
        (self.root / "openspec").mkdir()
        (self.root / "openspec" / "config.yaml").write_text(
            "schema: spec-driven\nrules:\n  apply:\n    - x\n", encoding="utf-8"
        )
        plan = rc.compute_plan(self.root, _intents())
        conflicts = self._conflicts_by_id(plan)
        # 四类受管 drift 均不产决策冲突
        self.assertFalse(
            any(cid.startswith(("s3:", "s4:", "s7:")) for cid in conflicts),
            f"不应再有冲突条目: {list(conflicts)}",
        )
        # 资产以确定性动作 + 备份需求表达
        s3_assets = {a["path"]: a for a in plan["steps"][rc.STEP_RULES_FILES]["assets"]}
        self.assertEqual(s3_assets[".claude/rules/language.md"]["action"], "replace")
        self.assertTrue(s3_assets[".claude/rules/language.md"]["backup_needed"])
        self.assertEqual(
            s3_assets[f".claude/rules/{rc.L1_RULE_FILENAME}"]["action"], "replace"
        )
        s4_assets = {a["path"]: a for a in plan["steps"][rc.STEP_ENTRY_FILES]["assets"]}
        self.assertEqual(s4_assets["CLAUDE.md"]["action"], "replace")
        self.assertTrue(s4_assets["CLAUDE.md"]["backup_needed"])
        s7_assets = {
            a["path"]: a for a in plan["steps"][rc.STEP_OPENSPEC_CONFIG]["assets"]
        }
        self.assertEqual(s7_assets["openspec/config.yaml"]["action"], "remove-apply")
        self.assertTrue(s7_assets["openspec/config.yaml"]["backup_needed"])
```

- [ ] **Step 2: 改写 `test_drift_still_conflict_with_allowed_decisions` 为确定性动作断言（红）**

```python
    def test_l0_drift_is_deterministic_action_not_conflict(self):
        """ut-compute_plan-l0-drift-deterministic / 契约「当前无活跃冲突类型」
        （drift/broken 不产 decision 冲突，以 replace 确定性动作 + 备份屏障表达）"""
        (self.root / "CLAUDE.md").write_text(
            "# CLAUDE.md\n\n" + V2_START + "\n漂移\n" + V2_END + "\n", encoding="utf-8"
        )
        plan = rc.compute_plan(self.root, _intents())
        conflicts = self._conflicts_by_id(plan)
        self.assertNotIn("s4:CLAUDE.md", conflicts)
        asset = next(
            a for a in plan["steps"][rc.STEP_ENTRY_FILES]["assets"]
            if a["path"] == "CLAUDE.md"
        )
        self.assertEqual(asset["action"], "replace")
        self.assertTrue(asset["backup_needed"])
        self.assertIn(self.root / "CLAUDE.md", plan["backup_needs"])
```

- [ ] **Step 3: 更新 `TestCodegraphSectionUnifiedMerge::test_missing_codegraph_section_is_plain_drift`（红→绿随实现）**

删除其中对 `plan["conflicts"]` 含 code-reading.md 的断言（约 3122-3128 行的 `assertTrue(any(... plan["conflicts"]))` 块），保留资产 `action`/`conflict`/`backup_needed`/`backup_needs` 断言与 `codegraph-section-missing` 否定断言；docstring 改为 `ut-s3-codegraph-section-unified-drift / RF-04（缺 CodeGraph 段落 → 普通 drift 动作，进备份需求，不产冲突）`。

- [ ] **Step 4: 删除 `TestDriftConflictNoInterruptAction` 整个类（约 2745-2804 行，4 用例）**

`no_interrupt_action` 字段随冲突条目一并移除（Task 5 清理转发代码），整类删除。

- [ ] **Step 5: 改写 `TestTask6RegressionMatrix` 两个 dry-run 字段用例（红）**

`test_dry_run_no_interrupt_action_field` 与 `test_dry_run_normal_mode_no_field` 两个方法整体替换为：

```python
    def test_dry_run_drift_plan_no_conflict_replace_action(self):
        """drift 计划：两模式 dry-run 均无冲突条目，资产动作 replace + 备份需求"""
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "mcp-servers.md").write_text("drift", encoding="utf-8")
        for ni in (False, True):
            report = {}
            with mock.patch.object(
                rc, "locate_templates",
                return_value=(self.rules_root, self.openspec_yaml),
            ):
                code = rc.run_dry_run(
                    self.root, _intents(no_interrupt=ni), report
                )
            self.assertEqual(code, 0)
            self.assertFalse(
                any("mcp-servers" in c.get("conflict_id", "")
                    for c in report.get("conflicts", []))
            )
            step = next(
                s for s in report["steps"] if s["name"] == rc.STEP_RULES_FILES
            )
            asset = next(a for a in step["assets"] if "mcp-servers" in a["path"])
            self.assertEqual(asset["action"], "replace")
            self.assertTrue(asset["backup_needed"])
```

- [ ] **Step 6: 改写 `TestFilterBackupNeeds` 四个用例（红）**

`test_s3_keep_decision_not_backed_up` → `test_s3_drift_always_backed_up`：

```python
    def test_s3_drift_always_backed_up(self):
        """ut-filter-backup-s3-drift / 契约（drift 两模式均写入 → 均备份，与决策无关）"""
        target = self.root / ".claude" / "rules" / "language.md"
        plan = self._plan(
            s3_assets=[{
                "path": ".claude/rules/language.md", "action": "replace",
                "conflict": "drift", "backup_needed": True,
            }],
        )
        plan["backup_needs"] = [target]
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [target])
        self.assertEqual(
            rc._filter_backup_needs(plan, _intents(no_interrupt=True), self.root),
            [target],
        )
```

`test_s4_upgrade_always_backed_up_drift_keep_not` → `test_s4_upgrade_and_drift_always_backed_up`：

```python
    def test_s4_upgrade_and_drift_always_backed_up(self):
        """ut-filter-backup-s4-states / 契约（upgrade/drift 两模式均写入 → 均备份，与决策无关）"""
        entry = self.root / "CLAUDE.md"
        plan = self._plan(s4_assets=[{
            "path": "CLAUDE.md", "action": "upgrade",
            "conflict": "upgrade", "backup_needed": True,
        }])
        plan["backup_needs"] = [entry]
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [entry])
        plan2 = self._plan(s4_assets=[{
            "path": "CLAUDE.md", "action": "replace",
            "conflict": "drift", "backup_needed": True,
        }])
        plan2["backup_needs"] = [entry]
        self.assertEqual(rc._filter_backup_needs(plan2, _intents(), self.root), [entry])
        self.assertEqual(
            rc._filter_backup_needs(plan2, _intents(no_interrupt=True), self.root),
            [entry],
        )
```

`test_s7_rules_apply_default_keep_not_backed_up` → `test_s7_remove_apply_always_backed_up`：

```python
    def test_s7_remove_apply_always_backed_up(self):
        """ut-filter-backup-s7-remove-apply / 契约（移除禁用键两模式均写入 → 均备份）"""
        config = self.root / "openspec" / "config.yaml"
        config.parent.mkdir(parents=True)
        config.write_text(
            "schema: spec-driven\nrules:\n  apply:\n    - x\n", encoding="utf-8",
        )
        plan = self._plan(s7_assets=[{
            "path": "openspec/config.yaml", "action": "remove-apply",
            "conflict": {"kind": "rules.apply"}, "backup_needed": True,
        }])
        plan["backup_needs"] = [config]
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [config])
        self.assertEqual(
            rc._filter_backup_needs(plan, _intents(no_interrupt=True), self.root),
            [config],
        )
```

`test_s7_structure_conflict_normal_not_backed_up_no_interrupt_backed_up` → `test_s7_replace_always_backed_up`：

```python
    def test_s7_replace_always_backed_up(self):
        """ut-filter-backup-s7-replace / 契约（模板整体替换两模式均写入 → 均备份）"""
        config = self.root / "openspec" / "config.yaml"
        config.parent.mkdir(parents=True)
        config.write_text("schema: [1]\n", encoding="utf-8")
        plan = self._plan(s7_assets=[{
            "path": "openspec/config.yaml", "action": "replace",
            "conflict": {"kind": "structure", "fields": ["schema"]},
            "backup_needed": True,
        }])
        plan["backup_needs"] = [config]
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [config])
        self.assertEqual(
            rc._filter_backup_needs(plan, _intents(no_interrupt=True), self.root),
            [config],
        )
```

- [ ] **Step 7: 运行确认红**

Run: `cd cadence-init/skills/rule-config && python3 -m pytest tests/test_rule_config.py::TestComputePlanFinalReview tests/test_rule_config.py::TestCodegraphSectionUnifiedMerge tests/test_rule_config.py::TestTask6RegressionMatrix tests/test_rule_config.py::TestFilterBackupNeeds -q`
Expected: 本任务新断言 FAIL（冲突仍存在 / 新动作名未实现 / 旧过滤逻辑保留 keep 豁免）；未点名用例（insert/upgrade/dedup 确定性、`test_unmatched_target_conservatively_kept`、`test_s7_idempotent_merge_not_backed_up` 等）保持 PASS。

- [ ] **Step 8: 实现——S3 非 L1 分支删除冲突生成（rule-config.py 约 1524-1556 行）**

保留资产追加与 `_append_backup_need`，删除 `s3_conflict`/`top_conflict` 构造、`no_interrupt_action` 标注与两处 `conflicts` 追加。改后该分支主体：

```python
            else:
                s3["assets"].append({
                    "path": rel, "template_source": src_name,
                    "action": "replace", "conflict": "drift",
                    "backup_needed": True, "is_l1": False,
                })
                # 契约「当前无活跃冲突类型」：drift 为两模式确定性动作，
                # 以资产动作 + 备份需求表达，不产决策冲突条目。
                _append_backup_need(plan, target)
```

- [ ] **Step 9: 实现——S3 L1 分支删除冲突生成（约 1484-1511 行）**

保留资产追加与 `_append_backup_need(plan, target)`，删除 `s3["conflicts"].append(...)` 与 `plan["conflicts"].append(...)` 两个块及其 C3 注释。

- [ ] **Step 10: 实现——S4 drift/broken 分支删除冲突生成（约 1603-1625 行）**

保留 `s4["assets"].append({... "action": "replace", "conflict": state, "backup_needed": True})` 与 `_append_backup_need(plan, entry_path)`，删除 `plan["conflicts"].append({...})` 整块；分支注释改为 `# drift/broken → 两模式确定性替换/归并（屏障归档后执行），不产决策冲突`。

- [ ] **Step 11: 实现——S7 冲突分支改为动作改名（约 1723-1766 行）**

将整个 `else:`（conflict 非空）分支替换为：

```python
        else:
            # 契约「当前无活跃冲突类型」：rules.apply 两模式移除并保守合并；
            # structure/unparseable/unreadable 两模式归档后以模板整体替换。
            # 均以资产动作 + 备份需求表达，不产决策冲突条目。
            action = (
                "remove-apply"
                if conflict["kind"] == "rules.apply"
                else "replace"
            )
            s7["assets"].append({
                "path": "openspec/config.yaml",
                "action": action,
                "conflict": conflict,
                "backup_needed": True,
            })
```

同时删除该分支上方注释中"rules.apply 冲突：allowed_decisions=…"等决策描述行；`DECISION_REMOVE_APPLY`/`DECISION_KEEP` 常量保留（休眠机制仍引用）。

- [ ] **Step 12: 实现——`_backup_required_for` 三段适配**

S3 段替换为：

```python
    # S3 规则文件
    for asset in (steps.get(STEP_RULES_FILES, {}) or {}).get("assets", []) or []:
        if not _matches(asset):
            continue
        # 两模式统一：带冲突状态（drift/upgrade/replace）即写入 → 备份；无冲突跳过不备份
        return bool(asset.get("conflict"))
```

S4 段替换为：

```python
    # S4 入口文件
    for asset in (steps.get(STEP_ENTRY_FILES, {}) or {}).get("assets", []) or []:
        if not _matches(asset):
            continue
        action = asset.get("action")
        if action in ("upgrade", "dedup", "replace"):
            # 确定性升级/归并/漂移替换（两模式同动作）→ 始终写入
            return True
        return False
```

S7 段：保留 `action == "merge"` 幂等判定块不变，其后 `if action == "keep" and isinstance(conflict, dict):` 整块替换为：

```python
        if action in ("remove-apply", "replace"):
            # 移除禁用键/模板整体替换（两模式同动作）→ 始终写入
            return True
        return False
```

同步重写 `_backup_required_for` docstring 的规则清单（删除 keep 决策/no-interrupt 分流描述，改为"两模式同动作即写入即备份"；保留 S7 merge 幂等剔除与"无法归属→保守保留"两条）。

- [ ] **Step 13: shell 删除四个决策编排用例 + 改写 C17f**

`verify-managed-lifecycle.sh` 中：

1. 删除 B2b 整段（`it-l0-drift-normal-keep-default`，约 584-604 行）与 B6b 整段（`it-l1-drift-normal-keep-default`，约 688-708 行）：keep 决策编排路径随计划层冲突消亡。B6b 删除后，其后备份失败段落的评审 M3 注释中"隐含「L1-02 普通模式零写入」假设"字样改为"基准取故障注入运行前目标 hash，与前置运行结果无关"。
2. 删除 C2b（`it-decisions-unknown`）与 C2c（`it-decisions-stale`）整段（约 862-895 行）：零冲突计划下 `run_apply` 跳过 decisions 读取，CLI 级 fail-closed 不可复现；机制兜底由 Task 5 的 `TestValidateDecisionsDormant` 单测覆盖。C2 区首注释追加一行：`# 2026-08-19：六类受管冲突转确定性动作后，unknown/stale 决策的 CLI 触发路径消亡，移至 ut-validate-decisions-* 单测。`
3. C17f（`it-dryrun-report-completeness`，约 1906-1916 行）：将 `jqr "['conflicts']" | grep -q 'allowed_decisions'` 断言改为断言 conflicts 为空：

```bash
# C17f. dry-run 报告完整性：无活跃冲突类型（conflicts 为空）、steps 含真实 elapsed_ms
# （it-dryrun-report-completeness / codex 终审 I4 + 2026-08-19 权威化）。
case_root="$(mk_drift_fixture fx-dryrun-completeness)"
run_script dry-run "$case_root"
if [ "$RUN_STATUS" -eq 0 ] \
  && jqr "['conflicts']" 2>/dev/null | grep -q '\[\]' \
  && assert_report_completeness "$REPORT"; then
  record_result it-dryrun-report-completeness "$RUN_STATUS" present present pass
else
  record_result it-dryrun-report-completeness "$RUN_STATUS" present missing fail
fi
```

- [ ] **Step 14: 运行确认绿**

Run: `cd cadence-init/skills/rule-config && python3 -m pytest tests/test_rule_config.py -q && bash tests/verify-managed-lifecycle.sh`
Expected: pytest 全量 PASS；shell 全部 pass。注意中间态说明：step 函数未合流，普通模式 CLI 对 drift 资产因决策缺失走旧 keep 分支（不写入），B2/B6/B7/C4 旧断言（普通模式保留）本任务后仍通过，Task 2~4 逐一翻转。

- [ ] **Step 15: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/
git commit -m "refactor(rule-config): compute_plan 移除受管 drift 决策冲突生成，备份过滤两模式适配"
```

---

### Task 2: step_s3 两模式合流（含 L1）+ S3 测试与 shell 用例

**映射：** tasks.md 1.1/1.2 + 2.2；requirement「合并与保护语义脚本内确定性实现」之「普通模式框架规则文件权威覆盖」scenario、「L1 框架规则升级必须保护无法识别的本地内容」。

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`step_s3_rules_files` L1 分支与框架规则分支 ~2127-2176）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`
- Test: `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`（C4 ~1037-1049；B6 ~669-686）

**Interfaces:**
- Consumes: Task 1 的计划层产出（drift 资产 `action="replace"`）。
- Produces: 动作日志分支名 `authoritative-overwrite`（非 L1）、`l1-authoritative-<state>`（L1）；退役 `rules-replace`/`rules-keep`/`l1-no-interrupt`/`l1-replace`/`l1-keep`。

- [ ] **Step 1: 新增普通模式覆盖单测（红）**

`TestStepS3RulesFiles` 新增两个方法：

```python
    def test_ordinary_normal_mode_overwrites_with_template(self):
        """ut-step_s3-authoritative-overwrite-normal / RF-05（普通模式无决策 → 模板权威全覆盖）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / "language.md"
        target.write_text(self.language_tpl + "\n项目独有行\n", encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_RULES_FILES: {
                "name": rc.STEP_RULES_FILES, "status": "ok",
                "assets": [{
                    "path": ".claude/rules/language.md", "action": "replace",
                    "conflict": "drift", "backup_needed": True, "is_l1": False,
                }],
            }
        })
        rc.step_s3_rules_files(self.root, _intents(), plan, {})
        result = target.read_text(encoding="utf-8")
        self.assertEqual(result, self.language_tpl)
        self.assertNotIn("项目补充", result)
        self.assertNotIn("项目独有行", result)

    def test_l1_normal_mode_replaced_with_v1(self):
        """ut-step_s3-l1-authoritative-normal / L1-04~06（普通模式无决策 → 替换为当前框架版本）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / rc.L1_RULE_FILENAME
        target.write_text("# 被篡改的旧版\n项目内容\n", encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_RULES_FILES: {
                "name": rc.STEP_RULES_FILES, "status": "ok",
                "assets": [{
                    "path": f".claude/rules/{rc.L1_RULE_FILENAME}", "action": "replace",
                    "conflict": "replace", "backup_needed": True, "is_l1": True,
                }],
            }
        })
        rc.step_s3_rules_files(self.root, _intents(), plan, {})
        result = target.read_text(encoding="utf-8")
        self.assertEqual(result, self.l1_v1)
        self.assertNotIn("项目补充", result)
```

- [ ] **Step 2: 运行确认红**

Run: `python3 -m pytest tests/test_rule_config.py::TestStepS3RulesFiles -q`
Expected: 两个新用例 FAIL（普通模式仍走 `rules-keep`/`l1-keep` 保留分支）；旧用例 PASS。

- [ ] **Step 3: 实现——step_s3 L1 分支合流**

将 L1 分支（`if is_l1:` 内 no-interrupt/decision 分流）整体替换为：

```python
        if is_l1:
            # --- L1 独立分支：绝不调 merge_markdown，结果绝不含「项目补充」 ---
            # 两模式统一：备份已由全局屏障完成；直接写当前模板（upgrade/replace 均替换）。
            atomic_write(target, template_text)
            actions_log.append({
                "path": asset["path"], "action": "replaced",
                "branch": f"l1-authoritative-{conflict}",
            })
```

- [ ] **Step 4: 实现——step_s3 框架规则分支合流**

非 L1 冲突资产分支删除 `if intents.no_interrupt: ... else: decision == DECISION_REPLACE ...` 分流，保留幂等检查后统一覆盖：

```python
        else:
            # --- 框架受管规则文件：两模式统一权威全覆盖（不调 merge_markdown；屏障已归档）---
            existing_text = _safe_read(target)
            if existing_text == template_text:
                actions_log.append({
                    "path": asset["path"],
                    "action": "unchanged",
                    "branch": "authoritative-idempotent",
                })
                continue
            atomic_write(target, template_text)
            actions_log.append({
                "path": asset["path"],
                "action": "overwritten",
                "branch": "authoritative-overwrite",
            })
```

同时删除函数首部不再使用的 `decisions_map = plan.get("decisions_map", {}) or {}` 与 `conflict_id` 变量（若无其他引用）。

- [ ] **Step 5: 运行确认绿**

Run: `python3 -m pytest tests/test_rule_config.py -q`
Expected: 全量 PASS。

- [ ] **Step 6: shell C4 改写（`it-s3-normal-keep-decision` → `it-s3-normal-authoritative-overwrite`）**

`verify-managed-lifecycle.sh` 约 1037-1049 行整段替换为：

```bash
# C4. 普通模式规则 drift 权威覆盖（it-s3-normal-authoritative-overwrite / RF-05）
# 契约：普通模式不再询问 keep/replace，drift 归档后以模板原子覆盖，全程无决策文件。
case_root="$TEST_ROOT/fx-existing-rules"
mkdir -p "$case_root/.claude/rules"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
cp "$TEST_DIR/../references/rules/language.md" "$case_root/.claude/rules/language.md"
printf '\n# 用户自定义补充\n覆盖我\n' >> "$case_root/.claude/rules/language.md"
before=$(sha256_file "$case_root/.claude/rules/language.md")
run_script apply "$case_root"
after=$(sha256_file "$case_root/.claude/rules/language.md")
if [ "$RUN_STATUS" -eq 0 ] \
  && cmp -s "$case_root/.claude/rules/language.md" "$TEST_DIR/../references/rules/language.md" \
  && legacy_archive_exists "$case_root" '.claude/rules/language.md'; then
  assert_changed it-s3-normal-authoritative-overwrite "$RUN_STATUS" "$before" "$after"
else
  record_result it-s3-normal-authoritative-overwrite "$RUN_STATUS" "$before" "$after" fail
fi
```

- [ ] **Step 7: shell B6 改写（`it-s3-l1-drift-normal` → `it-s3-l1-drift-normal-replaced`）**

B6 段（约 669-686 行）的普通模式断言由"保留"改为"替换+归档"：

```bash
# B6. L1 漂移两模式统一替换（it-s3-l1-drift-normal-replaced / L1-04~06）。
# 契约：普通模式不再询问，drift 归档后替换为当前框架版本；备份失败保留见 it-s3-l1-backup-failure-preserved。
case_root="$TEST_ROOT/fx-l1"
mkdir -p "$case_root/.claude/rules"
cp "$L1_SOURCE" "$case_root/.claude/rules/openspec-superpowers-workflow.md"
printf '\n本地漂移\n' >> "$case_root/.claude/rules/openspec-superpowers-workflow.md"
l1_target="$case_root/.claude/rules/openspec-superpowers-workflow.md"
before=$(sha256_file "$l1_target")
run_script apply "$case_root"
after=$(sha256_file "$l1_target")
if [ "$RUN_STATUS" -eq 0 ] && cmp -s "$l1_target" "$L1_SOURCE" \
  && legacy_archive_exists "$case_root" '.claude/rules/openspec-superpowers-workflow.md'; then
  assert_changed it-s3-l1-drift-normal-replaced "$RUN_STATUS" "$before" "$after"
else
  record_result it-s3-l1-drift-normal-replaced "$RUN_STATUS" "$before" "$after" fail
fi
```

- [ ] **Step 8: 运行确认绿**

Run: `bash tests/verify-managed-lifecycle.sh`
Expected: 全部 pass；结果清单含 `it-s3-normal-authoritative-overwrite`、`it-s3-l1-drift-normal-replaced`，不含 `it-s3-normal-keep-decision`、`it-s3-l1-drift-normal`。

- [ ] **Step 9: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/
git commit -m "feat(rule-config): S3 规则文件与 L1 drift 两模式统一权威覆盖（归档+模板替换）"
```

---

### Task 3: step_s4 两模式合流（L0 drift/broken）+ L0 测试与 shell 用例

**映射：** tasks.md 1.3 + 2.3；requirement「L0 入口内容必须版本化且可安全升级」之「当前 v1 受管区块存在内容漂移」「单侧或顺序错误标记确定性归并」scenario。

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`step_s4_entry_files` drift/broken 分支 ~2333-2351）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`
- Test: `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`（B2 ~564-582）

**Interfaces:**
- Consumes: `_compose_entry(existing, kernel_source, state=..., project_type=..., entry_name=..., existing_rule_files=...)`（drift/broken 状态内部走 `_normalize_l0_to_single_block` 确定性归并）。
- Produces: 动作日志分支名 `authoritative-<state>`；退役 `no-interrupt-<state>`/`replace-<state>`/`keep-<state>`。

- [ ] **Step 1: 新增普通模式 drift 替换单测（红）**

`TestStepS4EntryFiles` 新增（现有 `test_drift_replaced_block_matches_source_outside_preserved` 的普通模式变体）：

```python
    def test_drift_replaced_normal_mode_outside_preserved(self):
        """ut-step_s4-drift-replace-normal / L0-03（普通模式无决策 → 区块=规范源，区块外保留）"""
        entry = self.root / "CLAUDE.md"
        drift_block = rc.L0_BEGIN + "\n漂移内容\n" + rc.L0_END
        original = "# CLAUDE.md\n\n文件说明\n\n" + drift_block + "\n## 强制规则\n\n- 用户规则\n"
        entry.write_text(original, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_ENTRY_FILES: {
                "name": rc.STEP_ENTRY_FILES, "status": "ok",
                "assets": [{
                    "path": "CLAUDE.md", "action": "replace",
                    "conflict": "drift", "backup_needed": True,
                }],
            }
        })
        rc.step_s4_entry_files(self.root, _intents(), plan, {})
        result = entry.read_text(encoding="utf-8")
        begin = result.index(rc.L0_BEGIN)
        end = result.index(rc.L0_END, begin) + len(rc.L0_END)
        self.assertEqual(result[begin:end].strip(), self.kernel.strip())
        self.assertNotIn("漂移内容", result)
        self.assertIn("- 用户规则", result)
```

- [ ] **Step 2: 运行确认红**

Run: `python3 -m pytest tests/test_rule_config.py::TestStepS4EntryFiles -q`
Expected: 新用例 FAIL（普通模式 drift 仍 `kept`）；其余 PASS。

- [ ] **Step 3: 实现——step_s4 drift/broken 分支合流**

将 `# drift/broken → 按模式/决策处理。` 起的整段（`decision = decisions_map.get(conflict_id)` 及其后 if/else）替换为：

```python
        # drift/broken → 两模式统一：屏障归档后以规范源当前版本替换/安全归并，
        # 不经用户决策；区块外内容逐字保留（L0-B2）。
        composed, warnings = _compose_entry(
            existing, kernel_source, state=state or "insert",
            project_type=project_type,
            entry_name=entry_name, existing_rule_files=existing_rule_files,
        )
        report.setdefault("warnings", []).extend(warnings)
        atomic_write(entry_path, composed)
        actions_log.append({"path": entry_name, "action": "updated", "branch": f"authoritative-{state}"})
```

同时删除函数首部不再使用的 `decisions_map` 与 `conflict_id` 变量（若无其他引用）。

- [ ] **Step 4: 运行确认绿**

Run: `python3 -m pytest tests/test_rule_config.py -q`
Expected: 全量 PASS。

- [ ] **Step 5: shell B2 改写（`it-s4-drift-normal` → `it-s4-drift-normal-replaced`）**

B2 段（约 564-582 行）替换为（断言普通模式替换 + 区块外保留 + 归档）：

```bash
# B2. L0 漂移普通模式权威替换（it-s4-drift-normal-replaced / L0-03）。
# 契约：普通模式不再询问 keep/replace，屏障归档后以规范源当前版本替换，区块外逐字保留。
case_root="$TEST_ROOT/fx-l0-drift-normal"
mkdir -p "$case_root"
mk_converged_entries "$case_root"
replace_first_visible_paragraph "$case_root/CLAUDE.md" '本地漂移段落'
replace_first_visible_paragraph "$case_root/AGENTS.md" '另一个漂移段落'
outside_claude_before=$(outside_l0_hash "$case_root/CLAUDE.md")
outside_agents_before=$(outside_l0_hash "$case_root/AGENTS.md")
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_script apply "$case_root"
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$(managed_block_hash "$case_root/CLAUDE.md")" = "$(sha256_file "$KERNEL")" ] \
  && [ "$(managed_block_hash "$case_root/AGENTS.md")" = "$(sha256_file "$KERNEL")" ] \
  && [ "$outside_claude_before" = "$(outside_l0_hash "$case_root/CLAUDE.md")" ] \
  && [ "$outside_agents_before" = "$(outside_l0_hash "$case_root/AGENTS.md")" ] \
  && legacy_archive_exists "$case_root" 'CLAUDE.md' \
  && legacy_archive_exists "$case_root" 'AGENTS.md'; then
  assert_changed it-s4-drift-normal-replaced "$RUN_STATUS" "$before" "$after"
else
  record_result it-s4-drift-normal-replaced "$RUN_STATUS" "$before" "$after" fail
fi
```

- [ ] **Step 6: 运行确认绿**

Run: `bash tests/verify-managed-lifecycle.sh`
Expected: 全部 pass；结果清单含 `it-s4-drift-normal-replaced`，不含 `it-s4-drift-normal`。

- [ ] **Step 7: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/
git commit -m "feat(rule-config): L0 受管区块 drift/异常标记两模式统一归档+替换/安全归并"
```

---

### Task 4: step_s7 两模式合流（rules.apply + 结构/解析冲突）+ S7 测试与 shell 用例

**映射：** tasks.md 1.4 + 2.4；requirement「OpenSpec 配置验证以结构预检取代 instructions 验证」之「结构不兼容失败关闭」（语义更新）scenario。

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`step_s7_openspec_config` `action == "keep"` 区段 ~3172-3234）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`
- Test: `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`（B7 ~736-743；B8 ~745-768）

**Interfaces:**
- Consumes: Task 1 的 S7 资产动作新枚举（`remove-apply`/`replace`）；`_s7_publish_or_abort(config_path, candidate, report, actions_log, rel, branch=..., removed_key=...)`；`merge_yaml(template, existing)`（候选自动剔除 `rules.apply`）。
- Produces: 分支名 `rules-apply-removed`、`template-replace`；退役 `rules-apply-keep`、`<kind>-preserve`、`<kind>-terminate`。

- [ ] **Step 1: 改写四个 S7 单测（红）**

`TestStepS7OpenspecConfig` 中：

`test_rules_apply_normal_default_keep_preserved` → 替换为：

```python
    def test_rules_apply_normal_removed(self):
        """ut-step_s7-rules-apply-remove-normal / OS-04（普通模式无决策 → 移除 rules.apply 并保守合并）"""
        cfg = self.root / "openspec" / "config.yaml"
        cfg.parent.mkdir(parents=True)
        cfg.write_text(
            "schema: spec-driven\nrules:\n  proposal:\n    - custom\n  apply:\n    - x\n",
            encoding="utf-8",
        )
        plan = self._base_plan(steps={
            rc.STEP_OPENSPEC_CONFIG: {
                "name": rc.STEP_OPENSPEC_CONFIG, "status": "ok",
                "assets": [{
                    "path": "openspec/config.yaml", "action": "remove-apply",
                    "conflict": {"kind": "rules.apply", "value": ["x"]},
                    "backup_needed": True,
                }],
            }
        })
        rc.step_s7_openspec_config(self.root, _intents(), plan, {})
        doc = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        self.assertNotIn("apply", doc.get("rules", {}))
        self.assertIn("custom", doc["rules"]["proposal"])
```

`test_rules_apply_no_interrupt_removed`：仅将资产 `"action": "keep"` 改为 `"action": "remove-apply"`，其余不变。

`test_structure_conflict_no_interrupt_raises` → 替换为：

```python
    def test_structure_conflict_no_interrupt_replaced(self):
        """ut-step_s7-structure-replace / OS-03/05（no-interrupt 结构冲突 → 归档+模板整体替换）"""
        cfg = self.root / "openspec" / "config.yaml"
        cfg.parent.mkdir(parents=True)
        cfg.write_text("schema: spec-driven\nrules:\n  proposal: invalid-string\n", encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_OPENSPEC_CONFIG: {
                "name": rc.STEP_OPENSPEC_CONFIG, "status": "ok",
                "assets": [{
                    "path": "openspec/config.yaml", "action": "replace",
                    "conflict": {
                        "kind": "structure", "fields": ["rules.proposal"],
                        "field_types": {"rules.proposal": "str"},
                    },
                    "backup_needed": True,
                }],
            }
        })
        rc.step_s7_openspec_config(self.root, _intents(no_interrupt=True), plan, {})
        expected, _ = rc.merge_yaml(self.tpl, "")
        self.assertEqual(cfg.read_text(encoding="utf-8"), expected)
```

`test_structure_conflict_normal_preserved` → 替换为：

```python
    def test_structure_conflict_normal_replaced(self):
        """ut-step_s7-structure-replace-normal / OS-03/05（普通模式结构冲突 → 归档+模板整体替换，不记录冲突）"""
        cfg = self.root / "openspec" / "config.yaml"
        cfg.parent.mkdir(parents=True)
        cfg.write_text("schema: spec-driven\nrules:\n  proposal: invalid-string\n", encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_OPENSPEC_CONFIG: {
                "name": rc.STEP_OPENSPEC_CONFIG, "status": "ok",
                "assets": [{
                    "path": "openspec/config.yaml", "action": "replace",
                    "conflict": {
                        "kind": "structure", "fields": ["rules.proposal"],
                        "field_types": {"rules.proposal": "str"},
                    },
                    "backup_needed": True,
                }],
            }
        })
        report = {"steps": [rc._step_skeleton(rc.STEP_OPENSPEC_CONFIG)]}
        rc.step_s7_openspec_config(self.root, _intents(), plan, report)
        expected, _ = rc.merge_yaml(self.tpl, "")
        self.assertEqual(cfg.read_text(encoding="utf-8"), expected)
        # 不再记录决策冲突
        s7_conflicts = report["steps"][0].get("conflicts", [])
        self.assertFalse(any(c.get("kind") == "structure" for c in s7_conflicts))
```

- [ ] **Step 2: 运行确认红**

Run: `python3 -m pytest tests/test_rule_config.py::TestStepS7OpenspecConfig -q`
Expected: 四个改写用例 FAIL（旧 `keep` 动作走保留/终止分支）；`test_create_when_missing`、`test_merge_no_conflict_publishes`、`test_publish_candidate_precheck_fail_raises` 保持 PASS。

- [ ] **Step 3: 实现——step_s7 合流**

将 `# action == "keep"（conflict 非空）。` 起的整个区段（含 rules.apply 的 decision 分支与结构冲突的双模式分支）替换为：

```python
        # action == "remove-apply"：两模式统一——备份后移除 rules.apply 并保守合并
        #（merge_yaml 候选已剔除 apply；全局屏障已归档）。
        if action == "remove-apply":
            existing = _safe_read(config_path) or ""
            candidate, _ = merge_yaml(template_text, existing)
            if candidate is None:
                _s7_abort_unparseable(config_path, report, actions_log, rel)
                raise PublishError(
                    "openspec/config.yaml 不可解析，无法移除 rules.apply"
                )
            _s7_publish_or_abort(
                config_path, candidate, report, actions_log, rel,
                branch="rules-apply-removed",
                removed_key="rules.apply",
            )
            continue

        # action == "replace"：structure/unparseable/unreadable——无法无损规范化，
        # 两模式统一归档后以模板整体替换；候选取模板的安全 dump 形式以保证重跑幂等。
        if action == "replace":
            if not template_text:
                actions_log.append({
                    "path": rel, "action": "skipped", "reason": "模板缺失",
                })
                continue
            candidate, _ = merge_yaml(template_text, "")
            if candidate is None:
                # 模板不可解析（不应发生）→ 兜底用模板原文
                candidate = template_text
            _s7_publish_or_abort(
                config_path, candidate, report, actions_log, rel,
                branch="template-replace",
            )
            continue

        # 未知动作兜底：不写入，仅记录（防御性；compute_plan 不产生其他取值）。
        actions_log.append({
            "path": rel, "action": "skipped",
            "reason": f"未识别动作 {action!r}",
        })
```

同时删除该区段不再使用的 `_record_step_conflicts` 调用、`decisions_map` 变量（若无其他引用）。

- [ ] **Step 4: 运行确认绿**

Run: `python3 -m pytest tests/test_rule_config.py -q`
Expected: 全量 PASS。

- [ ] **Step 5: shell B7/B8 改写**

B7（约 736-743 行）替换为：

```bash
# B7. 普通模式 rules.apply 归档后移除（it-s7-openspec-normal-apply-removed / OS-04）。
# 契约：普通模式不再询问，与 no-interrupt 同动作。
case_root="$TEST_ROOT/fx-openspec-existing"
mkdir -p "$case_root/openspec"
printf 'schema: spec-driven\nrules:\n  proposal:\n    - custom-proposal\n  apply:\n    - invalid-artifact\n' > "$case_root/openspec/config.yaml"
before=$(sha256_file "$case_root/openspec/config.yaml")
run_script apply "$case_root"
after=$(sha256_file "$case_root/openspec/config.yaml")
if [ "$RUN_STATUS" -eq 0 ] && ! grep -q '^  apply:' "$case_root/openspec/config.yaml" \
  && grep -q 'custom-proposal' "$case_root/openspec/config.yaml" \
  && legacy_archive_exists "$case_root" 'openspec/config.yaml'; then
  assert_changed it-s7-openspec-normal-apply-removed "$RUN_STATUS" "$before" "$after"
else
  record_result it-s7-openspec-normal-apply-removed "$RUN_STATUS" "$before" "$after" fail
fi
```

B8 两段（约 745-768 行）替换为：

```bash
# B8. 不可解析/不兼容 YAML 两模式归档后模板替换（it-s7-openspec-invalid-yaml-backed-up-replaced 等 / OS-03/05）。
# 契约：不再失败关闭；归档成功后以模板整体替换并正常完成，产物可解析且含模板 schema。
case_root="$TEST_ROOT/fx-openspec-unparseable"
mkdir -p "$case_root/openspec"
printf 'schema: spec-driven\nrules: [\n' > "$case_root/openspec/config.yaml"
before=$(sha256_file "$case_root/openspec/config.yaml")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/openspec/config.yaml")
if [ "$RUN_STATUS" -eq 0 ] && [ "$before" != "$after" ] \
  && legacy_archive_exists "$case_root" 'openspec/config.yaml' \
  && python3 -c "import yaml,sys; d=yaml.safe_load(open(sys.argv[1])); assert d.get('schema')=='spec-driven'" "$case_root/openspec/config.yaml"; then
  assert_changed it-s7-openspec-invalid-yaml-backed-up-replaced "$RUN_STATUS" "$before" "$after"
else
  record_result it-s7-openspec-invalid-yaml-backed-up-replaced "$RUN_STATUS" "$before" "$after" fail
fi
# 类型冲突（普通模式同样替换）
printf 'schema: spec-driven\nrules:\n  proposal: invalid-string\n' > "$case_root/openspec/config.yaml"
before=$(sha256_file "$case_root/openspec/config.yaml")
run_script apply "$case_root"
after=$(sha256_file "$case_root/openspec/config.yaml")
if [ "$RUN_STATUS" -eq 0 ] && [ "$before" != "$after" ] \
  && legacy_archive_exists "$case_root" 'openspec/config.yaml' \
  && python3 -c "import yaml,sys; d=yaml.safe_load(open(sys.argv[1])); assert isinstance(d.get('rules',{}).get('proposal',[]),list)" "$case_root/openspec/config.yaml"; then
  assert_changed it-s7-openspec-yaml-type-conflict-backed-up-replaced "$RUN_STATUS" "$before" "$after"
else
  record_result it-s7-openspec-yaml-type-conflict-backed-up-replaced "$RUN_STATUS" "$before" "$after" fail
fi
```

- [ ] **Step 6: 运行确认绿**

Run: `bash tests/verify-managed-lifecycle.sh`
Expected: 全部 pass；结果清单含三个新 ID，不含 `it-s7-openspec-normal-preserved`、`it-s7-openspec-invalid-yaml-backed-up-preserved`、`it-s7-openspec-yaml-type-conflict-backed-up-preserved`。

- [ ] **Step 7: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/
git commit -m "feat(rule-config): rules.apply 两模式移除合并；不可解析/不兼容配置归档+模板替换"
```

---

### Task 5: 报告转发清理 + 决策机制休眠单测

**映射：** tasks.md 2.5；requirement「脚本两阶段执行与模式衔接」之「普通模式冲突经用户决策」（语义更新：休眠契约）scenario；REMOVED「dry-run 冲突报告标注 no-interrupt 真实动作」。

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`_sync_plan_to_report` 冲突转发块 ~3784-3803；`validate_decisions` docstring）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`

- [ ] **Step 1: 新增决策机制休眠单测（绿——机制未动，直接通过）**

`test_rule_config.py` 新增类（放在 `TestReportCompleteness` 之后）：

```python
class TestValidateDecisionsDormant(unittest.TestCase):
    """决策机制休眠兜底：以合成冲突直接驱动 validate_decisions（当前无活跃冲突类型，
    机制保留供未来复用；未知/重复/过期仍失败关闭，default_keep 缺失不违规）。"""

    def _plan_with_conflict(self):
        return {"conflicts": [{
            "conflict_id": "sX:synthetic", "asset": "synthetic",
            "allowed_decisions": ["replace", "keep"],
            "recommendation": "keep", "default_keep": True,
        }]}

    def test_unknown_conflict_id_rejected(self):
        violations = rc.validate_decisions(
            self._plan_with_conflict(),
            [{"conflict_id": "sX:unknown", "decision": "keep"}],
        )
        self.assertTrue(any("未知" in v for v in violations))

    def test_duplicate_conflict_id_rejected(self):
        violations = rc.validate_decisions(
            self._plan_with_conflict(),
            [
                {"conflict_id": "sX:synthetic", "decision": "keep"},
                {"conflict_id": "sX:synthetic", "decision": "replace"},
            ],
        )
        self.assertTrue(any("重复" in v for v in violations))

    def test_stale_decision_rejected(self):
        violations = rc.validate_decisions(
            self._plan_with_conflict(),
            [{"conflict_id": "sX:synthetic", "decision": "keep-foreign-value"}],
        )
        self.assertTrue(any("过期" in v for v in violations))

    def test_missing_decision_default_keep_passes(self):
        self.assertEqual(rc.validate_decisions(self._plan_with_conflict(), []), [])
```

- [ ] **Step 2: 实现——`_sync_plan_to_report` 删除 `no_interrupt_action` 转发**

删除冲突转发块中的以下行（约 3793-3795 行）：

```python
        if intents.no_interrupt:
            # P1-1：仅 no-interrupt 对外报告暴露实际执行动作；普通模式不写该键。
            conflict_entry["no_interrupt_action"] = c.get("no_interrupt_action")
```

保留 `allowed_decisions`/`default_keep` 转发（休眠机制对外契约不变）。`validate_decisions` docstring 中"仅普通模式且 plan 有冲突时调用"后补充一句：`当前系统无活跃冲突类型，本函数为休眠兜底。`

- [ ] **Step 3: 运行确认绿**

Run: `python3 -m pytest tests/test_rule_config.py -q && bash tests/verify-managed-lifecycle.sh`
Expected: pytest 全量 PASS（含新增 4 例）；shell 全部 pass。

- [ ] **Step 4: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "refactor(rule-config): 报告移除 no_interrupt_action 转发；决策机制休眠单测补位"
```

---

### Task 6: merge-semantics.md 语义对账更新

**映射：** tasks.md 3.2；requirements「受管资产必须按三类策略分别处理」「L0/L1/合并保护/结构预检」全部 MODIFIED 条目。

**Files:**
- Modify: `cadence-init/skills/rule-config/references/merge-semantics.md`

- [ ] **Step 1: RF 表（§5）**

- RF-05 行"普通模式动作"列：`询问 keep/replace，replace 时屏障归档+atomic_write` → `屏障归档+atomic_write 模板（两模式同动作，不经用户决策）`。
- RF-02b 行"普通模式动作"列：`询问用户；无响应则保留并报告 status=0（A 类…）…` → `见 RF-05 权威覆盖（两模式同动作，不经用户决策）`；对应测试 ID 列 `it-s3-normal-keep-decision`（普通 keep 分支）/ `it-s3-rules-drift-replace`（待补集成用例）→ `it-s3-normal-authoritative-overwrite`。
- RF-04 行"普通模式动作"列：`视为 RF-05 drift：询问 keep/replace；无响应保留并报告…` → `视为 RF-05 drift：两模式屏障归档后以模板覆盖，不经用户决策`；"备份要求"列删除"普通模式 keep 无归档"，统一为"两模式均纳入 RF-05 全局归档屏障"。
- 行 ID 与表结构不变，仅更新语义与测试 ID 列。

- [ ] **Step 2: L1 表（§3）L1-04/05/06 行**

三行"普通模式动作"列统一改为：`归入"与任何已知框架版本不匹配"；备份后以框架 v1 替换并报告（两模式同动作，不经用户决策）`；"no-interrupt 动作"列改为"同普通模式（两模式同动作）"。测试 ID 列追加 `it-s3-l1-drift-normal-replaced`；"仅单测覆盖/待补"括注保持。

- [ ] **Step 3: L0 表（§4）L0-03/L0-06 行**

- L0-03"普通模式动作"列 → `视为本地修改；纳入备份屏障后以规范源当前 v2 替换（两模式同动作，不经用户决策）`；"no-interrupt 动作"列改"同普通模式"；测试 ID 列 `it-s4-drift-normal` → `it-s4-drift-normal-replaced`。
- L0-06"普通模式动作"列 → `单侧/顺序错误、混合版本与重复区块均按确定性安全归并执行（两模式同动作，不经用户决策）`；"no-interrupt 动作"列改"同普通模式"。

- [ ] **Step 4: OS 表（§2）OS-03/04/05 行**

- OS-03"普通模式动作"列 → `先归档，归档成功后以模板内容原子替换原位并报告（两模式同动作，不经用户决策）`；"no-interrupt 动作"列改"同普通模式"；"备份要求"列统一为"先成功备份原文件（§11.1）；备份失败终止且不改原文件"；测试 ID 列 `it-s7-openspec-yaml-type-conflict-backed-up-preserved` → `it-s7-openspec-yaml-type-conflict-backed-up-replaced`。
- OS-04"普通模式动作"列 → `先创建备份；备份成功后在候选中移除并继续合并（两模式同动作，不经用户决策）`；"no-interrupt 动作"列改"同普通模式"；测试 ID 列 `it-s7-openspec-normal-preserved` → `it-s7-openspec-normal-apply-removed`。
- OS-05 同 OS-03 模式改写；测试 ID 列 `it-s7-openspec-invalid-yaml-backed-up-preserved` → `it-s7-openspec-invalid-yaml-backed-up-replaced`。

- [ ] **Step 5: §11.3 决策文件 schema 与 §11.6 重写**

- §11.3"决策文件 schema"小节：五个 decision 枚举条目标注"（2026-08-19 起转为确定性动作，不再产生该冲突）"；保留 conflict_id 格式与"decisions 四类异常"契约，注明其休眠兜底属性。
- §11.6 整节重写：标题保留"default_keep 语义（Task 8 裁决区分）"，正文改为——六类原 A 类冲突全部转为两模式确定性动作（列清单：RF-05、L1-04~06、L0-03、L0-06 单侧/顺序错误子分支、OS-03、OS-04、OS-05），当前系统无活跃冲突类型；`default_keep`/`validate_decisions` 机制代码保留休眠兜底，供未来冲突类型复用；保留 codex 三轮 C3/五轮历史说明块，追加 2026-08-19 裁决记录（用户裁决：框架受管内容以 Cadence-skills 模板为权威，归档提供可恢复性替代"保留原状"作为安全兜底）。

- [ ] **Step 6: §12 追加对账记录**

追加段落：`2026-08-19 权威化对账（change rule-config-authoritative-overwrite）：RF-05/L1-04~06/L0-03/L0-06/OS-03~05 普通模式列两模式统一为归档+权威处理；§11.6 A 类清单清空；it-s3-normal-keep-decision→it-s3-normal-authoritative-overwrite 等 7 个集成 ID 改名（清单见 skill-clause-map.md）；it-l0-drift-normal-keep-default、it-l1-drift-normal-keep-default、it-decisions-unknown、it-decisions-stale 四个用例随决策编排路径消亡移除。`

- [ ] **Step 7: Commit**

```bash
git add cadence-init/skills/rule-config/references/merge-semantics.md
git commit -m "docs(rule-config): merge-semantics 十表与 §11.6 对账为两模式权威化语义"
```

---

### Task 7: SKILL.md 与 references/rules/README.md 更新

**映射：** tasks.md 3.1/3.3。

**Files:**
- Modify: `cadence-init/skills/rule-config/SKILL.md`
- Modify: `cadence-init/skills/rule-config/references/rules/README.md`

- [ ] **Step 1: SKILL.md 概述段**

- 首段"内容 drift 时执行框架权威全覆盖"表述保留。
- 第二段"Agent 只负责定位脚本、按本文件编排调用、解读报告，并在普通模式就冲突逐条提问、回收决策"改为"Agent 只负责定位脚本、按本文件编排调用、解读报告；当前系统无活跃冲突类型，两模式全程不经用户决策（决策文件机制休眠兜底，见 references/merge-semantics.md §11.6）"。

- [ ] **Step 2: SKILL.md 普通模式流程（两阶段流程节）**

五步流程改为三步：

```markdown
1. **dry-run**：脚本只读探测目标项目，报告给出计划动作（含 drift 资产的 `replace`/归档需求），对项目零写入。
2. **读 plan**：Agent 读取报告中的计划，向用户汇报将以模板权威覆盖/处理的资产清单与归档位置。
3. **apply**：执行阶段二命令。当前系统无活跃冲突类型，计划不要求决策文件；`--decisions`/`validate_decisions`/`default_keep` 机制保留休眠兜底（未来引入需用户决策的冲突类型时恢复"逐条提问、每次一问、附带推荐默认项"流程，语义见 references/merge-semantics.md §11.3/§11.6）。
```

- [ ] **Step 3: SKILL.md no-interrupt 汇报规则**

"汇报冲突实际动作（强制）"段改为：两模式汇报 drift 处理结果时，Agent MUST 依据报告 `steps[].actions[]` 条目的 `action`/`branch`（如 `overwritten`/`authoritative-overwrite`/`l1-authoritative-replace`/`rules-apply-removed`/`template-replace`）描述实际执行动作；冲突清单已不再承载 drift 条目。

- [ ] **Step 4: SKILL.md 报告解读节**

冲突清单提取示例的注释更新为休眠兜底说明（保留命令本身）。退出码表、失败关闭、hints 不变。

- [ ] **Step 5: references/rules/README.md 第 43 行段落**

"普通模式先 dry-run 探测 drift，就冲突逐条询问；无响应或缺失决策时按安全默认 keep 保留原文件并报告，选择 replace 时先统一复制归档…"改为"两模式均在 dry-run/apply 两阶段内完成：drift 文件先统一复制归档到 `cadence/legacy/`，归档成功后按模板权威全覆盖，不经用户决策；不执行章节合并"。

- [ ] **Step 6: Commit**

```bash
git add cadence-init/skills/rule-config/SKILL.md cadence-init/skills/rule-config/references/rules/README.md
git commit -m "docs(rule-config): SKILL 与 rules README 更新为两模式权威化编排语义"
```

---

### Task 8: skill-clause-map.md 条款对账

**映射：** tasks.md 3.4；routing-conformance「路由目标和版本必须通过静态检查」对账要求。

**Files:**
- Modify: `cadence-init/skills/rule-config/tests/skill-clause-map.md`

- [ ] **Step 1: 更新映射表受影响行**

按 Task 6 的 ID 变更清单逐行更新（测试 ID 列与关键断言列）：RF-05/RF-02b/RF-04、L1-04~06、L0-03/L0-06、OS-03/04/05、XC-03（C2b/C2c 移除 → `ut-validate-decisions-*` 休眠单测四例）、DF/IA 表相关行（普通模式无响应默认保留 → 无活跃冲突类型说明）、P1-1 行（`no_interrupt_action` 字段移除，四个 ut 用例删除登记）。

- [ ] **Step 2: 追加变更记录**

在文件头部版本说明下追加：`> 2026-08-19 对账（change rule-config-authoritative-overwrite）：六类受管冲突转两模式确定性动作；7 个集成 ID 改名，4 个用例移除，新增 ut-validate-decisions-dormant 休眠单测 4 例；SKILL 行号区间不变（语义正文在 references/merge-semantics.md）。`

- [ ] **Step 3: Commit**

```bash
git add cadence-init/skills/rule-config/tests/skill-clause-map.md
git commit -m "docs(rule-config): 条款对账表同步两模式权威化语义与测试 ID 变更"
```

---

### Task 9: 全量验证 + 两模式端到端一致性

**映射：** tasks.md 4.1/4.2/4.3。

**Files:**
- 无修改（纯验证）

- [ ] **Step 1: pytest 全量**

Run: `cd cadence-init/skills/rule-config && python3 -m pytest tests/test_rule_config.py -q`
Expected: 全量 PASS，无 skip 之外的失效。

- [ ] **Step 2: 生命周期套件全量**

Run: `bash tests/verify-managed-lifecycle.sh`
Expected: 末尾汇总全部 pass，0 fail。

- [ ] **Step 3: 两模式 E2E 一致性（真实临时项目）**

```bash
E2E=$(mktemp -d)
for mode in normal ni; do
  proj="$E2E/$mode"
  mkdir -p "$proj/.claude/rules" "$proj/openspec"
  printf '### Serena MCP\nold\n' > "$proj/.claude/rules/mcp-servers.md"
  printf '本地漂移\n' > "$proj/.claude/rules/language.md"
  printf 'schema: spec-driven\nrules:\n  proposal: invalid-string\n' > "$proj/openspec/config.yaml"
done
python3 scripts/rule-config.py apply --project-root "$E2E/normal" --report "$E2E/r1.json"
python3 scripts/rule-config.py apply --project-root "$E2E/ni" --report "$E2E/r2.json" --no-interrupt
# 断言：两模式产物逐字一致
diff -r --exclude=legacy "$E2E/normal/.claude" "$E2E/ni/.claude"
diff "$E2E/normal/openspec/config.yaml" "$E2E/ni/openspec/config.yaml"
# 断言：归档存在、无提问交互（命令未挂起即证明）
ls "$E2E/normal/cadence/legacy"/*/.claude/rules/mcp-servers.md
ls "$E2E/ni/cadence/legacy"/*/.claude/rules/mcp-servers.md
```

Expected: diff 无输出（一致）；归档文件存在；两条 apply 均退出 0。注意：本任务在 `cadence-init/skills/rule-config/` 下执行；模板定位走脚本三级定位（开发环境 glob 回退会命中本仓库 references），无需额外 mock。

- [ ] **Step 4: 收尾提交（如验证中产生修复）**

```bash
git add -A && git commit -m "test(rule-config): 两模式权威化全量验证与 E2E 一致性"
```

---

## Self-Review 记录

- **Spec coverage**：MODIFIED 的 6 个 requirement ↔ Task 1-5（脚本与测试）、6-8（文档对账）；REMOVED「dry-run 冲突报告标注 no-interrupt 真实动作」↔ Task 1 Step 4 + Task 5 Step 2；routing-conformance 生命周期场景 ↔ Task 2/3/4 shell 改写 + Task 9。无遗漏。
- **Placeholder 扫描**：无 TBD/TODO；所有测试与实现代码均为完整可执行内容。
- **类型一致性**：S7 资产动作枚举 `remove-apply`/`replace` 在 Task 1（产出）、Task 4（消费）、`_backup_required_for`（Task 1 Step 12）三处一致；分支命名与 Global Constraints 一致。
- **中间态核验**：Task 1 完成后 step 函数未合流，普通模式 CLI 对 drift 资产因决策缺失走旧 keep 分支，shell B2/B6/B7/C4 旧断言仍通过（B2b/B6b/C2b/C2c 四个依赖计划层冲突的用例已在 Task 1 内删除/改写）；Task 2~4 每任务翻转对应 shell 用例，逐任务保持双套件绿。
