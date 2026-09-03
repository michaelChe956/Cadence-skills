"""mock 四端 CLI：罐头产物 + 罐头轨迹（Tier-0 冒烟与 Tier-1 付费前自检）。

只验证 harness 管线（argv/env/捕获/断言/报告），不验证 skill 语义——
skill 语义归 Tier-1 真实端。行为由 env 驱动：
  EVAL_STAGE=stage1|probe   EVAL_PROBE_ID=P1..P8
  EVAL_COMMAND=pre-check|rule-config|mcp-configuration|project-rules-examples
（阶段一按 command 名分支：pre-check 只产诊断报告零写盘，其余各写各自产物）
"""
import argparse
import json
import os
import sys
from pathlib import Path

RULES_FILES = ["README.md", "code-reading.md", "code-usage.md", "document-storage.md",
               "language.md", "markdown-format.md", "mcp-servers.md",
               "openspec-superpowers-workflow.md", "playwright.md"]


def _emit(lines):
    for ln in lines:
        sys.stdout.write(json.dumps(ln, ensure_ascii=False) + "\n")


def _stage1_pre_check(cwd: Path) -> None:
    """pre-check：只产出诊断报告（stdout），零写盘（断言 pre-check.zero-change）。"""


def _stage1_rule_config(cwd: Path) -> None:
    """rule-config：规则清单 / L0 v4 / 权限区 / codex 内联区。"""
    rules = cwd / ".claude" / "rules"
    rules.mkdir(parents=True, exist_ok=True)  # 先建目录再写文件
    for name in RULES_FILES:
        (rules / name).write_text("# rule\n", encoding="utf-8")
    (cwd / "CLAUDE.md").write_text(
        "<!-- cadence-managed:openspec-superpowers-routing:v4:start -->\n"
        "Cadence L0 路由内核 v4\n"
        "<!-- cadence-managed:openspec-superpowers-routing:v4:end -->\n",
        encoding="utf-8")
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
        writer = STAGE1_WRITERS.get(command)  # pre-check/未知 command：零写盘
        if writer is not None:
            writer(cwd)
        _emit([{"type": "result", "subtype": "success",
                "result": f"诊断报告：{command or '检查'}完成", "duration_ms": 5000}])
        return 0
    _emit(_probe_transcript(args.agent, probe_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
