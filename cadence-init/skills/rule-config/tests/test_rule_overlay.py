"""`.claude/rules` overlay 抽取测试（TDD）。"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "rule-config.py"
spec = importlib.util.spec_from_file_location("rule_config_overlay", SCRIPT)
rc = importlib.util.module_from_spec(spec)
sys.modules["rule_config_overlay"] = rc
spec.loader.exec_module(rc)

TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "references" / "rules"


class TestRuleOverlay(unittest.TestCase):
    def _run(self, root: Path, report: dict):
        plan = {
            "templates": {"rules_root": str(TEMPLATE_ROOT)},
            "steps": {
                rc.STEP_RULES_FILES: {
                    "assets": [{
                        "path": ".claude/rules/language.md",
                        "template_source": "language.md",
                        "action": "replace",
                        "conflict": "drift",
                        "is_l1": False,
                    }],
                },
            },
        }
        rc.step_s3_rules_files(
            root,
            rc.Intents(
                no_interrupt=True, project_type=None, ignore_cadence=False,
                enable_playwright=False, enable_codegraph=False, decisions=None,
            ),
            plan,
            report,
        )

    def test_user_edit_extracted_and_framework_file_purified(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / ".claude" / "rules" / "language.md"
            target.parent.mkdir(parents=True)
            template = (TEMPLATE_ROOT / "language.md").read_text(encoding="utf-8")
            target.write_text(template + "\nUSER-EXTRA-LINE\n", encoding="utf-8")
            report = {}
            self._run(root, report)
            self.assertEqual(target.read_text(encoding="utf-8"), template)
            overlay = root / ".claude" / "rules" / "user-language.md"
            self.assertTrue(overlay.exists())
            self.assertIn("USER-EXTRA-LINE", overlay.read_text(encoding="utf-8"))
            self.assertTrue(
                (root / "cadence" / "framework-state" / "manifest.json").exists()
            )

    def test_overlay_is_idempotent_and_keeps_manual_area(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / ".claude" / "rules" / "language.md"
            target.parent.mkdir(parents=True)
            template = (TEMPLATE_ROOT / "language.md").read_text(encoding="utf-8")
            target.write_text(template + "\nUSER-EXTRA-LINE\n", encoding="utf-8")
            overlay = root / ".claude" / "rules" / "user-language.md"
            overlay.write_text(
                "<!-- cadence-overlay:extracted:start base=old -->\nold\n"
                "<!-- cadence-overlay:extracted:end -->\n\nMANUAL-AREA\n",
                encoding="utf-8",
            )
            report = {}
            self._run(root, report)
            first = overlay.read_text(encoding="utf-8")
            self.assertIn("USER-EXTRA-LINE", first)
            self.assertIn("MANUAL-AREA", first)
            self.assertEqual(first.count("cadence-overlay:extracted:start"), 1)
            self._run(root, report)
            self.assertEqual(overlay.read_text(encoding="utf-8"), first)
            self.assertEqual(
                overlay.read_text(encoding="utf-8").count(
                    "cadence-overlay:extracted:start"
                ),
                1,
            )


    def test_unreadable_overlay_is_archived_before_rebuild(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / ".claude" / "rules" / "language.md"
            target.parent.mkdir(parents=True)
            template = (TEMPLATE_ROOT / "language.md").read_text(encoding="utf-8")
            target.write_text(template + "\nUSER-EXTRA-LINE\n", encoding="utf-8")
            overlay = root / ".claude" / "rules" / "user-language.md"
            overlay.write_bytes("手动中文覆盖".encode("gbk"))
            report = {}
            self._run(root, report)
            self.assertTrue(any(
                "OVERLAY_UNREADABLE_ARCHIVED" == w.get("code")
                for w in report.get("warnings", [])
            ))
            backups = list((root / "cadence" / "legacy").glob(
                "*/.claude/rules/user-language.md"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), "手动中文覆盖".encode("gbk"))


    def test_l1_file_goes_through_overlay(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / ".claude" / "rules" / "openspec-superpowers-workflow.md"
            target.parent.mkdir(parents=True)
            template = (TEMPLATE_ROOT / "openspec-superpowers-workflow.md").read_text(encoding="utf-8")
            target.write_text(template + "\nUSER-L1-LINE\n", encoding="utf-8")
            plan = {
                "templates": {"rules_root": str(TEMPLATE_ROOT)},
                "steps": {
                    rc.STEP_RULES_FILES: {
                        "assets": [{
                            "path": ".claude/rules/openspec-superpowers-workflow.md",
                            "template_source": "openspec-superpowers-workflow.md",
                            "action": "replace",
                            "conflict": "replace",
                            "is_l1": True,
                        }],
                    },
                },
            }
            report = {}
            rc.step_s3_rules_files(
                root,
                rc.Intents(
                    no_interrupt=True, project_type=None, ignore_cadence=False,
                    enable_playwright=False, enable_codegraph=False, decisions=None,
                ),
                plan, report,
            )
            self.assertEqual(target.read_text(encoding="utf-8"), template)
            overlay = root / ".claude" / "rules" / "user-openspec-superpowers-workflow.md"
            self.assertTrue(overlay.exists())
            self.assertIn("USER-L1-LINE", overlay.read_text(encoding="utf-8"))

    def test_second_edit_accumulates_previous_extraction(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / ".claude" / "rules" / "language.md"
            target.parent.mkdir(parents=True)
            template = (TEMPLATE_ROOT / "language.md").read_text(encoding="utf-8")
            target.write_text(template + "\nFIRST-USER-LINE\n", encoding="utf-8")
            report = {}
            self._run(root, report)
            overlay = root / ".claude" / "rules" / "user-language.md"
            self.assertIn("FIRST-USER-LINE", overlay.read_text(encoding="utf-8"))
            target.write_text(template + "\nSECOND-USER-LINE\n", encoding="utf-8")
            self._run(root, report)
            text = overlay.read_text(encoding="utf-8")
            self.assertIn("FIRST-USER-LINE", text)
            self.assertIn("SECOND-USER-LINE", text)
            self.assertEqual(text.count("cadence-overlay:extracted:start"), 1)


if __name__ == "__main__":
    unittest.main()
