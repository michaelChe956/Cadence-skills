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


def tool_used(traj, pattern: str, require_ok: bool = False) -> bool:
    """只看真实工具调用事件（tool 名或参数摘要）；朗读规则文本不算使用。
    require_ok=True 时仅计非错误调用——失败的调用尝试≠真实使用
    （2026-09-11 M 组实测：MCP 启动失败时模型仍会尝试调用并记为
    is_error=True，旧实现按名字匹配误判 mcp_called PASS）。"""
    rx = re.compile(pattern)
    return any((not require_ok or not c.is_error)
               and (rx.search(c.tool) or rx.search(c.args_digest))
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


def classify_infra(returncode, stderr, traj_present, timed_out=False,
                   infra_errors=None):
    """基础设施失败分类；返回 None 表示非 infra（agent 行为问题）。

    ``infra_errors``：轨迹里采到的上游 API 报错（pi 的 stopReason=error /
    codex 的 event_msg error）。会话文件存在但只有报错时属于上游不可用，
    不能归因 transcript-missing（后者的语义是 harness 没拿到轨迹，会把真实
    的配额/鉴权问题误指为自身缺陷）。
    """
    low = (stderr or "").lower()
    if timed_out:
        return "infra-fail:timeout"
    if not traj_present:
        joined = " ".join(str(e) for e in (infra_errors or [])).lower()
        if joined:
            for kind, markers in INFRA_PATTERNS:
                if any(m in joined for m in markers):
                    return f"infra-fail:{kind}"
            return "infra-fail:api-error"
        return "infra-fail:transcript-missing"
    if returncode != 0:
        for kind, markers in INFRA_PATTERNS:
            if any(m in low for m in markers):
                return f"infra-fail:{kind}"
        return "infra-fail:cli-crash"
    return None


def stopped_at_design(changes: dict) -> bool:
    """P3 是未获人工确认的新任务。用探针前后快照验收停在 Design。"""
    design_written = False
    for path, action in changes.items():
        if path == 'loaded.log' or path.startswith(('.codegraph/', '.superpowers/')):
            continue
        if path.startswith('cadence/designs/') and path.endswith('.md') and action != 'removed':
            design_written = True
        elif not path.startswith('cadence/designs-reviews/'):
            return False
    return design_written


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
        if workspace is not None and pre_snapshot is not None:
            from eval.install.idempotency import diff_trees, snapshot_tree
            return stopped_at_design(diff_trees(pre_snapshot, snapshot_tree(workspace)))
        plan_rx = re.compile(spec["plan_dir_regex"])
        artifact_rx = re.compile(r"(?:^|/)(?:openspec/changes|cadence/designs(?:-reviews)?)/")
        # 工作区末态不能证明 Plan 在实施前存在。只采用起始快照和有序写入事件。
        prior_plans = {path for path in (pre_snapshot or {}) if plan_rx.match(path)}
        first_plan = min((w.at_index for w in traj.writes if plan_rx.search(w.path)), default=None)
        for call in traj.tool_calls:
            if call.tool == 'Read' and not call.is_error and call.args_digest in prior_plans:
                first_plan = call.index if first_plan is None else min(first_plan, call.index)
        impl_writes = [w.at_index for w in traj.writes
                       if not plan_rx.search(w.path) and not artifact_rx.search(w.path)]
        known_writes = {w.at_index for w in traj.writes}
        impl_writes.extend(c.index for c in traj.tool_calls if c.tool in ("Edit", "Write", "NotebookEdit")
                           and c.index not in known_writes)
        if impl_writes:
            return first_plan is not None and first_plan < min(impl_writes)
        # 仅写 Design 或草拟 change，仍在合法的规划阶段。
        return bool(traj.writes)
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
    if kind == "image_handled":
        # 图片路由规则（mcp-servers.md）：multimodal 直读（Read 图片路径）或图片 MCP 任一即合规
        for call in (traj.tool_calls or []):
            if call.tool.startswith("mcp__zai") or call.tool.startswith("mcp__MiniMax"):
                return True
            if call.tool == "Read" and str(call.args_digest).lower().endswith(
                    (".png", ".jpg", ".jpeg", ".webp")):
                return True
        return False
    if kind == "mcp_called":
        server = spec["server"]
        prefix = f"mcp__{server.replace('-', '_')}__"
        in_traj = tool_used(traj, re.escape(prefix), require_ok=True)
        in_log = fake_mcp_log is not None and any(
            entry.get("server") == server for entry in fake_mcp_log)
        return in_traj or in_log  # stdout 缺事件时以 fake server 调用记录为准
    if kind == "mcp_answer":
        seeds = spec.get("must_contain", [])
        return all(s in traj.final_text for s in seeds)
    if kind == "text_contains":
        # 最终输出文本（traj 最终 assistant 消息）必须包含锚点子串
        return spec["pattern"] in traj.final_text
    if kind == "text_lacks":
        # 最终输出文本不得包含禁止子串
        return spec["pattern"] not in traj.final_text
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
                           timed_out=timed_out,
                           infra_errors=getattr(traj, "infra_errors", None))
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
