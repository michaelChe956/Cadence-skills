"""pre-check Task 1 的阶段报告契约测试。"""
import json
import os
import shutil
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


class TestSuperpowersGitPhase(unittest.TestCase):
    def test_non_git_source_fails_without_local_fallback(self):
        with isolated_fixture("superpowers-non-git") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            phase = phase_by_name(doc, "superpowers-git")
            self.assertEqual(phase["result"], "failed")
            self.assertIn("not-git", phase["action"])
            self.assertEqual(phase["error"], "not-git")
            self.assertEqual(fx.git_args.read_text(encoding="utf-8").count("rev-parse"), 1)

    def test_all_clone_candidates_fail_cleans_temp(self):
        with isolated_fixture("superpowers-source-missing") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            phase = phase_by_name(doc, "superpowers-git")
            self.assertEqual(phase["result"], "failed")
            self.assertIsInstance(phase["error"], str)
            for candidate in ("one", "two", "three"):
                self.assertIn(candidate, phase["error"])
            self.assertEqual(len(list(fx.tmp.glob("cadence-superpowers.*"))), 0)
            clone_calls = [line for line in fx.git_args.read_text(encoding="utf-8").splitlines() if "[clone]" in line]
            self.assertEqual(len(clone_calls), 3)

    def test_candidates_are_each_argv_element_under_zsh(self):
        if shutil.which("zsh") is None:
            self.skipTest("需要 zsh")
        with isolated_fixture("superpowers-zsh-multiple-candidates") as fx:
            proc, _doc = run_precheck_under_shell(fx, "zsh", "run", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            args = fx.git_args.read_text(encoding="utf-8")
            self.assertNotIn("one two", args)
            self.assertIn("[one]", args)
            self.assertIn("[two]", args)

    def test_single_candidate_timeout_is_structured(self):
        with isolated_fixture("superpowers-timeout") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            phase = phase_by_name(doc, "superpowers-git")
            self.assertEqual(phase["result"], "failed")
            self.assertIn("exit=124", phase["error"])
            self.assertEqual(phase["created"], 0)
            self.assertEqual(phase["updated"], 0)
            self.assertEqual(len(list(fx.tmp.glob("cadence-superpowers.*"))), 0)

    def test_candidate_limit_fails_without_truncation(self):
        with isolated_fixture("superpowers-source-missing") as fx:
            fx_env = fx.env()
            fx_env["CADENCE_TEST_GIT_CANDIDATES"] = "one two three four"
            proc = subprocess.run(
                ["bash", str(SCRIPT), "run", "--no-interrupt"],
                cwd=fx.project, env=fx_env, capture_output=True, text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            phase = phase_by_name(json.loads(proc.stdout), "superpowers-git")
            self.assertEqual(phase["error"], "too-many-candidates:3")
            self.assertEqual(fx.git_args.read_text(encoding="utf-8"), "")

    def test_origin_matching_second_candidate_is_not_rewritten(self):
        with isolated_fixture() as fx:
            second = fx.root / "second-candidate.git"
            shutil.copytree(fx.git_source, second)
            target = fx.home / ".agents" / "superpowers"
            subprocess.run(["git", "-C", str(target), "remote", "set-url", "origin", str(second)], check=True)
            env = fx.env()
            env["CADENCE_TEST_GIT_CANDIDATES"] = str(fx.git_source) + " " + str(second)
            proc = subprocess.run(
                ["bash", str(SCRIPT), "run", "--no-interrupt"],
                cwd=fx.project, env=env, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(json.loads(proc.stdout), "superpowers-git")
            self.assertEqual(phase["result"], "skipped")
            self.assertEqual(phase["action"], "fetch-pull-ff-only")
            git_calls = fx.git_args.read_text(encoding="utf-8").splitlines()
            self.assertFalse(any("[set-url]" in line for line in git_calls))
            self.assertEqual(phase["origin"], str(second))

    def test_phase_budget_timeout_arguments_are_nonincreasing(self):
        with isolated_fixture("superpowers-source-missing") as fx:
            proc, _doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            values = [int(line) for line in (fx.root / "timeouts").read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(values, sorted(values, reverse=True))
            self.assertTrue(values)
            self.assertLessEqual(max(values), 60)

    def test_delayed_candidates_consume_budget_and_stop_after_exhaustion(self):
        with isolated_fixture("superpowers-source-missing") as fx:
            env = fx.env()
            env["CADENCE_TEST_GIT_CANDIDATES"] = "one two three"
            env.pop("FAKE_GIT_FAIL", None)
            env["FAKE_GIT_BLOCK"] = "clone"
            env["FAKE_GIT_BLOCK_SECONDS"] = "0"
            env["FAKE_GIT_DELAY"] = "2"
            env["CADENCE_TEST_GIT_PHASE_BUDGET_S"] = "5"
            proc = subprocess.run(
                ["bash", str(SCRIPT), "run", "--no-interrupt"],
                cwd=fx.project, env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            phase = phase_by_name(json.loads(proc.stdout), "superpowers-git")
            self.assertIn("phase-timeout", phase["error"])
            values = [int(line) for line in (fx.root / "timeouts").read_text().splitlines() if line.strip()]
            self.assertTrue(values)
            self.assertEqual(values, sorted(values, reverse=True))
            self.assertLessEqual(len([line for line in fx.git_args.read_text().splitlines() if "[clone]" in line]), 3)

    def test_clone_success_uses_shallow_clone_and_reports_revision(self):
        with isolated_fixture() as fx:
            shutil.rmtree(fx.home / ".agents", ignore_errors=True)
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(doc, "superpowers-git")
            self.assertEqual(phase["result"], "success")
            self.assertEqual(phase["action"], "clone")
            self.assertEqual(phase["before_revision"], "")
            self.assertTrue(phase["after_revision"])
            self.assertEqual(phase["branch"], "main")
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(fx.home / ".agents/superpowers"), "rev-parse", "--is-shallow-repository"],
                    check=True, capture_output=True, text=True,
                ).stdout.strip(),
                "true",
            )

    def test_fetch_pull_revision_idempotence_and_metadata(self):
        with isolated_fixture() as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(doc, "superpowers-git")
            self.assertEqual(phase["result"], "skipped")
            self.assertEqual(phase["action"], "fetch-pull-ff-only")
            self.assertEqual(phase["before_revision"], phase["after_revision"])
            self.assertEqual(phase["branch"], "main")
            self.assertTrue(phase["origin"])


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
