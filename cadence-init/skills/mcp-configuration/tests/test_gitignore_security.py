"""MCP `.gitignore` 安全单元测试。"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mcp-config.py"
spec = importlib.util.spec_from_file_location("mcp_config_gitignore", SCRIPT)
mc = importlib.util.module_from_spec(spec)
sys.modules["mcp_config_gitignore"] = mc
spec.loader.exec_module(mc)


class TestGitignoreSecurity(unittest.TestCase):
    def test_adds_security_lines_and_removes_reverse_rules(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gi = root / ".gitignore"
            gi.write_text("!.mcp.json\nnode_modules/\n", encoding="utf-8")
            report = mc.build_report("no-interrupt", root)
            mc.ensure_gitignore_security(root, report)
            lines = gi.read_text(encoding="utf-8").splitlines()
            self.assertNotIn("!.mcp.json", lines)
            for line in mc.SECURITY_GITIGNORE_LINES:
                self.assertIn(line, lines)
            self.assertIn("node_modules/", lines)
            self.assertTrue(any(b["file"] == ".gitignore" for b in report["backups"]))
            self.assertTrue(any("SECURITY_UNIT_FRAMEWORK_WINS" in w for w in report["warnings"]))

    def test_idempotent_no_backup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gi = root / ".gitignore"
            gi.write_text(
                "\n".join(mc.SECURITY_GITIGNORE_LINES) + "\n", encoding="utf-8"
            )
            report = mc.build_report("no-interrupt", root)
            mc.ensure_gitignore_security(root, report)
            self.assertEqual(report["backups"], [])
            self.assertEqual(report["actions"][-1]["action"], "unchanged")

    def test_slash_prefixed_reverse_rule_is_removed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gi = root / ".gitignore"
            gi.write_text("!/.mcp.json\nnode_modules/\n", encoding="utf-8")
            report = mc.build_report("no-interrupt", root)
            mc.ensure_gitignore_security(root, report)
            lines = gi.read_text(encoding="utf-8").splitlines()
            self.assertNotIn("!/.mcp.json", lines)
            self.assertEqual(lines[-len(mc.SECURITY_GITIGNORE_LINES):], list(mc.SECURITY_GITIGNORE_LINES))
            self.assertTrue(any("SECURITY_UNIT_FRAMEWORK_WINS" in w for w in report["warnings"]))

    def test_allow_override_keeps_reverse_rule(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gi = root / ".gitignore"
            gi.write_text("!.mcp.json\n", encoding="utf-8")
            report = mc.build_report("no-interrupt", root)
            mc.ensure_gitignore_security(root, report, allow_override=True)
            lines = gi.read_text(encoding="utf-8").splitlines()
            self.assertIn("!.mcp.json", lines)
            self.assertGreater(lines.index("!.mcp.json"), lines.index(".mcp.json"))
            self.assertTrue(any("SECURITY_OVERRIDE_ALLOWED" in w for w in report["warnings"]))


if __name__ == "__main__":
    unittest.main()
