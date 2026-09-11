"""四矩阵聚合、双键基线具名 diff、基线治理与对照组差值（eval-ci-matrix R3）。

治理规则：基线仅在维护者显式提交 eval/baselines/baseline.json 后生效；
夜间只对比不改基线；主版本不匹配的基线不参与 diff 并显式标注。
"""
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from eval.scoring import schema

MCP_PROBES = ("P2", "P6", "P7")
PROBE_NAMES = {"P1": "P1检索", "P2": "P2文档", "P3": "P3时序", "P4": "P4语言",
               "P5": "P5产物", "P6": "P6时间", "P7": "P7图片", "P8": "P8幂等",
               "D1": "D1环境检测"}
AGENT_NAMES = {"claude": "Claude", "codex": "Codex", "pi": "Pi", "kimi": "Kimi"}
_VALID_VERDICTS = ("PASS", "FAIL")


def load_results(nightly_root: Path, window_nights: int = 7,
                 end_date: Optional[str] = None) -> list:
    """加载包含结束日的滚动窗口；坏 JSON、非对象及无 run_id 行均跳过。"""
    end = date.fromisoformat(end_date) if end_date else date.today()
    rows = []
    if window_nights <= 0:
        return rows
    root = Path(nightly_root)
    for offset in range(window_nights):
        day = (end - timedelta(days=offset)).isoformat()
        runs_dir = root / day / "runs"
        if not runs_dir.is_dir():
            continue
        for path in sorted(runs_dir.glob("*.json")):
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            if isinstance(doc, dict) and isinstance(doc.get("run_id"), str):
                rows.append(doc)
    return rows


def _rate(cells: list) -> dict:
    """仅 PASS/FAIL 参与率；INFRA_FAIL 与 MODEL_DRIFT 是 skip。"""
    valid = [r for r in cells if r.get("verdict") in _VALID_VERDICTS]
    if not valid:
        return {"rate": None, "n": 0, "missing": True}
    passed = sum(1 for r in valid if r["verdict"] == "PASS")
    return {"rate": passed / len(valid), "n": len(valid), "missing": False}


def _cell(results: list, *, probe: str, agent: Optional[str] = None) -> dict:
    return _rate([r for r in results if r.get("probe_id") == probe and
                  (agent is None or r.get("agent") == agent)])


def _safe_rate(value):
    """基线中的比率必须是有限数值，避免坏基线造成报告异常。"""
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0 <= value <= 1)


def control_delta(installed: list, control: list) -> dict:
    """计算单个探针的安装组/对照组边际差值（百分点）。"""
    installed_rate = _rate(installed)
    control_rate = _rate(control)
    delta = (None if installed_rate["rate"] is None or control_rate["rate"] is None
             else round((installed_rate["rate"] - control_rate["rate"]) * 100, 1))
    return {"installed_rate": installed_rate["rate"],
            "control_rate": control_rate["rate"], "delta_pp": delta}


def aggregate(results: list) -> dict:
    """生成规则遵循、MCP、弱模型、跨端及条款×探针矩阵。"""
    rows = [r for r in results if isinstance(r, dict)]
    agents = sorted({r.get("agent") for r in rows if isinstance(r.get("agent"), str)}) or ["claude"]
    probes = sorted({r.get("probe_id") for r in rows if isinstance(r.get("probe_id"), str)}) or ["P1"]
    # strong 增补行只进入 weak_model，不能污染安装组四矩阵。
    installed = [r for r in rows if r.get("variant", "installed") == "installed"
                 and "-strong-" not in r.get("run_id", "")]
    controls = [r for r in rows if r.get("variant") == "control"]

    adherence = {probe: {agent: _cell(installed, probe=probe, agent=agent)
                         for agent in agents} for probe in probes}
    mcp_usage = {probe: {agent: adherence[probe][agent]
                         for agent in agents}
                 for probe in probes if probe in MCP_PROBES}

    clause_rows = {}
    for row in installed:
        if row.get("verdict") not in _VALID_VERDICTS:
            continue
        clauses = row.get("rule_clause_ids", [])
        if not isinstance(clauses, list):
            continue
        for clause in clauses:
            if not isinstance(clause, str):
                continue
            clause_rows.setdefault(clause, {}).setdefault(row.get("probe_id"), []).append(row)
    clause_probe = {
        clause: {probe: _rate(entries) for probe, entries in sorted(probe_rows.items())}
        for clause, probe_rows in sorted(clause_rows.items())
    }

    weak_model = {}
    for agent in agents:
        pinned_rows = [r for r in installed if r.get("agent") == agent and
                       "-strong-" not in str(r.get("run_id", ""))]
        strong_rows = [r for r in rows if r.get("variant", "installed") == "installed"
                       and r.get("agent") == agent and
                       "-strong-" in str(r.get("run_id", ""))]
        pinned, strong = _rate(pinned_rows), _rate(strong_rows)
        delta = (None if pinned["rate"] is None or strong["rate"] is None else
                 round((pinned["rate"] - strong["rate"]) * 100, 1))
        weak_model[agent] = {"pinned_rate": pinned["rate"],
                             "strong_rate": strong["rate"],
                             "delta": delta, "delta_pp": delta,
                             "missing": pinned["missing"] or strong["missing"]}

    cross_end = {}
    for probe in probes:
        rates = [cell["rate"] for cell in adherence[probe].values()
                 if not cell["missing"]]
        if len(rates) < 2:
            cross_end[probe] = {"range_pp": None, "variance": None, "missing": True}
            continue
        mean = sum(rates) / len(rates)
        cross_end[probe] = {
            "range_pp": round((max(rates) - min(rates)) * 100, 1),
            "variance": round(sum((rate - mean) ** 2 for rate in rates) / len(rates), 4),
            "missing": False,
        }

    control_out = {}
    for probe in sorted({r.get("probe_id") for r in controls
                         if isinstance(r.get("probe_id"), str)}):
        control_out[probe] = control_delta(
            [r for r in installed if r.get("probe_id") == probe],
            [r for r in controls if r.get("probe_id") == probe])

    dates = sorted({str(r.get("started_at", ""))[:10] for r in rows
                    if str(r.get("started_at", ""))[:10]})
    skip = sum(1 for r in rows if r.get("verdict") not in _VALID_VERDICTS)
    return {"window": {"n": len(rows), "nights": dates, "skip": skip},
            "adherence": adherence, "mcp_usage": mcp_usage,
            "weak_model": weak_model, "cross_end": cross_end,
            "clause_probe": clause_probe, "control": control_out}


def _diff_row(view, key, baseline, current, clause_file=None,
              degrade_drop_pp=20.0, absolute_floor=0.70):
    drop = round((baseline - current) * 100, 1)
    return {"view": view, "key": key, "baseline": baseline, "current": current,
            "drop_pp": drop,
            "red": drop >= degrade_drop_pp or current < absolute_floor,
            "clause_file": clause_file}


def named_diff(agg: dict, baseline: Optional[dict], degrade_drop_pp: float = 20.0,
               absolute_floor: float = 0.70) -> list:
    """返回基线存在且当前可测的双键 diff；缺失基线/缺测永不判红。"""
    diff = []
    if not baseline:
        for probe, cells in sorted(agg.get("adherence", {}).items()):
            for agent, cell in sorted(cells.items()):
                if not cell.get("missing"):
                    diff.append({"view": "probe_agent", "key": f"{probe}@{agent}",
                                 "baseline": None, "current": cell["rate"],
                                 "drop_pp": None, "red": False, "clause_file": None})
        return diff
    for probe, cells in sorted(baseline.get("probe_agent", {}).items()):
        if not isinstance(cells, dict):
            continue
        for agent, base_rate in sorted(cells.items()):
            cell = agg.get("adherence", {}).get(probe, {}).get(agent)
            if cell is None or cell.get("missing") or not _safe_rate(base_rate):
                continue
            diff.append(_diff_row("probe_agent", f"{probe}@{agent}", base_rate,
                                  cell["rate"], degrade_drop_pp=degrade_drop_pp,
                                  absolute_floor=absolute_floor))
    for clause, probes in sorted(baseline.get("clause_probe", {}).items()):
        if not isinstance(probes, dict):
            continue
        for probe, base_rate in sorted(probes.items()):
            cell = agg.get("clause_probe", {}).get(clause, {}).get(probe)
            if cell is None or cell.get("missing") or not _safe_rate(base_rate):
                continue
            diff.append(_diff_row("clause_probe", f"{clause}#{probe}", base_rate,
                                  cell["rate"], clause.split("#", 1)[0],
                                  degrade_drop_pp, absolute_floor))
    return diff


def _pct(value):
    return f"{value * 100:.0f}%" if value is not None else "—缺测"


def render_markdown(agg: dict, diff: list, baseline_note: Optional[str] = None,
                    streaks: Optional[list] = None, global_drift: Optional[dict] = None) -> str:
    """渲染含缺测、连续失败告警、对照组及全局漂移观测的 Markdown 报告。"""
    lines = ["# eval 夜间报告（滚动 7 夜聚合）", ""]
    if streaks:
        lines += ["## ⚠️ 置顶告警：连续 ≥3 夜失败端", ""]
        lines += [f"- **{AGENT_NAMES.get(agent, agent)}**：连续失败，请检查登录态/配额/适配器" for agent in streaks]
        lines.append("")
    if baseline_note:
        lines += [f"> {baseline_note}", ""]
    adherence = agg.get("adherence", {})
    agents = sorted({agent for cells in adherence.values() for agent in cells})
    lines += ["## 1. 规则遵循率矩阵（探针 × 端）",
              "| 探针 | " + " | ".join(agents) + " |",
              "|---" * (len(agents) + 1) + "|"]
    for probe, cells in sorted(adherence.items()):
        lines.append("| " + " | ".join([PROBE_NAMES.get(probe, probe)] +
                    [_pct(cells.get(agent, {}).get("rate")) if
                     cells.get(agent, {}).get("missing", True) else
                     f"{cells[agent]['rate'] * 100:.0f}%（n={cells[agent]['n']}）"
                     for agent in agents]) + " |")
    lines += ["", "## 2. MCP 使用率（P2/P6/P7 × 端）"]
    for probe, cells in sorted(agg.get("mcp_usage", {}).items()):
        for agent, cell in sorted(cells.items()):
            lines.append(f"- {PROBE_NAMES.get(probe, probe)}@{agent}：" +
                         (f"{cell['rate'] * 100:.0f}%（n={cell['n']}）" if not cell.get("missing") else "—缺测"))
    lines += ["", "## 3. 弱模型保证度（端内 pinned vs strong 差值，pp）"]
    for agent, cell in sorted(agg.get("weak_model", {}).items()):
        if cell.get("missing"):
            lines.append(f"- {agent}：—缺测（strong 行未配置或未跑）")
        else:
            lines.append(f"- {agent}：pinned {_pct(cell['pinned_rate'])} vs strong {_pct(cell['strong_rate'])}，Δ={cell['delta']}pp")
    lines += ["", "## 4. 跨端一致性（各端 pinned 口径：极差/方差）"]
    for probe, cell in sorted(agg.get("cross_end", {}).items()):
        lines.append(f"- {PROBE_NAMES.get(probe, probe)}：" +
                     (f"极差 {cell['range_pp']}pp，方差 {cell['variance']}" if not cell.get("missing") else "—缺测"))
    lines += ["", "## 5. 对照组差值（规则边际效应）"]
    for probe, cell in sorted(agg.get("control", {}).items()):
        if cell.get("installed_rate") is None or cell.get("control_rate") is None:
            lines.append(f"- {PROBE_NAMES.get(probe, probe)}：—缺测")
        else:
            lines.append(f"- {PROBE_NAMES.get(probe, probe)}：安装组 {_pct(cell['installed_rate'])} vs 对照组 {_pct(cell['control_rate'])}（Δ{cell['delta_pp']}pp）")
    lines += ["", "## 6. 全局配置漂移（真实 HOME，HOME 策略 b 方案；观测不判红）"]
    if global_drift:
        for day in sorted(global_drift):
            paths = global_drift[day]
            lines.append(f"- {day}：" + "、".join(paths[:10]))
    else:
        lines.append("- 窗口内无漂移（或非 Tier-1 真实模式）")
    lines += ["", "## 7. 基线具名 diff（红灯=降幅超阈值或低于下限）"]
    if not diff:
        lines.append("- 无基线可比（首次运行或 schema 不兼容）")
    for entry in diff:
        name = entry["key"]
        if entry["view"] == "probe_agent":
            probe, agent = entry["key"].split("@", 1)
            name = f"{PROBE_NAMES.get(probe, probe)}@{AGENT_NAMES.get(agent, agent)}"
        mark = "▼" if entry["red"] else "·"
        lines.append(f"- {mark} {name}: {_pct(entry['baseline']) if entry['baseline'] is not None else '—'}→{_pct(entry['current'])}" +
                     (f"（{entry['clause_file']}）" if entry.get("clause_file") else ""))
    reds = [entry for entry in diff if entry["red"]]
    if reds:
        lines += ["", f"**红灯 {len(reds)} 项**"]
    return "\n".join(lines) + "\n"


def _load_global_drift(nightly_root: Path, window_nights: int = 7,
                       end_date: Optional[str] = None) -> dict:
    """加载滚动窗口内各夜真实 HOME 漂移；漂移只观测，不进入红灯。"""
    end = date.fromisoformat(end_date) if end_date else date.today()
    out = {}
    for offset in range(max(0, window_nights)):
        day = (end - timedelta(days=offset)).isoformat()
        path = Path(nightly_root) / day / "global-config-drift.json"
        if not path.is_file():
            continue
        try:
            changed = json.loads(path.read_text(encoding="utf-8")).get("changed", [])
        except (OSError, ValueError, TypeError):
            continue
        if isinstance(changed, list) and changed:
            out[day] = [str(item) for item in changed]
    return out


def write_report(base_dir: Path, baseline_path: Optional[Path], config_dir: Optional[Path] = None,
                 end_date: Optional[str] = None) -> int:
    """写滚动报告；只读基线，返回红灯或无数据状态码。"""
    base_dir = Path(base_dir)
    policy = {"degrade_drop_pp": 20.0, "absolute_floor": 0.70, "window_nights": 7}
    if config_dir:
        policy.update(json.loads((Path(config_dir) / "policy.json").read_text(encoding="utf-8")))
    results = load_results(base_dir / "reports" / "nightly", policy["window_nights"], end_date)
    if not results:
        print("[report] 窗口内无结果数据")
        return 1
    agg = aggregate(results)
    baseline, note = None, None
    if baseline_path and Path(baseline_path).is_file():
        baseline, note = schema.load_baseline(Path(baseline_path))
        if note:
            print(f"[report] {note}")
    diff = named_diff(agg, baseline, policy["degrade_drop_pp"], policy["absolute_floor"])
    from eval.runner import guards
    streaks = guards.streak_alerts(base_dir / "reports" / "state" / "streaks.json")
    end_day = end_date or date.today().isoformat()
    global_drift = _load_global_drift(base_dir / "reports" / "nightly", policy["window_nights"], end_day)
    md = render_markdown(agg, diff, baseline_note=note, streaks=streaks, global_drift=global_drift)
    out_dir = base_dir / "reports" / "eval" / end_day
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps({"aggregate": agg, "diff": diff,
                    "global_config_drift": global_drift, "baseline_note": note},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "report.md").write_text(md, encoding="utf-8")
    red = [entry for entry in diff if entry["red"]]
    print(f"[report] 输出 {out_dir}/report.md；红灯 {len(red)} 项")
    return 1 if red else 0


def candidate_baseline(base_dir: Path, out_path: Path, end_date: Optional[str] = None) -> int:
    """从当前窗口生成候选基线；绝不把候选写入生效基线。"""
    base_dir = Path(base_dir)
    results = load_results(base_dir / "reports" / "nightly", end_date=end_date)
    if not results:
        print("[baseline] 窗口内无结果数据")
        return 1
    agg = aggregate(results)
    probe_agent = {probe: {agent: cell["rate"] for agent, cell in cells.items()
                           if not cell["missing"]}
                   for probe, cells in agg["adherence"].items()}
    clause_probe = {clause: {probe: cell["rate"] for probe, cell in cells.items()
                             if not cell["missing"]}
                    for clause, cells in agg["clause_probe"].items()}
    doc = {"schema_version": schema.SCHEMA_VERSION,
           "created_at": date.today().isoformat(), "probe_agent": probe_agent,
           "clause_probe": clause_probe, "control": agg["control"]}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[baseline] 候选基线已生成：{out_path}（审阅后提交为 eval/baselines/baseline.json 才生效）")
    return 0
