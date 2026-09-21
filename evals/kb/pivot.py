#!/usr/bin/env python3
"""kb-eval 技术层透视报告：扫描 results/ 全部运行，生成跨端×跨项×跨轮次透视表。

价值层报告（同端配对实验）见 evals/kb/value_report.py。

用法：python3 evals/kb/pivot.py [--out report-pivot.md]
"""
import argparse
import json
import sys
from pathlib import Path

RESULTS_ROOT = Path(__file__).resolve().parents[0] / "results"
STAGES = ["bootstrap", "base-info", "api", "pages", "overview", "global-validation"]
PROBES = [f"P{i}" for i in range(1, 10)]
PROBE_NAMES = {
    "P1": "组合查询", "P2": "规则检索", "P3": "变更更新", "P4": "漂移分级",
    "P5": "字段变更Coding", "P6": "余额Debug", "P7": "影响评估", "P8": "方案设计", "P9": "Review",
}


def load_runs():
    """扫描 results/<日期>/<端>-<变体>/results.json → [(日期, 端, 变体, data)]"""
    runs = []
    if not RESULTS_ROOT.exists():
        return runs
    for date_dir in sorted(RESULTS_ROOT.iterdir()):
        if not date_dir.is_dir():
            continue
        for run_dir in sorted(date_dir.iterdir()):
            rf = run_dir / "results.json"
            if not rf.exists():
                continue
            try:
                d = json.loads(rf.read_text(encoding="utf-8"))
                agent, _, variant = run_dir.name.partition("-")
                runs.append({"date": date_dir.name, "agent": agent,
                             "variant": variant or "full", "dir": run_dir.name, "data": d})
            except Exception:
                continue
    return runs


def mark(v):
    if v is None:
        return " — "
    if isinstance(v, dict) and v.get("blocked"):
        return " ⏸ "
    return " ✅ " if (isinstance(v, dict) and v.get("ok")) else " ❌ "


def fmt_s(v):
    if not isinstance(v, dict):
        return "—"
    s = v.get("duration_s")
    return f"{s:.0f}" if isinstance(s, (int, float)) else "—"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    runs = load_runs()
    if not runs:
        print("无运行数据"); sys.exit(1)

    runs = load_runs()
    if not runs:
        print("无运行数据"); sys.exit(1)

    lines = ["# kb-eval 透视报告", ""]
    dates = sorted({r["date"] for r in runs})

    # ═══ ① 端 × 项 通过矩阵（最新一轮 each 端）═══
    lines += ["## 一、端 × 项 通过矩阵（各端最新一轮）", ""]
    latest = {}
    for r in runs:
        key = r["agent"]
        if key not in latest:
            latest[key] = r
        elif r["variant"] == "full" and latest[key]["variant"] != "full":
            latest[key] = r  # 完整跑优先
        elif r["variant"] == latest[key]["variant"] and r["date"] > latest[key]["date"]:
            latest[key] = r
    agents = sorted(latest)
    if agents:
        lines.append("| 项 | " + " | ".join(a.center(14) for a in agents) + " |")
        lines.append("|---|" + "---|" * len(agents))
        for s in STAGES:
            row = [s]
            for ag in agents:
                row.append(mark(latest[ag]["data"].get("stages", {}).get(s)).center(14))
            lines.append("| " + " | ".join(row) + " |")
        for p in PROBES:
            row = [f"{p} {PROBE_NAMES[p]}"]
            for ag in agents:
                row.append(mark(latest[ag]["data"].get("probes", {}).get(p)).center(14))
            lines.append("| " + " | ".join(row) + " |")
        # 合计
        row = ["**合计**"]
        for ag in agents:
            d = latest[ag]["data"]
            n = sum(1 for s in STAGES if d.get("stages", {}).get(s, {}).get("ok")) + \
                sum(1 for p in PROBES if d.get("probes", {}).get(p, {}).get("ok"))
            row.append(f"**{n}/15**".center(14))
        lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    # ═══ ② 阶段 × 端 耗时（秒）═══
    lines += ["## 二、阶段 × 端 耗时（秒，最新一轮）", ""]
    if agents:
        lines.append("| 阶段 | " + " | ".join(a.center(10) for a in agents) + " |")
        lines.append("|---|" + "---|" * len(agents))
        for s in STAGES:
            row = [s]
            for ag in agents:
                row.append(fmt_s(latest[ag]["data"].get("stages", {}).get(s)).center(10))
            lines.append("| " + " | ".join(row) + " |")
        total_row = ["**总时长**"]
        for ag in agents:
            d = latest[ag]["data"]
            t = sum(v.get("duration_s", 0) for v in d.get("stages", {}).values()) + \
                sum(v.get("duration_s", 0) for v in d.get("probes", {}).values())
            total_row.append(f"**{t / 60:.0f}min**".center(10))
        lines.append("| " + " | ".join(total_row) + " |")
        lines.append("")

    # ═══ ③ 基线具名 diff（stages + probes）═══
    lines += ["## 三、对基线具名 diff（最新 vs baseline，仅列变化项）", ""]
    any_diff = False
    for ag in agents:
        r = latest[ag]
        bf = r["dir"] and (RESULTS_ROOT / r["date"] / r["dir"] / "baseline-results.json")
        d = r["data"]
        diffs = []
        for kind, keys in [("stage", STAGES), ("probe", PROBES)]:
            for k in keys:
                cur = d.get(f"{kind}s", {}).get(k, {})
                cur_ok = cur.get("ok") if cur else None
                base_ok = None
                if bf and bf.exists():
                    try:
                        bl = json.loads(bf.read_text(encoding="utf-8"))
                        bv = bl.get(f"{kind}s", {}).get(k, {})
                        base_ok = bv.get("ok") if bv else None
                    except Exception:
                        pass
                if base_ok is not None and cur_ok is not None and base_ok != cur_ok:
                    arrow = "PASS→FAIL ▼" if base_ok else "FAIL→PASS ▲"
                    diffs.append(f"{kind} {k}: {arrow}")
        if diffs:
            any_diff = True
            lines.append(f"**{ag}**: " + "；".join(diffs))
    if not any_diff:
        lines.append("无变化（全部与基线一致）")
    lines.append("")

    # ═══ ④ 历史轮次追踪 ═══
    if len(dates) > 1 or len(runs) > len(agents):
        lines += ["## 四、历史轮次追踪", ""]
        lines.append("| 日期 | 端 | 变体 | 阶段通过 | 探针通过 | 总时长 |")
        lines.append("|-----|---|------|---------|---------|--------|")
        for r in runs:
            d = r["data"]
            sp = f"{sum(1 for s in STAGES if d.get('stages', {}).get(s, {}).get('ok'))}/6"
            pp = f"{sum(1 for p in PROBES if d.get('probes', {}).get(p, {}).get('ok'))}/9"
            t = sum(v.get('duration_s', 0) for v in d.get('stages', {}).values()) + \
                sum(v.get('duration_s', 0) for v in d.get('probes', {}).values())
            lines.append(f"| {r['date']} | {r['agent']} | {r['variant']} | {sp} | {pp} | {t / 60:.0f}min |")
        lines.append("")

    # ═══ ⑤ 失败项定位 ═══
    lines += ["## 五、失败项定位（最新一轮）", ""]
    any_fail = False
    for ag in agents:
        d = latest[ag]["data"]
        for kind, keys in [("stages", STAGES), ("probes", PROBES)]:
            for k in keys:
                v = d.get(kind, {}).get(k, {})
                if v and not v.get("ok") and not v.get("blocked"):
                    any_fail = True
                    fails = v.get("failures") or ["断言失败"]
                    t = v.get("transcript", "")
                    lines.append(f"- **{ag} / {k}**: {'; '.join(str(f)[:120] for f in fails[:2])}")
                    if t:
                        lines.append(f"  - transcript: `{latest[ag]['dir']}/{t}`")
    if not any_fail:
        lines.append("全部通过 ✅")
    lines.append("")

    out = Path(a.out) if a.out else RESULTS_ROOT / "report-pivot.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"透视报告 → {out}")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
