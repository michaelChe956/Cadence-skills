"""eval/tests/test_offline_rerun.py —— 离线重跑（tasks 4.2 / oracle §2-c）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.runner import offline_rerun as rr


TRANS = Path(__file__).resolve().parents[1] / "transcripts"


class TestOfflineRerun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def _golden(self, verdict="PASS"):
        path = self.base / "golden-verdicts.json"
        path.write_text(json.dumps([
            {"path": "claude/golden-1.jsonl", "agent": "claude",
             "probe_id": "P1", "expect_verdict": verdict,
             "settings_snapshot": {"permissions": {"deny": [
                 "@@cadence-managed:permission-gate:v1:start@@", "Bash(ls:*)",
                 "Grep", "Glob",
                 "@@cadence-managed:permission-gate:v1:end@@"]}}}]),
            encoding="utf-8")
        return path

    def test_rerun_matches_golden(self):
        """ut-rr-match：罐头轨迹重判与登记一致（受管 deny→改道=PASS）。"""
        self.assertEqual(rr.run_rerun(TRANS, self._golden("PASS")), 0)

    def test_rerun_detects_flip(self):
        """ut-rr-flip：判定翻转被点名（断言器回归红线）。"""
        self.assertEqual(rr.run_rerun(TRANS, self._golden("FAIL")), 1)

    def test_rerun_missing_file_reported(self):
        """ut-rr-missing：登记文件缺失报错不静默。"""
        path = self.base / "golden-verdicts.json"
        path.write_text(json.dumps([
            {"path": "claude/nope.jsonl", "agent": "claude",
             "probe_id": "P1", "expect_verdict": "PASS"}]), encoding="utf-8")
        self.assertEqual(rr.run_rerun(TRANS, path), 1)


if __name__ == "__main__":
    unittest.main()
