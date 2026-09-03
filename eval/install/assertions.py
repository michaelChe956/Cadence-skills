"""阶段一产物断言表（design §4 全表；纯函数，Tier-0 可离线单测）。

断言期望值锚点：L0 v4 标记 / permission-gate v1 区块 / codex-rules-inline v1
区块均取自 p1 已合入产物（rule-config.py 常量同源；p1 改标记名时本文件同步）。
"""
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from eval.fixtures import generator as gen

L0_BEGIN = "<!-- cadence-managed:openspec-superpowers-routing:v4:start -->"
GATE_BEGIN = "@@cadence-managed:permission-gate:v1:start@@"
GATE_END = "@@cadence-managed:permission-gate:v1:end@@"
INLINE_BEGIN = "<!-- cadence-managed:codex-rules-inline:v1:start -->"
GITIGNORE_LINES = (".worktrees/", ".mcp.json", ".codex/config.toml",
                   "cadence/cache/mcp-availability/")
MCP_REQUIRED_SERVERS = ("zai-mcp-server", "MiniMax", "codegraph")  # coding fixture 期望下限


@dataclass
class Assertion:
    name: str
    ok: bool
    detail: str


def _ok(name: str, detail: str = "") -> Assertion:
    return Assertion(name, True, detail)


def _bad(name: str, detail: str) -> Assertion:
    return Assertion(name, False, detail)


def _read(root: Path, rel: str) -> Optional[str]:
    p = root / rel
    return p.read_text(encoding="utf-8") if p.is_file() else None


def _hash_tree(directory: Path) -> dict:
    out = {}
    if directory.is_dir():
        for p in sorted(directory.rglob("*")):
            if p.is_file():
                out[str(p.relative_to(directory))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def assert_stage1(variant: str, root: Path, verify_exit: Optional[int],
                  final_texts: dict, extra: Optional[dict] = None) -> list[Assertion]:
    """按 design §4 断言表逐项核对 workspace；extra 由 stage1 runner 采集。"""
    extra = extra or {}
    results = []
    texts = final_texts or {}

    # --- pre-check：诊断报告产出 + 项目文件零改动 ---
    report_text = texts.get("pre-check", "")
    results.append(_ok("pre-check.report") if "诊断" in report_text or "检查" in report_text
                   else _bad("pre-check.report", f"final_text 无诊断标记：{report_text[:80]!r}"))
    if variant == "fresh":  # v3/mcp_pre 本身有预置文件，零改动断言只对全新变体成立
        clean = extra.get("pre_check_clean")
        results.append(_ok("pre-check.zero-change") if clean is not False
                       else _bad("pre-check.zero-change", "pre-check 产生文件改动"))

    # --- rule-config：规则清单 / L0 v4 / 权限区 / 内联区 / --verify ---
    rules_dir = root / ".claude" / "rules"
    actual = sorted(p.name for p in rules_dir.glob("*.md")) if rules_dir.is_dir() else []
    expect = sorted(gen.expected_rules_files())
    results.append(_ok("rules.manifest") if actual == expect
                   else _bad("rules.manifest", f"清单不符：{actual} != {expect}"))
    claude_md = _read(root, "CLAUDE.md") or ""
    results.append(_ok("l0.v4") if L0_BEGIN in claude_md else _bad("l0.v4", "CLAUDE.md 无 v4 受管区块"))
    settings_raw = _read(root, ".claude/settings.json")
    gate_ok = False
    if settings_raw is not None:
        try:
            deny = json.loads(settings_raw).get("permissions", {}).get("deny", [])
            gate_ok = GATE_BEGIN in deny and GATE_END in deny
        except (ValueError, TypeError):
            gate_ok = False
    results.append(_ok("gate.region") if gate_ok else _bad("gate.region", "settings.json 无受管 deny 区块"))
    agents_md = _read(root, "AGENTS.md") or ""
    results.append(_ok("codex.inline") if INLINE_BEGIN in agents_md
                   else _bad("codex.inline", "AGENTS.md 无 codex-rules-inline 区块"))
    results.append(_ok("verify.exit0") if verify_exit == 0
                   else _bad("verify.exit0", f"--verify 退出码 {verify_exit}"))

    # --- v3 变体追加：确定性升级 + 备份 + 区块外逐字不变 ---
    if variant == "v3":
        results.append(_ok("v3.upgraded") if L0_BEGIN in claude_md and "v3:start" not in claude_md
                       else _bad("v3.upgraded", "v3 区块未升级为 v4"))
        legacy = root / "cadence" / "legacy"
        results.append(_ok("v3.backup") if legacy.is_dir() and any(legacy.iterdir())
                       else _bad("v3.backup", "cadence/legacy/ 无备份"))
        baseline = extra.get("outside_l0_baseline")
        if baseline is None:
            results.append(_bad("v3.outside-verbatim", "缺少区块外基线（runner 未采集）"))
        else:
            m = re.search(re.escape(L0_BEGIN) + r".*?" + "v4:end -->", claude_md, re.S)
            outside = claude_md.replace(m.group(0), "") if m else claude_md
            results.append(_ok("v3.outside-verbatim") if baseline in outside
                           else _bad("v3.outside-verbatim", "区块外内容变化"))

    # --- mcp-configuration：合法性 / 一致性 / .gitignore 精确行 ---
    mcp_raw = _read(root, ".mcp.json")
    servers = {}
    if mcp_raw is not None:
        try:
            servers = json.loads(mcp_raw).get("mcpServers", {})
        except (ValueError, TypeError):
            servers = {}
    missing = [s for s in MCP_REQUIRED_SERVERS if s not in servers]
    results.append(_ok("mcp.valid") if mcp_raw is not None and not missing and bool(servers)
                   else _bad("mcp.valid", f".mcp.json 缺 server：{missing}"))
    toml = _read(root, ".codex/config.toml") or ""
    inconsistent = [s for s in servers if f"[mcp_servers.{s}]" not in toml]
    results.append(_ok("mcp.codex-consistent") if servers and not inconsistent
                   else _bad("mcp.codex-consistent", f"config.toml 缺区块：{inconsistent}"))
    gi = _read(root, ".gitignore") or ""
    gi_lines = {ln.strip() for ln in gi.splitlines()}
    absent = [ln for ln in GITIGNORE_LINES if ln not in gi_lines]
    results.append(_ok("mcp.gitignore") if not absent else _bad("mcp.gitignore", f"缺行：{absent}"))
    if variant == "mcp_pre":
        results.append(_ok("mcp.pre-existing") if "existing-server" in servers
                       else _bad("mcp.pre-existing", "既有 server 被覆盖"))

    # --- project-rules-examples：就位 + 不写 .claude/rules/ ---
    pr = root / "cadence" / "project-rules"
    placed = pr.is_dir() and (pr / "README.md").is_file() and (pr / "examples").is_dir()
    results.append(_ok("prx.placed") if placed else _bad("prx.placed", "cadence/project-rules/ 未就位"))
    before = extra.get("rules_before")
    if before is None:
        # 缺快照时判 skip（ok=True + skip: 前缀），不判红也不计入失败——
        # 离线/单测调用（test_fresh_all_green、test_v3_upgrade_assertions）无需补传
        results.append(_ok("prx.not-rules", "skip: 缺 rules_before 快照（runner 未采集），本项不判"))
    else:
        results.append(_ok("prx.not-rules") if _hash_tree(rules_dir) == before
                       else _bad("prx.not-rules", ".claude/rules/ 被本步修改"))
    return results
