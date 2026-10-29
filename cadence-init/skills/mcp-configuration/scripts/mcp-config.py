#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mcp-config — MCP 配置确定性合并脚本。

用法::

    python3 mcp-config.py apply --project-root <root> --report <path> [--no-interrupt]
    python3 mcp-config.py apply --project-root <root> --report <path> --project-type coding

行为契约（设计文档 §9，用户裁决 D5）：

* ``.mcp.json`` 不存在 → 创建全部默认 server；
* 默认 server 缺失 → **补回**，报告 ``MCP_SERVER_RESTORED``（用户删除不是持久禁用）；
* 同名 server 的 ``type`` / ``command`` / ``url`` → **用户值优先**，框架值进 ``pending``；
* ``args`` → 框架必需参数在前，项目不重复参数追加；
* ``env`` / ``headers`` / ``http_headers`` → 按键合并，用户非占位值优先，用户为占位符则取框架值；
* 项目额外 server 与扩展字段 → 保留；
* ``.codex/config.toml`` → 按 ``[mcp_servers.<name>]`` 表块补齐缺失项，已有表块不覆盖用户字段；
* 任何对**已存在文件**的写入前，先归档到 ``cadence/legacy/<14位时间戳>/<相对路径>``；
* 解析失败 → 不重建、不覆盖，保持原文件，整体 ``degraded``，候选进 ``pending``；
* 幂等：第二次运行零写入、零备份。

退出码：0=ok/degraded，1=fail，2=usage。

报告只输出 server 名、字段名、变量名与框架值，**绝不输出用户真实密钥**。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, NamedTuple, Optional

try:  # Python 3.11+
    import tomllib
except ImportError:  # pragma: no cover - 老解释器降级
    tomllib = None  # type: ignore[assignment]

SKILL_DIR = Path(__file__).resolve().parent.parent
REQUIRED_SERVERS_FILE = SKILL_DIR / "references" / "required-servers.json"

LEGACY_GITIGNORE = "*\n!.gitignore\n"
MCP_JSON_RELPATH = ".mcp.json"
CODEX_TOML_RELPATH = ".codex/config.toml"

# 占位符判定：`your_*` 形式（含 `Bearer your_zhipu_api_key` 这类带前缀的值）。
PLACEHOLDER_RE = re.compile(r"your_[A-Za-z0-9_]+")

# 项目类型检测：有界扫描应用源码/构建描述文件。
PRUNE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".claude", ".claude-plugin",
    "cadence", "target", "dist", "build", "out", "vendor", ".venv", "venv",
    "__pycache__", ".idea", ".gradle", ".next", ".cache", "coverage",
}
SOURCE_EXTS = (
    ".java", ".js", ".jsx", ".ts", ".tsx", ".py", ".go", ".php", ".rs",
    ".rb", ".swift", ".kt", ".kts", ".c", ".cc", ".cpp", ".h", ".cs", ".vue",
)
MARKER_FILES = (
    "package.json", "pom.xml", "build.gradle", "build.gradle.kts",
    "pyproject.toml", "go.mod", "Cargo.toml", "requirements.txt",
    "setup.py", "composer.json", "build.sbt", "mix.exs",
)

# 单值冲突字段（用户值优先）。
SINGLE_FIELDS = ("type", "command", "url")
# 按键合并字段（env / headers / http_headers）。
MAP_FIELDS = ("env", "headers", "http_headers")


class UsageError(Exception):
    """命令行用法错误（退出码 2）。"""


class BackupError(Exception):
    """归档失败（退出码 1，零发布）。"""


class PublishError(Exception):
    """原子写失败（退出码 1）。"""


class ServerSpec(NamedTuple):
    """一个默认 MCP server 定义。"""

    name: str
    config: dict
    applies_to: tuple[str, ...]

    def applies(self, project_type: str) -> bool:
        return project_type in self.applies_to


# ---------------------------------------------------------------------------
# 纯函数工具
# ---------------------------------------------------------------------------


def is_placeholder(value: Any) -> bool:
    """判断值是否为 `your_*` 占位符（含 `Bearer your_xxx` 这类带前缀形式）。"""
    if not isinstance(value, str):
        return False
    return bool(PLACEHOLDER_RE.search(value))


def dedupe(items: Iterable[Any]) -> list:
    """保序去重。"""
    out: list = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def rel_to_root(path: Path, root: Path) -> str:
    """返回相对项目根的 POSIX 路径；失败时退回绝对路径。"""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def toml_str(value: str) -> str:
    """TOML 基本字符串（与 JSON 字符串转义兼容）。"""
    return json.dumps(value, ensure_ascii=False)


def toml_key(key: str) -> str:
    """TOML 键名：裸键可用时直接用，否则加引号。"""
    if re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return key
    return toml_str(key)


def toml_value(value: Any) -> str:
    """把 Python 值渲染为 TOML 值文本。"""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return toml_str(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        inner = ", ".join(
            f"{toml_key(k)} = {toml_value(v)}" for k, v in value.items()
        )
        return "{ " + inner + " }" if inner else "{}"
    return toml_str(str(value))


# ---------------------------------------------------------------------------
# 默认 server 数据源
# ---------------------------------------------------------------------------


def load_specs(path: Path = REQUIRED_SERVERS_FILE) -> list[ServerSpec]:
    """读取 references/required-servers.json，返回 ServerSpec 列表。"""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UsageError(f"默认 server 数据文件不可用：{path}（{exc}）") from exc
    entries = raw.get("servers")
    if not isinstance(entries, list) or not entries:
        raise UsageError(f"默认 server 数据文件缺少 servers 列表：{path}")
    specs: list[ServerSpec] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise UsageError(f"默认 server 条目不是对象：{path}")
        name = entry.get("name")
        config = entry.get("config")
        if not isinstance(name, str) or not name:
            raise UsageError(f"默认 server 条目缺少 name：{path}")
        if not isinstance(config, dict):
            raise UsageError(f"默认 server {name} 缺少 config：{path}")
        applies = entry.get("applies_to") or ["coding", "non-coding"]
        if not isinstance(applies, list):
            raise UsageError(f"默认 server {name} 的 applies_to 非法：{path}")
        specs.append(ServerSpec(name=name, config=config,
                                applies_to=tuple(str(x) for x in applies)))
    return specs


def detect_project_type(root: Path) -> tuple[str, list[str]]:
    """检测项目类型（coding / non-coding）与证据；命中即停止。"""
    evidence: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]
        for fname in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fname), str(root))
            if fname.endswith(SOURCE_EXTS):
                return "coding", [rel]
            if fname in MARKER_FILES:
                evidence.append(rel)
                return "coding", evidence
    return "non-coding", evidence


# ---------------------------------------------------------------------------
# 报告
# ---------------------------------------------------------------------------


def build_report(mode: str, root: Path) -> dict:
    """初始报告骨架。"""
    return {
        "overall": "ok",
        "mode": mode,
        "project_root": str(root),
        "project_type": None,
        "steps": [],
        "actions": [],
        "backups": [],
        "warnings": [],
        "pending": [],
        "overrides": [],
        "failure": None,
        "hints": {"next": "rule-config"},
    }


def write_report(path: Path, report: dict) -> None:
    """写出报告 JSON（父目录不存在则创建）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def add_warning(report: dict, code: str, detail: str) -> None:
    """追加 warning（code 前缀，便于 grep）。"""
    report["warnings"].append(f"{code}: {detail}")


# ---------------------------------------------------------------------------
# 归档与原子写
# ---------------------------------------------------------------------------


def _ensure_legacy_gitignore(legacy_dir: Path) -> None:
    """确保 cadence/legacy/.gitignore 内容为 `*` + `!.gitignore`。"""
    gi = legacy_dir / ".gitignore"
    try:
        current = gi.read_text(encoding="utf-8") if gi.exists() else None
    except OSError as exc:
        raise BackupError(f"无法检查归档忽略文件：{gi}（{exc}）") from exc
    if current == LEGACY_GITIGNORE:
        return
    try:
        legacy_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(gi, LEGACY_GITIGNORE)
    except (OSError, PublishError) as exc:
        raise BackupError(f"无法写入归档忽略文件：{gi}（{exc}）") from exc


def backup_file(path: Path, root: Path) -> Path:
    """把既有文件归档到 cadence/legacy/<14位时间戳>/<相对 root 路径>。

    同秒冲突时时间戳目录追加 ``-2`` / ``-3``。原文件保持不动。
    """
    legacy_root = root / "cadence" / "legacy"
    _ensure_legacy_gitignore(legacy_root)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        rel = path.relative_to(root)
    except ValueError as exc:
        raise BackupError(f"归档目标不在项目根目录内：{path}（root={root}）") from exc
    dest_dir = legacy_root / stamp / rel.parent
    seq = 2
    while dest_dir.exists():
        dest_dir = legacy_root / f"{stamp}-{seq}" / rel.parent
        seq += 1
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        backup_path = dest_dir / path.name
        shutil.copy2(path, backup_path)
    except OSError as exc:
        raise BackupError(f"归档失败：{path} -> {dest_dir / path.name}（{exc}）") from exc
    return backup_path


def atomic_write(path: Path, content: str) -> None:
    """原子写入：同目录临时文件 + os.replace。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Optional[Path] = None
    try:
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".cadence-atomic-")
        tmp_path = Path(tmp_name)
        with os.fdopen(fd, "wb") as fh:
            fh.write(content.encode("utf-8"))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except OSError as exc:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise PublishError(f"原子写入失败：{path}（{exc}）") from exc


def publish(path: Path, content: str, root: Path, report: dict) -> None:
    """写入受管文件：既有文件先归档，再原子写。"""
    if path.exists():
        backup_path = backup_file(path, root)
        report["backups"].append({
            "file": rel_to_root(path, root),
            "backup": rel_to_root(backup_path, root),
        })
    atomic_write(path, content)


# ---------------------------------------------------------------------------
# `.mcp.json` 合并
# ---------------------------------------------------------------------------


def merge_map_field(framework: dict, user: dict, path_label: str,
                    server: str, field: str,
                    report: dict) -> dict:
    """按键合并 env / headers / http_headers。

    用户非占位值优先；用户值为占位符时取框架值；框架独有的键补齐。
    """
    merged = dict(user)
    for key, framework_value in framework.items():
        if key not in user:
            merged[key] = framework_value
            report["actions"].append({
                "path": path_label, "action": "field-added",
                "server": server, "field": field, "key": key,
            })
            continue
        user_value = user[key]
        if is_placeholder(user_value):
            merged[key] = framework_value
            if user_value != framework_value:
                report["actions"].append({
                    "path": path_label, "action": "placeholder-replaced",
                    "server": server, "field": field, "key": key,
                })
                report["pending"].append({
                    "path": path_label, "server": server, "field": field,
                    "key": key, "framework_value": framework_value,
                })
        else:
            if user_value != framework_value:
                report["actions"].append({
                    "path": path_label, "action": "user-value-kept",
                    "server": server, "field": field, "key": key,
                })
                report["overrides"].append({
                    "path": path_label, "server": server, "field": field,
                    "key": key, "reason": "user-value-kept",
                })
                add_warning(report, "MCP_USER_VALUE_KEPT",
                            f"{path_label} `{server}` 的 `{field}.{key}` "
                            f"保留用户值")
    return merged


def _package_name(token: str) -> str:
    if token.startswith("@"):
        scope_end = token.find("/")
        at = token.rfind("@")
        if scope_end != -1 and at > scope_end:
            return token[:at]
        return token
    return token.split("@", 1)[0]


def _first_package(args: list[str]) -> tuple[Optional[int], Optional[str]]:
    for index, token in enumerate(args):
        if not token.startswith("-"):
            return index, token
    return None, None


def _dedupe_flag_values(args: list[str]) -> list[str]:
    result: list[str] = []
    seen: dict[str, int] = {}
    for token in args:
        match = re.match(r"^(--[^=]+)=", token)
        if match and match.group(1) in seen:
            result[seen[match.group(1)]] = token
            continue
        if match:
            seen[match.group(1)] = len(result)
        result.append(token)
    return result


def merge_args(command: str, framework_args: list[str], user_args: list[str]) -> list[str]:
    """按启动器语法合并 args：用户包 token/flag 值优先，避免重复包。"""
    fw = list(framework_args)
    user = list(user_args)
    if not user:
        return fw
    cmd = Path(command).name.lower()
    if cmd in ("npx", "bunx"):
        fi, fw_pkg = _first_package(fw)
        ui, user_pkg = _first_package(user)
    elif cmd == "uvx":
        fi = 0 if fw and not fw[0].startswith("-") else None
        ui = 0 if user and not user[0].startswith("-") else None
        fw_pkg = fw[fi] if fi is not None else None
        user_pkg = user[ui] if ui is not None else None
    else:
        fi = ui = None
        fw_pkg = user_pkg = None
    if cmd in ("npx", "bunx", "uvx"):
        if fi is not None and ui is not None:
            if _package_name(fw_pkg) == _package_name(user_pkg):
                return _dedupe_flag_values(dedupe(fw[:fi] + user))
            return _dedupe_flag_values(user)
    if cmd not in ("npx", "bunx", "uvx"):
        # 通用命令无法判断位置 token 语义：用户 args 整体优先。
        return _dedupe_flag_values(user)
    return _dedupe_flag_values(dedupe(fw + user))


def merge_server(framework: dict, user: dict, path_label: str, server: str,
                 report: dict) -> dict:
    """合并单个 server 配置：用户值优先，框架补齐缺失。"""
    merged: dict = {}
    for key, value in user.items():
        merged[key] = value

    for field in SINGLE_FIELDS:
        if field not in framework:
            continue
        framework_value = framework[field]
        if field not in user:
            merged[field] = framework_value
            report["actions"].append({
                "path": path_label, "action": "field-added",
                "server": server, "field": field,
            })
        elif user[field] != framework_value:
            report["actions"].append({
                "path": path_label, "action": "user-value-kept",
                "server": server, "field": field,
            })
            report["overrides"].append({
                "path": path_label, "server": server, "field": field,
                "reason": "user-value-kept",
            })
            report["pending"].append({
                "path": path_label, "server": server, "field": field,
                "framework_value": framework_value,
            })
            add_warning(report, "MCP_USER_VALUE_KEPT",
                        f"{path_label} `{server}` 的 `{field}` 保留用户值")

    if "args" in framework:
        framework_args = framework["args"] if isinstance(framework["args"], list) else []
        user_args = user.get("args")
        if user_args is not None and not isinstance(user_args, list):
            # 用户值不是数组：按“用户值优先”保持原样，不做框架覆盖。
            add_warning(report, "MCP_FIELD_INVALID",
                        f"{path_label} `{server}` 的 `args` 不是数组，保持用户原值")
        else:
            user_args = user_args or []
            merged_args = merge_args(
                str(user.get("command") or framework.get("command") or ""),
                list(framework_args), list(user_args),
            )
            if user_args and merged_args != user_args:
                report["actions"].append({
                    "path": path_label, "action": "args-merged",
                    "server": server, "field": "args",
                })
            merged["args"] = merged_args

    for field in MAP_FIELDS:
        framework_map = framework.get(field)
        user_map = user.get(field)
        if isinstance(framework_map, dict) and isinstance(user_map, dict):
            merged[field] = merge_map_field(
                framework_map, user_map, path_label, server, field, report)
        elif isinstance(framework_map, dict):
            if not framework_map:
                # 空表（如 env: {}）无信息量，不为补齐而改写用户文件。
                continue
            merged[field] = dict(framework_map)
            report["actions"].append({
                "path": path_label, "action": "field-added",
                "server": server, "field": field,
            })
        # 用户侧为非 dict 值：保持用户原值，框架不覆盖。

    for key, value in framework.items():
        if key in merged:
            continue
        if key in SINGLE_FIELDS or key == "args" or key in MAP_FIELDS:
            continue
        merged[key] = value
        report["actions"].append({
            "path": path_label, "action": "field-added",
            "server": server, "field": key,
        })
    return merged


def merge_mcp_json(root: Path, specs: list[ServerSpec], project_type: str,
                   report: dict) -> None:
    """合并（或创建）项目根 `.mcp.json`。"""
    path = root / MCP_JSON_RELPATH
    applicable = [spec for spec in specs if spec.applies(project_type)]

    if not path.exists():
        servers = {spec.name: json.loads(json.dumps(spec.config))
                   for spec in applicable}
        content = json.dumps({"mcpServers": servers}, ensure_ascii=False,
                             indent=2) + "\n"
        publish(path, content, root, report)
        report["steps"].append({
            "name": "mcp_json", "status": "created",
            "detail": f"创建默认 server {len(servers)} 个",
        })
        report["actions"].append({
            "path": MCP_JSON_RELPATH, "action": "created",
            "detail": f"默认 server {len(servers)} 个",
        })
        return

    try:
        original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        add_warning(report, "UNIT_UNPARSEABLE",
                    f"{MCP_JSON_RELPATH} 无法按 UTF-8 读取：{exc}")
        report["steps"].append({
            "name": "mcp_json", "status": "degraded",
            "detail": "无法读取，保持原文件",
        })
        report["overall"] = "degraded"
        return
    try:
        document = json.loads(original)
    except ValueError as exc:
        _degrade_unparseable(path, MCP_JSON_RELPATH, original, applicable,
                             report, f"JSON 解析失败：{exc}")
        return

    if not isinstance(document, dict):
        _degrade_unparseable(path, MCP_JSON_RELPATH, original, applicable,
                             report, "顶层不是 JSON 对象")
        return

    user_servers = document.get("mcpServers", {})
    if not isinstance(user_servers, dict):
        _degrade_unparseable(path, MCP_JSON_RELPATH, original, applicable,
                             report, "mcpServers 不是对象")
        return

    merged_servers: dict = dict(user_servers)
    restored: list[str] = []
    for spec in applicable:
        user_value = merged_servers.get(spec.name)
        if spec.name not in merged_servers:
            merged_servers[spec.name] = json.loads(json.dumps(spec.config))
            restored.append(spec.name)
            report["actions"].append({
                "path": MCP_JSON_RELPATH, "action": "server-restored",
                "server": spec.name,
            })
            add_warning(report, "MCP_SERVER_RESTORED",
                        f"{MCP_JSON_RELPATH} 补回默认 server `{spec.name}`")
            continue
        if not isinstance(user_value, dict):
            add_warning(report, "MCP_SERVER_INVALID",
                        f"{MCP_JSON_RELPATH} 的 `{spec.name}` 不是对象，保持原值不合并")
            continue
        merged_servers[spec.name] = merge_server(
            spec.config, user_value, MCP_JSON_RELPATH, spec.name, report)

    new_document = dict(document)
    new_document["mcpServers"] = merged_servers
    if new_document == document:
        # 语义无变化 → 不改写既有文件（零写入、零备份）。
        report["steps"].append({
            "name": "mcp_json", "status": "unchanged",
            "detail": "无需改写",
        })
        report["actions"].append({
            "path": MCP_JSON_RELPATH, "action": "unchanged",
        })
        return
    content = json.dumps(new_document, ensure_ascii=False, indent=2) + "\n"

    if content == original:
        report["steps"].append({
            "name": "mcp_json", "status": "unchanged",
            "detail": "无需改写",
        })
        report["actions"].append({
            "path": MCP_JSON_RELPATH, "action": "unchanged",
        })
        return

    publish(path, content, root, report)
    report["steps"].append({
        "name": "mcp_json", "status": "merged",
        "detail": f"补回 {len(restored)} 个默认 server，合并其余 server",
    })
    report["actions"].append({
        "path": MCP_JSON_RELPATH, "action": "merged",
        "detail": f"restored={len(restored)}",
    })


def _degrade_unparseable(path: Path, rel_label: str, original: str,
                         specs: list[ServerSpec], report: dict,
                         reason: str, step_name: str = "mcp_json") -> None:
    """解析失败：不重建、不覆盖，保持原文件，报告 degraded 与 pending。"""
    add_warning(report, "UNIT_UNPARSEABLE",
                f"{rel_label} {reason}，保持原文件不写入")
    for spec in specs:
        report["pending"].append({
            "path": rel_label, "server": spec.name,
            "reason": "unparseable-target",
            "framework_value": spec.config,
        })
    report["steps"].append({
        "name": step_name, "status": "degraded",
        "detail": f"{reason}；原文件保持不变 sha256="
                  f"{hashlib.sha256(original.encode('utf-8')).hexdigest()[:16]}",
    })
    report["actions"].append({
        "path": rel_label, "action": "kept-unparseable",
    })
    report["overall"] = "degraded"


# ---------------------------------------------------------------------------
# `.codex/config.toml` 合并
# ---------------------------------------------------------------------------

HEADER_RE = re.compile(r"^\s*\[\[?([^\]]+)\]\]?\s*(?:#.*)?$")
KEY_RE = re.compile(r"^(\s*)(?:([A-Za-z0-9_-]+)|\"([^\"]*)\")\s*=\s*(.*)$")


def _split_toml_path(raw: str) -> list[str]:
    """拆分 TOML 表路径（支持引号段）。"""
    parts = re.findall(r'"[^"]*"|[^.\s]+', raw)
    out = []
    for part in parts:
        part = part.strip()
        if part.startswith('"') and part.endswith('"'):
            part = part[1:-1]
        out.append(part)
    return out


def _parse_toml_sections(lines: list[str]) -> list[dict]:
    """扫描表头，返回 [{path, start, end}]（end 为下一个表头行号）。"""
    sections: list[dict] = []
    for idx, line in enumerate(lines):
        match = HEADER_RE.match(line)
        if not match:
            continue
        if sections:
            sections[-1]["end"] = idx
        sections.append({
            "path": _split_toml_path(match.group(1)),
            "start": idx,
            "end": len(lines),
        })
    return sections


def _section_keys(lines: list[str], section: dict) -> dict[str, int]:
    """返回该表块内已有的键 → 行号。"""
    keys: dict[str, int] = {}
    for idx in range(section["start"] + 1, section["end"]):
        match = KEY_RE.match(lines[idx])
        if not match:
            continue
        key = match.group(2) if match.group(2) is not None else match.group(3)
        keys.setdefault(key, idx)
    return keys


def _parse_inline_table(text: str) -> Optional[list[list[str]]]:
    """解析 inline table 文本 → [[key, raw_value], ...]；失败返回 None。"""
    stripped = text.strip()
    if not stripped.startswith("{") or not stripped.endswith("}"):
        return None
    body = stripped[1:-1].strip()
    if not body:
        return []
    items: list[list[str]] = []
    depth = 0
    in_string = False
    escaped = False
    current = ""
    for char in body:
        if in_string:
            current += char
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            current += char
            continue
        if char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        if char == "," and depth == 0:
            items.append(current)
            current = ""
            continue
        current += char
    items.append(current)
    pairs: list[list[str]] = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            return None
        key_token, _, value = item.partition("=")
        key_token = key_token.strip()
        key = key_token
        if key.startswith('"') and key.endswith('"'):
            key = key[1:-1]
        # 第三个元素保留用户原始键写法（引号风格），渲染时原样回写。
        pairs.append([key, value.strip(), key_token])
    return pairs


def _render_inline_table(pairs: list[list[str]]) -> str:
    inner = ", ".join(
        f"{pair[2] if len(pair) > 2 else toml_key(pair[0])} = {pair[1]}"
        for pair in pairs)
    return "{ " + inner + " }" if inner else "{}"


def _raw_is_placeholder(raw: str) -> bool:
    """inline table 中的原始值是否是占位符。"""
    value = raw.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    return is_placeholder(value)


def _merge_inline_table(raw_value: str, framework_map: dict) -> tuple[str, list[str]]:
    """合并 inline table：补齐框架独有的键；用户占位符值取框架值。

    返回 (新文本, 变更说明列表)。
    """
    pairs = _parse_inline_table(raw_value)
    if pairs is None:
        return raw_value, []
    present = {pair[0] for pair in pairs}
    notes: list[str] = []
    for key, framework_value in framework_map.items():
        if key not in present:
            pairs.append([key, toml_value(framework_value), toml_key(key)])
            notes.append(f"added:{key}")
            continue
        for pair in pairs:
            if pair[0] == key and _raw_is_placeholder(pair[1]):
                new_raw = toml_value(framework_value)
                if new_raw != pair[1]:
                    pair[1] = new_raw
                    notes.append(f"placeholder-replaced:{key}")
                break
    if not notes:
        return raw_value, []
    return _render_inline_table(pairs), notes


def codex_block(spec: ServerSpec) -> list[str]:
    """渲染 `[mcp_servers.<name>]` 表块行。"""
    lines = [f"[mcp_servers.{toml_key(spec.name)}]"]
    config = spec.config
    if "command" in config:
        lines.append(f"command = {toml_value(config['command'])}")
        if config.get("args"):
            lines.append(f"args = {toml_value(config['args'])}")
        if config.get("env"):
            lines.append(f"env = {toml_value(config['env'])}")
    elif "url" in config:
        lines.append(f"url = {toml_value(config['url'])}")
        headers = config.get("headers") or config.get("http_headers")
        if headers:
            lines.append(f"http_headers = {toml_value(headers)}")
    return lines


def _codex_framework_fields(spec: ServerSpec) -> dict[str, Any]:
    """框架的 Codex 表块字段（command/args/env/url/http_headers）。"""
    config = spec.config
    fields: dict[str, Any] = {}
    if "command" in config:
        fields["command"] = config["command"]
        if config.get("args"):
            fields["args"] = config["args"]
        if config.get("env"):
            fields["env"] = config["env"]
    elif "url" in config:
        fields["url"] = config["url"]
        headers = config.get("headers") or config.get("http_headers")
        if headers:
            fields["http_headers"] = headers
    return fields


def merge_codex_toml(root: Path, specs: list[ServerSpec], project_type: str,
                     report: dict) -> None:
    """合并（或创建）`.codex/config.toml`：按 `[mcp_servers.<name>]` 补齐缺失项。"""
    path = root / CODEX_TOML_RELPATH
    applicable = [spec for spec in specs if spec.applies(project_type)]

    if not path.exists():
        lines = ["[mcp_servers]"]
        for spec in applicable:
            lines.append("")
            lines.extend(codex_block(spec))
        content = "\n".join(lines) + "\n"
        publish(path, content, root, report)
        report["steps"].append({
            "name": "codex_toml", "status": "created",
            "detail": f"创建默认 server {len(applicable)} 个",
        })
        report["actions"].append({
            "path": CODEX_TOML_RELPATH, "action": "created",
            "detail": f"默认 server {len(applicable)} 个",
        })
        return

    if tomllib is None:
        add_warning(report, "UNIT_UNPARSEABLE",
                    f"{CODEX_TOML_RELPATH} 缺少 tomllib，跳过 TOML 合并")
        report["steps"].append({
            "name": "codex_toml", "status": "degraded",
            "detail": "缺少 tomllib",
        })
        report["overall"] = "degraded"
        return

    try:
        original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        add_warning(report, "UNIT_UNPARSEABLE",
                    f"{CODEX_TOML_RELPATH} 无法按 UTF-8 读取：{exc}")
        report["steps"].append({
            "name": "codex_toml", "status": "degraded",
            "detail": "无法读取，保持原文件",
        })
        report["overall"] = "degraded"
        return
    try:
        tomllib.loads(original)
    except Exception as exc:  # noqa: BLE001 - tomllib 抛多种异常
        _degrade_unparseable(path, CODEX_TOML_RELPATH, original, applicable,
                             report, f"TOML 解析失败：{exc}", step_name="codex_toml")
        return

    lines = original.splitlines()
    trailing_newline = original.endswith("\n")
    sections = _parse_toml_sections(lines)
    restored: list[str] = []
    changed = False

    for spec in applicable:
        target = None
        for section in sections:
            if section["path"] == ["mcp_servers", spec.name]:
                target = section
                break
        if target is None:
            restored.append(spec.name)
            changed = True
            if lines and lines[-1].strip():
                lines.append("")
            lines.extend(codex_block(spec))
            sections = _parse_toml_sections(lines)
            report["actions"].append({
                "path": CODEX_TOML_RELPATH, "action": "server-restored",
                "server": spec.name,
            })
            add_warning(report, "MCP_SERVER_RESTORED",
                        f"{CODEX_TOML_RELPATH} 补回默认 server `{spec.name}`")
            continue

        framework_fields = _codex_framework_fields(spec)
        sub_tables = {
            section["path"][2]
            for section in sections
            if len(section["path"]) == 3
            and section["path"][0] == "mcp_servers"
            and section["path"][1] == spec.name
        }
        for field, framework_value in framework_fields.items():
            keys = _section_keys(lines, target)
            if field in keys:
                line_idx = keys[field]
                if isinstance(framework_value, dict):
                    match = KEY_RE.match(lines[line_idx])
                    if not match:
                        continue
                    raw_value = match.group(4)
                    new_raw, notes = _merge_inline_table(raw_value, framework_value)
                    if notes:
                        lines[line_idx] = (
                            f"{match.group(1)}{toml_key(field)} = {new_raw}")
                        changed = True
                        for note in notes:
                            report["actions"].append({
                                "path": CODEX_TOML_RELPATH, "action": note,
                                "server": spec.name, "field": field,
                                "key": note.split(":", 1)[-1],
                            })
                continue
            if field in sub_tables:
                # 已有子表形式（[mcp_servers.<name>.<field>]），不重复写内联表。
                continue
            indent = ""
            for idx in range(target["start"] + 1, target["end"]):
                match = KEY_RE.match(lines[idx])
                if match:
                    indent = match.group(1)
                    break
            insert_at = target["start"] + 1
            lines.insert(insert_at, f"{indent}{toml_key(field)} = "
                                     f"{toml_value(framework_value)}")
            changed = True
            sections = _parse_toml_sections(lines)
            target = next(s for s in sections
                          if s["path"] == ["mcp_servers", spec.name])
            report["actions"].append({
                "path": CODEX_TOML_RELPATH, "action": "field-added",
                "server": spec.name, "field": field,
            })

    if not changed:
        report["steps"].append({
            "name": "codex_toml", "status": "unchanged",
            "detail": "无需改写",
        })
        report["actions"].append({
            "path": CODEX_TOML_RELPATH, "action": "unchanged",
        })
        return

    content = "\n".join(lines)
    if trailing_newline or not original:
        content += "\n"

    if content == original:
        # 文本无变化 → 不改写既有文件（零写入、零备份）。
        report["steps"].append({
            "name": "codex_toml", "status": "unchanged",
            "detail": "无需改写",
        })
        report["actions"].append({
            "path": CODEX_TOML_RELPATH, "action": "unchanged",
        })
        return

    try:
        tomllib.loads(content)
    except Exception as exc:  # noqa: BLE001
        _degrade_unparseable(path, CODEX_TOML_RELPATH, original, applicable,
                             report, f"TOML 合并结果校验失败：{exc}",
                             step_name="codex_toml")
        return

    publish(path, content, root, report)
    report["steps"].append({
        "name": "codex_toml", "status": "merged",
        "detail": f"补回 {len(restored)} 个默认 server，补齐缺失表块",
    })
    report["actions"].append({
        "path": CODEX_TOML_RELPATH, "action": "merged",
        "detail": f"restored={len(restored)}",
    })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


SECURITY_GITIGNORE_LINES = (
    ".worktrees/",
    ".mcp.json",
    ".codex/config.toml",
    "cadence/cache/mcp-availability/",
)
SECURITY_GITIGNORE_REVERSE = {
    "!.worktrees/",
    "!.mcp.json",
    "!.codex/config.toml",
    "!cadence/cache/mcp-availability/",
}


def ensure_gitignore_security(root: Path, report: dict, allow_override: bool = False) -> None:
    """安全单元框架优先：确保忽略项存在，移除精确反向允许规则。

    ``allow_override=True`` 时保留用户反向规则并报告高风险。
    """
    path = root / ".gitignore"
    try:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
    except (OSError, UnicodeDecodeError) as exc:
        raise PublishError(f"无法读取 .gitignore（{exc}）") from exc
    lines = existing.splitlines()
    kept = []
    removed = []
    reverse_kept = []
    protected_tokens = (".mcp.json", "config.toml", "mcp-availability", ".worktrees")
    for line in lines:
        stripped = line.strip()
        is_reverse = stripped.startswith("!") and any(
            token in stripped for token in protected_tokens
        )
        if is_reverse:
            if allow_override:
                reverse_kept.append(stripped)
                continue
            removed.append(stripped)
            continue
        if stripped in SECURITY_GITIGNORE_LINES:
            continue  # 统一在尾部重建
        kept.append(line)
    kept.extend(line for line in SECURITY_GITIGNORE_LINES if line not in kept)
    if reverse_kept:
        kept.extend(reverse_kept)
    new_text = "\n".join(kept).rstrip("\n") + "\n"
    if new_text == existing:
        report["steps"].append({
            "name": "gitignore-security", "status": "ok",
            "action": "unchanged",
        })
        report["actions"].append({
            "file": ".gitignore", "action": "unchanged",
            "branch": "security-unit",
        })
        return
    if path.exists():
        backup_path = backup_file(path, root)
        report["backups"].append({
            "file": ".gitignore",
            "backup": rel_to_root(backup_path, root),
        })
    atomic_write(path, new_text)
    report["steps"].append({
        "name": "gitignore-security", "status": "ok",
        "action": "security-ensured",
    })
    report["actions"].append({
        "file": ".gitignore", "action": "security-ensured",
        "branch": "security-unit",
    })
    if removed:
        add_warning(
            report, "SECURITY_UNIT_FRAMEWORK_WINS",
            "已移除反向允许规则：" + ", ".join(sorted(set(removed))),
        )
    if allow_override:
        add_warning(
            report, "SECURITY_OVERRIDE_ALLOWED",
            "按 --allow-security-override 保留用户反向规则，安全风险由用户承担",
        )


def cmd_apply(args: argparse.Namespace) -> int:
    """apply 子命令。"""
    root = Path(args.project_root).expanduser()
    if not root.exists() or not root.is_dir():
        raise UsageError(f"项目根不存在或不是目录：{root}")
    root = root.resolve()
    mode = "no-interrupt" if args.no_interrupt else "normal"
    report = build_report(mode, root)

    try:
        specs = load_specs()
    except UsageError as exc:
        report["overall"] = "fail"
        report["failure"] = {
            "file": str(REQUIRED_SERVERS_FILE),
            "reason": str(exc),
            "recovery": "重新安装 mcp-configuration skill 后重试",
        }
        _finish(args, report)
        return 1

    if args.project_type:
        project_type = args.project_type
        evidence = ["--project-type 显式指定"]
    else:
        project_type, evidence = detect_project_type(root)
    report["project_type"] = project_type
    report["evidence"] = evidence

    try:
        merge_mcp_json(root, specs, project_type, report)
        merge_codex_toml(root, specs, project_type, report)
        ensure_gitignore_security(
            root, report,
            allow_override=getattr(args, "allow_security_override", False),
        )
    except (BackupError, PublishError) as exc:
        report["overall"] = "fail"
        report["failure"] = {
            "file": str(root),
            "reason": str(exc),
            "recovery": "检查归档目录与目标目录写权限后重试",
        }
        _finish(args, report)
        return 1
    except OSError as exc:
        report["overall"] = "fail"
        report["failure"] = {
            "file": str(root),
            "reason": f"文件系统错误：{exc}",
            "recovery": "检查项目目录权限后重试",
        }
        _finish(args, report)
        return 1
    except Exception as exc:  # noqa: BLE001 - 兜底：任何异常都要落报告
        report["overall"] = "fail"
        report["failure"] = {
            "file": str(root),
            "reason": f"未捕获异常：{exc}",
            "recovery": "检查项目状态与脚本版本后重试",
        }
        _finish(args, report)
        return 1

    _finish(args, report)
    return 0 if report["overall"] in ("ok", "degraded") else 1


def _finish(args: argparse.Namespace, report: dict) -> None:
    """写报告并输出摘要（不含任何密钥）。"""
    write_report(Path(args.report).expanduser(), report)
    restored = sum(1 for a in report["actions"] if a.get("action") == "server-restored")
    kept = sum(1 for a in report["actions"] if a.get("action") == "user-value-kept")
    sys.stdout.write(
        "mcp-config: overall={overall} project_type={ptype} "
        "restored={restored} user_value_kept={kept} "
        "backups={backups} warnings={warn}\n".format(
            overall=report["overall"],
            ptype=report.get("project_type"),
            restored=restored,
            kept=kept,
            backups=len(report["backups"]),
            warn=len(report["warnings"]),
        )
    )


def build_parser() -> argparse.ArgumentParser:
    """命令行解析器。"""
    parser = argparse.ArgumentParser(
        prog="mcp-config",
        description="MCP 配置确定性合并（.mcp.json / .codex/config.toml）")
    sub = parser.add_subparsers(dest="command", required=True)

    apply_cmd = sub.add_parser("apply", help="合并或创建 MCP 配置")
    apply_cmd.add_argument("--project-root", required=True,
                            help="项目根目录")
    apply_cmd.add_argument("--report", required=True,
                            help="报告 JSON 输出路径")
    apply_cmd.add_argument("--no-interrupt", action="store_true",
                            help="no-interrupt 模式（本脚本全程不提问）")
    apply_cmd.add_argument("--project-type", choices=["coding", "non-coding"],
                            default=None,
                            help="显式指定项目类型（默认自动检测）")
    apply_cmd.add_argument("--allow-security-override", action="store_true",
                            help="保留用户 .gitignore 反向规则（高风险，默认关闭）")
    apply_cmd.set_defaults(func=cmd_apply)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """入口。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except UsageError as exc:
        sys.stderr.write(f"mcp-config: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
