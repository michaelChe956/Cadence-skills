"""结果与基线 JSON 的版本化最小契约（oracle §2-e / eval-trajectory-scoring R7）。

稳定键受版本约束；其余字段放 details 自由演进。主版本不匹配的基线
不参与 diff，报告显式标注，杜绝静默错比。
"""
import json
from pathlib import Path
from typing import Optional

SCHEMA_VERSION = "1.0"

STABLE_KEYS = [
    "run_id", "agent", "model", "cli_version", "probe_id", "rule_clause_ids",
    "verdict", "fail_reason", "denials", "transcript_path", "started_at",
    "duration_s",
]

_DEFAULTS = {
    "model": "", "cli_version": None, "rule_clause_ids": [], "verdict": "FAIL",
    "fail_reason": "", "denials": [], "transcript_path": "", "started_at": "",
    "duration_s": 0.0,
}

# 稳定键的类型也属于最小契约；details 的内部结构不受此表约束。
_STABLE_TYPES = {
    "run_id": str,
    "agent": str,
    "model": str,
    "cli_version": (str, type(None)),
    "probe_id": str,
    "rule_clause_ids": list,
    "verdict": str,
    "fail_reason": str,
    "denials": list,
    "transcript_path": str,
    "started_at": str,
    "duration_s": (int, float),
}
_VERDICTS = ("PASS", "FAIL", "INFRA_FAIL", "MODEL_DRIFT")


def build_result(**kwargs) -> dict:
    doc = {"schema_version": SCHEMA_VERSION}
    for key in STABLE_KEYS:
        value = kwargs.get(key, _DEFAULTS.get(key))
        # 默认列表必须逐次构造，避免一次结果的写入污染后续结果。
        if key in ("rule_clause_ids", "denials") and key not in kwargs:
            value = list(value)
        doc[key] = value
    doc["details"] = kwargs.get("details", {})
    return doc


def validate_result(doc: dict) -> list:
    """返回缺失或类型不符的稳定键；details 的额外字段不参与校验。"""
    if not isinstance(doc, dict):
        return ["<not-object>"]
    problems = []
    for key in STABLE_KEYS:
        if key not in doc:
            problems.append(key)
            continue
        value = doc[key]
        # 未提供的字段由 build_result 以 None 占位；None 是兼容的缺省语义。
        if value is None:
            continue
        expected = _STABLE_TYPES[key]
        # bool 是 int 的子类，但不是合法的 duration_s 数值。
        if key == "duration_s" and isinstance(value, bool):
            problems.append(key)
        elif not isinstance(value, expected):
            problems.append(key)
    verdict = doc.get("verdict")
    if isinstance(verdict, str) and verdict not in _VERDICTS:
        problems.append(f"verdict:{verdict}")
    return problems


def load_baseline(path: Path):
    """读取基线；主版本不匹配返回 (None, 原因)——调用方必须显式标注不比对。"""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"基线不可读：{exc}"
    if not isinstance(doc, dict):
        return None, "基线不可读：JSON 顶层不是对象"
    base_version = str(doc.get("schema_version", ""))
    current_major = SCHEMA_VERSION.split(".")[0]
    base_major = base_version.split(".")[0] if base_version else ""
    if base_major != current_major:
        return None, (f"基线 schema 不兼容，本次不比对（基线 {base_version or '无版本'}"
                      f" / 当前 {SCHEMA_VERSION}）")
    return doc, None
