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
                    ["bash", str(helper), str(report), "sh", "-c", "printf '%s\\n' '{\"overall\":\"success\"}'; exit $0", str(exit_code)],
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
                        "printf '%s\\n' '{\"overall\":\"success\"}'; sleep 30",
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
            self.assertEqual(len(list((fx.project / ".pi/skills").glob("openspec-*"))), 6)
            self.assertEqual(len(list((fx.project / ".pi/prompts").glob("opsx-*.md"))), 6)
            self.assertEqual(len(list((fx.project / ".kimi-code/skills").glob("openspec-*"))), 6)

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
            self.assertEqual(len(list((fx.project / ".pi/skills").glob("openspec-*"))), 6)
            self.assertEqual(len(list((fx.project / ".pi/prompts").glob("opsx-*.md"))), 6)
            self.assertEqual(len(list((fx.project / ".kimi-code/skills").glob("openspec-*"))), 6)

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

    SHARED_CORE_NAMES = (
        "apply-change", "archive-change", "explore", "propose", "sync-specs", "update-change",
    )

    def _remove_legacy_layout(self, project):
        for relative in (".pi", ".kimi-code", ".claude/commands/opsx"):
            shutil.rmtree(project / relative, ignore_errors=True)

    def _write_shared_layout(self, project, marker_text, *, claude_links=True):
        skills = project / ".agents" / "skills"
        for name in self.SHARED_CORE_NAMES:
            skill = skills / ("openspec-" + name)
            skill.mkdir(parents=True, exist_ok=True)
            (skill / "SKILL.md").write_text("shared %s\n" % name, encoding="utf-8")
        if marker_text is not None:
            (skills / ".openspec-target").write_text(marker_text, encoding="utf-8")
        if claude_links:
            layer = project / ".claude" / "skills"
            layer.mkdir(parents=True, exist_ok=True)
            for name in self.SHARED_CORE_NAMES:
                link = layer / ("openspec-" + name)
                if link.is_symlink() or link.exists():
                    link.unlink()
                link.symlink_to(Path("../../.agents/skills") / ("openspec-" + name))

    @staticmethod
    def _run_with_shared_fake(fx, *args):
        env = fx.env()
        env["FAKE_OPENSPEC_SHARED_LAYOUT"] = "1"
        proc = subprocess.run(
            ["bash", str(SCRIPT), *args],
            cwd=fx.project,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError:
            report = {}
        return proc, report

    @staticmethod
    def _prepare_superpowers_check_links(fx):
        # check 不补链接；为正例提供有效的独立前置，避免后续 verify 掩盖投影结果。
        source = fx.home / ".agents/superpowers/skills"
        (source / "README.md").unlink()
        skill = source / "fixture-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("# fixture skill\n", encoding="utf-8")
        for relative in (".agents/skills", ".codex/skills", ".claude/skills", ".pi/agent/skills"):
            layer = fx.home / relative
            layer.mkdir(parents=True, exist_ok=True)
            (layer / "fixture-skill").symlink_to(skill)

    def test_modern_shared_layout_check_mode_is_readonly_ready(self):
        with isolated_fixture("openspec-ready") as fx:
            self._prepare_superpowers_check_links(fx)
            self._remove_legacy_layout(fx.project)
            # 上游 2.x marker 每行首 token 是工具 ID，可追加 own-files 等列。
            self._write_shared_layout(
                fx.project, "claude\ncodex\npi own-files\nkimi own-files\n"
            )
            self.assertFalse((fx.project / ".pi").exists())
            self.assertFalse((fx.project / ".kimi-code").exists())
            self.assertFalse((fx.project / ".claude/commands/opsx").exists())
            before_agents = snapshot_tree(fx.project / ".agents")
            before_claude = snapshot_tree(fx.project / ".claude")
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["action"], "verify-ready")
            self.assertEqual(phase["result"], "skipped")
            self.assertEqual(snapshot_tree(fx.project / ".agents"), before_agents)
            self.assertEqual(snapshot_tree(fx.project / ".claude"), before_claude)
            calls = fx.calls.read_text(encoding="utf-8").splitlines()
            self.assertFalse(
                [call for call in calls if call == "update" or call.startswith("init")]
            )

    def test_modern_shared_layout_run_updates_without_init(self):
        with isolated_fixture("openspec-ready") as fx:
            self._remove_legacy_layout(fx.project)
            self._write_shared_layout(fx.project, "pi\nkimi\n")
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            calls = fx.calls.read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls.count("update"), 1)
            self.assertFalse([call for call in calls if call.startswith("init")])
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["action"], "update-verify")
            self.assertEqual(phase["result"], "skipped")
            self.assertFalse((fx.project / ".pi").exists())
            self.assertFalse((fx.project / ".kimi-code").exists())

    def test_shared_marker_client_missing_core_skill_fails_even_legacy_present(self):
        # 旧 6+6 布局完整，但 marker 列出 pi → 只认 shared，缺失即失败，绝不回退。
        with isolated_fixture("openspec-ready") as fx:
            self._write_shared_layout(fx.project, "codex\npi\n")
            (fx.project / ".agents/skills/openspec-explore/SKILL.md").unlink()
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "failed")
            self.assertEqual(
                [item["phase"] for item in doc["phases"]],
                ["base-tools", "openspec"],
            )

    def test_shared_marker_kimi_missing_core_skill_fails_even_legacy_present(self):
        with isolated_fixture("openspec-ready") as fx:
            self._write_shared_layout(fx.project, "codex\nkimi\n")
            (fx.project / ".agents/skills/openspec-sync-specs/SKILL.md").unlink()
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "failed")

    def test_shared_core_empty_skill_fails(self):
        with isolated_fixture("openspec-ready") as fx:
            self._remove_legacy_layout(fx.project)
            self._write_shared_layout(fx.project, "pi\nkimi\n")
            (fx.project / ".agents/skills/openspec-propose/SKILL.md").write_text(
                "", encoding="utf-8"
            )
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "failed")

    def test_marker_listing_kimi_uses_shared_while_pi_uses_complete_legacy(self):
        with isolated_fixture("openspec-ready") as fx:
            self._prepare_superpowers_check_links(fx)
            self._write_shared_layout(fx.project, "codex\nkimi\n")
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "skipped")

    def test_marker_listing_pi_uses_shared_while_kimi_uses_complete_legacy(self):
        with isolated_fixture("openspec-ready") as fx:
            self._prepare_superpowers_check_links(fx)
            self._write_shared_layout(fx.project, "pi\n")
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "skipped")

    def test_unlisted_client_with_incomplete_legacy_fails(self):
        with isolated_fixture("openspec-ready") as fx:
            self._write_shared_layout(fx.project, "pi\n")
            shutil.rmtree(fx.project / ".kimi-code/skills/openspec-verify")
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "failed")

    def test_empty_marker_allows_complete_legacy_layout(self):
        with isolated_fixture("openspec-ready") as fx:
            self._prepare_superpowers_check_links(fx)
            (fx.project / ".agents/skills/.openspec-target").write_text(
                "", encoding="utf-8"
            )
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "skipped")

    def test_codex_only_marker_allows_complete_legacy_layout(self):
        with isolated_fixture("openspec-ready") as fx:
            self._prepare_superpowers_check_links(fx)
            (fx.project / ".agents/skills/.openspec-target").write_text(
                "codex\n", encoding="utf-8"
            )
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "skipped")

    def test_shared_core_without_marker_requires_complete_legacy(self):
        with isolated_fixture("openspec-ready") as fx:
            self._remove_legacy_layout(fx.project)
            self._write_shared_layout(fx.project, None)
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "failed")

    def test_broken_marker_symlink_is_invalid_and_fails_without_fallback(self):
        with isolated_fixture("openspec-ready") as fx:
            marker = fx.project / ".agents/skills/.openspec-target"
            marker.symlink_to("missing-target")
            proc, doc = run_precheck(fx, "check", "--no-interrupt")
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "failed")

    def test_shared_init_completes_layout_without_legacy_projection(self):
        with isolated_fixture("openspec-partial") as fx:
            proc, doc = self._run_with_shared_fake(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            calls = fx.calls.read_text(encoding="utf-8").splitlines()
            self.assertIn("init --tools pi,kimi", calls)
            self.assertEqual(calls.count("update"), 1)
            marker = (fx.project / ".agents/skills/.openspec-target").read_text(
                encoding="utf-8"
            )
            self.assertEqual(sorted(marker.split()), ["kimi", "pi"])
            for name in self.SHARED_CORE_NAMES:
                self.assertTrue(
                    (fx.project / ".agents/skills" / ("openspec-" + name) / "SKILL.md").is_file(),
                    name,
                )
            self.assertFalse((fx.project / ".pi").exists())
            self.assertFalse((fx.project / ".kimi-code").exists())
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "success")

    def test_shared_init_with_claude_creates_relative_skill_links(self):
        with isolated_fixture("openspec-partial") as fx:
            shutil.rmtree(fx.project / ".claude")
            shutil.rmtree(fx.project / ".agents")
            proc, doc = self._run_with_shared_fake(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            calls = fx.calls.read_text(encoding="utf-8").splitlines()
            self.assertIn("init --tools claude,codex,pi,kimi", calls)
            link = fx.project / ".claude/skills/openspec-propose"
            self.assertTrue(link.is_symlink())
            self.assertEqual(
                os.readlink(link), "../../.agents/skills/openspec-propose"
            )
            self.assertFalse((fx.project / ".claude/commands/opsx").exists())
            self.assertFalse((fx.project / ".pi").exists())
            self.assertFalse((fx.project / ".kimi-code").exists())
            self.assertEqual(phase_by_name(doc, "openspec")["result"], "success")

    @staticmethod
    def _run_with_scope_aware_fake(fx, *args, **extra_env):
        env = fx.env()
        env["FAKE_OPENSPEC_SHARED_LAYOUT"] = "1"
        env["FAKE_OPENSPEC_VERSION"] = "2.1.0"
        env.update(extra_env)
        proc = subprocess.run(
            ["bash", str(SCRIPT), *args],
            cwd=fx.project,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError:
            report = {}
        return proc, report

    def test_openspec_2_1_init_pins_project_scope(self):
        # 2.1.0 默认把技能装进 $HOME，项目根只剩骨架；pre-check 必须显式钉住项目作用域。
        with isolated_fixture() as fx:
            proc, doc = self._run_with_scope_aware_fake(fx, "run", "--no-interrupt")
            calls = fx.calls.read_text(encoding="utf-8").splitlines()
            self.assertIn("init --tools claude,codex,pi,kimi --scope project", calls)
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "success", phase.get("error"))
            self.assertTrue(
                (fx.project / ".agents/skills/openspec-apply-change/SKILL.md").is_file()
            )
            self.assertEqual(list((fx.home / ".agents/skills").glob("openspec-*")), [])
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_openspec_2_1_failure_message_names_scope_cause(self):
        with isolated_fixture() as fx:
            proc, doc = self._run_with_scope_aware_fake(
                fx, "run", "--no-interrupt", FAKE_OPENSPEC_NOOP_INIT="1"
            )
            self.assertNotEqual(proc.returncode, 0)
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "failed")
            self.assertTrue(phase["error"].startswith("OpenSpec 客户端投影数量或路径复核失败"))
            self.assertIn("--scope project", phase["error"])

    def test_cn_mirror_falls_back_across_github_proxies_for_openspec_2_1(self):
        # 2.1.0+ 的 init 要克隆 GitHub；大陆网络直连不通，--mirror cn 按序走加速代理。
        with isolated_fixture() as fx:
            envlog = fx.root / "openspec-env"
            proc, doc = self._run_with_scope_aware_fake(
                fx, "run", "--mirror", "cn", "--no-interrupt",
                FAKE_OPENSPEC_ENVLOG=str(envlog),
                FAKE_OPENSPEC_UNREACHABLE="fail",
                FAKE_OPENSPEC_GITHUB_OK_VIA="gh-proxy.com",
            )
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "success", phase.get("error"))
            inits = [l for l in envlog.read_text(encoding="utf-8").splitlines() if l.startswith("init ")]
            self.assertEqual(len(inits), 2, inits)
            self.assertIn("KEY_0=url.https://ghfast.top/https://github.com/.insteadOf", inits[0])
            self.assertIn("KEY_0=url.https://gh-proxy.com/https://github.com/.insteadOf", inits[1])
            self.assertIn("VALUE_0=https://github.com/", inits[1])

    def test_openspec_2_1_hang_is_bounded_and_reported(self):
        # CLI 自身没有网络超时：GitHub 不通时脚本必须在超时后明确失败，而不是无限挂起。
        with isolated_fixture() as fx:
            (fx.bin / "timeout").unlink()  # 使用真实 timeout 以验证超时确实生效
            started = time.monotonic()
            proc, doc = self._run_with_scope_aware_fake(
                fx, "run", "--no-interrupt",
                FAKE_OPENSPEC_UNREACHABLE="hang", CADENCE_OPENSPEC_TIMEOUT_S="2",
            )
            self.assertLess(time.monotonic() - started, 30)
            self.assertNotEqual(proc.returncode, 0)
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "failed")
            self.assertIn("超时", phase["error"])
            self.assertIn("GitHub", phase["error"])

    def test_github_proxy_rewrite_only_for_cn_mirror_and_openspec_2_1(self):
        for mirror_args, version in ((("--mirror", "cn"), "2.0.0"), ((), "2.1.0")):
            with self.subTest(mirror=mirror_args, version=version), isolated_fixture() as fx:
                envlog = fx.root / "openspec-env"
                proc, doc = self._run_with_scope_aware_fake(
                    fx, "run", *mirror_args, "--no-interrupt",
                    FAKE_OPENSPEC_ENVLOG=str(envlog), FAKE_OPENSPEC_VERSION=version,
                )
                self.assertEqual(phase_by_name(doc, "openspec")["result"], "success")
                for line in envlog.read_text(encoding="utf-8").splitlines():
                    self.assertIn("GIT_CONFIG_COUNT= KEY_0= VALUE_0=", line)


class TestUpgradePiMcpAdapter(unittest.TestCase):
    ADAPTER = ".pi/agent/npm/node_modules/pi-mcp-adapter"

    def _run(self, fx, version, latest, *args, **extra_env):
        adapter = fx.home / self.ADAPTER
        adapter.mkdir(parents=True)
        (adapter / "package.json").write_text(
            '{\n  "name": "pi-mcp-adapter",\n  "version": "%s"\n}\n' % version, encoding="utf-8"
        )
        self.pi_calls = fx.root / "pi-calls"
        env = fx.env()
        env.update(
            FAKE_PI_ADAPTER_DIR=str(adapter),
            FAKE_PI_CALLS=str(self.pi_calls),
            FAKE_NPM_LATEST_pi_mcp_adapter=latest,
        )
        env.update(extra_env)
        proc = subprocess.run(
            ["bash", str(SCRIPT), "run", "--upgrade", "--no-interrupt", *args],
            cwd=fx.project, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        doc = json.loads(proc.stdout)
        step = [s for s in doc["steps"] if s["name"] == "pi-mcp-adapter"]
        self.assertEqual(len(step), 1, doc["steps"])
        return proc, doc, step[0]

    def _pi_calls(self):
        return self.pi_calls.read_text(encoding="utf-8").splitlines() if self.pi_calls.exists() else []

    def test_stale_adapter_is_updated_through_mirror_registry(self):
        with isolated_fixture() as fx:
            proc, doc, step = self._run(
                fx, "5.4.0", "7.0.1", "--mirror", "cn", FAKE_PI_UPDATE_TO="7.0.1"
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(step["status"], "upgraded")
            self.assertEqual(step["version"], "7.0.1")
            self.assertIn("from=5.4.0 to=7.0.1", step["error"])
            self.assertEqual(
                self._pi_calls(),
                ["update npm:pi-mcp-adapter --no-approve | npm_config_registry=https://registry.npmmirror.com"],
            )

    def test_update_that_does_not_reach_latest_is_failure(self):
        with isolated_fixture() as fx:
            proc, doc, step = self._run(fx, "5.4.0", "7.0.1")
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(step["status"], "failed")
            self.assertEqual(step["action"], "upgrade-failed")
            self.assertEqual(doc["overall"], "failed")

    def test_current_adapter_is_not_touched(self):
        with isolated_fixture() as fx:
            proc, doc, step = self._run(fx, "7.0.1", "7.0.1")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(step["status"], "ready")
            self.assertEqual(self._pi_calls(), [])

    def test_version_pinned_adapter_is_left_alone(self):
        with isolated_fixture() as fx:
            proc, doc, step = self._run(fx, "5.4.0", "7.0.1", FAKE_PI_PINNED="1")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(step["status"], "ready")
            self.assertEqual(self._pi_calls(), [])


class TestMirrorAwareExternalFetches(unittest.TestCase):
    """pi install 与 codegraph npm shim 的回退下载也必须走当前镜像，不能偷偷直连。"""

    @staticmethod
    def _run(fx, *args, **extra_env):
        env = fx.env()
        env.update(extra_env)
        proc = subprocess.run(
            ["bash", str(SCRIPT), "run", "--no-interrupt", *args],
            cwd=fx.project, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        return proc, json.loads(proc.stdout)

    @staticmethod
    def _step(doc, name):
        steps = [s for s in doc["steps"] if s["name"] == name]
        assert len(steps) == 1, doc["steps"]
        return steps[0]

    def test_pi_install_uses_mirror_npm_registry(self):
        with isolated_fixture() as fx:
            calls = fx.root / "pi-calls"
            proc, doc = self._run(
                fx, "--mirror", "cn",
                FAKE_PI_CALLS=str(calls), FAKE_PI_INSTALL_FLAG=str(fx.root / "pi-installed"),
            )
            self.assertEqual(self._step(doc, "pi-mcp-adapter")["status"], "installed")
            self.assertEqual(
                calls.read_text(encoding="utf-8").splitlines(),
                ["install npm:pi-mcp-adapter | npm_config_registry=https://registry.npmmirror.com"],
            )

    def test_codegraph_cn_mirror_falls_back_across_github_proxies(self):
        # npmmirror 缺平台子包时 npm shim 会回退到 GitHub Releases；cn 下必须经加速代理。
        with isolated_fixture() as fx:
            envlog = fx.root / "codegraph-env"
            proc, doc = self._run(
                fx, "--mirror", "cn",
                FAKE_CODEGRAPH_ENVLOG=str(envlog), FAKE_CODEGRAPH_OK_VIA="gh-proxy.com",
            )
            step = self._step(doc, "codegraph")
            self.assertEqual(step["status"], "ready", step)
            self.assertEqual(
                envlog.read_text(encoding="utf-8").splitlines(),
                [
                    "CODEGRAPH_DOWNLOAD_BASE=https://ghfast.top/https://github.com/colbymchenry/codegraph/releases/download",
                    "CODEGRAPH_DOWNLOAD_BASE=https://gh-proxy.com/https://github.com/colbymchenry/codegraph/releases/download",
                ],
            )

    def test_codegraph_download_base_untouched_without_proxies_or_when_user_set(self):
        cases = (
            ((), {}, ""),
            (("--mirror", "cn"), {"CODEGRAPH_DOWNLOAD_BASE": "https://example.invalid/dl"}, "https://example.invalid/dl"),
        )
        for args, extra, expected in cases:
            with self.subTest(args=args), isolated_fixture() as fx:
                envlog = fx.root / "codegraph-env"
                proc, doc = self._run(fx, *args, FAKE_CODEGRAPH_ENVLOG=str(envlog), **extra)
                self.assertEqual(self._step(doc, "codegraph")["status"], "ready")
                self.assertEqual(
                    envlog.read_text(encoding="utf-8").splitlines(),
                    ["CODEGRAPH_DOWNLOAD_BASE=" + expected],
                )

    def test_openspec_network_budget_bounds_total_attempts(self):
        # 阶段总预算耗尽后必须停止重试并失败，不得无限累积尝试（仓库性能熔断 240 秒上限）。
        with isolated_fixture() as fx:
            (fx.bin / "timeout").unlink()  # 使用真实 timeout 才能真正触发超时
            envlog = fx.root / "openspec-env"
            proc, doc = self._run(
                fx, "--mirror", "cn", "--no-interrupt",
                FAKE_OPENSPEC_ENVLOG=str(envlog),
                FAKE_OPENSPEC_SHARED_LAYOUT="1", FAKE_OPENSPEC_VERSION="2.1.0",
                FAKE_OPENSPEC_UNREACHABLE="hang",
                FAKE_OPENSPEC_GITHUB_OK_VIA="never-matches",
                CADENCE_OPENSPEC_TIMEOUT_S="4", CADENCE_OPENSPEC_BUDGET_S="5",
            )
            phase = phase_by_name(doc, "openspec")
            self.assertEqual(phase["result"], "failed")
            self.assertIn("超时", phase["error"])
            # 阶段耗时受网络预算约束（预算 5 秒 + 少量开销），不得靠反复重试拖长整体运行。
            self.assertLessEqual(phase["duration_ms"], 7000)
            inits = [l for l in envlog.read_text(encoding="utf-8").splitlines() if l.startswith("init ")]
            self.assertTrue(inits)


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


class TestTerminalReceipt(unittest.TestCase):
    """终端回执契约（cadence.skill-receipt/v1）：完整报告与早退错误共用六字段。"""

    _UNSET = object()

    def _run_receipt(self, fixture, *args, run_id=_UNSET):
        """以真实 bash 进程运行 pre-check；默认剥离外部 CADENCE_SKILL_RUN_ID 保证断言确定性。"""
        env = fixture.env()
        env.pop("CADENCE_SKILL_RUN_ID", None)
        if run_id is not TestTerminalReceipt._UNSET:
            env["CADENCE_SKILL_RUN_ID"] = run_id
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            cwd=fixture.project,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_check_partial_receipt_normal_mode(self):
        """check 普通模式 partial 仍以 0 退出，回执六字段齐全且 run_id 紧邻顶层 overall 之前。"""
        with isolated_fixture("base-tools-failure") as fx:
            proc = self._run_receipt(fx, "check")
            self.assertEqual(proc.returncode, 0)
            doc = json.loads(proc.stdout)
            self.assertEqual(doc["schema"], "cadence.skill-receipt/v1")
            self.assertEqual(doc["skill"], "pre-check")
            self.assertEqual(doc["action"], "check")
            self.assertIsNone(doc["run_id"])
            self.assertEqual(doc["exit_code"], 0)
            self.assertEqual(doc["overall"], "partial")
            # 旧消费端按文本扫描 "overall"：run_id 键必须出现在顶层真实 overall 之前。
            self.assertLess(proc.stdout.index('"run_id"'), proc.stdout.index('"overall"'))

    def test_no_interrupt_failure_receipt_nonzero(self):
        """--no-interrupt 失败以非零退出，exit_code 等于真实退出码，stderr 诊断保留。"""
        with isolated_fixture("base-tools-failure") as fx:
            proc = self._run_receipt(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 1)
            doc = json.loads(proc.stdout)
            self.assertEqual(doc["schema"], "cadence.skill-receipt/v1")
            self.assertEqual(doc["skill"], "pre-check")
            self.assertEqual(doc["action"], "run")
            self.assertIsNone(doc["run_id"])
            self.assertEqual(doc["exit_code"], proc.returncode)
            self.assertEqual(doc["overall"], "failed")
            self.assertIn("❌", proc.stderr)

    def test_cancelled_probe_reports_its_process_exit_code(self):
        with isolated_fixture() as fx:
            # 在第一个工具探测处发送真实信号；独立会话确保只取消本次预检。
            (fx.bin / "npx").write_text('#!/bin/sh\nkill -s "$FAKE_CANCEL_SIGNAL" 0\n',
                                        encoding="utf-8")
            for sig, code in (("HUP", 129), ("INT", 130), ("TERM", 143)):
                with self.subTest(signal=sig):
                    proc = subprocess.run(
                        ["bash", str(SCRIPT), "check"], cwd=fx.project,
                        env=dict(fx.env(), FAKE_CANCEL_SIGNAL=sig), start_new_session=True,
                        capture_output=True, text=True, timeout=10,
                    )
                    self.assertEqual(proc.returncode, code, proc.stderr)
                    report = json.loads(proc.stdout)
                    self.assertEqual(report["exit_code"], proc.returncode)
                    self.assertEqual(report["overall"], "failed")
                    self.assertEqual(report["action"], "check")

    def test_run_then_check_receipt_success_on_same_project(self):
        """先 run 成功再对同一项目 check：两份回执 action 分别为 run/check 且 overall=success。"""
        with isolated_fixture("openspec-ready") as fx:
            run_proc = self._run_receipt(fx, "run")
            self.assertEqual(run_proc.returncode, 0, run_proc.stderr)
            run_doc = json.loads(run_proc.stdout)
            self.assertEqual(run_doc["schema"], "cadence.skill-receipt/v1")
            self.assertEqual(run_doc["skill"], "pre-check")
            self.assertEqual(run_doc["action"], "run")
            self.assertIsNone(run_doc["run_id"])
            self.assertEqual(run_doc["exit_code"], 0)
            self.assertEqual(run_doc["overall"], "success")
            check_proc = self._run_receipt(fx, "check")
            self.assertEqual(check_proc.returncode, 0, check_proc.stderr)
            check_doc = json.loads(check_proc.stdout)
            self.assertEqual(check_doc["schema"], "cadence.skill-receipt/v1")
            self.assertEqual(check_doc["action"], "check")
            self.assertEqual(check_doc["exit_code"], 0)
            self.assertEqual(check_doc["overall"], "success")

    def test_run_id_special_characters_roundtrip(self):
        """run_id 的双引号/反斜杠/换行/制表/回车/控制字符与尾换行必须原样回传。"""
        run_id = 'pre"check\\v1\t混合\ncr\r\x07\n'
        with isolated_fixture() as fx:
            proc = self._run_receipt(fx, "check", run_id=run_id)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            doc = json.loads(proc.stdout)
            self.assertEqual(doc["run_id"], run_id)
            self.assertEqual(doc["action"], "check")
            self.assertEqual(doc["exit_code"], 0)

    def test_run_id_empty_string_counts_as_set(self):
        """空串 run_id 视为已设置，回传空字符串而非 null。"""
        with isolated_fixture() as fx:
            proc = self._run_receipt(fx, "check", run_id="")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            doc = json.loads(proc.stdout)
            self.assertEqual(doc["run_id"], "")

    def test_usage_errors_missing_unknown_duplicate_and_help(self):
        """缺少子命令/未知参数/子命令互斥重复/--help：同一 fixture 内依次验证兼容与回执。"""
        run_id = 'usage"err\n'
        with isolated_fixture() as fx:
            # 缺少子命令：exit 2、action=null，run_id 仍原样回传，stderr 帮助与诊断保留。
            proc = self._run_receipt(fx, run_id=run_id)
            self.assertEqual(proc.returncode, 2)
            doc = json.loads(proc.stdout)
            self.assertEqual(doc["schema"], "cadence.skill-receipt/v1")
            self.assertEqual(doc["skill"], "pre-check")
            self.assertIsNone(doc["action"])
            self.assertEqual(doc["run_id"], run_id)
            self.assertEqual(doc["exit_code"], 2)
            self.assertEqual(doc["overall"], "failed")
            self.assertIn("用法:", proc.stderr)
            self.assertIn("缺少子命令", proc.stderr)
            self.assertLess(proc.stdout.index('"run_id"'), proc.stdout.index('"overall"'))
            # 未知参数：action=null，stderr 帮助与诊断保留。
            proc = self._run_receipt(fx, "bogus-subcommand")
            self.assertEqual(proc.returncode, 2)
            doc = json.loads(proc.stdout)
            self.assertIsNone(doc["action"])
            self.assertEqual(doc["exit_code"], 2)
            self.assertEqual(doc["overall"], "failed")
            self.assertIn("未知参数", proc.stderr)
            self.assertIn("用法:", proc.stderr)
            # 同时指定 run 与 check 为互斥输入：无法确定单一动作，action=null。
            proc = self._run_receipt(fx, "run", "check")
            self.assertEqual(proc.returncode, 2)
            doc = json.loads(proc.stdout)
            self.assertIsNone(doc["action"])
            self.assertEqual(doc["exit_code"], 2)
            self.assertEqual(doc["overall"], "failed")
            self.assertIn("子命令重复", proc.stderr)
            # --help：保持原有 stderr 帮助并以 0 退出，不输出回执 JSON。
            proc = self._run_receipt(fx, "--help")
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")
            self.assertIn("用法:", proc.stderr)
            self.assertIn("pre-check.sh run", proc.stderr)

    def test_usage_error_after_parsed_subcommand_keeps_action(self):
        """子命令解析后的用法错与镜像加载失败：回执保留实际解析的子命令。"""
        with isolated_fixture() as fx:
            proc = self._run_receipt(fx, "check", "--upgrade")
            self.assertEqual(proc.returncode, 2)
            doc = json.loads(proc.stdout)
            self.assertEqual(doc["action"], "check")
            self.assertEqual(doc["exit_code"], 2)
            self.assertEqual(doc["overall"], "failed")
            self.assertIn("check 模式不支持", proc.stderr)
        with isolated_fixture() as fx:
            proc = self._run_receipt(fx, "run", "--mirror", "bogus")
            self.assertEqual(proc.returncode, 2)
            doc = json.loads(proc.stdout)
            self.assertEqual(doc["action"], "run")
            self.assertEqual(doc["exit_code"], 2)
            self.assertIn("未知 mirror", proc.stderr)
