#!/usr/bin/env python3
"""apply.py 确定性章节合并测试（单元 + 端到端）。

运行：python3 tests/test_apply.py   （或经 tests/test-apply.sh 统一入口）
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import apply as prx  # noqa: E402

REFS = Path(__file__).resolve().parent.parent / "references" / "project-rules"
TEMPLATES = {tmpl_rel: (REFS / tmpl_rel).read_text(encoding="utf-8") for tmpl_rel, _ in prx.TARGETS}
PROJECT_RELS = [rel for _, rel in prx.TARGETS]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def drop_section(text: str, title_contains: str) -> str:
    """从模板文本中删除标题含 token 的章节，构造'缺失章节'夹具。"""
    sections = prx._sections(text)
    keep = [raw for _level, _key, _title, raw in sections if title_contains not in _title]
    assert len(keep) < len(sections), f"未找到章节：{title_contains}"
    return "\n".join("\n".join(raw) for raw in keep).rstrip() + "\n"


class PrxTestCase(unittest.TestCase):
    def make_root(self) -> Path:
        tmp = tempfile.TemporaryDirectory(prefix="prx-apply-pytest.")
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def write_target(self, root: Path, rel: str, text: str) -> None:
        path = root / "cadence" / "project-rules" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_apply(self, root: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "apply.py"), "--project-root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )

    def state_of(self, stdout: str, rel: str) -> str:
        """按行尾目标路径取状态；rel 可为模板相对路径（如 README.md）。"""
        for line in stdout.splitlines():
            parts = line.split(" ", 1)
            if len(parts) == 2 and (parts[1] == rel or parts[1].endswith(f"/{rel}")):
                return parts[0]
        return ""


class UnitTests(PrxTestCase):
    def test_fence_aware_parsing(self):
        text = "# 标题\n\n正文\n\n```text\n# 围栏内不是标题\n```\n\n## 第二节\n\n- x\n"
        self.assertEqual([t for _l, _k, t, _r in prx._sections(text)], ["标题", "第二节"])

    def test_multilevel_numbering_no_collision_drop(self):
        """6.2/7.2 等多级编号章节互不相同，不得因编号归一丢章节。"""
        text = "### 6.2 规则\n\n- a\n\n### 7.2 规则\n\n- b\n"
        merged, changed = prx.merge_missing_sections(text, text)
        self.assertFalse(changed)
        self.assertEqual(merged, text)

    def test_missing_appended_and_renumbered_matched(self):
        template = "## 1. 总体原则\n\n- a\n\n## 2. 编码规则\n\n- b\n"
        merged, changed = prx.merge_missing_sections(
            "## 1. 总体原则\n\n- 用户改写\n", template)
        self.assertTrue(changed)
        self.assertIn("## 2. 编码规则\n\n- b\n", merged)
        # 用户重编号：去编号标题按 (级别, key) 配对，不误判缺失
        _merged2, changed2 = prx.merge_missing_sections(
            "## 3. 总体原则\n\n- 用户改写\n\n## 9. 编码规则\n\n- b\n", template)
        self.assertFalse(changed2)

    def test_append_prefix_preserved(self):
        ours = "# 用户文档\n\n## 我的章节\n\n- 用户行\n\n\n"  # 尾部空行必须保留
        template = ours + "## 模板新章节\n\n- 模板行\n\n- 另一行\n"
        merged, changed = prx.merge_missing_sections(ours, template)
        self.assertTrue(changed)
        self.assertTrue(merged.startswith(ours), "既有字节必须零改动（仅追加）")
        self.assertIn("## 模板新章节", merged)
        self.assertIn("- 模板行\n\n- 另一行\n", merged)

    def test_append_empty_and_crlf(self):
        template = "## 新章节\n\n- 行\n"
        merged, changed = prx.merge_missing_sections("", template)
        self.assertTrue(changed)
        self.assertTrue(merged.startswith("## 新章节"))
        crlf = "# 文档\r\n\r\n## 节\r\n"
        merged_crlf, _ = prx.merge_missing_sections(crlf, template.replace("\n", "\r\n"))
        self.assertTrue(merged_crlf.startswith(crlf))
        self.assertIn("\r\n## 新章节\r\n\r\n- 行\r\n", merged_crlf)

    def test_guards_unparseable_kept(self):
        headingless = "纯文本说明，没有任何 Markdown 标题。\n第二行。\n"
        merged, changed = prx.merge_missing_sections(headingless, TEMPLATES["README.md"])
        self.assertFalse(changed)
        self.assertEqual(merged, headingless)
        unclosed = "# 标题\n\n```text\n未闭合\n"
        merged2, changed2 = prx.merge_missing_sections(unclosed, TEMPLATES["README.md"])
        self.assertFalse(changed2)
        self.assertEqual(merged2, unclosed)


class EndToEndTests(PrxTestCase):
    def test_fresh_project_created_and_entries_reported(self):
        root = self.make_root()
        result = self.run_apply(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        for rel in PROJECT_RELS:
            self.assertEqual(self.state_of(result.stdout, rel), "created", rel)
        for entry in prx.ENTRY_FILES:
            self.assertEqual(self.state_of(result.stdout, entry), "needs-rule-config")
            self.assertFalse((root / entry).exists(), f"{entry} 不得被创建")
        for tmpl_rel, rel in prx.TARGETS:
            self.assertEqual((root / rel).read_bytes(), (REFS / tmpl_rel).read_bytes(), rel)
        self.assertFalse((root / "cadence" / "legacy").exists(), "全新项目无备份")

    def test_rerun_pristine_zero_backup(self):
        root = self.make_root()
        self.run_apply(root)
        result = self.run_apply(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        for rel in PROJECT_RELS:
            self.assertEqual(self.state_of(result.stdout, rel), "pristine", rel)
        self.assertFalse((root / "cadence" / "legacy").exists())

    def test_customized_without_missing_unchanged(self):
        root = self.make_root()
        rel = "examples/coding-standards.md"
        customized = (
            TEMPLATES[rel].replace("**版本**: v1.0", "**版本**: v9.9-用户版")
            + "\n## 我的团队约定\n\n| 键 | 值 |\n|---|---|\n| 提交 | 必须跑回归 |\n"
        )
        self.write_target(root, rel, customized)
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, rel), "unchanged", result.stdout)
        self.assertEqual(
            (root / "cadence" / "project-rules" / rel).read_text(encoding="utf-8"),
            customized,
            "用户段落必须逐字保留",
        )
        self.assertFalse((root / "cadence" / "legacy").exists())

    def test_customized_without_base_is_not_appended(self):
        root = self.make_root()
        rel = "README.md"
        original = (
            drop_section(TEMPLATES[rel], "💡 提示")
            + "\n## 用户独有章节\n\n| 键 | 值 |\n|---|---|\n| 回归 | 必跑 |\n\n```text\n# 围栏里的伪标题\n```\n"
        )
        self.write_target(root, rel, original)
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, rel), "unchanged", result.stdout)
        merged = (root / "cadence" / "project-rules" / rel).read_text(encoding="utf-8")
        self.assertEqual(merged, original, "无基线且含用户内容时不得追加模板章节")
        self.assertFalse((root / "cadence" / "legacy").exists())

    def test_entry_files_untouched(self):
        root = self.make_root()
        claude = root / "CLAUDE.md"
        agents = root / "AGENTS.md"
        claude.write_text(
            "# CLAUDE.md\n\n## 项目个性化规则\n\n引用 cadence/project-rules/README.md\n",
            encoding="utf-8",
        )
        agents.write_text("# AGENTS.md\n\n普通内容，没有引用。\n", encoding="utf-8")
        hash_c, hash_a = sha(claude.read_text()), sha(agents.read_text())
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, "CLAUDE.md"), "skipped")
        self.assertEqual(self.state_of(result.stdout, "AGENTS.md"), "needs-rule-config")
        self.assertEqual(sha(claude.read_text()), hash_c, "CLAUDE.md 哈希必须不变")
        self.assertEqual(sha(agents.read_text()), hash_a, "AGENTS.md 哈希必须不变")

    def test_second_run_zero_writes(self):
        root = self.make_root()
        rel = "examples/test-standards.md"
        self.write_target(root, rel, drop_section(TEMPLATES[rel], "快照测试"))
        first = self.run_apply(root)
        self.assertEqual(self.state_of(first.stdout, rel), "merged")
        cadence = root / "cadence"
        snapshot = {
            str(p): sha(p.read_text(encoding="utf-8")) for p in cadence.rglob("*") if p.is_file()
        }
        legacy_before = {p.name for p in (cadence / "legacy").iterdir()}
        second = self.run_apply(root)
        self.assertEqual(second.returncode, 0, second.stderr)
        for line in second.stdout.splitlines():
            self.assertIn(
                line.split(" ", 1)[0], {"unchanged", "pristine", "skipped", "needs-rule-config"},
                f"第二次运行不得再写入：{line}",
            )
        snapshot_after = {
            str(p): sha(p.read_text(encoding="utf-8")) for p in cadence.rglob("*") if p.is_file()
        }
        self.assertEqual(snapshot, snapshot_after, "第二次运行文件内容必须零变化")
        self.assertEqual(
            legacy_before, {p.name for p in (cadence / "legacy").iterdir()}, "第二次运行零备份"
        )

    def test_unclosed_fence_unchanged(self):
        root = self.make_root()
        rel = "examples/design-template.md"
        text = TEMPLATES[rel] + "\n```text\n未闭合围栏\n"
        self.write_target(root, rel, text)
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, rel), "unchanged")
        self.assertEqual((root / "cadence" / "project-rules" / rel).read_text(encoding="utf-8"), text)

    def test_headingless_file_unchanged(self):
        root = self.make_root()
        rel = "README.md"
        text = "纯文本说明，没有任何 Markdown 标题。\n第二行。\n"
        self.write_target(root, rel, text)
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, rel), "unchanged")
        self.assertEqual((root / "cadence" / "project-rules" / rel).read_text(encoding="utf-8"), text)

    def test_empty_file_merged(self):
        root = self.make_root()
        rel = "README.md"
        self.write_target(root, rel, "")
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, rel), "merged", result.stdout)
        merged = (root / "cadence" / "project-rules" / rel).read_text(encoding="utf-8")
        self.assertIn("# 项目个性化规则文档", merged)
        second = self.run_apply(root)
        self.assertEqual(self.state_of(second.stdout, rel), "pristine")

    def test_missing_root_exit_2(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "apply.py"), "--project-root", "/nonexistent-prx-xyz"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
