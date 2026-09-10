"""阶段一产物断言表（design §4 全表；纯函数，Tier-0 可离线单测）。

断言期望值锚点：L0 v5 标记 / permission-gate v1 区块 / codex-rules-inline v1
区块均取自 p1 已合入产物（rule-config.py 常量同源；p1 改标记名时本文件同步）。
"""
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


TARGET_HOME_LAYERS = (
    ".agents/skills", ".codex/skills/skills", ".claude/skills", ".pi/agent/skills",
)


def _path_is_openspec_projection(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    return (rel == ".agents/skills/.openspec-target"
            or rel == ".claude/commands/opsx" or rel.startswith(".claude/commands/opsx/")
            or rel.startswith(".claude/skills/openspec-")
            or rel.startswith(".agents/skills/openspec-")
            or rel.startswith(".pi/skills/") or rel.startswith(".pi/prompts/")
            or rel.startswith(".kimi-code/skills/openspec-"))


def _zero_change_violations(before, after) -> list[str]:
    """按 openspec 分层守卫检查 pre-check 前后树差异。"""
    b = {str(k).replace("\\", "/"): v for k, v in (before or {}).items()}
    a = {str(k).replace("\\", "/"): v for k, v in (after or {}).items()}
    violations = []
    for rel in sorted(set(b) | set(a)):
        if _path_is_openspec_projection(rel):
            continue
        if rel.startswith("openspec/") and "/" not in rel[len("openspec/"):]:
            if rel not in b and rel in a:
                continue
        if b.get(rel) != a.get(rel):
            violations.append(rel)
    return violations


def _non_target_tree_hash(snapshot, root: Optional[Path] = None) -> dict:
    """返回排除 OpenSpec 投影白名单后的 workspace 文件哈希。"""
    if isinstance(snapshot, Path):
        root = snapshot
        snapshot = {}
        if root.is_dir():
            for p in sorted(root.rglob("*")):
                if p.is_file() or p.is_symlink():
                    rel = p.relative_to(root).as_posix()
                    if _path_is_openspec_projection(rel):
                        continue
                    try:
                        snapshot[rel] = ("link:" + str(p.read_link()) if p.is_symlink()
                                         else hashlib.sha256(p.read_bytes()).hexdigest())
                    except OSError:
                        snapshot[rel] = "unreadable"
    else:
        snapshot = dict(snapshot or {})
        snapshot = {str(k): v for k, v in snapshot.items()
                    if not _path_is_openspec_projection(str(k))}
    return snapshot


def _phase_map(report: Optional[dict]) -> dict:
    if not isinstance(report, dict) or not isinstance(report.get("phases"), list):
        return {}
    return {p.get("phase"): p for p in report["phases"]
            if isinstance(p, dict) and isinstance(p.get("phase"), str)}


def _count_named(path: Path, prefix: str = "", suffix: str = "") -> int:
    if not path.is_dir():
        return 0
    return sum(1 for item in path.iterdir()
               if item.name.startswith(prefix) and item.name.endswith(suffix))


def _precheck_projection_ok(root: Path) -> tuple[bool, str]:
    """按四端锚路径验证 OpenSpec 投影，不依赖 stdout 文案。"""
    checks = {
        ".claude (commands/opsx OR skills/openspec-*)": (
            (root / ".claude" / "commands" / "opsx").is_dir()
            or _count_named(root / ".claude" / "skills", "openspec-") > 0
        ),
        ".agents/skills/openspec-*": _count_named(root / ".agents/skills", "openspec-") > 0,
        ".pi/skills/openspec-* (5)": _count_named(root / ".pi/skills", "openspec-") == 5,
        ".pi/prompts/opsx-*.md (5)": _count_named(root / ".pi/prompts", "opsx-", ".md") == 5,
        ".kimi-code/skills/openspec-* (5)": _count_named(root / ".kimi-code/skills", "openspec-") == 5,
    }
    bad = [path for path, ok in checks.items() if not ok]
    return not bad, "缺少或数量错误的投影路径：" + ", ".join(bad) if bad else ""


def _precheck_links_ok(home: Optional[Path], expected: int = 14) -> tuple[bool, str]:
    """验证 Superpowers 源对应的四层链接恰为 expected 条。"""
    if home is None:
        return True, "skip: 未提供 HOME"
    home = Path(home)
    source = home / ".agents/superpowers/skills"
    names = sorted(p.name for p in source.iterdir()) if source.is_dir() else []
    names = [n for n in names if n != "knowledge-base-context"]
    if len(names) != expected:
        return False, f"源条目数量 {len(names)} != {expected}（{source}）"
    failures = []
    for layer_rel in TARGET_HOME_LAYERS:
        layer = home / layer_rel
        if layer.is_dir():
            source_root = source.resolve()
            extras = []
            for item in layer.iterdir():
                if item.name in names or not item.is_symlink():
                    continue
                try:
                    item.resolve().relative_to(source_root)
                except (OSError, ValueError):
                    continue
                extras.append(item.name)
            failures.extend(
                f"{layer_rel}/{name} 非目标条目（不在源目录枚举中）" for name in sorted(extras)
            )
        actual = 0
        for name in names:
            target = layer / name
            if not target.is_symlink():
                failures.append(f"{layer_rel}/{name} 非软链")
                continue
            try:
                resolved = target.resolve()
            except OSError:
                failures.append(f"{layer_rel}/{name} 无法解析")
                continue
            if resolved != (source / name).resolve():
                failures.append(f"{layer_rel}/{name} -> {resolved}（期望 {(source / name).resolve()}）")
            else:
                actual += 1
        if actual != expected:
            failures.append(f"{layer_rel} 链接数 {actual}/{expected}")
    return not failures, "; ".join(failures)


def _precheck_home_schema(home_info: object) -> tuple[bool, str]:
    """验证 runner 注入的 HOME 模式、实际路径和 fixture 路径一致。"""
    if home_info is None:
        return True, "skip: 未提供 HOME 前后快照"
    if not isinstance(home_info, dict):
        return False, "HOME 快照结构非法"
    mode = home_info.get("mode")
    path = home_info.get("path")
    fixture_path = home_info.get("fixture_path")
    if mode not in ("fixture", "inherited") or not isinstance(path, str) or not isinstance(fixture_path, str):
        return False, "HOME 快照缺少 mode/path/fixture_path"
    same = Path(path).resolve() == Path(fixture_path).resolve()
    if (mode == "fixture") != same:
        return False, f"HOME 路径与 mode 矛盾：mode={mode!r}, path={path!r}, fixture_path={fixture_path!r}"
    return True, ""


def _precheck_home_changed(home_info: object) -> tuple[bool, str]:
    schema_ok, schema_detail = _precheck_home_schema(home_info)
    if not schema_ok:
        return False, schema_detail
    if home_info is None:
        return True, schema_detail
    if "before" not in home_info or "after" not in home_info:
        return False, "HOME 快照缺少 before/after"
    before = home_info.get("before") or {}
    after = home_info.get("after") or {}
    changed = sorted(set(before) ^ set(after) |
                     {p for p in before if p in after and before[p] != after[p]})
    return not changed, "HOME 非目标条目变化：" + ", ".join(changed) if changed else ""

from eval.fixtures import generator as gen

L0_BEGIN = "<!-- cadence-managed:openspec-superpowers-routing:v5:start -->"
GATE_BEGIN = "@@cadence-managed:permission-gate:v1:start@@"
GATE_END = "@@cadence-managed:permission-gate:v1:end@@"
INLINE_BEGIN = "<!-- cadence-managed:codex-rules-inline:v1:start -->"
OMP_CONTEXT_MARKER = "<!-- cadence-managed:omp-context:v1 -->"
OMP_AGENTS_MD_BODY = (  # .omp/AGENTS.md 受管正文（rule-config.py 同源三行活引用）
    f"{OMP_CONTEXT_MARKER}\n"
    "@../.claude/CLAUDE.md\n"
    "@../AGENTS.md\n"
)
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
    report = extra.get("pre_check_report")
    report_ok = (isinstance(report, dict) and report.get("overall") in ("success", "ok")
                 and isinstance(report.get("steps"), list)
                 and isinstance(report.get("phases"), list))
    has_structured_report = isinstance(report, dict) and isinstance(report.get("phases"), list)
    results.append(_ok("pre-check.report") if report_ok or "诊断" in report_text or "检查" in report_text
                   else _bad("pre-check.report", f"final_text 无诊断标记或合法报告：{report_text[:80]!r}"))
    if variant == "fresh":  # v3/mcp_pre 本身有预置文件，零改动断言只对全新变体成立
        clean = extra.get("pre_check_clean")
        results.append(_ok("pre-check.zero-change") if clean is not False
                       else _bad("pre-check.zero-change", "pre-check 产生文件改动"))

    # 结构化 pre-check 断言：先验证报告，再验证真实锚点。
    phases = _phase_map(report)
    expected_phases = ("base-tools", "openspec", "superpowers-git", "superpowers-links", "verify")
    missing_phases = ([p for p in expected_phases if p not in phases]
                      if has_structured_report else [])
    # 先锁定 runner 提供的路径事实，再让投影和 links 消费相同路径。
    home_info = extra.get("pre_check_home")
    home_schema_ok, home_schema_detail = _precheck_home_schema(home_info)
    projection_ok, projection_detail = _precheck_projection_ok(root)
    # 直接调用断言器的旧单测没有 HOME/投影 fixture；集成 runner 总会传入 home，
    # 因而只在有快照时把锚点作为硬断言，报告缺 phase 仍始终判红。
    if home_info is not None and not home_schema_ok:
        results.append(_bad("pre-check.projections", home_schema_detail))
    elif missing_phases:
        results.append(_bad("pre-check.projections",
                            "报告缺少 phase：" + ", ".join(missing_phases)))
    elif extra.get("pre_check_home") is None:
        results.append(_ok("pre-check.projections", "skip: 未提供集成 HOME 快照"))
    else:
        results.append(_ok("pre-check.projections") if projection_ok
                       else _bad("pre-check.projections", projection_detail))

    # 先锁定 runner 提供的路径事实，再让 links 消费相同路径。
    if home_info is not None and not home_schema_ok:
        results.append(_bad("pre-check.links", home_schema_detail))
    elif missing_phases:
        results.append(_bad("pre-check.links", "报告缺少 phase：" + ", ".join(missing_phases)))
    elif home_info is None:
        results.append(_ok("pre-check.links", "skip: 未提供集成 HOME 快照"))
    else:
        home_path = home_info["path"]
        links_ok, links_detail = _precheck_links_ok(Path(home_path).resolve(), 14)
        results.append(_ok("pre-check.links") if links_ok else _bad("pre-check.links", links_detail))

    phase_errors = []
    for name in expected_phases:
        phase = phases.get(name)
        if phase is None:
            continue
        if phase.get("error") not in (None, ""):
            phase_errors.append(f"{name}.error={phase.get('error')!r}")
        if not all(key in phase for key in ("result", "action", "created", "updated", "skipped", "conflicts")):
            phase_errors.append(f"{name} 缺少 result/action/计数字段")
        writes = int(phase.get("created", 0) or 0) + int(phase.get("updated", 0) or 0)
        if writes and phase.get("result") != "success":
            phase_errors.append(f"{name} 有写入但 result={phase.get('result')!r}（必须 success）")
        if not writes and int(phase.get("conflicts", 0) or 0) == 0 and phase.get("result") not in ("skipped", "success"):
            phase_errors.append(f"{name} 零写入但 result={phase.get('result')!r}（应 skipped）")
    git = phases.get("superpowers-git")
    if git is not None:
        for key in ("origin", "branch", "before_revision", "after_revision"):
            if not git.get(key):
                phase_errors.append(f"superpowers-git 缺少 {key}")
    results.append(_ok("pre-check.phases") if (not phase_errors and not missing_phases)
                   or (not has_structured_report)
                   else _bad("pre-check.phases", "; ".join(phase_errors or ["缺少：" + ", ".join(missing_phases)])))

    if not has_structured_report:
        results.append(_ok("pre-check.performance", "skip: 未提供结构化 pre-check 报告"))
    else:
        calls = extra.get("pre_check_tool_calls")
        duration = extra.get("pre_check_duration_s")
        budget_errors = []
        if not isinstance(calls, int) or calls > 5:
            budget_errors.append(f"tool_calls={calls!r}，阈值 <=5")
        try:
            duration_value = float(duration)
        except (TypeError, ValueError):
            duration_value = None
        if duration_value is None or duration_value > 120:
            budget_errors.append(f"duration_s={duration!r}，阈值 <=120s")
        results.append(_ok("pre-check.performance") if not budget_errors
                       else _bad("pre-check.performance", "; ".join(budget_errors)))
    home_ok, home_detail = _precheck_home_changed(extra.get("pre_check_home"))
    results.append(_ok("pre-check.home", home_detail) if home_ok
                   else _bad("pre-check.home", home_detail))

    # --- rule-config：规则清单 / L0 v5 / 权限区 / 内联区 / --verify ---
    rules_dir = root / ".claude" / "rules"
    actual = sorted(p.name for p in rules_dir.glob("*.md")) if rules_dir.is_dir() else []
    expect = sorted(gen.expected_rules_files())
    results.append(_ok("rules.manifest") if actual == expect
                   else _bad("rules.manifest", f"清单不符：{actual} != {expect}"))
    claude_md = _read(root, "CLAUDE.md") or ""
    results.append(_ok("l0.v5") if L0_BEGIN in claude_md else _bad("l0.v5", "CLAUDE.md 无 v5 受管区块"))
    settings_raw = _read(root, ".claude/settings.json")
    # 纯文本模式（实验撤除物理拦截）：deny 区块不生成——settings 缺失或无受管
    # 区块均为合规；仅当出现"半截区块"（有 begin 无 end，疑似手改损坏）才判红。
    gate_ok = True
    if settings_raw is not None:
        try:
            deny = json.loads(settings_raw).get("permissions", {}).get("deny", [])
            has_begin, has_end = GATE_BEGIN in deny, GATE_END in deny
            if has_begin != has_end:
                gate_ok = False
        except (ValueError, TypeError):
            gate_ok = False
    results.append(_ok("gate.region") if gate_ok else _bad("gate.region", "settings.json 受管 deny 区块损坏（begin/end 不成对）"))
    agents_md = _read(root, "AGENTS.md") or ""
    results.append(_ok("codex.inline") if INLINE_BEGIN in agents_md
                   else _bad("codex.inline", "AGENTS.md 无 codex-rules-inline 区块"))
    results.append(_ok("verify.exit0") if verify_exit == 0
                   else _bad("verify.exit0", f"--verify 退出码 {verify_exit}"))

    # --- v3 变体追加：确定性升级 + 备份 + 区块外逐字不变 ---
    if variant == "v3":
        results.append(_ok("v3.upgraded") if L0_BEGIN in claude_md and "v3:start" not in claude_md
                       else _bad("v3.upgraded", "v3 区块未升级为 v5"))
        legacy = root / "cadence" / "legacy"
        results.append(_ok("v3.backup") if legacy.is_dir() and any(legacy.iterdir())
                       else _bad("v3.backup", "cadence/legacy/ 无备份"))
        baseline = extra.get("outside_l0_baseline")
        if baseline is None:
            results.append(_bad("v3.outside-verbatim", "缺少区块外基线（runner 未采集）"))
        else:
            m = re.search(re.escape(L0_BEGIN) + r".*?" + "v5:end -->", claude_md, re.S)
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
    # --- 五端渐进规则资产（Change A omp 桥接产物；设计文档 §6.6.2） ---
    # rules.frontmatter：规则文件逐个核对 frontmatter 围栏内含 description（README 豁免）
    fm_missing = []
    for p in sorted(rules_dir.glob("*.md")) if rules_dir.is_dir() else []:
        if p.name == "README.md":
            continue  # 仓库自有文档，不属受管规则清单
        m = re.match(r"^---\n(.*?\n)---\n", p.read_text(encoding="utf-8"), re.S)
        if not m or "description:" not in m.group(1):
            fm_missing.append(p.name)
    results.append(_ok("rules.frontmatter") if not fm_missing
                   else _bad("rules.frontmatter",
                             "缺 frontmatter/description：" + ", ".join(fm_missing)))

    # omp.symlinks：.agents/rules 软链集合==规则集合减 README，且逐个指回 .claude/rules
    bridge = root / ".agents" / "rules"
    want = sorted(p.name for p in rules_dir.glob("*.md")
                  if p.name != "README.md") if rules_dir.is_dir() else []
    have = sorted(p.name for p in bridge.glob("*.md")) if bridge.is_dir() else []
    bad_links = [n for n in want
                 if not (bridge / n).is_symlink()
                 or os.readlink(bridge / n) != f"../../.claude/rules/{n}"]
    results.append(_ok("omp.symlinks") if have == want and not bad_links
                   else _bad("omp.symlinks",
                             f"want={want} have={have} 坏链={bad_links}"))

    # omp.agents-md：.omp/AGENTS.md 逐字等于受管正文（omp-context v1 三行活引用）
    omp_md = root / ".omp" / "AGENTS.md"
    results.append(_ok("omp.agents-md")
                   if omp_md.is_file()
                   and omp_md.read_text(encoding="utf-8") == OMP_AGENTS_MD_BODY
                   else _bad("omp.agents-md", "缺失或非受管内容"))

    # agents-md.budget：AGENTS.md 行数预算（80+60 行预算加余量，200 封顶）
    n_lines = len(agents_md.splitlines())
    results.append(_ok("agents-md.budget") if n_lines <= 200
                   else _bad("agents-md.budget", f"{n_lines} 行超 200 行预算"))
    return results
