"""eval/tests/test_ifmt.py —— 统一中间格式（tasks 2.1 数据契约）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval import ifmt


def _sample_traj():
    traj = ifmt.IntermediateTrajectory(agent="claude")
    traj.model_readback = "glm-5.3"
    traj.cli_version = "2.1.233"
    traj.tool_calls = [
        ifmt.ToolCall(index=0, tool="Bash", raw_tool="Bash",
                      args_digest="ls -R src", is_error=False),
        ifmt.ToolCall(index=1, tool="mcp__codegraph__codegraph_explore",
                      raw_tool="mcp__codegraph__codegraph_explore",
                      args_digest="query", is_error=False),
    ]
    traj.denials = [ifmt.Denial(at_index=0, tool="Bash",
                                reason="permission denied", raw={"x": 1})]
    traj.writes = [ifmt.WriteEvent(at_index=1, path="cadence/plans/a.md")]
    traj.final_text = "中文结论"
    traj.settings_snapshot = {"permissions": {"deny": [
        "@@cadence-managed:permission-gate:v1:start@@", "Bash(ls:*)",
        "@@cadence-managed:permission-gate:v1:end@@"]}}
    return traj


class TestIfmt(unittest.TestCase):
    def test_roundtrip_dict(self):
        """ut-ifmt-roundtrip：dict 往返字段全保留。"""
        traj = _sample_traj()
        restored = ifmt.IntermediateTrajectory.from_dict(traj.to_dict())
        self.assertEqual(restored.agent, "claude")
        self.assertEqual(restored.model_readback, "glm-5.3")
        self.assertEqual(restored.tool_calls[1].tool, "mcp__codegraph__codegraph_explore")
        self.assertEqual(restored.denials[0].at_index, 0)
        self.assertEqual(restored.writes[0].path, "cadence/plans/a.md")
        self.assertIn("Bash(ls:*)", restored.settings_snapshot["permissions"]["deny"])

    def test_json_file_roundtrip(self):
        """ut-ifmt-json：落盘/读盘往返（transcript 分级保留的"中间格式"载体）。"""
        traj = _sample_traj()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "traj.json"
            ifmt.dump(traj, path)
            doc = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(doc["model_readback"], "glm-5.3")
            restored = ifmt.load(path)
            self.assertEqual(len(restored.tool_calls), 2)

    def test_model_changes_field_default(self):
        """ut-ifmt-drift：model_changes 默认空（pi 会话内变更回填处）。"""
        traj = ifmt.IntermediateTrajectory(agent="pi")
        self.assertEqual(traj.model_changes, [])


if __name__ == "__main__":
    unittest.main()
