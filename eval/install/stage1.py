"""阶段一安装流水线：四 command 依序 headless 调用 + 断言表 + --verify 消费。"""
import hashlib
import json
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

REAL_STAGE1_ARGV_EXTRA = {
    # 安装阶段全放行：deny 尚未安装/安装流程不依赖 deny；敏感文件（.mcp.json）
    # 与 Write 工具拦截均已消除。deny 测试点在探针阶段（PROBE_ARGV_EXTRA）。
    "claude": ["--dangerously-skip-permissions"],
    # codex/pi/kimi 的真实策略属首夜 Runbook 核定项，claude 先行。
    "codex": [],
    "pi": [],
    "kimi": [],
}


def _tree_hash(directory: Path) -> dict:
    out = {}
    if directory.is_dir():
        for p in sorted(directory.rglob("*")):
            if p.is_file():
                out[str(p.relative_to(directory))] = \
                    hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _extract_precheck_report(text: str):
    """从终文本扫描完整 JSON object；任意解析失败安全返回 ``None``。"""
    if not isinstance(text, str):
        return None
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _end = decoder.raw_decode(text[index:])
        except ValueError:
            continue
        if isinstance(value, dict) and isinstance(value.get("phases"), list):
            return value
    return None


def _count_tool_calls(transcript_path: str) -> int:
    """仅统计 transcript 中的 ``tool_use`` 事件，不计脚本内部子命令。"""
    if not transcript_path:
        return 0
    count = 0
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                message = event.get("message") if isinstance(event, dict) else None
                content = message.get("content") if isinstance(message, dict) else None
                if isinstance(content, list):
                    count += sum(1 for item in content
                                 if isinstance(item, dict) and item.get("type") == "tool_use")
    except OSError:
        return 0
    return count


def _is_precheck_home_target(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    return (rel.startswith(".agents/superpowers/") or rel == ".agents/superpowers"
            or rel.startswith(".agents/skills/") or rel.startswith(".codex/skills/skills/")
            or rel.startswith(".claude/skills/") or rel.startswith(".pi/agent/skills/")
            or rel.startswith(".claude/commands/opsx/") or rel.startswith(".claude/skills/openspec-")
            or rel.startswith(".agents/skills/openspec-") or rel.startswith(".pi/skills/")
            or rel.startswith(".pi/prompts/") or rel.startswith(".kimi-code/skills/openspec-"))


def _snapshot_precheck_home(home: Path) -> dict:
    """HOME 非目标文件快照；投影、Superpowers 源与四层链接不纳入漂移比较。"""
    home = Path(home)
    snap = {}
    if not home.is_dir():
        return snap
    for path in sorted(home.rglob("*")):
        if not (path.is_file() or path.is_symlink()):
            continue
        rel = path.relative_to(home).as_posix()
        if _is_precheck_home_target(rel):
            continue
        try:
            snap[rel] = ("link:" + str(path.readlink()) if path.is_symlink()
                         else hashlib.sha256(path.read_bytes()).hexdigest())
        except OSError:
            snap[rel] = "unreadable"
    return snap


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
               verify=None, bin_dir=None, skill_env=None, pre_check_timeout_s=240):
    variant, outside_baseline = _detect_variant(fixture.root)
    root, home, repo = fixture.root, fixture.home, fixture.repo
    verify = verify or _default_verify(repo)
    extra: dict = {}
    commands_report = []
    real_cli = cli is proc.run_cli
    precheck_home_before = _snapshot_precheck_home(home)
    for spec in STAGE1_COMMANDS:
        before = _tree_hash(root)
        cli_kwargs = {
            "cwd": root,
            "home": None if skill_env else home,
            "pins": pins,
            "timeout_s": pre_check_timeout_s if spec["name"] == "pre-check" else timeout_s,
            "env_extra": {"EVAL_STAGE": "stage1", "EVAL_COMMAND": spec["name"]},
            "bin_dir": bin_dir,
            "skill_env": skill_env,
        }
        if real_cli:
            cli_kwargs["argv_extra"] = list(REAL_STAGE1_ARGV_EXTRA.get(agent) or [])
            # agents.json 的 argv_extra（如 kimi 的 --skills-dir）也追加
            from eval.runner.night import _resolved_argv_extra as _rae
            from eval.runner import guards as _guards
            try:
                _cfg = _guards.load_config(fixture.repo / "eval" / "config" / "agents.json")
                cli_kwargs["argv_extra"].extend(_rae(_cfg, agent, fixture))
            except Exception:
                pass
        out = cli(agent, spec["prompt"], **cli_kwargs)
        final_text = proc.extract_final_text(agent, out.get("transcript_path") or "")
        if spec["name"] == "pre-check":
            extra["pre_check_clean"] = asrt._non_target_tree_hash(before, root) == asrt._non_target_tree_hash(_tree_hash(root), root)
            extra["pre_check_report"] = _extract_precheck_report(final_text)
            extra["pre_check_tool_calls"] = _count_tool_calls(out.get("transcript_path") or "")
            extra["pre_check_duration_s"] = float(out.get("duration_s", 0.0))
            extra["pre_check_home"] = {"path": str(home),
                                        "before": precheck_home_before,
                                        "after": _snapshot_precheck_home(home)}
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
