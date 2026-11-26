#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mcp-config 单元测试（unittest）。

覆盖：
  * 默认 server 缺失后重跑补回（报告 MCP_SERVER_RESTORED）；
  * 用户改过的 command / url 保留（用户值优先）；
  * 项目额外 server 保留；
  * 写入前归档到 cadence/legacy/<14位时间戳>/<rel>；
  * 第二次运行零写入、零备份；
  * 真实密钥不出现在报告与标准输出；
  * 解析失败不重建、不覆盖（degraded + pending）；
  * `.codex/config.toml` 按表块补齐、已有块不覆盖用户字段。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "mcp-config.py"

RECEIPT_SCHEMA = "cadence.skill-receipt/v1"
RUN_ID_ENV = "CADENCE_SKILL_RUN_ID"

WRITE_ACTIONS = {
    "created", "merged", "server-restored", "field-added",
    "args-merged", "placeholder-replaced",
}


class McpConfigTestCase(unittest.TestCase):
    """测试基类：临时项目 + 脚本调用。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="mcp-config-test-"))
        self.project = self.tmp / "project"
        self.project.mkdir()
        self.report_path = self.tmp / "report.json"

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- helpers ---------------------------------------------------------

    def child_env(self, overrides: Optional[dict] = None) -> dict:
        """子进程环境：默认清除 `CADENCE_SKILL_RUN_ID`，让 run_id 断言确定。"""
        env = {k: v for k, v in os.environ.items() if k != RUN_ID_ENV}
        if overrides:
            env.update(overrides)
        return env

    def run_apply(self, *extra: str, env: Optional[dict] = None) -> subprocess.CompletedProcess:
        """执行 mcp-config.py apply。"""
        cmd = [
            sys.executable, str(SCRIPT), "apply",
            "--project-root", str(self.project),
            "--report", str(self.report_path),
            "--no-interrupt",
            *extra,
        ]
        return subprocess.run(cmd, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=120,
                              env=self.child_env(env))

    def read_report(self) -> dict:
        return json.loads(self.report_path.read_text(encoding="utf-8"))

    def read_mcp_json(self) -> dict:
        return json.loads((self.project / ".mcp.json").read_text(encoding="utf-8"))

    def write_mcp_json(self, document: dict) -> None:
        (self.project / ".mcp.json").write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")

    def legacy_backups(self) -> list[Path]:
        legacy = self.project / "cadence" / "legacy"
        if not legacy.exists():
            return []
        found: list[Path] = []
        for stamp_dir in legacy.iterdir():
            if not stamp_dir.is_dir():
                continue
            for path in stamp_dir.rglob("*"):
                if path.is_file() and path.name != ".gitignore":
                    found.append(path)
        return found


class TestCreation(McpConfigTestCase):
    """首次创建。"""

    def test_creates_mcp_json_with_default_servers(self) -> None:
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        servers = self.read_mcp_json()["mcpServers"]
        for name in ("time", "context7", "sequential-thinking",
                     "zai-mcp-server", "MiniMax"):
            self.assertIn(name, servers)
        # 非 coding 项目不写 codegraph。
        self.assertNotIn("codegraph", servers)
        report = self.read_report()
        self.assertEqual(report["overall"], "ok")

    def test_creates_codex_toml(self) -> None:
        self.run_apply()
        text = (self.project / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("[mcp_servers.time]", text)
        self.assertIn("[mcp_servers.context7]", text)
        self.assertIn("http_headers", text)  # HTTP server 同步为 http_headers

    def test_coding_project_gets_codegraph(self) -> None:
        (self.project / "main.py").write_text("print('hi')\n", encoding="utf-8")
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("codegraph", self.read_mcp_json()["mcpServers"])
        self.assertEqual(self.read_report()["project_type"], "coding")


class TestMergeSemantics(McpConfigTestCase):
    """既有配置的合并语义。"""

    def test_removed_default_server_is_restored(self) -> None:
        self.write_mcp_json({"mcpServers": {"context7": {
            "type": "stdio", "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"], "env": {},
        }}})
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        servers = self.read_mcp_json()["mcpServers"]
        self.assertIn("time", servers)
        self.assertIn("sequential-thinking", servers)
        report = self.read_report()
        self.assertIn("MCP_SERVER_RESTORED", json.dumps(report, ensure_ascii=False))

    def test_user_command_is_preserved(self) -> None:
        self.write_mcp_json({"mcpServers": {"context7": {
            "type": "stdio", "command": "my-own-ctx",
            "args": ["-y", "@upstash/context7-mcp"], "env": {},
        }}})
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        servers = self.read_mcp_json()["mcpServers"]
        self.assertEqual(servers["context7"]["command"], "my-own-ctx")
        report = self.read_report()
        self.assertIn("MCP_USER_VALUE_KEPT", json.dumps(report, ensure_ascii=False))

    def test_user_url_is_preserved(self) -> None:
        self.write_mcp_json({"mcpServers": {"zread": {
            "type": "http", "url": "https://my-proxy.example/mcp",
            "headers": {"Authorization": "Bearer my-own"},
        }}})
        self.run_apply()
        servers = self.read_mcp_json()["mcpServers"]
        self.assertEqual(servers["zread"]["url"], "https://my-proxy.example/mcp")
        self.assertEqual(servers["zread"]["headers"]["Authorization"],
                         "Bearer my-own")

    def test_extra_project_server_is_preserved(self) -> None:
        self.write_mcp_json({"mcpServers": {"my-own-server": {
            "command": "node", "args": ["server.js"], "extraField": {"a": 1},
        }}})
        self.run_apply()
        servers = self.read_mcp_json()["mcpServers"]
        self.assertIn("my-own-server", servers)
        self.assertEqual(servers["my-own-server"]["extraField"], {"a": 1})

    def test_framework_args_come_first(self) -> None:
        self.write_mcp_json({"mcpServers": {"time": {
            "command": "uvx", "args": ["--tz", "UTC"],
        }}})
        self.run_apply()
        args = self.read_mcp_json()["mcpServers"]["time"]["args"]
        self.assertEqual(args, [
            "mcp-server-time", "--local-timezone=Asia/Shanghai",
            "--tz", "UTC",
        ])

    def test_pinned_package_version_not_duplicated(self) -> None:
        self.write_mcp_json({"mcpServers": {"context7": {
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp@1.0.2"],
        }}})
        self.run_apply()
        args = self.read_mcp_json()["mcpServers"]["context7"]["args"]
        self.assertEqual(args, ["-y", "@upstash/context7-mcp@1.0.2"])

    def test_duplicate_project_args_are_not_appended(self) -> None:
        self.write_mcp_json({"mcpServers": {"time": {
            "command": "uvx",
            "args": ["mcp-server-time", "--local-timezone=Asia/Shanghai"],
        }}})
        self.run_apply()
        args = self.read_mcp_json()["mcpServers"]["time"]["args"]
        self.assertEqual(args, ["mcp-server-time", "--local-timezone=Asia/Shanghai"])

    def test_placeholder_env_value_takes_framework_value(self) -> None:
        self.write_mcp_json({"mcpServers": {"zai-mcp-server": {
            "type": "stdio", "command": "npx", "args": ["-y", "@z_ai/mcp-server"],
            "env": {"Z_AI_MODE": "your_zhipu_api_key"},
        }}})
        self.run_apply()
        env = self.read_mcp_json()["mcpServers"]["zai-mcp-server"]["env"]
        self.assertEqual(env["Z_AI_MODE"], "ZHIPU")
        self.assertEqual(env["Z_AI_API_KEY"], "your_zhipu_api_key")

    def test_non_placeholder_env_value_is_kept(self) -> None:
        self.write_mcp_json({"mcpServers": {"zai-mcp-server": {
            "type": "stdio", "command": "npx", "args": ["-y", "@z_ai/mcp-server"],
            "env": {"Z_AI_MODE": "CUSTOM"},
        }}})
        self.run_apply()
        env = self.read_mcp_json()["mcpServers"]["zai-mcp-server"]["env"]
        self.assertEqual(env["Z_AI_MODE"], "CUSTOM")

    def test_malformed_user_args_are_kept(self) -> None:
        self.write_mcp_json({"mcpServers": {"time": {
            "command": "uvx", "args": "not-a-list",
        }}})
        self.run_apply()
        args = self.read_mcp_json()["mcpServers"]["time"]["args"]
        self.assertEqual(args, "not-a-list")
        report = self.read_report()
        self.assertIn("MCP_FIELD_INVALID", json.dumps(report, ensure_ascii=False))


class TestBackupAndIdempotency(McpConfigTestCase):
    """归档与幂等。"""

    def test_existing_file_is_archived_before_write(self) -> None:
        original = json.dumps({"mcpServers": {"context7": {
            "type": "stdio", "command": "npx", "args": ["-y", "@upstash/context7-mcp"],
        }}}, ensure_ascii=False, indent=2) + "\n"
        (self.project / ".mcp.json").write_text(original, encoding="utf-8")
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        backups = self.legacy_backups()
        self.assertTrue(backups, "写入前必须归档")
        archived = [p for p in backups if p.name == ".mcp.json"]
        self.assertTrue(archived)
        self.assertEqual(archived[0].read_text(encoding="utf-8"), original)
        # 归档目录为 14 位时间戳
        stamp_names = [p.name for p in archived[0].parents
                       if re.fullmatch(r"\d{14}(-\d+)?", p.name)]
        self.assertTrue(stamp_names, f"归档目录名不是 14 位时间戳：{archived[0]}")

    def test_second_run_is_zero_write(self) -> None:
        self.write_mcp_json({"mcpServers": {"context7": {
            "type": "stdio", "command": "npx", "args": ["-y", "@upstash/context7-mcp"],
        }}})
        first = self.run_apply()
        self.assertEqual(first.returncode, 0, first.stderr)
        mcp_before = (self.project / ".mcp.json").read_bytes()
        toml_before = (self.project / ".codex" / "config.toml").read_bytes()
        backups_before = sorted(str(p) for p in self.legacy_backups())

        second = self.run_apply()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((self.project / ".mcp.json").read_bytes(), mcp_before)
        self.assertEqual((self.project / ".codex" / "config.toml").read_bytes(),
                         toml_before)
        report = self.read_report()
        self.assertEqual(report["backups"], [])
        self.assertEqual(sorted(str(p) for p in self.legacy_backups()),
                         backups_before)
        write_actions = [a for a in report["actions"]
                         if a.get("action") in WRITE_ACTIONS]
        self.assertEqual(write_actions, [], f"第二次运行不应有写动作：{write_actions}")

    def test_second_run_after_user_deletion_restores_and_is_stable(self) -> None:
        self.run_apply()
        document = self.read_mcp_json()
        del document["mcpServers"]["time"]
        self.write_mcp_json(document)
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("time", self.read_mcp_json()["mcpServers"])
        report = self.read_report()
        self.assertIn("MCP_SERVER_RESTORED", json.dumps(report, ensure_ascii=False))
        stable_before = (self.project / ".mcp.json").read_bytes()
        self.run_apply()
        self.assertEqual((self.project / ".mcp.json").read_bytes(), stable_before)
        self.assertEqual(self.read_report()["backups"], [])


class TestSecretSafety(McpConfigTestCase):
    """私密值不外泄。"""

    SECRET = "sk-live-9f8e7d6c5b4a3210-SECRET"

    def test_secret_never_appears_in_report_or_stdout(self) -> None:
        self.write_mcp_json({"mcpServers": {"zai-mcp-server": {
            "type": "stdio", "command": "npx", "args": ["-y", "@z_ai/mcp-server"],
            "env": {"Z_AI_API_KEY": self.SECRET},
        }}})
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report_text = self.report_path.read_text(encoding="utf-8")
        self.assertNotIn(self.SECRET, report_text)
        self.assertNotIn(self.SECRET, proc.stdout)
        self.assertNotIn(self.SECRET, proc.stderr)
        # 用户真实值仍保留在配置文件里。
        env = self.read_mcp_json()["mcpServers"]["zai-mcp-server"]["env"]
        self.assertEqual(env["Z_AI_API_KEY"], self.SECRET)
        # 报告只记录变量名
        self.assertIn("Z_AI_API_KEY", report_text)

    def test_secret_in_header_is_not_echoed(self) -> None:
        self.write_mcp_json({"mcpServers": {"zread": {
            "type": "http", "url": "https://open.bigmodel.cn/api/mcp/zread/mcp",
            "headers": {"Authorization": f"Bearer {self.SECRET}"},
        }}})
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn(self.SECRET, self.report_path.read_text(encoding="utf-8"))
        self.assertNotIn(self.SECRET, proc.stdout)


class TestDegradedPath(McpConfigTestCase):
    """解析失败：不重建、不覆盖。"""

    def test_unparseable_json_is_kept_and_reported(self) -> None:
        broken = "{ this is not json\n"
        (self.project / ".mcp.json").write_text(broken, encoding="utf-8")
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((self.project / ".mcp.json").read_text(encoding="utf-8"),
                         broken)
        report = self.read_report()
        self.assertEqual(report["overall"], "degraded")
        self.assertIn("UNIT_UNPARSEABLE", json.dumps(report, ensure_ascii=False))
        self.assertTrue(report["pending"])
        self.assertEqual(report["backups"], [])

    def test_unparseable_toml_is_kept_and_reported(self) -> None:
        broken = "[mcp_servers.time\ncommand = \n"
        (self.project / ".codex").mkdir()
        (self.project / ".codex" / "config.toml").write_text(broken,
                                                             encoding="utf-8")
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            (self.project / ".codex" / "config.toml").read_text(encoding="utf-8"),
            broken)
        report = self.read_report()
        self.assertEqual(report["overall"], "degraded")
        self.assertIn("UNIT_UNPARSEABLE", json.dumps(report, ensure_ascii=False))


class TestCodexTomlMerge(McpConfigTestCase):
    """`.codex/config.toml` 表块合并。"""

    def test_existing_block_keeps_user_fields(self) -> None:
        toml_text = (
            "[mcp_servers.time]\n"
            "command = \"my-uvx\"\n"
        )
        (self.project / ".codex").mkdir()
        (self.project / ".codex" / "config.toml").write_text(toml_text,
                                                             encoding="utf-8")
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = (self.project / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn('command = "my-uvx"', text)
        self.assertIn("[mcp_servers.context7]", text)
        self.assertIn("[mcp_servers.MiniMax]", text)
        # 缺失字段被补齐
        self.assertIn('args = ["mcp-server-time", "--local-timezone=Asia/Shanghai"]',
                      text)

    def test_missing_server_block_is_appended(self) -> None:
        (self.project / ".codex").mkdir()
        (self.project / ".codex" / "config.toml").write_text(
            "[mcp_servers.context7]\ncommand = \"npx\"\n", encoding="utf-8")
        self.run_apply()
        text = (self.project / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("[mcp_servers.time]", text)
        self.assertIn("[mcp_servers.zai-mcp-server]", text)

    def test_codex_toml_is_idempotent(self) -> None:
        self.run_apply()
        before = (self.project / ".codex" / "config.toml").read_bytes()
        self.run_apply()
        self.assertEqual((self.project / ".codex" / "config.toml").read_bytes(),
                         before)
        self.assertEqual(self.read_report()["backups"], [])


class TestCliContract(McpConfigTestCase):
    """CLI 契约。"""

    def test_usage_error_for_missing_project_root(self) -> None:
        cmd = [sys.executable, str(SCRIPT), "apply",
               "--project-root", str(self.tmp / "nope"),
               "--report", str(self.report_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_report_is_written(self) -> None:
        self.run_apply()
        self.assertTrue(self.report_path.exists())
        report = self.read_report()
        for key in ("overall", "steps", "actions", "backups", "warnings",
                    "pending", "overrides", "failure"):
            self.assertIn(key, report)

    def test_script_does_not_touch_other_directories(self) -> None:
        self.run_apply()
        created = sorted(p.name for p in self.project.iterdir())
        # 无既有文件被改写时不产生归档目录。
        self.assertEqual(created, [".codex", ".gitignore", ".mcp.json"])

    def test_project_type_override(self) -> None:
        proc = self.run_apply("--project-type", "coding")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("codegraph", self.read_mcp_json()["mcpServers"])
        self.assertEqual(self.read_report()["project_type"], "coding")

    def test_existing_formatting_is_not_rewritten(self) -> None:
        """语义无变化时不得因为缩进风格不同而改写用户文件。"""
        data = json.loads(
            (SKILL_DIR / "references" / "required-servers.json")
            .read_text(encoding="utf-8"))
        servers = {
            entry["name"]: entry["config"]
            for entry in data["servers"]
            if "non-coding" in entry["applies_to"]
        }
        text = json.dumps({"mcpServers": servers}, ensure_ascii=False,
                          indent=4) + "\n"
        (self.project / ".mcp.json").write_text(text, encoding="utf-8")
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((self.project / ".mcp.json").read_text(encoding="utf-8"), text)
        self.assertEqual(self.read_report()["backups"], [])

    def test_top_level_extra_keys_are_preserved(self) -> None:
        self.write_mcp_json({"mcpServers": {}, "someOtherTool": {"a": 1}})
        self.run_apply()
        document = self.read_mcp_json()
        self.assertEqual(document["someOtherTool"], {"a": 1})
        self.assertIn("time", document["mcpServers"])


def recipe_report_verdict(tool_output: str) -> str:
    """镜像 cadence-aria `recipe_report_verdict`：带引号的 "overall" 后 64 字符窗口，
    含 failed → failed；含 success 且此前无结论 → success；无字段 → absent。"""
    field, window, verdict = '"overall"', 64, "absent"
    rest = tool_output
    while True:
        index = rest.find(field)
        if index < 0:
            return verdict
        win = rest[index + len(field):][:window]
        if "failed" in win:
            verdict = "failed"
        elif "success" in win and verdict == "absent":
            verdict = "success"
        rest = rest[index + 1:]


class TestStdoutReport(McpConfigTestCase):
    """stdout 收尾报告：单行 JSON，overall ∈ {success, failed}，原摘要行保留。"""

    def last_report(self, stdout: str) -> dict:
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        self.assertTrue(lines and lines[-1].startswith("{"), stdout)
        return json.loads(lines[-1])

    def assert_receipt(self, receipt: dict, *, action: Optional[str],
                       exit_code: int, overall: str) -> None:
        """cadence.skill-receipt/v1 契约断言。"""
        self.assertEqual(receipt["schema"], RECEIPT_SCHEMA)
        self.assertEqual(receipt["skill"], "mcp-configuration")
        self.assertEqual(receipt["action"], action)
        self.assertEqual(receipt["exit_code"], exit_code)
        self.assertEqual(receipt["overall"], overall)
        self.assertIn("run_id", receipt)
        self.assertEqual(list(receipt)[-1], "overall", "overall 必须是最后一个键")

    def test_first_run_reports_success(self) -> None:
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = self.last_report(proc.stdout)
        self.assertEqual(report["overall"], "success")
        self.assertEqual(report["native"], "ok")
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["report"], str(self.report_path))
        self.assertIn("mcp-config: overall=ok", proc.stdout)  # 原摘要行保留
        self.assertEqual(recipe_report_verdict(proc.stdout), "success")
        # 收尾回执契约：动作、run_id、真实退出码；stdout 只有一行 JSON（空格不属契约）。
        self.assert_receipt(report, action="apply", exit_code=0, overall="success")
        self.assertIsNone(report["run_id"])
        self.assertEqual(proc.returncode, report["exit_code"])
        receipt_lines = [ln for ln in proc.stdout.splitlines()
                         if ln.strip().startswith("{")]
        self.assertEqual(len(receipt_lines), 1)

    def test_idempotent_rerun_reports_success(self) -> None:
        self.run_apply()
        before = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        proc = self.run_apply()
        after = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "重跑必须零写入")
        self.assertEqual(self.read_report()["backups"], [])
        self.assertEqual(self.last_report(proc.stdout)["overall"], "success")
        self.assertEqual(recipe_report_verdict(proc.stdout), "success")
        self.assert_receipt(self.last_report(proc.stdout), action="apply",
                             exit_code=0, overall="success")

    def test_degraded_reports_success_with_native_degraded(self) -> None:
        (self.project / ".mcp.json").write_text("{ this is not json\n", encoding="utf-8")
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = self.last_report(proc.stdout)
        self.assertEqual(report["overall"], "success")
        self.assertEqual(report["native"], "degraded")
        self.assertGreaterEqual(report["pending"], 1)
        # degraded 仍是成功收尾：原生取值保留在 native，退出码与进程一致。
        self.assert_receipt(report, action="apply", exit_code=0, overall="success")
        self.assertEqual(proc.returncode, report["exit_code"])

    def test_backup_failure_reports_failed(self) -> None:
        self.write_mcp_json({"mcpServers": {"context7": {
            "type": "stdio", "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"], "env": {},
        }}})
        (self.project / "cadence").mkdir()
        (self.project / "cadence" / "legacy").write_text("占位文件", encoding="utf-8")
        proc = self.run_apply()
        self.assertEqual(proc.returncode, 1, proc.stderr)
        report = self.last_report(proc.stdout)
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["native"], "fail")
        self.assertEqual(report["exit_code"], 1)
        self.assertTrue(report["failure"]["reason"])
        self.assertEqual(recipe_report_verdict(proc.stdout), "failed")
        self.assert_receipt(report, action="apply", exit_code=1, overall="failed")
        self.assertEqual(proc.returncode, report["exit_code"])

    def test_report_write_failure_reports_failed(self) -> None:
        """--report 指向目录：报告写不进去也要给出失败回执，退出码与真实进程一致。"""
        report_dir = self.tmp / "report-dir"
        report_dir.mkdir()
        proc = subprocess.run([sys.executable, str(SCRIPT), "apply",
                               "--project-root", str(self.project),
                               "--report", str(report_dir),
                               "--no-interrupt"],
                              capture_output=True, text=True,
                              env=self.child_env())
        self.assertEqual(proc.returncode, 1, proc.stderr)
        report = self.last_report(proc.stdout)
        self.assert_receipt(report, action="apply", exit_code=1, overall="failed")
        self.assertEqual(report["native"], "fail")
        self.assertEqual(report["failure"]["file"], str(report_dir))
        self.assertTrue(report["failure"]["reason"])
        self.assertEqual(proc.returncode, report["exit_code"])

    def test_report_path_expand_failure_reports_failed(self) -> None:
        """--report 指向 ~不存在的账户：路径展开失败也要给出失败回执。"""
        proc = subprocess.run([sys.executable, str(SCRIPT), "apply",
                               "--project-root", str(self.project),
                               "--report", "~不存在的账户/out",
                               "--no-interrupt"],
                              capture_output=True, text=True,
                              env=self.child_env())
        self.assertEqual(proc.returncode, 1, proc.stderr)
        report = self.last_report(proc.stdout)
        self.assert_receipt(report, action="apply", exit_code=1, overall="failed")
        self.assertEqual(report["native"], "fail")
        self.assertTrue(report["failure"]["reason"])
        self.assertEqual(proc.returncode, report["exit_code"])

    def test_project_root_expand_failure_reports_usage_error(self) -> None:
        """项目根路径展开失败：走 UsageError / 退出码 2，非法 --report 也不得拖垮回执。"""
        cases = [
            (["--project-root", "~不存在的账户/x",
              "--report", str(self.report_path)], str(self.report_path)),
            (["--project-root", str(self.tmp / "nope"),
              "--report", "~不存在的账户/out"], "~不存在的账户/out"),
        ]
        for extra, expected_report in cases:
            with self.subTest(extra=extra):
                proc = subprocess.run([sys.executable, str(SCRIPT), "apply", *extra],
                                      capture_output=True, text=True,
                                      env=self.child_env())
                self.assertEqual(proc.returncode, 2, proc.stderr)
                report = self.last_report(proc.stdout)
                self.assert_receipt(report, action="apply", exit_code=2,
                                     overall="failed")
                self.assertIsNone(report["native"])
                self.assertEqual(report["report"], expected_report)
                self.assertEqual(proc.returncode, report["exit_code"])

    def test_usage_error_reports_failed(self) -> None:
        cmd = [sys.executable, str(SCRIPT), "apply",
               "--project-root", str(self.tmp / "nope"),
               "--report", str(self.report_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              env=self.child_env())
        self.assertEqual(proc.returncode, 2)
        report = self.last_report(proc.stdout)
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["exit_code"], 2)
        # 子命令已解析：动作仍是 apply，退出码与真实进程一致。
        self.assert_receipt(report, action="apply", exit_code=2, overall="failed")
        self.assertEqual(proc.returncode, report["exit_code"])
        self.assertIsNone(report["run_id"])

    def test_usage_error_without_action_reports_null_action(self) -> None:
        """用法错误且无法确定动作：action 为 null。"""
        for argv in ([], ["bogus"]):
            with self.subTest(argv=argv):
                proc = subprocess.run([sys.executable, str(SCRIPT), *argv],
                                      capture_output=True, text=True,
                                      env=self.child_env())
                self.assertEqual(proc.returncode, 2)
                report = self.last_report(proc.stdout)
                self.assert_receipt(report, action=None, exit_code=2,
                                     overall="failed")
                self.assertIsNone(report["run_id"])

    def test_usage_error_inside_subcommand_keeps_action(self) -> None:
        """子命令已选中但参数缺失：动作仍是 apply。"""
        proc = subprocess.run([sys.executable, str(SCRIPT), "apply",
                               "--project-root", str(self.project)],
                              capture_output=True, text=True,
                              env=self.child_env())
        self.assertEqual(proc.returncode, 2)
        report = self.last_report(proc.stdout)
        self.assert_receipt(report, action="apply", exit_code=2, overall="failed")
        self.assertEqual(proc.returncode, report["exit_code"])

    def test_run_id_follows_environment(self) -> None:
        """run_id 取当次环境变量：未设置 null，空串按已设置保留，特殊字符原样保留。

        回执为纯 ASCII：U+2028 / U+0085 不拆行，中文经转义仍可在
        PYTHONIOENCODING=ascii 的终端回传。
        """
        values = ("run-2026", "", 'a"b\\c', "中文\u2028\u2029\u0085run")
        for value in values:
            with self.subTest(run_id=value):
                proc = self.run_apply(env={RUN_ID_ENV: value,
                                           "PYTHONIOENCODING": "ascii"})
                self.assertEqual(proc.returncode, 0, proc.stderr)
                report = self.last_report(proc.stdout)
                self.assertEqual(report["run_id"], value)
                self.assert_receipt(report, action="apply", exit_code=0,
                                     overall="success")

    def test_help_prints_no_report(self) -> None:
        for argv in (["apply", "--help"], ["--help"]):
            with self.subTest(argv=argv):
                proc = subprocess.run([sys.executable, str(SCRIPT), *argv],
                                      capture_output=True, text=True,
                                      env=self.child_env())
                self.assertEqual(proc.returncode, 0)
                self.assertNotIn('"overall"', proc.stdout)
                self.assertNotIn(RECEIPT_SCHEMA, proc.stdout)
                self.assertIn("usage:", proc.stdout)  # 原有帮助不变


if __name__ == "__main__":
    unittest.main()
