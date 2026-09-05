"""pre-check Task 1 的阶段报告契约测试。"""
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from helpers.fixture import (
    SCRIPT,
    isolated_fixture,
    normalize_snapshot_text,
    phase_by_name,
    run_precheck,
    run_precheck_under_shell,
    snapshot_tree,
)


NEGATIVE_CASES = {
    1: "base-tools-failure",
    2: "openspec-partial",
    3: "superpowers-source-missing",
    4: "superpowers-non-git",
    5: "superpowers-zsh-multiple-candidates",
    6: "links-correct",
    7: "links-non-symlink-conflict",
    8: "links-pi-missing-cadence",
    9: "playwright-not-requested",
    10: "report-cleanup",
}


class TestNegativeFixtureMatrix(unittest.TestCase):
    def test_all_design_negative_fixtures_are_registered(self):
        self.assertEqual(set(NEGATIVE_CASES), set(range(1, 11)))
        for number, name in NEGATIVE_CASES.items():
            with self.subTest(number=number):
                self.assertTrue((Path(__file__).parent / "fixtures" / name).exists(), name)

    def test_no_interrupt_failures_stop_downstream_writes(self):
        # #7 的 no-interrupt 语义是备份→创建→验证成功，按设计口径不属于失败快返矩阵。
        for number in (1, 3, 4, 5):
            with self.subTest(number=number), isolated_fixture(NEGATIVE_CASES[number]) as fx:
                before_project, before_home = snapshot_tree(fx.project), snapshot_tree(fx.home)
                proc, doc = run_precheck(fx, "run", "--no-interrupt")
                self.assertNotEqual(proc.returncode, 0)
                self.assertEqual(snapshot_tree(fx.project), before_project)
                self.assertEqual(snapshot_tree(fx.home), before_home)
                self.assertIn("failed", {p["result"] for p in doc["phases"]})


class TestSkillContract(unittest.TestCase):
    def setUp(self):
        self.text = (Path(__file__).parents[1] / "SKILL.md").read_text(encoding="utf-8")

    def test_has_three_step_contract(self):
        self.assertIn("步骤 1：定位 skill 目录", self.text)
        self.assertIn('bash "<PRE_CHECK_SH>" run', self.text)
        self.assertIn("读取 JSON 报告", self.text)
        self.assertIn("phases[]", self.text)

    def test_no_model_orchestration_commands_remain(self):
        for phrase in (
            # HEAD 旧版正文中的真实命令/流程措辞。
            "git clone --depth 1",
            "git clone",
            "git -C",
            "npm install",
            "npx ",
            "mkdir -p",
            "openspec init --tools",
            "openspec update",
            "python3 -c \"import json;print(' '.join",
            "增量运行",
            "快速参考",
            "digraph",
            "逐项软链",
            "模型先执行一次",
        ):
            self.assertNotIn(phrase, self.text)

        # 面向未来的补充防线：HEAD 旧版没有这些字面命令/格式。
        for phrase in ("ln -s", "ln -sf", "heredoc"):
            self.assertNotIn(phrase, self.text)

    def test_keeps_boundaries(self):
        for phrase in (
            "Playwright",
            "your_zhipu_api_key",
            "your_minimax_api_key",
            "不收集真实密钥",
            "unsupported",
        ):
            self.assertIn(phrase, self.text)


class TestFailureFastReturn(unittest.TestCase):
    def test_base_tool_failure_does_not_write_downstream(self):
        with isolated_fixture("base-tools-failure") as fx:
            failing_tool = Path(__file__).resolve().parent / "helpers" / "fake-failing-tool.sh"
            shutil.copy2(failing_tool, fx.bin / "npx")
            (fx.bin / "npx").chmod(0o755)
            before_project = snapshot_tree(fx.project)
            before_home = snapshot_tree(fx.home)
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(snapshot_tree(fx.project), before_project)
            self.assertEqual(snapshot_tree(fx.home), before_home)
            self.assertEqual(phase_by_name(doc, "base-tools")["result"], "failed")
            self.assertEqual([p["phase"] for p in doc["phases"]], ["base-tools"])
            self.assertEqual(doc["overall"], "failed")
            self.assertNotIn("init --tools", fx.calls.read_text(encoding="utf-8"))

    def test_playwright_not_requested_writes_nothing(self):
        with isolated_fixture("playwright-not-requested") as fx:
            _proc, _doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertFalse((fx.project / ".claude/rules/playwright.md").exists())
            self.assertFalse((fx.home / ".claude/skills/playwright-cli").exists())

    def test_verify_error_is_reported(self):
        with isolated_fixture("superpowers-source-missing") as fx:
            _proc, doc = run_precheck(fx, "run")
            verify = phase_by_name(doc, "verify")
            self.assertIsInstance(verify["error"], str)
            self.assertTrue(verify["error"])

    def test_report_cleanup_success_failure_timeout(self):
        helper = Path(__file__).resolve().parent / "helpers" / "report-cleanup.sh"
        for exit_code in (0, 1, 124):
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory() as td:
                report = Path(td) / "report.json"
                proc = subprocess.run(
                    ["bash", str(helper), str(report), "sh", "-c", "printf '{\\\"overall\\\":\\\"success\\\"}\\n'; exit $0", str(exit_code)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self.assertEqual(proc.returncode, exit_code)
                self.assertEqual(json.loads(proc.stdout)["overall"], "success")
                self.assertFalse(report.exists())

    def test_report_cleanup_removes_report_on_hup_int_term(self):
        helper = Path(__file__).resolve().parent / "helpers" / "report-cleanup.sh"
        for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=sig.name), tempfile.TemporaryDirectory() as td:
                report = Path(td) / "report.json"
                proc = subprocess.Popen(
                    [
                        "bash", str(helper), str(report), "bash", "-c",
                        "printf '{\\\"overall\\\":\\\"success\\\"}\\n'; sleep 30",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                pgid = os.getpgid(proc.pid)
                try:
                    deadline = time.monotonic() + 5
                    while not report.exists() and time.monotonic() < deadline:
                        self.assertIsNone(proc.poll(), "报告文件出现前 helper 已退出")
                        time.sleep(0.05)
                    self.assertTrue(report.exists(), "受包装命令未在时限内写入报告")
                    os.killpg(pgid, sig)
                    proc.wait(timeout=30)
                    self.assertFalse(report.exists())
                finally:
                    if proc.poll() is None:
                        os.killpg(pgid, signal.SIGKILL)
                        proc.wait(timeout=5)

    def test_run_precheck_removes_auto_report_on_hup_int_term(self):
        helper = Path(__file__).resolve().parent / "helpers" / "run-pre-check.sh"
        for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=sig.name), isolated_fixture("superpowers-timeout") as fx:
                proc = subprocess.Popen(
                    ["bash", str(helper), str(fx.project), "run", "--no-interrupt"],
                    cwd=fx.root,
                    env=fx.env(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                pgid = os.getpgid(proc.pid)
                report = None
                try:
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        reports = list(fx.tmp.glob("precheck-report.*.json"))
                        if reports and "[clone]" in fx.git_args.read_text(encoding="utf-8"):
                            report = reports[0]
                            break
                        self.assertIsNone(proc.poll(), "报告创建或 pre-check 阻塞前 wrapper 已退出")
                        time.sleep(0.05)
                    self.assertIsNotNone(report, "未观察到自动报告文件和阻塞的 pre-check 子进程")
                    os.killpg(pgid, sig)
                    proc.wait(timeout=30)
                    self.assertFalse(report.exists())
                finally:
                    if proc.poll() is None:
                        os.killpg(pgid, signal.SIGKILL)
                        proc.wait(timeout=5)

    def test_normal_mode_records_partial_and_continues(self):
        with isolated_fixture("base-tools-failure") as fx:
            failing_tool = Path(__file__).resolve().parent / "helpers" / "fake-failing-tool.sh"
            shutil.copy2(failing_tool, fx.bin / "npx")
            (fx.bin / "npx").chmod(0o755)
            proc, doc = run_precheck(fx, "run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            base = phase_by_name(doc, "base-tools")
            self.assertEqual(base["result"], "partial")
            self.assertIn("未检测到 npx", base["error"])
            self.assertEqual(doc["overall"], "partial")
            self.assertEqual(
                [phase["phase"] for phase in doc["phases"]],
                ["base-tools", "openspec", "superpowers-git", "superpowers-links", "verify"],
            )
            self.assertIn("init --tools", fx.calls.read_text(encoding="utf-8"))


class TestOpenSpecPhase(unittest.TestCase):
    def test_legacy_five_file_names_are_missing_and_initialized(self):
        with isolated_fixture("openspec-ready") as fx:
            for directory in (fx.project / ".pi/skills", fx.project / ".pi/prompts", fx.project / ".kimi-code/skills"):
                for path in list(directory.iterdir()):
                    if path.is_dir():
                        name = "write-plan" if path.name == "plan" else path.name.removeprefix("openspec-")
                        legacy = directory / name
                        shutil.rmtree(path)
                        legacy.write_text("legacy skill\n", encoding="utf-8")
                    else:
                        name = path.name.replace("opsx-plan", "write-plan")
                        path.rename(directory / name)
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("init --tools pi,kimi", fx.calls.read_text(encoding="utf-8").splitlines())
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "success")
            self.assertEqual(len(list((fx.project / ".pi/skills").glob("openspec-*"))), 5)
            self.assertEqual(len(list((fx.project / ".pi/prompts").glob("opsx-*.md"))), 5)
            self.assertEqual(len(list((fx.project / ".kimi-code/skills").glob("openspec-*"))), 5)

    def test_verify_does_not_allow_legacy_five_file_names(self):
        with isolated_fixture("openspec-ready") as fx:
            for directory in (fx.project / ".pi/skills", fx.project / ".pi/prompts", fx.project / ".kimi-code/skills"):
                for path in list(directory.iterdir()):
                    if path.is_dir():
                        name = "write-plan" if path.name == "plan" else path.name.removeprefix("openspec-")
                        legacy = directory / name
                        shutil.rmtree(path)
                        legacy.write_text("legacy skill\n", encoding="utf-8")
                    else:
                        name = path.name.replace("opsx-plan", "write-plan")
                        path.rename(directory / name)
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "failed")
            self.assertNotIn("verify", [phase["phase"] for phase in doc["phases"]])

    def test_missing_config_yaml_prints_rule_config_hint(self):
        with isolated_fixture("openspec-ready") as fx:
            proc, _doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("openspec/config.yaml 缺失", proc.stderr)
            self.assertIn("rule-config 步骤 11 创建", proc.stderr)

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

    def test_ready_projection_updates_without_init(self):
        with isolated_fixture("openspec-ready") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            calls = fx.calls.read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls.count("update"), 1)
            self.assertFalse(any(call.startswith("init") for call in calls))
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "skipped")
            self.assertEqual(phase["action"], "update-verify")
            self.assertEqual(phase["updated"], 0)
            self.assertEqual(phase["skipped"], 4)

    def test_ready_projection_check_mode_stays_readonly(self):
        with isolated_fixture("openspec-ready") as fx:
            proc, doc = run_precheck(fx, "check")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            calls = fx.calls.read_text(encoding="utf-8").splitlines()
            self.assertNotIn("update", calls)
            self.assertFalse(any(call.startswith("init") for call in calls))
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["action"], "verify-ready")
            self.assertEqual(phase["result"], "skipped")
            self.assertEqual(phase["skipped"], 4)

    def test_ready_projection_update_failure_bridges_phase_error(self):
        with isolated_fixture("openspec-ready") as fx:
            env = fx.env()
            env["FAKE_OPENSPEC_UPDATE_FAIL"] = "1"
            proc = subprocess.run(
                ["bash", str(SCRIPT), "run", "--no-interrupt"],
                cwd=fx.project,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            doc = json.loads(proc.stdout)
            self.assertEqual(proc.returncode, 1)
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "failed")
            self.assertGreaterEqual(phase["conflicts"], 1)
            self.assertIn("openspec update 失败", phase["error"])


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


class TestSuperpowersLinks(unittest.TestCase):
    def test_correct_links_are_skipped_and_non_superpowers_survives(self):
        with isolated_fixture("links-correct") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(doc, "superpowers-links")
            self.assertEqual(phase["created"], 0)
            self.assertEqual(phase["updated"], 0)
            self.assertEqual(phase["conflicts"], 0)
            self.assertEqual(phase["result"], "skipped")
            self.assertEqual((fx.home / ".agents/skills/third-party/KEEP").read_text(), "user\n")

    def test_direct_and_layered_topologies_are_both_skipped(self):
        for fixture_name in ("links-correct-direct", "links-correct-layered"):
            with self.subTest(fixture=fixture_name), isolated_fixture(fixture_name) as fx:
                proc, doc = run_precheck(fx, "run", "--no-interrupt")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                phase = phase_by_name(doc, "superpowers-links")
                self.assertEqual(phase["result"], "skipped")
                self.assertEqual(phase["created"], 0)
                self.assertEqual(phase["updated"], 0)
                self.assertEqual(phase["conflicts"], 0)

    def test_correct_links_all_skipped_and_report_is_dynamic(self):
        with isolated_fixture("links-correct-direct") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(doc, "superpowers-links")
            self.assertEqual(phase["source_entries"], 14)
            self.assertEqual(phase["skipped"], 56)
            self.assertEqual(phase["created"], 0)
            self.assertEqual(phase["updated"], 0)
            self.assertEqual(phase["conflicts"], 0)
            self.assertEqual(len(phase["layers"]), 4)
            for layer in phase["layers"]:
                self.assertEqual(layer["source_entries"], 14)
                self.assertEqual(layer["superpowers_links"], 14)
                self.assertEqual(layer["correct"], 14)
                self.assertEqual(layer["stale"], 0)
                self.assertEqual(layer["broken"], 0)
                self.assertEqual(layer["conflicts"], 0)

    def test_non_symlink_conflict_normal_warns_and_preserves(self):
        with isolated_fixture("links-non-symlink-conflict") as fx:
            target = fx.home / ".agents/skills/skill-01"
            before = target.read_text(encoding="utf-8")
            proc, doc = run_precheck(fx, "run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(doc, "superpowers-links")
            self.assertGreaterEqual(phase["conflicts"], 1)
            self.assertGreaterEqual(phase["skipped"], 1)
            self.assertEqual(target.read_text(encoding="utf-8"), before)
            self.assertFalse(target.is_symlink())
            self.assertFalse(list(target.parent.glob("skill-01.cadence-backup-*")))

    def test_non_symlink_conflict_no_interrupt_backups_then_verifies(self):
        with isolated_fixture("links-non-symlink-conflict") as fx:
            target = fx.home / ".agents/skills/skill-01"
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(doc, "superpowers-links")
            self.assertGreaterEqual(phase["conflicts"], 1)
            self.assertTrue(target.is_symlink())
            self.assertEqual(target.resolve(), (fx.home / ".agents/superpowers/skills/skill-01").resolve())
            backups = list(target.parent.glob("skill-01.cadence-backup-*"))
            self.assertEqual(len(backups), 1)
            self.assertRegex(backups[0].name, r"^skill-01\.cadence-backup-[0-9]{14}(-1)?$")
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "sentinel\n")

    def test_no_interrupt_link_failure_fails_phase(self):
        with isolated_fixture("links-non-symlink-conflict") as fx:
            fake_ln = fx.bin / "ln"
            fake_ln.write_text(
                "#!/usr/bin/env bash\n"
                "if [ \"${1:-}\" = \"-s\" ]; then exit 42; fi\n"
                "exec \"${REAL_LN:-/usr/bin/ln}\" \"$@\"\n",
                encoding="utf-8",
            )
            fake_ln.chmod(0o755)
            env = fx.env()
            env["REAL_LN"] = "/usr/bin/ln"
            proc = subprocess.run(
                ["bash", str(SCRIPT), "run", "--no-interrupt"],
                cwd=fx.project,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            doc = json.loads(proc.stdout)
            phase = phase_by_name(doc, "superpowers-links")
            self.assertEqual(phase["result"], "failed")
            self.assertTrue(phase["error"])
            backups = list((fx.home / ".agents/skills").glob("skill-01.cadence-backup-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "sentinel\n")
            self.assertFalse((fx.home / ".agents/skills/skill-01").exists())

    def test_broken_superpowers_link_is_rebuilt_without_backup(self):
        with isolated_fixture("links-correct-direct") as fx:
            target = fx.home / ".agents/skills/skill-01"
            target.unlink()
            target.symlink_to(fx.home / ".agents/superpowers/skills/missing-skill")
            proc, doc = run_precheck(fx, "run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(doc, "superpowers-links")
            self.assertEqual(phase["conflicts"], 0)
            self.assertEqual(phase["updated"], 1)
            self.assertTrue(target.is_symlink())
            self.assertEqual(target.resolve(), (fx.home / ".agents/superpowers/skills/skill-01").resolve())
            self.assertFalse(list(target.parent.glob("skill-01.cadence-backup-*")))

    def test_broken_superpowers_link_no_interrupt_is_rebuilt_without_backup(self):
        with isolated_fixture("links-correct-direct") as fx:
            target = fx.home / ".agents/skills/skill-01"
            target.unlink()
            target.symlink_to(fx.home / ".agents/superpowers/skills/missing-skill")
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(doc, "superpowers-links")
            self.assertEqual(phase["conflicts"], 0)
            self.assertEqual(phase["updated"], 1)
            self.assertTrue(target.is_symlink())
            self.assertEqual(target.resolve(), (fx.home / ".agents/superpowers/skills/skill-01").resolve())
            self.assertFalse(list(target.parent.glob("skill-01.cadence-backup-*")))

    def test_pi_missing_cadence_entry_does_not_fail_superpowers(self):
        with isolated_fixture("links-pi-missing-cadence") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(doc, "superpowers-links")
            self.assertEqual(phase["result"], "skipped")
            self.assertEqual(phase["created"], 0)
            self.assertEqual(phase["updated"], 0)
            self.assertEqual(phase["conflicts"], 0)
            self.assertTrue((fx.home / ".pi/agent/skills/skill-14").is_symlink())


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
