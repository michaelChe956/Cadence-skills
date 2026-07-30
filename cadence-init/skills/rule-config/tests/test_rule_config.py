# rule-config 脚本纯函数库单元测试（RED 骨架）
#
# 用例清单来源：tests/skill-clause-map.md（Task 1 产物）。
# 每个测试方法的 docstring 第一行标注对应 ut-* 测试 ID 与条款编号。
# 加载方式与签名由 Plan 全局约束冻结，Task 4-9 必须逐字实现：
#   rc.merge_markdown / rc.merge_yaml / rc.l0_block / rc.precheck_openspec_structure
#   rc.backup_file / rc.atomic_write / rc.sha256_file / rc.classify_l1
#   rc.detect_project / rc.locate_templates  （Task 5 实现）

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


# ---------------------------------------------------------------------------
# Task 5：detect_project / locate_templates 纯函数单测（ut-detect_project-* / ut-locate_templates-*）
# 用例清单来源：tests/skill-clause-map.md §2.8（S1a-01~05 / S1b-01~04）与 §2.5/2.6（DF-01/02、IA-02）。
# 加载方式与 Task 4 一致；测试自建临时 fixture，不依赖仓库实际环境。
# ---------------------------------------------------------------------------

# locate_templates 成对校验所需的最小文件集（在线/离线路径三件套 + config.yaml）
_ONLINE_RULES = ("agent-routing-kernel.md", "language.md", "openspec-superpowers-workflow.md")
# 回退 glob 路径额外需要 document-storage.md（S1b-02）
_FALLBACK_EXTRA = ("document-storage.md",)


def _write_minimal_templates(rules_dir: Path, *, fallback: bool = False) -> None:
    """在 rules_dir 下创建成对校验所需的最小模板占位文件 + 同级 openspec/config.yaml。"""
    rules_dir.mkdir(parents=True, exist_ok=True)
    for name in _ONLINE_RULES:
        (rules_dir / name).write_text(f"# placeholder {name}\n", encoding="utf-8")
    if fallback:
        for name in _FALLBACK_EXTRA:
            (rules_dir / name).write_text(f"# placeholder {name}\n", encoding="utf-8")
    openspec_dir = rules_dir.parent / "openspec"
    openspec_dir.mkdir(parents=True, exist_ok=True)
    (openspec_dir / "config.yaml").write_text("schema: spec-driven\n", encoding="utf-8")


def _intents(**overrides):
    """构造 rc.Intents，默认空意图。"""
    defaults = dict(
        no_interrupt=False,
        project_type=None,
        ignore_cadence=False,
        enable_playwright=False,
        enable_codegraph=False,
        decisions=None,
    )
    defaults.update(overrides)
    return rc.Intents(**defaults)


class TestDetectProject(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    # --- ut-detect_project-coding / DF-01（检测到源码 → Coding）---
    def test_source_file_detected_as_coding(self):
        """ut-detect_project-coding / DF-01（首命中源码即判 Coding；evidence 记录相对路径）"""
        (self.root / "app").mkdir()
        (self.root / "app" / "main.py").write_text("print('hi')\n")
        result = rc.detect_project(self.root, _intents())
        self.assertEqual(result["project_type"], "coding")
        self.assertIsInstance(result["evidence"], str)
        self.assertTrue(result["evidence"])  # 非空证据

    # --- ut-detect_project-noncoding / DF-01（无源码无主配置 → 非 Coding）---
    def test_empty_project_is_noncoding(self):
        """ut-detect_project-noncoding / DF-01（无源码无主配置 → non-coding）"""
        (self.root / "README.md").write_text("docs only\n")
        result = rc.detect_project(self.root, _intents())
        self.assertEqual(result["project_type"], "non-coding")

    # --- ut-detect_project-bounded-scan / S1a-01（剪枝目录内源码不触发；首命中即停）---
    def test_pruned_dirs_skipped_and_first_match_stops(self):
        """ut-detect_project-bounded-scan / S1a-01（剪枝目录内源码不触发 Coding；首命中即返回）"""
        # node_modules 内有 .js（应被剪枝，不触发）
        nm = self.root / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module.exports = 1;\n")
        # .venv 内有 .py（应被剪枝）
        venv = self.root / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "x.py").write_text("x = 1\n")
        result = rc.detect_project(self.root, _intents())
        self.assertEqual(result["project_type"], "non-coding")
        # 加入一个真实源码后应立即判 coding（首命中即停）
        src = self.root / "src"
        src.mkdir()
        (src / "a.ts").write_text("export const x = 1;\n")
        result2 = rc.detect_project(self.root, _intents())
        self.assertEqual(result2["project_type"], "coding")

    # --- ut-detect_project-main-config / S1a-03（仅主工程配置即判 Coding）---
    def test_main_config_without_source_is_coding(self):
        """ut-detect_project-main-config / S1a-03（仅 package.json/pyproject.toml 即判 Coding；evidence 记主配置）"""
        (self.root / "package.json").write_text('{"name": "demo"}\n', encoding="utf-8")
        result = rc.detect_project(self.root, _intents())
        self.assertEqual(result["project_type"], "coding")
        self.assertIn("package.json", result["evidence"])

    # --- ut-detect_project-user-override / S1a-04（--project-type 优先于检测）---
    def test_user_override_takes_precedence(self):
        """ut-detect_project-user-override / S1a-04（intents.project_type 覆盖检测结果）"""
        (self.root / "app.py").write_text("x = 1\n")  # 检测应为 coding
        result = rc.detect_project(self.root, _intents(project_type="non-coding"))
        self.assertEqual(result["project_type"], "non-coding")  # 用户指定优先

    # --- ut-detect_project-conflict / IA-02（矛盾判定 → s1:project-type-conflict）---
    def test_user_override_conflict_with_detection(self):
        """ut-detect_project-conflict / IA-02（用户指定与检测矛盾 → conflict 字段标记 s1:project-type-conflict；project_type 仍取用户值）"""
        (self.root / "app.py").write_text("x = 1\n")  # 检测为 coding
        result = rc.detect_project(self.root, _intents(project_type="non-coding"))
        self.assertEqual(result["project_type"], "non-coding")  # 用户值优先
        conflict = result.get("conflict")
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict["conflict_id"], "s1:project-type-conflict")
        self.assertEqual(conflict["allowed_decisions"], ["coding", "non-coding"])

    # --- ut-detect_project-techstack / S4-01（package.json scripts + pytest 检测 + 默认覆盖率 80%）---
    def test_techstack_extracted_from_package_json_and_pytest(self):
        """ut-detect_project-techstack / S4-01（package.json scripts 提取 test/lint/format；requirements.txt 检测 pytest；coverage 默认 80%）"""
        import json as _json
        (self.root / "package.json").write_text(_json.dumps({
            "name": "demo",
            "scripts": {"test": "vitest", "lint": "eslint .", "format": "prettier --write ."},
        }), encoding="utf-8")
        result = rc.detect_project(self.root, _intents())
        ts = result["tech_stack"]
        self.assertEqual(ts["test"], "vitest")
        self.assertEqual(ts["lint"], "eslint .")
        self.assertEqual(ts["format"], "prettier --write .")
        self.assertEqual(ts["coverage"], "80%")

    def test_techstack_pytest_detected_from_requirements(self):
        """ut-detect_project-techstack / S4-01（requirements.txt 含 pytest → test 字段为 pytest）"""
        (self.root / "requirements.txt").write_text("pytest\nrequests\n", encoding="utf-8")
        result = rc.detect_project(self.root, _intents())
        ts = result["tech_stack"]
        self.assertEqual(ts["test"], "pytest")
        # lint/format 未检出 → 未检测到
        self.assertEqual(ts["lint"], "未检测到")
        self.assertEqual(ts["format"], "未检测到")

    def test_techstack_undetected_defaults(self):
        """ut-detect_project-techstack / S4-03（无任何可检测配置 → 各命令写「未检测到」不阻塞）"""
        (self.root / "README.md").write_text("docs\n")
        result = rc.detect_project(self.root, _intents())
        ts = result["tech_stack"]
        self.assertEqual(ts["test"], "未检测到")
        self.assertEqual(ts["lint"], "未检测到")
        self.assertEqual(ts["format"], "未检测到")
        # coverage 默认仍为 80%
        self.assertEqual(ts["coverage"], "80%")


class TestLocateTemplates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "fakehome"
        self.home.mkdir()
        # 记录原始 HOME，用 addCleanup 恢复
        self._orig_home = os.environ.get("HOME")
        os.environ["HOME"] = str(self.home)
        self.addCleanup(self._restore_home)

    def _restore_home(self):
        if self._orig_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._orig_home

    # --- ut-locate_templates-online / S1b-01（在线路径优先命中）---
    def test_online_path_preferred(self):
        """ut-locate_templates-online / S1b-01（在线 marketplace 路径完整时优先返回）"""
        online = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-marketplace"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(online)
        rules_root, openspec_yaml = rc.locate_templates()
        self.assertEqual(rules_root, online)
        self.assertTrue(openspec_yaml.exists())
        self.assertEqual(openspec_yaml.name, "config.yaml")

    # --- ut-locate_templates-offline / S1b-01（离线路径命中）---
    def test_offline_path_used_when_online_missing(self):
        """ut-locate_templates-offline / S1b-01（在线缺失时回退到离线 cadence-skills-local）"""
        offline = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-local"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(offline)
        rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, offline)

    # --- ut-locate_templates-fallback / S1b-01（glob 回退；需 document-storage.md）---
    def test_glob_fallback_when_fixed_paths_missing(self):
        """ut-locate_templates-fallback / S1b-01（固定路径均缺失时 glob 回退；候选需含 document-storage.md）"""
        # 在 fakehome 下构造一个 glob 可命中的候选（带 document-storage.md）
        dev_candidate = (
            self.home / "workspace" / "proj" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(dev_candidate, fallback=True)
        rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, dev_candidate)

    # --- ut-locate_templates-pair-check / S1b-02（缺成对文件或 config.yaml 的候选被跳过）---
    def test_incomplete_candidate_skipped(self):
        """ut-locate_templates-pair-check / S1b-02（在线候选缺 config.yaml → 跳过；落到 glob 回退完整候选）"""
        # 在线候选缺 config.yaml（不写 openspec/config.yaml）
        online_rules = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-marketplace"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        online_rules.mkdir(parents=True)
        for name in _ONLINE_RULES:
            (online_rules / name).write_text("# x\n")
        # 故意不写 openspec/config.yaml → 该候选不完整
        # glob 回退候选完整（带 document-storage.md + config.yaml）
        dev_candidate = (
            self.home / "workspace" / "proj" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(dev_candidate, fallback=True)
        rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, dev_candidate)

    # --- ut-locate_templates-mtime-latest / S1b-03（多候选取 mtime 最新）---
    def test_multiple_candidates_pick_latest_mtime(self):
        """ut-locate_templates-mtime-latest / S1b-03（glob 多候选通过校验后取修改时间最新者）"""
        old_candidate = (
            self.home / "workspace" / "old" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        new_candidate = (
            self.home / "workspace" / "new" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(old_candidate, fallback=True)
        _write_minimal_templates(new_candidate, fallback=True)
        # 确保老候选的 openspec_yaml（mtime 比较基准）严格更新
        import time as _time
        _time.sleep(0.05)
        (old_candidate.parent / "openspec" / "config.yaml").touch()
        # 断言：mtime 主导 → 老候选胜出
        rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, old_candidate)

    # --- ut-locate_templates-online-preferred-over-offline / S1b-01（双有效场景在线优先）---
    def test_online_preferred_over_offline_when_both_valid(self):
        """ut-locate_templates-online-preferred / S1b-01（在线与离线均完整且离线 mtime 更新时仍返回在线）"""
        online = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-marketplace"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        offline = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-local"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(online)
        _write_minimal_templates(offline)
        # 让离线 mtime 严格更新，确保“在线优先”是短路优先级而非 mtime 选择
        import time as _time
        _time.sleep(0.05)
        (offline / "language.md").touch()
        rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, online)

    # --- ut-locate_templates-error-lists-missing / S1b-04（TemplateError 列出每个候选缺失文件名）---
    def test_template_error_lists_missing_files(self):
        """ut-locate_templates-error-lists-missing / S1b-04（全不完整时 TemplateError 消息列出缺失文件名）"""
        # 在线候选：目录存在但缺 openspec/config.yaml（三件套齐全）
        online_rules = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-marketplace"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        online_rules.mkdir(parents=True)
        for name in _ONLINE_RULES:
            (online_rules / name).write_text("# x\n", encoding="utf-8")
        # 离线候选：目录存在但缺 language.md
        offline_rules = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-local"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        offline_rules.mkdir(parents=True)
        for name in (_ONLINE_RULES[0], _ONLINE_RULES[2]):  # 仅写 ark + osw，缺 language.md
            (offline_rules / name).write_text("# x\n", encoding="utf-8")
        # glob 回退候选：目录存在但缺 document-storage.md（fallback 额外要求）
        dev_rules = (
            self.home / "workspace" / "proj" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        dev_rules.mkdir(parents=True)
        for name in _ONLINE_RULES:
            (dev_rules / name).write_text("# x\n", encoding="utf-8")
        # 故意不写 document-storage.md，并补上 config.yaml 让 language.md 作为 glob 标识可命中
        openspec_dir = dev_rules.parent / "openspec"
        openspec_dir.mkdir(parents=True, exist_ok=True)
        (openspec_dir / "config.yaml").write_text("schema: spec-driven\n", encoding="utf-8")
        with self.assertRaises(rc.TemplateError) as ctx:
            rc.locate_templates()
        msg = str(ctx.exception)
        # 断言消息含每个候选具体缺失的文件名
        self.assertIn("openspec/config.yaml", msg)  # 在线候选缺
        self.assertIn("language.md", msg)  # 离线候选缺
        self.assertIn("document-storage.md", msg)  # 回退候选缺
        self.assertIn("在线候选", msg)
        self.assertIn("离线候选", msg)
        self.assertIn("回退候选", msg)

    # --- ut-locate_templates-all-incomplete / S1b-04（全不完整 → TemplateError）---
    def test_all_incomplete_raises_template_error(self):
        """ut-locate_templates-all-incomplete / S1b-04（所有候选均不完整 → TemplateError 终止）"""
        # 不创建任何模板候选；HOME 下无任何 cadence-init/skills/rule-config 路径
        # glob 也无命中 → TemplateError
        with self.assertRaises(rc.TemplateError):
            rc.locate_templates()


# ---------------------------------------------------------------------------
# Task 6：step_s3_rules_files / step_s4_entry_files step 级集成断言
# 验证 S3（含 L1 独立分支红线）与 S4（双入口合成 + 幂等 + 漂移修复）的核心行为。
# 不重复 Task 2 纯函数单测；聚焦 step 函数对 plan/report 的驱动与文件产出。
# ---------------------------------------------------------------------------


class TestStepS3RulesFiles(unittest.TestCase):
    """step_s3_rules_files 集成断言：普通规则分支、L1 独立分支、Playwright。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # 模板根：复用 skill 自带 references/rules
        self.rules_root = Path(__file__).resolve().parents[1] / "references" / "rules"
        self.kernel = (self.rules_root / "agent-routing-kernel.md").read_text(encoding="utf-8")
        self.l1_v1 = (self.rules_root / rc.L1_RULE_FILENAME).read_text(encoding="utf-8")
        self.language_tpl = (self.rules_root / "language.md").read_text(encoding="utf-8")
        self.playwright_tpl = (self.rules_root / "playwright.md").read_text(encoding="utf-8")

    def _base_plan(self, **overrides):
        plan = {
            "project_type": "non-coding",
            "templates": {"rules_root": str(self.rules_root)},
            "decisions_map": {},
            "steps": {},
        }
        plan.update(overrides)
        return plan

    def test_ordinary_rule_created_when_missing(self):
        """ut-step_s3-ordinary-create / RF-01（普通规则不存在 → 读模板创建）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / "language.md"
        plan = self._base_plan(steps={
            rc.STEP_RULES_FILES: {
                "name": rc.STEP_RULES_FILES, "status": "ok",
                "assets": [{
                    "path": ".claude/rules/language.md", "action": "create",
                    "conflict": None, "backup_needed": False, "is_l1": False,
                }],
            }
        })
        rc.step_s3_rules_files(self.root, _intents(), plan, {})
        self.assertEqual(target.read_text(encoding="utf-8"), self.language_tpl)

    def test_l1_independent_branch_no_merge_no_supplement(self):
        """ut-step_s3-l1-red-line / L1 独立分支红线（no-interrupt → 直接写 v1 模板；
        结果不得含「项目补充」，不调 merge_markdown）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / rc.L1_RULE_FILENAME
        # 项目旧版内容（漂移）
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
        rc.step_s3_rules_files(self.root, _intents(no_interrupt=True), plan, {})
        result = target.read_text(encoding="utf-8")
        self.assertEqual(result, self.l1_v1)  # 逐字等于 v1 规范源
        self.assertNotIn("项目补充", result)  # 红线：不含项目补充

    def test_playwright_existing_not_overwritten(self):
        """ut-step_s3-playwright-no-overwrite / RF-02（已存在 playwright.md 不覆盖）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / "playwright.md"
        custom = "# 自定义 playwright\n保留\n"
        target.write_text(custom, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_RULES_FILES: {
                "name": rc.STEP_RULES_FILES, "status": "ok",
                "assets": [{
                    "path": ".claude/rules/playwright.md", "action": "skip",
                    "conflict": None, "backup_needed": False, "is_l1": False,
                }],
            }
        })
        rc.step_s3_rules_files(
            self.root, _intents(no_interrupt=True, enable_playwright=True), plan, {}
        )
        self.assertEqual(target.read_text(encoding="utf-8"), custom)

    def test_ordinary_no_interrupt_merge_uses_project_supplement(self):
        """ut-step_s3-ordinary-merge / NC-03（普通规则 no-interrupt → merge_markdown 章节合并，含项目补充）"""
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
        rc.step_s3_rules_files(self.root, _intents(no_interrupt=True), plan, {})
        result = target.read_text(encoding="utf-8")
        self.assertIn("项目补充", result)  # 普通规则走 merge，含项目补充
        self.assertIn("项目独有行", result)


class TestStepS4EntryFiles(unittest.TestCase):
    """step_s4_entry_files 集成断言：双入口合成、幂等、漂移修复。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rules_root = Path(__file__).resolve().parents[1] / "references" / "rules"
        self.kernel = (self.rules_root / "agent-routing-kernel.md").read_text(encoding="utf-8")

    def _base_plan(self, **overrides):
        plan = {
            "project_type": "non-coding",
            "templates": {"rules_root": str(self.rules_root)},
            "decisions_map": {},
            "steps": {},
        }
        plan.update(overrides)
        return plan

    def test_entry_created_from_base_when_missing(self):
        """ut-step_s4-base-created / L0-P5（入口不存在 → BASE 基线 + L0 + 强制规则）"""
        plan = self._base_plan(steps={
            rc.STEP_ENTRY_FILES: {
                "name": rc.STEP_ENTRY_FILES, "status": "ok",
                "assets": [{
                    "path": "CLAUDE.md", "action": "create",
                    "conflict": None, "backup_needed": False,
                }],
            }
        })
        rc.step_s4_entry_files(self.root, _intents(no_interrupt=True), plan, {})
        text = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn(rc.L0_BEGIN, text)
        self.assertIn(rc.L0_END, text)
        self.assertIn("## 强制规则", text)

    def test_skip_state_idempotent_no_change(self):
        """ut-step_s4-skip-idempotent / L0-P6（skip 状态 → 不修改入口）"""
        entry = self.root / "CLAUDE.md"
        # 构造一个 skip 状态的入口（L0 区块 = 规范源）
        base = "# CLAUDE.md\n\n说明\n\n" + self.kernel + "\n## 强制规则\n- x\n"
        entry.write_text(base, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_ENTRY_FILES: {
                "name": rc.STEP_ENTRY_FILES, "status": "ok",
                "assets": [{
                    "path": "CLAUDE.md", "action": "skip",
                    "conflict": None, "backup_needed": False,
                }],
            }
        })
        rc.step_s4_entry_files(self.root, _intents(no_interrupt=True), plan, {})
        self.assertEqual(entry.read_text(encoding="utf-8"), base)

    def test_drift_replaced_block_matches_source_outside_preserved(self):
        """ut-step_s4-drift-replace / L0-P7+L0-B2（no-interrupt 修复 drift：区块=规范源，区块外逐字保留）"""
        entry = self.root / "CLAUDE.md"
        # 构造 drift：L0 区块内含漂移内容
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
        rc.step_s4_entry_files(self.root, _intents(no_interrupt=True), plan, {})
        result = entry.read_text(encoding="utf-8")
        # 区块 = 规范源
        begin = result.index(rc.L0_BEGIN)
        end = result.index(rc.L0_END, begin) + len(rc.L0_END)
        self.assertEqual(result[begin:end].strip(), self.kernel.strip())
        # 区块外保留用户内容（漂移内容被移除）
        self.assertNotIn("漂移内容", result)
        self.assertIn("- 用户规则", result)


if __name__ == "__main__":
    unittest.main()

