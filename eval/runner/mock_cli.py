"""mock 四端 CLI：罐头产物 + 罐头轨迹（Tier-0 冒烟与 Tier-1 付费前自检）。

只验证 harness 管线（argv/env/捕获/断言/报告），不验证 skill 语义——
skill 语义归 Tier-1 真实端。行为由 env 驱动：
  EVAL_STAGE=stage1|probe   EVAL_PROBE_ID=P1..P8
  EVAL_COMMAND=pre-check|rule-config|mcp-configuration|project-rules-examples
（阶段一按 command 名分支：pre-check 只产诊断报告零写盘，其余各写各自产物）
"""
import argparse
import re as _re
import json
import os
import sys
from pathlib import Path

# 单一事实源：与 fixture 期望清单同源（generator.RULES_FILES），防两处漂移。
from eval.fixtures.generator import RULES_FILES

V3_BLOCK_RE = _re.compile(
    r"<!-- cadence-managed:openspec-superpowers-routing:v3:start -->.*?v3:end -->",
    _re.S)


def _emit(lines):
    for ln in lines:
        sys.stdout.write(json.dumps(ln, ensure_ascii=False) + "\n")


def _stage1_pre_check(cwd: Path) -> dict:
    """pre-check：稳定五 phase JSON 报告，fixture 已就绪时零写盘。"""
    report = {
        "overall": "success",
        "steps": [{"name": n, "status": "ready", "action": "already-installed",
                   "version": "fixture", "error": ""}
                  for n in ("npx", "uvx", "ast-grep", "codegraph", "openspec", "pi-mcp-adapter")],
        "phases": [
            {"phase": "base-tools", "result": "skipped", "action": "do_base_tools", "duration_ms": 1,
             "created": 0, "updated": 0, "skipped": 6, "conflicts": 0, "error": None},
            {"phase": "openspec", "result": "skipped", "action": "verify-ready", "duration_ms": 2,
             "created": 0, "updated": 0, "skipped": 4, "conflicts": 0, "error": None},
            {"phase": "superpowers-git", "result": "skipped", "action": "fetch-pull-ff-only", "duration_ms": 4,
             "created": 0, "updated": 0, "skipped": 1, "conflicts": 0, "error": None,
             "origin": "fixture-origin", "branch": "main", "before_revision": "abc", "after_revision": "abc"},
            {"phase": "superpowers-links", "result": "skipped", "action": "all-skipped", "duration_ms": 1,
             "created": 0, "updated": 0, "skipped": 56, "conflicts": 0, "error": None},
            {"phase": "verify", "result": "skipped", "action": "all-skipped", "duration_ms": 1,
             "created": 0, "updated": 0, "skipped": 1, "conflicts": 0, "error": None},
        ],
    }
    return report


def _stage1_rule_config(cwd: Path) -> None:
    """rule-config：规则清单 / L0 v4 / 权限区 / codex 内联区。"""
    # mock 安装也复刻 OpenSpec 四端投影锚点，供 stage1 断言消费；pre-check 本身不写盘。
    (cwd / ".claude" / "commands" / "opsx").mkdir(parents=True, exist_ok=True)
    for base, prefix, suffix, count in (
        (cwd / ".claude" / "skills", "openspec-", "", 1),
        (cwd / ".agents" / "skills", "openspec-", "", 1),
        (cwd / ".pi" / "skills", "openspec-", "", 5),
        (cwd / ".pi" / "prompts", "opsx-", ".md", 5),
        (cwd / ".kimi-code" / "skills", "openspec-", "", 5),
    ):
        for index in range(count):
            path = base / f"{prefix}{index + 1}{suffix}"
            if suffix:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# opsx prompt\n", encoding="utf-8")
            else:
                (path / "SKILL.md").parent.mkdir(parents=True, exist_ok=True)
                (path / "SKILL.md").write_text("# openspec\n", encoding="utf-8")
    rules = cwd / ".claude" / "rules"
    rules.mkdir(parents=True, exist_ok=True)  # 先建目录再写文件
    for name in RULES_FILES:
        (rules / name).write_text("# rule\n", encoding="utf-8")
    claude_md = cwd / "CLAUDE.md"
    v4_block = (
        "<!-- cadence-managed:openspec-superpowers-routing:v4:start -->\n"
        "Cadence L0 路由内核 v4\n"
        "<!-- cadence-managed:openspec-superpowers-routing:v4:end -->")
    old_text = claude_md.read_text(encoding="utf-8") if claude_md.is_file() else ""
    m = V3_BLOCK_RE.search(old_text)
    if m:
        # v3 升级链：旧文件备份到 cadence/legacy/<ts>/，区块外内容逐字保留
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        legacy = cwd / "cadence" / "legacy" / ts
        legacy.mkdir(parents=True, exist_ok=True)
        (legacy / "CLAUDE.md.v3.md").write_text(old_text, encoding="utf-8")
        (legacy.parent / ".gitignore").write_text("*\n", encoding="utf-8")
        claude_md.write_text(old_text.replace(m.group(0), v4_block), encoding="utf-8")
    else:
        claude_md.write_text(v4_block + "\n", encoding="utf-8")
    (cwd / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": [
        "@@cadence-managed:permission-gate:v1:start@@", "Grep", "Glob", "Bash(grep:*)",
        "@@cadence-managed:permission-gate:v1:end@@"]}}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (cwd / "AGENTS.md").write_text(
        "<!-- cadence-managed:codex-rules-inline:v1:start -->\n链\n"
        "<!-- cadence-managed:codex-rules-inline:v1:end -->\n", encoding="utf-8")


def _stage1_mcp(cwd: Path) -> None:
    """mcp-configuration：.mcp.json / .codex/config.toml / .gitignore 精确行。"""
    (cwd / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "zai-mcp-server": {"command": "npx"}, "MiniMax": {"command": "uvx"},
        "codegraph": {"command": "codegraph-server"},
        "existing-server": {"command": "echo"}}}, indent=2), encoding="utf-8")
    (cwd / ".codex").mkdir(exist_ok=True)
    (cwd / ".codex" / "config.toml").write_text(
        "[mcp_servers.zai-mcp-server]\ncommand = \"npx\"\n"
        "[mcp_servers.MiniMax]\ncommand = \"uvx\"\n"
        "[mcp_servers.codegraph]\ncommand = \"codegraph-server\"\n"
        "[mcp_servers.existing-server]\ncommand = \"echo\"\n", encoding="utf-8")
    (cwd / ".gitignore").write_text(
        ".worktrees/\n.mcp.json\n.codex/config.toml\ncadence/cache/mcp-availability/\n",
        encoding="utf-8")


def _stage1_prx(cwd: Path) -> None:
    """project-rules-examples：仅写 cadence/project-rules/，不碰 .claude/rules/。"""
    pr = cwd / "cadence" / "project-rules"
    (pr / "examples").mkdir(parents=True, exist_ok=True)
    (pr / "README.md").write_text("# 项目规则\n", encoding="utf-8")


# 阶段一按 command 名分支（env EVAL_COMMAND）：pre-check 零写盘，其余各写各自产物
STAGE1_WRITERS = {
    "rule-config": _stage1_rule_config,
    "mcp-configuration": _stage1_mcp,
    "project-rules-examples": _stage1_prx,
}


def _probe_transcript(agent, probe_id):
    """罐头探针轨迹：P1 演示 deny→改道；MCP 探针演示 fake server 调用。

    工具入参用真实形状：Bash→{"command": ...}、Read/Write→{"file_path": ...}、
    检索/MCP→{"query": ...}（适配器 WriteEvent/P8 判分依赖该形状）。
    """
    model = {"claude": "glm-5.3", "codex": "gpt-5.4",
             "pi": "glm-5.3", "kimi": "kimi-code/kimi-for-coding"}[agent]
    if probe_id == "P1":
        calls = [("Bash", {"command": "ls -R src"}),
                 ("mcp__codegraph__codegraph_explore", {"query": "orders"})]
    elif probe_id in ("P2", "P6", "P7"):
        server = {"P2": "context7", "P6": "time", "P7": "zai-mcp-server"}[probe_id]
        calls = [(f"mcp__{server.replace('-', '_')}__tool", {"query": "seed"})]
    else:
        calls = [("Read", {"file_path": "src/main.py"}),
                 ("Write", {"file_path": "cadence/plans/doc.md"})]
    lines = [{"type": "system", "subtype": "init", "session_id": "mock",
              "model": model, "version": "2.1.233"}]
    for i, (tool, inp) in enumerate(calls):
        lines.append({"type": "assistant", "message": {"model": model, "content": [
            {"type": "tool_use", "id": f"t{i}", "name": tool, "input": inp}]}})
        denied = probe_id == "P1" and tool == "Bash"
        lines.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"t{i}", "is_error": denied,
             "content": "permission denied by settings" if denied else "ok"}]}})
    lines.append({"type": "result", "subtype": "success", "duration_ms": 3000,
                  "result": "中文结论：调用链已梳理 / 任务完成"})
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description="mock coding agent CLI（eval 专用）")
    parser.add_argument("--agent", required=True, choices=["claude", "codex", "pi", "kimi"])
    args = parser.parse_args(argv)
    cwd = Path(os.environ.get("EVAL_CWD", os.getcwd()))
    stage = os.environ.get("EVAL_STAGE", "probe")
    probe_id = os.environ.get("EVAL_PROBE_ID", "P1")
    if stage == "stage1":
        command = os.environ.get("EVAL_COMMAND", "")
        if command == "pre-check":
            report = _stage1_pre_check(cwd)
            _emit([{"type": "result", "subtype": "success",
                    "result": json.dumps(report, ensure_ascii=False), "duration_ms": 5000}])
        else:
            writer = STAGE1_WRITERS.get(command)
            if writer is not None:
                writer(cwd)
            _emit([{"type": "result", "subtype": "success",
                    "result": f"诊断报告：{command or '检查'}完成", "duration_ms": 5000}])
        return 0
    _emit(_probe_transcript(args.agent, probe_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
