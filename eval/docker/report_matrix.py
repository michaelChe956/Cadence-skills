#!/usr/bin/env python3
"""Docker 夜测透视：总览 → 分组矩阵 → 均时参考 → 基线对比 → 降级注记。

用法: python3 eval/docker/report_matrix.py [--base eval/results/docker-night] [--day YYYY-MM-DD|all]
数据源: <base>/reports/nightly/<date>/runs/docker-*.json（schema 1.0 结果）
看点设计:
  - 总览一眼看端健康度（通过/失败/通过率/降级）
  - 矩阵按 P 组（规则遵循）/ R 组（规则加载）/ 安装产物（stage1）分组,
    格内 ✅全过/⚠️部分/❌全挂 + 通过数/轮次
  - 均时取中位数（抗重试长尾）
"""
import argparse
import glob
import json
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

AGENTS = ("claude", "codex", "pi", "kimi", "omp")

try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from eval.probes.definitions import PROBES
    _PROBE_NAMES = {pid: d["name"] for pid, d in PROBES.items()}
except Exception:  # 独立运行兜底（无包上下文时只显示 ID）
    _PROBE_NAMES = {}


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


def _cell_symbol(ok: int, n: int) -> str:
    if n == 0:
        return "—"
    if ok == n:
        return "✅"
    if ok == 0:
        return "❌"
    return "⚠️"


def _probe_group(pid: str) -> str:
    if pid == "stage1":
        return "安装产物（stage1 确定性断言）"
    if pid == "resident":
        return "渐进受控（常载审计）"
    if pid.startswith("P"):
        return "P 组（规则遵循）"
    if pid.startswith("R"):
        return "R 组（规则加载）"
    return "其他"


def _probe_label(pid: str) -> str:
    if pid == "stage1":
        return "stage1 安装产物断言"
    if pid == "resident":
        return "claude 常载审计（session_start 仅常驻桶+目录页+入口）"
    if pid in _PROBE_NAMES:
        return f"{pid} {_PROBE_NAMES[pid]}"
    return f"{pid}（已撤销 · 历史记录）"

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

    days = sorted({r["_day"] for r in rows})
    # 聚合：agent → probe → [(verdict, duration)]
    cell = defaultdict(list)
    agent_pass = defaultdict(lambda: [0, 0])  # agent -> [pass, total]
    for r in rows:
        verdict = r.get("verdict", "?")
        dur = float(r.get("duration_s") or 0)
        a, p = r.get("agent", "?"), r.get("probe_id", "?")
        cell[(a, p)].append((verdict, dur))
        agent_pass[a][1] += 1
        if verdict == "PASS":
            agent_pass[a][0] += 1

    probes = sorted({p for (_, p) in cell},
                    key=lambda p: ({"P": 0, "R": 1}.get(p[0], 2 if p != "resident" else 1.5), p))
    used_agents = [a for a in AGENTS if any(k[0] == a for k in cell)]
    degrades = sorted({(r.get("agent", "?"), r.get("degrade"))
                       for r in rows if r.get("degrade")})

    span = days[0] if len(days) == 1 else f"{days[0]}~{days[-1]}"
    print(f"## Docker 夜测透视（{span} · {len(rows)} 条记录 · {len(used_agents)} 端）\n")

    # --- 总览：端健康度 ---
    print("### 总览")
    print("| 端 | 通过/总数 | 通过率 | 降级 |")
    print("|---|---|---|---|")
    tot_ok = tot_n = 0
    for a in used_agents:
        ok, n = agent_pass[a]
        tot_ok, tot_n = tot_ok + ok, tot_n + n
        dg = "⚠️" if any(d[0] == a for d in degrades) else "—"
        print(f"| {a} | {ok}/{n} | {ok / n:.0%} | {dg} |")
    print(f"| **合计** | **{tot_ok}/{tot_n}** | **{tot_ok / tot_n:.0%}** | "
          f"{'⚠️' if degrades else '—'} |")

    # --- 矩阵：分组 + 状态符号 ---
    print("\n### 结果矩阵（✅ 全过 · ⚠️ 部分过 · ❌ 全挂 · — 未跑；格=通过数/轮次）")
    print("| 探针 | " + " | ".join(used_agents) + " |")
    print("|---|" + "---|" * len(used_agents))
    current_group = None
    for p in probes:
        grp = _probe_group(p)
        if grp != current_group:
            print(f"| **{grp}** |" + " |" * len(used_agents))
            current_group = grp
        cols = []
        for a in used_agents:
            runs = cell.get((a, p), [])
            n = len(runs)
            ok = sum(1 for v, _ in runs if v == "PASS")
            cols.append("—" if n == 0 else f"{_cell_symbol(ok, n)} {ok}/{n}")
        print(f"| {_probe_label(p)} | " + " | ".join(cols) + " |")

    # --- 均时参考（中位数，抗重试长尾） ---
    print("\n### 均时参考（s · 中位数）")
    print("| 探针 | " + " | ".join(used_agents) + " |")
    print("|---|" + "---|" * len(used_agents))
    for p in probes:
        cols = []
        for a in used_agents:
            runs = cell.get((a, p), [])
            durs = [d for _, d in runs]
            cols.append(f"{statistics.median(durs):.0f}" if durs else "—")
        print(f"| {_probe_label(p)} | " + " | ".join(cols) + " |")

    # --- 基线对比 ---
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
        print("\n### 基线对比\n" + ("；".join(drift) if drift else "无降级 ✅"))

    # --- 降级注记 ---
    if degrades:
        notes = "；".join(f"{a} 考场降级：{d}" for a, d in degrades)
        print(f"\n### 降级注记\n> ⚠️ {notes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
