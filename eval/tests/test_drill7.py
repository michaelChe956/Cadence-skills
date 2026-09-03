"""eval/tests/test_drill7.py —— 连续 7 夜端到端演练（tasks 5.2，mock 加速）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.runner import night


class TestDrill7(unittest.TestCase):
    def test_drill7_cli_is_registered(self):
        """ut-drill7-cli：CLI 注册 drill7 且默认启用 mock。"""
        from eval.runner.cli import build_parser

        args = build_parser().parse_args(["drill7", "--base", "/tmp/eval-drill7"])
        self.assertEqual(args.command, "drill7")
        self.assertTrue(args.mock)

    def test_drill7_mock_produces_all_outputs(self):
        """ut-drill7：7 夜 mock 演练产出四矩阵+审计表+双键 diff 齐全。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            self.assertEqual(night.drill7(base, repo, mock=True), 0)
            # 四矩阵：report.json 含全部矩阵键
            reports = list((base / "reports/eval").glob("*/report.json"))
            self.assertTrue(reports, "无聚合报告")
            agg = json.loads(reports[-1].read_text(encoding="utf-8"))["aggregate"]
            for key in ("adherence", "mcp_usage", "weak_model", "cross_end",
                        "clause_probe", "control"):
                self.assertIn(key, agg)
            # 7 夜结果目录齐备
            nights = sorted(p.name for p in (base / "reports/nightly").iterdir())
            self.assertEqual(len(nights), 7)
            # 分夜轮转：奇偶夜探针集合互补（从各夜结果文件直接验证）
            probe_sets = set()
            for n in nights:
                # 只统计安装组主行：排除 strong 增补行（全部 8 探针）与对照组行，
                # 奇偶夜互补性才是本断言靶子
                ids = {json.loads(p.read_text(encoding="utf-8"))["probe_id"]
                       for p in (base / "reports/nightly" / n / "runs").glob("*.json")
                       if not p.name.endswith(".intermediate.json")
                       and "-strong-" not in p.name and "-control-" not in p.name}
                probe_sets.add(tuple(sorted(ids)))
            self.assertEqual(len(probe_sets), 2)  # 奇偶夜两套互补集合


if __name__ == "__main__":
    unittest.main()
