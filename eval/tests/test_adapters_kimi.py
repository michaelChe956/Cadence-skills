"""eval/tests/test_adapters_kimi.py —— kimi wire.jsonl 解析（tasks 2.2）。"""
import unittest
from pathlib import Path

from eval.adapters import get_adapter

GOLDEN = Path(__file__).resolve().parents[1] / "transcripts" / "kimi" / "golden-1.jsonl"


class TestKimiAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = get_adapter("kimi")

    def test_parse_golden(self):
        """ut-adv-kimi-golden：模型回读取 usage.record（后值覆盖 config.update）。"""
        traj = self.adapter.parse_file(GOLDEN)
        self.assertEqual(traj.model_readback, "kimi-code/kimi-for-coding")
        self.assertEqual(traj.cli_version, "wire/1.4")
        tools = [c.tool for c in traj.tool_calls]
        self.assertEqual(tools, ["Read", "Grep", "Bash"])
        self.assertEqual(traj.tool_calls[1].is_error, True)
        self.assertEqual(traj.denials[0].tool, "Grep")
        self.assertIn("结论", traj.final_text)

    def test_capture_is_session(self):
        """ut-adv-kimi-capture：kimi 为 session 捕获端。"""
        self.assertEqual(self.adapter.capture, "session")

    def test_missing_model_falls_back_alias(self):
        """ut-adv-kimi-alias：无 usage.record 时回退 config.update.modelAlias。"""
        lines = [
            '{"type":"metadata","protocol_version":"1.4","created_at":1}',
            '{"type":"config.update","modelAlias":"kimi-code/kimi-for-coding","time":"1"}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertEqual(traj.model_readback, "kimi-code/kimi-for-coding")


if __name__ == "__main__":
    unittest.main()
