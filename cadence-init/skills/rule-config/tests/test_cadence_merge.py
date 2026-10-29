"""共享 Markdown 合并模块测试（TDD RED 起点）。

覆盖设计文档 §5.3/§6/§8：围栏感知、标题归一、三方冲突用户胜、模板缺失章节补齐。
"""

import importlib.util
import json
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "cadence_merge.py"
spec = importlib.util.spec_from_file_location("cadence_merge", SCRIPT)
cm = importlib.util.module_from_spec(spec)
sys.modules["cadence_merge"] = cm
spec.loader.exec_module(cm)


class TestNormalizeTitle(unittest.TestCase):
    def test_strips_numbering_and_trailing_parenthetical(self):
        self.assertEqual(
            cm.normalize_title("### 6. 项目个性化规则（强制规则）"),
            "项目个性化规则",
        )

    def test_keeps_plain_title(self):
        self.assertEqual(cm.normalize_title("语言规则"), "语言规则")

    def test_hierarchical_number_is_not_collapsed(self):
        self.assertEqual(cm.normalize_title("### 6.2 规则"), "6.2 规则")
        self.assertEqual(cm.normalize_title("### 7.2 规则"), "7.2 规则")
        self.assertNotEqual(
            cm.normalize_title("### 6.2 规则"),
            cm.normalize_title("### 7.2 规则"),
        )


class TestParseSections(unittest.TestCase):
    def test_fence_hash_is_not_heading(self):
        text = (
            "# 文档\n\n"
            "## 1. A\n"
            "```bash\n"
            "# 这是注释不是标题\n"
            "```\n\n"
            "## 2. B\n"
            "正文\n"
        )
        sections = cm.parse_sections(text)
        self.assertEqual([s.key for s in sections], ["文档", "A", "B"])

    def test_body_preserves_blank_lines(self):
        text = "## 1. A\n\n第一段\n\n第二段\n"
        sections = cm.parse_sections(text)
        self.assertEqual(sections[0].body_lines, ["", "第一段", "", "第二段"])

    def test_longer_fence_is_not_closed_by_shorter(self):
        text = "````markdown\n```bash\n# 内层不是标题\n```\n````\n\n## 1. A\n正文\n"
        sections = cm.parse_sections(text)
        self.assertEqual([s.key for s in sections], ["A"])


class TestThreeWay(unittest.TestCase):
    def test_user_only_change_wins(self):
        merged, pending = cm.three_way("a\nb\n", "a\nUSER\n", "a\nb\n")
        self.assertEqual(merged, "a\nUSER\n")
        self.assertEqual(pending, [])

    def test_framework_only_change_applies(self):
        merged, pending = cm.three_way("a\nb\n", "a\nb\n", "a\nFRAME\n")
        self.assertEqual(merged, "a\nFRAME\n")
        self.assertEqual(pending, [])

    def test_overlap_keeps_user_and_records_pending(self):
        merged, pending = cm.three_way("a\nb\n", "a\nUSER\n", "a\nFRAME\n")
        self.assertIn("USER", merged)
        self.assertNotIn("FRAME", merged)
        self.assertTrue(pending)


class TestMergeSections(unittest.TestCase):
    def test_adds_missing_template_section_and_keeps_user_body(self):
        ours = "## 1. A\n用户正文\n"
        theirs = "## 1. A\n模板正文\n\n## 2. B\n模板 B\n"
        merged, pending = cm.merge_sections(None, ours, theirs)
        self.assertIn("用户正文", merged)
        self.assertIn("## 2. B", merged)
        self.assertIn("模板 B", merged)
        self.assertIn("用户正文", merged)

    def test_user_only_section_is_kept(self):
        ours = "## 1. A\n用户正文\n\n## 3. 用户独有\n保留\n"
        theirs = "## 1. A\n模板正文\n\n## 2. B\n模板 B\n"
        merged, _ = cm.merge_sections(None, ours, theirs)
        self.assertIn("## 3. 用户独有", merged)
        self.assertIn("保留", merged)

    def test_duplicate_titles_are_not_dropped(self):
        ours = "### 6.2 规则\n用户六\n\n### 7.2 规则\n用户七\n"
        theirs = "### 6.2 规则\n模板六\n\n### 7.2 规则\n模板七\n"
        merged, pending = cm.merge_sections(None, ours, theirs)
        self.assertIn("用户六", merged)
        self.assertIn("用户七", merged)
        self.assertTrue(any("模板六" in json.dumps(p, ensure_ascii=False) for p in pending))
        self.assertTrue(any("模板七" in json.dumps(p, ensure_ascii=False) for p in pending))


    def test_user_section_order_is_preserved(self):
        ours = "## A\n用户A\n\n## 用户独有\nUSER\n\n## B\n用户B\n"
        theirs = "## A\n模板A\n\n## B\n模板B\n\n## 新框架\nNEW\n"
        merged, _ = cm.merge_sections("## A\n模板A\n\n## B\n模板B\n", ours, theirs)
        self.assertLess(merged.find("## 用户独有"), merged.find("## B"))
        self.assertLess(merged.find("## B"), merged.find("## 新框架"))

    def test_fenced_preamble_is_preserved(self):
        ours = "```bash\n# 编译命令\nmake build\n```\n\n## 1. A\n用户正文\n"
        theirs = "## 1. A\n模板正文\n\n## 2. B\n模板 B\n"
        merged, _ = cm.merge_sections(None, ours, theirs)
        self.assertIn("```bash\n# 编译命令\nmake build\n```", merged)
        self.assertIn("用户正文", merged)
        self.assertIn("## 2. B", merged)


if __name__ == "__main__":
    unittest.main()
