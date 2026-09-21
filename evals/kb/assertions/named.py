"""具名期望断言（F1–F10 → N1–N10）。
--stage 控制断言子集；--phase init|post-update 分期望；--variant full|min。
"""
import re
import sys
import argparse
from pathlib import Path
from common import Result, kb_files, matrix_rows

STAGE_N = {"bootstrap": [], "base-info": [], "api": ["N4"], "pages": [],
           "overview": ["N1", "N2", "N3", "N5", "N6", "N7", "N8"],
           "global-validation": ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"],
           "update": ["N9"]}

EMPTY_IMPL = ("", "无", "未提供", "{{实际聚合端点 API-*；为空=未实现，状态恒 proposed}}")


def cap_meta(text: str):
    status = re.search(r"\|\s*状态\s*\|\s*(proposed|verified|retired)", text)
    impl = re.search(r"implementation_api_ids[：:]\s*([^\n]*)", text)
    return (status.group(1) if status else None), (impl.group(1).strip() if impl else None)


EMPTY_IMPL = ("", "无", "未提供", "{{实际聚合端点 API-*；为空=未实现，状态恒 proposed}}")


def _impl_empty(impl):
    """空实现判定：显式空值，或"（空——…）/未实现…"形式的带证据说明空。"""
    return impl is None or impl in EMPTY_IMPL or \
        (impl is not None and (impl.startswith("（空") or "未实现" in impl[:30] or "未发现聚合" in impl[:40]))


def rules_text(kb: Path) -> str:
    d = kb / "business" / "rules"
    if not d.exists():
        return ""
    return "\n".join(p.read_text(encoding="utf-8") for p in d.glob("RULE-*.md"))


def run(kb: Path, stage: str, phase: str, variant: str) -> Result:
    r = Result()
    todo = list(STAGE_N.get(stage, []))
    if stage == "update":
        todo = ["N9"]
    if phase == "post-update":
        todo = ["N9", "N1"]
    t = kb_files(kb)
    caps_dir = kb / "capabilities"
    caps = sorted(caps_dir.glob("CAP-*.md")) if caps_dir.exists() else []
    cap_texts = [p.read_text(encoding="utf-8") for p in caps]
    m = t["matrix"] or ""
    allmd = "\n".join(p.read_text(encoding="utf-8") for p in kb.rglob("*.md"))
    if "N1" in todo:
        r.check("N1 CAP文档存在", len(caps) >= 1)
        for p, c in zip(caps, cap_texts):
            st, impl = cap_meta(c)
            if phase == "init":
                r.check(f"N1[{p.name}]状态proposed", st == "proposed", f"got {st}")
                r.check(f"N1[{p.name}]实现为空", _impl_empty(impl), f"impl={impl}")
            else:
                r.check(f"N1[{p.name}]非断链verified", st in ("proposed", "retired") or "待确认" in c, f"got {st}")
        if phase == "init":
            comp = [l for l in matrix_rows(m) if "COMPOSES" in l]
            ok = len(comp) >= 2 and all(l.split("|")[1].strip().startswith("CAP-") for l in comp if len(l.split("|")) > 2)
            r.check("N1 COMPOSES边2条且指向CAP来源对", ok, str(comp[:2]))
    if "N2" in todo:
        jk = [l for l in matrix_rows(m) if "JOIN_KEY" in l]
        r.check("N2 JOIN_KEY边存在且含待确认", bool(jk) and any("待确认" in l for l in jk), str(jk[:1]))
    if "N3" in todo:
        rd = kb / "business"
        rules = list((rd / "rules").glob("RULE-*.md")) if (rd / "rules").exists() else []
        flows = list((rd / "flows").glob("FLOW-*.md")) if (rd / "flows").exists() else []
        rule_txt = rules_text(kb)
        flow_txt = "\n".join(p.read_text(encoding="utf-8") for p in flows)
        r.check("N3 规则卡>=1", len(rules) >= 1, [p.name for p in rules])
        r.check("N3 取消不可发货规则", "不可发货" in rule_txt or ("不可发货" in allmd and rules))
        r.check("N3 流程>=1含状态流转", len(flows) >= 1 and "状态流转" in flow_txt)
        itfs = "\n".join(p.read_text(encoding="utf-8") for p in (kb / "interfaces").glob("*.md")) if (kb / "interfaces").exists() else ""
        r.check("N3 寄生注释原文保留", "已取消" in itfs)
    if "N4" in todo:
        r.check("N4 PRODUCES/CONSUMES边", "PRODUCES" in m and "CONSUMES" in m)
        r.check("N4 JOB稳定ID", ("JOB-" in m) or ("JOB-" in allmd))
    if "N5" in todo:
        r.check("N5 无明文敏感值", all(s not in allmd for s in
                ["Pr0d@Acct#2026", "Mq_2026_Order", "Dev_Only_123", "10.20.31.14"]))
        r.check("N5 redacted存在", "<redacted>" in allmd)
    if "N6" in todo:
        rt = rules_text(kb)
        r.check("N6 余额规则具名+ai-draft", ("余额不可为负" in rt) and ("ai-draft" in rt))
    if "N7" in todo:
        if variant == "full":
            blob = m + "\n" + rules_text(kb)
            r.check("N7 ref型证据@commit", bool(re.search(r"@[0-9a-f]{7,40}", blob)))
        else:
            r.check("N7 min变体跳过", True)
    if "N8" in todo:
        rd_txt = (kb / "README.md").read_text(encoding="utf-8") if (kb / "README.md").exists() else ""
        if variant == "full":
            r.check("N8 README标用户提供", "[用户提供" in rd_txt)
        else:
            r.check("N8 README记未提供", "未提供" in rd_txt)
    if "N9" in todo:
        ok = any(("待确认" in c or cap_meta(c)[0] == "retired") for c in cap_texts)
        r.check("N9 CAP失效(待确认/retired)", ok)
    r.check("N10 由探针阶段断言", True)
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb-products", required=True)
    ap.add_argument("--stage", default="global-validation")
    ap.add_argument("--phase", default="init")
    ap.add_argument("--variant", default="full")
    a = ap.parse_args()
    r = run(Path(a.kb_products), a.stage, a.phase, a.variant)
    sys.exit(0 if r.report("named") else 1)
