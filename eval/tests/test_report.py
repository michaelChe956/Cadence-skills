"""eval/tests/test_report.py —— 四矩阵/双键 diff/基线治理/对照组差值（tasks 4.4、1.4）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.runner import report as rep


def _result(date, agent, probe, verdict, variant="installed", model="pinned",
            clauses=("code-reading-coding.md#cadence-tools[0]",)):
    _result.seq += 1  # verdict 序号：同夜同端同探针多行不互覆（落盘文件名唯一）
    return {"schema_version": "1.0",
            "run_id": f"{date}-{agent}-{probe}-{variant}-{_result.seq}",
            "agent": agent, "model": model, "cli_version": None, "probe_id": probe,
            "rule_clause_ids": list(clauses),
            "verdict": verdict, "fail_reason": "", "denials": [],
            "transcript_path": "", "started_at": date, "duration_s": 10.0,
            "details": {}, "variant": variant}


_result.seq = 0  # 模块级自增序号（消同名覆盖）


class TestReport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def _results(self):
        rows = []
        for agent in ("claude", "codex"):
            for v in ("PASS", "PASS", "FAIL"):
                rows.append(_result("2026-09-02", agent, "P1", v))
                rows.append(_result("2026-09-03", agent, "P1", v))
        rows.append(_result("2026-09-02", "claude", "P1", "INFRA_FAIL"))
        rows.append(_result("2026-09-02", "claude", "P1", "MODEL_DRIFT"))
        rows.append(_result("2026-09-02", "codex", "P6", "PASS"))
        for v in ("PASS", "PASS", "PASS", "FAIL"):
            rows.append(_result("2026-09-02", "claude", "P1", v, variant="control"))
        return rows

    def test_aggregate_excludes_infra_and_drift(self):
        """ut-rep-exclude：INFRA/MODEL_DRIFT 出矩阵；比率=PASS/(PASS+FAIL)。"""
        agg = rep.aggregate(self._results())
        cell = agg["adherence"]["P1"]["claude"]
        # 安装组 P1@claude：两日各 PASS,PASS,FAIL → 4 PASS / 6 有效（INFRA/DRIFT 剔除）
        self.assertAlmostEqual(cell["rate"], 4 / 6)
        self.assertEqual(cell["n"], 6)

    def test_strong_rows_do_not_pollute_installed_matrix(self):
        """ut-rep-strong-isolation：strong FAIL 不混入安装组遵循率。"""
        installed = _result("2026-09-02", "claude", "P1", "PASS")
        strong = _result("2026-09-02", "claude", "P1", "FAIL")
        strong["run_id"] = "2026-09-02-claude-P1-installed-strong-0"
        agg = rep.aggregate([installed, strong])
        cell = agg["adherence"]["P1"]["claude"]
        self.assertEqual(cell["rate"], 1.0)
        self.assertEqual(cell["n"], 1)
        self.assertEqual(agg["weak_model"]["claude"]["strong_rate"], 0.0)

    def test_missing_cell_flagged_not_red(self):
        """ut-rep-missing：缺测组合标 missing，不产生红灯。"""
        agg = rep.aggregate(self._results())
        cell = agg["adherence"]["P6"]["claude"]
        self.assertTrue(cell["missing"])
        self.assertIsNone(cell["rate"])

    def test_control_delta(self):
        """ut-rep-control：安装组 vs 对照组差值（规则边际效应）。"""
        agg = rep.aggregate(self._results())
        ctl = agg["control"]["P1"]
        # 安装组 4/6；对照组 PASS,PASS,PASS,FAIL → 3/4 = 0.75；Δ = -8.3pp（合成数据允诉负值）
        self.assertAlmostEqual(ctl["installed_rate"], 4 / 6)
        self.assertAlmostEqual(ctl["control_rate"], 0.75)
        self.assertAlmostEqual(ctl["delta_pp"], round((4 / 6 - 0.75) * 100, 1))

    def test_named_diff_double_key_red(self):
        """ut-rep-diff：双键降级红灯（条款×探针定位规则文件）。"""
        rows = self._results() + [
            _result("2026-09-03", "claude", "P1", "FAIL"),
            _result("2026-09-03", "claude", "P1", "FAIL"),
            _result("2026-09-03", "claude", "P1", "FAIL")]
        agg = rep.aggregate(rows)  # P1@claude = 4/9 ≈ 44%：跌 56pp 且低于 70% 下限
        baseline = {"schema_version": "1.0",
                    "probe_agent": {"P1": {"claude": 1.0, "codex": 1.0}},
                    "clause_probe": {"code-reading-coding.md#cadence-tools[0]":
                                     {"P1": 1.0}}}
        diff = rep.named_diff(agg, baseline, degrade_drop_pp=20.0, absolute_floor=0.70)
        keys = {(d["view"], d["key"]) for d in diff if d["red"]}
        self.assertIn(("probe_agent", "P1@claude"), keys)
        clause_rows = [d for d in diff
                       if d["view"] == "clause_probe" and d["red"]]
        self.assertTrue(clause_rows)
        self.assertEqual(clause_rows[0]["clause_file"],
                         "code-reading-coding.md")

    def test_named_diff_baseline_missing_not_red(self):
        """ut-rep-nobaseline：无基线时只报当前值，不判红。"""
        agg = rep.aggregate(self._results())
        diff = rep.named_diff(agg, None)
        self.assertTrue(diff)
        self.assertTrue(all(not d["red"] for d in diff))

    def test_write_report_exit_and_baseline_untouched(self):
        """ut-rep-write：红灯 exit 1；基线文件零改写（治理：仅维护者提交）。"""
        night_dir = self.base / "reports/nightly/2026-09-02"
        runs = night_dir / "runs"
        runs.mkdir(parents=True)
        for row in self._results():
            (runs / f"{row['run_id']}.json").write_text(
                json.dumps(row), encoding="utf-8")
        (night_dir / "global-config-drift.json").write_text(
            json.dumps({"changed": [str(self.base / ".claude/settings.json")]}),
            encoding="utf-8")
        baseline = self.base / "baseline.json"
        baseline.write_text(json.dumps({"schema_version": "1.0",
                                        "probe_agent": {"P1": {"claude": 1.0}},
                                        "clause_probe": {}}), encoding="utf-8")
        before = baseline.read_text(encoding="utf-8")
        code = rep.write_report(self.base, baseline, end_date="2026-09-03")
        # P1@claude = 4/6 ≈ 67%：跌 33pp（超 20pp 阈值）且低于 70% 下限 → 红灯 exit 1
        self.assertEqual(code, 1)
        self.assertEqual(baseline.read_text(encoding="utf-8"), before)
        out_md = next((self.base / "reports/eval").glob("*/report.md"))
        text = out_md.read_text(encoding="utf-8")
        self.assertIn("缺测", text)
        self.assertIn("全局配置漂移", text)

    def test_candidate_baseline_schema(self):
        """ut-rep-candidate：候选基线含双键与 schema_version。"""
        runs = self.base / "reports/nightly/2026-09-02/runs"
        runs.mkdir(parents=True)
        for row in self._results():
            (runs / f"{row['run_id']}.json").write_text(
                json.dumps(row), encoding="utf-8")
        out = self.base / "candidate.json"
        self.assertEqual(rep.candidate_baseline(self.base, out,
                                                end_date="2026-09-03"), 0)
        doc = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(doc["schema_version"], "1.0")
        self.assertIn("probe_agent", doc)
        self.assertIn("clause_probe", doc)


if __name__ == "__main__":
    unittest.main()
