"""forensics-denial 回归：真实模式必须收到 prompt，且 fixture 必须触发权限 gate。"""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from eval.runner import cli, forensics


class TestForensicsDenial(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo_root = self.base / "repo"
        self.repo_root.mkdir()

    def _make_fixture(self, seen):
        def make_fixture(variant, work_dir, repo_root):
            seen.append(variant)
            root = work_dir / "fixture"
            home = work_dir / "home"
            root.mkdir()
            home.mkdir()
            return SimpleNamespace(root=root, home=home, repo=repo_root)
        return make_fixture

    def test_default_variant_is_mcp_pre_and_gate_deny_is_recorded(self):
        """ut-forensics-default：默认 mcp_pre，阶段一写出 deny 后才运行真实 CLI。"""
        seen = []
        trajectory = SimpleNamespace(denials=[], tool_calls=[])

        def stage1_with_gate(agent, fixture, pins, timeout_s, **kw):
            settings = fixture.root / ".claude" / "settings.json"
            settings.parent.mkdir()
            settings.write_text(json.dumps({"permissions": {"deny": ["Grep"]}}),
                                encoding="utf-8")

        with mock.patch.object(forensics.gen, "make_fixture", self._make_fixture(seen)), \
                mock.patch.object(forensics.guards, "load_config", return_value={}), \
                mock.patch.object(forensics.stage1, "run_stage1", stage1_with_gate), \
                mock.patch("eval.runner.proc.run_cli", return_value={
                    "transcript_path": str(self.base / "run.jsonl"), "returncode": 0,
                    "stderr": ""}), \
                mock.patch.object(forensics, "get_adapter", return_value=SimpleNamespace(
                    parse_file=mock.Mock(return_value=trajectory))):
            evidence = forensics.forensics_denial(self.repo_root, self.base / "runs", {})

        self.assertEqual(seen, ["mcp_pre"])
        payload = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(payload["fixture_settings_deny"], ["Grep"])

    def test_forensics_rejects_fixture_without_deny_gate(self):
        """ut-forensics-gate：fixture 未产生 deny 配置时，禁止无效取证。"""
        seen = []
        with mock.patch.object(forensics.gen, "make_fixture", self._make_fixture(seen)), \
                mock.patch.object(forensics.guards, "load_config", return_value={}), \
                mock.patch.object(forensics.stage1, "run_stage1", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "fixture_settings_deny"):
                forensics.forensics_denial(self.repo_root, self.base / "runs", {})

    def test_cli_forwards_variant(self):
        """ut-forensics-cli-variant：--variant 原样透传至 forensics runner。"""
        evidence = self.base / "denial.json"
        evidence.write_text(json.dumps({"denial_events_raw": [{}]}), encoding="utf-8")
        with mock.patch.object(forensics, "forensics_denial", return_value=evidence) as runner:
            result = cli.main([
                "forensics-denial", "--base", str(self.base / "runs"), "--variant", "fresh",
            ])

        self.assertEqual(result, 0)
        self.assertEqual(runner.call_args.kwargs["variant"], "fresh")
        parsed = cli.build_parser().parse_args([
            "forensics-denial", "--base", str(self.base / "runs"),
        ])
        self.assertEqual(parsed.variant, "mcp_pre")


    def test_real_mode_skill_env_wiring(self):
        """ut-forensics-skillenv：真实模式必须经 skill_env 走真实 HOME（B10 策略）。"""
        seen = []
        trajectory = SimpleNamespace(denials=[], tool_calls=[])
        stage1_kwargs, probe_kwargs = {}, {}

        def stage1_with_gate(agent, fixture, pins, timeout_s, **kw):
            stage1_kwargs.update(kw)
            settings = fixture.root / ".claude" / "settings.json"
            settings.parent.mkdir()
            settings.write_text(json.dumps({"permissions": {"deny": ["Grep"]}}),
                                encoding="utf-8")

        def probe_cli(agent, prompt, **kw):
            probe_kwargs.update(kw)
            return {"transcript_path": str(self.base / "run.jsonl"),
                    "returncode": 0, "stderr": ""}

        fake_cfg = {"claude": {"skill_env": {"CLAUDE_CONFIG_DIR": "{fixture_home}/.claude"}}}
        with mock.patch.object(forensics.gen, "make_fixture", self._make_fixture(seen)), \
                mock.patch.object(forensics.guards, "load_config", return_value={}), \
                mock.patch.object(forensics.stage1, "run_stage1", stage1_with_gate), \
                mock.patch("eval.runner.proc.run_cli", probe_cli), \
                mock.patch.object(forensics, "get_adapter", return_value=SimpleNamespace(
                    parse_file=mock.Mock(return_value=trajectory))), \
                mock.patch.object(forensics.guards, "load_config", return_value=fake_cfg):
            forensics.forensics_denial(self.repo_root, self.base / "runs", {})

        expected_env = {"CLAUDE_CONFIG_DIR": str(self.base / "runs" / "tmp-placeholder")}
        # skill_env 已解析（占位符替换为 fixture.home）
        self.assertIn("skill_env", stage1_kwargs)
        self.assertTrue(stage1_kwargs["skill_env"])
        self.assertEqual(probe_kwargs.get("home"), None)
        self.assertEqual(probe_kwargs.get("skill_env"), stage1_kwargs["skill_env"])
        self.assertTrue(probe_kwargs.get("session_root"))


if __name__ == "__main__":

    def test_real_mode_skill_env_wiring(self):
        """ut-forensics-skillenv：真实模式必须经 skill_env 走真实 HOME（B10 策略）。"""
        seen = []
        trajectory = SimpleNamespace(denials=[], tool_calls=[])
        stage1_kwargs, probe_kwargs = {}, {}

        def stage1_with_gate(agent, fixture, pins, timeout_s, **kw):
            stage1_kwargs.update(kw)
            settings = fixture.root / ".claude" / "settings.json"
            settings.parent.mkdir()
            settings.write_text(json.dumps({"permissions": {"deny": ["Grep"]}}),
                                encoding="utf-8")

        def probe_cli(agent, prompt, **kw):
            probe_kwargs.update(kw)
            return {"transcript_path": str(self.base / "run.jsonl"),
                    "returncode": 0, "stderr": ""}

        fake_cfg = {"claude": {"skill_env": {"CLAUDE_CONFIG_DIR": "{fixture_home}/.claude"}}}
        with mock.patch.object(forensics.gen, "make_fixture", self._make_fixture(seen)), \
                mock.patch.object(forensics.guards, "load_config", return_value={}), \
                mock.patch.object(forensics.stage1, "run_stage1", stage1_with_gate), \
                mock.patch("eval.runner.proc.run_cli", probe_cli), \
                mock.patch.object(forensics, "get_adapter", return_value=SimpleNamespace(
                    parse_file=mock.Mock(return_value=trajectory))), \
                mock.patch.object(forensics.guards, "load_config", return_value=fake_cfg):
            forensics.forensics_denial(self.repo_root, self.base / "runs", {})

        expected_env = {"CLAUDE_CONFIG_DIR": str(self.base / "runs" / "tmp-placeholder")}
        # skill_env 已解析（占位符替换为 fixture.home）
        self.assertIn("skill_env", stage1_kwargs)
        self.assertTrue(stage1_kwargs["skill_env"])
        self.assertEqual(probe_kwargs.get("home"), None)
        self.assertEqual(probe_kwargs.get("skill_env"), stage1_kwargs["skill_env"])
        self.assertTrue(probe_kwargs.get("session_root"))


if __name__ == "__main__":
    unittest.main()
