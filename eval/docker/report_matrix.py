#!/usr/bin/env python3
"""Docker 夜测透视汇总：按 端×探针 聚合成功率与时长，输出 markdown 表。

用法: python3 eval/docker/report_matrix.py [--base eval/results/docker-night]
数据源: <base>/reports/nightly/<date>/runs/docker-*.json（schema 1.0 结果）
"""
import argparse
import glob
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

AGENTS = ("claude", "codex", "pi", "kimi")


def load_runs(base: Path) -> list:
    rows = []
    for path in sorted(glob.glob(str(base / "reports/nightly/*/runs/docker-*.json"))):
        try:
            d = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and isinstance(d.get("run_id"), str):
            d["_day"] = Path(path).parts[-3]
            rows.append(d)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="eval/results/docker-night")
    ap.add_argument("--day", default=date.today().isoformat(),
                    help="只统计该日期（默认今天）；all 为全部")
    args = ap.parse_args()
    base = Path(args.base)

    rows = load_runs(base)
    if args.day != "all":
        rows = [r for r in rows if r["_day"] == args.day]
    if not rows:
        print(f"无结果数据（base={base} day={args.day}）")
        return 1

    # 聚合：agent → probe → [(verdict, duration)]
    cell = defaultdict(list)
    for r in rows:
        det = r.get("details", {})
        cell[(r.get("agent", "?"), r.get("probe_id", "?"))].append(
            (r.get("verdict", "?"), float(r.get("duration_s") or 0)))

    probes = sorted({p for (_, p) in cell})
    used_agents = [a for a in AGENTS if any(k[0] == a for k in cell)]

    print(f"## Docker 夜测透视（{args.day}，{len(rows)} 条运行记录）\n")
    print("| 探针 | " + " | ".join(
        f"{a} 成功率 | {a} 均时(s) | {a} 轮次" for a in used_agents) + " |")
    print("|---|" + "---|" * (3 * len(used_agents)))
    for p in probes:
        cols = []
        for a in used_agents:
            runs = cell.get((a, p), [])
            n = len(runs)
            ok = sum(1 for v, _ in runs if v == "PASS")
            rate = f"{ok}/{n}" if n else "—"
            avg = f"{sum(d for _, d in runs)/n:.0f}" if n else "—"
            cols += [rate, avg, str(n)]
        print(f"| {p} | " + " | ".join(cols) + " |")

    # 总览行
    print("| **合计** | " + " | ".join(
        (lambda runs: f"**{sum(1 for v,_ in runs if v=='PASS')}/{len(runs)}**")(
            [r for (aa, _), lst in cell.items() if aa == a for r in lst])
        for a in used_agents) + " |")

    # stage1 时长（从 log 无落盘，此处只统计探针）；补基线对比
    bl_path = Path("eval/baselines/baseline.json")
    if bl_path.exists():
        bl = json.loads(bl_path.read_text(encoding="utf-8"))
        drift = []
        for p in probes:
            for a in used_agents:
                base_rate = bl.get("probe_agent", {}).get(p, {}).get(a)
                if base_rate is None:
                    continue
                runs = cell.get((a, p), [])
                if not runs:
                    continue
                cur = sum(1 for v, _ in runs if v == "PASS") / len(runs)
                if cur < base_rate:
                    drift.append(f"{a}/{p}: 基线 {base_rate:.0%} → 当前 {cur:.0%}")
        print("\n基线对比：" + ("；".join(drift) if drift else "无降级 ✅"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
