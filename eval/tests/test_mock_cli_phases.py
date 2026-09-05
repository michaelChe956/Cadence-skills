"""mock CLI 阶段报告 action 口径回归测试。"""
import unittest
from pathlib import Path

from eval.runner.mock_cli import _stage1_pre_check


class TestMockCliPhases(unittest.TestCase):
    def test_pre_check_phase_actions_match_real_run_ready_semantics(self):
        """mock 五 phase action 必须与真实 run/fixture-ready 口径一致。"""
        report = _stage1_pre_check(Path("/tmp/eval-mock-cli-phases"))
        actions = {phase["phase"]: phase["action"] for phase in report["phases"]}
        self.assertEqual(actions, {
            "base-tools": "do_base_tools",
            "openspec": "verify-ready",
            "superpowers-git": "fetch-pull-ff-only",
            "superpowers-links": "all-skipped",
            "verify": "all-skipped",
        })


if __name__ == "__main__":
    unittest.main()
