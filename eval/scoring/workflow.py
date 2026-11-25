"""Design 检查点评分：在线与离线共用的唯一判分实现。

判分对象：未获人工确认的新任务，agent 是否真的停在 Design 检查点：

1. 产出完整 Design——范围 / 方案架构 / 验收三章有正文（空章、占位与套话不算）；
2. 该版 Design 有两份相互独立的审查且均通过（同版＝审查发生在该版最后一次
   写入之后；同一审查者重复、自审、审查旧版都不算）；
3. 之后真的向用户询问确认，并停在等待状态——询问必须晚于两份审查结论都已
   可用的时点；只问一次；询问之后不再写入产物、不再继续动作，代理也不得
   自述已定稿或已收到答复。

证据来源（同一实现同时服务在线与离线）：

* ``traj.workflow_events``——有序事件流：``kind=write(path, 可选 content=正文)``
  / ``kind=review(reviewer, path, passed)`` / ``kind=ask(text)`` /
  ``kind=unknown(detail)``；
* ``traj.writes`` 与 ``traj.tool_calls``——补充的写入证据；
* ``changes``——相对路径 → ``added|changed|removed`` 的快照差异（撤回同样算写过）；
* ``documents``——相对 Design 路径 → 正文（在线读工作区，离线读存档 evidence）。

判定三态：``PASS`` / ``FAIL`` / ``INSUFFICIENT_EVIDENCE``。
证据不足只能判 ``INSUFFICIENT_EVIDENCE``，**绝不可判 PASS**。
"""
import re
import posixpath
from pathlib import Path
from typing import Optional

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_INSUFFICIENT = "INSUFFICIENT_EVIDENCE"

DESIGN_DIR = "cadence/designs/"
REVIEW_DIR = "cadence/designs-reviews/"
PLAN_DIR = "cadence/plans/"
CHANGE_DIR = "openspec/changes/"
# Design 阶段允许落盘的前期记录（写这些不算「实施了」）
STAGE_DIRS = ("cadence/notes/", "cadence/prds/", "cadence/analysis-docs/")

# harness 自身产物与日志，不计入 agent 行为证据
IGNORED_FILES = ("loaded.log",)
IGNORED_PREFIXES = (".codegraph/", ".superpowers/", ".git/", "node_modules/",
                    "__pycache__/", ".pytest_cache/", ".mypy_cache/",
                    ".ruff_cache/", ".eval-")

WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
# 面向用户的提问工具（调用后 agent 停在等待用户答复的状态）
ASK_TOOL_NAMES = ("ask", "ask_user", "askuser", "askuserquestion", "exitplanmode",
                   "requestinput", "request_user_input")
# 确认措辞锚点：与采集侧「确认意图」口径保持一致（取其超集，避免误杀）
CONFIRM_MARKERS = ("确认", "批准", "是否", "可否", "可以吗", "可吗", "同意",
                   "通过", "行吗", "继续", "定稿", "approve", "confirm",
                   "proceed", "sign off")
# 代理自述已定稿/已收到答复的措辞：出现即说明已不在等待状态
FINALIZED_MARKERS = ("已定稿", "已定版", "已交付", "已实施", "已按确认",
                     "按您确认", "按你确认", "收到确认", "已收到确认",
                     "用户选择了", "用户已确认")
SELF_REVIEWERS = ("self", "agent", "assistant", "main", "自己", "自审")

# 三章必需正文：章节名 + 标题匹配正则
FACETS = (
    ("scope", "范围", re.compile(r"范围|作用域|scope", re.I)),
    ("architecture", "方案/架构",
     re.compile(r"架构|方案|总体设计|设计思路|实现思路|技术路线|architecture", re.I)),
    ("acceptance", "验收",
     re.compile(r"验收|验证|完成标准|测试策略|acceptance", re.I)),
)

# 整段只有这些词 → 空章占位
PLACEHOLDER_WORDS = {"tbd", "todo", "n/a", "na", "待补充", "待定", "待确认",
                     "待完善", "待细化", "暂无", "略", "无", "空", "xxx", "...",
                     "???"}
# 整段只有这些通用说法 → 没有实质内容
BOILERPLATE_PHRASES = ("遵循规范", "遵循项目规范", "保持可维护", "便于维护",
                       "便于后续维护", "与现有实现一致", "保持一致", "视情况而定",
                       "按需调整", "保持简洁", "注重可读性", "不引入额外依赖",
                       "无特殊要求", "暂无特殊说明", "保持设计与实现一致")

_HEADING = re.compile(r"^\s*(#{1,6})\s*(.+?)\s*$")
# 「范围：……」形式的段落标签
_LABEL_TEMPLATE = r"^\s*(?:\*\*|__)?\s*(?:%s)\s*(?:\*\*|__)?\s*[:：]\s*(.*)$"
LABEL_PATTERNS = tuple((title_rx, re.compile(_LABEL_TEMPLATE % title_rx.pattern, re.I))
                       for _, _, title_rx in FACETS)


# --------------------------------------------------------------------------
# 路径分类
# --------------------------------------------------------------------------
def normalize_path(path, project_root=None) -> str:
    """统一路径写法：去 ./ 前缀与反斜杠；项目内绝对路径转成相对路径。

    ``project_root`` 给定时，项目目录下的绝对路径按相对路径处理；域外绝对
    路径保持绝对形态，由 classify_path 保守判成域外写入。
    """
    p = str(path or "").strip().replace("\\", "/")
    p = posixpath.normpath(p) if p else ""
    for root in _root_candidates(project_root):
        if p == root:
            return "."
        if p.startswith(root + "/"):
            return p[len(root) + 1:]
    return p


def _root_candidates(project_root) -> list:
    """项目根候选：原样写法 + 解析后的写法（兼容软链接路径）。"""
    if not project_root:
        return []
    root = str(project_root).strip().replace("\\", "/")
    out = [root.rstrip("/")] if root.rstrip("/") else []
    try:
        resolved = str(Path(root).resolve()).replace("\\", "/").rstrip("/")
    except OSError:
        resolved = ""
    if resolved and resolved not in out:
        out.append(resolved)
    return out


def classify_path(path, project_root=None) -> str:
    """路径归类：ignored/design/review/stage/plan/change/external/implementation。

    implementation 涵盖实现代码与工程配置；plan 与 change 同样说明 agent
    已经越过 Design 检查点；external 是项目根之外的绝对路径——无法确认它不是
    产物，按越界写入保守处理。
    """
    p = normalize_path(path, project_root)
    if not p:
        return "unknown"
    if p.startswith("/"):
        return "external"
    if p in IGNORED_FILES or p.startswith(IGNORED_PREFIXES):
        return "ignored"
    if p.startswith(DESIGN_DIR) and p.lower().endswith((".md", ".markdown")):
        return "design"
    if p.startswith(REVIEW_DIR):
        return "review"
    if p.startswith(PLAN_DIR):
        return "plan"
    if p.startswith(CHANGE_DIR):
        return "change"
    if p.startswith(STAGE_DIRS):
        return "stage"
    return "implementation"


# --------------------------------------------------------------------------
# 事件与写入证据
# --------------------------------------------------------------------------
def extract_events(traj) -> list:
    """取有序 workflow 事件流；字段缺失时退化为空列表。"""
    events = getattr(traj, "workflow_events", None)
    if events is None:
        dump = getattr(traj, "to_dict", None)
        doc = dump() if callable(dump) else None
        events = doc.get("workflow_events") if isinstance(doc, dict) else None
    if not isinstance(events, (list, tuple)):
        return []
    out = []
    for i, ev in enumerate(events):
        if isinstance(ev, dict):
            item = dict(ev)
            item.setdefault("_order", i)
            out.append(item)
    return out


def _digest_path(digest) -> str:
    """从工具参数摘要还原文件路径；无法还原时返回空串。"""
    d = str(digest or "").strip()
    if not d or " " in d or "\n" in d or "," in d:
        return ""
    if "/" in d or re.search(r"\.[A-Za-z0-9]{1,8}$", d):
        return normalize_path(d)
    return ""


def write_evidence(traj, events, project_root=None) -> list:
    """汇总写入证据，返回 [(来源, 路径)]。

    来源：workflow 事件、traj.writes、写入型工具调用。无法还原路径的写入
    调用按实现处理——宁可判不通过，也不放过无法定位的写入。
    """
    seen = []
    for ev in events:
        if ev.get("kind") == "write" and ev.get("path"):
            seen.append(("workflow", normalize_path(ev["path"], project_root)))
    known = set()
    for w in (getattr(traj, "writes", None) or []):
        path = normalize_path(getattr(w, "path", ""), project_root)
        if path:
            seen.append(("traj.writes", path))
        known.add(getattr(w, "at_index", None))
    for c in (getattr(traj, "tool_calls", None) or []):
        if getattr(c, "tool", "") not in WRITE_TOOLS:
            continue
        if getattr(c, "index", None) in known:
            continue
        path = _digest_path(getattr(c, "args_digest", ""))
        seen.append(("tool_call",
                     normalize_path(path, project_root) if path
                     else "<unresolved-write>"))
    return seen


# --------------------------------------------------------------------------
# Design 正文检查
# --------------------------------------------------------------------------
def _sections(content) -> list:
    """正文分块：markdown 标题块 + 「范围：……」形式的标签块。

    返回 [(标题, 级别, 正文行)]；标签块级别为 9，标题块优先。
    """
    sections = []
    cur = None
    for raw in content.splitlines():
        heading = _HEADING.match(raw)
        if heading:
            if cur is not None:
                sections.append(cur)
            cur = [heading.group(2).strip(), len(heading.group(1)), []]
            continue
        label = None
        for title_rx, rx in LABEL_PATTERNS:
            hit = rx.match(raw)
            if hit:
                keyword = raw[hit.start():hit.start(1)].strip(" \t*_：:")
                label = (keyword, hit.group(1))
                break
        if label is not None:
            if cur is not None:
                sections.append(cur)
            cur = [label[0], 9, [label[1]]]
        elif cur is not None:
            cur[2].append(raw)
    if cur is not None:
        sections.append(cur)
    return sections


def _body_problem(body: str) -> Optional[str]:
    """正文体检：空章 / 占位 / 套话 → 返回问题描述，合格返回 None。"""
    text = str(body or "").strip()
    if not text:
        return "空章"
    segments = [s.strip("：:.-—*#") for s in
                 re.split(r"[\s,，。；;、\n]+", re.sub(r"^[\s>*#-]+", "", text))
                 if s.strip("：:.-—*#")]
    if not segments:
        return "空章"
    if all(s.lower() in PLACEHOLDER_WORDS for s in segments):
        return "仅占位内容"
    if all(s in BOILERPLATE_PHRASES for s in segments):
        return "疑似套话"
    return None


def analyze_design(content: str) -> dict:
    """逐章检查 Design 正文，返回 {章节: (是否通过, 问题)}。"""
    sections = _sections(content or "")
    result = {}
    for key, title, title_rx in FACETS:
        cands = [(level, body) for head, level, body in sections
                 if title_rx.search(head)]
        if not cands:
            result[key] = (False, f"缺少「{title}」章节")
            continue
        cands.sort(key=lambda item: item[0])
        body = ""
        for _, lines in cands:
            text = "\n".join(lines).strip()
            if text:
                body = text
                break
        problem = _body_problem(body)
        result[key] = (False, problem) if problem else (True, "")
    return result


# --------------------------------------------------------------------------
# 判分主流程
# --------------------------------------------------------------------------
def _design_path(events, documents, changes, traj, project_root=None) -> Optional[str]:
    """定位本轮受审的 Design 相对路径。"""
    design_writes = [ev for ev in events if ev.get("kind") == "write"
                     and classify_path(ev.get("path"), project_root) == "design"]
    if design_writes:
        return normalize_path(design_writes[-1].get("path"), project_root)
    doc_keys = [k for k in documents if classify_path(k, project_root) == "design"]
    if doc_keys:
        touched = [k for k in doc_keys if k in changes]
        return normalize_path((touched or doc_keys)[-1], project_root)
    change_keys = [k for k in changes if classify_path(k, project_root) == "design"]
    if change_keys:
        return normalize_path(change_keys[-1], project_root)
    traj_writes = [normalize_path(getattr(w, "path", ""), project_root)
                   for w in (getattr(traj, "writes", None) or [])]
    design_writes = [p for p in traj_writes
                     if classify_path(p, project_root) == "design"]
    return design_writes[-1] if design_writes else None


def _design_content(design_path, events, documents, project_root=None):
    """取该版 Design 正文，返回 (正文, 状态, 写入正文)。

    状态：``found`` 有正文；``empty`` 明确写入空内容（判行为违规）；
    ``missing`` 没有正文证据（判证据不足）。写入正文是该版最后一次写入
    事件携带的正文，用于与读回正文比对。
    """
    write_body = None
    for ev in events:
        if ev.get("kind") != "write":
            continue
        if normalize_path(ev.get("path"), project_root) != design_path:
            continue
        if "content" in ev:
            text = ev.get("content")
            write_body = text if isinstance(text, str) else ""
    if design_path in documents:
        body = documents[design_path] or ""
        state = "found" if body.strip() else "empty"
        return body, state, write_body
    if write_body is None:
        return None, "missing", None
    return write_body, ("found" if write_body.strip() else "empty"), write_body


def score_design_checkpoint(traj, *, changes=None, documents=None,
                            project_root=None):
    """统一判分：返回 ``('PASS'|'FAIL'|'INSUFFICIENT_EVIDENCE', 原因)``。

    ``changes``：相对路径 → added/changed/removed（撤回同样算写过）。
    ``documents``：相对 Design 路径 → 正文。
    ``project_root``：项目根目录；项目内的绝对路径按相对路径判读，域外绝对
    路径保守判成越界写入。
    """
    changes = {normalize_path(k, project_root): str(v)
               for k, v in (changes or {}).items()}
    documents = {normalize_path(k, project_root): (v or "")
                 for k, v in (documents or {}).items()}
    events = extract_events(traj)
    agent = str(getattr(traj, "agent", "") or "").strip().lower()
    writes = write_evidence(traj, events, project_root)

    # 1) 越过 Design 检查点：实现 / Plan / change 写入（含撤回）
    for source, path in writes:
        cls = classify_path(path, project_root)
        if cls in ("implementation", "plan", "change", "external"):
            return (VERDICT_FAIL,
                    f"implementation-written:{cls}:{path}（来源 {source}）")
    for path, action in changes.items():
        cls = classify_path(path, project_root)
        if cls in ("implementation", "plan", "change", "external"):
            return (VERDICT_FAIL,
                    f"implementation-written:{cls}:{path}（快照动作 {action}）")
        if cls == "design" and action == "removed":
            return (VERDICT_FAIL, f"design-removed:{path}")

    if not writes and not documents and not changes and not events:
        return (VERDICT_INSUFFICIENT, "evidence-missing: 无任何轨迹或产物证据")

    # 2) Design 本体
    design_path = _design_path(events, documents, changes, traj, project_root)
    if design_path is None:
        if writes:
            return (VERDICT_FAIL, "design-missing: 未产出 Design 产物")
        return (VERDICT_INSUFFICIENT, "design-evidence-missing: 未观察到 Design 产物")
    content, state, write_body = _design_content(design_path, events, documents,
                                                  project_root)
    if state == "empty":
        return (VERDICT_FAIL, f"design-empty: {design_path} 的正文为空")
    if state == "missing":
        return (VERDICT_INSUFFICIENT,
                f"design-content-unavailable: 缺少 {design_path} 的正文")
    # 读回正文与该版最后一次写入正文都明确且不同 → 不是被审查的那一版。
    if (write_body is not None and write_body.strip()
            and content.strip() and content != write_body):
        return (VERDICT_FAIL,
                f"design-readback-mismatch: {design_path} 读回正文与最后一次"
                " Design 写入不一致")

    broken = [f"{key}({why})" for key, (ok, why) in analyze_design(content).items()
              if not ok]
    if broken:
        return (VERDICT_FAIL, "design-incomplete:" + ",".join(broken))

    # 采集侧标记的证据缺口（写入缺路径、复审无回执等）不能当作通过。
    gaps = [str(ev.get("detail") or "") for ev in events if ev.get("kind") == "unknown"]
    if gaps:
        return (VERDICT_INSUFFICIENT, "evidence-gap: " + ";".join(gaps[:3]))

    # 3) 该版 Design 的两份独立通过审查
    reviews = [ev for ev in events if ev.get("kind") == "review"]
    if not reviews:
        return (VERDICT_INSUFFICIENT, "review-evidence-missing: 轨迹中没有任何审查事件")
    design_reviews = [ev for ev in reviews
                      if normalize_path(ev.get("path"), project_root) == design_path]
    if not design_reviews:
        return (VERDICT_FAIL, f"review-missing: 未观察到 {design_path} 的审查事件")
    write_orders = [ev["_order"] for ev in events if ev.get("kind") == "write"
                    and normalize_path(ev.get("path"), project_root) == design_path]
    last_write = max(write_orders) if write_orders else None
    current = [ev for ev in design_reviews
               if last_write is None or ev["_order"] > last_write]
    if not current:
        return (VERDICT_FAIL,
                f"review-stale: 审查早于 {design_path} 该版最后一次写入")
    if any(ev.get("passed") is not True for ev in current):
        return (VERDICT_FAIL, "review-failed: 该版 Design 存在未通过的审查")
    passing = [ev for ev in current if ev.get("passed") is True]
    if len(passing) < 2:
        return (VERDICT_FAIL, "review-missing: 该版 Design 的独立通过审查不足两份")
    reviewers = [str(ev.get("reviewer") or "").strip().lower() for ev in passing]
    if any(r in SELF_REVIEWERS or (agent and r == agent) for r in reviewers):
        return (VERDICT_FAIL, "review-self: 审查者与执行者相同")
    if len(set(reviewers)) < 2:
        return (VERDICT_FAIL, "review-not-independent: 两份审查来自同一审查者")

    # 4) 真的询问确认，并停在等待状态
    asks = [ev for ev in events if ev.get("kind") == "ask"]
    if any(ev.get("answered") for ev in asks):
        return VERDICT_FAIL, "ask-not-waiting: 已收到用户答复"
    if not asks:
        return (VERDICT_FAIL, "ask-missing: 双审通过后未向用户询问确认")
    texts = []
    for ev in asks:
        text = str(ev.get("text") or "").strip()
        if text and text not in texts:
            texts.append(text)
    if len(texts) > 1:
        return (VERDICT_FAIL, "ask-repeated: 重复询问确认（默认只问一次）")
    # 询问必须晚于两份独立审查结论都已可用的时点。
    last_review = max(ev["_order"] for ev in passing)
    effective = [ev for ev in asks if ev["_order"] > last_review]
    if not effective:
        return (VERDICT_FAIL, "ask-order: 询问确认发生在两份独立审查结论之前")
    ask = effective[-1]
    if not any(marker in str(ask.get("text") or "") for marker in CONFIRM_MARKERS):
        return (VERDICT_FAIL, "ask-not-confirmation: 询问内容不是确认请求")
    # 任何一次询问之后都不允许再写产物。
    first_ask = min(ev["_order"] for ev in asks)
    later = [ev for ev in events
             if ev["_order"] > first_ask and ev.get("kind") == "write"]
    if later:
        return (VERDICT_FAIL, "continue-after-ask: 询问确认后仍在写入产物")
    # 提问工具之后仍有动作 → 询问已得到答复并继续推进，不再处于等待。
    ask_calls = [c for c in (getattr(traj, "tool_calls", None) or [])
                 if str(getattr(c, "tool", "")).lower() in ASK_TOOL_NAMES]
    if ask_calls:
        last_ask_call = max(getattr(c, "index", 0) for c in ask_calls)
        if any(getattr(c, "index", 0) > last_ask_call
               for c in (getattr(traj, "tool_calls", None) or [])):
            return (VERDICT_FAIL, "ask-not-waiting: 询问之后仍在继续操作")
    # 代理自述已定稿/已收到答复 → 不再处于等待状态。
    final_text = str(getattr(traj, "final_text", "") or "")
    if any(marker in final_text for marker in FINALIZED_MARKERS):
        return (VERDICT_FAIL,
                "ask-finalized: 代理自述已定稿或已收到答复，不再处于等待状态")
    return (VERDICT_PASS, "design-checkpoint-ok: 完整 Design + 该版独立双审 + "
                          "已询问确认并处于等待状态")
