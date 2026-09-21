"""反例断言：产物中不得存在的内容。"""
import re
import sys
import argparse
from pathlib import Path
from common import Result

SECRETS = ["Pr0d@Acct#2026", "Mq_2026_Order", "Dev_Only_123", "10.20.31.14", "mq.internal.demo.local"]


def run(kb: Path) -> Result:
    r = Result()
    texts = [p.read_text(encoding="utf-8") for p in kb.rglob("*.md")]
    texts += [p.read_text(encoding="utf-8") for p in kb.rglob("*.yaml")]
    blob = "\n".join(texts)
    for s in SECRETS:
        r.check(f"反例:无敏感值[{s[:6]}…]", s not in blob)
    m = kb / "evidence" / "traceability-matrix.md"
    if m.exists():
        for l in m.read_text(encoding="utf-8").splitlines():
            p = [x.strip() for x in l.strip().strip("|").split("|")]
            if len(p) >= 3 and p[1].strip("`") == "COMPOSES":
                r.check("反例:COMPOSES源为CAP", p[0].startswith("CAP-"), l)
    for cap in kb.glob("capabilities/CAP-*.md"):
        c = cap.read_text(encoding="utf-8")
        st = re.search(r"\|\s*状态\s*\|\s*(\w+)", c)
        impl = re.search(r"implementation_api_ids[：:]\s*([^\n]*)", c)
        empty = (not impl) or (impl.group(1).strip() in
                ("", "无", "未提供", "{{实际聚合端点 API-*；为空=未实现，状态恒 proposed}}"))
        r.check(f"反例:空实现不得verified[{cap.name}]", not (empty and st and st.group(1) == "verified"))
    br = kb / "business/README.md"
    if br.exists():
        bt = br.read_text(encoding="utf-8")
        bad = [l for l in bt.splitlines()
               if re.search(r"(RULE-|FLOW-|CAP-)", l) and "ai-draft" in l
               and re.search(r"\|\s*confirmed\s*\|", l)]
        r.check("反例:ai-draft不被标confirmed", not bad, str(bad[:1]))
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb-products", required=True)
    a = ap.parse_args()
    r = run(Path(a.kb_products))
    sys.exit(0 if r.report("negative") else 1)
