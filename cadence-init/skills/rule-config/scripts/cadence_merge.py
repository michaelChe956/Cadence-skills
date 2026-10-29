"""Cadence 受管内容合并基础库。

提供围栏感知的 Markdown 章节解析、标题归一、行级三方合并与章节级合并。
设计约束：证据只能抑制写入，不能授权删除；冲突时用户内容优先，框架新版
通过 pending 返回，绝不静默丢弃用户行。
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_NUMBERING_RE = re.compile(r"^\d+[.、．](?!\d)\s*")
_TRAILING_PAREN_RE = re.compile(r"[（(][^（）()]*[）)]\s*$")
_FENCE_RE = re.compile(r"^\s*(```+|~~~+)")


@dataclass
class Section:
    """Markdown 标题章节。"""

    level: int
    key: str
    title: str
    body_lines: list[str] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)


def normalize_title(title: str) -> str:
    """标题身份：去 ATX 标记、编号、尾部括号限定与首尾空白。"""
    text = title.strip()
    text = re.sub(r"^#{1,6}\s*", "", text)
    text = _NUMBERING_RE.sub("", text)
    text = _TRAILING_PAREN_RE.sub("", text)
    return text.strip()


def _heading(line: str) -> Optional[tuple[int, str]]:
    match = _HEADING_RE.match(line)
    if not match:
        return None
    return len(match.group(1)), match.group(2)


def _first_heading_index(lines: list[str]) -> int:
    """返回首个非围栏标题行号；围栏内的 # 不算标题。"""
    fence: tuple[str, int] | None = None
    for idx, line in enumerate(lines):
        match = _FENCE_RE.match(line)
        if fence is None and match:
            fence = (match.group(1)[0], len(match.group(1)))
            continue
        if fence is not None:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= fence[1]:
                fence = None
            continue
        if _heading(line) is not None:
            return idx
    return len(lines)


def parse_sections(text: str) -> list[Section]:
    """按 ATX 标题切分；围栏代码块内的 # 不识别为标题。

    返回所有层级章节，正文保留原始空行。首个标题前的前言不返回。
    """
    lines = text.splitlines()
    sections: list[Section] = []
    current: Section | None = None
    fence: tuple[str, int] | None = None
    for line in lines:
        fence_match = _FENCE_RE.match(line)
        if fence is None and fence_match:
            fence = (fence_match.group(1)[0], len(fence_match.group(1)))
        elif fence is not None and fence_match and fence_match.group(1)[0] == fence[0] and len(fence_match.group(1)) >= fence[1]:
            fence = None

        heading = None if fence is not None else _heading(line)
        if heading is not None:
            level, title = heading
            current = Section(
                level=level,
                key=normalize_title(title),
                title=title,
                body_lines=[],
                raw_lines=[line],
            )
            sections.append(current)
            continue
        if current is not None:
            current.body_lines.append(line)
            current.raw_lines.append(line)
    return sections


def split_blocks(text: str, level: int = 3) -> list[Section]:
    """按指定标题级别切块；块内更深标题保留在正文中。

    用于入口 ``## 强制规则``：H3 条目是合并单元，条目内 H4/表格/围栏不拆散。
    """
    lines = text.splitlines()
    blocks: list[Section] = []
    current: Section | None = None
    fence: tuple[str, int] | None = None
    for line in lines:
        fence_match = _FENCE_RE.match(line)
        if fence is None and fence_match:
            fence = (fence_match.group(1)[0], len(fence_match.group(1)))
        elif fence is not None and fence_match and fence_match.group(1)[0] == fence[0] and len(fence_match.group(1)) >= fence[1]:
            fence = None

        heading = None if fence is not None else _heading(line)
        if heading is not None:
            hlevel, title = heading
            if hlevel <= level and current is not None:
                current = None
            if hlevel == level:
                current = Section(
                    level=hlevel,
                    key=normalize_title(title),
                    title=title,
                    body_lines=[],
                    raw_lines=[line],
                )
                blocks.append(current)
                continue
            if current is not None:
                current.body_lines.append(line)
                current.raw_lines.append(line)
            continue
        if current is not None:
            current.body_lines.append(line)
            current.raw_lines.append(line)
    return blocks


def _split_text(text: str) -> tuple[list[str], bool]:
    trailing = text.endswith("\n")
    return text.splitlines(), trailing


def _join_text(lines: Iterable[str], trailing: bool) -> str:
    result = "\n".join(lines)
    if trailing:
        result += "\n"
    return result


def _edits(base_lines: list[str], variant_lines: list[str]) -> list[tuple[int, int, list[str]]]:
    matcher = difflib.SequenceMatcher(None, base_lines, variant_lines)
    edits = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        edits.append((i1, i2, variant_lines[j1:j2]))
    return edits


def _overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    a1, a2 = a
    b1, b2 = b
    if a1 == a2 and b1 == b2:
        return False  # 同点纯插入：双方都保留
    if a1 == a2:
        return b1 < a1 < b2
    if b1 == b2:
        return a1 < b1 < a2
    return max(a1, b1) < min(a2, b2)


def three_way(base: str | None, ours: str, theirs: str) -> tuple[str, list[dict]]:
    """行级三方合并；冲突时保留 ours，theirs 写入 pending。

    返回 (合并文本, pending 列表)。pending 条目只描述被挡住的框架文本，
    不修改 ours 的任何行。
    """
    base_text = "" if base is None else base
    base_lines, base_trailing = _split_text(base_text)
    ours_lines, ours_trailing = _split_text(ours)
    theirs_lines, theirs_trailing = _split_text(theirs)
    trailing = ours_trailing or theirs_trailing or base_trailing

    if base is None:
        if ours == theirs:
            return ours, []
        return ours, [{"reason": "base-missing", "theirs": theirs}]

    if ours == base:
        return theirs, []
    if theirs == base:
        return ours, []
    if ours == theirs:
        return ours, []

    ours_edits = _edits(base_lines, ours_lines)
    theirs_edits = _edits(base_lines, theirs_lines)
    pending: list[dict] = []
    accepted_theirs: list[tuple[int, int, list[str]]] = []
    for edit in theirs_edits:
        if any(_overlap((edit[0], edit[1]), (o[0], o[1])) for o in ours_edits):
            pending.append({
                "reason": "three-way-conflict",
                "base": base_lines[edit[0]:edit[1]],
                "theirs": edit[2],
            })
            continue
        accepted_theirs.append(edit)

    # 先应用 ours，再应用不冲突的 theirs；同位置纯插入时 theirs 在前。
    # 倒序应用避免索引漂移。
    combined = [(e, 1) for e in ours_edits] + [(e, 0) for e in accepted_theirs]
    combined.sort(key=lambda item: (item[0][0], item[0][1], item[1]), reverse=True)
    result = list(base_lines)
    for (start, end, replacement), _source in combined:
        result[start:end] = replacement
    return _join_text(result, trailing), pending


def _render_section(section: Section, body_lines: list[str] | None = None) -> list[str]:
    body = section.body_lines if body_lines is None else body_lines
    return [f"{'#' * section.level} {section.title}", *body]


def _group_sections(sections: list[Section]) -> tuple[list[tuple[int, str]], dict]:
    order: list[tuple[int, str]] = []
    groups: dict[tuple[int, str], list[Section]] = {}
    for section in sections:
        key = (section.level, section.key)
        if key not in groups:
            order.append(key)
            groups[key] = []
        groups[key].append(section)
    return order, groups


def merge_sections(
    base: str | None,
    ours: str,
    theirs: str,
    required_keys: Optional[list[str]] = None,
) -> tuple[str, list[dict]]:
    """章节级合并。

    - 以 theirs 的章节顺序为主；
    - 同名同级别章节按出现顺序配对，重复章节不丢弃；
    - ours 已有章节：正文三方合并，标题保留 ours；
    - ours 缺失章节：取 theirs；
    - ours 独有章节：追加保留；
    - required_keys 中的章节缺失时报告 pending。
    """
    ours_sections = parse_sections(ours)
    theirs_sections = parse_sections(theirs)
    base_sections = parse_sections(base or "")
    if not theirs_sections:
        return ours, []
    ours_order, ours_groups = _group_sections(ours_sections)
    theirs_order, theirs_groups = _group_sections(theirs_sections)
    _base_order, base_groups = _group_sections(base_sections)

    ours_lines = ours.splitlines()
    preamble: list[str] = []
    if ours_sections:
        first = _first_heading_index(ours_lines)
        preamble = ours_lines[:first]
    else:
        preamble = list(ours_lines)

    output: list[str] = list(preamble)
    if output and output[-1].strip():
        output.append("")
    pending: list[dict] = []
    emitted: set[tuple[int, str]] = set()

    def emit(lines: list[str]) -> None:
        if output and output[-1].strip():
            output.append("")
        output.extend(lines)
        output.append("")

    consumed: dict[tuple[int, str], int] = {}
    for key in ours_order:
        ours_list = ours_groups[key]
        theirs_list = theirs_groups.get(key, [])
        for index, ours_section in enumerate(ours_list):
            if index < len(theirs_list):
                section = theirs_list[index]
                base_list = base_groups.get(key, [])
                base_body = (
                    "\n".join(base_list[index].body_lines)
                    if index < len(base_list) else None
                )
                merged_body, section_pending = three_way(
                    base_body,
                    "\n".join(ours_section.body_lines),
                    "\n".join(section.body_lines),
                )
                pending.extend(section_pending)
                emit(_render_section(ours_section, merged_body.splitlines()))
                consumed[key] = index + 1
            else:
                emit(_render_section(ours_section))
        emitted.add(key)

    for key in theirs_order:
        theirs_list = theirs_groups[key]
        start = consumed.get(key, 0)
        for section in theirs_list[start:]:
            emit(_render_section(section))
        emitted.add(key)

    if required_keys:
        emitted_keys = {key for _level, key in emitted}
        for key in required_keys:
            if key not in emitted_keys:
                pending.append({"reason": "required-section-missing", "key": key})

    text = _join_text(output, ours.endswith("\n") or theirs.endswith("\n"))
    return text, pending
