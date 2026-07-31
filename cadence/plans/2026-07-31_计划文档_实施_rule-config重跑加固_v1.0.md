# rule-config 重跑加固实施 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 merge_markdown 重跑不幂等（P0），并让 no-interrupt 全流程零人工：unchanged 跳过写盘、dry-run 冲突报告标注真实动作、RF-04 缺 CodeGraph 段落回归统一自动合并。

**Architecture:** 全部改动收敛在 `cadence-init/skills/rule-config/` 单 skill 内：Python 脚本四处点状修改（merge_markdown 保留字过滤、step_s3 unchanged 短路、compute_plan 报告字段与 RF-04 特判删除）+ 三份文档同步。严格 TDD：每个行为变化先写失败测试再实现。

**Tech Stack:** Python 3 标准库 + PyYAML（既有依赖）；unittest 测试框架；OpenSpec 契约已获批（`openspec/changes/rule-config-rerun-hardening/`）。

**契约映射：** 本 Plan 只展开 `openspec/changes/rule-config-rerun-hardening/tasks.md` 的 6 个工作包，不重定义范围、架构或验收。验收 Scenario 以 `specs/rule-config-scripted-execution/spec.md` 为准。

## Global Constraints

- 测试文件：`cadence-init/skills/rule-config/tests/test_rule_config.py`，模块以 `rc` 指代被测脚本（importlib 加载），每个测试方法 docstring 首行标注 `ut-*` 测试 ID 与条款编号（既有约定，必须沿用）。
- 新增测试 ID 必须同步登记到 `cadence-init/skills/rule-config/tests/skill-clause-map.md`。
- 测试运行命令（本 Plan 统一）：`cd cadence-init/skills/rule-config/tests && python3 -m unittest test_rule_config.<ClassName> -v`；全量：`python3 -m unittest test_rule_config -v`。
- 脚本内注释与文档一律中文；Markdown 遵循 `.claude/rules/markdown-format.md`。
- 不得改动 L0/L1 合并路径、普通模式冲突询问流程、NC-08 回退语义（P0 范围外）。
- `**项目补充**` 是合并协议保留字，脚本内一律经 Task 1 引入的常量 `PROJECT_SUPPLEMENT_MARKER` 引用，禁止新增字面量。
- 每个 Task 结束独立提交，提交信息遵循仓库既有风格（`fix(rule-config): ...` / `docs(rule-config): ...`）。

---

### Task 1: merge_markdown 重跑幂等（P0，契约工作包 1）

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（模块级常量约 139-140 行附近；`merge_markdown` 约 797-810 行）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（`TestMergeMarkdown` 类，约 46 行起）

**Interfaces:**
- Consumes: 既有 `rc.merge_markdown(template: str, existing: Optional[str]) -> Optional[str]`
- Produces: 模块级常量 `rc.PROJECT_SUPPLEMENT_MARKER = "**项目补充**"`（Task 2-5 及后续维护共用）；`merge_markdown` 新语义：`merge(t, merge(t, x)) == merge(t, x)`

- [ ] **Step 1: 写两个失败测试**

在 `TestMergeMarkdown` 类内追加：

```python
    def test_rerun_is_idempotent(self):
        """ut-merge_markdown-rerun-idempotent / NC-03（重跑幂等：merge(t, merge(t, x)) == merge(t, x)）"""
        tpl = "## 规则A\n\n模板行1\n模板行2\n\n## 规则B\n\n模板行3\n"
        old = "## 规则A\n\n模板行1\n模板行2\n\n项目独有行X\n\n## 规则B\n\n模板行3\n\n项目独有行Y\n"
        run1 = rc.merge_markdown(tpl, old)
        run2 = rc.merge_markdown(tpl, run1)
        run3 = rc.merge_markdown(tpl, run2)
        self.assertEqual(run1, run2)
        self.assertEqual(run2, run3)
        # 每个含项目补充的同名章节恰好一个标记行
        self.assertEqual(run2.count("**项目补充**"), 2)

    def test_polluted_file_self_heals(self):
        """ut-merge_markdown-polluted-self-heal / NC-03（历史重复标记污染 → 合并自愈为单标记且内容不丢）"""
        tpl = "## 规则A\n\n模板行1\n"
        polluted = "## 规则A\n\n模板行1\n\n\n**项目补充**\n**项目补充**\n项目独有行X\n"
        out = rc.merge_markdown(tpl, polluted)
        self.assertEqual(out.count("**项目补充**"), 1)
        self.assertIn("项目独有行X", out)
        self.assertEqual(out, rc.merge_markdown(tpl, out))
```

- [ ] **Step 2: 运行确认失败**

Run: `cd cadence-init/skills/rule-config/tests && python3 -m unittest test_rule_config.TestMergeMarkdown -v`
Expected: 两个新用例 FAIL（`run1 != run2`，标记计数为 2 而非 1）

- [ ] **Step 3: 最小实现**

3a. 在 `rule-config.py` 模块级常量区（`CODEGRAPH_RULE_FILE` 定义旁，约 139-140 行）添加：

```python
# NC-03 项目补充标记：合并协议保留字。注入与项目独有行过滤共用此常量；
# 重跑时过滤必须排除标记行自身，保证 merge(t, merge(t, x)) == merge(t, x)（重跑幂等）。
PROJECT_SUPPLEMENT_MARKER = "**项目补充**"
```

3b. `merge_markdown` 内项目独有行过滤（原约 797-800 行）改为：

```python
            project_only_raw = [
                line for line in project_body
                if line not in template_lines and line.strip()
                and line.strip() != PROJECT_SUPPLEMENT_MARKER
            ]
```

3c. 注入处（原约 808 行）`body.append("**项目补充**")` 改为：

```python
                body.append(PROJECT_SUPPLEMENT_MARKER)
```

- [ ] **Step 4: 运行确认通过**

Run: `cd cadence-init/skills/rule-config/tests && python3 -m unittest test_rule_config.TestMergeMarkdown -v`
Expected: 全部 PASS（含既有用例无回归）

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "fix(rule-config): merge_markdown 重跑幂等——项目补充标记升为保留字常量并从项目独有行过滤排除"
```

---

### Task 2: unchanged 跳过写盘（契约工作包 2）

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`step_s3_rules_files` 普通规则 no-interrupt 分支，约 2104-2114 行）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（`TestStepS3RulesFiles` 类，约 790 行起）

**Interfaces:**
- Consumes: Task 1 的幂等 `merge_markdown`；既有 `_safe_read` / `atomic_write` / `actions_log` / `_record_step_actions`
- Produces: 资产动作新取值 `{"action": "unchanged", "branch": "markdown-merge-idempotent"}`（报告消费方按 unknown action 忽略即可，向后兼容）

- [ ] **Step 1: 写失败测试**

在 `TestStepS3RulesFiles` 类内追加：

```python
    def test_ordinary_no_interrupt_unchanged_skips_write(self):
        """ut-step_s3-ordinary-unchanged / NC-03（no-interrupt 合并结果与现有文件逐字一致 → 跳过写盘，报告 unchanged）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / "language.md"
        merged_once = rc.merge_markdown(self.language_tpl, self.language_tpl + "\n项目独有行\n")
        target.write_text(merged_once, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_RULES_FILES: {
                "name": rc.STEP_RULES_FILES, "status": "ok",
                "assets": [{
                    "path": ".claude/rules/language.md", "action": "replace",
                    "conflict": "drift", "backup_needed": True, "is_l1": False,
                }],
            }
        })
        report = {"steps": [], "overall": "ok"}
        with mock.patch.object(rc, "atomic_write") as m_write:
            rc.step_s3_rules_files(self.root, _intents(no_interrupt=True), plan, report)
        m_write.assert_not_called()
        s3 = next(s for s in report["steps"] if s["name"] == rc.STEP_RULES_FILES)
        self.assertTrue(any(a.get("action") == "unchanged" for a in s3.get("actions", [])))
        self.assertEqual(target.read_text(encoding="utf-8"), merged_once)
```

- [ ] **Step 2: 运行确认失败**

Run: `cd cadence-init/skills/rule-config/tests && python3 -m unittest test_rule_config.TestStepS3RulesFiles -v`
Expected: FAIL（`atomic_write` 被调用 / 无 `unchanged` 动作）

- [ ] **Step 3: 最小实现**

`step_s3_rules_files` 普通规则 no-interrupt 分支（原约 2104-2114 行）改为：

```python
            if intents.no_interrupt:
                existing_text = _safe_read(target)
                merged = merge_markdown(template_text, existing_text)
                if merged is None:
                    # NC-08 回退：标准结构 + `\n\n## 原项目补充\n\n` + 原文（备份已由屏障完成）。
                    original = existing_text or ""
                    fallback = template_text.rstrip("\n") + "\n\n## 原项目补充\n\n" + original
                    atomic_write(target, fallback)
                    actions_log.append({"path": asset["path"], "action": "merged-fallback", "branch": "markdown-unparseable"})
                elif merged == existing_text:
                    # 幂等短路：合并产物与现有文件逐字一致 → 跳过写盘（避免重跑刷新 mtime）。
                    actions_log.append({"path": asset["path"], "action": "unchanged", "branch": "markdown-merge-idempotent"})
                else:
                    atomic_write(target, merged)
                    actions_log.append({"path": asset["path"], "action": "merged", "branch": "markdown-merge"})
```

（原 NC-08 回退分支逻辑不变，仅复用已读出的 `existing_text`。）

- [ ] **Step 4: 运行确认通过**

Run: `cd cadence-init/skills/rule-config/tests && python3 -m unittest test_rule_config.TestStepS3RulesFiles -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "feat(rule-config): no-interrupt 合并结果与现有文件一致时跳过写盘并报告 unchanged"
```

---

### Task 3: dry-run 冲突报告标注 no-interrupt 真实动作（契约工作包 3）

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`compute_plan` 普通规则 drift 分支，约 1440-1466 行，s3 级与 plan 级两处 conflicts append）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（新增 `TestDriftConflictNoInterruptAction` 类，置于 `TestCodegraphSectionMissing` 附近）

**Interfaces:**
- Consumes: 既有 `rc.compute_plan(root, intents)`、`rc.STEP_RULES_FILES`、测试辅助 `_intents(**overrides)`
- Produces: drift 冲突条目可选字段 `no_interrupt_action: "markdown-merge"`（仅 no-interrupt；普通模式条目不出现该字段）

- [ ] **Step 1: 写失败测试**

```python
class TestDriftConflictNoInterruptAction(unittest.TestCase):
    """P1-1：no-interrupt 下 drift 冲突条目携带真实执行动作字段，避免 recommendation=keep 误导。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.refs = Path(__file__).resolve().parents[1] / "references"
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "language.md").write_text("# 项目自定义语言规则\n\n与模板不同。\n", encoding="utf-8")

    def _compute(self, **overrides):
        with mock.patch.object(
            rc, "locate_templates",
            return_value=(self.refs / "rules", self.refs / "openspec" / "config.yaml"),
        ):
            return rc.compute_plan(self.root, _intents(**overrides))

    def test_no_interrupt_marks_real_action(self):
        """ut-compute-plan-no-interrupt-action / P1-1（no-interrupt drift 冲突含 no_interrupt_action=markdown-merge，recommendation 不变）"""
        plan = self._compute(no_interrupt=True)
        s3 = plan["steps"][rc.STEP_RULES_FILES]
        entry = next(c for c in s3["conflicts"] if str(c.get("asset", "")).endswith("language.md"))
        self.assertEqual(entry["no_interrupt_action"], "markdown-merge")
        self.assertEqual(entry["recommendation"], "keep")
        top = next(c for c in plan["conflicts"] if str(c.get("asset", "")).endswith("language.md"))
        self.assertEqual(top["no_interrupt_action"], "markdown-merge")

    def test_normal_mode_omits_field(self):
        """ut-compute-plan-normal-no-action-field / P1-1（普通模式冲突条目不新增字段）"""
        plan = self._compute()
        s3 = plan["steps"][rc.STEP_RULES_FILES]
        self.assertFalse(any("no_interrupt_action" in c for c in s3["conflicts"]))
        self.assertFalse(any("no_interrupt_action" in c for c in plan["conflicts"]))
```

- [ ] **Step 2: 运行确认失败**

Run: `cd cadence-init/skills/rule-config/tests && python3 -m unittest test_rule_config.TestDriftConflictNoInterruptAction -v`
Expected: FAIL（KeyError: 'no_interrupt_action'）

- [ ] **Step 3: 最小实现**

`compute_plan` 普通规则 drift 分支（原约 1447-1466 行）两处 append 改为先构造 dict、按模式增量字段再 append：

```python
                s3_conflict = {
                    "conflict_id": conflict_id, "asset": rel, "state": "drift",
                    "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                    "question": f"规则文件 {rel} 与模板不一致",
                    "recommendation": DECISION_KEEP,
                    "default_keep": True,
                }
                top_conflict = {
                    "conflict_id": conflict_id, "asset": rel, "kind": "rules",
                    "state": "drift",
                    "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                    "question": f"规则文件 {rel} 与模板不一致",
                    "recommendation": DECISION_KEEP,
                    "default_keep": True,
                }
                if intents.no_interrupt:
                    # P1-1：no-interrupt 实际执行为章节合并写盘；显式标注真实动作，
                    # 避免安全默认 recommendation=keep 误导为"保留原文件不动"。
                    s3_conflict["no_interrupt_action"] = "markdown-merge"
                    top_conflict["no_interrupt_action"] = "markdown-merge"
                s3["conflicts"].append(s3_conflict)
                plan["conflicts"].append(top_conflict)
```

- [ ] **Step 4: 运行确认通过**

Run: `cd cadence-init/skills/rule-config/tests && python3 -m unittest test_rule_config.TestDriftConflictNoInterruptAction -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "feat(rule-config): dry-run 冲突报告在 no-interrupt 下标注 no_interrupt_action=markdown-merge"
```

---

### Task 4: RF-04 去特判——缺 CodeGraph 段落回归统一合并（契约工作包 4，BREAKING）

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`compute_plan` RF-04 elif 分支，约 1417-1437 行；`step_s3_rules_files` RF-04 执行分支，约 2074-2080 行；`CODEGRAPH_RULE_FILE` 注释约 139-140 行）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（`TestCodegraphSectionMissing` 类整体改写为 `TestCodegraphSectionUnifiedMerge`，约 1848-1906 行）

**Interfaces:**
- Consumes: Task 3 后的 `compute_plan`（drift 分支）；既有 `_sync_plan_to_report`、`step_s3_rules_files`
- Produces: `codegraph-section-missing` 冲突类型从脚本中彻底移除；code-reading.md drift 时与普通规则文件同构（action=replace / conflict=drift / backup_needed=True）

- [ ] **Step 1: 改写测试为失败测试**

将 `TestCodegraphSectionMissing` 类整体替换为（setUp 与 `_compute` 保持不变）：

```python
class TestCodegraphSectionUnifiedMerge(unittest.TestCase):
    """RF-04 去特判：缺 CodeGraph 段落的 code-reading.md 回归普通规则文件统一 drift 处理。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.refs = Path(__file__).resolve().parents[1] / "references"
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "code-reading.md").write_text(
            "# 旧版代码阅读规则\n\n仅 ast-grep，无其他内容。\n", encoding="utf-8",
        )

    def _compute(self):
        with mock.patch.object(
            rc, "locate_templates",
            return_value=(self.refs / "rules", self.refs / "openspec" / "config.yaml"),
        ):
            return rc.compute_plan(self.root, _intents())

    def test_missing_codegraph_section_is_plain_drift(self):
        """ut-s3-codegraph-section-unified-drift / RF-04（缺 CodeGraph 段落 → 普通 drift 冲突，进 decisions 与备份需求）"""
        plan = self._compute()
        s3 = plan["steps"][rc.STEP_RULES_FILES]
        asset = next(a for a in s3["assets"] if a["path"].endswith("code-reading.md"))
        self.assertEqual(asset["action"], "replace")
        self.assertEqual(asset["conflict"], "drift")
        self.assertTrue(asset["backup_needed"])
        self.assertTrue(
            any(str(c.get("asset", "")).endswith("code-reading.md")
                for c in plan["conflicts"])
        )
        self.assertTrue(
            any(str(b).endswith("code-reading.md") for b in plan["backup_needs"])
        )
        # codegraph-section-missing 冲突类型已移除
        self.assertFalse(
            any(c.get("kind") == "codegraph-section-missing"
                or c.get("conflict") == "codegraph-section-missing"
                for c in s3["conflicts"])
        )

    def test_no_interrupt_execute_merges_codegraph_section(self):
        """ut-s3-codegraph-section-unified-merge / RF-04（no-interrupt 自动合并：模板 CodeGraph 段落并入、项目原文保留）"""
        plan = self._compute()
        report = {"steps": [], "overall": "ok"}
        rc._sync_plan_to_report(plan, report, _intents(no_interrupt=True))
        rc.step_s3_rules_files(self.root, _intents(no_interrupt=True), plan, report)
        result = (self.root / ".claude" / "rules" / "code-reading.md").read_text(encoding="utf-8")
        self.assertIn("CodeGraph", result)          # 模板段落并入
        self.assertIn("仅 ast-grep", result)        # 项目原文保留（项目补充/独有章节）
```

- [ ] **Step 2: 运行确认失败**

Run: `cd cadence-init/skills/rule-config/tests && python3 -m unittest test_rule_config.TestCodegraphSectionUnifiedMerge -v`
Expected: FAIL（asset 仍为 skip / codegraph-section-missing；文件未被合并）

- [ ] **Step 3: 最小实现**

3a. 删除 `compute_plan` 中 RF-04 elif 分支（原约 1417-1437 行，即 `elif (fname == CODEGRAPH_RULE_FILE and "CodeGraph" in template_text and "CodeGraph" not in existing_text):` 整块），使缺 CodeGraph 段落的 drift 文件落入其后的普通 `else` drift 分支。

3b. 删除 `step_s3_rules_files` 中执行分支（原约 2074-2080 行）：

```python
        if action == "skip" or conflict is None:
            if conflict == "codegraph-section-missing":
                # codex 终审 I5 / RF-04：报告手动合并提示，不重写文件
                actions_log.append({...})
            else:
                actions_log.append({"path": asset["path"], "action": "skipped"})
            continue
```

改为：

```python
        if action == "skip" or conflict is None:
            actions_log.append({"path": asset["path"], "action": "skipped"})
            continue
```

3c. 更新 `CODEGRAPH_RULE_FILE` 注释（约 139-140 行）：常量保留（OP-01 可选规则完整性检查仍在用），注释改为仅说明 OP-01 用途，删除 RF-04 相关表述。

- [ ] **Step 4: 运行确认通过**

Run: `cd cadence-init/skills/rule-config/tests && python3 -m unittest test_rule_config.TestCodegraphSectionUnifiedMerge test_rule_config.TestOptionalRuleIntegrity -v`
Expected: 全部 PASS（OP-01 完整性检查不受影响）

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "feat(rule-config)!: RF-04 去特判——缺 CodeGraph 段落的 code-reading.md 回归统一 drift/章节合并"
```

---

### Task 5: 文档同步（契约工作包 5）

**Files:**
- Modify: `cadence-init/skills/rule-config/references/merge-semantics.md`（NC-03 行约 36 行、RF-02b 行约 138 行、RF-04 行约 140 行）
- Modify: `cadence-init/skills/rule-config/SKILL.md`（「第一步——定位脚本」段落，约 42 行）
- Modify: `cadence-init/skills/rule-config/tests/skill-clause-map.md`

**Interfaces:**
- Consumes: Task 1-4 落地后的真实行为与测试 ID
- Produces: 与实现一致的权威合并语义表、条款映射、脚本定位规则

- [ ] **Step 1: 更新 merge-semantics.md**

1a. NC-03 行（约 36 行）：no-interrupt 决策列补「（`**项目补充**` 为合并协议保留字，重跑幂等：merge(t, merge(t, x)) == merge(t, x)；合并结果与现有文件一致时跳过写盘并报告 unchanged）」；测试列追加 ` / ut-merge_markdown-rerun-idempotent / ut-merge_markdown-polluted-self-heal / ut-step_s3-ordinary-unchanged`。

1b. RF-02b 行（约 138 行）：no-interrupt 列补「合并结果与现有文件逐字一致时不写盘，报告 `unchanged`」。

1c. RF-04 行（约 140 行）整行改写为：触发条件不变（规则文件已存在但缺少 CodeGraph 段落）；普通模式=同 RF-02b 询问；no-interrupt=按章节级权威规则自动合并（模板 CodeGraph 段落并入、项目内容保留、先备份）；测试列改为 `ut-s3-codegraph-section-unified-drift / ut-s3-codegraph-section-unified-merge`；删除「需用户手动合并」表述。

- [ ] **Step 2: 更新 SKILL.md 定位段落**

在「第一步——定位脚本」（约 42 行）现有约定后补充 plugin 安装场景：

- 候选根定位顺序：① plugin 缓存（`<plugin 缓存根>/cadence-init/skills/rule-config/scripts/rule-config.py`）② 仓库安装根（`<skill 安装根>/cadence-init/skills/rule-config/scripts/rule-config.py`）。
- 若候选根下 `scripts/` 缺失（旧版本缓存），重新安装/刷新 plugin 后重试；不得从其他项目目录复制脚本。

- [ ] **Step 3: 更新 skill-clause-map.md**

- NC-03 行（约 80 行）测试 ID 列追加三个新 ID；
- RF-04 相关行的行为描述与测试 ID 改为统一合并语义 + `ut-s3-codegraph-section-unified-drift / ut-s3-codegraph-section-unified-merge`；
- 新增 P1-1 报告字段映射行：`ut-compute-plan-no-interrupt-action / ut-compute-plan-normal-no-action-field`。

- [ ] **Step 4: Commit**

```bash
git add cadence-init/skills/rule-config/references/merge-semantics.md cadence-init/skills/rule-config/SKILL.md cadence-init/skills/rule-config/tests/skill-clause-map.md
git commit -m "docs(rule-config): 同步 NC-03 幂等语义、RF-04 统一合并、plugin 场景脚本定位与条款映射"
```

---

### Task 6: 全量验证与契约收尾（契约工作包 6）

**Files:**
- Modify: `openspec/changes/rule-config-rerun-hardening/tasks.md`（勾选复选框）

- [ ] **Step 1: 全量测试**

Run: `cd cadence-init/skills/rule-config/tests && python3 -m unittest test_rule_config -v`
Expected: 全部 PASS，无 skip 之外的异常

- [ ] **Step 2: OpenSpec 校验**

Run: `openspec validate rule-config-rerun-hardening --strict`
Expected: `Change 'rule-config-rerun-hardening' is valid`

- [ ] **Step 3: 勾选契约 tasks.md 全部复选框并提交**

```bash
git add -A
git commit -m "chore(openspec): rule-config-rerun-hardening 实施完成，勾选 tasks"
```

## Self-Review 记录

- **Spec coverage**：契约 6 个工作包 ↔ Task 1-6 一一对应；spec 全部 7 个 Scenario（幂等/自愈/unchanged/统一合并/普通模式不变/字段标注/普通模式无字段）均有对应测试步骤。
- **Placeholder scan**：无 TBD/TODO；所有测试与实现代码均为完整可粘贴内容。
- **Type consistency**：`PROJECT_SUPPLEMENT_MARKER`（Task 1 定义，全局约束引用）、`no_interrupt_action`（Task 3 定义，Task 5 文档引用）、`unchanged` 动作取值（Task 2 定义，Task 5 文档引用）命名一致。
