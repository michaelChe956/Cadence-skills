#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rule-config `--defer-codegraph-index` 行为测试（配置-only 延迟索引）。

覆盖点：

* defer 生效时只补齐双 MCP 配置（.mcp.json / .codex/config.toml），绝不执行
  任何 codegraph 子命令，索引目录与索引文件字节不变；
* 默认 defer=False 时既有矩阵不变（fresh → install+init；existing → 仅 status）；
* 幂等重跑不产生备份、不重复追加 codex 区块；
* dry-run 零写入且计划标注 deferred；
* 畸形 .mcp.json 保持原文件并降级为 degraded（沿用既有 helper 语义）；
* 备份/发布失败仍抛 PublishError（不降级、不静默吞掉）；
* 真实 CLI 子进程：PATH 上的哨兵 codegraph 可执行文件零调用，退出码 0。
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "rule-config.py"
)

_spec = importlib.util.spec_from_file_location("rule_config_defer", SCRIPT_PATH)
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)


def _intents(**overrides):
    """构造 Intents（默认 defer_codegraph_index=False）。"""
    kwargs = {
        "no_interrupt": False,
        "project_type": None,
        "ignore_cadence": False,
        "enable_playwright": False,
        "enable_codegraph": False,
        "decisions": None,
    }
    kwargs.update(overrides)
    return rc.Intents(**kwargs)


class _FakeRun:
    """记录 codegraph 子命令调用的假 subprocess.run。"""

    def __init__(self, returncode: int = 0):
        self.calls = []
        self.returncode = returncode

    def __call__(self, argv, *args, **kwargs):
        self.calls.append(list(argv))
        return types.SimpleNamespace(
            returncode=self.returncode, stdout="", stderr=""
        )


class DeferredCodegraphIndexTest(unittest.TestCase):
    """`--defer-codegraph-index` 的行为契约。"""

    # ---------------------------------------------------------------- 工具

    def _project(self, coding: bool = True) -> Path:
        """建立临时项目根；coding=True 时放一个 .py 文件触发编码检测。"""
        tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        if coding:
            (root / "main.py").write_text("print('hello')\n", encoding="utf-8")
        return root

    def _plan_report(self, root: Path, intents):
        plan = rc.compute_plan(root, intents)
        report = rc.build_report("normal", root)
        rc._sync_plan_to_report(plan, report, intents)
        return plan, report

    def _step(self, report: dict, name: str) -> dict:
        for step in report.get("steps", []):
            if step.get("name") == name:
                return step
        self.fail(f"报告缺少 step: {name}")

    def _actions(self, report: dict, name: str) -> list:
        return list(self._step(report, name).get("actions") or [])

    @staticmethod
    def _snapshot(root: Path) -> dict:
        return {
            str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }

    # ------------------------------------------------------------ defer 生效

    def test_defer_fresh_project_configures_dual_mcp_without_codegraph_call(self):
        """defer + 新项目：只写双 MCP 配置，codegraph 子命令零调用。"""
        root = self._project(coding=True)
        intents = _intents(defer_codegraph_index=True)
        plan, report = self._plan_report(root, intents)

        fake = _FakeRun()
        with mock.patch.object(rc.subprocess, "run", fake):
            rc.step_s8_codegraph(root, intents, plan, report)

        self.assertEqual(fake.calls, [], "defer 模式不得执行任何 codegraph 子命令")
        mcp = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("codegraph", mcp["mcpServers"])
        toml_text = (root / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("[mcp_servers.codegraph]", toml_text)
        actions = self._actions(report, rc.STEP_CODEGRAPH)
        self.assertTrue(
            any(a.get("branch") == "codegraph-index-deferred" for a in actions),
            f"缺少 deferred 动作记录: {actions}",
        )
        self.assertEqual(report["overall"], "ok")
        self.assertFalse((root / ".codegraph").exists(), "defer 不得创建索引目录")

    def test_defer_existing_index_files_are_untouched(self):
        """defer + 既有 .codegraph/：索引文件字节不变，且不新增文件。"""
        root = self._project(coding=True)
        index_dir = root / ".codegraph"
        index_dir.mkdir()
        (index_dir / "index.db").write_bytes(b"\x00IDX-BINARY\xff")
        (index_dir / "meta.json").write_text('{"built":true}\n', encoding="utf-8")
        before = self._snapshot(index_dir)

        intents = _intents(defer_codegraph_index=True)
        plan, report = self._plan_report(root, intents)
        fake = _FakeRun()
        with mock.patch.object(rc.subprocess, "run", fake):
            rc.step_s8_codegraph(root, intents, plan, report)

        self.assertEqual(fake.calls, [], "defer 模式不得执行 status/install/init")
        self.assertEqual(self._snapshot(index_dir), before, "索引文件不得被改动")
        self.assertTrue(
            any(
                a.get("branch") == "codegraph-index-deferred"
                for a in self._actions(report, rc.STEP_CODEGRAPH)
            )
        )
        mcp = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("codegraph", mcp["mcpServers"])

    def test_defer_keeps_existing_user_mcp_entries(self):
        """defer 不破坏用户既有 MCP 配置（.mcp.json 与 .codex/config.toml）。"""
        root = self._project(coding=True)
        (root / ".mcp.json").write_text(
            json.dumps(
                {"mcpServers": {"context7": {"command": "npx", "args": ["-y"]}}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (root / ".codex").mkdir()
        (root / ".codex" / "config.toml").write_text(
            'model = "gpt-5"\n', encoding="utf-8"
        )

        intents = _intents(defer_codegraph_index=True)
        plan, report = self._plan_report(root, intents)
        fake = _FakeRun()
        with mock.patch.object(rc.subprocess, "run", fake):
            rc.step_s8_codegraph(root, intents, plan, report)

        mcp = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("context7", mcp["mcpServers"])
        self.assertIn("codegraph", mcp["mcpServers"])
        toml_text = (root / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn('model = "gpt-5"', toml_text)
        self.assertIn("[mcp_servers.codegraph]", toml_text)
        self.assertEqual(fake.calls, [])

    def test_defer_rerun_is_idempotent_without_backups(self):
        """defer 重跑幂等：不产生备份、不重复追加 codex 区块。"""
        root = self._project(coding=True)
        intents = _intents(defer_codegraph_index=True)

        plan1, report1 = self._plan_report(root, intents)
        fake = _FakeRun()
        with mock.patch.object(rc.subprocess, "run", fake):
            rc.step_s8_codegraph(root, intents, plan1, report1)
        first_mcp = (root / ".mcp.json").read_bytes()
        first_toml = (root / ".codex" / "config.toml").read_bytes()

        plan2, report2 = self._plan_report(root, intents)
        with mock.patch.object(rc.subprocess, "run", _FakeRun()):
            rc.step_s8_codegraph(root, intents, plan2, report2)

        self.assertEqual((root / ".mcp.json").read_bytes(), first_mcp)
        self.assertEqual((root / ".codex" / "config.toml").read_bytes(), first_toml)
        self.assertEqual(
            (root / ".codex" / "config.toml")
            .read_text(encoding="utf-8")
            .count("[mcp_servers.codegraph]"),
            1,
            "重跑不得重复追加 codex 区块",
        )
        self.assertEqual(
            report2.get("backups") or [], [], "幂等重跑不得产生备份"
        )
        self.assertEqual(fake.calls, [])

    # ------------------------------------------------------------ 默认行为

    def test_default_defer_flag_is_false(self):
        """默认不启用 defer。"""
        self.assertFalse(_intents().defer_codegraph_index)
        self.assertFalse(rc.Intents(False, None, False, False, False, None)
                         .defer_codegraph_index)

    def test_default_fresh_project_runs_install_then_init(self):
        """默认（defer=False）新项目仍走 install → init。"""
        root = self._project(coding=True)
        intents = _intents()
        plan, report = self._plan_report(root, intents)

        fake = _FakeRun()
        with mock.patch.object(rc.subprocess, "run", fake):
            rc.step_s8_codegraph(root, intents, plan, report)

        self.assertTrue(fake.calls, "默认路径必须调用 codegraph")
        self.assertEqual(fake.calls[0][:2], ["codegraph", "install"])
        self.assertTrue(
            any(call[1] == "init" for call in fake.calls),
            f"默认路径缺少 init: {fake.calls}",
        )

    def test_default_existing_index_runs_status_only(self):
        """默认（defer=False）既有 .codegraph/ 只跑 status，不重复 install/init。"""
        root = self._project(coding=True)
        (root / ".codegraph").mkdir()
        (root / ".codegraph" / "index.db").write_bytes(b"IDX")

        intents = _intents()
        plan, report = self._plan_report(root, intents)
        fake = _FakeRun()
        with mock.patch.object(rc.subprocess, "run", fake):
            rc.step_s8_codegraph(root, intents, plan, report)

        self.assertTrue(
            any(call[1] == "status" for call in fake.calls),
            f"既有索引路径缺少 status: {fake.calls}",
        )
        self.assertFalse(
            any(call[1] in ("install", "init") for call in fake.calls),
            f"既有索引路径不得重复 install/init: {fake.calls}",
        )

    # ---------------------------------------------------------- 跳过与组合

    def test_noncoding_project_is_skipped_even_with_defer(self):
        """非编码项目且未显式 enable：S8 整体跳过（defer 不改变该前提）。"""
        root = self._project(coding=False)
        intents = _intents(defer_codegraph_index=True)
        plan, report = self._plan_report(root, intents)

        fake = _FakeRun()
        with mock.patch.object(rc.subprocess, "run", fake):
            rc.step_s8_codegraph(root, intents, plan, report)

        actions = self._actions(report, rc.STEP_CODEGRAPH)
        self.assertTrue(
            any(a.get("branch") == "codegraph-skip" for a in actions),
            f"非编码项目应跳过 S8: {actions}",
        )
        self.assertEqual(fake.calls, [])
        self.assertFalse((root / ".mcp.json").exists())

    def test_noncoding_with_explicit_enable_and_defer_only_configures(self):
        """非编码 + --enable-codegraph + defer：只配置，不建索引。"""
        root = self._project(coding=False)
        intents = _intents(enable_codegraph=True, defer_codegraph_index=True)
        plan, report = self._plan_report(root, intents)

        fake = _FakeRun()
        with mock.patch.object(rc.subprocess, "run", fake):
            rc.step_s8_codegraph(root, intents, plan, report)

        self.assertEqual(fake.calls, [])
        mcp = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("codegraph", mcp["mcpServers"])
        actions = self._actions(report, rc.STEP_CODEGRAPH)
        self.assertTrue(
            any(a.get("branch") == "codegraph-index-deferred" for a in actions),
            f"缺少 deferred 动作记录: {actions}",
        )

    # ---------------------------------------------------------------- dry-run

    def test_dry_run_writes_nothing_and_marks_deferred_plan(self):
        """dry-run 零写入，且计划标注 deferred。"""
        root = self._project(coding=True)
        intents = _intents(defer_codegraph_index=True)
        report = rc.build_report("normal", root)

        exit_code = rc.run_dry_run(root, intents, report)

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["overall"], "ok")
        step = self._step(report, rc.STEP_CODEGRAPH)
        assets = step.get("assets") or []
        self.assertTrue(
            any(a.get("action") == "deferred" for a in assets),
            f"dry-run 计划缺少 deferred 标注: {assets}",
        )
        self.assertIn(
            "codegraph-index-deferred", step.get("reason") or "",
            f"dry-run 步骤说明缺少 deferred 标注: {step.get('reason')}",
        )
        self.assertFalse((root / ".mcp.json").exists(), "dry-run 不得写入 .mcp.json")
        self.assertFalse((root / ".codex").exists(), "dry-run 不得写入 .codex/")
        self.assertFalse((root / ".claude").exists(), "dry-run 不得写入 .claude/")

    # ------------------------------------------------------------ 失败语义

    def test_malformed_mcp_json_is_preserved_and_degraded(self):
        """畸形 .mcp.json：原文件保持不变，整体降级为 degraded。"""
        root = self._project(coding=True)
        raw = "{ this is not json\n"
        (root / ".mcp.json").write_text(raw, encoding="utf-8")

        intents = _intents(defer_codegraph_index=True)
        plan, report = self._plan_report(root, intents)
        fake = _FakeRun()
        with mock.patch.object(rc.subprocess, "run", fake):
            rc.step_s8_codegraph(root, intents, plan, report)

        self.assertEqual(
            (root / ".mcp.json").read_text(encoding="utf-8"), raw,
            "畸形 .mcp.json 必须原样保留",
        )
        self.assertEqual(report["overall"], "degraded")
        codes = [w.get("code") for w in report.get("warnings") or []]
        self.assertIn("UNIT_UNPARSEABLE", codes)
        self.assertEqual(fake.calls, [])

    def test_backup_failure_still_raises_publish_error(self):
        """配置补写前备份失败：抛 PublishError，且步骤动作/耗时仍被记录。"""
        root = self._project(coding=True)
        (root / ".codex").mkdir()
        (root / ".codex" / "config.toml").write_text(
            'model = "gpt-5"\n', encoding="utf-8"
        )
        (root / ".mcp.json").write_text(
            json.dumps({"mcpServers": {}}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        intents = _intents(defer_codegraph_index=True)
        plan, report = self._plan_report(root, intents)

        real_backup = rc.backup_file
        counter = {"n": 0}

        def _flaky_backup(*args, **kwargs):
            counter["n"] += 1
            if counter["n"] == 1:
                return real_backup(*args, **kwargs)
            raise rc.BackupError("注入的备份失败")

        with mock.patch.object(rc, "backup_file", side_effect=_flaky_backup):
            with self.assertRaises(rc.PublishError):
                rc.step_s8_codegraph(root, intents, plan, report)

        step = self._step(report, rc.STEP_CODEGRAPH)
        self.assertIn("elapsed_ms", step)
        self.assertTrue(
            step.get("actions"), "失败路径仍须记录已执行动作"
        )

    def test_publish_failure_still_raises_publish_error(self):
        """原子发布失败：抛 PublishError（不降级、不静默）。"""
        root = self._project(coding=True)
        (root / ".codex").mkdir()
        (root / ".codex" / "config.toml").write_text(
            'model = "gpt-5"\n', encoding="utf-8"
        )
        (root / ".mcp.json").write_text(
            json.dumps({"mcpServers": {}}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        intents = _intents(defer_codegraph_index=True)
        plan, report = self._plan_report(root, intents)

        def _flaky_write(path, content):
            if path == root / ".mcp.json":
                raise rc.PublishError("注入的发布失败")
            return real_atomic_write(path, content)

        real_atomic_write = rc.atomic_write
        with mock.patch.object(rc, "atomic_write", side_effect=_flaky_write):
            with self.assertRaises(rc.PublishError):
                rc.step_s8_codegraph(root, intents, plan, report)

        step = self._step(report, rc.STEP_CODEGRAPH)
        self.assertIn("elapsed_ms", step)
        self.assertIn("[mcp_servers.codegraph]", (root / ".codex/config.toml").read_text())
        self.assertEqual(json.loads((root / ".mcp.json").read_text()), {"mcpServers": {}})
        self.assertTrue(any(a.get("branch") == "codex-mcp-patched" for a in step["actions"]))

    # ------------------------------------------------------------- CLI 端到端

    def test_cli_defer_never_invokes_codegraph_binary(self):
        """真实 CLI：PATH 上的哨兵 codegraph 零调用，整体成功。"""
        root = self._project(coding=True)
        bin_dir = Path(tempfile.mkdtemp(dir="/tmp"))
        self.addCleanup(shutil.rmtree, bin_dir, ignore_errors=True)
        marker = bin_dir / "codegraph-invoked.marker"
        sentinel = bin_dir / "codegraph"
        sentinel.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$*\" >> '" + str(marker) + "'\nexit 0\n",
            encoding="utf-8",
        )
        sentinel.chmod(0o755)

        report_dir = Path(tempfile.mkdtemp(dir="/tmp"))
        self.addCleanup(shutil.rmtree, report_dir, ignore_errors=True)
        report_path = report_dir / "report.json"

        env = os.environ.copy()
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")

        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "apply",
                "--project-root",
                str(root),
                "--report",
                str(report_path),
                "--defer-codegraph-index",
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd="/tmp",
        )

        self.assertEqual(
            proc.returncode, 0,
            f"CLI 应成功退出；stdout={proc.stdout}\nstderr={proc.stderr}",
        )
        self.assertFalse(
            marker.exists(), "defer 模式不得调用 codegraph 可执行文件"
        )
        self.assertTrue(report_path.is_file(), "CLI 必须写出报告")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertIn(report["overall"], {"ok", "degraded"})
        self.assertFalse(report.get("failure"), f"CLI 报告失败: {report.get('failure')}")
        s8 = None
        for step in report.get("steps", []):
            if step.get("name") == rc.STEP_CODEGRAPH:
                s8 = step
        self.assertIsNotNone(s8, "报告缺少 s8_codegraph 步骤")
        branches = [
            a.get("branch") for a in (s8.get("actions") or []) if isinstance(a, dict)
        ]
        self.assertIn("codegraph-index-deferred", branches)
        self.assertNotIn("codegraph-install", branches)
        self.assertNotIn("codegraph-existing", branches)
        mcp = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("codegraph", mcp["mcpServers"])


if __name__ == "__main__":
    unittest.main()
