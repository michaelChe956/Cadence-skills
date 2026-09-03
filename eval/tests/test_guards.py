"""eval/tests/test_guards.py —— 续跑/熔断/漂移/保留/连续失败（tasks 4.1）。"""
import json
import tempfile
import time
import unittest
from pathlib import Path

from eval import ifmt
from eval.runner import guards


def _traj(agent="claude", model="glm-5.3", changes=None):
    traj = ifmt.IntermediateTrajectory(agent=agent)
    traj.model_readback = model
    traj.model_changes = changes or []
    return traj


class TestGuards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.policy = {"max_sessions_per_night": 2, "max_wall_minutes": 60,
                       "max_error_streak": 3}

    def test_model_drift_detection(self):
        """ut-gd-drift：回读与 pin 不一致 / pi 会话内变更 / 回读缺失 → 出矩阵。"""
        self.assertIsNone(guards.model_drift(_traj(), {"pinned_model": "glm-5.3"}))
        self.assertEqual(guards.model_drift(_traj(model="glm-5.2"),
                                            {"pinned_model": "glm-5.3"}),
                         "MODEL_DRIFT:glm-5.2!=glm-5.3")
        self.assertTrue(guards.model_drift(_traj(agent="pi", changes=["a", "b"]),
                                           {"pinned_model": "glm-5.3"})
                        .startswith("pi-model-change:"))
        self.assertEqual(guards.model_drift(_traj(model=""),
                                            {"pinned_model": "glm-5.3"}),
                         "model-unreadable")

    def test_should_skip_resume(self):
        """ut-gd-resume：结果已存在即跳过（断点续跑）。"""
        runs = self.base / "runs"
        runs.mkdir()
        (runs / "r1.json").write_text("{}", encoding="utf-8")
        self.assertTrue(guards.should_skip(runs, "r1"))
        self.assertFalse(guards.should_skip(runs, "r2"))

    def test_circuit_breaker_layers(self):
        """ut-gd-breaker：轮次/墙钟/连续错误三层熔断。"""
        cb = guards.CircuitBreaker(self.policy)
        self.assertFalse(cb.check(1, 1.0, 0)[0])
        self.assertTrue(cb.check(3, 1.0, 0)[0])
        self.assertTrue(cb.check(1, 61.0, 0)[0])
        self.assertTrue(cb.check(1, 1.0, 3)[0])

    def test_retention_prunes_passed_raw_only(self):
        """ut-gd-retention：通过 run 原始轨迹超窗清理，中间格式与结果保留。"""
        old = time.time() - 8 * 86400
        for verdict, path in (("PASS", self.base / "nightly/2026-08-25"),
                              ("FAIL", self.base / "nightly/2026-08-26")):
            (path / "transcripts").mkdir(parents=True)
            (path / "runs").mkdir(parents=True)
            (path / "transcripts" / "r.raw.jsonl").write_text("x", encoding="utf-8")
            (path / "runs" / "r.json").write_text(json.dumps(
                {"verdict": verdict}), encoding="utf-8")
            for p in path.rglob("*"):
                import os
                os.utime(p, (old, old))
        pruned = guards.apply_retention(self.base / "nightly", keep_nights=7)
        self.assertTrue((self.base / "nightly/2026-08-25/runs/r.json").exists())
        self.assertFalse((self.base / "nightly/2026-08-25/transcripts/r.raw.jsonl").exists())
        self.assertTrue((self.base / "nightly/2026-08-26/transcripts/r.raw.jsonl").exists())

    def test_streak_alerts(self):
        """ut-gd-streak：连续 3 夜失败端告警。"""
        state = self.base / "streaks.json"
        for _ in range(3):
            guards.update_streak(state, "kimi", ok=False)
        guards.update_streak(state, "claude", ok=True)
        self.assertEqual(guards.streak_alerts(state), ["kimi"])


if __name__ == "__main__":
    unittest.main()
