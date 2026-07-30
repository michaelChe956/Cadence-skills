#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rule-config — 受管生命周期配置脚本（骨架，Task 4）。

本文件实现 CLI 两阶段（dry-run / apply）、报告 schema、备份、原子写、
decisions 校验与全局备份屏障。S1-S8 的实际发布逻辑（merge/replace/create）
由后续 Task（5-9）逐步填充；当前 compute_plan 只做只读探测，step_* 执行
函数为桩（pass / raise NotImplementedError），但保证：

  * CLI / dry-run / apply 两阶段可运行；
  * 报告按冻结 schema 写出；
  * decisions 校验（缺失/未知/重复/过期）在普通模式有冲突时强制执行；
  * 全局备份屏障：任一 backup_file 失败 → 终止零发布；
  * PyYAML 缺失 → 构造 failed 报告后退出码 77。

退出码：0=success/degraded，1=failed，2=usage，77=missing-yaml。
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
import time
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple, Optional

# ---------------------------------------------------------------------------
# 依赖探测：PyYAML 缺失时构造 failed 报告后退出 77（XC-06）。
# 必须在任何业务逻辑之前；main() 入口已在更早处记录 T0。
# ---------------------------------------------------------------------------
try:
    import yaml  # type: ignore
except ImportError:
    # 允许 main() 在解析 argv 前就感知到 --report，以便写出 failed 报告。
    _arg_report: Optional[str] = None
    for _i, _a in enumerate(sys.argv):
        if _a == "--report" and _i + 1 < len(sys.argv):
            _arg_report = sys.argv[_i + 1]
        elif _a.startswith("--report="):
            _arg_report = _a.split("=", 1)[1]
    if _arg_report:
        try:
            Path(_arg_report).parent.mkdir(parents=True, exist_ok=True)
            Path(_arg_report).write_text(
                json.dumps(
                    {
                        "overall": "fail",
                        "mode": "normal",
                        "failure": {
                            "file": __file__,
                            "reason": "missing dependency: PyYAML",
                            "recovery": "pip install pyyaml",
                        },
                        "steps": [],
                        "hints": {"next": "mcp-configuration"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass
    sys.stderr.write("rule-config: 缺少依赖 PyYAML，请执行 pip install pyyaml\n")
    sys.exit(77)


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# step name 约定（Task 3 it-budget 断言 s8_codegraph elapsed_ms 对齐）。
STEP_DETECT = "s1_detect"
STEP_TEMPLATES = "s2_locate_templates"
STEP_RULES_FILES = "s3_rules_files"
STEP_ENTRY_FILES = "s4_entry_files"
STEP_SCAFFOLD = "s5_scaffold"
STEP_GITIGNORE = "s6_gitignore"
STEP_OPENSPEC_CONFIG = "s7_openspec_config"
STEP_CODEGRAPH = "s8_codegraph"

# 所有步骤的固定顺序（compute_plan 与执行阶段共用）。
STEP_ORDER = (
    STEP_DETECT,
    STEP_TEMPLATES,
    STEP_RULES_FILES,
    STEP_ENTRY_FILES,
    STEP_SCAFFOLD,
    STEP_GITIGNORE,
    STEP_OPENSPEC_CONFIG,
    STEP_CODEGRAPH,
)

# ---------------------------------------------------------------------------
# L0/L1 受管区块标记与版本常量（Task 6）
# ---------------------------------------------------------------------------

# L0 受管区块标记：版本化注释对，用于在入口文件中圈定 cadence-managed 内容。
# 与 references/rules/agent-routing-kernel.md 首尾标记逐字一致（由 Task 2 单测
# 锁定 L0_SOURCE 全文）。版本号固定为 v1（当前版本）。
L0_BEGIN = "<!-- cadence-managed:openspec-superpowers-routing:v1:start -->"
L0_END = "<!-- cadence-managed:openspec-superpowers-routing:v1:end -->"

# L1 规则文件版本标记（单行注释，位于文件首行）。
L1_MARKER_PREFIX = "<!-- cadence-framework-rule:openspec-superpowers-workflow:"
L1_V1_MARKER = "<!-- cadence-framework-rule:openspec-superpowers-workflow:v1 -->"

# 当前受支持的 L1 旧版本集合（空集）：仓库仅存 v1 规范源，无真实旧版；
# upgrade 路径由单测经 classify_l1(known_versions=...) 参数注入旧版文本覆盖。
# KNOWN_L1_VERSIONS 必须包含当前 v1 全文（与规范源逐字一致）。
KNOWN_L1_VERSIONS: dict = {}

# L1 规则文件名（走独立分支，**不**进入 merge_markdown 章节合并）。
L1_RULE_FILENAME = "openspec-superpowers-workflow.md"

# S3 普通规则文件清单（8 个，不含 L1_RULE_FILENAME；document-storage/code-reading/
# markdown-format/mcp-servers/language/code-usage-coding/code-usage-noncoding/
# agent-routing-kernel）。
ORDINARY_RULE_FILES = (
    "agent-routing-kernel.md",
    "language.md",
    "document-storage.md",
    "markdown-format.md",
    "mcp-servers.md",
    "code-reading.md",
    "code-usage-coding.md",
    "code-usage-noncoding.md",
)
# Playwright 规则文件（仅 intents.enable_playwright 时处理）。
PLAYWRIGHT_RULE_FILE = "playwright.md"


def _load_reference(name: str) -> str:
    """从 skill 目录下的 references/<name> 加载文本（加载失败返回空串）。"""
    skill_dir = Path(__file__).resolve().parent.parent
    target = skill_dir / "references" / name
    try:
        return target.read_text(encoding="utf-8")
    except OSError:
        return ""


# 初始化 KNOWN_L1_VERSIONS：v1 取 references/rules/openspec-superpowers-workflow.md 全文。
# （模块加载期执行；测试 import rc 即生效，与 test_rule_config.py 中 L1_V1 加载一致。）
try:
    KNOWN_L1_VERSIONS["v1"] = _load_reference(Path("rules") / L1_RULE_FILENAME)
except Exception:  # noqa: BLE001 — 加载失败兜底为空串，不阻断模块导入
    KNOWN_L1_VERSIONS["v1"] = ""


# ---------------------------------------------------------------------------
# BASE 入口文本常量（Task 6）：入口不存在时创建的基础文本（含文件说明 + ## 强制规则 骨架）
# 模板来源：现行 SKILL.md 的 CLAUDE.md / AGENTS.md 模板章节（见 SKILL.md 行 205+、256+）。
# L0 受管区块由 step_s4_entry_files 在首个 ## 强制规则 前插入；技术栈/包管理器/覆盖率 80%
# 块按检测结果追加；规则 2 摘要行按项目类型选择文本。
# ---------------------------------------------------------------------------

BASE_CLAUDE_MD = """# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作提供指导。

## 强制规则

> **🔴 必须遵守 - 无例外**
> 详细规则见 `.claude/rules/` 目录下的各规则文件。
> 用户自定义规则见 `cadence/project-rules/` 目录。

### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 2. 代码使用规则
- **非必要不编写代码** → 详见 `.claude/rules/code-usage.md`

### 3. 文档存储规则
- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules/` 目录下** → 详见 `.claude/rules/document-storage.md`

### 4. Markdown 格式规则
- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`

### 5. MCP Server 使用规则
- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`

### 6. 项目个性化规则（强制规则）
- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**
- 禁止在 `rules/` 目录中添加用户自定义规则
- 禁止直接修改 `rules/` 目录下的框架内置规则文件
- 详见 `cadence/project-rules/README.md`

### 7. 代码阅读规则
- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`
"""

BASE_AGENTS_MD = """# AGENTS.md

本文件为 Codex 及其他 AI Agents 在此仓库中工作提供指导。

## 默认角色

- **Coding 项目**：默认角色为**谨慎执行者**，优先阅读 issue、现有代码和约束，再按指令完成实现、验证与结果汇报。
- **非 Coding 项目**：默认遵循文档、配置、规则维护职责，非必要不编写代码。

## 强制规则

> **🔴 必须遵守 - 无例外**
> 详细规则见 `.claude/rules/` 目录下的各规则文件。
> 用户自定义规则见 `cadence/project-rules/` 目录。

### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 2. 代码使用规则
- **非必要不编写代码** → 详见 `.claude/rules/code-usage.md`

### 3. 文档存储规则
- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules/` 目录下** → 详见 `.claude/rules/document-storage.md`

### 4. Markdown 格式规则
- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`

### 5. MCP Server 与工具使用规则
- **各 MCP 工具及相关自动化工具的使用必须遵循项目规范** → 详见 `.claude/rules/mcp-servers.md`

### 6. 项目个性化规则
- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**
- 禁止在 `.claude/rules/` 目录中添加用户自定义规则
- 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件
- 详见 `cadence/project-rules/README.md`

### 7. 代码阅读规则
- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`
"""

# 规则 2（代码使用规则）摘要行：按项目类型选择文本（Coding → 遵循 TDD；非 Coding → 非必要不编写）。
RULE2_TEXT_CODING = "- **遵循 TDD 和代码规范** → 详见 `.claude/rules/code-usage.md`"
RULE2_TEXT_NONCODING = "- **非必要不编写代码** → 详见 `.claude/rules/code-usage.md`"

# 决策枚举（规则文件/L0/L1 冲突）：replace | keep。
DECISION_REPLACE = "replace"
DECISION_KEEP = "keep"

# 有界源码扫描剪枝目录清单（与 SKILL.md find 块一致；由 harness
# assert_bounded_source_scan_contract 核对）。
PRUNE_DIRS = [
    ".git",
    ".claude",
    ".claude-plugin",
    ".codex",
    ".pi",
    ".codegraph",
    "cadence-init",
    "Cadence-skills",
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    "coverage",
    ".next",
    "target",
    "__pycache__",
]

# 受支持的应用源码扩展名（detect_project 用；13 个，逐字对齐 SKILL.md find 块
# `*.java *.js *.ts *.py *.go *.php *.rs *.rb *.swift *.kt *.c *.cpp *.cs`）。
# 以带点后缀形式存储，便于 fname.endswith(SOURCE_EXTS) 一次判定。
SOURCE_EXTS = (
    ".java", ".js", ".ts", ".py", ".go", ".php", ".rs",
    ".rb", ".swift", ".kt", ".c", ".cpp", ".cs",
)

# S2 locate_templates 成对校验所需文件清单（与 SKILL.md 步骤 1b 一致）。
# 在线/离线固定路径校验三件套；glob 回退路径额外校验 document-storage.md。
TEMPLATE_REQUIRED = (
    "agent-routing-kernel.md",
    "language.md",
    "openspec-superpowers-workflow.md",
)
# glob 回退路径额外要求的文件（S1b-02）。
TEMPLATE_REQUIRED_FALLBACK = ("document-storage.md",)

# 全局 T0：main() 入口第一行记录（budget_seconds_excluding_codegraph 基准）。
T0: float = time.monotonic()


# ---------------------------------------------------------------------------
# 异常类型（Task 2 §5 契约：继承 OSError 以兼容 assertRaises(OSError)）
# ---------------------------------------------------------------------------


class UsageError(Exception):
    """命令行用法错误（退出码 2）。"""


class PublishError(OSError):
    """原子发布失败（目标文件保持不变）。"""


class BackupError(OSError):
    """备份失败（屏障终止零发布）。"""


class TemplateError(OSError):
    """模板定位失败（所有候选均不完整 → 终止并列缺失）。S2 locate_templates 用。"""


# ---------------------------------------------------------------------------
# Intents：用户意图（Task 4 接口契约）
# ---------------------------------------------------------------------------


class Intents(NamedTuple):
    """用户意图参数集合。"""

    no_interrupt: bool
    project_type: Optional[str]
    ignore_cadence: bool
    enable_playwright: bool
    enable_codegraph: bool
    decisions: Optional[Path]


# ---------------------------------------------------------------------------
# 报告构造（冻结 schema）
# ---------------------------------------------------------------------------


def build_report(mode: str, project_root: Path) -> dict:
    """构造初始报告骨架（overall/fields 占位，steps 待填充）。"""
    return {
        "overall": "ok",
        "mode": mode,
        "project_root": str(project_root),
        "project_type": None,
        "budget_seconds_excluding_codegraph": None,
        "steps": [],
        "conflicts": [],
        "backups": [],
        "hints": {"next": "mcp-configuration"},
        "failure": None,
    }


def write_report(path: Path, report: dict) -> None:
    """将报告以 JSON 写入 path（先建父目录）。"""
    ensure_parent(path)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# 纯函数：路径校验 / 父目录 / sha256 / 备份 / 原子写
# ---------------------------------------------------------------------------


def ensure_parent(path: Path) -> None:
    """确保 path 的父目录存在（parents=True, exist_ok=True）。"""
    path.parent.mkdir(parents=True, exist_ok=True)


def validate_external_path(p: Path, root: Path) -> None:
    """验证 p 为合法的「外部输入」路径：必须位于 root 之外。

    用途：decisions 等用户提供的全局输入文件应位于项目根之外（不污染项目）；
    当 p 位于 root 之内时触发 UsageError（契约：根内→UsageError）。
    根外路径（合法外部输入）静默通过。
    """
    try:
        root_resolved = root.resolve()
        p_resolved = p.resolve()
    except OSError as exc:
        raise UsageError(f"无法解析路径：{p}（{exc}）") from exc
    try:
        p_resolved.relative_to(root_resolved)
    except ValueError:
        # 位于 root 之外 → 合法外部输入，通过
        return
    # 落在 root 之内 → 触发 UsageError
    raise UsageError(f"路径 {p} 位于项目根 {root} 之内（外部输入必须位于根外）")


def sha256_file(path: Path) -> str:
    """计算文件 sha256 十六进制摘要。"""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_file(path: Path) -> Path:
    """备份文件：shutil.copy2 到同目录的 <name>.cadence-backup-<14位时间戳>。

    返回备份文件 Path；失败抛 BackupError。
    命名约定：config.yaml.cadence-backup-20260731120000（NB-02/OS-B1/L1-B1）。
    """
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = Path(str(path) + f".cadence-backup-{stamp}")
    try:
        shutil.copy2(path, backup_path)
    except OSError as exc:
        raise BackupError(f"备份失败：{path} -> {backup_path}（{exc}）") from exc
    return backup_path


def atomic_write(path: Path, content) -> None:
    """原子写入：同目录 tempfile + os.replace。

    先 ensure_parent；同目录 mkstemp 写入后 os.replace；任一步异常 → 删临时
    文件并抛 PublishError，目标文件不变。
    """
    ensure_parent(path)
    if isinstance(content, str):
        data = content.encode("utf-8")
    elif isinstance(content, bytes):
        data = content
    else:
        data = str(content).encode("utf-8")
    fd = None
    tmp_path: Optional[Path] = None
    try:
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".cadence-atomic-")
        tmp_path = Path(tmp_name)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
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


# ---------------------------------------------------------------------------
# 纯函数：merge / classify（Task 6 完整实现）
# ---------------------------------------------------------------------------
# merge_markdown / parse_sections / render_sections / l0_block / classify_l1
# 的完整语义由 Task 2 单测锁定（NC-01~08、L0-P6~P10、L1-02~06）。


# Markdown ATX 标题正则：`#{1,6}` 后接空白与标题文本。
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
# 章节标题去编号正则：去除开头的 `1.` / `1、` / `01．` 等（不要求后接空白）。
# 与 NB-01 一致：标题同名判定按去编号后的纯文本，级别必须一致。
_NUMBERING_RE = re.compile(r"^\d+[.、．]?\s*")


class Section(NamedTuple):
    """解析后的 Markdown 章节。"""

    level: int          # 标题级别（1-6）
    key: str            # 去编号后的标题文本（同名判定键）
    title: str          # 原标题文本（含编号）
    body_lines: list    # 该章节标题下的正文行列表（不含标题行本身）


def parse_sections(text: str) -> list:
    """将 Markdown 切分为章节列表（NC-01~08 / NB-01）。

    返回 list[Section]：每个章节含 level/key/title/body_lines。
    切章规则：`^(#{1,6})` + 空白 + 标题文本 识别 ATX 标题；key 为级别 + 去编号标题文本。
    文件首个标题之前的行（前言）被舍弃；无任何标题 → 返回空列表。
    """
    sections: list = []
    current: Optional[Section] = None
    for line in text.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            if current is not None:
                sections.append(current)
            level = len(m.group(1))
            title = m.group(2)
            key_body = _NUMBERING_RE.sub("", title)
            key = f"{level}:{key_body}"
            current = Section(level=level, key=key, title=title, body_lines=[])
        else:
            if current is not None:
                current.body_lines.append(line)
    if current is not None:
        sections.append(current)
    return sections


def render_sections(sections: list) -> str:
    """将 Section 列表渲染回 Markdown 文本。"""
    chunks: list = []
    for sec in sections:
        chunks.append("#" * sec.level + " " + sec.title)
        chunks.extend(sec.body_lines)
    # 保留末尾换行语义：join 后每行间用 \n；body_lines 已含原本的空行。
    return "\n".join(chunks)


def _dedup_lines_preserve_order(lines: list) -> list:
    """按完整行去重，保留首次出现的顺序。"""
    seen: set = set()
    result: list = []
    for line in lines:
        if line in seen:
            continue
        seen.add(line)
        result.append(line)
    return result


def merge_markdown(template: str, existing: Optional[str]) -> Optional[str]:
    """合并 Markdown（NC-01~08）。

    语义：
      * existing is None → 返回 template（NC-01）；
      * existing 不可解析（含不可打印控制字符） → 返回 None（NC-08，函数级终止信号）；
      * 章节合并：模板章节序为主；项目独有章节按原序追加；同名章节
        = 模板正文 + `\n\n**项目补充**\n` + 项目去重行（按完整行去重、保序）。
        强制规则章节（## 强制规则）走相同同名合并逻辑：模板正文覆盖（NC-04），
        项目补充仅保留模板中未出现的项目独有行。

    返回合并后的文本字符串；不可解析返回 None。
    """
    if existing is None:
        return template
    # NC-08：含不可打印控制字符（二进制垃圾） → 不可解析 → None。
    # 注意：正常 Markdown 含 \n/\t 等空白字符是合法的，不视为不可解析；
    # 仅当出现 str.isprintable() 判定的非空白控制字符时才终止。
    if any(ch for ch in existing if not ch.isprintable() and not ch.isspace()):
        return None

    tpl_sections = parse_sections(template)
    old_sections = parse_sections(existing)

    # 模板无章节 → 直接返回模板（无法做章节合并，模板为准）。
    if not tpl_sections:
        return template

    # 以 key 索引项目章节；同名判定按 key（级别 + 去编号标题）。
    old_by_key: dict = {}
    for sec in old_sections:
        old_by_key.setdefault(sec.key, sec)

    merged: list = []
    used_keys: set = set()
    for tsec in tpl_sections:
        used_keys.add(tsec.key)
        body = list(tsec.body_lines)
        if tsec.key in old_by_key:
            old_sec = old_by_key[tsec.key]
            # 项目独有行 = 项目章节中模板未出现的完整行（按完整行去重、保序）。
            template_lines = set(_dedup_lines_preserve_order(body))
            project_only = [
                line for line in old_sec.body_lines
                if line not in template_lines and line.strip()
            ]
            if project_only:
                # NC-03：同名章节正文 = 模板正文 + \n\n**项目补充**\n + 项目去重行。
                body.append("")
                body.append("")
                body.append("**项目补充**")
                body.extend(project_only)
        merged.append(Section(
            level=tsec.level, key=tsec.key, title=tsec.title, body_lines=body,
        ))

    # 项目独有章节（模板无同名 key）按原序追加。
    for osec in old_sections:
        if osec.key not in used_keys:
            merged.append(osec)

    return render_sections(merged)


def l0_block(text: str, source: str) -> str:
    """判定 L0 受管区块状态（L0-P6~P10）。

    返回五态之一：
      * skip：当前 v1 标记对且区块与规范源逐字一致；
      * drift：v1 标记对但区块内容不同；
      * insert：两个标记都不存在（需插入）；
      * upgrade：成对受支持旧版本标记（v0 等，不在当前 v1/source 中）；
      * broken：单侧标记或标记顺序错误。
    """
    begin_idx = text.find(L0_BEGIN)
    end_idx = text.find(L0_END)
    has_begin = begin_idx != -1
    has_end = end_idx != -1

    if has_begin and has_end:
        # 两个 v1 标记都在：顺序必须正确（begin 在 end 之前），否则 broken。
        if begin_idx > end_idx:
            return "broken"
        block_start = begin_idx
        block_end = end_idx + len(L0_END)
        block = text[block_start:block_end]
        return "skip" if block.strip() == source.strip() else "drift"

    # 恰有一个 v1 标记 → 先看是否成对旧版标记（upgrade），否则单侧 broken。
    if has_begin or has_end:
        for ver in ("v0",):
            old_begin_marker = (
                "<!-- cadence-managed:openspec-superpowers-routing:" + ver + ":start -->"
            )
            old_end_marker = (
                "<!-- cadence-managed:openspec-superpowers-routing:" + ver + ":end -->"
            )
            ob = text.find(old_begin_marker)
            oe = text.find(old_end_marker)
            if ob != -1 and oe != -1 and ob < oe:
                return "upgrade"
        # 单侧 v1 标记且无成对旧版标记 → broken。
        return "broken"

    # 两个 v1 标记都不在：检查是否成对旧版标记（upgrade）。
    for ver in ("v0",):
        old_begin_marker = (
            "<!-- cadence-managed:openspec-superpowers-routing:" + ver + ":start -->"
        )
        old_end_marker = (
            "<!-- cadence-managed:openspec-superpowers-routing:" + ver + ":end -->"
        )
        ob = text.find(old_begin_marker)
        oe = text.find(old_end_marker)
        if ob != -1 and oe != -1 and ob < oe:
            return "upgrade"
        if ob != -1 or oe != -1:
            # 旧版单侧标记 → broken。
            return "broken"

    # 两标记都不存在 → 需插入。
    return "insert"


def classify_l1(path: Path, v1_source: str, known_versions: dict) -> str:
    """判定 L1 规则文件版本分类（L1-02~06）。

    返回 'skip'/'upgrade'/'replace' 之一：
      * skip：完整内容与当前框架 v1 规范源逐字一致；
      * upgrade：完整内容与 known_versions 中某个旧版逐字一致（仓库无真实旧版，
        由单测经 known_versions={"v0": ...} 注入覆盖）；
      * replace：v1 漂移 / 旧版漂移 / 无标记（任何分支都不调 merge_markdown）。

    红线：标记只用于定位候选版本；最终识别必须比较完整文件内容（L1-B2）。
    任何分支 MUST NOT 调 merge_markdown，结果 MUST NOT 含「项目补充」。
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # 文件不可读 → 当作无标记文件，replace（备份与替换由调用方处理）。
        return "replace"

    # 1) 当前 v1 逐字一致 → skip。
    if content == v1_source:
        return "skip"

    # 2) known_versions 旧版逐字一致 → upgrade（按版本号排序保证 v1 优先已在上一步处理）。
    versions = known_versions or {}
    for ver, text in versions.items():
        if ver == "v1":
            continue
        if text and content == text:
            return "upgrade"

    # 3) 其余（v1 漂移 / 旧版漂移 / 无标记） → replace。
    return "replace"


def merge_yaml(template: str, existing: str):
    """合并 OpenSpec config.yaml（NC-05/06, OS-N5~N8）。

    返回 (merged_text, conflicts)；不可解析时 merged=None 作为终止信号（NC-06）。
    语义：
      * existing 不可解析 → (None, [])（函数级终止信号，备份与终止由调用方执行）；
      * rules.apply 存在 → 报告 conflicts=[{"kind":"rules.apply",...}]（NC-05+OS-N8），
        但 merged 仍返回合并后的文本（移除 rules.apply）；调用方据 conflicts 决定是否终止；
      * schema 缺失 → 写入 spec-driven（OS-N5）；保留项目 schema；
      * context 按完整行去重追加（项目行在前，模板去重行在后）（OS-N6）；
      * 四个 artifact 数组去重追加，项目额外规则保留（OS-N7）；
      * 保留项目自定义键。
    """
    try:
        tpl_doc = yaml.safe_load(template) or {}
    except yaml.YAMLError:
        # 模板不可解析（不应发生）→ 返回模板原文。
        return template, []
    try:
        old_doc = yaml.safe_load(existing) if existing else {}
    except yaml.YAMLError:
        # NC-06：不可解析 → None 终止信号。
        return None, []
    if not isinstance(old_doc, dict):
        old_doc = {}
    if not isinstance(tpl_doc, dict):
        tpl_doc = {}

    conflicts: list = []
    merged: dict = {}

    # 保留项目自定义键（模板与项目均有的键按下面逻辑合并；项目独有的原样保留）。
    for key, val in old_doc.items():
        if key not in ("schema", "context", "rules"):
            merged[key] = val

    # schema：项目保留；缺失时写入模板值（OS-N5）。
    if "schema" in old_doc:
        merged["schema"] = old_doc["schema"]
    elif "schema" in tpl_doc:
        merged["schema"] = tpl_doc["schema"]

    # context：项目行在前 + 模板去重行在后（OS-N06，按完整行去重保序）。
    tpl_context = tpl_doc.get("context", "") or ""
    old_context = old_doc.get("context", "") or ""
    if old_context or tpl_context:
        old_lines = old_context.splitlines()
        tpl_lines = tpl_context.splitlines()
        seen = set()
        result_lines: list = []
        for line in old_lines:
            if line not in seen:
                seen.add(line)
                result_lines.append(line)
        for line in tpl_lines:
            if line not in seen:
                seen.add(line)
                result_lines.append(line)
        merged["context"] = "\n".join(result_lines) + "\n" if result_lines else ""

    # rules：合并四个 artifact 数组（OS-N07）；检测 rules.apply 冲突（NC-05+OS-N8）。
    tpl_rules = tpl_doc.get("rules", {}) or {}
    old_rules = old_doc.get("rules", {}) or {}
    merged_rules: dict = {}
    # 项目独有的 rules 子键原样保留（除四个 artifact 外）。
    for key, val in old_rules.items():
        if key not in ("proposal", "design", "specs", "tasks") and key != "apply":
            merged_rules[key] = val
    # 四个 artifact：项目规则在前 + 模板去重规则在后。
    for group in ("proposal", "design", "specs", "tasks"):
        old_items = old_rules.get(group, []) or []
        tpl_items = tpl_rules.get(group, []) or []
        if not isinstance(old_items, list):
            old_items = []
        if not isinstance(tpl_items, list):
            tpl_items = []
        seen_items: list = []
        seen_set: set = set()
        for item in old_items:
            if isinstance(item, str) and item not in seen_set:
                seen_set.add(item)
                seen_items.append(item)
        for item in tpl_items:
            if isinstance(item, str) and item not in seen_set:
                seen_set.add(item)
                seen_items.append(item)
        if seen_items:
            merged_rules[group] = seen_items
    # rules.apply 冲突检测（NC-05+OS-N8）：项目含 apply → 报告冲突。
    if "apply" in old_rules:
        conflicts.append({
            "kind": "rules.apply",
            "path": "rules.apply",
            "value": old_rules["apply"],
        })
    if merged_rules:
        merged["rules"] = merged_rules

    # 渲染为 YAML 文本（保留中文；sort_keys=False 保序）。
    try:
        merged_text = yaml.safe_dump(
            merged, allow_unicode=True, sort_keys=False, default_flow_style=False,
            width=4096,
        )
    except yaml.YAMLError:
        return None, []
    return merged_text, conflicts


def precheck_openspec_structure(doc: Any) -> list:
    """校验 openspec config 结构（OS-N2）。返回冲突字段路径列表，空=通过。

    类型矩阵：
      * 根必须为映射；
      * schema（若存在）必须为标量（非 list/dict）；
      * context（若存在）必须为字符串；
      * rules（若存在）必须为映射；
      * rules.{proposal,design,specs,tasks}（若存在）必须为字符串数组。
    自定义键原样保留（不报冲突）。
    """
    conflicts: list = []
    if not isinstance(doc, dict):
        conflicts.append("<root>")
        return conflicts
    # schema 必须为标量（允许缺失；存在时非 list/dict）。
    if "schema" in doc and isinstance(doc["schema"], (list, dict)):
        conflicts.append("schema")
    # context 必须为字符串。
    if "context" in doc and not isinstance(doc["context"], str):
        conflicts.append("context")
    # rules 必须为映射。
    rules = doc.get("rules")
    if rules is not None:
        if not isinstance(rules, dict):
            conflicts.append("rules")
        else:
            # 四个 artifact 必须为字符串数组（若存在）。
            for group in ("proposal", "design", "specs", "tasks"):
                if group in rules:
                    val = rules[group]
                    if not isinstance(val, list) or any(
                        not isinstance(item, str) for item in val
                    ):
                        conflicts.append(f"rules.{group}")
    return conflicts


# ---------------------------------------------------------------------------
# decisions 校验（XC-03）
# ---------------------------------------------------------------------------


def load_decisions(path: Path) -> list:
    """加载 decisions JSON 文件，返回决策列表。

    格式：[{"conflict_id": "<id>", "decision": "<keep|replace|...>"}]。
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise UsageError(f"无法读取 decisions 文件：{path}（{exc}）") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UsageError(f"decisions 文件不是合法 JSON：{path}（{exc}）") from exc
    if not isinstance(data, list):
        raise UsageError(f"decisions 文件必须是数组：{path}")
    return data


def validate_decisions(plan: dict, decisions: list) -> list:
    """校验 decisions 与 plan 冲突清单的一致性。

    返回违规清单（字符串列表），空=通过。检查：
      * 缺失：plan 有冲突但 decisions 未提供（无 --decisions 时 decisions=[]）；
      * 未知：decisions 含 plan 不认识的 conflict_id；
      * 重复：同一 conflict_id 出现多次；
      * 过期：decision 不在该冲突的 allowed_decisions 集合内（含空 decision）。

    仅普通模式且 plan 有冲突时调用（no-interrupt 模式按权威规则自动决策）。

    每个 conflict 条目应携带 allowed_decisions（list[str]），由 compute_plan
    按资产类型生成（如规则文件/L0/L1 → ['replace','keep']）。decision 不在
    该集合内即记为「过期」违规（区别于「缺失」）。
    """
    violations: list = []
    plan_conflicts = plan.get("conflicts", []) or []
    # conflict_id -> 允许的决策集（缺失时退化为 ['replace','keep']）
    allowed_by_id: dict = {}
    for c in plan_conflicts:
        cid = c.get("conflict_id")
        if not cid:
            continue
        allowed = c.get("allowed_decisions")
        if not isinstance(allowed, list) or not allowed:
            allowed = ["replace", "keep"]
        allowed_by_id[cid] = allowed
    plan_ids = set(allowed_by_id.keys())

    # decisions 索引
    seen: dict = {}
    for entry in decisions:
        if not isinstance(entry, dict):
            violations.append("decisions 条目不是对象")
            continue
        cid = entry.get("conflict_id")
        decision = entry.get("decision")
        if cid is None:
            violations.append("decisions 条目缺少 conflict_id")
            continue
        if cid not in plan_ids:
            violations.append(f"未知 conflict_id：{cid}")
            continue
        if cid in seen:
            violations.append(f"重复 conflict_id：{cid}")
            continue
        seen[cid] = decision
        # 过期：decision 不在该冲突的允许决策集内（含空 decision）。
        allowed = allowed_by_id[cid]
        if not decision or decision not in allowed:
            violations.append(
                f"决策过期：{cid} 的 decision={decision!r} 不在允许集 {allowed}"
            )

    # 缺失：plan 有冲突但 decisions 未覆盖
    missing = plan_ids - set(seen.keys())
    for cid in sorted(missing):
        violations.append(f"冲突缺少决策：{cid}")

    return violations


# ---------------------------------------------------------------------------
# compute_plan：只读探测，填充 steps/conflicts/backup_needs（S1-S8 骨架）
# ---------------------------------------------------------------------------


def compute_plan(root: Path, intents: Intents) -> dict:
    """两阶段共享的只读探测：扫描项目，填充 plan。

    plan 结构：
      {
        "project_type": "coding"|"non-coding",
        "steps": {<step_name>: {"status", "actions", "conflicts", "backup_needs", ...}},
        "conflicts": [{"conflict_id", "kind", ...}],
        "backup_needs": [<Path>, ...],   # 全部需要备份的文件
      }

    本骨架实现：
      * S1 detect：判定 project_type（扫描源码文件）；
      * S2-S7：对入口文件 / 规则文件 / openspec config 做存在性与漂移探测，
        产生 conflict 条目（普通模式需 decisions 响应）；
      * backup_needs：汇总所有将被修改/替换的现有文件。
    """
    plan: dict = {
        "project_type": "non-coding",
        "steps": {},
        "conflicts": [],
        "backup_needs": [],
    }

    # --- S1 detect：项目类型 + 技术栈 ---
    s1 = _step_skeleton(STEP_DETECT)
    detect_result = detect_project(root, intents)
    plan["project_type"] = detect_result["project_type"]
    plan["tech_stack"] = detect_result["tech_stack"]
    s1["status"] = "ok"
    s1["note"] = (
        f"project_type={detect_result['project_type']}; "
        f"evidence={detect_result['evidence']}"
    )
    s1["assets"] = [{
        "path": "<project>",
        "action": "detect",
        "conflict": None,
        "backup_needed": False,
        "project_type": detect_result["project_type"],
        "evidence": detect_result["evidence"],
        "tech_stack": detect_result["tech_stack"],
    }]
    # 矛盾冲突项（allowed_decisions=['coding','non-coding']）
    conflict = detect_result.get("conflict")
    if conflict:
        s1["conflicts"] = [conflict]
        plan["conflicts"].append(conflict)
    plan["steps"][STEP_DETECT] = s1

    # --- S2 locate templates：三级定位 ---
    s2 = _step_skeleton(STEP_TEMPLATES)
    try:
        rules_root, openspec_yaml = locate_templates()
        s2["status"] = "ok"
        s2["note"] = f"rules_root={rules_root}"
        s2["assets"] = [{
            "path": str(rules_root),
            "action": "locate",
            "conflict": None,
            "backup_needed": False,
            "openspec_yaml": str(openspec_yaml),
        }]
        plan["templates"] = {
            "rules_root": str(rules_root),
            "openspec_yaml": str(openspec_yaml),
        }
    except TemplateError as exc:
        s2["status"] = "fail"
        s2["note"] = str(exc)
        plan["failure"] = {
            "step": STEP_TEMPLATES,
            "reason": str(exc),
            "recovery": "检查模板安装路径或提供完整模板候选",
        }
    plan["steps"][STEP_TEMPLATES] = s2

    # --- S3 rules files：探测普通规则文件（8 个）+ L1 独立分支 + Playwright ---
    s3 = _step_skeleton(STEP_RULES_FILES)
    templates_info = plan.get("templates", {}) or {}
    rules_root_str = templates_info.get("rules_root")
    rules_root = Path(rules_root_str) if rules_root_str else None
    rules_dir = root / ".claude" / "rules"
    # S3 处理的文件清单（按序）：普通 8 文件 + L1 + （enable_playwright 时）Playwright。
    s3_targets = list(ORDINARY_RULE_FILES) + [L1_RULE_FILENAME]
    if intents.enable_playwright:
        s3_targets.append(PLAYWRIGHT_RULE_FILE)
    for fname in s3_targets:
        is_l1 = (fname == L1_RULE_FILENAME)
        target = rules_dir / fname
        rel = str(target.relative_to(root)) if target.exists() else f".claude/rules/{fname}"
        # 模板源文本（rules_root 不可用时退化为空串，该文件跳过处理）。
        if rules_root is not None:
            try:
                template_text = (rules_root / fname).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                template_text = ""
        else:
            template_text = ""
        if not target.exists():
            # 不存在 → created（无冲突；模板缺失时退化为 skip，不创建空文件）。
            action = "create" if template_text else "skip"
            s3["assets"].append({
                "path": rel,
                "action": action,
                "conflict": None,
                "backup_needed": False,
                "is_l1": is_l1,
            })
            continue
        # 文件存在 → 分类。
        # Playwright 规则文件已存在时不覆盖（尊重用户自定义，无论内容差异）。
        if fname == PLAYWRIGHT_RULE_FILE and target.exists():
            s3["assets"].append({
                "path": rel, "action": "skip", "conflict": None,
                "backup_needed": False, "is_l1": False,
            })
            continue
        try:
            existing_text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            existing_text = ""
        if is_l1:
            state = classify_l1(target, template_text, KNOWN_L1_VERSIONS)
            # L1：skip → 无冲突；upgrade/replace → 冲突（allowed=['replace','keep']）。
            if state == "skip":
                s3["assets"].append({
                    "path": rel, "action": "skip", "conflict": None,
                    "backup_needed": False, "is_l1": True,
                })
            else:
                s3["assets"].append({
                    "path": rel, "action": "replace", "conflict": state,
                    "backup_needed": True, "is_l1": True,
                })
                conflict_id = f"s3:{rel}"
                s3["conflicts"].append({
                    "conflict_id": conflict_id, "asset": rel, "state": state,
                    "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                    "question": f"L1 规则文件 {rel} 状态为 {state}",
                    "recommendation": DECISION_REPLACE,
                })
                plan["conflicts"].append({
                    "conflict_id": conflict_id, "asset": rel, "kind": "l1",
                    "state": state,
                    "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                    "question": f"L1 规则文件 {rel} 状态为 {state}",
                    "recommendation": DECISION_REPLACE,
                })
                _append_backup_need(plan, target)
        else:
            # 普通规则文件：一致 → skipped；冲突 → 冲突（allowed=['replace','keep']）。
            if existing_text == template_text:
                s3["assets"].append({
                    "path": rel, "action": "skip", "conflict": None,
                    "backup_needed": False, "is_l1": False,
                })
            else:
                s3["assets"].append({
                    "path": rel, "action": "replace", "conflict": "drift",
                    "backup_needed": True, "is_l1": False,
                })
                conflict_id = f"s3:{rel}"
                s3["conflicts"].append({
                    "conflict_id": conflict_id, "asset": rel, "state": "drift",
                    "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                    "question": f"规则文件 {rel} 与模板不一致",
                    "recommendation": DECISION_REPLACE,
                })
                plan["conflicts"].append({
                    "conflict_id": conflict_id, "asset": rel, "kind": "rules",
                    "state": "drift",
                    "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                    "question": f"规则文件 {rel} 与模板不一致",
                    "recommendation": DECISION_REPLACE,
                })
                _append_backup_need(plan, target)
    s3["status"] = "ok"
    plan["steps"][STEP_RULES_FILES] = s3

    # --- S4 entry files：探测 CLAUDE.md / AGENTS.md 漂移 ---
    s4 = _step_skeleton(STEP_ENTRY_FILES)
    kernel_source = _load_kernel_source()
    for entry_name in ("CLAUDE.md", "AGENTS.md"):
        entry_path = root / entry_name
        if not entry_path.exists():
            s4["assets"].append({
                "path": entry_name,
                "action": "create",
                "conflict": None,
                "backup_needed": False,
            })
            continue
        # 文件存在 → 检测 L0 区块状态（骨架：存在即视为可能漂移 → conflict）
        try:
            text = entry_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            text = ""
        state = l0_block(text, kernel_source) if kernel_source else "insert"
        conflict_id = f"s4:{entry_name}"
        if state == "skip":
            s4["assets"].append({
                "path": entry_name,
                "action": "skip",
                "conflict": None,
                "backup_needed": False,
            })
        else:
            # insert/drift/upgrade/broken 均视为需要决策的冲突（普通模式）
            s4["assets"].append({
                "path": entry_name,
                "action": "replace" if state in ("drift", "upgrade") else "create",
                "conflict": state,
                "backup_needed": True,
            })
            plan["conflicts"].append({
                "conflict_id": conflict_id,
                "asset": entry_name,
                "state": state,
                "allowed_decisions": ["replace", "keep"],
                "question": f"入口文件 {entry_name} 的 L0 受管区块状态为 {state}",
                "recommendation": "replace",
            })
            _append_backup_need(plan, entry_path)
    s4["status"] = "ok"
    plan["steps"][STEP_ENTRY_FILES] = s4

    # --- S5 scaffold：探测 cadence/ 目录（骨架） ---
    s5 = _step_skeleton(STEP_SCAFFOLD)
    s5["status"] = "ok"
    plan["steps"][STEP_SCAFFOLD] = s5

    # --- S6 gitignore：探测 .gitignore（骨架） ---
    s6 = _step_skeleton(STEP_GITIGNORE)
    s6["status"] = "ok"
    plan["steps"][STEP_GITIGNORE] = s6

    # --- S7 openspec config：探测 openspec/config.yaml ---
    # 骨架：当前不产生 conflict（rules.apply 类型/结构冲突由 Task 8 实现）。
    # 后续 Task 8 在此产生 openspec 冲突时，allowed_decisions 应为
    # ['remove_apply','keep']（见 validate_decisions 的 allowed_decisions 约定）。
    s7 = _step_skeleton(STEP_OPENSPEC_CONFIG)
    config_path = root / "openspec" / "config.yaml"
    if config_path.exists():
        s7["assets"].append({
            "path": "openspec/config.yaml",
            "action": "merge",
            "conflict": None,
            "backup_needed": True,
        })
        _append_backup_need(plan, config_path)
    s7["status"] = "ok"
    plan["steps"][STEP_OPENSPEC_CONFIG] = s7

    # --- S8 codegraph：探测是否需要执行（骨架） ---
    s8 = _step_skeleton(STEP_CODEGRAPH)
    s8["elapsed_ms"] = 0
    s8["status"] = "ok"
    plan["steps"][STEP_CODEGRAPH] = s8

    return plan


def _step_skeleton(name: str) -> dict:
    """构造一个步骤骨架。"""
    return {
        "name": name,
        "status": "skip",
        "elapsed_ms": 0,
        "actions": [],
        "assets": [],
        "conflicts": [],
        "note": "",
    }


def _append_backup_need(plan: dict, target: Path) -> None:
    """将 target 加入 plan.backup_needs（去重，避免重复备份）。

    按规范字符串形式去重（M-4）：同一文件可能被多个步骤探测到，
    备份屏障只应备份一次。
    """
    backup_needs = plan.setdefault("backup_needs", [])
    key = str(target)
    if any(str(existing) == key for existing in backup_needs):
        return
    backup_needs.append(target)


def _detect_project_type(root: Path, intents: Intents) -> str:
    """判定项目类型：显式覆盖 > 源码扫描 > 主工程配置 > non-coding。

    保留为 compute_plan 内部辅助（旧骨架入口）；完整语义见 detect_project。
    """
    return detect_project(root, intents)["project_type"]


# S2 locate_templates 固定路径的 rules 子目录后缀（相对 $HOME）。
_ONLINE_RULES_SUBPATH = (
    ".claude/plugins/marketplaces/cadence-skills-marketplace"
    "/cadence-init/skills/rule-config/references/rules"
)
_OFFLINE_RULES_SUBPATH = (
    ".claude/plugins/marketplaces/cadence-skills-local"
    "/cadence-init/skills/rule-config/references/rules"
)
# glob 回退标识文件（相对任意搜索根）。
_FALLBACK_GLOB_PATTERN = "**/cadence-init/skills/rule-config/references/rules/language.md"


def detect_project(root: Path, intents: Intents) -> dict:
    """S1 项目类型与技术栈检测。

    返回 dict：
      {
        "project_type": "coding"|"non-coding",
        "evidence": str,            # 检测证据（相对路径 / 主配置名 / "none"）
        "tech_stack": {             # 五类技术栈检测（未检出写「未检测到」）
          "language": str, "pkg_manager": str,
          "test": str, "lint": str, "format": str, "coverage": "80%",
        },
        "conflict": dict|None,     # 矛盾时为 s1:project-type-conflict 条目
      }

    优先级（简报 Task 5）：intents.project_type 优先于检测结果；
    用户指定与检测结果矛盾 → conflict=s1:project-type-conflict
    （allowed_decisions=['coding','non-coding']）。
    """
    # 1) 自动检测：有界首命中源码扫描 → coding；否则查 6 个主工程配置；全无 → non-coding。
    detected_type = "non-coding"
    evidence = "none"
    source_hit = next(_iter_source_files(root), None)
    if source_hit is not None:
        detected_type = "coding"
        try:
            evidence = f"source: {source_hit.relative_to(root)}"
        except ValueError:
            evidence = f"source: {source_hit}"
    else:
        main_cfg = _detect_main_config(root)
        if main_cfg is not None:
            detected_type = "coding"
            evidence = f"main config: {main_cfg}"

    # 2) intents.project_type 优先；矛盾判定 → conflict。
    conflict = None
    project_type = detected_type
    if intents.project_type in ("coding", "non-coding"):
        project_type = intents.project_type
        if intents.project_type != detected_type:
            conflict = {
                "conflict_id": "s1:project-type-conflict",
                "asset": "<project>",
                "detected_type": detected_type,
                "user_type": intents.project_type,
                "allowed_decisions": ["coding", "non-coding"],
                "question": (
                    f"检测结果为 {detected_type}，但用户指定为 {intents.project_type}"
                ),
                "recommendation": intents.project_type,
            }

    # 3) 技术栈检测（不受 project_type 覆盖影响，始终扫描配置文件）。
    tech_stack = _detect_tech_stack(root)

    return {
        "project_type": project_type,
        "evidence": evidence,
        "tech_stack": tech_stack,
        "conflict": conflict,
    }


# S1a-03：主工程配置清单（有界首命中扫描无源码时按此顺序查）。
_MAIN_CONFIGS = (
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
)


def _detect_main_config(root: Path) -> Optional[str]:
    """检测根下的主工程配置文件（6 个），返回首个命中名或 None。"""
    for name in _MAIN_CONFIGS:
        if (root / name).is_file():
            return name
    return None


def _detect_tech_stack(root: Path) -> dict:
    """S4 技术栈检测五类（DF-02 / S4-01~03）。

    返回 dict(language, pkg_manager, test, lint, format, coverage)。
    未检出的字段写「未检测到」（不阻塞初始化）；coverage 默认 80%。
    """
    ts = {
        "language": "未检测到",
        "pkg_manager": "未检测到",
        "test": "未检测到",
        "lint": "未检测到",
        "format": "未检测到",
        "coverage": "80%",
    }
    package_json = root / "package.json"
    if package_json.is_file():
        ts["language"] = "JavaScript/TypeScript"
        ts["pkg_manager"] = "pnpm"
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        scripts = data.get("scripts") if isinstance(data, dict) else None
        if isinstance(scripts, dict):
            for key in ("test", "lint", "format"):
                val = scripts.get(key)
                if isinstance(val, str) and val:
                    ts[key] = val

    requirements = root / "requirements.txt"
    pyproject = root / "pyproject.toml"
    has_python_cfg = requirements.is_file() or pyproject.is_file()
    if has_python_cfg:
        if ts["language"] == "未检测到":
            ts["language"] = "Python"
        ts["pkg_manager"] = "uv"
        # 检测 pytest（requirements.txt 或 pyproject.toml 任一含 pytest）
        py_text = ""
        for p in (requirements, pyproject):
            if p.is_file():
                try:
                    py_text += "\n" + p.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    pass
        if "pytest" in py_text:
            ts["test"] = "pytest"
    return ts


def locate_templates() -> tuple:
    """S2 三级模板定位（S1b-01~04）。

    返回 (rules_root: Path, openspec_yaml: Path)。

    固定路径之间按优先级短路（在线优先）：
      1) 在线 ~/.claude/plugins/marketplaces/cadence-skills-marketplace/... 完整即直接返回；
      2) 在线不完整 → 离线 ~/.claude/plugins/marketplaces/cadence-skills-local/... 完整即返回；
      3) 固定路径均不完整 → glob 回退
         **/cadence-init/skills/rule-config/references/rules/language.md
         （多候选取 mtime 最新；mtime 比较仅在此阶段用于多候选择优）。

    成对校验（S1b-02）：每候选 rules/ 下须含 TEMPLATE_REQUIRED 三件套
    （回退路径额外须含 document-storage.md）+ 同级 references/openspec/config.yaml；
    缺任则该候选不完整。固定路径间不混入统一 mtime 比较，以确保“在线优先”语义。
    全部候选不完整 → TemplateError 终止并逐个列出每个候选具体缺失的文件名。
    """
    home = Path(os.path.expanduser("~"))
    # (kind, rules_root, missing_files) 用于失败时构造详细错误
    failures: list = []

    # 1) 在线固定路径（短路优先：完整即返回，不查离线）
    online_rules = home / _ONLINE_RULES_SUBPATH
    online = _check_template_candidate(online_rules, fallback=False)
    if online is not None:
        return online[0], online[1]
    failures.append((
        "在线",
        online_rules,
        _missing_template_files(online_rules, fallback=False),
    ))

    # 2) 离线固定路径（在线不完整才查；完整即返回）
    offline_rules = home / _OFFLINE_RULES_SUBPATH
    offline = _check_template_candidate(offline_rules, fallback=False)
    if offline is not None:
        return offline[0], offline[1]
    failures.append((
        "离线",
        offline_rules,
        _missing_template_files(offline_rules, fallback=False),
    ))

    # 3) glob 回退：从 home 起搜索标识文件并成对校验；多候选取 mtime 最新
    fallback_candidates: list = []  # (rules_root, openspec_yaml)
    seen: set = set()
    for lang_path in home.glob(_FALLBACK_GLOB_PATTERN):
        rules_root = lang_path.parent
        key = str(rules_root.resolve())
        if key in seen:
            continue
        seen.add(key)
        pair = _check_template_candidate(rules_root, fallback=True)
        if pair is not None:
            fallback_candidates.append(pair)
        else:
            failures.append((
                "回退",
                rules_root,
                _missing_template_files(rules_root, fallback=True),
            ))

    if fallback_candidates:
        # mtime 比较仅用于 glob 回退阶段的多候选择优
        best = max(fallback_candidates, key=lambda c: _candidate_mtime(c[1]))
        return best[0], best[1]

    # 全不完整：构造逐候选缺失明细
    raise TemplateError(_format_template_failures(failures))


def _missing_template_files(rules_root: Path, *, fallback: bool) -> list:
    """返回单一候选缺失的文件名列表（含同级 openspec/config.yaml）。"""
    missing: list = []
    required = list(TEMPLATE_REQUIRED)
    if fallback:
        required = required + list(TEMPLATE_REQUIRED_FALLBACK)
    if not rules_root.is_dir():
        # 目录不存在视为三件套（含回退的 document-storage.md）全缺
        return list(required) + ["openspec/config.yaml"]
    for name in required:
        if not (rules_root / name).is_file():
            missing.append(name)
    openspec_yaml = rules_root.parent / "openspec" / "config.yaml"
    if not openspec_yaml.is_file():
        missing.append("openspec/config.yaml")
    return missing


def _format_template_failures(failures: list) -> str:
    """格式化全部不完整候选的缺失明细（每候选一行，列出缺失文件名）。"""
    lines = ["模板定位失败：所有候选均不完整"]
    for kind, rules_root, missing in failures:
        if missing:
            joined = "、".join(missing)
            lines.append(f"{kind}候选 {rules_root} 缺 {joined}")
        else:
            lines.append(f"{kind}候选 {rules_root} 不完整")
    lines.append("（在线/离线/回退均不完整）")
    return "；".join(lines)


def _check_template_candidate(rules_root: Path, *, fallback: bool):
    """校验单一候选完整性。返回 (rules_root, openspec_yaml) 或 None。

    在线/离线校验 TEMPLATE_REQUIRED 三件套；回退额外校验 document-storage.md。
    所有候选还须存在同级 references/openspec/config.yaml。
    """
    if not rules_root.is_dir():
        return None
    required = list(TEMPLATE_REQUIRED)
    if fallback:
        required = required + list(TEMPLATE_REQUIRED_FALLBACK)
    for name in required:
        if not (rules_root / name).is_file():
            return None
    openspec_yaml = rules_root.parent / "openspec" / "config.yaml"
    if not openspec_yaml.is_file():
        return None
    return rules_root, openspec_yaml


def _candidate_mtime(path: Path) -> float:
    """安全读取文件 mtime（失败返回 0）。"""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _iter_source_files(root: Path):
    """有界扫描应用源码文件（尊重 PRUNE_DIRS 剪枝，first-match -quit 语义）。"""
    prune_set = set(PRUNE_DIRS)
    for dirpath, dirnames, filenames in os.walk(root):
        # 剪枝：原地修改 dirnames 跳过
        dirnames[:] = [d for d in dirnames if d not in prune_set]
        for fname in filenames:
            if fname.endswith(SOURCE_EXTS):
                yield Path(dirpath) / fname
                return  # first-match 即可判定 coding


def _load_kernel_source() -> str:
    """加载 L0 kernel 规范源（references/rules/agent-routing-kernel.md）。"""
    skill_dir = Path(__file__).resolve().parent.parent
    kernel = skill_dir / "references" / "rules" / "agent-routing-kernel.md"
    try:
        return kernel.read_text(encoding="utf-8")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# 执行阶段：step_* 桩（Task 5-9 实现）
# ---------------------------------------------------------------------------


def step_s1_detect(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S1 执行（Task 5 实现）：回填 project_type/tech_stack 到报告。"""
    detect_result = detect_project(root, intents)
    report["project_type"] = detect_result["project_type"]
    # tech_stack 写入报告（供后续 S4 入口文件技术栈章节使用）。
    report["tech_stack"] = detect_result["tech_stack"]
    report["evidence"] = detect_result["evidence"]


def step_s2_locate_templates(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S2 执行（Task 5 实现）：定位模板根路径并缓存到 plan/report 供后续步骤复用。"""
    try:
        rules_root, openspec_yaml = locate_templates()
    except TemplateError as exc:
        # 模板定位失败已在 compute_plan 记录；执行阶段不再重复抛出
        report.setdefault("templates", {})
        report["templates"]["error"] = str(exc)
        return
    plan["templates"] = {
        "rules_root": str(rules_root),
        "openspec_yaml": str(openspec_yaml),
    }
    report["templates"] = plan["templates"]


def step_s3_rules_files(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S3 执行（Task 6 实现）。

    处理 8 个普通规则文件 + L1 独立分支 + （enable_playwright 时）Playwright。
    每个资产按 compute_plan 探测的状态执行：
      * create：读模板 atomic_write；
      * skip：不处理；
      * drift/replay（普通规则）：普通模式按 decision（keep→不覆盖，replace→已备份后写模板）；
        no-interrupt → merge_markdown，返回 None → 备份后标准结构 + `\n\n## 原项目补充\n\n` + 原文；
      * upgrade/replace（L1）：**独立分支，不调 merge_markdown**；普通模式按 decision；
        no-interrupt → 备份后写当前 v1 模板。
    """
    templates_info = plan.get("templates", {}) or {}
    rules_root_str = templates_info.get("rules_root")
    if not rules_root_str:
        return
    rules_root = Path(rules_root_str)
    rules_dir = root / ".claude" / "rules"
    decisions_map = plan.get("decisions_map", {}) or {}
    s3_step = (plan.get("steps", {}) or {}).get(STEP_RULES_FILES, {})
    assets = s3_step.get("assets", []) or []
    actions_log: list = []

    for asset in assets:
        fname = Path(asset["path"]).name
        is_l1 = asset.get("is_l1", False)
        target = rules_dir / fname
        action = asset.get("action")
        conflict = asset.get("conflict")
        # 模板源文本。
        try:
            template_text = (rules_root / fname).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            template_text = ""
        if not template_text:
            actions_log.append({"path": asset["path"], "action": "skip", "reason": "模板缺失"})
            continue

        if action == "create":
            ensure_parent(target)
            atomic_write(target, template_text)
            actions_log.append({"path": asset["path"], "action": "created"})
            continue
        if action == "skip" or conflict is None:
            actions_log.append({"path": asset["path"], "action": "skipped"})
            continue

        # 冲突资产（conflict 非空）。
        conflict_id = f"s3:{asset['path']}"
        decision = decisions_map.get(conflict_id)

        if is_l1:
            # --- L1 独立分支：绝不调 merge_markdown，结果绝不后「项目补充」 ---
            if intents.no_interrupt:
                # no-interrupt：备份已由全局屏障完成；直接写当前 v1 模板（upgrade/replace 均替换为 v1）。
                atomic_write(target, template_text)
                actions_log.append({"path": asset["path"], "action": "replaced", "branch": "l1-no-interrupt"})
            else:
                # 普通模式：按 decision（replace→已备份后写 v1 模板；keep→保留报告）。
                if decision == DECISION_REPLACE:
                    atomic_write(target, template_text)
                    actions_log.append({"path": asset["path"], "action": "replaced", "branch": "l1-replace"})
                else:
                    actions_log.append({"path": asset["path"], "action": "kept", "branch": "l1-keep"})
        else:
            # --- 普通规则文件分支 ---
            if intents.no_interrupt:
                merged = merge_markdown(template_text, _safe_read(target))
                if merged is None:
                    # NC-08 回退：标准结构 + `\n\n## 原项目补充\n\n` + 原文（备份已由屏障完成）。
                    original = _safe_read(target) or ""
                    fallback = template_text.rstrip("\n") + "\n\n## 原项目补充\n\n" + original
                    atomic_write(target, fallback)
                    actions_log.append({"path": asset["path"], "action": "merged-fallback", "branch": "markdown-unparseable"})
                else:
                    atomic_write(target, merged)
                    actions_log.append({"path": asset["path"], "action": "merged", "branch": "markdown-merge"})
            else:
                if decision == DECISION_REPLACE:
                    atomic_write(target, template_text)
                    actions_log.append({"path": asset["path"], "action": "replaced", "branch": "rules-replace"})
                else:
                    actions_log.append({"path": asset["path"], "action": "kept", "branch": "rules-keep"})

    # 回写 actions 到报告 step。
    _record_step_actions(report, STEP_RULES_FILES, actions_log)


def _safe_read(path: Path) -> Optional[str]:
    """安全读取文件文本，失败返回 None。"""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _record_step_actions(report: dict, step_name: str, actions: list) -> None:
    """将执行动作回写到报告对应 step 的 actions 字段。"""
    for step in report.get("steps", []):
        if step.get("name") == step_name:
            existing = step.get("actions") or []
            existing.extend(actions)
            step["actions"] = existing
            return
    # 未找到对应 step（异常路径）→ 追加一个最小 step 记录。
    report.setdefault("steps", []).append({
        "name": step_name, "status": "ok", "action": None,
        "reason": "", "elapsed_ms": 0, "assets": [], "conflicts": [],
        "actions": list(actions),
    })



def step_s4_entry_files(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S4 执行（Task 6 实现）：双入口统一预检 + 单次写入。

    流程（简报 Step 4）：
      1. 各入口在内存合成最终文本（入口不存在 → BASE 文本为基线）；
      2. L0 插入位置 = 首个 `## 强制规则` 前；无则文件说明后；
      3. drift/upgrade/broken → 替换/修复 L0 区块为规范源，区块外内容逐字保留；
      4. 缺失摘要行追加；技术栈/包管理器/覆盖率 80% 块追加；规则 2 按项目类型选文本；
      5. 摘要编号冲突 → 保留原文追加缺失并在 detail 说明；
      6. 各一次 atomic_write（全局备份屏障已由 run_apply 完成）。
    """
    kernel_source = _load_kernel_source()
    if not kernel_source:
        return
    project_type = plan.get("project_type", "non-coding")
    tech_stack = report.get("tech_stack") or {}
    s4_step = (plan.get("steps", {}) or {}).get(STEP_ENTRY_FILES, {})
    assets = s4_step.get("assets", []) or []
    decisions_map = plan.get("decisions_map", {}) or {}
    actions_log: list = []

    for asset in assets:
        entry_name = asset["path"]
        entry_path = root / entry_name
        state = asset.get("conflict")  # None=skip/create, 或 insert/drift/upgrade/broken
        action = asset.get("action")
        base_text = BASE_CLAUDE_MD if entry_name == "CLAUDE.md" else BASE_AGENTS_MD

        if action == "skip" or (state is None and action != "create"):
            # 已是 skip 状态（L0 与规范源一致）→ 幂等：不修改入口文件。
            actions_log.append({"path": entry_name, "action": "skipped", "branch": "skip"})
            continue

        # 入口不存在 → 以 BASE 为基线，状态视为 create。
        if action == "create" and not entry_path.exists():
            composed = _compose_entry(base_text, kernel_source, state="create",
                                      project_type=project_type, tech_stack=tech_stack,
                                      entry_name=entry_name)
            ensure_parent(entry_path)
            atomic_write(entry_path, composed)
            actions_log.append({"path": entry_name, "action": "created", "branch": "base-created"})
            continue

        # 入口存在且状态为 insert/drift/upgrade/broken。
        conflict_id = f"s4:{entry_name}"
        decision = decisions_map.get(conflict_id)
        existing = _safe_read(entry_path) or ""
        if intents.no_interrupt:
            composed = _compose_entry(existing, kernel_source, state=state or "insert",
                                      project_type=project_type, tech_stack=tech_stack,
                                      entry_name=entry_name)
            atomic_write(entry_path, composed)
            actions_log.append({"path": entry_name, "action": "updated", "branch": f"no-interrupt-{state}"})
        else:
            if decision == DECISION_REPLACE:
                composed = _compose_entry(existing, kernel_source, state=state or "insert",
                                          project_type=project_type, tech_stack=tech_stack,
                                          entry_name=entry_name)
                atomic_write(entry_path, composed)
                actions_log.append({"path": entry_name, "action": "updated", "branch": f"replace-{state}"})
            else:
                actions_log.append({"path": entry_name, "action": "kept", "branch": f"keep-{state}"})

    _record_step_actions(report, STEP_ENTRY_FILES, actions_log)


def _compose_entry(existing: str, l0_source: str, *, state: str,
                   project_type: str, tech_stack: dict, entry_name: str) -> str:
    """合成入口文件最终文本。

    按状态区分行为（保证幂等与区块外保留）：
      * skip：完全不动（幂等）；
      * create（入口不存在，基线=BASE 文本）：插入 L0 + 补摘要行 + 规则 2 选文本
        + 追加技术栈块（若有检测数据）；
      * insert（入口存在但无 L0 标记）：插入 L0 + 补摘要行 + 规则 2 选文本
        （不追加技术栈块——入口已存在，尊重用户内容）；
      * drift/upgrade/broken：仅修复 L0 区块，不动区块外内容。
    """
    text = existing
    # 状态决定是否做“完整初始化”（摘要行 + 技术栈块）。
    full_init = state in ("create", "insert")

    # --- 步骤 1：规范化 L0 ---
    if state == "skip":
        pass
    elif state == "insert":
        text = _insert_l0_block(text, l0_source)
    elif state in ("drift", "upgrade"):
        # 标记对完整：移除整个旧区块，保留区块外内容，重新插入规范 L0。
        text = _remove_l0_block_pair(text)
        text = _insert_l0_block(text, l0_source)
    elif state == "create":
        # BASE 基线本身无 L0 → 插入。
        text = _insert_l0_block(text, l0_source)
    else:
        # broken：只移除孤立标记行，保留所有非标记内容。
        text = _strip_l0_marker_lines_only(text)
        text = _insert_l0_block(text, l0_source)

    if not full_init:
        # drift/upgrade/broken：仅修 L0，不动区块外。规范化末尾换行。
        return text.rstrip("\n") + "\n"

    # --- 步骤 2：规则 2 摘要行按项目类型选择 ---
    rule2_text = (
        RULE2_TEXT_CODING if project_type == "coding" else RULE2_TEXT_NONCODING
    )
    for variant in (RULE2_TEXT_CODING, RULE2_TEXT_NONCODING):
        if variant in text and variant != rule2_text:
            text = text.replace(variant, rule2_text, 1)

    # --- 步骤 3：缺失摘要行追加（仅 create/insert）---
    text = _ensure_summary_lines(text, entry_name)

    # --- 步骤 4：技术栈块追加（仅 create；insert 不追加以尊重用户内容）---
    if state == "create":
        text = _ensure_techstack_block(text, tech_stack)

    return text


def _insert_l0_block(text: str, l0_source: str) -> str:
    """在首个 `## 强制规则` 前插入 L0 区块；无则在文件说明后插入。

    L0 区块前后各保留一个空行分隔。幂等：若 L0_BEGIN 已存在则不重复插入。
    """
    if L0_BEGIN in text:
        return text
    lines = text.splitlines()
    insert_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == "## 强制规则":
            insert_idx = idx
            break
    if insert_idx is None:
        # 无 ## 强制规则 → 在文件说明后插入（首个空行分隔处之后）。
        # 文件说明 = 首个非空段落后。简单策略：在文件末尾追加（保证 BASE 已含说明）。
        # 但更稳妥：找首个 H1 后的简介段落结束位置。这里采用“首个空行后”启发式。
        insert_idx = len(lines)
        # 回溯跳过末尾空行。
        while insert_idx > 0 and lines[insert_idx - 1].strip() == "":
            insert_idx -= 1
    block_lines = l0_source.splitlines()
    # 组装：[原有前部] + 空行 + L0 区块 + 空行 + [原有后部]
    head = lines[:insert_idx]
    tail = lines[insert_idx:]
    parts = []
    if head:
        parts.extend(head)
        if head[-1].strip() != "":
            parts.append("")
    parts.extend(block_lines)
    parts.append("")
    parts.extend(tail)
    return "\n".join(parts)


def _remove_l0_block_pair(text: str) -> str:
    """移除完整的 L0 受管区块对（begin...end 含内部全部内容），保留区块外内容。

    用于 drift/upgrade 状态：标记对完整时，整个旧区块（含漂移内容）移除。
    支持任意版本（v1/v0 等）的成对标记。若仅有单侧标记则保留不动（由 broken 路径处理）。
    """
    # 收集所有版本的 begin/end 标记对，逐个移除完整的 begin...end 区间。
    versions = ["v1", "v0"]
    result = text
    for ver in versions:
        begin_marker = (
            "<!-- cadence-managed:openspec-superpowers-routing:" + ver + ":start -->"
        )
        end_marker = (
            "<!-- cadence-managed:openspec-superpowers-routing:" + ver + ":end -->"
        )
        while True:
            b_idx = result.find(begin_marker)
            if b_idx == -1:
                break
            e_idx = result.find(end_marker, b_idx)
            if e_idx == -1:
                # 单侧 begin 无配对 end → 不处理（broken 路径负责）。
                break
            e_end = e_idx + len(end_marker)
            # 移除区间，同时吸收周围多余空行（避免出现连续多个空行）。
            before = result[:b_idx]
            after = result[e_end:]
            # 合并：去掉 before 尾部与 after 头部的空行，中间保留至多一个空行分隔。
            before = before.rstrip("\n")
            after = after.lstrip("\n")
            if before and after:
                result = before + "\n\n" + after
            elif before:
                result = before + "\n"
            elif after:
                result = after
            else:
                result = ""
    return result


def _strip_l0_marker_lines_only(text: str) -> str:
    """仅移除独立的 L0 标记行（整行匹配），保留所有其他内容（含区块内正文）。

    用于 broken 状态：单侧/乱序标记无法判定区块归属，只移除标记行本身。
    """
    lines = text.splitlines()
    kept: list = []
    for line in lines:
        stripped = line.strip()
        if (
            stripped.startswith("<!-- cadence-managed:openspec-superpowers-routing:")
            and stripped.endswith("-->")
        ):
            continue
        kept.append(line)
    return "\n".join(kept)


def _ensure_summary_lines(text: str, entry_name: str) -> str:
    """确保 ## 强制规则 章节含所有标准摘要行；缺失则追加到章节末尾。

    摘要编号冲突 → 保留原文，追加缺失行（不重新编号）。
    """
    required = [
        "- **必须使用中文回答** → 详见 `.claude/rules/language.md`",
        "- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules` 目录下** → 详见 `.claude/rules/document-storage.md`",
        "- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`",
    ]
    # CLAUDE.md 与 AGENTS.md 的 MCP 摘要行文本略有不同，按入口选择。
    if entry_name == "CLAUDE.md":
        required.append("- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`")
    else:
        required.append("- **各 MCP 工具及相关自动化工具的使用必须遵循项目规范** → 详见 `.claude/rules/mcp-servers.md`")
    required.append("- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`")

    lines = text.splitlines()
    # 定位 ## 强制规则 章节范围（到下一个同级或更高级标题）。
    rules_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == "## 强制规则":
            rules_idx = idx
            break
    if rules_idx is None:
        # 无 ## 强制规则 章节 → 不追加（BASE 已含；入口缺该章节属异常，不动）。
        return text
    # 找章节末尾（下一个 ## 或 # 标题，或文件末尾）。
    end_idx = len(lines)
    for idx in range(rules_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("## ") or stripped.startswith("# "):
            end_idx = idx
            break
    # 收集章节内现有文本，判定缺失行。
    section_text = "\n".join(lines[rules_idx:end_idx])
    missing = [line for line in required if line not in section_text]
    if not missing:
        return text
    # 在章节末尾追加缺失行（保留原文，不重新编号）。
    # 插入位置：end_idx 前（章节末尾）。
    insert_block = list(missing)
    new_lines = lines[:end_idx] + insert_block + lines[end_idx:]
    return "\n".join(new_lines)


def _ensure_techstack_block(text: str, tech_stack: dict) -> str:
    """追加技术栈/包管理器/覆盖率块（幂等：已含则不动）。

    块格式（追加到文件末尾的 ## 项目信息 或直接末尾）。
    """
    if not tech_stack:
        return text
    # 幂等检查：若已含包管理器/覆盖率标记，视为已写入。
    if "覆盖率阈值**：80%" in text or "### 项目技术栈" in text:
        return text
    language = tech_stack.get("language", "未检测到")
    pkg = tech_stack.get("pkg_manager", "未检测到")
    test_cmd = tech_stack.get("test", "未检测到")
    lint_cmd = tech_stack.get("lint", "未检测到")
    fmt_cmd = tech_stack.get("format", "未检测到")
    block = (
        "\n## 项目配置\n"
        "\n> 以下内容由初始化脚本根据项目环境自动检测生成，非通用规则。"
        "\n\n### 项目技术栈"
        f"\n- **语言**：{language}"
        f"\n- **包管理器**：{pkg}"
        f"\n- **测试命令**：{test_cmd}"
        f"\n- **检查命令**：{lint_cmd}"
        f"\n- **格式化命令**：{fmt_cmd}"
        "\n- **覆盖率阈值**：80%"
        "\n"
    )
    return text.rstrip("\n") + "\n" + block



def step_s5_scaffold(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S5 执行（Task 7 实现）。骨架：pass。"""
    _ = (root, intents, plan, report)


def step_s6_gitignore(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S6 执行（Task 7 实现）。骨架：pass。"""
    _ = (root, intents, plan, report)


def step_s7_openspec_config(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S7 执行（Task 8 实现）。骨架：pass。"""
    _ = (root, intents, plan, report)


def step_s8_codegraph(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S8 执行（Task 9 实现）。骨架：pass，但记录独立 elapsed_ms。"""
    _ = (root, intents, plan, report)


# 步骤名 → 执行函数映射
STEP_FUNCS = {
    STEP_DETECT: step_s1_detect,
    STEP_TEMPLATES: step_s2_locate_templates,
    STEP_RULES_FILES: step_s3_rules_files,
    STEP_ENTRY_FILES: step_s4_entry_files,
    STEP_SCAFFOLD: step_s5_scaffold,
    STEP_GITIGNORE: step_s6_gitignore,
    STEP_OPENSPEC_CONFIG: step_s7_openspec_config,
    STEP_CODEGRAPH: step_s8_codegraph,
}


# ---------------------------------------------------------------------------
# 主流程：dry-run / apply
# ---------------------------------------------------------------------------


def run_dry_run(root: Path, intents: Intents, report: dict) -> int:
    """dry-run：compute_plan + 写报告，零写入。"""
    plan = compute_plan(root, intents)
    _sync_plan_to_report(plan, report, intents)
    report["overall"] = "ok"
    return 0


def run_apply(root: Path, intents: Intents, report: dict) -> int:
    """apply：compute_plan → decisions 校验 → 全局备份屏障 → S1-S8 执行。

    执行顺序冻结（简报 Step 2）：
      1. compute_plan；
      2. 普通模式且 plan 有冲突 → load_decisions + validate_decisions，
         违规 → failed 报告 + 退出 1 + 零写入；
      3. 全局备份屏障：汇总 plan 全部 backup_needs 逐一 backup_file，
         任一失败 → 终止零发布（已建备份列入 report.backups）；
      4. 屏障通过后按 S1-S8 执行发布；
      5. S7 完成时计算 budget_seconds_excluding_codegraph = time.monotonic() - T0；
      6. 异常兜底 → overall=crashed + 写报告 + 退出 1。
    """
    # 1. compute_plan
    plan = compute_plan(root, intents)
    _sync_plan_to_report(plan, report, intents)

    # 2. decisions 校验（仅普通模式且 plan 有冲突）
    plan_conflicts = plan.get("conflicts", []) or []
    if not intents.no_interrupt and plan_conflicts:
        if intents.decisions is None:
            violations = [f"冲突缺少决策：{c['conflict_id']}" for c in plan_conflicts]
        else:
            validate_external_path(intents.decisions, root)
            decisions = load_decisions(intents.decisions)
            violations = validate_decisions(plan, decisions)
        if violations:
            report["overall"] = "fail"
            report["failure"] = {
                "file": str(intents.decisions) if intents.decisions else None,
                "reason": "decisions 校验失败：" + "; ".join(violations),
                "recovery": "提供覆盖全部冲突的合法 --decisions 文件，或使用 --no-interrupt",
            }
            report["conflicts"] = [
                {
                    "conflict_id": c.get("conflict_id"),
                    "asset": c.get("asset"),
                    "state": c.get("state"),
                    "question": c.get("question"),
                    "recommendation": c.get("recommendation"),
                }
                for c in plan_conflicts
            ]
            return 1
        # 校验通过：构建 conflict_id -> decision 映射存入 plan，供 step 读取。
        decisions_map: dict = {}
        if intents.decisions is not None:
            for entry in decisions:
                cid = entry.get("conflict_id") if isinstance(entry, dict) else None
                decision = entry.get("decision") if isinstance(entry, dict) else None
                if cid is not None:
                    decisions_map[cid] = decision
        plan["decisions_map"] = decisions_map
    else:
        plan["decisions_map"] = {}

    # 3. 全局备份屏障：汇总 plan 全部 backup_needs 逐一 backup_file
    backup_needs = plan.get("backup_needs", []) or []
    backups_done: list = []
    for target in backup_needs:
        try:
            backup_path = backup_file(Path(target))
            backups_done.append({"file": str(target), "backup": str(backup_path)})
            report["backups"] = list(backups_done)
        except BackupError as exc:
            # 任一失败 → 终止零发布；已建备份列入 report.backups
            report["backups"] = list(backups_done)
            report["overall"] = "fail"
            report["failure"] = {
                "file": str(target),
                "reason": f"备份屏障失败：{exc}",
                "recovery": "检查目标目录写权限后重试",
            }
            return 1

    # 4. 屏障通过后按 S1-S8 执行发布
    try:
        for step_name in STEP_ORDER:
            step_func = STEP_FUNCS[step_name]
            step_func(root, intents, plan, report)
            # S7 完成时计算 budget_seconds_excluding_codegraph
            if step_name == STEP_OPENSPEC_CONFIG:
                report["budget_seconds_excluding_codegraph"] = time.monotonic() - T0
        # 若 S7 未执行到（异常路径），兜底在最后计算
        if report.get("budget_seconds_excluding_codegraph") is None:
            report["budget_seconds_excluding_codegraph"] = time.monotonic() - T0
    except NotImplementedError:
        # S1-S8 桩未实现：标记 degraded 但不 crash（骨架阶段允许）
        report["overall"] = "degraded"
        return 0
    except Exception as exc:  # noqa: BLE001 — 异常兜底（简报 Step 2.6）
        report["overall"] = "crashed"
        report["failure"] = {
            "file": None,
            "reason": f"执行异常：{exc}",
            "recovery": "检查日志后重试",
        }
        return 1

    if report["overall"] == "ok":
        report["overall"] = "ok"
    return 0


def _sync_plan_to_report(plan: dict, report: dict, intents: Intents) -> None:
    """将 compute_plan 的探测结果同步到报告 steps/conflicts/project_type。"""
    report["project_type"] = plan.get("project_type", "non-coding")
    steps_in_plan = plan.get("steps", {}) or {}
    report_steps: list = []
    for step_name in STEP_ORDER:
        step_data = steps_in_plan.get(step_name, {})
        if not step_data:
            step_data = _step_skeleton(step_name)
        report_steps.append({
            "name": step_name,
            "status": step_data.get("status", "skip"),
            "action": step_data.get("action"),
            "reason": step_data.get("note", ""),
            "elapsed_ms": step_data.get("elapsed_ms", 0),
            "assets": step_data.get("assets", []),
            "conflicts": step_data.get("conflicts", []),
        })
    report["steps"] = report_steps
    report["conflicts"] = [
        {
            "conflict_id": c.get("conflict_id"),
            "asset": c.get("asset"),
            "state": c.get("state"),
            "question": c.get("question"),
            "recommendation": c.get("recommendation"),
        }
        for c in (plan.get("conflicts", []) or [])
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rule-config",
        description="受管生命周期配置（dry-run / apply 两阶段）",
    )
    parser.add_argument(
        "mode",
        choices=("dry-run", "apply"),
        help="dry-run 只探测写报告零写入；apply 执行发布",
    )
    parser.add_argument("--project-root", required=True, help="目标项目根目录")
    parser.add_argument("--report", required=True, help="报告 JSON 输出路径")
    parser.add_argument(
        "--no-interrupt",
        action="store_true",
        help="无中断模式：冲突按权威规则自动决策，不要求 --decisions",
    )
    parser.add_argument(
        "--project-type",
        choices=("coding", "non-coding"),
        default=None,
        help="显式覆盖检测的项目类型",
    )
    parser.add_argument(
        "--ignore-cadence",
        action="store_true",
        help="将 cadence/ 加入 .gitignore",
    )
    parser.add_argument(
        "--enable-playwright",
        action="store_true",
        help="创建 .claude/rules/playwright.md",
    )
    parser.add_argument(
        "--enable-codegraph",
        action="store_true",
        help="非 Coding 项目也执行 S8 CodeGraph 配置",
    )
    parser.add_argument(
        "--decisions",
        default=None,
        help="决策 JSON 文件（普通模式有冲突时必需）",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    """CLI 入口。退出码：0=success/degraded，1=failed，2=usage，77=missing-yaml。"""
    global T0
    T0 = time.monotonic()  # 入口第一行：budget 基准

    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse 解析失败 → 退出码 2（usage）
        code = exc.code if isinstance(exc.code, int) else 2
        return code if code != 0 else 2

    # 构造 intents
    root = Path(args.project_root).resolve()
    report_path = Path(args.report).resolve()
    decisions_path = Path(args.decisions).resolve() if args.decisions else None

    # --report 必须位于项目根之外（Plan L22 全局约束：脚本拒绝根内路径）。
    # 若 report 路径在项目根内 → stderr 输出错误 + exit 2。
    # 注意：不尝试写报告文件，因为报告路径本身非法。
    try:
        validate_external_path(report_path, root)
    except UsageError as exc:
        sys.stderr.write(f"rule-config: {exc}\n")
        return 2

    # decisions 必须位于项目根之外（外部输入；根内 → UsageError，退出码 2）
    if decisions_path is not None:
        try:
            validate_external_path(decisions_path, root)
        except UsageError as exc:
            report = build_report("normal" if not args.no_interrupt else "no-interrupt", root)
            report["overall"] = "fail"
            report["failure"] = {
                "file": str(decisions_path),
                "reason": str(exc),
                "recovery": "将 decisions 文件放在项目根目录之外（外部输入）",
            }
            write_report(report_path, report)
            return 2

    intents = Intents(
        no_interrupt=args.no_interrupt,
        project_type=args.project_type,
        ignore_cadence=args.ignore_cadence,
        enable_playwright=args.enable_playwright,
        enable_codegraph=args.enable_codegraph,
        decisions=decisions_path,
    )

    mode = "no-interrupt" if args.no_interrupt else "normal"
    report = build_report(mode, root)

    try:
        if args.mode == "dry-run":
            exit_code = run_dry_run(root, intents, report)
        else:
            exit_code = run_apply(root, intents, report)
    except Exception as exc:  # noqa: BLE001 — 顶层异常兜底
        report["overall"] = "crashed"
        report["failure"] = {
            "file": None,
            "reason": f"未捕获异常：{exc}",
            "recovery": "检查日志后重试",
        }
        exit_code = 1

    # 始终写出报告
    try:
        write_report(report_path, report)
    except OSError:
        # 报告写失败不影响已确定的退出码语义，但记录到 stderr
        sys.stderr.write(f"rule-config: 无法写出报告到 {report_path}\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
