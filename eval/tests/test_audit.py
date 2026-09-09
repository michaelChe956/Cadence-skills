"""eval/tests/test_audit.py —— 既有 session 审计表（tasks 4.6 / oracle §2-d）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.runner import audit as aud

TRANS = Path(__file__).resolve().parents[1] / "transcripts"


class TestAudit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def test_audit_fabricated_home(self):
        """ut-aud-scan：伪造 HOME 树——工具分布/命令头/模型分布可统计。"""
        claude_dir = self.base / "projects" / "proj-a"
        claude_dir.mkdir(parents=True)
        (claude_dir / "s1.jsonl").write_text(
            (TRANS / "claude" / "golden-1.jsonl").read_text(encoding="utf-8"),
            encoding="utf-8")
        data = aud.audit_dirs({"claude": self.base / "projects"}, limit_per_agent=10)
        per = data["per_agent"]["claude"]
        self.assertEqual(per["sessions"], 1)
        self.assertGreaterEqual(per["tools"]["Bash"], 1)
        self.assertIn("mcp__codegraph__codegraph_explore", per["tools"])
        self.assertEqual(per["bash_heads"]["ls -R src"], 1)
        self.assertEqual(per["models"]["glm-5.3"], 1)
        self.assertEqual(per["denials"], 1)

    def test_limit_per_agent(self):
        """ut-aud-limit：每端扫描上限（313MB～1.6GB 存量不可全量解析）。"""
        claude_dir = self.base / "projects"
        claude_dir.mkdir(parents=True)
        golden = (TRANS / "claude" / "golden-1.jsonl").read_text(encoding="utf-8")
        for i in range(5):
            (claude_dir / f"s{i}.jsonl").write_text(golden, encoding="utf-8")
        data = aud.audit_dirs({"claude": claude_dir}, limit_per_agent=2)
        self.assertEqual(data["per_agent"]["claude"]["sessions"], 2)

    def test_write_audit_outputs(self):
        """ut-aud-write：json+md 双产物；md 含观测定位声明（不进 gate）。"""
        claude_dir = self.base / "projects"
        claude_dir.mkdir(parents=True)
        (claude_dir / "s1.jsonl").write_text(
            (TRANS / "claude" / "golden-1.jsonl").read_text(encoding="utf-8"),
            encoding="utf-8")
        data = aud.audit_dirs({"claude": claude_dir})
        out = aud.write_audit(self.base / "out", data)
        md = (out / "audit.md").read_text(encoding="utf-8")
        self.assertIn("仅作观测参考", md)
        self.assertTrue((out / "audit.json").is_file())

    def test_gitignore_covers_reports(self):
        """ut-aud-gitignore：.gitignore 覆盖 cadence/reports/eval/（不入 git）。"""
        text = Path(".gitignore").read_text(encoding="utf-8")
        self.assertIn("cadence/reports/eval/", text)


if __name__ == "__main__":
    unittest.main()
