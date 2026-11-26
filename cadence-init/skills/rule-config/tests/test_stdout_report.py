#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rule-config stdout 收尾报告契约测试（unittest，真实子进程）。

契约：非 `--json` 运行在 stdout 最后一行输出单行 JSON，
`"overall"` 取值 success（退出码 0）/ failed（非 0），且为最后一个键；
原生三值（ok/degraded/fail）与 verify 的 healthy/drift 在 `native`。
`verify --json` 的 stdout 必须保持为单个完整 JSON 文档（不追加收尾行）。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "rule-config.py"


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


class StdoutReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="failed-rc-stdout-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.project = self.tmp / "project"
        self.project.mkdir()
        self.report_path = self.tmp / "report.json"
        home = self.tmp / "home"
        home.mkdir()
        self.env = dict(os.environ, HOME=str(home))
        self.env.pop("CADENCE_SKILL_RUN_ID", None)

    def run_rc(self, *args: str, env: dict | None = None,
               no_bytecode: bool = False) -> subprocess.CompletedProcess:
        cmd = [sys.executable]
        if no_bytecode:
            cmd.append("-B")
        cmd.extend([str(SCRIPT), *args, "--project-root", str(self.project),
                    "--report", str(self.report_path)])
        return subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                              timeout=60, env={**self.env, **(env or {})})

    def receipt(self, proc: subprocess.CompletedProcess, action: str | None,
                run_id: str | None = None) -> dict:
        report = json.loads(proc.stdout.splitlines()[-1])
        self.assertEqual(list(report)[-1], "overall")
        self.assertEqual(report["schema"], "cadence.skill-receipt/v1")
        self.assertEqual(report["skill"], "rule-config")
        self.assertEqual(report["action"], action)
        self.assertEqual(report["run_id"], run_id)
        self.assertIs(type(report["exit_code"]), int)
        self.assertEqual(report["exit_code"], proc.returncode)
        return report

    def snapshot(self) -> dict:
        return {p.relative_to(self.project): (p.read_bytes(), p.lstat().st_mtime_ns)
                for p in self.project.rglob("*") if p.is_file()}

    def test_dry_run_then_apply_distinguishes_success_on_same_project(self) -> None:
        preview = self.run_rc("dry-run", "--no-interrupt")
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(self.receipt(preview, "dry-run")["overall"], "success")
        self.assertEqual(self.snapshot(), {})

        proc = self.run_rc("apply", "--no-interrupt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((self.project / "CLAUDE.md").is_file())
        report = self.receipt(proc, "apply")
        self.assertEqual(report["overall"], "success")
        self.assertEqual(report["native"], "ok")
        self.assertEqual(report["report"], str(self.report_path))
        self.assertEqual(recipe_report_verdict(proc.stdout), "success")

    def test_idempotent_rerun_reports_success_and_writes_nothing(self) -> None:
        first_id = "工单\u2028一"
        first = self.run_rc("apply", "--no-interrupt",
                            env={"CADENCE_SKILL_RUN_ID": first_id, "PYTHONIOENCODING": "ascii"})
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(self.receipt(first, "apply", first_id)["overall"], "success")
        before = self.snapshot()
        proc = self.run_rc("apply", "--no-interrupt", no_bytecode=True,
                           env={"CADENCE_SKILL_RUN_ID": "overall"})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(before, self.snapshot(), "重跑必须零写入")
        self.assertEqual(self.receipt(proc, "apply", "overall")["overall"], "success")
        self.assertEqual(recipe_report_verdict(proc.stdout), "success")

    def test_remove_permission_gate_reports_action_and_empty_run_id(self) -> None:
        proc = self.run_rc("--remove-permission-gate", env={"CADENCE_SKILL_RUN_ID": ""})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.receipt(proc, "remove-permission-gate", "")["overall"], "success")

    def test_verify_healthy_keeps_lines_and_reports_success(self) -> None:
        self.run_rc("apply", "--no-interrupt")
        proc = self.run_rc("verify")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("[ok] l0_version CLAUDE.md", proc.stdout)  # 原逐行输出保留
        report = self.receipt(proc, "verify")
        self.assertEqual(report["overall"], "success")
        self.assertEqual(report["native"], "healthy")

    def test_verify_drift_reports_failed(self) -> None:
        proc = self.run_rc("--verify")  # 空项目：入口/规则缺失 ⇒ drift
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[drift]", proc.stdout)
        report = self.receipt(proc, "verify")
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["native"], "drift")
        self.assertEqual(report["exit_code"], 1)
        self.assertEqual(recipe_report_verdict(proc.stdout), "failed")

    def test_verify_json_stdout_stays_single_json_document(self) -> None:
        self.run_rc("apply", "--no-interrupt")
        proc = self.run_rc("verify", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)  # 追加收尾行会导致整体解析失败
        self.assertEqual(payload, json.loads(self.report_path.read_text(encoding="utf-8")))
        self.assertNotIn("schema", payload)
        self.assertEqual(payload["overall"], "healthy")

    def test_help_only_prints_usage(self) -> None:
        proc = self.run_rc("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--project-root", proc.stdout)
        self.assertNotIn('"overall"', proc.stdout)
        self.assertFalse(self.report_path.exists())

    def test_backup_barrier_failure_reports_failed(self) -> None:
        (self.project / "CLAUDE.md").write_text("# CLAUDE.md\n\n自定义内容\n", encoding="utf-8")
        (self.project / "cadence").mkdir()
        (self.project / "cadence" / "legacy").write_text("占位文件", encoding="utf-8")
        proc = self.run_rc("apply", "--no-interrupt")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        report = self.receipt(proc, "apply")
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["native"], "fail")
        self.assertEqual(report["exit_code"], 1)
        self.assertIn("备份屏障失败", report["failure"]["reason"])
        self.assertEqual(recipe_report_verdict(proc.stdout), "failed")

    def test_missing_mode_exit_2_reports_failed(self) -> None:
        proc = self.run_rc()
        self.assertEqual(proc.returncode, 2)
        report = self.receipt(proc, None)
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["exit_code"], 2)

    def test_report_inside_project_root_exit_2_reports_failed(self) -> None:
        self.report_path = self.project / "report.json"
        proc = self.run_rc("apply", env={"CADENCE_SKILL_RUN_ID": "run-42"})
        self.assertEqual(proc.returncode, 2, proc.stderr)
        report = self.receipt(proc, "apply", "run-42")
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["report"], str(self.report_path))
        self.assertEqual(report["failure"]["file"], str(self.report_path))
        self.assertIn("项目根", report["failure"]["reason"])
        self.assertFalse(self.report_path.exists())

    def test_unknown_flag_exit_2_reports_failed(self) -> None:
        proc = self.run_rc("apply", "--bogus-flag")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.receipt(proc, "apply")["overall"], "failed")

    def test_conflicting_actions_have_no_unique_action(self) -> None:
        proc = self.run_rc("dry-run", "--verify")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.receipt(proc, None)["overall"], "failed")

    def test_missing_pyyaml_exit_77_reports_failed(self) -> None:
        shim = self.tmp / "shim"
        shim.mkdir()
        (shim / "yaml.py").write_text("raise ImportError('shim: no yaml')\n", encoding="utf-8")
        env = {"PYTHONPATH": str(shim)}
        for action in ("apply", None):
            with self.subTest(action=action):
                self.report_path = self.tmp / f"{action}.json"
                proc = self.run_rc(*([action] if action else []), env=env)
                self.assertEqual(proc.returncode, 77, proc.stderr)
                receipt = self.receipt(proc, action)
                self.assertEqual(receipt["overall"], "failed")
                self.assertIn("PyYAML", receipt["failure"]["reason"])
                saved = json.loads(self.report_path.read_text(encoding="utf-8"))
                self.assertEqual(receipt["failure"], saved["failure"])

        proc = self.run_rc("verify", "--json", env=env)
        self.assertEqual(proc.returncode, 77, proc.stderr)
        native = json.loads(proc.stdout)
        self.assertEqual(native["mode"], "verify")
        self.assertEqual(native["exit_code"], 77)
        self.assertEqual(native["checks"], [])
        self.assertIn("PyYAML", native["failure"]["reason"])


if __name__ == "__main__":
    unittest.main()
