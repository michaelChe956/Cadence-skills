#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""project-rules-examples 确定性铺设/合并脚本。

安全不变量：
- 已存在文件的用户正文逐字保留（含空行、表格、围栏代码块与尾部空行），
  只把模板中缺失的章节按模板原文追加到文件末尾，不重排、不改写、
  不生成“项目补充”。
- 任何实际写入既有文件前，先备份到
  ``cadence/legacy/<14位时间戳>/cadence/project-rules/<相对路径>``。
- 绝不创建或修改 CLAUDE.md / AGENTS.md（入口文件由 rule-config 唯一拥有）；
  入口缺失或缺少等价引用时只报告 ``needs-rule-config``。
- 幂等：第二次运行全部 unchanged/pristine/skipped，零写入、零备份。

章节身份 = 标题级别 + 去编号标题文本（NB-01，围栏感知）；
多级编号（如 ``6.2 规则`` 与 ``7.2 规则``）不碰撞，配对按出现顺序队列进行。

状态输出（stdout 每行一条）：
  created|pristine|merged|unchanged <目标相对路径>
  skipped|needs-rule-config CLAUDE.md|AGENTS.md

退出码：0 正常；2 用法错误；3 内部错误。
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REFS = SCRIPT_DIR.parent / "references" / "project-rules"
TARGETS = [
    ("README.md", "cadence/project-rules/README.md"),
    ("examples/requirement-template.md", "cadence/project-rules/examples/requirement-template.md"),
    ("examples/design-template.md", "cadence/project-rules/examples/design-template.md"),
    ("examples/coding-standards.md", "cadence/project-rules/examples/coding-standards.md"),
    ("examples/test-standards.md", "cadence/project-rules/examples/test-standards.md"),
]
ENTRY_FILES = ("CLAUDE.md", "AGENTS.md")

# ---------- 章节解析：优先共享模块 cadence_merge，失败本地回退 ----------

_SHARED = SCRIPT_DIR.parent.parent / "rule-config" / "scripts" / "cadence_merge.py"
try:
    _spec = importlib.util.spec_from_file_location("cadence_merge", _SHARED)
    _module = importlib.util.module_from_spec(_spec)
    sys.modules.setdefault("cadence_merge", _module)  # dataclass 需要模块已注册
    _spec.loader.exec_module(_module)
    parse_sections = _module.parse_sections
    merge_sections = _module.merge_sections
except Exception:  # pragma: no cover - 安装布局异常时保守退化
    parse_sections = None
    merge_sections = None

_SHARED_STATE = SCRIPT_DIR.parent.parent / "rule-config" / "scripts" / "cadence_state.py"
try:
    _state_spec = importlib.util.spec_from_file_location("cadence_state", _SHARED_STATE)
    _state_module = importlib.util.module_from_spec(_state_spec)
    sys.modules.setdefault("cadence_state", _state_module)
    _state_spec.loader.exec_module(_state_module)
except Exception:  # pragma: no cover
    _state_module = None


def _fallback_key(title: str) -> str:
    import re

    text = re.sub(r"^#+\s*", "", title)
    text = re.sub(r"^\d+[.、．](?!\d)\s*", "", text)
    text = re.sub(r"[（(][^（）()]*[）)]\s*$", "", text)
    return text.strip()


def _fence_info(line: str):
    s = line.lstrip()
    if not s or s[0] not in "`~":
        return None
    ch = s[0]
    count = len(s) - len(s.lstrip(ch))
    return (ch, count) if count >= 3 else None


def _simple_sections(text: str):
    """最小 H1-H6 解析回退；fence 内的 # 不识别。"""
    sections = []
    current = None
    fence = None
    for line in text.splitlines():
        info = _fence_info(line)
        if fence is None and info:
            fence = info
        elif fence is not None and info and info[0] == fence[0] and info[1] >= fence[1]:
            fence = None
        if fence is None and line.startswith("#"):
            hashes = len(line) - len(line.lstrip("#"))
            title = line[hashes:].strip()
            if 1 <= hashes <= 6 and title:
                current = {"level": hashes, "title": title,
                           "key": _fallback_key(title), "raw": [line]}
                sections.append(current)
                continue
        if current is not None:
            current["raw"].append(line)
    return sections


def _sections(text: str):
    """统一返回 [(level, key, title, raw_lines)]，fence 感知。"""
    if parse_sections is not None:
        return [(s.level, s.key, s.title, list(s.raw_lines)) for s in parse_sections(text)]
    return [(s["level"], s["key"], s["title"], list(s["raw"])) for s in _simple_sections(text)]


def _fences_closed(text: str) -> bool:
    fence = None
    for line in text.splitlines():
        info = _fence_info(line)
        if fence is None and info:
            fence = info
        elif fence is not None and info and info[0] == fence[0] and info[1] >= fence[1]:
            fence = None
    return fence is None


def find_missing_sections(existing_secs, template_secs):
    """返回模板有而目标缺失的章节（保持模板顺序）。

    两遍配对：先精确标题（忽略级别），再 NB-01 身份（级别 + 去编号标题）；
    每章节按出现顺序队列消费，杜绝重复键导致的丢章节/重复追加。
    """
    consumed = [False] * len(existing_secs)
    missing = []
    for t_level, t_key, t_title, _t_raw in template_secs:
        idx = None
        for i, (level, _key, title, _raw) in enumerate(existing_secs):
            if not consumed[i] and title.strip() == t_title.strip():
                idx = i
                break
        if idx is None:
            for i, (level, key, _title, _raw) in enumerate(existing_secs):
                if not consumed[i] and level == t_level and key == t_key:
                    idx = i
                    break
        if idx is None:
            missing.append((t_level, t_key, t_title, _t_raw))
        else:
            consumed[idx] = True
    return missing


def _append_blocks(existing: str, blocks: list[str], newline: str) -> str:
    """把章节块追加到原文末尾；既有字节零改动（仅补行尾换行与分隔空行）。"""
    if existing == "":
        return newline.join(blocks) + newline
    base = existing if existing.endswith(newline) else existing + newline
    return base + newline + newline.join(blocks) + newline


def _nonempty_lines(text: str) -> set[str]:
    return {line for line in text.splitlines() if line.strip()}


def _is_line_subset(existing: str, template: str) -> bool:
    return _nonempty_lines(existing) <= _nonempty_lines(template)


def merge_missing_sections(existing: str, template: str) -> tuple[str, bool]:
    """只追加模板中缺失的章节；不重排、不改写已有正文。

    无法安全解析（非空但无任何标题、围栏未闭合）时原样返回。
    """
    if existing and not _sections(existing):
        return existing, False  # 非空文件无任何标题：保守保留
    if not _fences_closed(existing) or not _fences_closed(template):
        return existing, False  # 围栏未闭合：保守保留
    missing = find_missing_sections(_sections(existing), _sections(template))
    if not missing:
        return existing, False
    newline = "\r\n" if "\r\n" in existing else "\n"
    blocks = [newline.join(raw).rstrip("\r\n") for _level, _key, _title, raw in missing]
    text = _append_blocks(existing, blocks, newline)
    return text, text != existing


def _backup_file(root: Path, stamp: str, rel: str, src: Path) -> Path:
    legacy = root / "cadence" / "legacy"
    gitignore = legacy / ".gitignore"
    if not gitignore.exists():
        gitignore.parent.mkdir(parents=True, exist_ok=True)
        gitignore.write_text("*\n!.gitignore\n", encoding="utf-8")
    dest = legacy / stamp / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def _write_file(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".cadence-tmp")
    try:
        tmp.write_text(text, encoding="utf-8", newline="")
        tmp.replace(path)
        if path.read_text(encoding="utf-8") != text:
            raise RuntimeError(f"写后回读校验失败：{path}")
    finally:
        if tmp.exists():
            tmp.unlink()


def ref_anchor(path: Path) -> bool:
    """等价引用判定：含“项目个性化规则”且指向 cadence/project-rules。"""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return "项目个性化规则" in text and "cadence/project-rules" in text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="铺设/合并 cadence/project-rules")
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(f"[prx-apply][错误] 项目根不存在：{root}", file=sys.stderr)
        return 2
    if not REFS.is_dir():
        print(f"[prx-apply][错误] 模板源缺失：{REFS}", file=sys.stderr)
        return 3

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for src_rel, dst_rel in TARGETS:
        src = REFS / src_rel
        dst = root / dst_rel
        if not src.is_file():
            print(f"[prx-apply][错误] 模板文件缺失：{src}", file=sys.stderr)
            return 3
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            if _state_module is not None:
                _state_module.record_asset_base(root, dst_rel, src.read_text(encoding="utf-8"))
            print(f"created {dst_rel}")
            continue
        try:
            existing = dst.read_text(encoding="utf-8")
            template = src.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"[prx-apply][错误] 读取失败：{dst_rel}: {exc}", file=sys.stderr)
            return 3
        if existing == template:
            if _state_module is not None:
                _state_module.record_asset_base(root, dst_rel, template)
            print(f"pristine {dst_rel}")
            continue

        base = (
            _state_module.get_asset_base(root, dst_rel)
            if _state_module is not None else None
        )
        if base is not None and merge_sections is not None:
            if base == template:
                # 框架模板未变：只补缺失章节，用户正文不重写。
                merged, changed = merge_missing_sections(existing, template)
                if changed:
                    _backup_file(root, stamp, dst_rel, dst)
                    _write_file(dst, merged)
                    print(f"merged {dst_rel}")
                else:
                    print(f"unchanged {dst_rel}")
                if _state_module is not None:
                    _state_module.record_asset_base(root, dst_rel, template)
                continue
            merged, pending = merge_sections(base, existing, template)
            if pending:
                print(
                    f"[prx-apply][pending] {dst_rel}: "
                    f"{len(pending)} 项框架新版未自动采纳",
                    file=sys.stderr,
                )
            if merged != existing:
                _backup_file(root, stamp, dst_rel, dst)
                _write_file(dst, merged)
                print(f"merged {dst_rel}")
            else:
                print(f"unchanged {dst_rel}")
            if _state_module is not None:
                _state_module.record_asset_base(root, dst_rel, template)
            continue

        # 无基线：只有“纯旧版”（所有行都在模板中）才升级；
        # 含用户内容的文件保持不变，只报告 pending，避免追加通用章节污染。
        if _is_line_subset(existing, template):
            _backup_file(root, stamp, dst_rel, dst)
            _write_file(dst, template)
            if _state_module is not None:
                _state_module.record_asset_base(root, dst_rel, template)
            print(f"merged {dst_rel}")
            continue
        print(
            f"[prx-apply][pending] {dst_rel}: 无基线且含用户内容，"
            f"保持原文件，未追加模板章节",
            file=sys.stderr,
        )
        print(f"unchanged {dst_rel}")

    for entry in ENTRY_FILES:
        path = root / entry
        if path.exists() and ref_anchor(path):
            print(f"skipped {entry}")
        else:
            print(f"needs-rule-config {entry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
