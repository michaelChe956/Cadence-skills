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
                         ["pre-check", "rule-config", "mcp-configuration",
                          "project-rules-examples"])
        for c in cmd.STAGE1_COMMANDS[1:]:
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
