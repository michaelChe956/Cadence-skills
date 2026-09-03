"""eval/tests/test_adapters_claude.py —— claude stream-json 适配（tasks 2.1）。"""
import json
import unittest
from pathlib import Path

from eval.adapters import get_adapter
from eval.adapters import base

GOLDEN = Path(__file__).resolve().parents[1] / "transcripts" / "claude" / "golden-1.jsonl"


class TestClaudeAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = get_adapter("claude")

    def test_registry(self):
        """ut-adv-registry：注册表暴露四端且 capture 口径正确。"""
        from eval.adapters import AGENTS
        self.assertEqual(AGENTS, ("claude", "codex", "pi", "kimi"))
        self.assertEqual(self.adapter.name, "claude")
        self.assertEqual(self.adapter.capture, "stdout")

    def test_parse_golden(self):
        """ut-adv-claude-golden：罐头轨迹解析出模型/工具/改道/终文本。"""
        traj = self.adapter.parse_file(GOLDEN)
        self.assertEqual(traj.agent, "claude")
        self.assertEqual(traj.model_readback, "glm-5.3")
        tools = [c.tool for c in traj.tool_calls]
        self.assertEqual(tools, ["Bash", "mcp__codegraph__codegraph_explore"])
        self.assertTrue(traj.tool_calls[0].is_error)
        self.assertEqual(traj.denials[0].tool, "Bash")
        self.assertIn("调用链", traj.final_text)
        self.assertEqual(traj.cli_version, "2.1.233")
        self.assertGreater(traj.duration_s, 0)
        self.assertEqual(len(traj.denials), 1)

    def test_normalize_tool(self):
        """ut-adv-normalize：工具名归一口径。"""
        self.assertEqual(base.normalize_tool("codex", "exec_command"), "Bash")
        self.assertEqual(base.normalize_tool("codex", "exec"), "Bash")
        self.assertEqual(base.normalize_tool("codex", "apply_patch"), "Edit")
        self.assertEqual(base.normalize_tool("pi", "bash"), "Bash")
        self.assertEqual(base.normalize_tool("pi", "read"), "Read")
        self.assertEqual(base.normalize_tool("claude", "mcp__time__get_time"),
                         "mcp__time__get_time")

    def test_reroute_window_ordering(self):
        """ut-adv-order：时间序 index 严格递增（改道窗口判定的基础）。"""
        traj = self.adapter.parse_file(GOLDEN)
        indexes = [c.index for c in traj.tool_calls]
        self.assertEqual(indexes, sorted(indexes))


if __name__ == "__main__":
    unittest.main()
