"""pre-check Task 1 的阶段报告契约测试。"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers.fixture import (
    SCRIPT,
    isolated_fixture,
    normalize_snapshot_text,
    phase_by_name,
    run_precheck,
    run_precheck_under_shell,
)


class TestOpenSpecPhase(unittest.TestCase):
    def test_only_missing_pi_kimi_are_initialized(self):
        with isolated_fixture("openspec-partial") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            calls = fx.calls.read_text(encoding="utf-8").splitlines()
            self.assertIn("init --tools pi,kimi", calls)
            self.assertIn("update", calls)
            self.assertNotIn("init --tools claude,codex", calls)
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "success")
            self.assertEqual(len(list((fx.project / ".pi/skills").glob("openspec-*"))), 5)
            self.assertEqual(len(list((fx.project / ".pi/prompts").glob("opsx-*.md"))), 5)
            self.assertEqual(len(list((fx.project / ".kimi-code/skills").glob("openspec-*"))), 5)

    def test_wrong_pi_count_fails(self):
        with isolated_fixture("openspec-wrong-pi-count") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 1)
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "failed")
            self.assertGreaterEqual(phase["conflicts"], 1)

    def test_ready_projection_content_unchanged(self):
        with isolated_fixture("openspec-ready") as fx:
            before = {
                path: path.read_bytes()
                for path in (
                    fx.project / ".claude/commands/opsx/.sentinel",
                    fx.project / ".agents/skills/openspec-execute/SKILL.md",
                )
            }
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(
                {path: Path(path).read_bytes() for path in before}, before
            )
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "skipped")

    def test_ready_projection_skips_update(self):
        with isolated_fixture("openspec-ready") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn("update", fx.calls.read_text(encoding="utf-8").splitlines())
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["skipped"], 4)


class TestPhaseReport(unittest.TestCase):
    def test_check_has_five_timed_phases_and_legacy_steps(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "project"
            project.mkdir()
            report = Path(td) / "report.json"
            env = os.environ.copy()
            env["HOME"] = str(Path(td) / "home")
            env["PATH"] = str(Path(__file__).parent / "helpers/fake-bin") + os.pathsep + env["PATH"]
            with report.open("w", encoding="utf-8") as fh:
                proc = subprocess.run(
                    ["bash", str(SCRIPT), "check", "--mirror", "default"],
                    cwd=project,
                    env=env,
                    stdout=fh,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            self.assertIn(proc.returncode, (0, 1))
            doc = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(
                [p["phase"] for p in doc["phases"]],
                ["base-tools", "openspec", "superpowers-git", "superpowers-links", "verify"],
            )
            for phase in doc["phases"]:
                self.assertIn(phase["result"], {"success", "partial", "failed", "skipped"})
                self.assertIsInstance(phase["duration_ms"], int)
                for key in ("created", "updated", "skipped", "conflicts"):
                    self.assertIsInstance(phase[key], int)
            self.assertEqual(set(doc["steps"][0]), {"name", "status", "action", "version", "error"})
            self.assertIn("hints", doc)

    def test_snapshot_path_normalization_uses_stable_placeholders(self):
        """回归：Task 8 对照前替换随机隔离根前缀。"""
        text = (
            "link layer name readlink=/tmp/f/project/x "
            "resolved=/tmp/f/home/target\n"
            "git origin /tmp/f/remote.git\n"
        )
        normalized = normalize_snapshot_text(text, "/tmp/f")
        self.assertEqual(
            normalized,
            "link layer name readlink=<ISOLATION_ROOT>/project/x "
            "resolved=<ISOLATION_ROOT>/home/target\n"
            "git origin <ISOLATION_ROOT>/remote.git\n",
        )

    def test_run_precheck_under_shell_preserves_arguments_and_report(self):
        """回归：独立 bash shell 不重复展开项目根和脚本参数。"""
        with isolated_fixture() as fixture:
            proc, report = run_precheck_under_shell(
                fixture, "check", "--mirror", "default"
            )
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(
                [phase["phase"] for phase in report["phases"]],
                ["base-tools", "openspec", "superpowers-git", "superpowers-links", "verify"],
            )
