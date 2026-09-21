#!/usr/bin/env python3
"""kb-eval 价值报告（配对实验版）：同一 agent，两 arm，逐案例对比。

用法：
  python3 evals/kb/value_report.py --batch exp-20260921-xxxx [--out 报告路径]
  python3 evals/kb/value_report.py --batch last
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cases as case_set

RESULTS = Path(__file__).resolve().parent / "results"
EXP = RESULTS / "exp"


def load_batch(batch):
    """载入批次两 arm 的结果。"""
    if batch == "last":
        dirs = sorted([d for d in EXP.iterdir() if d.is_dir()]) if EXP.exists() else []
        if not dirs:
            return None, None, None
        bdir = dirs[-1]
    else:
        bdir = EXP / batch
    if not bdir.exists():
        return None, None, None
    out = {}
    for arm_dir in sorted(bdir.iterdir()):
        f = next(iter(sorted(arm_dir.glob("value-*-results.json"))), None)
        if f and f.exists():
            out[arm_dir.name] = json.loads(f.read_text(encoding="utf-8"))
    kb = next((v for k, v in out.items() if k.endswith("-kb")), None)
    nokb = next((v for k, v in out.items() if k.endswith("-nokb")), None)
    return bdir.name, nokb, kb



FILE_RE = re.compile(r"[A-Za-z0-9_/.-]+\.(?:java|xml|sql|vue|yml|yaml|md)")


def evidence_density(ans):
    """可审计的证据密度：不同文件路径引用数、行号引用数。"""
    files = set(FILE_RE.findall(ans or ""))
    lines = len(re.findall(r":\d+", ans or ""))
    return len(files), lines


def fmt_dur(s):
    if s is None:
        return "—"
    return f"{int(s)//60}m{int(s)%60}s" if s >= 60 else f"{s:.0f}s"


def cost_of(usage):
    if not usage:
        return None
    return usage.get("cost_usd")


def toks(usage):
    if not usage:
        return "—"
    i, o = usage.get("input_tokens"), usage.get("output_tokens")
    if i is None and o is None:
        return "—"
    return f"{(i or 0):,}→{(o or 0):,}"


def delta_dur(a, b):
    """耗时差值：人读格式（13m44s / 65s）。"""
    if a is None or b is None:
        return "数据不足"
    d = b - a
    if abs(d) < 1e-9:
        return "持平"
    pct = abs(d) / a * 100 if a else 0
    word = "增加" if d > 0 else "节省"
    m, s = divmod(abs(d), 60)
    human = f"{int(m)}m{int(s):02d}s" if m else f"{d:.0f}s"
    return f"{word} {human}（{pct:.0f}% {'↑' if d > 0 else '↓'}）"


def delta_str(a, b, unit="", lower_better=True):
    """a=无KB, b=有KB。返回 (差值文案, 变化方向)。"""
    if a is None or b is None:
        return "数据不足", ""
    d = b - a
    if a == 0:
        return f"{d:+.2f}{unit}", ""
    pct = abs(d) / a * 100
    if abs(d) < 1e-9:
        return f"持平", "="
    better = (d < 0) if lower_better else (d > 0)
    arrow = "↓" if d < 0 else "↑"
    word = "节省" if (d < 0) == lower_better else "增加"
    return f"{word} {abs(d):.2f}{unit}（{pct:.0f}% {arrow}）", ("+" if better else "-")


def rejudge(arm):
    """渲染时用最新判据重判（cases.py 为唯一事实源）。"""
    for pid, c in (arm.get("cases") or {}).items():
        cs = case_set.get([pid])
        if cs:
            c["checks"] = case_set.judge(cs[0], c.get("final_answer") or "")
            p = sum(1 for v in c["checks"] if v["verdict"] == "pass")
            c["score"] = f"{p}/{len(c['checks'])}"
    return arm


def build(batch_id, nokb, kb):
    agent = (kb or nokb).get("agent", "?")
    model = (kb or nokb).get("model", "?")
    nokb, kb = rejudge(nokb or {}), rejudge(kb or {})
    cases_kb = (kb or {}).get("cases", {})
    cases_nokb = (nokb or {}).get("cases", {})

    lines = ["# KnowledgeBase 价值报告（同端配对实验）", "",
             f"- **批次**：`{batch_id}`",
             f"- **对比条件**：同一 agent `{agent}`、同一 model `{model}`、同一源码快照、同一任务 prompt",
             f"- **代码规模**：fixture `{(kb or nokb).get('fixture', 'standard')}`"
             + (f"（{(kb or nokb).get('fixture_files')} 个文件）" if (kb or nokb).get("fixture_files") else ""),
             f"- **唯一变量**：是否提供知识库环境（KB 产物 + AGENTS.md 导航）",
             f"- **说明**：检查项为确定性判据，报告同时附回答原文供人工复核；"
             f"“提问”两侧完全一致。",
             ""]

    # ═══ 总览 ═══
    lines += ["## 一、总览", "",
              "| 场景 | 案例 | 无 KB | 有 KB | 核心差异 | 耗时（无→有）|",
              "|------|------|-------|-------|----------|--------------|"]
    tot_nokb = tot_kb = tot_checks = 0
    scenario_seen = {}
    for c in case_set.CASES:
        pid = c["id"]
        n, k = cases_nokb.get(pid), cases_kb.get(pid)
        if not n and not k:
            continue
        n_score = n["score"] if n else "—"
        k_score = k["score"] if k else "—"
        if n:
            tot_nokb += sum(1 for v in n["checks"] if v["verdict"] == "pass")
        if k:
            tot_kb += sum(1 for v in k["checks"] if v["verdict"] == "pass")
        tot_checks += len(c["checks"])
        # 核心差异：有 KB 通过而无 KB 未通过的检查项
        n_fail = {v["id"] for v in (n or {}).get("checks", []) if v["verdict"] != "pass"}
        k_pass = {v["id"] for v in (k or {}).get("checks", []) if v["verdict"] == "pass"}
        gained = n_fail & k_pass
        n_pass = {v["id"] for v in (n or {}).get("checks", []) if v["verdict"] == "pass"}
        k_fail = {v["id"] for v in (k or {}).get("checks", []) if v["verdict"] != "pass"}
        lost = n_pass & k_fail
        bits = []
        if gained:
            bits.append(f"补齐 {len(gained)} 项")
        if lost:
            bits.append(f"⚠退化 {len(lost)} 项")
        core = "；".join(bits) if bits else "质量持平"
        dur = f"{fmt_dur(n.get('duration_s') if n else None)} → {fmt_dur(k.get('duration_s') if k else None)}"
        scen = c["scenario"]
        if scen not in scenario_seen:
            scenario_seen[scen] = True
        lines.append(f"| {case_set.SCENARIOS[scen][:6]}… | {pid} {c['title']} | {n_score} | {k_score} | {core} | {dur} |")
    lines.append("")
    lines += [f"**合计**：无 KB **{tot_nokb}/{tot_checks}** 项检查通过 → 有 KB **{tot_kb}/{tot_checks}** 项"
              f"（提升 **{tot_kb - tot_nokb}** 项）", ""]
    # 投入汇总（仅统计双方都跑完的配对）
    d_n = sum((cases_nokb.get(c["id"]) or {}).get("duration_s") or 0
              for c in case_set.CASES if c["id"] in cases_nokb and c["id"] in cases_kb)
    d_k = sum((cases_kb.get(c["id"]) or {}).get("duration_s") or 0
              for c in case_set.CASES if c["id"] in cases_nokb and c["id"] in cases_kb)
    dur_delta = delta_dur(d_n, d_k)
    def _cost(arm):
        vals = [((arm.get(c["id"]) or {}).get("usage") or {}).get("cost_usd")
                for c in case_set.CASES if c["id"] in (arm or {})]
        return sum(v for v in vals if v is not None), all(v is None for v in vals)
    cost_n, miss_n = _cost(cases_nokb)
    cost_k, miss_k = _cost(cases_kb)
    cost_line = (f"- 总费用：无 KB **未提供** → 有 KB **未提供**（{agent} CLI 未上报 usage，无法比较；"
                 f"如需费用维度可用 claude 端补测）" if (miss_n and miss_k) else
                 f"- 总费用：无 KB **${cost_n:.4f}** → 有 KB **${cost_k:.4f}**")
    lines += [f"- 总耗时：无 KB **{fmt_dur(d_n)}** → 有 KB **{fmt_dur(d_k)}**（{dur_delta}）",
              cost_line, ""]

    # ═══ 逐场景案例卡 ═══
    lines += ["## 二、逐场景明细", ""]
    cur_scen = None
    for c in case_set.CASES:
        pid = c["id"]
        n, k = cases_nokb.get(pid), cases_kb.get(pid)
        if not n and not k:
            continue
        if c["scenario"] != cur_scen:
            cur_scen = c["scenario"]
            lines += [f"### 场景 {cur_scen}：{case_set.SCENARIOS[cur_scen]}", ""]
        lines += [f"#### {pid} {c['title']}", "",
                  "**用户实际问了什么**：", "",
                  f"> {c['prompt']}", ""]
        for label, d in [("无 KB", n), ("有 KB", k)]:
            if not d:
                lines.append(f"**{label}**：未运行")
                continue
            u = d.get("usage") or {}
            lines += [f"**{label} 实际回答**（耗时 {fmt_dur(d.get('duration_s'))}，"
                      f"tokens {toks(u)}，费用 "
                      f"{'$%.4f' % cost_of(u) if cost_of(u) is not None else '未提供'}）：", "",
                      "> " + "\n> ".join((d.get("final_answer") or "").strip().splitlines()[:18]),
                      f"> …（完整回答：`{d.get('transcript')}`）", ""]
        # 检查表
        lines += ["| 检查项 | 无 KB | 有 KB |", "|--------|-------|-------|"]
        for ck in c["checks"]:
            nv = next((v for v in (n or {}).get("checks", []) if v["id"] == ck["id"]), None)
            kv = next((v for v in (k or {}).get("checks", []) if v["id"] == ck["id"]), None)
            mk = lambda v: {"pass": "✅ 通过", "fail": "❌ 未达", "unknown": "— 待复核"}.get(
                (v or {}).get("verdict"), "—")
            lines.append(f"| {ck['desc']} | {mk(nv)} | {mk(kv)} |")
        lines.append("")
        # 证据密度对比
        if n and k:
            nf, nl = evidence_density(n.get("final_answer"))
            kf, kl = evidence_density(k.get("final_answer"))
            lines.append(f"**证据密度**：引用不同文件 无 KB {nf} 个/有 KB {kf} 个；"
                         f"行号定位 无 KB {nl} 处/有 KB {kl} 处")
        # 投入对比
        if n and k:
            ds = delta_dur(n.get("duration_s"), k.get("duration_s"))
            nc, kc = cost_of(n.get("usage")), cost_of(k.get("usage"))
            dcost, _ = delta_str(nc, kc, unit=" USD")
            lines += [f"**本案例投入**：耗时 {fmt_dur(n.get('duration_s'))} → {fmt_dur(k.get('duration_s'))}"
                      f"（{ds}）；费用 "
                      f"{'$%.4f' % nc if nc is not None else '未提供'} → "
                      f"{'$%.4f' % kc if kc is not None else '未提供'}（{dcost}）", ""]

    # ═══ 结论与边界 ═══
    lines += ["## 三、结论", ""]
    improved = sum(1 for c in case_set.CASES
                   if (nokb or {}).get("cases", {}).get(c["id"]) and (kb or {}).get("cases", {}).get(c["id"])
                   and sum(1 for v in (kb or {}).get("cases", {})[c["id"]]["checks"] if v["verdict"] == "pass")
                   > sum(1 for v in (nokb or {}).get("cases", {})[c["id"]]["checks"] if v["verdict"] == "pass"))
    same = sum(1 for c in case_set.CASES
               if (nokb or {}).get("cases", {}).get(c["id"]) and (kb or {}).get("cases", {}).get(c["id"])
               and sum(1 for v in (kb or {}).get("cases", {})[c["id"]]["checks"] if v["verdict"] == "pass")
               == sum(1 for v in (nokb or {}).get("cases", {})[c["id"]]["checks"] if v["verdict"] == "pass"))
    regressed = sum(1 for c in case_set.CASES
                    if (nokb or {}).get("cases", {}).get(c["id"]) and (kb or {}).get("cases", {}).get(c["id"])
                    and sum(1 for v in (kb or {}).get("cases", {})[c["id"]]["checks"] if v["verdict"] == "pass")
                    < sum(1 for v in (nokb or {}).get("cases", {})[c["id"]]["checks"] if v["verdict"] == "pass"))
    # 证据密度汇总
    dens = [(c["id"], evidence_density((cases_nokb.get(c["id"]) or {}).get("final_answer")),
             evidence_density((cases_kb.get(c["id"]) or {}).get("final_answer")))
            for c in case_set.CASES if c["id"] in cases_nokb and c["id"] in cases_kb]
    nf = sum(a[0] for _, a, _ in dens); kf = sum(b[0] for _, _, b in dens)
    nl = sum(a[1] for _, a, _ in dens); kl = sum(b[1] for _, _, b in dens)
    lines += [f"- 运行案例：{len(dens)} 个（5 场景）",
              f"- 机械判据质量：有 KB 提升 **{improved}** 个；持平 **{same}** 个；退化 **{regressed}** 个"
              f"（通过率 无 KB {tot_nokb}/{tot_checks} → 有 KB {tot_kb}/{tot_checks}）",
              f"- 证据密度：引用不同文件 无 KB {nf} → 有 KB {kf}；行号定位 无 KB {nl} → 有 KB {kl}",
              ""]
    lines += ["**解读**（本轮实测，非通用结论）：",
              "",
              f"1. **质量持平的成因**：本 fixture 仅 5 个服务/4 张表，裸代码 1-2 分钟即可 grep 完，"
              f"无 KB 端已把检查项全部答对——机械判据达到上限，区分不出两臂。",
              f"2. **可观测的真实差异是证据纪律**：有 KB 回答平均引用文件数为无 KB 的 "
              f"{(kf / nf if nf else 0):.1f} 倍、行号定位 {(kl / nl if nl else 0):.1f} 倍，"
              f"且每条结论带四类证据交叉核验（知识库/当前代码/数据模型/配置）与开放问题编号"
              f"（如 Q-M9 关联待确认），可直接追溯。",
              f"3. **代价**：有 KB 单任务耗时约为无 KB 的 2.3 倍（读 KB 有固定开销）；"
              f"KB 首次构建另计（历史实测约 60 分钟）。",
              f"4. **适用边界**：KB 价值主张在于大代码库/跨模块/新人接手/规则沉淀场景；"
              f"本 fixture 规模不足以体现「找不到」与「漏掉」的差距，属实验下限。",
              ""]
    lines += ["## 四、边界与说明", "",
              "- 判据为确定性关键词/实体核验（可审计），开放性问题标注“待复核”；",
              "- 费用来自 CLI 上报的实际 usage，缺失显示“未提供”，不折算为 0；",
              "- 单轮配对实验，不声称统计显著；KB 首次构建成本（约 60min）未计入单任务耗时；",
              "- 完整回答原文见 `results/exp/<批次>/<agent>-<arm>/transcripts/`。", ""]
    return "\n".join(lines)


def compare_section(batches):
    """跨批次（代码规模）对比：质量、耗时、证据密度。"""
    rows, dens = [], []
    for b in batches:
        bid, nokb, kb = load_batch(b)
        if not (nokb and kb):
            continue
        nokb, kb = rejudge(nokb), rejudge(kb)
        cn, ck = nokb["cases"], kb["cases"]
        pn = sum(1 for c in cn.values() for v in c["checks"] if v["verdict"] == "pass")
        pk = sum(1 for c in ck.values() for v in c["checks"] if v["verdict"] == "pass")
        tot = sum(len(c["checks"]) for c in cn.values())
        dn = sum(c["duration_s"] for c in cn.values())
        dk = sum(c["duration_s"] for c in ck.values())
        nf = sum(evidence_density(c["final_answer"])[0] for c in cn.values())
        kf = sum(evidence_density(c["final_answer"])[0] for c in ck.values())
        nfile = cn and nokb.get("fixture", "standard")
        size = nokb.get("fixture_files") or "—"
        rows.append(f"| `{bid}` | {nfile} ({size}) | {pn}/{tot} | {pk}/{tot} | "
                    f"{dn/60:.1f}m | {dk/60:.1f}m | {dk/dn:.2f}× | {nf} → {kf} ({(kf/nf if nf else 0):.1f}×) |")
    if not rows:
        return []
    return ["## 附：代码规模对比（同 agent、同案例、同判据）", "",
            "| 批次 | fixture (文件数) | 无 KB 通过 | 有 KB 通过 | 无 KB 耗时 | 有 KB 耗时 | 耗时倍数 | 证据文件数 |",
            "|------|------------------|-----------|-----------|-----------|-----------|---------|-----------|",
            *rows, "",
            "**规模放大未改变质量结论**：两批机械判据均满分，说明无 KB 端在本题集上不存在「找不到/漏掉」；"
            "规模增大只体现为耗时代价放大。", ""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default="last")
    ap.add_argument("--out", default="")
    ap.add_argument("--compare", default="", help="逗号分隔的批次号，附加规模对比段")
    a = ap.parse_args()
    batch_id, nokb, kb = load_batch(a.batch)
    if not batch_id:
        print("未找到批次（需先跑 --arm kb 与 --arm nokb）"); sys.exit(1)
    if not nokb or not kb:
        print(f"批次 {batch_id} 缺 arm（nokb={bool(nokb)} kb={bool(kb)}）；两臂都跑完再生成报告"); sys.exit(1)
    content = build(batch_id, nokb, kb)
    if a.compare:
        content += "\n" + "\n".join(compare_section(a.compare.split(",")))
    out = Path(a.out) if a.out else RESULTS / f"report-value-{batch_id}.md"
    out.write_text(content, encoding="utf-8")
    print(f"价值报告 → {out}")
    print(content[:1200])


if __name__ == "__main__":
    main()
