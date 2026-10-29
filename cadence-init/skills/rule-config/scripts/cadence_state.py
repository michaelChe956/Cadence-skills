"""Cadence 受管状态、基线与用户 overlay。

状态目录固定为 ``cadence/framework-state/``，本地保存，不提交 VCS。
只保存框架渲染文本基线与哈希，不保存用户内容或密钥。
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import tempfile
from pathlib import Path

STATE_REL = Path("cadence/framework-state")
OVERLAY_BEGIN = "<!-- cadence-overlay:extracted:start -->"
OVERLAY_END = "<!-- cadence-overlay:extracted:end -->"
OVERLAY_FILE_PREFIX = "user-"
OVERLAY_HEADER_PREFIX = "<!-- cadence-user-overlay:"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def state_dir(root: Path) -> Path:
    return root / STATE_REL


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".cadence-state-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_manifest(root: Path) -> dict:
    path = state_dir(root) / "manifest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"schema": 1, "rules": {}}
    if not isinstance(data, dict):
        return {"schema": 1, "rules": {}}
    data.setdefault("schema", 1)
    data.setdefault("rules", {})
    if not isinstance(data["rules"], dict):
        data["rules"] = {}
    return data


def save_manifest(root: Path, data: dict) -> None:
    directory = state_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "pending").mkdir(exist_ok=True)
    gitignore = directory / ".gitignore"
    if not gitignore.exists():
        _atomic_write(gitignore, "*\n!.gitignore\n")
    manifest = directory / "manifest.json"
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        if manifest.read_text(encoding="utf-8") == text:
            return
    except (OSError, UnicodeDecodeError):
        pass
    _atomic_write(manifest, text)


def save_pending(root: Path, items: list[dict]) -> Path | None:
    """把非空 pending 清单落到 `pending/latest.json`；幂等。"""
    if not items:
        return None
    path = state_dir(root) / "pending" / "latest.json"
    text = json.dumps({"pending": items}, ensure_ascii=False, indent=2) + "\n"
    try:
        if path.read_text(encoding="utf-8") == text:
            return path
    except (OSError, UnicodeDecodeError):
        pass
    _atomic_write(path, text)
    return path


def base_path(root: Path, digest: str) -> Path:
    return state_dir(root) / "base" / digest


def get_rule_base(root: Path, rel: str) -> str | None:
    data = load_manifest(root)
    entry = (data.get("rules") or {}).get(rel)
    if not isinstance(entry, dict):
        return None
    digest = entry.get("base_sha")
    if not digest:
        return None
    try:
        return base_path(root, digest).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def record_rule_base(root: Path, rel: str, text: str) -> None:
    digest = sha256_text(text)
    directory = state_dir(root)
    path = base_path(root, digest)
    if not path.exists():
        _atomic_write(path, text)
    data = load_manifest(root)
    rules = data.setdefault("rules", {})
    existing = rules.get(rel)
    if isinstance(existing, dict) and existing.get("base_sha") == digest:
        return
    rules[rel] = {"base_sha": digest}
    save_manifest(root, data)


def get_asset_base(root: Path, rel: str) -> str | None:
    data = load_manifest(root)
    entry = (data.get("assets") or {}).get(rel)
    if not isinstance(entry, dict):
        return None
    digest = entry.get("base_sha")
    if not digest:
        return None
    try:
        return base_path(root, digest).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def record_asset_base(root: Path, rel: str, text: str) -> None:
    digest = sha256_text(text)
    path = base_path(root, digest)
    if not path.exists():
        _atomic_write(path, text)
    data = load_manifest(root)
    assets = data.setdefault("assets", {})
    existing = assets.get(rel)
    if isinstance(existing, dict) and existing.get("base_sha") == digest:
        return
    assets[rel] = {"base_sha": digest}
    save_manifest(root, data)


def _opcodes(base: str, current: str):
    return difflib.SequenceMatcher(
        None, base.splitlines(), current.splitlines()
    ).get_opcodes()


def build_overlay_body(
    rule_name: str,
    base_text: str,
    current_text: str,
    base_origin: str,
) -> tuple[str, bool]:
    """返回 overlay 自动抽取区与“是否有差异”。"""
    base_lines = base_text.splitlines()
    current_lines = current_text.splitlines()
    added: list[str] = []
    replaced: list[tuple[list[str], list[str]]] = []
    removed: list[str] = []
    for tag, i1, i2, j1, j2 in _opcodes(base_text, current_text):
        if tag == "equal":
            continue
        if tag == "insert":
            added.extend(current_lines[j1:j2])
        elif tag == "delete":
            removed.extend(base_lines[i1:i2])
        elif tag == "replace":
            replaced.append((base_lines[i1:i2], current_lines[j1:j2]))
    if not added and not replaced and not removed:
        return "", False

    lines = [f"<!-- cadence-overlay:extracted:start base={base_origin} -->"]
    lines.append("## 用户新增")
    if added:
        lines.extend(added)
    else:
        lines.append("（无）")
    lines.append("")
    lines.append("## 用户替换")
    if replaced:
        for old, new in replaced:
            lines.append("### 框架原文")
            lines.extend(old)
            lines.append("### 用户文本")
            lines.extend(new)
            lines.append("")
    else:
        lines.append("（无）")
    lines.append("")
    if base_origin == "template-fallback":
        lines.append("## 旧版本差异（provisional，非用户禁用）")
    else:
        lines.append("## 用户禁用")
    if removed:
        lines.extend(removed)
    else:
        lines.append("（无）")
    lines.append("<!-- cadence-overlay:extracted:end -->")
    return "\n".join(lines) + "\n", True


def _region_parts(text: str, begin_prefix: str, end_prefix: str):
    begin = text.find(begin_prefix)
    finish = text.find(end_prefix, begin if begin >= 0 else 0)
    if begin < 0 or finish < 0:
        return None
    start_line_end = text.find("\n", begin)
    if start_line_end < 0:
        start_line_end = begin
    end_line_end = text.find("\n", finish)
    if end_line_end < 0:
        end_line_end = finish
    return (
        text[:begin],
        text[begin:start_line_end],
        text[start_line_end + 1:finish],
        text[finish:end_line_end],
        text[end_line_end + 1:] if end_line_end < len(text) else "",
    )


def merge_overlay(
    existing: str | None,
    rule_name: str,
    base_text: str,
    current_text: str,
    base_origin: str,
) -> tuple[str | None, bool]:
    """合并 overlay 自动抽取区；保留用户手写区，并累积既有抽取内容。"""
    body, changed = build_overlay_body(rule_name, base_text, current_text, base_origin)
    if not changed:
        return existing, False

    header = (
        f"{OVERLAY_HEADER_PREFIX} rule={rule_name} "
        f"base={base_origin} -->\n"
        f"# 用户覆盖：{rule_name}\n\n"
        f"> 本文件内容优先级高于 `.claude/rules/{rule_name}` 中对应规则。\n\n"
    )
    if existing is None:
        return header + body, True
    begin_prefix = "<!-- cadence-overlay:extracted:start"
    end_prefix = "<!-- cadence-overlay:extracted:end"
    old_parts = _region_parts(existing, begin_prefix, end_prefix)
    new_parts = _region_parts(body, begin_prefix, end_prefix)
    if old_parts is None or new_parts is None:
        return (existing.rstrip("\n") + "\n\n" + header + body), True
    before, _old_start, old_inner, _old_end, after = old_parts
    _new_before, new_start, new_inner, new_end, _new_after = new_parts
    old_text = old_inner.strip()
    new_text = new_inner.strip()
    combined = old_text
    if new_text and new_text not in old_text:
        combined = (old_text + "\n\n" + new_text).strip()
    if not combined:
        combined = new_text
    if before.lstrip().startswith(OVERLAY_HEADER_PREFIX):
        lines = before.splitlines()
        if lines:
            lines[0] = header.splitlines()[0]
            before = "\n".join(lines) + "\n"
    if not before.strip():
        before = header
    return before + new_start + "\n" + combined + "\n" + new_end + "\n" + after, True


def overlay_path(rules_dir: Path, rule_name: str) -> Path:
    return rules_dir / f"{OVERLAY_FILE_PREFIX}{rule_name}"
