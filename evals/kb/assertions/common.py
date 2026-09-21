"""kb-eval 断言公共库。"""
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[3] / "cadence-init" / "skills"


class Result:
    def __init__(self):
        self.items = []  # dict(name, ok, detail)

    def check(self, name, ok, detail=""):
        self.items.append({"name": name, "ok": bool(ok), "detail": str(detail)})
        return bool(ok)

    def failed_names(self):
        return [i["name"] for i in self.items if not i["ok"]]

    def report(self, title):
        fail = self.failed_names()
        print(f"[{title}] PASS {len(self.items) - len(fail)} FAIL {len(fail)}")
        for i in self.items:
            if not i["ok"]:
                print(f"  FAIL: {i['name']} {i['detail']}")
        return len(fail) == 0


def kb_files(kb: Path) -> dict:
    """读取知识库产物关键文件（不存在则值为 None）。"""
    out = {}
    for key, rel in [("manifest", "manifest.yaml"),
                     ("matrix", "evidence/traceability-matrix.md"),
                     ("graph", "evidence/relation-graph.yaml"),
                     ("interfaces_idx", "interfaces/README.md"),
                     ("business_readme", "business/README.md"),
                     ("capabilities_readme", "capabilities/README.md"),
                     ("glossary", "domain-glossary.md")]:
        p = kb / rel
        out[key] = p.read_text(encoding="utf-8") if p.exists() else None
    return out


def matrix_rows(m: str) -> list:
    """矩阵数据行（排除表头与分隔行）。"""
    return [l for l in m.splitlines()
            if l.strip().startswith("|") and "来源稳定 ID" not in l and "---" not in l]
