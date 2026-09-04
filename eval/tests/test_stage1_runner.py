"""eval/tests/test_stage1_runner.py —— CLI 封装与阶段一流水线（mock CLI，零真实端）。"""
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from eval.fixtures import generator as gen
from eval.install import commands as cmd
from eval.install import stage1
from eval.runner import proc

REPO_ROOT = Path(__file__).resolve().parents[2]


def _make_mock_bin(base: Path) -> Path:
    """生成四个 mock CLI 可执行文件（转发到 eval.runner.mock_cli）。"""
    bin_dir = base / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for agent in ("claude", "codex", "pi", "kimi"):
        wrapper = bin_dir / agent
        wrapper.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            f"sys.path.insert(0, {str(REPO_ROOT)!r})  # 子进程可导入 eval 包（脚本模式 sys.path[0]=bin 目录）\n"
            "from eval.runner import mock_cli\n"
            f"sys.exit(mock_cli.main(['--agent', '{agent}']))\n",
            encoding="utf-8")
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
    return bin_dir


class TestProc(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def test_argv_from_env_no_shell(self):
        """ut-proc-env：prompt 只经 env 注入，argv 列表直传（无 shell 展开污染）。"""
        poison = '含"双引号"与 $HOME 与 `id` 反引号'
        os.environ["EVAL_PROMPT"] = poison
        argv = proc.build_argv("claude", "glm-5.3", max_turns=40)
        self.assertIn(poison, argv)
        self.assertIn("--model", argv)
        self.assertNotIn("sh", argv[0])
        self.assertNotIn("-c", argv[:2])

    def test_run_cli_passes_argv_extra_after_template(self):
        """ut-proc-argv-extra：权限参数追加在模板 argv 末尾，None 不追加。"""
        fake_process = mock.Mock(returncode=0)
        fake_process.communicate.return_value = (b"", b"")
        extra = ["--dangerously-skip-permissions"]
        with mock.patch.object(proc.subprocess, "Popen", return_value=fake_process) as popen:
            proc.run_cli(
                "claude", "prompt", cwd=self.base, home=self.base / "home",
                pins={"pinned_model": "glm-5.3"}, timeout_s=60,
                out_dir=self.base / "out", argv_extra=extra)
            argv_with_extra = popen.call_args.args[0]
            proc.run_cli(
                "claude", "prompt", cwd=self.base, home=self.base / "home",
                pins={"pinned_model": "glm-5.3"}, timeout_s=60,
                out_dir=self.base / "out", argv_extra=None)
            argv_without_extra = popen.call_args.args[0]

        self.assertEqual(argv_with_extra[-len(extra):], extra)
        self.assertEqual(argv_without_extra, proc.build_argv("claude", "glm-5.3",
                                                              prompt="prompt"))

    def test_run_cli_passes_prompt_as_argv_argument(self):
        """ut-proc-prompt-argv：run_cli 传入真实 prompt，不能依赖父进程环境变量。"""
        from unittest import mock

        prompt = "请读取 orders；不要丢失 $HOME 或反引号 `id`"
        fake_process = mock.Mock(returncode=0)
        fake_process.communicate.return_value = (b"", b"")
        with mock.patch.object(proc.subprocess, "Popen", return_value=fake_process) as popen:
            out = proc.run_cli(
                "claude", prompt, cwd=self.base, home=self.base / "home",
                pins={"pinned_model": "glm-5.3"}, timeout_s=60,
                out_dir=self.base / "out")

        self.assertEqual(out["returncode"], 0)
        argv = popen.call_args.args[0]
        self.assertIn(prompt, argv)

    def test_build_argv_uses_explicit_prompt_without_environment(self):
        """ut-proc-prompt-isolated：显式 prompt 在 EVAL_PROMPT 清空时仍进入 argv。"""
        prompt = "隔离测试 prompt"
        with mock.patch.dict(os.environ, {"EVAL_PROMPT": ""}, clear=False):
            argv = proc.build_argv("claude", "glm-5.3", max_turns=40, prompt=prompt)
        self.assertIn(prompt, argv)

    def test_run_cli_mock_stage1_green(self):
        """ut-proc-run：mock claude 跑通一次调用并产出轨迹文件。"""
        bin_dir = _make_mock_bin(self.base)
        out = proc.run_cli("claude", "/pre-check", cwd=self.base, home=self.base / "home",
                           pins={"pinned_model": "glm-5.3"}, timeout_s=60,
                           env_extra={"EVAL_STAGE": "stage1"}, bin_dir=bin_dir)
        self.assertEqual(out["returncode"], 0)
        first = Path(out["stdout_path"]).read_text(encoding="utf-8").splitlines()[0]
        self.assertIn(json.loads(first)["type"], ("system", "user", "assistant", "result"))
        # stdout 捕获文件移出 cwd/fixture 根（缺省落系统临时目录），防污染幂等快照
        self.assertTrue(Path(out["stdout_path"]).name.startswith(".eval-claude-"))
        self.assertNotEqual(Path(out["stdout_path"]).parent, self.base)



class TestStage1Runner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.bin_dir = _make_mock_bin(self.base)
        self.fx = gen.make_fixture("fresh", self.base / "fx", REPO_ROOT)

    def test_real_stage1_argv_extra_policy(self):
        """ut-s1r-real-argv-extra：默认真 CLI 的四次调用透传端权限策略。"""
        expected = stage1.REAL_STAGE1_ARGV_EXTRA["claude"]
        calls = []

        def fake_run_cli(*args, **kwargs):
            calls.append(kwargs)
            return {"returncode": 0, "duration_s": 0, "transcript_path": ""}

        with mock.patch.object(stage1.proc, "run_cli", side_effect=fake_run_cli), \
                mock.patch.object(stage1.asrt, "assert_stage1", return_value=[]):
            report = stage1.run_stage1(
                "claude", self.fx, {"pinned_model": "glm-5.3"},
                cli=stage1.proc.run_cli, verify=lambda root: 0)

        self.assertTrue(report["ok"])
        self.assertEqual(len(calls), len(cmd.STAGE1_COMMANDS))
        self.assertTrue(all(call["argv_extra"] == expected for call in calls))

    def test_stage1_real_argv_extra_constant_covers_all_agents(self):
        """ut-s1r-real-argv-extra-constant：四端策略键完整，claude 安装阶段全放行。"""
        self.assertEqual(set(stage1.REAL_STAGE1_ARGV_EXTRA),
                         {"claude", "codex", "pi", "kimi"})
        self.assertEqual(stage1.REAL_STAGE1_ARGV_EXTRA["claude"],
                         ["--dangerously-skip-permissions"])
        for agent in ("codex", "pi", "kimi"):
            self.assertEqual(stage1.REAL_STAGE1_ARGV_EXTRA[agent], [])

    def test_stage1_mock_cli_does_not_receive_argv_extra(self):
        """ut-s1r-injected-cli-no-argv-extra：注入 CLI 保持原有调用契约。"""
        calls = []

        def fake_cli(*args, **kwargs):
            calls.append(kwargs)
            return {"returncode": 0, "duration_s": 0, "transcript_path": ""}

        with mock.patch.object(stage1.asrt, "assert_stage1", return_value=[]):
            report = stage1.run_stage1(
                "claude", self.fx, {"pinned_model": "glm-5.3"},
                cli=fake_cli, verify=lambda root: 0)

        self.assertTrue(report["ok"])
        self.assertTrue(all("argv_extra" not in call for call in calls))

    def test_default_verify_uses_external_report(self):
        """ut-s1r-verify-report：真实 verify argv 必须带项目根外临时报告路径。"""
        with mock.patch.object(stage1.subprocess, "run",
                               return_value=mock.Mock(returncode=0)) as run:
            verify = stage1._default_verify(REPO_ROOT)
            self.assertEqual(verify(self.fx.root), 0)
        argv = run.call_args.args[0]
        self.assertEqual(argv[:2], [stage1.sys.executable,
                                    str(REPO_ROOT / "cadence-init/skills/rule-config/scripts/rule-config.py")])
        self.assertIn("--verify", argv)
        self.assertIn("--project-root", argv)
        self.assertIn("--report", argv)
        report_path = Path(argv[argv.index("--report") + 1])
        self.assertNotIn(str(self.fx.root), str(report_path))
        self.assertFalse(report_path.exists(), "verify 临时报告应在调用后清理")

    def test_stage1_commands_table(self):
        """ut-s1r-commands：四 command 依序且均为 no-interrupt 确定性形态。"""
        self.assertEqual([c["name"] for c in cmd.STAGE1_COMMANDS],
                         ["pre-check", "mcp-configuration", "rule-config",
                          "project-rules-examples"])
        for c in cmd.STAGE1_COMMANDS:
            self.assertIn("no-interrupt", c["prompt"])

    def test_stage1_mock_all_green(self):
        """ut-s1r-green：mock CLI 下阶段一全绿（Tier-0 冒烟核心）。"""
        report = stage1.run_stage1("claude", self.fx, {"pinned_model": "glm-5.3"},
                                   bin_dir=self.bin_dir, verify=lambda root: 0)
        bad = [a for a in report["assertions"] if not a["ok"]]
        self.assertEqual(bad, [], [f"{a['name']}: {a['detail']}" for a in bad])
        self.assertTrue(report["ok"])
        self.assertEqual(report["verify_exit"], 0)

    def test_stage1_collects_extra(self):
        """ut-s1r-extra：runner 采集 pre-check 零改动与 rules_before 快照供断言表。"""
        report = stage1.run_stage1("claude", self.fx, {"pinned_model": "glm-5.3"},
                                   bin_dir=self.bin_dir, verify=lambda root: 0)
        names = [a["name"] for a in report["assertions"]]
        self.assertIn("pre-check.zero-change", names)
        self.assertIn("prx.not-rules", names)


if __name__ == "__main__":
    unittest.main()


class TestLinkAgentAuth(unittest.TestCase):
    """ut-authlink：skill_env 重定向带走凭证目录，真实模式需软链真实凭证。"""

    def test_links_credentials_into_fixture(self):
        import tempfile
        from types import SimpleNamespace
        from unittest import mock
        from eval.runner import proc
        with tempfile.TemporaryDirectory() as td:
            real_home = Path(td) / "realhome"
            (real_home / ".claude").mkdir(parents=True)
            (real_home / ".claude" / ".credentials.json").write_text("{}")
            fx = SimpleNamespace(home=Path(td) / "fx")
            with mock.patch.object(proc.Path, "home", lambda: real_home):
                n = proc.link_agent_auth("claude", fx)
            dst = fx.home / ".claude" / ".credentials.json"
            self.assertEqual(n, 1)
            self.assertTrue(dst.is_symlink())
            self.assertEqual(dst.resolve(), real_home / ".claude" / ".credentials.json")

    def test_skips_when_source_missing(self):
        import tempfile
        from types import SimpleNamespace
        from unittest import mock
        from eval.runner import proc
        with tempfile.TemporaryDirectory() as td:
            fx = SimpleNamespace(home=Path(td) / "fx2")
            with mock.patch.object(proc.Path, "home", lambda: Path(td) / "empty"):
                self.assertEqual(proc.link_agent_auth("claude", fx), 0)
