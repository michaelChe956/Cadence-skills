# rule-config 脚本纯函数库单元测试（RED 骨架）
#
# 用例清单来源：tests/skill-clause-map.md（Task 1 产物）。
# 每个测试方法的 docstring 第一行标注对应 ut-* 测试 ID 与条款编号。
# 加载方式与签名由 Plan 全局约束冻结，Task 4-9 必须逐字实现：
#   rc.merge_markdown / rc.merge_yaml / rc.l0_block / rc.precheck_openspec_structure
#   rc.backup_file / rc.atomic_write / rc.sha256_file / rc.classify_l1

import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rule-config.py"
spec = importlib.util.spec_from_file_location("rule_config", SCRIPT_PATH)
rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)

TPL = (Path(__file__).resolve().parents[1] / "references" / "openspec" / "config.yaml").read_text()
L0_SOURCE = (Path(__file__).resolve().parents[1] / "references" / "rules" / "agent-routing-kernel.md").read_text()
L1_V1 = (Path(__file__).resolve().parents[1] / "references" / "rules" / "openspec-superpowers-workflow.md").read_text()

# L0 受管区块标记（v1 为当前版本；v0 为受支持旧版本的合成样本）
V1_START = "<!-- cadence-managed:openspec-superpowers-routing:v1:start -->"
V1_END = "<!-- cadence-managed:openspec-superpowers-routing:v1:end -->"
V0_START = "<!-- cadence-managed:openspec-superpowers-routing:v0:start -->"
V0_END = "<!-- cadence-managed:openspec-superpowers-routing:v0:end -->"

# L1 版本标记（单行，位于文件首行）
V1_L1_MARKER = "<!-- cadence-framework-rule:openspec-superpowers-workflow:v1 -->"
V0_L1_MARKER = "<!-- cadence-framework-rule:openspec-superpowers-workflow:v0 -->"
V0_L1_TEXT = V0_L1_MARKER + "\n# 旧版协作规则\n旧版正文\n"


class TestMergeMarkdown(unittest.TestCase):
    def test_appends_project_only_sections_in_order(self):
        """ut-merge_markdown-keep-project-sections / NC-02"""
        tpl = "# T\n\n## A\ntpl-a\n\n## B\ntpl-b\n"
        old = "# T\n\n## A\nold-a\n\n## C\nold-c\n"
        out = rc.merge_markdown(tpl, old)
        self.assertIn("tpl-a", out); self.assertIn("## C", out)
        self.assertLess(out.index("## B"), out.index("## C"))
    def test_same_name_section_gets_project_supplement(self):
        """ut-merge_markdown-same-section-append / NC-03"""
        tpl = "## 1. 规则\ntpl-line\n"
        old = "## 1. 规则\ntpl-line\nold-line\n"
        out = rc.merge_markdown(tpl, old)
        self.assertEqual(out.count("tpl-line"), 1)  # 去重
        self.assertIn("项目补充", out); self.assertIn("old-line", out)
    def test_numbering_stripped_for_identity(self):
        """ut-merge_markdown-section-identity / NB-01（去除开头编号后判同名）"""
        self.assertIn("old", rc.merge_markdown("## 规则\nx\n", "## 3. 规则\nx\nold\n"))
    def test_unparseable_returns_none(self):
        """ut-merge_markdown-unparseable-fallback / NC-08（函数级终止信号，备份与标准结构回退由调用方执行）"""
        self.assertIsNone(rc.merge_markdown("# T\nx\n", "\x00\x01binary"))

    def test_target_missing_returns_template(self):
        """ut-merge_markdown-target-missing / NC-01"""
        tpl = "# T\n\n## A\ntpl-a\n"
        self.assertEqual(rc.merge_markdown(tpl, None), tpl)

    def test_duplicate_content_kept_once(self):
        """ut-merge_markdown-dedupe / NC-07"""
        out = rc.merge_markdown("## A\nsame-line\n", "## A\nsame-line\n")
        self.assertEqual(out.count("same-line"), 1)

    def test_different_heading_level_not_same_section(self):
        """ut-merge_markdown-section-identity / NB-01（级别不同不判同名，项目章节原样保留）"""
        out = rc.merge_markdown("## 规则\ntpl\n", "### 规则\nold\n")
        self.assertIn("### 规则", out)
        self.assertIn("old", out)

    def test_mandatory_conflict_template_wins_techstack_preserved(self):
        """ut-merge_markdown-mandatory-override / NC-04"""
        tpl = "## 强制规则\n- 必须使用中文回答 → 详见 `.claude/rules/language.md`\n"
        old = "## 强制规则\n- 旧摘要\n\n## 项目技术栈\n- Python\n"
        out = rc.merge_markdown(tpl, old)
        self.assertIn("必须使用中文回答", out)
        self.assertIn("## 项目技术栈", out)
        self.assertIn("- Python", out)
        self.assertLess(out.index("必须使用中文回答"), out.index("## 项目技术栈"))


class TestL0Block(unittest.TestCase):
    def test_skip_when_v1_block_matches_source(self):
        """ut-l0_block-read-source / L0-P1 + L0-P6（v1 标记对且区块与规范源逐字一致）"""
        text = "# CLAUDE.md\n\n文件说明\n\n" + L0_SOURCE + "\n## 强制规则\n- x\n"
        self.assertEqual(rc.l0_block(text, L0_SOURCE), "skip")

    def test_drift_when_v1_markers_but_content_differs(self):
        """ut-l0_block-drift / L0-P7（v1 标记对但区块内容不同）"""
        text = V1_START + "\n本地修改内容\n" + V1_END + "\n"
        self.assertEqual(rc.l0_block(text, L0_SOURCE), "drift")

    def test_insert_when_no_markers(self):
        """ut-l0_block-insert / L0-05（两个标记都不存在）"""
        self.assertEqual(rc.l0_block("# 入口\n无标记内容\n", L0_SOURCE), "insert")

    def test_insert_position_two_branches(self):
        """ut-l0_block-insert-position / L0-P8（有/无 `## 强制规则` 两分支均判 insert，落点由调用方保证）"""
        with_rules = "# 入口\n文件说明\n\n## 强制规则\n- x\n"
        without_rules = "# 入口\n文件说明\n"
        self.assertEqual(rc.l0_block(with_rules, L0_SOURCE), "insert")
        self.assertEqual(rc.l0_block(without_rules, L0_SOURCE), "insert")

    def test_upgrade_when_old_version_markers(self):
        """ut-l0_block-upgrade / L0-P9（成对受支持旧版本标记）"""
        text = V0_START + "\n旧版区块内容\n" + V0_END + "\n"
        self.assertEqual(rc.l0_block(text, L0_SOURCE), "upgrade")

    def test_broken_when_single_side_marker(self):
        """ut-l0_block-broken / L0-P10（单侧标记）"""
        self.assertEqual(rc.l0_block(V1_START + "\n内容\n", L0_SOURCE), "broken")
        self.assertEqual(rc.l0_block("内容\n" + V1_END + "\n", L0_SOURCE), "broken")

    def test_broken_when_markers_out_of_order(self):
        """ut-l0_block-broken / L0-P10（标记顺序错误）"""
        text = V1_END + "\n内容\n" + V1_START + "\n"
        self.assertEqual(rc.l0_block(text, L0_SOURCE), "broken")


class TestMergeYaml(unittest.TestCase):
    def test_appends_template_rules_dedup_preserving_order(self):
        """ut-merge_yaml-rules-append / OS-N7"""
        existing = "schema: spec-driven\ncontext: |\n  line1\nrules:\n  proposal:\n    - keep-me\n"
        merged, conflicts = rc.merge_yaml(TPL, existing)
        doc = yaml.safe_load(merged)
        self.assertEqual(doc["rules"]["proposal"][0], "keep-me")
        self.assertIn("记录 Why、范围、非目标和受影响 capability；不要写精确文件级实施步骤。", doc["rules"]["proposal"])
    def test_rules_apply_reported_as_conflict(self):
        """ut-merge_yaml-rules-apply-conflict / NC-05 + OS-N8（函数级只报告冲突，备份与移除由调用方执行）"""
        _, conflicts = rc.merge_yaml(TPL, "rules:\n  apply:\n    - x\n")
        self.assertEqual(conflicts[0]["kind"], "rules.apply")

    def test_preserve_existing_schema_context_and_extra_rules(self):
        """ut-merge_yaml-preserve-existing / NC-05"""
        existing = "schema: custom-schema\ncontext: |\n  项目上下文行\nrules:\n  proposal:\n    - 项目额外规则\n"
        merged, _ = rc.merge_yaml(TPL, existing)
        doc = yaml.safe_load(merged)
        self.assertEqual(doc["schema"], "custom-schema")
        self.assertIn("项目上下文行", doc["context"])
        self.assertIn("项目额外规则", doc["rules"]["proposal"])

    def test_unparseable_returns_abort_signal(self):
        """ut-merge_yaml-unparseable-abort / NC-06（函数级终止信号；目标文件 sha256 不变与备份由调用方保证）"""
        merged, _ = rc.merge_yaml(TPL, "rules: [unclosed\n")
        self.assertIsNone(merged)

    def test_schema_written_when_missing(self):
        """ut-merge_yaml-schema-default / OS-N5（缺失时写入 spec-driven）"""
        merged, _ = rc.merge_yaml(TPL, "context: |\n  x\n")
        self.assertEqual(yaml.safe_load(merged)["schema"], "spec-driven")

    def test_context_append_dedup_preserving_order(self):
        """ut-merge_yaml-context-append / OS-N6（按完整行去重，保留原顺序与项目上下文）"""
        first_tpl_line = "OpenSpec 是契约层：proposal 记录 Why、范围和非目标，design 记录架构边界与权衡，specs 记录 MUST/SHALL 验收场景，tasks 只记录高层工作包。"
        existing = "context: |\n  项目上下文行\n  " + first_tpl_line + "\n"
        merged, _ = rc.merge_yaml(TPL, existing)
        doc = yaml.safe_load(merged)
        self.assertEqual(doc["context"].count(first_tpl_line), 1)
        self.assertLess(doc["context"].index("项目上下文行"), doc["context"].index(first_tpl_line))

    def test_all_four_artifact_groups_present(self):
        """ut-merge_yaml-rules-append / OS-N7（四个 artifact 分组均补齐模板规则）"""
        merged, _ = rc.merge_yaml(TPL, "schema: spec-driven\n")
        doc = yaml.safe_load(merged)
        for group in ("proposal", "design", "specs", "tasks"):
            self.assertIn(group, doc["rules"])
            self.assertTrue(doc["rules"][group])

    def test_rules_append_dedup_and_extra_preserved(self):
        """ut-merge_yaml-rules-append / OS-N7（数组按完整字符串去重，顺序稳定）"""
        existing = "rules:\n  proposal:\n    - 记录 Why、范围、非目标和受影响 capability；不要写精确文件级实施步骤。\n    - 项目额外规则\n"
        merged, _ = rc.merge_yaml(TPL, existing)
        doc = yaml.safe_load(merged)
        self.assertEqual(doc["rules"]["proposal"].count("记录 Why、范围、非目标和受影响 capability；不要写精确文件级实施步骤。"), 1)
        self.assertEqual(doc["rules"]["proposal"][0], "记录 Why、范围、非目标和受影响 capability；不要写精确文件级实施步骤。")
        self.assertEqual(doc["rules"]["proposal"][1], "项目额外规则")

    def test_missing_pyyaml_exits_77(self):
        """ut-merge_yaml-missing-dependency / XC-06（PyYAML 缺失时退出码恰为 77 且 stderr 说明）"""
        code = (
            "import sys; sys.modules['yaml'] = None; "
            "import runpy; runpy.run_path(sys.argv[1], run_name='__main__')"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code, str(SCRIPT_PATH)],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 77)
        self.assertIn("yaml", (proc.stderr + proc.stdout).lower())


class TestPrecheckOpenspecStructure(unittest.TestCase):
    def test_type_conflict_listed(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2"""
        self.assertIn("rules.proposal", rc.precheck_openspec_structure({"rules": {"proposal": "not-a-list"}}))

    def test_valid_full_document_passes(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2（合法文档零冲突；自定义键原样保留）"""
        doc = {
            "schema": "spec-driven",
            "context": "ctx",
            "rules": {"proposal": ["a"], "design": ["b"], "specs": ["c"], "tasks": ["d"]},
            "custom-key": {"anything": [1, 2]},
        }
        self.assertEqual(rc.precheck_openspec_structure(doc), [])

    def test_empty_document_passes(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2（全部字段缺失均合法）"""
        self.assertEqual(rc.precheck_openspec_structure({}), [])

    def test_schema_scalar_passes(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2（schema 可保留标量）"""
        self.assertEqual(rc.precheck_openspec_structure({"schema": 1}), [])

    def test_root_must_be_mapping(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2（根非映射必报冲突）"""
        self.assertTrue(rc.precheck_openspec_structure(["not-a-mapping"]))

    def test_schema_must_be_scalar(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2"""
        self.assertIn("schema", rc.precheck_openspec_structure({"schema": ["x"]}))

    def test_context_must_be_string(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2"""
        self.assertIn("context", rc.precheck_openspec_structure({"context": {"k": 1}}))

    def test_rules_must_be_mapping(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2"""
        self.assertIn("rules", rc.precheck_openspec_structure({"rules": "x"}))

    def test_artifact_items_must_be_strings(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2（四个 artifact 必须为字符串数组）"""
        self.assertIn("rules.design", rc.precheck_openspec_structure({"rules": {"design": [1]}}))


class TestBackupFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_backup_naming_and_original_kept(self):
        """ut-backup_file-naming / NB-02（备份名正则；原文件仍在且 sha256 不变）"""
        p = Path(self.tmp.name) / "rule.md"
        p.write_text("content\n")
        before = rc.sha256_file(p)
        backup = rc.backup_file(p)
        self.assertRegex(str(backup), r".*\.cadence-backup-\d{14}$")
        self.assertTrue(p.exists())
        self.assertEqual(rc.sha256_file(p), before)
        self.assertEqual(Path(backup).read_text(), "content\n")

    def test_backup_openspec_naming(self):
        """ut-backup_file-openspec-naming / OS-B1（固定名 config.yaml.cadence-backup-<14位时间戳>，同目录）"""
        d = Path(self.tmp.name) / "openspec"
        d.mkdir()
        p = d / "config.yaml"
        p.write_text("schema: spec-driven\n")
        backup = rc.backup_file(p)
        self.assertRegex(Path(backup).name, r"^config\.yaml\.cadence-backup-\d{14}$")
        self.assertEqual(Path(backup).parent, d)

    def test_backup_l1_naming(self):
        """ut-backup_file-l1-naming / L1-B1（固定名 openspec-superpowers-workflow.md.cadence-backup-<14位时间戳>）"""
        d = Path(self.tmp.name) / ".claude" / "rules"
        d.mkdir(parents=True)
        p = d / "openspec-superpowers-workflow.md"
        p.write_text(L1_V1)
        backup = rc.backup_file(p)
        self.assertRegex(Path(backup).name, r"^openspec-superpowers-workflow\.md\.cadence-backup-\d{14}$")
        self.assertEqual(Path(backup).parent, d)


class TestAtomicWrite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_publish_content_consistent(self):
        """ut-atomic_write-publish / OS-N11（原子创建，发布后内容一致）"""
        target = Path(self.tmp.name) / "new.yaml"
        rc.atomic_write(target, "schema: spec-driven\n")
        self.assertEqual(target.read_text(), "schema: spec-driven\n")

    def test_replace_existing_atomically(self):
        """ut-atomic_write-replace / XC-07（经原子替换覆盖已有目标）"""
        target = Path(self.tmp.name) / "f.txt"
        target.write_text("old\n")
        rc.atomic_write(target, "new\n")
        self.assertEqual(target.read_text(), "new\n")

    def test_fail_readonly_dir_keeps_original(self):
        """ut-atomic_write-fail / OS-N13（fx-readonly-target：chmod 555 复现发布失败，原文件保持）"""
        d = Path(self.tmp.name) / "readonly"
        d.mkdir()
        target = d / "config.yaml"
        target.write_text("original\n")
        os.chmod(d, 0o555)
        self.addCleanup(os.chmod, d, 0o755)
        with self.assertRaises(OSError):
            rc.atomic_write(target, "new\n")
        self.assertEqual(target.read_text(), "original\n")


class TestSha256File(unittest.TestCase):
    def test_sha256_matches_hashlib(self):
        """ut-sha256_file-basic / XC-07（结果与 hashlib/系统工具一致）"""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "f.txt"
            p.write_bytes(b"hello cadence\n")
            self.assertEqual(rc.sha256_file(p), hashlib.sha256(b"hello cadence\n").hexdigest())


class TestClassifyL1(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.known = {"v0": V0_L1_TEXT}

    def _write(self, content):
        p = Path(self.tmp.name) / "openspec-superpowers-workflow.md"
        p.write_text(content)
        return p

    def test_current_v1_returns_skip(self):
        """ut-classify_l1-current / L1-02（完整内容与当前框架 v1 一致）"""
        p = self._write(L1_V1)
        self.assertEqual(rc.classify_l1(p, L1_V1, self.known), "skip")

    def test_known_old_version_returns_upgrade(self):
        """ut-classify_l1-old-version / L1-03（完整内容与注入的 known_versions 旧版逐字一致）"""
        p = self._write(V0_L1_TEXT)
        self.assertEqual(rc.classify_l1(p, L1_V1, self.known), "upgrade")

    def test_old_marker_drift_returns_replace(self):
        """ut-classify_l1-old-marker-drift / L1-04（仅旧版标记匹配但内容不同 → 不匹配 → replace）"""
        p = self._write(V0_L1_MARKER + "\n# 漂移内容\n")
        self.assertEqual(rc.classify_l1(p, L1_V1, self.known), "replace")

    def test_v1_marker_drift_returns_replace(self):
        """ut-classify_l1-v1-marker-drift / L1-05（v1 标记存在但完整内容不同 → 不得当作 current）"""
        p = self._write(V1_L1_MARKER + "\n# 漂移内容\n")
        self.assertEqual(rc.classify_l1(p, L1_V1, self.known), "replace")

    def test_unmarked_returns_replace(self):
        """ut-classify_l1-unmarked / L1-06（无标记文件不得当作已知框架版本）"""
        p = self._write("# 无标记文件\ncontent\n")
        self.assertEqual(rc.classify_l1(p, L1_V1, self.known), "replace")

    def test_classification_by_full_content_not_marker(self):
        """ut-classify_l1-full-compare / L1-B2（标记只定位候选版本，最终识别必须比较完整内容）"""
        drift = self._write(V1_L1_MARKER + "\n篡改内容\n")
        self.assertEqual(rc.classify_l1(drift, L1_V1, self.known), "replace")
        exact_old = self._write(V0_L1_TEXT)
        self.assertEqual(rc.classify_l1(exact_old, L1_V1, self.known), "upgrade")


if __name__ == "__main__":
    unittest.main()
