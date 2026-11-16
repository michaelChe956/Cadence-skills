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
        self.tmp = Path(tempfile.mkdtemp(prefix="rc-stdout-report-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.project = self.tmp / "project"
        self.project.mkdir()
        self.report_path = self.tmp / "report.json"

    def run_rc(self, *args: str, env: dict | None = None,
               root: Path | None = None) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(SCRIPT), *args,
               "--project-root", str(root or self.project),
               "--report", str(self.report_path)]
        return subprocess.run(cmd, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=300, env=env)

    def last_report(self, stdout: str) -> dict:
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        self.assertTrue(lines and lines[-1].startswith("{"), f"末行必须是报告 JSON：{stdout!r}")
        return json.loads(lines[-1])

    def snapshot(self) -> dict:
        return {str(p): p.read_bytes() for p in self.project.rglob("*") if p.is_file()}

    def test_apply_reports_success(self) -> None:
        proc = self.run_rc("apply", "--no-interrupt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = self.last_report(proc.stdout)
        self.assertEqual(report["overall"], "success")
        self.assertEqual(report["native"], "ok")
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["report"], str(self.report_path))
        self.assertEqual(recipe_report_verdict(proc.stdout), "success")

    def test_idempotent_rerun_reports_success_and_writes_nothing(self) -> None:
        self.assertEqual(self.run_rc("apply", "--no-interrupt").returncode, 0)
        before = self.snapshot()
        proc = self.run_rc("apply", "--no-interrupt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(before, self.snapshot(), "重跑必须零写入")
        self.assertEqual(self.last_report(proc.stdout)["overall"], "success")
        self.assertEqual(recipe_report_verdict(proc.stdout), "success")

    def test_dry_run_reports_success(self) -> None:
        proc = self.run_rc("dry-run", "--no-interrupt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.last_report(proc.stdout)["overall"], "success")

    def test_verify_healthy_keeps_lines_and_reports_success(self) -> None:
        self.run_rc("apply", "--no-interrupt")
        proc = self.run_rc("verify")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("[ok] l0_version CLAUDE.md", proc.stdout)  # 原逐行输出保留
        report = self.last_report(proc.stdout)
        self.assertEqual(report["overall"], "success")
        self.assertEqual(report["native"], "healthy")

    def test_verify_drift_reports_failed(self) -> None:
        proc = self.run_rc("verify")  # 空项目：入口/规则缺失 ⇒ drift
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[drift]", proc.stdout)
        report = self.last_report(proc.stdout)
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["native"], "drift")
        self.assertEqual(report["exit_code"], 1)
        self.assertEqual(recipe_report_verdict(proc.stdout), "failed")

    def test_verify_json_stdout_stays_single_json_document(self) -> None:
        self.run_rc("apply", "--no-interrupt")
        proc = self.run_rc("verify", "--json")
        payload = json.loads(proc.stdout)  # 不得追加收尾行，否则整体解析失败
        self.assertEqual(payload["overall"], "healthy")

    def test_backup_barrier_failure_reports_failed(self) -> None:
        (self.project / "CLAUDE.md").write_text("# CLAUDE.md\n\n自定义内容\n", encoding="utf-8")
        (self.project / "cadence").mkdir()
        (self.project / "cadence" / "legacy").write_text("占位文件", encoding="utf-8")
        proc = self.run_rc("apply", "--no-interrupt")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        report = self.last_report(proc.stdout)
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["native"], "fail")
        self.assertEqual(report["exit_code"], 1)
        self.assertIn("备份屏障失败", report["failure"]["reason"])
        self.assertEqual(recipe_report_verdict(proc.stdout), "failed")

    def test_missing_mode_exit_2_reports_failed(self) -> None:
        proc = self.run_rc()
        self.assertEqual(proc.returncode, 2)
        report = self.last_report(proc.stdout)
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["exit_code"], 2)

    def test_report_inside_project_root_exit_2_reports_failed(self) -> None:
        cmd = [sys.executable, str(SCRIPT), "apply", "--project-root", str(self.project),
               "--report", str(self.project / "report.json")]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.last_report(proc.stdout)["overall"], "failed")

    def test_unknown_flag_exit_2_reports_failed(self) -> None:
        proc = self.run_rc("apply", "--bogus-flag")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.last_report(proc.stdout)["overall"], "failed")

    def test_missing_pyyaml_exit_77_reports_failed(self) -> None:
        shim = self.tmp / "shim"
        shim.mkdir()
        (shim / "yaml.py").write_text("raise ImportError('shim: no yaml')\n", encoding="utf-8")
        import os
        env = dict(os.environ, PYTHONPATH=str(shim))
        proc = self.run_rc("apply", "--no-interrupt", env=env)
        self.assertEqual(proc.returncode, 77, proc.stderr)
        report = self.last_report(proc.stdout)
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["exit_code"], 77)
        self.assertIn("PyYAML", report["failure"]["reason"])


if __name__ == "__main__":
    unittest.main()
