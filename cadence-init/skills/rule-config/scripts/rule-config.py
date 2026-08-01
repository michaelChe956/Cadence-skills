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
import subprocess
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

# S3 普通规则文件清单（5 个，不含 L1_RULE_FILENAME、L0 kernel、
# code-usage 双来源模板与可选 Playwright）。
ORDINARY_RULE_FILES = (
    "language.md",
    "document-storage.md",
    "markdown-format.md",
    "mcp-servers.md",
    "code-reading.md",
)
# code-usage 按最终项目类型单选规范源，但项目落地名始终固定为 code-usage.md。
CODE_USAGE_SOURCE_MAP = {
    "coding": "code-usage-coding.md",
    "non-coding": "code-usage-noncoding.md",
}
CODE_USAGE_TARGET = "code-usage.md"
CODE_USAGE_LEGACY_FILES = ("code-usage-coding.md", "code-usage-noncoding.md")
# Playwright 规则文件（显式启用或目标已存在时处理）。
PLAYWRIGHT_RULE_FILE = "playwright.md"

# OP-01：可选规则完整性检查使用的 CodeGraph 规则文件。
CODEGRAPH_RULE_FILE = "code-reading.md"

# NC-03 项目补充标记：合并协议保留字。注入与项目独有行过滤共用此常量；
# 重跑时过滤必须排除标记行自身，保证 merge(t, merge(t, x)) == merge(t, x)（重跑幂等）。
PROJECT_SUPPLEMENT_MARKER = "**项目补充**"

# S5 目录结构创建（SKILL.md 第 5 步）：cadence/ 下 17 个子目录（含
# project-rules/examples 与 cache）。逐字对齐 SKILL.md mkdir 块展开后的目录名。
# project-rules 下含 examples 子目录，用 "project-rules/examples" 表示。
CADENCE_DIRS = (
    "prds",
    "analysis",
    "analysis-docs",
    "docs",
    "designs",
    "designs-reviews",
    "plans",
    "readmes",
    "modaos",
    "models",
    "architecture",
    "notes",
    "logs",
    "reports",
    "project-rules",
    "project-rules/examples",
    "cache",
)

# S6 历史产物迁移检测清单（SKILL.md 第 6 步检测块）：16 个精确目录名。
# 这些是 .claude/ 下的旧产物目录，普通模式下按 HM 表迁移到 cadence/。
# 注意：与 CADENCE_DIRS 的差异在于 project-rules/examples 拆出后历史清单为 16 个
# （历史清单不含 project-rules/examples 子目录，project-rules 整目录作为一项）。
HISTORY_DIRS = (
    "prds",
    "analysis",
    "analysis-docs",
    "docs",
    "designs",
    "designs-reviews",
    "plans",
    "readmes",
    "modaos",
    "models",
    "architecture",
    "notes",
    "logs",
    "reports",
    "project-rules",
    "cache",
)

# S6 历史迁移禁止目录（SKILL.md 第 6 步「禁止迁移」清单）：即便存在也不迁移。
HISTORY_FORBIDDEN_DIRS = ("rules", "commands", "skills")

# .gitignore 追加行与注释（S7/S9）。
GITIGNORE_CADENCE_LINE = "cadence/"
GITIGNORE_CADENCE_COMMENT = "# Cadence 产物目录"
GITIGNORE_CODEGRAPH_LINE = ".codegraph/"
GITIGNORE_CODEGRAPH_COMMENT = "# CodeGraph 本地索引"

# S8 CodeGraph：.codex/config.toml 追加的 MCP 服务区块（逐字常量）。
# 简报明文：CODEX_MCP_BLOCK toml 文本 =
#   [mcp_servers.codegraph]\ncommand = "codegraph"\nargs = ["serve", "--mcp"]
# 用三引号逐行书写以保持可读；末尾含一个换行，确保追加到既有 toml 时与上文分隔。
CODEX_MCP_BLOCK = (
    '[mcp_servers.codegraph]\n'
    'command = "codegraph"\n'
    'args = ["serve", "--mcp"]\n'
)

# S8 CodeGraph：.mcp.json（Claude Code MCP 配置）兜底合并写入的 codegraph 条目。
# 与 references 对齐：command="codegraph"、args=["serve","--mcp"]。
# has_codegraph_mcp_mcpjson 据此键存在性判定配置是否齐全。
MCPJSON_CODEGRAPH_ENTRY = {
    "command": "codegraph",
    "args": ["serve", "--mcp"],
}


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

# 规则 6（项目个性化规则）摘要多行块：CLAUDE.md 与 AGENTS.md 文本略有不同，按入口选择。
# _ensure_summary_lines 按各入口块的首行 marker 判断规则 6 是否已存在。
RULE6_BLOCK_CLAUDE = (
    "### 6. 项目个性化规则（强制规则）\n"
    "- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**\n"
    "- 禁止在 `rules/` 目录中添加用户自定义规则\n"
    "- 禁止直接修改 `rules/` 目录下的框架内置规则文件\n"
    "- 详见 `cadence/project-rules/README.md`"
)
RULE6_BLOCK_AGENTS = (
    "### 6. 项目个性化规则\n"
    "- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**\n"
    "- 禁止在 `.claude/rules/` 目录中添加用户自定义规则\n"
    "- 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件\n"
    "- 详见 `cadence/project-rules/README.md`"
)

# 决策枚举：规则文件/L0/L1 冲突 replace|keep；OpenSpec rules.apply 冲突 remove_apply|keep。
DECISION_REPLACE = "replace"
DECISION_KEEP = "keep"
DECISION_REMOVE_APPLY = "remove_apply"

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


# I-4：冻结 schema 仅允许 overall ∈ {ok, degraded, fail}；执行异常统一落 fail。
# failure.file 必须含实际失败文件路径——从异常上下文尽力提取：
# 优先异常属性（file/filename/path），其次异常消息中的已知受管文件路径，
# 兜底为失败步骤标识（不得为 None）。
_FAILURE_PATH_RE = re.compile(
    r"(openspec/config\.yaml|\.claude/rules/[\w.-]+\.md|CLAUDE\.md|AGENTS\.md|"
    r"\.mcp\.json|\.codex/config\.toml|\.gitignore)"
)


def _extract_failure_file(exc: BaseException, step_name: Optional[str]) -> str:
    """从异常上下文提取实际失败文件路径（I-4：failure.file 不得为 None）。"""
    for attr in ("file", "filename", "path"):
        val = getattr(exc, attr, None)
        if isinstance(val, (str, Path)) and str(val):
            return str(val)
    match = _FAILURE_PATH_RE.search(str(exc))
    if match:
        return match.group(1)
    # 兜底：至少给出失败步骤标识（如 s2_locate_templates），不为 None。
    return step_name or "<unknown>"


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


def _ensure_legacy_gitignore(legacy_dir: Path) -> None:
    """确保 cadence/legacy/.gitignore 为 * + !.gitignore；缺失/损坏则修复。"""
    gi = legacy_dir / ".gitignore"
    expected = "*\n!.gitignore\n"
    try:
        current = gi.read_text(encoding="utf-8") if gi.exists() else None
    except OSError as exc:
        raise BackupError(f"无法检查归档忽略文件：{gi}（{exc}）") from exc
    if current == expected:
        return
    try:
        legacy_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(gi, expected)
    except OSError as exc:
        raise BackupError(f"无法写入归档忽略文件：{gi}（{exc}）") from exc


def backup_file(path: Path, root: Path) -> Path:
    """复制原文件到 cadence/legacy/<时间戳[-N]>/<相对 root 路径>。

    原位文件不动；归档复制失败抛 BackupError。同秒冲突在时间戳目录后追加 -2/-3。
    每次归档前验证/修复 .gitignore。
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


def ensure_gitignore_line(root: Path, line: str, comment: str) -> str:
    """行级幂等追加一行到 root/.gitignore（S7/S9）。

    语义（与 SKILL.md `grep -qxF '...' || printf ...` 等价）：
      * 若 .gitignore 已含**完整匹配**的 line 行（grep -qxF 语义：整行精确相等），
        则不重复追加，返回 'skipped'；
      * 否则在文件末尾追加 `\n<comment>\n<line>\n`，返回 'added'。
      * .gitignore 不存在时创建（含父目录），写入 `<comment>\n<line>\n`，返回 'added'。

    幂等：重复调用同一 (line) 不会产生重复行；comment 仅在首次追加时写入。
    "line" 为空时直接返回 'skipped'（防御）。
    """
    if not line:
        return "skipped"
    gi = root / ".gitignore"
    # 行级精确匹配判断（等价 grep -qxF）：按整行精确相等比较（仅规范化行尾 CR）。
    if gi.is_file():
        try:
            existing = gi.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            existing = ""
        for raw in existing.splitlines():
            if raw.rstrip("\r") == line:
                return "skipped"
        # 追加：comment + line
        ensure_parent(gi)
        atomic_write(gi, existing.rstrip("\n") + "\n\n" + comment + "\n" + line + "\n")
        return "added"
    # 不存在 → 创建
    ensure_parent(gi)
    atomic_write(gi, comment + "\n" + line + "\n")
    return "added"


# ---------------------------------------------------------------------------
# S8 CodeGraph：MCP 配置探测纯函数（Task 9）
# ---------------------------------------------------------------------------
# has_codegraph_mcp_mcpjson / has_codegraph_mcp_codex 判定双 MCP 配置是否齐全。
# install 后再核验、仅补仍缺失方时调用。语义：
#   * .mcp.json：解析 JSON，顶层含 mcpServers.codegraph 键即视为齐全（不校 args 值，
#     因为 codegraph install 写入的 args=["mcp"] 与脚本兜底 args=["serve","--mcp"]
#     均合法——只要 codegraph 条目存在即代表 MCP 已注册）。
#   * .codex/config.toml：文本含 [mcp_servers.codegraph] 区块头即视为齐全
#    （toml 无标准库；按区块头存在性判定，与 install 写入格式兼容）。


def has_codegraph_mcp_mcpjson(root: Path) -> bool:
    """判定 root/.mcp.json 是否已注册 codegraph MCP 条目。

    解析 JSON；顶层 dict 含 mcpServers.codegraph 即 True。文件缺失/不可解析/
    结构非 dict/无该键均返回 False（配置缺失，需补写）。
    """
    mcp_path = root / ".mcp.json"
    raw = _safe_read(mcp_path)
    if not raw:
        return False
    try:
        doc = json.loads(raw)
    except (ValueError, TypeError):
        return False
    if not isinstance(doc, dict):
        return False
    servers = doc.get("mcpServers")
    if not isinstance(servers, dict):
        return False
    return "codegraph" in servers


def has_codegraph_mcp_codex(root: Path) -> bool:
    """判定 root/.codex/config.toml 是否已注册 codegraph MCP 区块。

    按文本含 `[mcp_servers.codegraph]` 区块头判定（与 install 写入格式兼容）。
    文件缺失/不含该区块头均返回 False（配置缺失，需补写）。
    """
    toml_path = root / ".codex" / "config.toml"
    raw = _safe_read(toml_path)
    if not raw:
        return False
    return "[mcp_servers.codegraph]" in raw


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


def _has_substantial_preamble(text: str) -> bool:
    """首个 ATX 标题之前是否存在实质（非空白）内容行（I-1）。

    parse_sections 会舍弃首个标题之前的所有行；若这些行含实质内容，
    章节合并将静默丢失项目原文，调用方应走 NC-08 fallback。
    """
    for line in text.splitlines():
        if _HEADING_RE.match(line):
            return False
        if line.strip():
            return True
    return False


def merge_markdown(template: str, existing: Optional[str]) -> Optional[str]:
    """合并 Markdown（NC-01~08）。

    语义：
      * existing is None → 返回 template（NC-01）；
      * existing 不可解析（含不可打印控制字符） → 返回 None（NC-08，函数级终止信号）；
      * existing 有实质内容但无任何 ATX 标题，或首个标题前有实质前言
        （parse_sections 会舍弃这些行，章节合并将静默丢失项目原文）
        → 返回 None（I-1 修复：走 NC-08 fallback，标准结构 + 原内容附加到
        「原项目补充」，避免数据丢失）；
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

    # I-1 修复：existing 无标题但有实质内容，或首个标题前有实质前言 → None，
    # 由调用方走 NC-08 fallback（原内容附加到「原项目补充」），不得静默丢弃。
    if not old_sections:
        if existing.strip():
            return None
    elif _has_substantial_preamble(existing):
        return None

    # 以 key 收集项目章节；同名章节（同一 key）的内容全部保留，后续去重。
    # 重要（评审 Important 4）：项目侧多个同名章节不能只保留第一个，
    # 必须把所有同名章节的正文行合并进该 key 的项目补充。
    old_by_key: dict = {}
    for sec in old_sections:
        old_by_key.setdefault(sec.key, []).extend(sec.body_lines)

    merged: list = []
    used_keys: set = set()
    for tsec in tpl_sections:
        used_keys.add(tsec.key)
        body = list(tsec.body_lines)
        if tsec.key in old_by_key:
            project_body = old_by_key[tsec.key]
            # 项目独有行 = 项目章节中模板未出现的完整行。
            template_lines = set(_dedup_lines_preserve_order(body))
            project_only_raw = [
                line for line in project_body
                if line not in template_lines and line.strip()
                and line.strip() != PROJECT_SUPPLEMENT_MARKER
            ]
            # 重要（评审 Important 3）：项目补充部分对项目侧独有行也按完整行去重、保序
            # （NC-07），避免项目侧自身重复行在合并结果中出现两次。
            project_only = _dedup_lines_preserve_order(project_only_raw)
            if project_only:
                # NC-03：同名章节正文 = 模板正文 + \n\n**项目补充**\n + 项目去重行。
                body.append("")
                body.append("")
                body.append(PROJECT_SUPPLEMENT_MARKER)
                body.extend(project_only)
        merged.append(Section(
            level=tsec.level, key=tsec.key, title=tsec.title, body_lines=body,
        ))

    # 项目独有章节（模板无同名 key）按原序追加。
    # 重要（评审 Important 4 扩展）：项目侧多个同名独有章节合并为一个章节，
    # 正文按完整行去重保序（NC-07），不整个丢失也不重复。
    project_only_sections: dict = {}
    project_only_order: list = []
    for osec in old_sections:
        if osec.key in used_keys:
            continue
        if osec.key not in project_only_sections:
            project_only_sections[osec.key] = osec
            project_only_order.append(osec.key)
            # 首次出现时对其正文去重。
            project_only_sections[osec.key] = Section(
                level=osec.level, key=osec.key, title=osec.title,
                body_lines=_dedup_lines_preserve_order(osec.body_lines),
            )
        else:
            base = project_only_sections[osec.key]
            merged_body = _dedup_lines_preserve_order(
                base.body_lines + osec.body_lines
            )
            project_only_sections[osec.key] = Section(
                level=base.level, key=base.key, title=base.title,
                body_lines=merged_body,
            )
    for key in project_only_order:
        merged.append(project_only_sections[key])

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
        # 重要（评审 Important 5）：逐字比对区块内容，不 strip() 整个区块
        # （避免吞掉首部/内部空白差异）。仅对尾随换行做 rstrip，以容忍
        # 规范源文件末尾的换行符与入口切片之间的尾随换行差异（文件系统层面，
        # 非区块内容差异）。首部/内部任何字符差异均判 drift。
        return "skip" if block.rstrip("\n") == source.rstrip("\n") else "drift"

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


def _openspec_field_types(doc: Any, fields: list) -> dict:
    """收集 openspec config 结构冲突字段的实际类型名（报告用）。

    fields 为 precheck_openspec_structure 返回的字段路径列表（如
    ['rules.proposal', 'context']）；对每个路径取 doc 中对应值的类型名，
    便于报告「字段路径与实际类型」。根冲突（'<root>'）记录 doc 整体类型。
    """
    types: dict = {}
    if not isinstance(doc, dict):
        types["<root>"] = type(doc).__name__
        return types
    for f in fields:
        if f == "<root>":
            types[f] = type(doc).__name__
            continue
        parts = f.split(".")
        val: Any = doc
        try:
            for p in parts:
                if isinstance(val, dict):
                    val = val.get(p)
                else:
                    val = None
                    break
        except Exception:  # noqa: BLE001 — 报告用途，兜底
            val = None
        types[f] = type(val).__name__ if val is not None else "missing"
    return types


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
    default_keep_ids: set = set()
    for c in plan_conflicts:
        cid = c.get("conflict_id")
        if not cid:
            continue
        allowed = c.get("allowed_decisions")
        if not isinstance(allowed, list) or not allowed:
            allowed = ["replace", "keep"]
        allowed_by_id[cid] = allowed
        if c.get("default_keep"):
            default_keep_ids.add(cid)
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
    #   default_keep 冲突（如 openspec rules.apply、规则文件 drift）缺失时默认
    #   keep 保留，不记违规（与 SKILL.md 合并矩阵「无响应则保留并报告」一致）。
    #   codex 五轮：当前系统所有冲突均为 A 类（default_keep=True），普通模式
    #   无响应→保留并报告 status=0；缺失决策不 fail closed。
    missing = plan_ids - set(seen.keys())
    for cid in sorted(missing):
        if cid in default_keep_ids:
            continue
        violations.append(f"冲突缺少决策：{cid}")

    return violations


# ---------------------------------------------------------------------------
# compute_plan：只读探测，填充 steps/conflicts/backup_needs（S1-S8 骨架）
# ---------------------------------------------------------------------------


def _compute_final_project_type(detected_type: str, intents: Intents) -> str:
    """根据用户裁决的两模式规则计算最终 project_type（codex 五轮重构）。

    规则（删除 s1:project-type-conflict 后的唯⼀确定结果）：
      - no-interrupt：final = detected_type（CLI --project-type 完全忽略）
      - 普通模式：
          1) 检测 coding → coding（无论 CLI 写什么）
          2) 检测 non-coding + CLI coding → coding（CLI 仅能提升）
          3) 检测 non-coding + CLI 不写或 non-coding → non-coding

    等价实现：普通模式下 final = 'coding' if (detected=='coding'
    or intents.project_type=='coding') else 'non-coding'。
    """
    if detected_type == "coding":
        return "coding"
    # detected == 'non-coding'
    if intents.no_interrupt:
        return "non-coding"  # no-interrupt：CLI 完全忽略
    # 普通模式：CLI coding 可提升 non-coding → coding；其余保持 non-coding
    return "coding" if intents.project_type == "coding" else "non-coding"


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
      * S1 detect：自动检测项目类型（检测结果）+ 两模式规则计算最终 project_type
        （codex 五轮重构：no-interrupt 以检测为准、普通模式 CLI 仅提升；
        s1:project-type-conflict 冲突已删除）；
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
    # codex 五轮重构：detect 只返回检测结果；最终 project_type 由两模式规则计算
    # （no-interrupt 以检测为准、普通模式 CLI 仅提升）。s1:project-type-conflict
    # 冲突机制已删除——任意检测+CLI 组合都有唯⼀确定结果，不再产冲突。
    s1 = _step_skeleton(STEP_DETECT)
    t_s1 = time.monotonic()  # codex 终审 I4：S1-S7 真实计时（起点）
    detect_result = detect_project(root, intents)
    final_project_type = _compute_final_project_type(
        detect_result["project_type"], intents
    )
    plan["project_type"] = final_project_type
    plan["tech_stack"] = detect_result["tech_stack"]
    s1["status"] = "ok"
    s1["note"] = (
        f"project_type={final_project_type}; "
        f"detected_type={detect_result['project_type']}; "
        f"evidence={detect_result['evidence']}"
    )
    s1["assets"] = [{
        "path": "<project>",
        "action": "detect",
        "conflict": None,
        "backup_needed": False,
        "detected_type": detect_result["project_type"],
        "project_type": final_project_type,
        "evidence": detect_result["evidence"],
        "tech_stack": detect_result["tech_stack"],
    }]
    s1["elapsed_ms"] = int((time.monotonic() - t_s1) * 1000)  # codex 终审 I4：真实计时
    plan["steps"][STEP_DETECT] = s1

    # --- S2 locate templates：三级定位 ---
    s2 = _step_skeleton(STEP_TEMPLATES)
    t_s2 = time.monotonic()  # codex 终审 I4：S1-S7 真实计时（起点）
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
    s2["elapsed_ms"] = int((time.monotonic() - t_s2) * 1000)  # codex 终审 I4：真实计时
    plan["steps"][STEP_TEMPLATES] = s2

    # --- S3 rules files：探测普通规则 + code-usage 单选 + L1 + Playwright ---
    s3 = _step_skeleton(STEP_RULES_FILES)
    t_s3 = time.monotonic()  # codex 终审 I4：S1-S7 真实计时（起点）
    templates_info = plan.get("templates", {}) or {}
    rules_root_str = templates_info.get("rules_root")
    rules_root = Path(rules_root_str) if rules_root_str else None
    rules_dir = root / ".claude" / "rules"
    project_type = plan.get("project_type", "non-coding")
    code_usage_source = CODE_USAGE_SOURCE_MAP[project_type]
    # (项目落地名, 模板来源名, 是否 L1)；code-usage 双模板只能单选一个来源。
    s3_targets = [(fname, fname, False) for fname in ORDINARY_RULE_FILES]
    s3_targets.append((CODE_USAGE_TARGET, code_usage_source, False))
    # 已存在的 Playwright 即视为启用，进入与普通规则相同的 drift 分类。
    if intents.enable_playwright or (rules_dir / PLAYWRIGHT_RULE_FILE).exists():
        s3_targets.append((PLAYWRIGHT_RULE_FILE, PLAYWRIGHT_RULE_FILE, False))
    s3_targets.append((L1_RULE_FILENAME, L1_RULE_FILENAME, True))
    for target_name, src_name, is_l1 in s3_targets:
        target = rules_dir / target_name
        rel = (
            str(target.relative_to(root))
            if target.exists()
            else f".claude/rules/{target_name}"
        )
        # 模板源文本（rules_root 不可用时退化为空串，该文件跳过处理）。
        if rules_root is not None:
            try:
                template_text = (rules_root / src_name).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                template_text = ""
        else:
            template_text = ""
        if not target.exists():
            # 不存在 → created（无冲突；模板缺失时退化为 skip，不创建空文件）。
            action = "create" if template_text else "skip"
            s3["assets"].append({
                "path": rel,
                "template_source": src_name,
                "action": action,
                "conflict": None,
                "backup_needed": False,
                "is_l1": is_l1,
            })
            continue
        # 文件存在 → 分类。
        try:
            existing_text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            existing_text = ""
        if is_l1:
            state = classify_l1(target, template_text, KNOWN_L1_VERSIONS)
            # L1：skip → 无冲突；upgrade/replace → 冲突（allowed=['replace','keep']）。
            if state == "skip":
                s3["assets"].append({
                    "path": rel, "template_source": src_name,
                    "action": "skip", "conflict": None,
                    "backup_needed": False, "is_l1": True,
                })
            else:
                s3["assets"].append({
                    "path": rel, "template_source": src_name,
                    "action": "replace", "conflict": state,
                    "backup_needed": True, "is_l1": True,
                })
                conflict_id = f"s3:{rel}"
                # codex 三轮 C3（方案 X）：L1 drift 回归 A 类——recommendation=keep
                # 是脚本认可的安全默认（保留原状可恢复），普通模式无响应（Agent 写
                # keep 或决策缺失）时默认保留并报告 status=0，与实现「keep→不写盘」
                # 一致，不 fail closed。default_keep=True 使 validate_decisions 对该
                # 冲突缺失决策不记违规。codex 五轮：s1:project-type-conflict 已删除，
                # 当前系统所有冲突均为 A 类（default_keep 保留兜底），无 B 类触发。
                s3["conflicts"].append({
                    "conflict_id": conflict_id, "asset": rel, "state": state,
                    "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                    "question": f"L1 规则文件 {rel} 状态为 {state}",
                    # C-1 修复：推荐保守默认 keep（不覆盖），与 spec「普通模式
                    # 无响应 MUST NOT 覆盖」、§11.6 default_keep 语义一致。
                    "recommendation": DECISION_KEEP,
                    "default_keep": True,
                })
                plan["conflicts"].append({
                    "conflict_id": conflict_id, "asset": rel, "kind": "l1",
                    "state": state,
                    "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                    "question": f"L1 规则文件 {rel} 状态为 {state}",
                    "recommendation": DECISION_KEEP,
                    "default_keep": True,
                })
                _append_backup_need(plan, target)
        else:
            # 普通规则文件：一致 → skipped；冲突 → 冲突（allowed=['replace','keep']）。
            if existing_text == template_text:
                s3["assets"].append({
                    "path": rel, "template_source": src_name,
                    "action": "skip", "conflict": None,
                    "backup_needed": False, "is_l1": False,
                })
            else:
                s3["assets"].append({
                    "path": rel, "template_source": src_name,
                    "action": "replace", "conflict": "drift",
                    "backup_needed": True, "is_l1": False,
                })
                conflict_id = f"s3:{rel}"
                # codex 三轮 C3（方案 X）：普通规则文件 drift 同 L1/L0 回归 A 类——
                # recommendation=keep 为安全默认（保留用户内容可恢复），普通模式
                # 无响应时默认保留并报告 status=0，不 fail closed。
                s3_conflict = {
                    "conflict_id": conflict_id, "asset": rel, "state": "drift",
                    "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                    "question": f"规则文件 {rel} 与模板不一致",
                    "recommendation": DECISION_KEEP,
                    "default_keep": True,
                }
                top_conflict = {
                    "conflict_id": conflict_id, "asset": rel, "kind": "rules",
                    "state": "drift",
                    "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                    "question": f"规则文件 {rel} 与模板不一致",
                    "recommendation": DECISION_KEEP,
                    "default_keep": True,
                }
                if intents.no_interrupt:
                    # P1-1：no-interrupt 实际执行为框架模板权威全覆盖；显式标注
                    # 真实动作，避免安全默认 recommendation=keep 误导为“保留原文件不动”。
                    s3_conflict["no_interrupt_action"] = "authoritative-overwrite"
                    top_conflict["no_interrupt_action"] = "authoritative-overwrite"
                s3["conflicts"].append(s3_conflict)
                plan["conflicts"].append(top_conflict)
                _append_backup_need(plan, target)
    s3["status"] = "ok"
    s3["elapsed_ms"] = int((time.monotonic() - t_s3) * 1000)  # codex 终审 I4：真实计时
    plan["steps"][STEP_RULES_FILES] = s3

    # --- S4 entry files：探测 CLAUDE.md / AGENTS.md 漂移 ---
    s4 = _step_skeleton(STEP_ENTRY_FILES)
    t_s4 = time.monotonic()  # codex 终审 I4：S1-S7 真实计时（起点）
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
        # I-2 修复：insert/upgrade 为「两模式同动作」确定性动作
        # （merge-semantics L0-05：无标记→直接插入；L0-04：旧版标记成对→备份后
        # 自动升级），不产 decision 冲突；allowed_decisions 仅用于 drift/broken。
        elif state in ("insert", "upgrade"):
            s4["assets"].append({
                "path": entry_name,
                "action": state,  # "insert" 直接插入 / "upgrade" 屏障后备份升级
                "conflict": state,
                # L0-05 insert 不改原内容无需备份；L0-04 upgrade 纳入备份屏障。
                "backup_needed": state == "upgrade",
            })
            if state == "upgrade":
                _append_backup_need(plan, entry_path)
        else:
            # drift/broken → 需要决策的冲突（普通模式；C-1 修复：推荐保守 keep）。
            s4["assets"].append({
                "path": entry_name,
                "action": "replace",
                "conflict": state,
                "backup_needed": True,
            })
            plan["conflicts"].append({
                "conflict_id": conflict_id,
                "asset": entry_name,
                "state": state,
                "allowed_decisions": [DECISION_REPLACE, DECISION_KEEP],
                "question": f"入口文件 {entry_name} 的 L0 受管区块状态为 {state}",
                "recommendation": DECISION_KEEP,
                # codex 三轮 C3（方案 X）：L0 drift/broken 回归 A 类——recommendation=keep
                # 为安全默认（保留区块原状可恢复），普通模式无响应时默认保留并报告
                # status=0，不 fail closed。default_keep=True 使 validate_decisions 对该
                # 冲突缺失决策不记违规。
                "default_keep": True,
            })
            _append_backup_need(plan, entry_path)
    s4["status"] = "ok"
    s4["elapsed_ms"] = int((time.monotonic() - t_s4) * 1000)  # codex 终审 I4：真实计时
    plan["steps"][STEP_ENTRY_FILES] = s4

    # --- S5 scaffold：探测 cadence/ 目录与历史目录（Task 7） ---
    s5 = _step_skeleton(STEP_SCAFFOLD)
    t_s5 = time.monotonic()  # codex 终审 I4：S1-S7 真实计时（起点）
    s5["status"] = "ok"
    # 历史目录检测：扫描 .claude/ 下 HISTORY_DIRS（16 个精确目录）。
    claude_dir = root / ".claude"
    detected: list = []
    for d in HISTORY_DIRS:
        if (claude_dir / d).exists():
            detected.append(f".claude/{d}")
    plan["history_detected"] = detected
    s5["assets"].append({
        "path": "cadence/", "action": "create",
        "conflict": None, "backup_needed": False,
        "detail": f"mkdir {len(CADENCE_DIRS)} cadence dirs",
    })
    if detected:
        s5["assets"].append({
            "path": "<history>", "action": "detect",
            "conflict": None, "backup_needed": False,
            "history_detected": detected,
        })
    s5["elapsed_ms"] = int((time.monotonic() - t_s5) * 1000)  # codex 终审 I4：真实计时
    plan["steps"][STEP_SCAFFOLD] = s5

    # --- S6 gitignore：探测 .gitignore（Task 7） ---
    s6 = _step_skeleton(STEP_GITIGNORE)
    t_s6 = time.monotonic()  # codex 终审 I4：S1-S7 真实计时（起点）
    s6["status"] = "ok"
    gi = root / ".gitignore"
    s6["assets"].append({
        "path": ".gitignore", "action": "skip",
        "conflict": None, "backup_needed": False,
        "exists": gi.exists(),
    })
    s6["elapsed_ms"] = int((time.monotonic() - t_s6) * 1000)  # codex 终审 I4：真实计时
    plan["steps"][STEP_GITIGNORE] = s6

    # --- S7 openspec config：探测 openspec/config.yaml（Task 8） ---
    # 只读探测：存在则解析+结构预检+rules.apply 检测，产出 conflict 条目。
    #   * rules.apply 冲突：allowed_decisions=['remove_apply','keep']，default_keep=True
    #     （普通模式无 decisions 时默认 keep 保留，与 SKILL.md 合并矩阵「无响应则保留并报告」一致）
    #   * 结构/解析冲突：allowed_decisions=['keep']（无决策可修正结构；step 阶段普通保留、no-interrupt 终止）
    templates_info = plan.get("templates", {}) or {}
    openspec_yaml_str = templates_info.get("openspec_yaml")
    s7 = _step_skeleton(STEP_OPENSPEC_CONFIG)
    t_s7 = time.monotonic()  # codex 终审 I4：S1-S7 真实计时（起点）
    config_path = root / "openspec" / "config.yaml"
    if not config_path.exists():
        # 目标不存在 → create（从模板原子创建，无需备份）。
        s7["assets"].append({
            "path": "openspec/config.yaml",
            "action": "create",
            "conflict": None,
            "backup_needed": False,
        })
    else:
        # 目标存在 → 需备份；解析+预检+rules.apply 检测。
        _append_backup_need(plan, config_path)
        existing = _safe_read(config_path)
        conflict = None
        if existing is None:
            conflict = {"kind": "unreadable", "fields": ["<file>"]}
        else:
            try:
                old_doc = yaml.safe_load(existing)
            except yaml.YAMLError:
                old_doc = None
                conflict = {"kind": "unparseable", "fields": ["<yaml>"]}
            if conflict is None:
                if old_doc is None:
                    old_doc = {}
                fields = precheck_openspec_structure(old_doc)
                if fields:
                    # 结构/类型不兼容：报告字段路径与实际类型。
                    field_types = _openspec_field_types(old_doc, fields)
                    conflict = {"kind": "structure", "fields": fields,
                                "field_types": field_types}
                elif (isinstance(old_doc, dict)
                      and isinstance(old_doc.get("rules"), dict)
                      and "apply" in old_doc["rules"]):
                    conflict = {"kind": "rules.apply",
                                "value": old_doc["rules"]["apply"]}
        if conflict is None:
            s7["assets"].append({
                "path": "openspec/config.yaml",
                "action": "merge",
                "conflict": None,
                "backup_needed": True,
            })
        else:
            cid = "s7:openspec/config.yaml"
            if conflict["kind"] == "rules.apply":
                allowed = [DECISION_REMOVE_APPLY, DECISION_KEEP]
                # rules.apply 缺省保留（普通模式无 decisions 时默认 keep）
                default_keep = True
                question = (
                    "openspec/config.yaml 含 rules.apply，是否移除？"
                    "（remove_apply=备份后移除，keep=保留并报告）"
                )
                # C-1 修复：推荐保守默认 keep（不移除），与 OS-04「无响应则保留
                # 并报告」一致。
                recommendation = DECISION_KEEP
            else:
                # 结构/解析冲突：无决策可修正，普通模式保留+报告，no-interrupt 终止
                allowed = [DECISION_KEEP]
                default_keep = True
                kind_label = {
                    "structure": "结构/类型不兼容",
                    "unparseable": "YAML 无法解析",
                    "unreadable": "文件无法读取",
                }.get(conflict["kind"], conflict["kind"])
                question = (
                    f"openspec/config.yaml {kind_label}"
                    f"（字段：{', '.join(conflict.get('fields', []))}）"
                )
                recommendation = DECISION_KEEP
            conflict_entry = {
                "conflict_id": cid,
                "asset": "openspec/config.yaml",
                "kind": conflict["kind"],
                "fields": conflict.get("fields"),
                "field_types": conflict.get("field_types"),
                "allowed_decisions": allowed,
                "default_keep": default_keep,
                "question": question,
                "recommendation": recommendation,
            }
            s7["conflicts"].append(dict(conflict_entry))
            plan["conflicts"].append(dict(conflict_entry))
            s7["assets"].append({
                "path": "openspec/config.yaml",
                "action": "keep",
                "conflict": conflict,
                "backup_needed": True,
            })
    s7["status"] = "ok"
    s7["elapsed_ms"] = int((time.monotonic() - t_s7) * 1000)  # codex 终审 I4：真实计时
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
    """判定项目类型（检测结果）：源码扫描 > 主工程配置 > non-coding。

    保留为 compute_plan 内部辅助（旧骨架入口）；完整语义见 detect_project。
    codex 五轮重构：仅返回检测结果，不应用 CLI（与 detect_project 一致）。
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
    """S1 项目类型与技术栈检测（codex 五轮重构：只返回检测结果）。

    返回 dict：
      {
        "project_type": "coding"|"non-coding",   # 等同 detected_type（检测结果）
        "evidence": str,            # 检测证据（相对路径 / 主配置名 / "none"）
        "tech_stack": {             # 五类技术栈检测（未检出写「未检测到」）
          "language": str, "pkg_manager": str,
          "test": str, "lint": str, "format": str, "coverage": "80%",
        },
      }

    用户裁决的项目类型规则（删除 s1:project-type-conflict 后）：detect 只负责自动检测，
    **完全不读取 intents**（既不应用 CLI --project-type，也不产生任何冲突）。最终
    project_type 的两模式裁决（no-interrupt 以检测为准、普通模式 CLI 仅提升）由
    compute_plan 在 detect 之上计算。intents 参数保留只为签名兼容（未来扩展）。
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

    # 2) 技术栈检测（不受 project_type 影响，始终扫描配置文件）。
    tech_stack = _detect_tech_stack(root)

    return {
        "project_type": detected_type,
        "evidence": evidence,
        "tech_stack": tech_stack,
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
    """S1 执行（Task 5 实现）：回填 project_type/tech_stack 到报告。

    codex 五轮重构：project_type 已在 compute_plan 阶段按两模式规则计算为最终值
    （plan["project_type"]）；detect_project 在此只用于补全 tech_stack/evidence。
    s1 决策消费机制已删除（无 s1 冲突）。
    """
    detect_result = detect_project(root, intents)
    report["project_type"] = plan.get("project_type") or detect_result["project_type"]
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

    处理框架受管规则、按项目类型单选来源并落地为 code-usage.md、L1 独立分支，
    以及显式启用或已存在的 Playwright。每个资产按 compute_plan 探测的状态执行：
      * create：读模板 atomic_write；
      * skip：不处理；
      * drift（框架受管规则）：内容==模板则幂等跳过；普通模式按 decision；
        no-interrupt 权威全覆盖为模板内容，不调用 merge_markdown；
      * upgrade/replace（L1）：独立版本化分支，不调 merge_markdown；普通模式按 decision；
        no-interrupt 写当前 v1 模板；
      * 历史 code-usage-coding.md/code-usage-noncoding.md：独立复制归档后移除原位。
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

    # 迁移历史框架产物（屏障外独立归档，因为这些文件不在 backup_needs 清单）。
    for legacy_name in CODE_USAGE_LEGACY_FILES:
        legacy_path = rules_dir / legacy_name
        if legacy_path.exists():
            backup_file(legacy_path, root)
            legacy_path.unlink()
            actions_log.append({
                "path": f".claude/rules/{legacy_name}",
                "action": "migrated-legacy",
            })

    for asset in assets:
        target_name = Path(asset["path"]).name
        template_source = asset.get("template_source", target_name)
        is_l1 = asset.get("is_l1", False)
        target = rules_dir / target_name
        action = asset.get("action")
        conflict = asset.get("conflict")
        # 模板来源可不同于落地名（code-usage.md 单选 coding/non-coding 来源）；
        # .get 兜底兼容既有手工构造 asset 的测试和外部调用。
        try:
            template_text = (rules_root / template_source).read_text(encoding="utf-8")
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
            # --- 框架受管规则文件：权威全覆盖（不调 merge_markdown；屏障已归档）---
            existing_text = _safe_read(target)
            if existing_text == template_text:
                actions_log.append({
                    "path": asset["path"],
                    "action": "unchanged",
                    "branch": "authoritative-idempotent",
                })
                continue
            if intents.no_interrupt:
                atomic_write(target, template_text)
                actions_log.append({
                    "path": asset["path"],
                    "action": "overwritten",
                    "branch": "authoritative-overwrite",
                })
            else:
                if decision == DECISION_REPLACE:
                    atomic_write(target, template_text)
                    actions_log.append({
                        "path": asset["path"],
                        "action": "overwritten",
                        "branch": "rules-replace",
                    })
                else:
                    actions_log.append({
                        "path": asset["path"],
                        "action": "kept",
                        "branch": "rules-keep",
                    })

    # codex 终审 I5 / OP-01：可选规则完整性检查（两模式同动作）。
    # 规则文件与摘要均存在 → 视为已启用，仅检查完整性并报告结果；
    # 文件与摘要不重写。摘要缺失时由 S4 摘要补全（SM-02）处理。
    optional_rules = [CODEGRAPH_RULE_FILE]
    if intents.enable_playwright:
        optional_rules.append(PLAYWRIGHT_RULE_FILE)
    for opt in optional_rules:
        if not (rules_dir / opt).exists():
            continue
        summary_ref = f".claude/rules/{opt}"
        summary_present = False
        for entry_name in ("CLAUDE.md", "AGENTS.md"):
            entry_text = _safe_read(root / entry_name)
            if entry_text and summary_ref in entry_text:
                summary_present = True
                break
        actions_log.append({
            "path": f".claude/rules/{opt}",
            "action": "optional-integrity",
            "branch": "op-01",
            "result": "ok" if summary_present else "summary-missing",
            "detail": (
                "规则文件与摘要均已存在（视为已启用）"
                if summary_present else "摘要缺失（S4 摘要补全将处理）"
            ),
        })

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


def _record_step_elapsed(report: dict, step_name: str, elapsed_ms: int) -> None:
    """将执行阶段真实耗时回写到报告对应 step 的 elapsed_ms 字段（codex 终审 I4）。"""
    for step in report.get("steps", []):
        if step.get("name") == step_name:
            step["elapsed_ms"] = elapsed_ms
            return
    report.setdefault("steps", []).append({
        "name": step_name, "status": "ok", "action": None,
        "reason": "", "elapsed_ms": elapsed_ms, "assets": [],
        "conflicts": [], "actions": [],
    })


def _record_step_conflicts(report: dict, step_name: str, conflicts: list) -> None:
    """将执行阶段产生的冲突回写到报告对应 step 的 conflicts 字段。

    用于 HM-03 等不进 decisions 机制、直接报告的冲突（仅记录，不阻塞）。
    """
    for step in report.get("steps", []):
        if step.get("name") == step_name:
            existing = step.get("conflicts") or []
            existing.extend(conflicts)
            step["conflicts"] = existing
            return
    report.setdefault("steps", []).append({
        "name": step_name, "status": "ok", "action": None,
        "reason": "", "elapsed_ms": 0, "assets": [],
        "conflicts": list(conflicts), "actions": [],
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
            # codex 终审 I2：L0 skip 状态也执行摘要补全与技术栈写入（SM-02/03、
            # S4「单次完成 L0、摘要、技术栈」；L0 区块处理与摘要/技术栈是独立动作）。
            # 内容无变化时不写盘（保持幂等，L0-02/SM-01）。
            existing = _safe_read(entry_path)
            if existing is None:
                actions_log.append({"path": entry_name, "action": "skipped", "branch": "skip-unreadable"})
                continue
            composed = _compose_entry(existing, kernel_source, state="skip",
                                      project_type=project_type, tech_stack=tech_stack,
                                      entry_name=entry_name)
            if composed != existing:
                atomic_write(entry_path, composed)
                actions_log.append({"path": entry_name, "action": "updated", "branch": "skip-backfill"})
            else:
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

        # 入口存在且状态为 insert/upgrade/drift/broken。
        conflict_id = f"s4:{entry_name}"
        existing = _safe_read(entry_path) or ""
        # I-2 修复：insert/upgrade 为确定性动作（merge-semantics L0-05/L0-04
        # 「两模式同动作」），不走 decisions：insert 直接插入当前 v1；
        # upgrade 在全局备份屏障通过后升级为当前 v1。
        if action in ("insert", "upgrade"):
            composed = _compose_entry(existing, kernel_source, state=state or action,
                                      project_type=project_type, tech_stack=tech_stack,
                                      entry_name=entry_name)
            atomic_write(entry_path, composed)
            actions_log.append({"path": entry_name, "action": "updated", "branch": action})
            continue
        # drift/broken → 按模式/决策处理。
        decision = decisions_map.get(conflict_id)
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

    按状态区分 L0 区块处理（保证幂等与区块外保留）：
      * skip：L0 区块不动；
      * create（入口不存在，基线=BASE 文本）：插入 L0；
      * insert（入口存在但无 L0 标记）：插入 L0；
      * drift/upgrade：移除旧区块对后重新插入规范 L0；
      * broken：只移除孤立标记行后插入规范 L0。

    codex 终审 I2：无论 L0 状态如何（skip/insert/upgrade/drift/broken/create），
    均执行规则 2 选文本、缺失摘要行追加（SM-02/03）与技术栈块写入（DF-02/S4
    「单次完成 L0、摘要、技术栈」）——L0 区块处理与摘要/技术栈是独立动作。
    摘要与技术栈补全均为幂等追加（已存在则不动），区块外用户内容保留（L0-B2）。
    """
    text = existing

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

    # --- 步骤 2：规则 2 摘要行按项目类型选择（I2：全状态执行）---
    rule2_text = (
        RULE2_TEXT_CODING if project_type == "coding" else RULE2_TEXT_NONCODING
    )
    for variant in (RULE2_TEXT_CODING, RULE2_TEXT_NONCODING):
        if variant in text and variant != rule2_text:
            text = text.replace(variant, rule2_text, 1)

    # --- 步骤 3：缺失摘要行追加（I2：全状态执行，SM-02）---
    text = _ensure_summary_lines(text, entry_name, project_type)

    # --- 步骤 4：技术栈块追加（I2：全状态执行；幂等，已含则不动）---
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


def _ensure_summary_lines(text: str, entry_name: str, project_type: str = "non-coding") -> str:
    """确保 ## 强制规则 章节含各规则文件引用；同一规则文件的多引用行去重。"""
    rule2_text = (
        RULE2_TEXT_CODING if project_type == "coding" else RULE2_TEXT_NONCODING
    )
    rule6_block = (
        RULE6_BLOCK_CLAUDE if entry_name == "CLAUDE.md" else RULE6_BLOCK_AGENTS
    )
    rule6_first_line = rule6_block.splitlines()[0]
    required = [
        (
            "language.md",
            "- **必须使用中文回答** → 详见 `.claude/rules/language.md`",
        ),
        ("code-usage.md", rule2_text),
        (
            "document-storage.md",
            "- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules/` 目录下** → 详见 `.claude/rules/document-storage.md`",
        ),
        (
            "markdown-format.md",
            "- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`",
        ),
        (
            "mcp-servers.md",
            "- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`"
            if entry_name == "CLAUDE.md"
            else "- **各 MCP 工具及相关自动化工具的使用必须遵循项目规范** → 详见 `.claude/rules/mcp-servers.md`",
        ),
        (
            "code-reading.md",
            "- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`",
        ),
    ]

    lines = text.splitlines()
    rules_idx = next(
        (idx for idx, line in enumerate(lines) if line.strip() == "## 强制规则"),
        None,
    )
    if rules_idx is None:
        return text

    end_idx = len(lines)
    for idx in range(rules_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("## ") or stripped.startswith("# "):
            end_idx = idx
            break

    section = lines[rules_idx:end_idx]
    section_text = "\n".join(section)

    # 同一规则文件仅保留首个精确 `.claude/rules/<name>` 引用行。
    rule_files = [marker for marker, _ in required]
    seen_refs = set()
    deduped = []
    for line in section:
        refs = [
            name
            for name in rule_files
            if f".claude/rules/{name}" in line
        ]
        if refs:
            key = refs[0]
            if key in seen_refs:
                continue
            seen_refs.add(key)
        deduped.append(line)

    missing = [line for marker, line in required if marker not in section_text]
    rule6_missing = rule6_first_line not in section_text
    if not missing and not rule6_missing:
        if deduped == section:
            return text
        return "\n".join(lines[:rules_idx] + deduped + lines[end_idx:])

    insert = list(missing)
    if rule6_missing:
        insert.extend(rule6_block.split("\n"))
    return "\n".join(lines[:rules_idx] + deduped + insert + lines[end_idx:])


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
    """S5 执行（Task 7 实现）：创建 cadence/ 目录结构 + 历史产物迁移。

    两模式行为（简报 Step 1）：
      1. mkdir -p cadence 根目录（仅根，迁移前不预建子目录，以保证 HM-01 三分支可达）；
      2. 历史目录检测：仅扫描 .claude/ 下 HISTORY_DIRS（16 个精确目录）；
         检测结果写入 report.history_detected（清单内存在的相对路径列表）；
      3. no-interrupt：**只写报告 actions**，不执行 mv/合并/rmdir/清理；
         迁移循环虽不执行，但迁移前不预建子目录，故普通模式 HM-01 仍可达；
      4. 普通模式：按 HM-01~03 迁移表处理（循环内按目标状态三分支）：
           * cadence/<dir> 不存在 → mv .claude/<dir> cadence/<dir>（HM-01，整目录 mv）；
           * cadence/<dir> 已存在且为空 → 内容移入 + rmdir 源空目录（HM-02）；
           * cadence/<dir> 已存在且非空 → 跳过 + 报告冲突（HM-03，不进 decisions，直接 report conflict）。
      5. 迁移循环结束后 mkdir -p 全部 17 个 CADENCE_DIRS 子目录（保证最终目录结构齐全，幂等）。

    评审 I-1 修复（方案 B）：迁移前只 mkdir cadence 根目录。
      历史实现先 mkdir -p 全部 17 子目录，导致 HM 循环中 dst.exists() 恒 True、
      目标恒空，HM-01（整目录 mv）永不触发、全部落 HM-02，与 SKILL.md 迁移表
      「目标不存在→mv」语义字面不符。方案 B 调整 mkdir 时机：迁移前只建根，
      循环内按目标状态三分支（HM-01 不存在→shutil.move 整目录 mv 可达、HM-02 空、
      HM-03 非空），循环后再补齐 17 子目录，action 标 moved 与契约字面一致。
    """
    actions_log: list = []
    cadence_root = root / "cadence"

    # 1) 迁移前只 mkdir cadence 根目录（不预建子目录，保证 HM-01 三分支可达）
    cadence_root.mkdir(parents=True, exist_ok=True)
    actions_log.append({
        "path": "cadence/", "action": "created",
        "detail": "mkdir cadence root (pre-migration)",
    })

    # 2) 历史目录检测：扫描 .claude/ 下 HISTORY_DIRS
    claude_dir = root / ".claude"
    detected: list = []
    for d in HISTORY_DIRS:
        src = claude_dir / d
        if src.exists():
            detected.append(f".claude/{d}")
    report["history_detected"] = detected

    # 3) no-interrupt：只写报告，不迁移
    if intents.no_interrupt:
        actions_log.append({
            "path": "<history>", "action": "report-only",
            "detail": f"detected={detected}",
        })
        # 迁移循环虽跳过，仍需补全最终子目录结构
        for sub in CADENCE_DIRS:
            (cadence_root / sub).mkdir(parents=True, exist_ok=True)
        actions_log.append({
            "path": "cadence/", "action": "created",
            "detail": f"mkdir {len(CADENCE_DIRS)} subdirs (post-migration)",
        })
        _record_step_actions(report, STEP_SCAFFOLD, actions_log)
        return

    # 4) 普通模式：按 HM 表迁移（循环内按目标状态三分支）
    conflicts_log: list = []
    for d in HISTORY_DIRS:
        src = claude_dir / d
        if not src.exists():
            continue
        dst = cadence_root / d
        # 判定目标状态（迁移前未预建子目录，dst 不存在时为真实 HM-01）
        dst_exists = dst.exists()
        dst_nonempty = dst_exists and any(dst.iterdir())

        if not dst_exists:
            # HM-01：目标不存在 → mv 整目录源到目标
            # 确保父目录存在（project-rules 等 HISTORY_DIRS 子目录的父级即 cadence 根）
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            actions_log.append({
                "path": f".claude/{d}", "action": "moved",
                "to": f"cadence/{d}", "branch": "hm-01",
            })
        elif not dst_nonempty:
            # HM-02：目标存在且为空 → 内容移入 + rmdir 源
            for entry in src.iterdir():
                shutil.move(str(entry), str(dst / entry.name))
            # 清理空源目录
            try:
                src.rmdir()
            except OSError:
                pass
            actions_log.append({
                "path": f".claude/{d}", "action": "merged",
                "to": f"cadence/{d}", "branch": "hm-02",
            })
        else:
            # HM-03：目标已存在且非空 → 跳过 + 报告冲突（不询问，直接 report conflict）
            conflict_id = f"s5:.claude/{d}"
            conflicts_log.append({
                "conflict_id": conflict_id,
                "asset": f".claude/{d}",
                "state": "target-nonempty",
                "kind": "history-migration",
                "question": f"历史目录 .claude/{d} 目标 cadence/{d} 非空，需手动处理",
                "recommendation": "手动合并后重试",
            })
            actions_log.append({
                "path": f".claude/{d}", "action": "skipped",
                "reason": f"target cadence/{d} nonempty",
                "branch": "hm-03",
            })

    # 5) 迁移循环结束后补全 17 个 CADENCE_DIRS 子目录（保证最终目录结构齐全，幂等）
    for sub in CADENCE_DIRS:
        (cadence_root / sub).mkdir(parents=True, exist_ok=True)
    actions_log.append({
        "path": "cadence/", "action": "created",
        "detail": f"mkdir {len(CADENCE_DIRS)} subdirs (post-migration)",
    })

    _record_step_actions(report, STEP_SCAFFOLD, actions_log)
    if conflicts_log:
        # 冲突写入报告 step.conflicts（不进 decisions 机制，仅报告）
        _record_step_conflicts(report, STEP_SCAFFOLD, conflicts_log)


def step_s6_gitignore(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S6 执行（Task 7 实现）：.gitignore 行级幂等追加。

    规则（简报 Step 2）：
      * cadence/ 仅在 intents.ignore_cadence 时追加（默认不加入）；
      * .codegraph/ 条件 =（project_type=='coding' 或 intents.enable_codegraph）；
      * codegraph.json 不处理（团队共享配置，不加入 gitignore）；
      * 行级幂等：ensure_gitignore_line 内部 grep -qxF 等价判断后追加。
    """
    actions_log: list = []
    project_type = plan.get("project_type", "non-coding")

    # cadence/ 分支（仅 ignore_cadence）
    if intents.ignore_cadence:
        status = ensure_gitignore_line(
            root, GITIGNORE_CADENCE_LINE, GITIGNORE_CADENCE_COMMENT,
        )
        actions_log.append({
            "path": ".gitignore", "action": status,
            "line": GITIGNORE_CADENCE_LINE, "branch": "ignore-cadence",
        })
    else:
        actions_log.append({
            "path": ".gitignore", "action": "skip",
            "reason": "ignore_cadence=False", "branch": "cadence-default",
        })

    # .codegraph/ 分支（coding 或 enable_codegraph）
    if project_type == "coding" or intents.enable_codegraph:
        status = ensure_gitignore_line(
            root, GITIGNORE_CODEGRAPH_LINE, GITIGNORE_CODEGRAPH_COMMENT,
        )
        actions_log.append({
            "path": ".gitignore", "action": status,
            "line": GITIGNORE_CODEGRAPH_LINE, "branch": "codegraph",
        })
    else:
        actions_log.append({
            "path": ".gitignore", "action": "skip",
            "reason": f"project_type={project_type}; enable_codegraph=False",
            "branch": "codegraph-skip",
        })

    _record_step_actions(report, STEP_GITIGNORE, actions_log)


def _s7_precheck_candidate(candidate: str) -> list:
    """对候选 YAML 文本做结构预检（保险层）。

    候选来自封闭来源（模板 + 已工作的既有配置经去重追加），正常应总能通过；
    此处再校验一次以防极端情况（如 merge_yaml 渲染异常）。返回字段路径列表，
    空=通过。不可解析同样视为结构冲突（返回 ['<yaml>']）。
    """
    try:
        doc = yaml.safe_load(candidate)
    except yaml.YAMLError:
        return ["<yaml>"]
    return precheck_openspec_structure(doc)


def _s7_publish_or_abort(
    config_path: Path, candidate: str, report: dict, actions_log: list,
    rel: str, *, branch: str, removed_key: Optional[str] = None,
) -> None:
    """S7 发布：候选 precheck → atomic_write；任一失败则终止、原文件不变。

    ensure_parent 已由 atomic_write 内部处理（此处不重复）。precheck 发现结构
    问题或 atomic_write 失败均 raise PublishError，由 run_apply 捕获标记 fail，
    原文件保持不变（atomic_write 失败时临时文件已清理，原文件未替换）。
    """
    fields = _s7_precheck_candidate(candidate)
    if fields:
        actions_log.append({
            "path": rel, "action": "aborted", "branch": f"{branch}-precheck-fail",
            "fields": fields,
        })
        _record_step_actions(report, STEP_OPENSPEC_CONFIG, actions_log)
        raise PublishError(
            f"openspec/config.yaml 候选结构预检失败（字段：{', '.join(fields)}）；"
            f"候选未发布，原文件不变"
        )
    atomic_write(config_path, candidate)
    entry = {"path": rel, "action": "published", "branch": branch}
    if removed_key:
        entry["removed_key"] = removed_key
    actions_log.append(entry)


def _s7_abort_unparseable(
    config_path: Path, report: dict, actions_log: list, rel: str,
) -> None:
    """记录不可解析终止动作（原文件不变；终止由调用方 raise）。"""
    actions_log.append({
        "path": rel, "action": "aborted", "branch": "unparseable-terminate",
        "detail": "existing YAML 不可解析，候选未构建",
    })
    _record_step_actions(report, STEP_OPENSPEC_CONFIG, actions_log)


def step_s7_openspec_config(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S7 执行（Task 8）：OpenSpec 候选结构预检、保守合并与原子发布。

    流程（简报 Step 2；SKILL.md OpenSpec 合并矩阵）：
      1. ensure_parent(root/openspec)（目录不存在时创建）；
      2. 候选构建：
           * 目标不存在 → 候选=模板文本（原子创建）；
           * 目标存在且无 conflict → merge_yaml 保守合并去重 → 候选；
           * rules.apply 冲突 → merge_yaml 候选已移除 apply；按模式/决策决定是否发布；
           * 结构/解析冲突 → 不构建候选（无法无损规范化）。
      3. 候选 precheck（结构预检保险）；结构问题→终止、原文件不变；
      4. 备份需求已在 compute_plan 进 plan.backup_needs（全局屏障已处理）；
      5. atomic_write 发布；失败→终止、原文件不变、report 含失败详情。

    冲突处理（合并矩阵）：
      * rules.apply：
          - no-interrupt → 备份后移除（候选不含 apply），atomic_write 发布；
          - 普通 remove_apply 决策 → 同上；
          - 普通 keep 或无决策（default_keep）→ 保留原文件，报告。
      * 结构/类型不兼容 / YAML 无法解析 / 文件不可读：
          - 普通模式 → 保留原文件，报告字段路径与类型（status=0）；
          - no-interrupt → 备份后终止（raise，status≠0），原文件不变。
    全程无临时 change、无 openspec instructions。
    """
    actions_log: list = []
    templates_info = plan.get("templates", {}) or {}
    openspec_yaml_str = templates_info.get("openspec_yaml")
    config_path = root / "openspec" / "config.yaml"
    decisions_map = plan.get("decisions_map", {}) or {}
    s7_step = (plan.get("steps", {}) or {}).get(STEP_OPENSPEC_CONFIG, {})
    assets = s7_step.get("assets", []) or []

    # 模板文本（定位失败时退化为空串 → 该资产 skip）。
    template_text = ""
    if openspec_yaml_str:
        try:
            template_text = Path(openspec_yaml_str).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            template_text = ""

    for asset in assets:
        rel = asset.get("path", "openspec/config.yaml")
        action = asset.get("action")
        conflict = asset.get("conflict")

        if action == "create":
            # 目标不存在 → 候选=模板的安全输出形式（merge_yaml(tpl, '')），
            # 确保与后续 merge 幂等（第二次 apply 走 merge 路径时字节不变）。
            if not template_text:
                actions_log.append({
                    "path": rel, "action": "skipped", "reason": "模板缺失",
                })
                continue
            candidate, _ = merge_yaml(template_text, "")
            if candidate is None:
                # 模板不可解析（不应发生）→ 兜底用模板原文
                candidate = template_text
            _s7_publish_or_abort(
                config_path, candidate, report, actions_log, rel,
                branch="create",
            )
            continue

        if action == "merge":
            # 目标存在且无 conflict → 保守合并去重。
            existing = _safe_read(config_path) or ""
            candidate, _ = merge_yaml(template_text, existing)
            if candidate is None:
                # existing 不可解析（不应到达此分支：compute_plan 会标 conflict；
                # 兜底终止）。
                _s7_abort_unparseable(config_path, report, actions_log, rel)
                raise PublishError(
                    f"openspec/config.yaml 不可解析，无法合并（候选未发布，原文件不变）"
                )
            # codex 终审 I3：候选与现状逐字节一致 → 幂等跳过（零写入零备份），
            # 报告明确标记幂等（spec「报告区分幂等跳过与实际变更」）。
            if candidate == existing:
                actions_log.append({
                    "path": rel, "action": "skipped", "branch": "merge-idempotent",
                    "detail": "候选与现状一致，幂等跳过",
                })
                continue
            _s7_publish_or_abort(
                config_path, candidate, report, actions_log, rel,
                branch="merge",
            )
            continue

        # action == "keep"（conflict 非空）。
        kind = conflict.get("kind") if conflict else None
        if kind == "rules.apply":
            decision = decisions_map.get("s7:openspec/config.yaml")
            if intents.no_interrupt or decision == DECISION_REMOVE_APPLY:
                # 备份后移除：merge_yaml 候选已移除 apply。
                existing = _safe_read(config_path) or ""
                candidate, _ = merge_yaml(template_text, existing)
                if candidate is None:
                    _s7_abort_unparseable(config_path, report, actions_log, rel)
                    raise PublishError(
                        "openspec/config.yaml 不可解析，无法移除 rules.apply"
                    )
                _s7_publish_or_abort(
                    config_path, candidate, report, actions_log, rel,
                    branch="rules-apply-removed",
                    removed_key="rules.apply",
                )
            else:
                # keep 或无决策（default_keep）→ 保留原文件，报告。
                actions_log.append({
                    "path": rel, "action": "kept", "branch": "rules-apply-keep",
                    "detail": "rules.apply 保留（用户未确认移除）",
                })
                _record_step_conflicts(report, STEP_OPENSPEC_CONFIG, [{
                    "conflict_id": "s7:openspec/config.yaml",
                    "asset": rel, "kind": "rules.apply",
                    "question": "openspec/config.yaml 含 rules.apply",
                    # C-1 修复：推荐保守默认 keep（不移除）。
                    "recommendation": DECISION_KEEP,
                }])
            continue

        # 结构/解析/不可读冲突。
        if intents.no_interrupt:
            # no-interrupt：备份后无法无损规范化→终止，原文件不变。
            _record_step_conflicts(report, STEP_OPENSPEC_CONFIG, [{
                "conflict_id": "s7:openspec/config.yaml",
                "asset": rel, "kind": kind,
                "fields": conflict.get("fields"),
                "field_types": conflict.get("field_types"),
                "question": (
                    f"openspec/config.yaml {kind}，无法无损规范化"
                ),
                "recommendation": "手动修复后重试",
            }])
            actions_log.append({
                "path": rel, "action": "aborted", "branch": f"{kind}-terminate",
                "detail": f"fields={conflict.get('fields')}",
            })
            _record_step_actions(report, STEP_OPENSPEC_CONFIG, actions_log)
            raise PublishError(
                f"openspec/config.yaml {kind}，无法无损规范化；已备份，原文件不变"
            )
        else:
            # 普通模式：保留原文件，报告字段路径与类型（status=0）。
            actions_log.append({
                "path": rel, "action": "kept", "branch": f"{kind}-preserve",
                "fields": conflict.get("fields"),
                "field_types": conflict.get("field_types"),
            })
            _record_step_conflicts(report, STEP_OPENSPEC_CONFIG, [{
                "conflict_id": "s7:openspec/config.yaml",
                "asset": rel, "kind": kind,
                "fields": conflict.get("fields"),
                "field_types": conflict.get("field_types"),
                "question": (
                    f"openspec/config.yaml {kind}（字段："
                    f"{', '.join(conflict.get('fields', []) or [])}）"
                ),
                "recommendation": "手动修复后重试",
            }])

    _record_step_actions(report, STEP_OPENSPEC_CONFIG, actions_log)


def _s8_record_elapsed(report: dict, elapsed_ms: int) -> None:
    """将 S8 独立计时写入报告 s8_codegraph step 的 elapsed_ms 字段。

    it-budget 断言 s8_codegraph step 必须含 elapsed_ms（Task 3 it-budget 契约）。
    """
    for step in report.get("steps", []):
        if step.get("name") == STEP_CODEGRAPH:
            step["elapsed_ms"] = elapsed_ms
            return
    report.setdefault("steps", []).append({
        "name": STEP_CODEGRAPH, "status": "ok", "action": None,
        "reason": "", "elapsed_ms": elapsed_ms, "assets": [],
        "conflicts": [], "actions": [],
    })


def _s8_ensure_mcp_configs(root: Path, report: dict, actions_log: list) -> None:
    """核验并补齐双 MCP 配置（.mcp.json 与 .codex/config.toml）。

    任一缺失则补写：
      * .codex/config.toml：追加 CODEX_MCP_BLOCK（先 ensure_parent，
        备份由全局屏障处理；此处读取既有文本末尾补换行后追加区块）；
      * .mcp.json：兜底 JSON 合并——解析既有 JSON（缺失/不可解析视为 {}），
        写入 mcpServers.codegraph = MCPJSON_CODEGRAPH_ENTRY，原子写回。
    配置补写/备份/原子写失败 → 抛错终止（PublishError）。
    """
    # .codex/config.toml 补写
    if not has_codegraph_mcp_codex(root):
        toml_path = root / ".codex" / "config.toml"
        existing_toml = _safe_read(toml_path) or ""
        # 末尾确保换行分隔后追加区块
        if existing_toml and not existing_toml.endswith("\n"):
            existing_toml += "\n"
        candidate = existing_toml + CODEX_MCP_BLOCK
        try:
            atomic_write(toml_path, candidate)
        except PublishError:
            raise
        actions_log.append({
            "path": ".codex/config.toml", "action": "published",
            "branch": "codex-mcp-patched",
        })
    # .mcp.json 补写（兜底 JSON 合并）
    if not has_codegraph_mcp_mcpjson(root):
        mcp_path = root / ".mcp.json"
        # codex 终审 C2：重写既有 .mcp.json 前必须先备份（无效/非对象 JSON
        # 同样备份——原配置可能是用户仅存的恢复点）；备份失败即终止（PublishError）。
        if mcp_path.exists():
            try:
                mcp_backup = backup_file(mcp_path, root)
            except BackupError as exc:
                raise PublishError(f".mcp.json 重写前备份失败：{exc}") from exc
            report.setdefault("backups", []).append({
                "file": str(mcp_path), "backup": str(mcp_backup),
            })
            actions_log.append({
                "path": ".mcp.json", "action": "backed-up",
                "branch": "mcpjson-pre-rewrite", "backup": str(mcp_backup),
            })
        raw = _safe_read(mcp_path)
        doc: dict = {}
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    doc = parsed
            except (ValueError, TypeError):
                # 不可解析 → 兆底为空 dict 重写（配置已损坏，按新配置覆盖）
                doc = {}
        servers = doc.get("mcpServers")
        if not isinstance(servers, dict):
            servers = {}
            doc["mcpServers"] = servers
        servers["codegraph"] = dict(MCPJSON_CODEGRAPH_ENTRY)
        try:
            atomic_write(mcp_path, json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
        except PublishError:
            raise
        actions_log.append({
            "path": ".mcp.json", "action": "published",
            "branch": "mcpjson-merged",
        })


def step_s8_codegraph(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S8 执行（Task 9）：CodeGraph 增量矩阵与降级、独立计时。

    启用条件 =（project_type=='coding' 或 intents.enable_codegraph）；否则 skip。
    状态矩阵（简报 Step 1）：
      * .codegraph/ 存在 → 仅调 codegraph status（不重复 install/init）；
      * .codegraph/ 不存在 → codegraph install（cwd=project_root）→
        核验双 MCP 配置、仅补仍缺失方 → codegraph init（cwd=project_root）。
    失败降级（简报 Step 2；S8 唯一例外：仅 install/init/status 子命令失败可 degraded）：
      * install 失败 → 仍补齐双配置 + status=degraded + note（不再 init/status）；
      * init/status 失败 → degraded + note；
      * codegraph 二进制缺失/不可执行（FileNotFoundError/OSError）→ 按 install
        失败降级路径处理（CS-07）：补齐双配置 + degraded + note，不 crashed（C-2）；
      * 配置补写/备份/原子写失败 → 抛错终止（PublishError）。
    预算口径：S8 全程 elapsed_ms 单独计时；budget_seconds_excluding_codegraph
    在 S7 完成点计算（S8 不计入 budget）。
    """
    t_start = time.monotonic()
    actions_log: list = []
    project_type = plan.get("project_type", "non-coding")
    notes: list = []
    degraded = False

    # 启用条件
    if not (project_type == "coding" or intents.enable_codegraph):
        actions_log.append({
            "action": "skip",
            "reason": f"project_type={project_type}; enable_codegraph=False",
            "branch": "codegraph-skip",
        })
        _record_step_actions(report, STEP_CODEGRAPH, actions_log)
        _s8_record_elapsed(report, int((time.monotonic() - t_start) * 1000))
        return

    codegraph_dir = root / ".codegraph"
    codegraph_exists = codegraph_dir.is_dir()

    try:
        if codegraph_exists:
            # .codegraph/ 存在 → 仅调 status（不重复 install/init）
            actions_log.append({
                "action": "status-only", "branch": "codegraph-existing",
                "detail": ".codegraph/ 已存在，仅执行 codegraph status",
            })
            status_rc = subprocess.run(
                ["codegraph", "status"], cwd=str(root),
            ).returncode
            if status_rc != 0:
                degraded = True
                notes.append(f"codegraph status 失败（rc={status_rc}）")
                actions_log.append({
                    "action": "degraded", "branch": "status-failed",
                    "detail": f"codegraph status rc={status_rc}",
                })
            # codex 终审 I1：.codegraph/ 已存在时也核验双 MCP 配置，缺失则补齐
            # （CS-04~06/CG-05~06：status 核验与配置补齐是独立动作，status
            # 失败降级不影响补齐；配置补写/备份/原子写失败仍抛 PublishError 终止）。
            _s8_ensure_mcp_configs(root, report, actions_log)
        else:
            # .codegraph/ 不存在 → install → 核验补配置 → init
            install_rc = subprocess.run(
                ["codegraph", "install", "--target=claude,codex",
                 "--location=local", "--yes"],
                cwd=str(root),
            ).returncode
            actions_log.append({
                "action": "install", "branch": "codegraph-install",
                "detail": f"install rc={install_rc}",
            })
            if install_rc != 0:
                # install 失败 → 仍补齐双配置 + degraded（不再 init/status）
                notes.append(f"codegraph install 失败（rc={install_rc}）")
                degraded = True
                # 配置补写失败 → 抛错终止（配置补写不允许降级）
                _s8_ensure_mcp_configs(root, report, actions_log)
                actions_log.append({
                    "action": "degraded", "branch": "install-failed",
                    "detail": "install 失败，已补齐双 MCP 配置",
                })
            else:
                # install 成功 → 核验补配置 → init
                _s8_ensure_mcp_configs(root, report, actions_log)
                init_rc = subprocess.run(
                    ["codegraph", "init"], cwd=str(root),
                ).returncode
                actions_log.append({
                    "action": "init", "branch": "codegraph-init",
                    "detail": f"init rc={init_rc}",
                })
                if init_rc != 0:
                    degraded = True
                    notes.append(f"codegraph init 失败（rc={init_rc}）")
                    actions_log.append({
                        "action": "degraded", "branch": "init-failed",
                        "detail": f"codegraph init rc={init_rc}",
                    })
    except PublishError:
        # 配置补写/备份/原子写失败 → 抛错终止（S8 唯一不允许降级的路径）
        _record_step_actions(report, STEP_CODEGRAPH, actions_log)
        _s8_record_elapsed(report, int((time.monotonic() - t_start) * 1000))
        raise
    except (FileNotFoundError, OSError) as exc:
        # C-2 修复：codegraph 二进制缺失/不可执行（FileNotFoundError/OSError）→
        # 按 install 失败降级路径处理（CS-07）：仍补齐双配置 + degraded + note，
        # 不得整体 crashed。配置补写失败仍为 PublishError（上方分支）向外传播。
        degraded = True
        notes.append(f"codegraph 二进制不可用（{type(exc).__name__}: {exc}）")
        actions_log.append({
            "action": "degraded", "branch": "binary-missing",
            "detail": f"codegraph 不可用：{exc}",
        })
        # 与 install 失败降级路径一致：仍补齐双 MCP 配置。
        _s8_ensure_mcp_configs(root, report, actions_log)

    # 记录动作与独立计时
    _record_step_actions(report, STEP_CODEGRAPH, actions_log)
    _s8_record_elapsed(report, int((time.monotonic() - t_start) * 1000))

    # 降级标记（不影响退出码；overall 由 ok 转为 degraded）
    if degraded:
        report["overall"] = "degraded"
        # note 记录到 s8 step 的 reason 字段
        for step in report.get("steps", []):
            if step.get("name") == STEP_CODEGRAPH:
                step["status"] = "degraded"
                existing_reason = step.get("reason") or ""
                note_text = "; ".join(notes)
                step["reason"] = (existing_reason + "; " + note_text).strip("; ") \
                    if existing_reason else note_text
                break



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
# I3（codex 终审）：备份屏障过滤——只收集真实写入需求
# ---------------------------------------------------------------------------


def _backup_required_for(target: Path, root: Path, plan: dict, intents: Intents) -> bool:
    """判定 target 是否真实需要备份（有实际写入/备份后终止动作）。

    规则（codex 终审 I3）：
      * S3 冲突资产：no-interrupt 或 decision==replace 才写入；keep 不备份；
      * S4 upgrade：确定性升级，始终写入 → 备份；drift/broken 同 S3 决策语义；
      * S7 merge：候选与现状逐字节不同才写入（幂等 → 不备份）；
      * S7 rules.apply：no-interrupt 或 decision==remove_apply → 备份；
        无决策默认 keep → 不备份；
      * S7 结构/解析/不可读冲突：no-interrupt 备份后终止 → 备份；普通保留 → 不备份；
      * 无法归属任何资产 → 保守保留（不放宽屏障）。
    """
    decisions_map = plan.get("decisions_map", {}) or {}
    steps = plan.get("steps", {}) or {}
    key = str(target)

    def _matches(asset: dict) -> bool:
        return str(root / asset.get("path", "")) == key

    # S3 规则文件
    for asset in (steps.get(STEP_RULES_FILES, {}) or {}).get("assets", []) or []:
        if not _matches(asset):
            continue
        if not asset.get("conflict"):
            return False
        if intents.no_interrupt:
            return True
        return decisions_map.get(f"s3:{asset['path']}") == DECISION_REPLACE

    # S4 入口文件
    for asset in (steps.get(STEP_ENTRY_FILES, {}) or {}).get("assets", []) or []:
        if not _matches(asset):
            continue
        action = asset.get("action")
        if action == "upgrade":
            # 确定性升级（两模式同动作）→ 始终写入
            return True
        if action == "replace":  # drift/broken
            if intents.no_interrupt:
                return True
            return decisions_map.get(f"s4:{asset['path']}") == DECISION_REPLACE
        return False

    # S7 OpenSpec 配置
    for asset in (steps.get(STEP_OPENSPEC_CONFIG, {}) or {}).get("assets", []) or []:
        if not _matches(asset):
            continue
        action = asset.get("action")
        conflict = asset.get("conflict")
        if action == "merge":
            # 幂等判定：候选与现状逐字节比较（I3：幂等不进备份需求）
            existing = _safe_read(target)
            if existing is None:
                return True  # 读不出 → 保守备份
            template_text = ""
            openspec_yaml = (plan.get("templates", {}) or {}).get("openspec_yaml")
            if openspec_yaml:
                try:
                    template_text = Path(openspec_yaml).read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    template_text = ""
            candidate, _ = merge_yaml(template_text, existing)
            if candidate is None:
                return True  # 无法判定 → 保守备份
            return candidate != existing
        if action == "keep" and isinstance(conflict, dict):
            kind = conflict.get("kind")
            if kind == "rules.apply":
                if intents.no_interrupt:
                    return True
                return decisions_map.get("s7:openspec/config.yaml") == DECISION_REMOVE_APPLY
            # structure/unparseable/unreadable：no-interrupt 备份后终止（OS-03/05）→
            # 备份；普通模式保留原文件不改 → 不备份
            return bool(intents.no_interrupt)
        return False

    # 未匹配到任何资产（异常路径）→ 保守保留备份需求
    return True


def _filter_backup_needs(plan: dict, intents: Intents, root: Path) -> list:
    """过滤 plan.backup_needs，只保留真实写入需求（codex 终审 I3）。

    keep 决策与幂等（候选==现状）不进备份屏障，避免无效备份破坏幂等，
    也避免无必要备份失败导致的中止。
    """
    return [
        target for target in (plan.get("backup_needs", []) or [])
        if _backup_required_for(target, root, plan, intents)
    ]


# ---------------------------------------------------------------------------
# 主流程：dry-run / apply
# ---------------------------------------------------------------------------


def run_dry_run(root: Path, intents: Intents, report: dict) -> int:
    """dry-run：compute_plan + 写报告，零写入。"""
    plan = compute_plan(root, intents)
    _sync_plan_to_report(plan, report, intents)
    # S2 模板定位失败（§11.5：所有候选不完整 → 终止并报告，非零退出）
    if plan.get("failure"):
        report["overall"] = "fail"
        report["failure"] = {
            "file": plan["failure"].get("step") or STEP_TEMPLATES,
            "reason": plan["failure"].get("reason", ""),
            "recovery": plan["failure"].get("recovery", ""),
        }
        return 1
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
      6. 异常兜底 → overall=fail + 写报告 + 退出 1。
    """
    # 1. compute_plan
    plan = compute_plan(root, intents)
    _sync_plan_to_report(plan, report, intents)

    # 1b. S2 模板定位失败 → fail closed（§11.5：非零退出、目标项目零写入；
    # decisions/备份屏障/发布均不得继续）。
    if plan.get("failure"):
        report["overall"] = "fail"
        report["failure"] = {
            "file": plan["failure"].get("step") or STEP_TEMPLATES,
            "reason": plan["failure"].get("reason", ""),
            "recovery": plan["failure"].get("recovery", ""),
        }
        return 1

    # 2. decisions 校验（仅普通模式且 plan 有冲突）
    plan_conflicts = plan.get("conflicts", []) or []
    # default_keep 冲突（如 openspec rules.apply）不要求 decisions 文件覆盖
    required_conflicts = [c for c in plan_conflicts if not c.get("default_keep")]
    if not intents.no_interrupt and plan_conflicts:
        if intents.decisions is None:
            violations = [f"冲突缺少决策：{c['conflict_id']}" for c in required_conflicts]
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
                    # codex 终审 I4：失败报告同样携带 allowed_decisions
                    "allowed_decisions": c.get("allowed_decisions"),
                    # codex 三轮 C3：失败报告同样携带 default_keep（A/B 类判别）。
                    "default_keep": c.get("default_keep", False),
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
    # codex 终审 I3：屏障只收集真实写入需求（keep 决策与幂等候选剔除）。
    backup_needs = _filter_backup_needs(plan, intents, root)
    backups_done: list = []
    for target in backup_needs:
        try:
            backup_path = backup_file(Path(target), root)
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
            if step_name == STEP_CODEGRAPH:
                # S8 独立计时（_s8_record_elapsed 自记录，不计入 budget）
                step_func(root, intents, plan, report)
            else:
                # codex 终审 I4：S1-S7 执行阶段真实 time.monotonic() 计时
                t_step = time.monotonic()
                step_func(root, intents, plan, report)
                _record_step_elapsed(
                    report, step_name, int((time.monotonic() - t_step) * 1000),
                )
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
        # I-4 修复：overall 收敛到 ok/degraded/fail 三值（crashed→fail）；
        # failure.file 填实际失败文件路径（从异常上下文提取）。
        report["overall"] = "fail"
        report["failure"] = {
            "file": _extract_failure_file(exc, locals().get("step_name")),
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
    # 同步 S5 历史目录检测结果（dry-run 与 apply 初始报告均需含此字段）。
    report["history_detected"] = plan.get("history_detected", []) or []
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
            # P1-1：no-interrupt 对外报告须如实暴露实际执行动作，避免 recommendation=keep 误导。
            "no_interrupt_action": c.get("no_interrupt_action"),
            # codex 终审 I4：Agent 需凭 allowed_decisions 提问并生成 decisions
            "allowed_decisions": c.get("allowed_decisions"),
            # codex 三轮 C3（方案 X）：报告携带 default_keep，明示该冲突具备安全默认
            # （无响应→保留并报告 status=0），供 Agent 与测试判别 A/B 类。
            "default_keep": c.get("default_keep", False),
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
        help=(
            "项目类型两模式规则：普通模式仅在检测为 non-coding 时可提升为 "
            "coding（检测 coding 则忽略）；no-interrupt 模式忽略，以检测结果为准"
        ),
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
        # I-4 修复：overall 收敛三值（crashed→fail）；failure.file 必填。
        report["overall"] = "fail"
        report["failure"] = {
            "file": _extract_failure_file(exc, None),
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
