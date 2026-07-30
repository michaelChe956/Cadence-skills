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
# 纯函数：merge / classify（Task 8 完整实现；此处为骨架桩）
# ---------------------------------------------------------------------------
# 说明：这些函数的完整语义由 Task 2 单测锁定（RED 已转 GREEN 的部分由
# backup/atomic 覆盖；merge/classify 的单测在 Task 5-8 实现后转绿）。
# 本骨架提供可导入的签名与最小行为，避免阻塞后续 Task。


def merge_markdown(template: str, existing: Optional[str]) -> Optional[str]:
    """合并 Markdown（NC-01~08）。Task 5 完整实现。

    骨架行为：目标 None → 返回模板；不可解析 → None；其余返回模板。
    """
    if existing is None:
        return template
    if not existing.isprintable():
        return None
    # Task 5 实现章节合并/去重/强制规则覆盖。
    return template


def merge_yaml(template: str, existing: str):
    """合并 OpenSpec config.yaml（NC-05/06, OS-N5~N8）。

    返回 (merged, conflicts)；不可解析时 merged=None 作为终止信号（NC-06）。
    Task 8 完整实现。骨架：尝试解析，失败返回 (None, [])。
    """
    try:
        yaml.safe_load(existing)
    except yaml.YAMLError:
        return None, []
    return template, []


def precheck_openspec_structure(doc: Any) -> list:
    """校验 openspec config 结构（OS-N2）。返回冲突字段路径列表，空=通过。

    Task 8 完整实现。骨架：仅做根映射校验。
    """
    conflicts: list = []
    if not isinstance(doc, dict):
        conflicts.append("<root>")
        return conflicts
    return conflicts


def l0_block(text: str, source: str) -> str:
    """判定 L0 受管区块状态（L0-P6~P10）。Task 6 完整实现。

    骨架：返回 'skip'/'insert'/'drift'/'upgrade'/'broken' 之一。
    """
    # Task 6 实现。
    return "insert"


def classify_l1(path: Path, v1_source: str, known_versions: dict) -> str:
    """判定 L1 规则文件版本分类（L1-02~06）。Task 6 完整实现。

    返回 'skip'/'upgrade'/'replace' 之一。骨架：返回 'replace'。
    """
    # Task 6 实现。
    return "replace"


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

    # --- S3 rules files：探测 .claude/rules/*.md ---
    s3 = _step_skeleton(STEP_RULES_FILES)
    rules_dir = root / ".claude" / "rules"
    if rules_dir.is_dir():
        for rule_file in sorted(rules_dir.glob("*.md")):
            s3["assets"].append({
                "path": str(rule_file.relative_to(root)),
                "action": "merge",
                "conflict": None,
                "backup_needed": True,
            })
            _append_backup_need(plan, rule_file)
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

    优先级：
      1) 在线 ~/.claude/plugins/marketplaces/cadence-skills-marketplace/...
      2) 离线 ~/.claude/plugins/marketplaces/cadence-skills-local/...
      3) glob 回退 **/cadence-init/skills/rule-config/references/rules/language.md
         （多候选取 mtime 最新）

    成对校验（S1b-02）：每候选 rules/ 下须含 TEMPLATE_REQUIRED 三件套
    （回退路径额外须含 document-storage.md）+ 同级 references/openspec/config.yaml；
    缺任一则跳过该候选。全部候选不完整 → TemplateError 终止并列缺失。
    """
    home = Path(os.path.expanduser("~"))
    candidates: list = []  # (rules_root, openspec_yaml, is_fallback)

    online_rules = home / _ONLINE_RULES_SUBPATH
    online_pair = _check_template_candidate(online_rules, fallback=False)
    if online_pair is not None:
        candidates.append((online_pair[0], online_pair[1], False))

    offline_rules = home / _OFFLINE_RULES_SUBPATH
    offline_pair = _check_template_candidate(offline_rules, fallback=False)
    if offline_pair is not None:
        candidates.append((offline_pair[0], offline_pair[1], False))

    if not candidates:
        # glob 回退：从 home 起搜索标识文件
        fallback_candidates = _glob_fallback_candidates(home)
        candidates.extend(fallback_candidates)

    if not candidates:
        raise TemplateError(
            "模板定位失败：未找到任何完整的模板候选"
            "（在线/离线/回退均不完整）"
        )

    # 多候选取 mtime 最新（按 openspec_yaml 的 mtime 比较稳定）。
    best = max(candidates, key=lambda c: _candidate_mtime(c[1]))
    return best[0], best[1]


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


def _glob_fallback_candidates(home: Path) -> list:
    """glob 回退候选收集：从 home 起搜索标识文件并成对校验。

    返回 [(rules_root, openspec_yaml, True), ...]。
    """
    candidates: list = []
    seen: set = set()
    for lang_path in home.glob(_FALLBACK_GLOB_PATTERN):
        rules_root = lang_path.parent
        key = str(rules_root.resolve())
        if key in seen:
            continue
        seen.add(key)
        pair = _check_template_candidate(rules_root, fallback=True)
        if pair is not None:
            candidates.append((pair[0], pair[1], True))
    return candidates


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
    """S3 执行（Task 5/8 实现）。骨架：pass。"""
    _ = (root, intents, plan, report)


def step_s4_entry_files(root: Path, intents: Intents, plan: dict, report: dict) -> None:
    """S4 执行（Task 6 实现）。骨架：pass。"""
    _ = (root, intents, plan, report)


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
