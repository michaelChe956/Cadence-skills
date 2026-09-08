"""eval/tests/test_night.py —— 单夜流水线（mock CLI：续跑/漂移/strong 行/结果落盘）。"""
import json
import unittest
from pathlib import Path

from eval.fixtures import generator as gen
from eval.runner import night


class TestNightMock(unittest.TestCase):
    def test_cli_subcommands_registered(self):
        """ut-night-cli：night/pins-audit/verify-kimi 子命令完成解析接线。"""
        from eval.runner.cli import build_parser
        parser = build_parser()
        self.assertEqual(parser.parse_args([
            "night", "--date", "2026-09-08", "--base", "/tmp/eval"
        ]).command, "night")
        self.assertEqual(parser.parse_args(["pins-audit"]).command, "pins-audit")
        self.assertEqual(parser.parse_args([
            "verify-kimi", "--base", "/tmp/eval"
        ]).command, "verify-kimi")
        self.assertEqual(parser.parse_args([
            "report", "--base", "/tmp/eval"
        ]).command, "report")
        self.assertEqual(parser.parse_args([
            "baseline", "--base", "/tmp/eval", "--out", "/tmp/candidate.json"
        ]).command, "baseline")

    def test_run_night_mock_end_to_end(self):
        """ut-night-mock：mock 单夜产出结果 JSON/中间格式/续跑跳过。"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            rc = night.run_night("2026-09-08", repo, base, mock=True)
            self.assertEqual(rc, 0)
            nightly = base / "reports" / "nightly" / "2026-09-08"
            results = list((nightly / "runs").glob("*.json"))
            self.assertTrue(results, "无结果 JSON 落盘")
            doc = json.loads(results[0].read_text(encoding="utf-8"))
            self.assertEqual(doc["schema_version"], "1.0")
            self.assertTrue(list(nightly.rglob("*.intermediate.json")), "无中间格式落盘")
            before = len(results)
            self.assertEqual(night.run_night("2026-09-08", repo, base, mock=True), 0)
            self.assertEqual(len(list((nightly / "runs").glob("*.json"))), before)
            self.assertTrue((nightly / "global-config-drift.json").is_file())
            controls = [p for p in (nightly / "runs").glob("*-control-*.json")
                        if not p.name.endswith(".intermediate.json")]
            self.assertEqual(len(controls), 16)
            from eval.runner.schedule import night_plan
            # 从 agents.json 动态读取启用的端（codex 禁用/kimi 启用后不再是硬编码三端）
            from eval.runner import guards as _g
            _cfg = _g.load_config(Path(__file__).parent.parent / 'config' / 'agents.json')
            _enabled = [a for a, c in _cfg.items() if isinstance(c, dict) and c.get('enabled')]
            expected_agents = set(night_plan("2026-09-08", _enabled)["control_agents"])
            self.assertEqual({p.name.split("-control-")[0].split("-")[3]
                              for p in controls}, expected_agents)

    def test_model_drift_clears_infra_streak(self):
        """ut-night-b8：MODEL_DRIFT 出矩阵但清零 infra streak，不误触发熔断。"""
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            cfg_dir = base / "cfg"
            cfg_dir.mkdir()
            agents = {"claude": {"enabled": True, "pinned_model": "pinned",
                                  "strong_model": None}}
            (cfg_dir / "agents.json").write_text(json.dumps(agents), encoding="utf-8")
            policy = {"runs_per_combo": 3, "max_error_streak": 2,
                      "window_nights": 7, "retention_keep_nights": 7}
            (cfg_dir / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
            sequence = iter(("INFRA_FAIL", "MODEL_DRIFT", "PASS"))
            def fake_probe(agent, probe, variant_idx, fixture, pins, policy,
                           run_id, results_dir, *args, **kwargs):
                verdict = next(sequence)
                result = {"run_id": run_id, "agent": agent, "probe_id": probe,
                          "verdict": verdict, "variant": "installed",
                          "rule_clause_ids": []}
                results_dir = Path(results_dir)
                results_dir.mkdir(parents=True, exist_ok=True)
                (results_dir / f"{run_id}.json").write_text(
                    json.dumps(result), encoding="utf-8")
                return result
            plan = {"agents": ["claude"], "probe_ids": ["P1"],
                    "control_agents": [], "v3_agents": [], "strong_agents": [],
                    "theme": "orders"}
            with mock.patch.object(night, "run_single_probe", fake_probe), \
                    mock.patch("eval.runner.schedule.night_plan", return_value=plan):
                rc = night.run_night("2026-09-08", repo, base,
                                     config_dir=cfg_dir, mock=True)
            self.assertEqual(rc, 0)
            runs = list((base / "reports/nightly/2026-09-08/runs").glob("*.json"))
            self.assertEqual(len(runs), 3)

    def test_circuit_breaker_writes_drift_and_report(self):
        """ut-night-breaker：熔断提前结束也必须落 drift 与单夜报告。"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            cfg_dir = base / "cfg"
            cfg_dir.mkdir()
            agents = json.loads((repo / "eval/config/agents.json").read_text())
            for agent in agents:
                agents[agent]["enabled"] = agent == "claude"
            (cfg_dir / "agents.json").write_text(json.dumps(agents), encoding="utf-8")
            policy = json.loads((repo / "eval/config/policy.json").read_text())
            policy["max_sessions_per_night"] = 1
            (cfg_dir / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
            rc = night.run_night("2026-09-08", repo, base,
                                 config_dir=cfg_dir, mock=True)
            self.assertEqual(rc, 0)
            nightly = base / "reports/nightly/2026-09-08"
            self.assertTrue((nightly / "global-config-drift.json").is_file())
            report = base / "reports/eval/2026-09-08/report.md"
            self.assertTrue(report.is_file())
            self.assertIn("全局配置漂移", report.read_text(encoding="utf-8"))

    def test_strong_rows_executed(self):
        """ut-night-strong：仅执行配置了 strong_model 的端。"""
        import tempfile
        from eval.runner import cli as cli_mod
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            bin_dir = cli_mod.mock_bin(base / "bin")
            fx = gen.make_fixture("fresh", base / "fx", repo)
            runs_dir = base / "runs"
            runs_dir.mkdir()
            plan = {"strong_agents": ["claude", "codex"], "theme": "orders"}
            agents_cfg = {"claude": {"pinned_model": "glm-5.3", "strong_model": "glm-5.3-air"},
                          "codex": {"pinned_model": "gpt-5.4", "strong_model": None}}
            executed = night.run_strong_rows(
                "2026-09-10", plan, agents_cfg, {"claude": fx, "codex": fx},
                {"per_run_timeout_s": 60, "runs_per_combo": 2}, runs_dir,
                base / "transcripts", base, mock_bin_dir=bin_dir)
            self.assertEqual(executed, 8)
            strong = sorted(p.name for p in runs_dir.glob("*-strong-*.json")
                            if not p.name.endswith(".intermediate.json"))
            self.assertEqual(len(strong), 8)
            self.assertTrue(all(n.startswith("2026-09-10-claude-P") for n in strong))

    def test_drifted_run_excluded_marker(self):
        """ut-night-drift：MODEL_DRIFT run 落盘但 verdict 特殊标记。"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            cfg_dir = base / "cfg"
            cfg_dir.mkdir()
            agents = json.loads((repo / "eval/config/agents.json").read_text())
            agents["claude"]["pinned_model"] = "other-model"
            (cfg_dir / "agents.json").write_text(json.dumps(agents), encoding="utf-8")
            (cfg_dir / "policy.json").write_text((repo / "eval/config/policy.json").read_text(), encoding="utf-8")
            night.run_night("2026-09-09", repo, base, config_dir=cfg_dir, mock=True)
            results = [p for p in (base / "reports/nightly/2026-09-09/runs").glob("*P2*.json")
                       if not p.name.endswith(".intermediate.json")]
            self.assertTrue(results)
            doc = json.loads(results[0].read_text(encoding="utf-8"))
            self.assertEqual(doc["verdict"], "MODEL_DRIFT")
            self.assertIn("MODEL_DRIFT", doc["fail_reason"])


class TestProbeHomeIsolation(unittest.TestCase):
    """探针阶段 HOME 隔离与 argv_extra 必须读显式传入的 agents_cfg。

    回归靶子：旧实现读模块级 ``_agents_cfg_global``，而该变量全仓无赋值。
    ``_home_isolation({}, "pi")`` 恒 False → 真实模式探针 home=None → pi 写宿主
    ``~/.pi/agent/sessions``→``fixture.home`` 下搜不到 session → 退回 stdout
    兜底（纯 Markdown）→ 适配器解出空轨迹 → r5 夜测 15/16 判
    ``INFRA_FAIL transcript-missing``。
    """

    def _probe(self, agents_cfg, agent="pi", skill_env=None, variant="installed"):
        import tempfile
        from unittest import mock
        captured = {}
        linked = []

        def fake_run_cli(_agent, _prompt, **kwargs):
            captured.update(kwargs)
            return {"returncode": 0, "stdout_path": "", "stderr": "",
                    "duration_s": 1.0, "transcript_path": "", "timed_out": False,
                    "actual_home": ""}

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            fx = gen.make_fixture("fresh", base / "fx", repo, install=False)
            with mock.patch.object(night.proc, "run_cli", fake_run_cli), \
                    mock.patch.object(night.proc, "link_agent_auth",
                                      lambda a, f: linked.append(a) or 0):
                night.run_single_probe(
                    agent, "P1", 0, fx, {"pinned_model": "m"},
                    {"per_run_timeout_s": 60}, f"rid-{agent}",
                    base / "runs", base / "transcripts", base / "stage",
                    real_home=True, variant=variant,
                    skill_env={"X": "1"} if skill_env is None else skill_env,
                    agents_cfg=agents_cfg)
            return captured, fx, linked

    def test_isolated_agent_probe_overrides_home(self):
        """ut-night-probe-home：home_isolation 端探针必须以 fixture.home 调用。"""
        cfg = {"pi": {"home_isolation": True,
                      "skill_env": {"PI_CONFIG_DIR": "{fixture_home}/.pi"}}}
        captured, fx, _ = self._probe(cfg)
        self.assertEqual(captured["home"], fx.home)
        self.assertEqual(captured["session_root"], fx.home)

    def test_non_isolated_agent_probe_keeps_real_home(self):
        """ut-night-probe-home-off：未开隔离的端仍继承真实 HOME（登录态）。"""
        captured, _, _ = self._probe({"kimi": {"skill_env": {}}}, agent="kimi")
        self.assertIsNone(captured["home"])

    def test_isolated_control_probe_isolates_and_links_auth(self):
        """ut-night-probe-control-home：对照组（无 skill_env）同样隔离并链入凭证。

        对照组不传 skill_env，若沿用 ``real_home and skill_env`` 作为 link 条件，
        隔离 HOME 会缺 auth/npm/git bootstrap 缓存，pi 首启即崩。
        """
        cfg = {"pi": {"home_isolation": True}}
        captured, fx, linked = self._probe(cfg, skill_env={}, variant="control")
        self.assertEqual(captured["home"], fx.home)
        self.assertEqual(linked, ["pi"])

    def test_probe_resolves_argv_extra_from_config(self):
        """ut-night-probe-argv：agents.json 的 argv_extra 必须解析并透传。"""
        cfg = {"kimi": {"argv_extra": ["--skills-dir", "{fixture_home}/.kimi-code/skills"]}}
        captured, fx, _ = self._probe(cfg, agent="kimi")
        self.assertEqual(captured["argv_extra"],
                         ["--skills-dir", f"{fx.home}/.kimi-code/skills"])

    def test_run_night_passes_agents_cfg_to_probe(self):
        """ut-night-probe-cfg-wired：run_night 必须把 agents_cfg 传给每个探针。"""
        import tempfile
        from unittest import mock
        seen = []

        def fake_probe(agent, probe, variant_idx, fixture, pins, policy,
                       run_id, results_dir, *args, **kwargs):
            seen.append(kwargs.get("agents_cfg"))
            result = {"run_id": run_id, "agent": agent, "probe_id": probe,
                      "verdict": "PASS", "variant": kwargs.get("variant", "installed"),
                      "rule_clause_ids": []}
            results_dir = Path(results_dir)
            results_dir.mkdir(parents=True, exist_ok=True)
            (results_dir / f"{run_id}.json").write_text(
                json.dumps(result), encoding="utf-8")
            return result

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            cfg_dir = base / "cfg"
            cfg_dir.mkdir()
            agents = {"pi": {"enabled": True, "pinned_model": "m",
                             "home_isolation": True, "strong_model": None,
                             "skill_env": {"PI_CONFIG_DIR": "{fixture_home}/.pi"}}}
            (cfg_dir / "agents.json").write_text(json.dumps(agents), encoding="utf-8")
            (cfg_dir / "policy.json").write_text(
                json.dumps({"runs_per_combo": 1, "retention_keep_nights": 7}),
                encoding="utf-8")
            plan = {"agents": ["pi"], "probe_ids": ["P1"], "control_agents": ["pi"],
                    "v3_agents": [], "strong_agents": [], "theme": "orders"}
            with mock.patch.object(night, "run_single_probe", fake_probe), \
                    mock.patch("eval.runner.schedule.night_plan", return_value=plan):
                night.run_night("2026-09-08", repo, base,
                                config_dir=cfg_dir, mock=True)
        self.assertTrue(seen, "未执行任何探针")
        self.assertTrue(all(s == agents for s in seen),
                        f"探针未收到 agents_cfg：{seen}")


if __name__ == "__main__":
    unittest.main()
