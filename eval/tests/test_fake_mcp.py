"""eval/tests/test_fake_mcp.py —— fake MCP server（tasks 2.5 / E6-9）。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from eval.mcp import fake_servers as fake

REPO_ROOT = Path(__file__).resolve().parents[2]


def _rpc(proc_stdin, obj):
    proc_stdin.write(json.dumps(obj) + "\n")
    proc_stdin.flush()


class TestFakeMcp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def _spawn(self, role):
        log = self.base / f"{role}-calls.jsonl"
        proc = subprocess.Popen(
            [sys.executable, "-m", "eval.mcp.fake_servers", "--role", role,
             "--log", str(log)],
            cwd=str(REPO_ROOT), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
        return proc, log

    def test_handshake_list_call_and_log(self):
        """ut-mcp-rpc：initialize→tools/list→tools/call 全链路且调用入记录。"""
        proc, log = self._spawn("time")
        try:
            _rpc(proc.stdin, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                              "params": {}})
            reply = json.loads(proc.stdout.readline())
            self.assertIn("result", reply)
            _rpc(proc.stdin, {"jsonrpc": "2.0", "method": "notifications/initialized"})
            _rpc(proc.stdin, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            reply = json.loads(proc.stdout.readline())
            self.assertIn("get_time", json.dumps(reply))
            _rpc(proc.stdin, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                              "params": {"name": "convert_time",
                                         "arguments": {"target": "America/New_York"}}})
            reply = json.loads(proc.stdout.readline())
            self.assertIn(fake.SEEDS["time"]["new_york"], json.dumps(reply))
        finally:
            proc.stdin.close()
            proc.wait(timeout=10)
        entries = [json.loads(ln) for ln in
                   log.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertEqual(entries[0]["server"], "time")
        self.assertEqual(entries[0]["tool"], "convert_time")

    def test_fixture_config_shape(self):
        """ut-mcp-config：注入片段指向本模块且 server 名与真实一致。"""
        cfg = fake.fixture_mcp_config(["time", "context7", "image"], self.base / "logs")
        self.assertEqual(sorted(cfg), ["context7", "time", "zai-mcp-server"])
        self.assertIn("eval.mcp.fake_servers", json.dumps(cfg))
        self.assertIn("--role", json.dumps(cfg))

    def test_read_calls_aggregates(self):
        """ut-mcp-readcalls：read_calls 汇总多角色记录。"""
        log_dir = self.base / "logs"
        log_dir.mkdir()
        (log_dir / "time-calls.jsonl").write_text(
            json.dumps({"server": "time", "tool": "get_time", "args": {}, "ts": 1}) + "\n",
            encoding="utf-8")
        (log_dir / "zai-mcp-server-calls.jsonl").write_text(
            json.dumps({"server": "zai-mcp-server", "tool": "analyze_screenshot",
                        "args": {}, "ts": 2}) + "\n", encoding="utf-8")
        calls = fake.read_calls(log_dir)
        self.assertEqual({c["server"] for c in calls}, {"time", "zai-mcp-server"})

    def test_seeds_stable(self):
        """ut-mcp-seeds：种子状态稳定（断言答案一致性依赖）。"""
        self.assertEqual(fake.SEEDS["time"]["now"], "2026-09-02 21:30")
        self.assertIn("RSC", fake.SEEDS["context7"]["summary"])


if __name__ == "__main__":
    unittest.main()
