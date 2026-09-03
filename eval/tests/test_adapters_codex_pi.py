"""eval/tests/test_adapters_codex_pi.py —— codex rollout 与 pi session 解析（tasks 2.2）。"""
import os
import tempfile
import unittest
from pathlib import Path

from eval.adapters import get_adapter

TRANS = Path(__file__).resolve().parents[1] / "transcripts"


class TestCodexAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = get_adapter("codex")

    def test_parse_golden(self):
        """ut-adv-codex-golden：模型回读/工具归一/命令头摘要。"""
        traj = self.adapter.parse_file(TRANS / "codex" / "golden-1.jsonl")
        self.assertEqual(traj.model_readback, "gpt-5.4")
        tools = [c.tool for c in traj.tool_calls]
        self.assertEqual(tools, ["Bash", "Read"])
        self.assertEqual(traj.tool_calls[0].args_digest, "ls src")
        self.assertGreater(traj.duration_s, 0)
        self.assertTrue(traj.started_at.startswith("2026-"))
        self.assertIsNone(traj.cli_version)

    def test_tool_name_variance_normalized(self):
        """ut-adv-codex-variance：custom_tool_call 形态同样归一（跨会话变体防线）。"""
        lines = [
            '{"timestamp":"2026-09-02T12:00:00Z","type":"turn_context","payload":{"model":"gpt-5.4"}}',
            '{"timestamp":"2026-09-02T12:00:01Z","type":"response_item","payload":'
            '{"type":"custom_tool_call","name":"exec","arguments":"{\\"command\\":\\"find . -name x\\"}"}}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertEqual(traj.tool_calls[0].tool, "Bash")
        self.assertEqual(traj.tool_calls[0].args_digest, "find . -name x")

    def test_local_shell_call_and_bash_lc_prefix(self):
        """ut-adv-codex-shell：local_shell_call 也纳入工具负载并剥离 bash -lc。"""
        lines = [
            '{"type":"response_item","payload":{"type":"local_shell_call","name":"exec_command",'
            '"arguments":"{\\"command\\":[\\"bash\\",\\"-lc\\",\\"printf hi\\"]}","call_id":"c1"}}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertEqual(len(traj.tool_calls), 1)
        self.assertEqual(traj.tool_calls[0].tool, "Bash")
        self.assertEqual(traj.tool_calls[0].args_digest, "printf hi")

    def test_output_error_marks_is_error(self):
        """ut-adv-codex-err：function_call_output 的 error 字段回填 is_error。"""
        lines = [
            '{"timestamp":"2026-09-02T12:00:00Z","type":"response_item","payload":'
            '{"type":"function_call","name":"exec_command","arguments":"{}","call_id":"c1"}}',
            '{"timestamp":"2026-09-02T12:00:01Z","type":"response_item","payload":'
            '{"type":"function_call_output","call_id":"c1","output":"{\\"error\\":\\"denied\\"}"}}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertTrue(traj.tool_calls[0].is_error)

    def test_event_error_is_recorded_as_infra_note(self):
        """ut-adv-codex-infra：event_msg error 旁路进入 settings 快照。"""
        lines = [
            '{"type":"event_msg","payload":{"type":"error","message":"sandbox unavailable"}}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertEqual(traj.settings_snapshot["_infra_errors"], ["sandbox unavailable"])

    def test_find_latest_session(self):
        """ut-adv-codex-session：按 mtime 定位 since_ts 后最新 rollout。"""
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            old = home / ".codex/sessions/2026/rollout-old.jsonl"
            new = home / ".codex/sessions/2026/rollout-new.jsonl"
            old.parent.mkdir(parents=True)
            old.write_text("{}\n", encoding="utf-8")
            new.write_text("{}\n", encoding="utf-8")
            old.touch()
            new.touch()
            now = new.stat().st_mtime
            os.utime(old, (now - 2, now - 2))
            self.assertEqual(self.adapter.find_latest_session(home, now - 1), new)
            self.assertIsNone(self.adapter.find_latest_session(home, now + 1))


class TestPiAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = get_adapter("pi")

    def test_parse_golden(self):
        """ut-adv-pi-golden：session 版本/工具归一/终文本。"""
        traj = self.adapter.parse_file(TRANS / "pi" / "golden-1.jsonl")
        self.assertEqual(traj.agent, "pi")
        self.assertEqual(traj.cli_version, "0.5.2")
        tools = [c.tool for c in traj.tool_calls]
        self.assertEqual(tools, ["Bash", "Read"])
        self.assertIn("完成", traj.final_text)

    def test_model_change_records_drift(self):
        """ut-adv-pi-drift：会话内 model_change 记入 model_changes（run 作废依据）。"""
        lines = [
            '{"type":"session","cwd":"/fx","id":"s1","timestamp":"2026-09-02T12:00:00Z","version":"0.5.2"}',
            '{"type":"model_change","modelId":"glm-5.3","provider":"zai","id":"m1",'
            '"parentId":null,"timestamp":"2026-09-02T12:00:01Z"}',
            '{"type":"message","id":"a1","message":{"role":"assistant",'
            '"content":[{"type":"text","text":"ok"}]}}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertEqual(traj.model_changes, ["glm-5.3"])
        self.assertEqual(traj.model_readback, "glm-5.3")

    def test_empty_model_change_is_ignored(self):
        """ut-adv-pi-empty-model：空 modelId 不制造漂移记录。"""
        traj = self.adapter.parse_stream(['{"type":"model_change","modelId":""}'])
        self.assertEqual(traj.model_changes, [])
        self.assertEqual(traj.model_readback, "")

    def test_tool_result_error_marks_denial(self):
        """ut-adv-pi-denial：toolResult 的 permission 标记回填错误并记录 Denial。"""
        lines = [
            '{"type":"message","message":{"role":"assistant","content":['
            '{"type":"toolCall","id":"c1","name":"bash","arguments":{"command":"rm -rf /"}}]}}',
            '{"type":"message","message":{"role":"toolResult","content":['
            '{"type":"text","text":"permission denied"}]}}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertTrue(traj.tool_calls[0].is_error)
        self.assertEqual(len(traj.denials), 1)
        self.assertEqual(traj.denials[0].tool, "Bash")

    def test_tool_results_pair_in_order(self):
        """ut-adv-pi-pairing：结果按最近未闭合调用的顺序配对。"""
        lines = [
            '{"type":"message","message":{"role":"assistant","content":['
            '{"type":"toolCall","id":"c1","name":"bash","arguments":{"command":"one"}},'
            '{"type":"toolCall","id":"c2","name":"read","arguments":{"path":"x"}}]}}',
            '{"type":"message","message":{"role":"toolResult","content":['
            '{"type":"text","text":"permission denied"}]}}',
            '{"type":"message","message":{"role":"toolResult","content":['
            '{"type":"text","text":"ok"}]}}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertTrue(traj.tool_calls[0].is_error)
        self.assertFalse(traj.tool_calls[1].is_error)

    def test_find_latest_session(self):
        """ut-adv-pi-session：按约定 run-*/session.jsonl 定位最新会话。"""
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            old = home / ".pi/agent/sessions/a/run-1/session.jsonl"
            new = home / ".pi/agent/sessions/b/run-2/session.jsonl"
            old.parent.mkdir(parents=True)
            new.parent.mkdir(parents=True)
            old.write_text("{}\n", encoding="utf-8")
            new.write_text("{}\n", encoding="utf-8")
            old.touch()
            new.touch()
            now = new.stat().st_mtime
            os.utime(old, (now - 2, now - 2))
            self.assertEqual(self.adapter.find_latest_session(home, now - 1), new)
            self.assertIsNone(self.adapter.find_latest_session(home, now + 1))

    def test_capture_is_session(self):
        """ut-adv-pi-capture：pi 为 session 捕获端。"""
        self.assertEqual(self.adapter.capture, "session")


if __name__ == "__main__":
    unittest.main()
