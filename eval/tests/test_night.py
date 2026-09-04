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


if __name__ == "__main__":
    unittest.main()
