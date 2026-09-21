"""Tier-0 结构断言。
--skill-src                          断言 skill 源契约
--kb-products <dir> [--stage <id>]   断言产物结构（按阶段子集）
阶段分级：bootstrap=manifest/输入；base-info+=矩阵/图；api+=接口索引；pages+=页面索引；global-validation/update=全部
"""
import re
import sys
import argparse
import yaml
from pathlib import Path
from common import Result, SKILL_ROOT, kb_files, matrix_rows

STAGE_LEVEL = {"bootstrap": 1, "base-info": 2, "api": 3, "pages": 4,
               "overview": 5, "global-validation": 6, "update": 6}
LEVEL_OF_CHECK = {"manifest存在": 1, "manifest合法YAML": 1, "documents域含business": 1,
                  "documents域含capabilities": 1, "输入七文件在位": 1,
                  "矩阵存在": 2, "矩阵表头六列": 2, "矩阵类型全在词表": 2,
                  "图derived_from": 2, "图边数==矩阵行数": 2, "图节点⊇矩阵两端": 2,
                  "接口索引进位": 3, "页面索引进位": 4}


def check_skill_src(r: Result):
    rt = (SKILL_ROOT / "knowledge-base-base-info/assets/relation-types.md").read_text(encoding="utf-8")
    vertical = re.findall(r"^\| `([A-Z_]+)` \|", rt.split("## 横向类型")[0].split("## 纵向类型")[1], re.M)
    horizontal = re.findall(r"^\| `([A-Z_]+)` \|", rt.split("## 横向类型")[1].split("自 2b")[0], re.M)
    allt = vertical + horizontal
    r.check("词表纵向11", len(vertical) == 11, f"got {len(vertical)}: {vertical}")
    r.check("词表横向3", len(horizontal) == 3, f"got {horizontal}")
    r.check("词表无重复", len(allt) == len(set(allt)))
    r.check("横向已启用标注", "已启用（2b）" in rt and "唯一合法写入方" in rt)
    for tpl, name in [("knowledge-base-base-info/assets/traceability-matrix-template.md", "矩阵模板"),
                      ("knowledge-base-overview/assets/rule-card-template.md", "规则卡模板"),
                      ("knowledge-base-overview/assets/flow-template.md", "流程模板"),
                      ("knowledge-base-overview/assets/capability-composition-template.md", "组合模板")]:
        lines = (SKILL_ROOT / tpl).read_text(encoding="utf-8").splitlines()
        tables, cur = [], []
        for ln in lines:
            if ln.strip().startswith("|"):
                cur.append(ln)
            elif cur:
                tables.append(cur); cur = []
        if cur:
            tables.append(cur)
        ok = bool(tables)
        for t in tables:
            if len(t) < 2:
                continue
            c = lambda s: len(s.strip().strip("|").split("|"))
            if c(t[0]) != c(t[1]):
                ok = False
        r.check(f"{name}表列一致", ok)
    mt = yaml.safe_load((SKILL_ROOT / "knowledge-base-bootstrap/assets/manifest-template.yaml").read_text(encoding="utf-8"))
    r.check("manifest模板合法", isinstance(mt, dict))
    r.check("manifest三新键", "business" in mt.get("documents", {}) and
            "capabilities" in mt.get("documents", {}) and
            "business_knowledge_sources" in mt.get("evidence", {}))
    ic = (SKILL_ROOT / "knowledge-base-bootstrap/references/input-contract.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)```", ic, re.S)
    ok = bool(blocks)
    for b in blocks:
        try:
            yaml.safe_load(b)
        except Exception:
            ok = False
    r.check("契约YAML块可解析", ok, f"{len(blocks)} blocks")
    sk = (SKILL_ROOT / "knowledge-base-bootstrap/SKILL.md").read_text(encoding="utf-8")
    life = set(re.findall(r"`([\w\-./]+/?)`", sk.split("固定产物包括")[1].split("。")[0]))
    det = set(re.findall(r"`([\w\-./]+/?)`", ic.split("检测集合为：")[1].split("。")[0]))
    r.check("固定产物两副本一致", life == det, str(life ^ det))
    for d in ["business", "capabilities", "evidence"]:
        r.check(f"副本含{d}", f"{d}/" in life or d in life, str(sorted(life)))


def check_products(r: Result, kb: Path, stage: str):
    lvl = STAGE_LEVEL.get(stage, 6)
    t = kb_files(kb)

    def L(name):
        return LEVEL_OF_CHECK.get(name, 6) <= lvl

    if L("manifest存在"):
        r.check("manifest存在", t["manifest"] is not None)
        ok = False
        if t["manifest"]:
            try:
                mf = yaml.safe_load(t["manifest"])
                ok = isinstance(mf, dict)
                r.check("documents域含business", ok and "business" in mf.get("documents", {}))
                r.check("documents域含capabilities", ok and "capabilities" in mf.get("documents", {}))
            except Exception:
                ok = False
        r.check("manifest合法YAML", ok)
        ui = kb / "user-input"
        need = ["base-info.md", "project-scope.md", "data-model-scope.md", "configuration-scope.md",
                "middleware-scope.md", "api-scope.md", "page-scope.md"]
        r.check("输入七文件在位", all((ui / f).exists() for f in need),
                [f for f in need if not (ui / f).exists()])
    if L("矩阵存在"):
        m = t["matrix"]
        r.check("矩阵存在", m is not None)
        if m:
            hdr = [l for l in m.splitlines() if l.strip().startswith("| 来源稳定 ID")]
            r.check("矩阵表头六列", bool(hdr) and len(hdr[0].strip().strip("|").split("|")) == 6)
            rows = matrix_rows(m)
            rt = (SKILL_ROOT / "knowledge-base-base-info/assets/relation-types.md").read_text(encoding="utf-8")
            allowed = set(re.findall(r"^\| `([A-Z_]+)` \|", rt, re.M))
            bad = [l for l in rows if l.strip().strip("|").split("|")[1].strip().strip("`") not in allowed]
            r.check("矩阵类型全在词表", not bad, str(bad[:2]))
            g = t["graph"]
            if g and L("图derived_from"):
                gy = yaml.safe_load(g)
                r.check("图derived_from", str(gy.get("derived_from", "")).endswith("traceability-matrix.md"))
                r.check("图边数==矩阵行数", len(gy.get("edges", [])) == len(rows),
                        f"edges={len(gy.get('edges', []))} rows={len(rows)}")
                mids = set()
                for l in rows:
                    p = [x.strip() for x in l.strip().strip("|").split("|")]
                    mids |= {p[0], p[2]}
                r.check("图节点⊇矩阵两端", mids <= {n["id"] for n in gy.get("nodes", [])}, str(sorted(mids)[:3]))
    if L("接口索引进位"):
        r.check("接口索引进位", t["interfaces_idx"] is not None and "对外能力" in (t["interfaces_idx"] or ""))
    if L("页面索引进位"):
        r.check("页面索引进位", (kb / "pages/README.md").exists())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-src", action="store_true")
    ap.add_argument("--kb-products")
    ap.add_argument("--stage", default="update")
    a = ap.parse_args()
    r = Result()
    if a.skill_src:
        check_skill_src(r)
    if a.kb_products:
        check_products(r, Path(a.kb_products), a.stage)
    sys.exit(0 if r.report("tier0") else 1)
