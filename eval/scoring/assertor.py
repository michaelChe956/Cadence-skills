"""确定性断言器：只消费统一中间格式；事件/产物/时间序三类断言 + 归因分类。

防线（oracle §6 / Backgrind / claudemd-check）：
* 排除规则原文——工具使用断言只读 tool_calls 事件，不读 assistant 文本；
* 假绿 gate——区块外 deny / is_error 判 FAIL（经 denial_gate 双分类）；
* infra 归因——CLI 崩溃/登录失效/超时/轨迹缺失 → INFRA_FAIL，出矩阵。
"""
import re
from pathlib import Path
from typing import Optional

from eval import ifmt
from eval.scoring import denial_gate

INFRA_PATTERNS = (
    ("login", ("login", "auth", "credential", "登录", "鉴权")),
    ("quota", ("quota", "rate limit", "usage limit", "配额")),
    ("cli-crash", ("traceback", "panic", "segfault", "core dump")),
)

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
ROAM_HEADS = ("ls", "find", "dir")


def tool_used(traj, pattern: str) -> bool:
    """只看真实工具调用事件（tool 名或参数摘要）；朗读规则文本不算使用。"""
    rx = re.compile(pattern)
    return any(rx.search(c.tool) or rx.search(c.args_digest)
               for c in traj.tool_calls)


def tool_absent(traj, pattern: str) -> bool:
    return not tool_used(traj, pattern)


def bash_heads(traj) -> list:
    return [c.args_digest for c in traj.tool_calls if c.tool == "Bash"]


def roam_detect(traj, max_count: int, preferred_pattern: str) -> bool:
    """ls/find 漫游检测：命令头计数超限且全程未用 preferred 工具。"""
    heads = [h.split(" ")[0] for h in bash_heads(traj)]
    roam_count = sum(1 for h in heads if h in ROAM_HEADS)
    return roam_count > max_count and not tool_used(traj, preferred_pattern)


def zh_ratio(text: str) -> float:
    """CJK 字符数 / 非空白字符数。"""
    compact = "".join(text.split())
    if not compact:
        return 0.0
    return len(CJK_RE.findall(compact)) / len(compact)


def classify_infra(returncode, stderr, traj_present, timed_out=False):
    """基础设施失败分类；返回 None 表示非 infra（agent 行为问题）。"""
    low = (stderr or "").lower()
    if timed_out:
        return "infra-fail:timeout"
    if not traj_present:
        return "infra-fail:transcript-missing"
    if returncode != 0:
        for kind, markers in INFRA_PATTERNS:
            if any(m in low for m in markers):
                return f"infra-fail:{kind}"
        return "infra-fail:cli-crash"
    return None


def _check_assertion(spec, traj, workspace, fake_mcp_log, pre_snapshot):
    kind = spec["kind"]
    if kind == "tool_used":
        return tool_used(traj, spec["pattern"])
    if kind == "tool_absent":
        return tool_absent(traj, spec["pattern"])
    if kind == "no_roam":
        return not roam_detect(traj, spec.get("max_ls_find", 5), spec["preferred"])
    if kind == "zh_output":
        return zh_ratio(traj.final_text) >= spec.get("min_ratio", 0.6)
    if kind == "plan_before_edit":
        plan_rx = re.compile(spec.get("plan_dir_regex", r"(openspec/changes|cadence/plans)/"))
        first_edit = next((c.index for c in traj.tool_calls
                           if c.tool in ("Edit", "Write")), None)
        first_plan = next((w.at_index for w in traj.writes
                           if plan_rx.search(w.path)), None)
        if first_plan is None:
            # 既有文件（探针前已存在的产物）也计入时间序合规
            if workspace is not None and any(
                    plan_rx.search(str(p.relative_to(workspace)))
                    for p in workspace.glob("openspec/changes/*")):
                return True
            if workspace is not None and any(
                    plan_rx.search(str(p.relative_to(workspace)))
                    for p in list(workspace.glob("cadence/plans/*"))
                    + list(workspace.glob("cadence/designs/*"))):
                return True
            return False
        return first_edit is None or first_plan < first_edit
    if kind == "file_exists":
        return workspace is not None and (workspace / spec["rel"]).exists()
    if kind == "file_matches":
        if workspace is None:
            return False
        if spec["rel"] == ".":
            # 树扫描形态：对 workspace 下全部产物路径做正则匹配（P5 产物目录/命名）
            for p in sorted(workspace.rglob("*")):
                if p.is_file():
                    rel = p.relative_to(workspace).as_posix()
                    if re.search(spec["regex"], rel):
                        return True
            return False
        p = workspace / spec["rel"]
        return p.is_file() and re.search(spec["regex"],
                                         p.read_text(encoding="utf-8", errors="replace")) is not None
    if kind == "mcp_called":
        server = spec["server"]
        prefix = f"mcp__{server.replace('-', '_')}__"
        in_traj = tool_used(traj, re.escape(prefix))
        in_log = fake_mcp_log is not None and any(
            entry.get("server") == server for entry in fake_mcp_log)
        return in_traj or in_log  # stdout 缺事件时以 fake server 调用记录为准
    if kind == "mcp_answer":
        seeds = spec.get("must_contain", [])
        return all(s in traj.final_text for s in seeds)
    if kind == "info_source_isolated":
        return all(tool_absent(traj, re.escape(f)) for f in spec.get("forbidden", []))
    if kind == "snapshot_unchanged":
        if pre_snapshot is None or workspace is None:
            return False
        from eval.install.idempotency import diff_trees, snapshot_tree
        return diff_trees(pre_snapshot, snapshot_tree(workspace)) == {}
    raise ValueError(f"未知断言种类：{kind}")


def score_run(run_id, probe, traj, workspace=None, fake_mcp_log=None,
              pre_snapshot=None, returncode=0, stderr="", timed_out=False):
    """判分入口：infra 归因先行 → 逐断言 → deny 双分类 gate → 结果 dict。"""
    from eval.scoring.schema import build_result
    infra = classify_infra(returncode, stderr,
                           traj_present=bool(traj and traj.tool_calls or traj and
                                             traj.final_text),
                           timed_out=timed_out)
    if infra:
        return build_result(
            run_id=run_id, agent=traj.agent, model=traj.model_readback,
            cli_version=traj.cli_version, probe_id=probe["id"],
            rule_clause_ids=list(probe.get("rule_clause_ids", [])),
            verdict="INFRA_FAIL", fail_reason=infra,
            denials=[vars(d) for d in traj.denials],
            transcript_path=traj.source_path, started_at=traj.started_at,
            duration_s=traj.duration_s,
            details={"deny_gate": {"managed": 0, "unmanaged": 0, "abandoned": 0,
                                   "rerouted": 0, "silent_errors": 0},
                     "stderr": stderr[-500:],
                     "settings_snapshot": traj.settings_snapshot})
    failures = []
    for spec in probe.get("assertions", []):
        if not _check_assertion(spec, traj, workspace, fake_mcp_log, pre_snapshot):
            failures.append(spec["kind"])
    gate = denial_gate.apply_deny_gate(traj, probe)
    if gate["unmanaged"] > 0:
        failures.append("deny-unmanaged(harness 配置错误)")
    if gate["abandoned"] > 0:
        failures.append("deny-abandoned(受管拦截后未改道)")
    if gate["silent_errors"] > 0:
        failures.append("is-error(静默失败假绿防线)")
    verdict = "FAIL" if failures else "PASS"
    return build_result(
        run_id=run_id, agent=traj.agent, model=traj.model_readback,
        cli_version=traj.cli_version, probe_id=probe["id"],
        rule_clause_ids=list(probe.get("rule_clause_ids", [])),
        verdict=verdict, fail_reason=";".join(failures),
        denials=[vars(d) for d in traj.denials],
        transcript_path=traj.source_path, started_at=traj.started_at,
        duration_s=traj.duration_s,
        details={"deny_gate": gate, "stderr": stderr[-500:],
                 "settings_snapshot": traj.settings_snapshot})
