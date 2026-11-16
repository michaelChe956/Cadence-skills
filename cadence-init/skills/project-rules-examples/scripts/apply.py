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

收尾报告（stdout 最后一行，单行 JSON；状态行之后输出，--help 除外）：
  {"skill": ..., "exit_code": N, "counts": {...}, "completed": [...],
   "needs_rule_config": [...], "pending": N, "failure": null|{...}, "overall": "success"|"failed"}
  overall 恒为最后一个键；退出码 0 ⇒ success，非 0 ⇒ failed。
  幂等重跑（全 pristine/unchanged/skipped）报告 success；needs-rule-config 是交接项，不算失败。

退出码：0 正常；2 用法错误；3 内部错误（备份/写入/读取/模板缺失，均落失败报告）。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
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


class ApplyError(Exception):
    """可预期的终止性失败：携带退出码与失败报告字段。"""

    def __init__(self, code: int, reason: str, file: str | None = None,
                 recovery: str = "按上方逐行状态确认已完成文件，修复后重跑本脚本（幂等）"):
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.file = file
        self.recovery = recovery


STATUSES = ("created", "pristine", "merged", "unchanged", "skipped", "needs-rule-config")


class Run:
    """一次运行的状态累积：逐行输出与收尾报告共用同一份记录。"""

    def __init__(self) -> None:
        self.counts = {status: 0 for status in STATUSES}
        self.completed: list[str] = []
        self.needs_rule_config: list[str] = []
        self.pending = 0

    def status(self, status: str, path: str) -> None:
        print(f"{status} {path}")
        self.counts[status] += 1
        if status == "needs-rule-config":
            self.needs_rule_config.append(path)
        else:
            self.completed.append(path)

    def warn_pending(self, message: str) -> None:
        print(f"[prx-apply][pending] {message}", file=sys.stderr)
        self.pending += 1

    def report(self, exit_code: int, error: ApplyError | None) -> dict:
        """收尾报告。`overall` 必须是最后一个键：解析器只看该字段后 64 字符窗口。"""
        return {
            "skill": "project-rules-examples",
            "exit_code": exit_code,
            "counts": self.counts,
            "completed": self.completed,
            "needs_rule_config": self.needs_rule_config,
            "pending": self.pending,
            "failure": None if error is None else {
                "file": error.file,
                "reason": error.reason,
                "recovery": error.recovery,
            },
            "overall": "failed" if exit_code != 0 else "success",
        }


def _apply(args: argparse.Namespace, run: Run) -> None:
    root = Path(args.project_root).resolve()
    if not root.is_dir():
        raise ApplyError(2, f"项目根不存在：{root}", file=str(root),
                         recovery="传入存在的 --project-root")
    if not REFS.is_dir():
        raise ApplyError(3, f"模板源缺失：{REFS}", file=str(REFS),
                         recovery="重新安装 project-rules-examples skill 后重试")

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for src_rel, dst_rel in TARGETS:
        src = REFS / src_rel
        dst = root / dst_rel
        if not src.is_file():
            raise ApplyError(3, f"模板文件缺失：{src}", file=str(src),
                             recovery="重新安装 project-rules-examples skill 后重试")
        try:
            _apply_target(root, stamp, src, dst, dst_rel, run)
        except ApplyError:
            raise
        except Exception as exc:  # noqa: BLE001 - 备份/写入/回读校验失败统一落失败报告
            raise ApplyError(
                3, f"{type(exc).__name__}: {exc}", file=dst_rel,
                recovery="按 cadence/legacy/<时间戳>/ 中的写入前原像恢复，修复权限或磁盘后重跑",
            ) from exc

    for entry in ENTRY_FILES:
        path = root / entry
        if path.exists() and ref_anchor(path):
            run.status("skipped", entry)
        else:
            run.status("needs-rule-config", entry)


def _apply_target(root: Path, stamp: str, src: Path, dst: Path, dst_rel: str, run: Run) -> None:
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if _state_module is not None:
            _state_module.record_asset_base(root, dst_rel, src.read_text(encoding="utf-8"))
        run.status("created", dst_rel)
        return
    try:
        existing = dst.read_text(encoding="utf-8")
        template = src.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ApplyError(3, f"读取失败：{exc}", file=dst_rel,
                         recovery="确认文件为可读的 UTF-8 文本后重跑") from exc
    if existing == template:
        if _state_module is not None:
            _state_module.record_asset_base(root, dst_rel, template)
        run.status("pristine", dst_rel)
        return

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
                run.status("merged", dst_rel)
            else:
                run.status("unchanged", dst_rel)
            if _state_module is not None:
                _state_module.record_asset_base(root, dst_rel, template)
            return
        merged, pending = merge_sections(base, existing, template)
        if pending:
            run.warn_pending(f"{dst_rel}: {len(pending)} 项框架新版未自动采纳")
        if merged != existing:
            _backup_file(root, stamp, dst_rel, dst)
            _write_file(dst, merged)
            run.status("merged", dst_rel)
        else:
            run.status("unchanged", dst_rel)
        if _state_module is not None:
            _state_module.record_asset_base(root, dst_rel, template)
        return

    # 无基线：只有“纯旧版”（所有行都在模板中）才升级；
    # 含用户内容的文件保持不变，只报告 pending，避免追加通用章节污染。
    if _is_line_subset(existing, template):
        _backup_file(root, stamp, dst_rel, dst)
        _write_file(dst, template)
        if _state_module is not None:
            _state_module.record_asset_base(root, dst_rel, template)
        run.status("merged", dst_rel)
        return
    run.warn_pending(f"{dst_rel}: 无基线且含用户内容，保持原文件，未追加模板章节")
    run.status("unchanged", dst_rel)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="铺设/合并 cadence/project-rules")
    parser.add_argument("--project-root", default=".")
    run = Run()
    error: ApplyError | None = None
    try:
        args = parser.parse_args(argv)
        _apply(args, run)
        exit_code = 0
    except SystemExit as exc:  # argparse：--help 退出 0 不出报告；用法错误退出 2 出失败报告
        code = exc.code if isinstance(exc.code, int) else 2
        if code == 0:
            return 0
        exit_code = code
        error = ApplyError(code, "命令行参数错误", recovery="见上方 usage 提示修正参数")
    except ApplyError as exc:
        print(f"[prx-apply][错误] {exc.reason}", file=sys.stderr)
        exit_code, error = exc.code, exc
    except Exception as exc:  # noqa: BLE001 - 兜底：任何异常都必须落失败报告
        print(f"[prx-apply][错误] 未预期异常：{type(exc).__name__}: {exc}", file=sys.stderr)
        exit_code = 3
        error = ApplyError(3, f"未预期异常：{type(exc).__name__}: {exc}")
    # 收尾报告：stdout 最后一行单行 JSON；逐行状态保持原样在其之前。
    print(json.dumps(run.report(exit_code, error), ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
