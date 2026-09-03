"""阶段一安装流水线：四 command 依序 headless 调用 + 断言表 + --verify 消费。"""
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

from eval.fixtures import generator as gen
from eval.install import assertions as asrt
from eval.install.commands import STAGE1_COMMANDS
from eval.runner import proc

V3_BLOCK_RE = re.compile(
    r"<!-- cadence-managed:openspec-superpowers-routing:v3:start -->.*?v3:end -->", re.S)


def _tree_hash(directory: Path) -> dict:
    out = {}
    if directory.is_dir():
        for p in sorted(directory.rglob("*")):
            if p.is_file():
                out[str(p.relative_to(directory))] = \
                    hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _default_verify(repo: Path) -> Callable[[Path], int]:
    script = repo / "cadence-init/skills/rule-config/scripts/rule-config.py"

    def verify(root: Path) -> int:
        report_fd, report_name = tempfile.mkstemp(
            dir=str(root.resolve().parent), prefix=".eval-verify-", suffix=".json")
        report_path = Path(report_name)
        try:
            return subprocess.run(
                [sys.executable, str(script), "--verify", "--project-root", str(root),
                 "--report", str(report_path)],
                capture_output=True, text=True, shell=False).returncode
        finally:
            # rule-config 要求 --report 位于项目根外；临时报告只用于消费退出码。
            try:
                os.close(report_fd)
            except OSError:
                pass
            report_path.unlink(missing_ok=True)
    return verify


def _detect_variant(root: Path) -> tuple:
    """由 workspace 现状推断变体（fresh/v3/mcp_pre）与 v3 区块外基线。"""
    if (root / "CLAUDE.md").is_file():
        text = (root / "CLAUDE.md").read_text(encoding="utf-8")
        m = V3_BLOCK_RE.search(text)
        if m:
            return "v3", text.replace(m.group(0), "")
    if (root / ".mcp.json").is_file():
        raw = (root / ".mcp.json").read_text(encoding="utf-8")
        if "existing-server" in raw:
            return "mcp_pre", None
    return "fresh", None


def run_stage1(agent, fixture, pins, timeout_s=1200, *, cli=proc.run_cli,
               verify=None, bin_dir=None, skill_env=None):
    variant, outside_baseline = _detect_variant(fixture.root)
    root, home, repo = fixture.root, fixture.home, fixture.repo
    verify = verify or _default_verify(repo)
    extra: dict = {}
    commands_report = []
    for spec in STAGE1_COMMANDS:
        before = _tree_hash(root)
        out = cli(agent, spec["prompt"], cwd=root,
                  home=None if skill_env else home, pins=pins,
                  timeout_s=timeout_s,
                  env_extra={"EVAL_STAGE": "stage1", "EVAL_COMMAND": spec["name"]},
                  bin_dir=bin_dir, skill_env=skill_env)
        final_text = proc.extract_final_text(agent, out.get("transcript_path") or "")
        if spec["name"] == "pre-check":
            extra["pre_check_clean"] = before == _tree_hash(root)
        if spec["name"] == "rule-config":
            extra["rules_before"] = _tree_hash(root / ".claude" / "rules")
        commands_report.append({"name": spec["name"], "returncode": out["returncode"],
                                "duration_s": out["duration_s"], "final_text": final_text})
    verify_exit = verify(root)
    if outside_baseline is not None:
        extra["outside_l0_baseline"] = outside_baseline
    results = asrt.assert_stage1(variant, root, verify_exit,
                                 {c["name"]: c["final_text"] for c in commands_report},
                                 extra)
    return {"variant": variant, "agent": agent, "commands": commands_report,
            "verify_exit": verify_exit,
            "assertions": [{"name": r.name, "ok": r.ok, "detail": r.detail} for r in results],
            "ok": all(r.ok for r in results) and verify_exit == 0}
