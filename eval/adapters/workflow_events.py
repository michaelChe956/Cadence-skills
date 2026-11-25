"""原生工作流证据采集（专项修复 P3）：直接解析原始 JSONL 产出有序事件。

trajectory.workflow_events（list[dict]，列表次序 = transcript 观察次序），与既有
writes/tool_calls 并用，供 scorer 判定真实写入 / 独立复审 / 用户确认 / 证据缺口。

事件契约（controller/判分侧共享）：
  {"kind": "write", "path": str[, "content": str]}
      content 仅在完整 Write 工具正文可观察时携带——键存在且为空串表示
      “写了空 Design”（判 FAIL），键不存在表示证据不足（Edit/apply_patch/
      bash 写入不带 content），空与缺严格区分；
  {"kind": "review", "reviewer": str, "path": str, "passed": bool}
      仅来自真实子代理/审查工具派工的成功返回，且关联派工输入中的 Design
      路径；reviewer 为独立调用身份（subagent_type/reviewer/agent/工具名），
      正文里出现角色名称不构成独立审查证据；
  {"kind": "ask", "text": str}
      明确面向用户确认 Design 的实际终端提问 / ask 工具；含等待态——
      最后一条 assistant/result 直接提问后会话停在原地，不要求其后必须
      跟真实用户回复；中间的“稍后会询问/我已询问”属代理自述，不算；
  {"kind": "unknown", "detail": str}
      写入/审查证据有重大缺失时的安全标识。
事件可携带附加键：summary（命令/结论摘要）；已通知 controller。

证据边界（一律从严，拒绝伪造）：
  - 用户输入 / 工具回执 / 代理自述三分：ask 只认 ask 工具调用、获真实用户
    回复的代理文本提问、或会话终点的等待态提问；review 只认派工调用
    tool_result 正文里的明确通过/不通过（结构化 passed/verdict 或明文结论，
    否定词优先防“未发现问题”误判）；assistant 自述一律不产事件。
  - 最终 result 行回显与 assistant 文本重复时不重复计提问。
  - bash 的显式写入和工作树恢复按路径留痕，间接目标或未知命令产生
    shell-effects-unobserved，已知的只读命令继续参与正常判分。

四端真实 schema（复用既有适配器口径，本模块不反向 import 适配器避免环）：
  claude stream-json/session（kimi 的 Claude-compatible 流同构复用）、
  codex rollout+stdout、pi session（omp 同格式；Docker --mode json 的
  message_start/update/delta 不重复计入，message_end 包裹视作完整消息）、
  kimi wire.jsonl 与 openai 分片（仅结构可辨时提取，残缺参数安全标 unknown）。
"""
import getopt
import json
import posixpath
import re
import shlex
from collections import deque
from typing import Iterable, Optional

WRITE_TOOLS = {"write"}
EDIT_TOOLS = {"edit", "multiedit", "notebookedit"}
APPLY_PATCH_TOOLS = {"apply_patch", "apply_model_patch"}
BASH_TOOLS = {"bash", "exec_command", "exec", "shell", "local_shell_call", "run_command"}
ASK_TOOLS = {"ask", "ask_user", "askuser", "exitplanmode", "requestinput"}
DISPATCH_TOOLS = {"task", "agent", "subagent", "spawn", "dispatch", "collab", "call"}

# 路径 token：排除空白/引号/括号/中英文标点，兼容 CJK 文件名（导出公开目录.md）。
_MD_PATH = re.compile(r"[^\s\"'<>()[）(；;，,。:：！?？`]+\.(?:md|markdown)\b", re.I)
_REVIEW_HINTS = ("review", "审查", "复审", "reviewer")
_ASK_TOPIC_HINTS = ("design", "设计", "方案", "spec", "规格", "plan", "确认",
                    "confirm", "approve", "是否")
# 代理自述话术（“已询问/稍后会询问”）不构成实际提问。
_NARRATION_PATTERNS = (r"已(经)?(询问|问过|提问)", r"稍后(会|再)(询问|问|提问)",
                       r"\basked\b", r"\bwill ask\b")
# 否定词优先于肯定词，防“未发现问题/无需修改”被 FAIL 误吞。
_FAIL_PATTERNS = (r"\bfail(?:ed|ing|ure)?\b", r"不通过", r"未通过", r"拒绝",
                  r"需要修改", r"must\s+fix", r"blocking", r"(?<!no )issues found",
                  r"(?<![未没无])发现问题", r"存在问题", r"❌")
# 等待态（无用户回复佐证）文本提问必须自带明确确认措辞，否则不认。
_CONFIRM_PHRASES = ("确认", "同意", "继续", "可以吗", "定稿", "approve",
                    "confirm", "proceed")
_PASS_PATTERNS = (r"\bpass(?:ed|ing)?\b", r"(?<![不未])通过", r"\blgtm\b", r"approved",
                  r"✅", r"无问题", r"没有问题", r"未发现问题", r"合格", r"达标",
                  r"无需修改")
_PASS_WORDS = {"pass", "passed", "approve", "approved", "lgtm", "通过"}
_FAIL_WORDS = {"fail", "failed", "reject", "rejected", "error", "blocked", "不通过", "未通过"}
# 保留引号，只有裸露的管道、分隔符和重定向才是 shell 操作符。
_SHELL_TOKEN = re.compile(r'''
    \#[^\n]*                                      # 行尾注释
    | (?P<process>[<>]\()                        # 进程替换的副作用需要额外证据
    | (?P<redir>\d*(?:<<<|<<-?|<>|<&|<|>>|>\||>&|>)|&>>?)
    | (?P<end>[;&|\n]+)                           # 命令分隔符、管道
    | (?:'[^']*'|"(?:\\.|[^"\\])*"|\\.|[^\s'"\\;&|<>])+  # 一个 shell 参数
    | \S
''', re.VERBOSE)
_READ_ONLY_COMMANDS = {'cat', 'ls', 'pwd', 'head', 'tail', 'wc', 'grep', 'echo',
                       'printf', 'test', '[', 'true', 'false'}
_READ_ONLY_GIT = {'status', 'diff', 'show', 'log', 'ls-files', 'ls-tree', 'rev-parse',
                  'rev-list', 'describe', 'show-ref', 'version', 'cat-file', 'blame'}
_PATCH_FILE = re.compile(r"^\*\*\* (?:Add|Update) File: (.+)$", re.I | re.M)
_DEVNULL = "/dev/null"
# pi 顺序配对下的硬错误词（窄口径：审查结论里的“拒绝”交给 verdict 解析）。
_PI_ERROR_MARKERS = ("permission", "denied", "错误：", "error:")


def _first_str(*values) -> Optional[str]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return None


def _result_text(content) -> str:
    """提取 tool_result / toolResult 正文（字符串或 text 项列表）。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(item["text"] for item in content
                         if isinstance(item, dict) and isinstance(item.get("text"), str))
    return ""


def _parse_json_maybe(value) -> Optional[dict]:
    if isinstance(value, str):
        try:
            data = json.loads(value)
        except ValueError:
            return None
        return data if isinstance(data, dict) else None
    return value if isinstance(value, dict) else None


def _literal_targets(operands, directory=''):
    """记录字面路径，用 None 标出需要展开或另行读取的目标。"""
    if any(c in directory for c in '$`*?[]{}') or directory.startswith('~'):
        return [None]
    paths = []
    for path in operands:
        if (not path or path == '-' or posixpath.basename(path) in ('', '.', '..')
                or path.startswith(('~', ':')) or any(c in path for c in '$`*?[]{}')):
            paths.append(None)
        else:
            paths.append(posixpath.join(directory, path))
    return paths or [None]


def _git_write_paths(args):
    global_opts, args = getopt.getopt(args, 'C:', ['no-pager', 'no-optional-locks', 'literal-pathspecs', 'version'])
    directory = ''
    for flag, value in global_opts:
        if flag == '-C':
            directory = posixpath.join(directory, value)
    if not args:
        return []
    verb, args = args[0], args[1:]
    options = args[:args.index('--')] if '--' in args else args
    if verb in _READ_ONLY_GIT:
        for i, opt in enumerate(options):
            if opt == '--output':
                return _literal_targets(options[i + 1:i + 2], directory)
            if opt.startswith('--output='):
                return _literal_targets([opt.partition('=')[2]], directory)
        return []
    if verb == 'restore':
        opts, targets = getopt.gnu_getopt(args, 's:SWq', ['source=', 'staged', 'worktree', 'quiet',
                                                           'ours', 'theirs', 'merge', 'overlay', 'no-overlay'])
        flags = {flag for flag, _ in opts}
        if flags.intersection({'-S', '--staged'}) and not flags.intersection({'-W', '--worktree'}):
            return []
    elif verb == 'checkout' and '--' in args:
        # 有明确路径分隔符时才按文件恢复。切换分支影响的文件由工作树决定。
        targets = args[args.index('--') + 1:]
    else:
        return [None]
    return _literal_targets(targets, directory)


def _command_write_paths(words):
    if not words:
        return []
    program, args = posixpath.basename(words[0]), words[1:]
    try:
        if program == 'git':
            return _git_write_paths(args)
        if program == 'truncate':
            _, targets = getopt.gnu_getopt(args, 'cor:s:', ['no-create', 'io-blocks', 'reference=', 'size='])
            return _literal_targets(targets)
    except getopt.GetoptError:
        return [None]
    operands = [arg for arg in args if not arg.startswith('-')]
    if program in {'rm', 'unlink', 'touch', 'mv', 'tee'}:
        return _literal_targets(operands) if operands or program != 'tee' else []
    if program in {'cp', 'install', 'ln'} or (program == 'sed' and any(a.startswith('-i') for a in args)):
        return _literal_targets(operands[-1:])
    if program in _READ_ONLY_COMMANDS or (program == 'rg' and not any(a.startswith('--pre') for a in args)):
        return []
    return [None]


def _bash_write_paths(command: str) -> list:
    """按 shell 执行顺序收集写入路径，无法定位的副作用用 None 表示。"""
    if not isinstance(command, str) or not command.strip():
        return [None]
    paths, words = [], []
    redir = None
    for match in _SHELL_TOKEN.finditer(command):
        if match.lastgroup == 'process':
            return paths + [None]
        token = match.group()
        if token.startswith('#'):
            continue
        if match.lastgroup == 'end':
            paths.extend(_command_write_paths(words))
            words.clear()
        elif match.lastgroup == 'redir':
            redir = token.lstrip('0123456789')
            if redir.startswith('<<'):
                # here-doc 正文是输入数据，不能把其中的行当作 shell 命令。
                if words == ['apply_patch'] and '*** Begin Patch' in command:
                    paths.extend(_patch_write_paths(command) or [None])
                else:
                    paths.extend(_command_write_paths(words))
                    paths.append(None)
                return [path for path in paths if path != _DEVNULL]
        else:
            try:
                word = shlex.split(token)[0]
            except (IndexError, ValueError):
                return paths + [None]
            if '$(' in token or '`' in token:
                paths.append(None)
            if redir is None:
                words.append(word)
            elif redir not in ('<', '<&') and not (redir == '>&' and (word.isdigit() or word == '-')):
                paths.extend(_literal_targets([word]))
            redir = None
    paths.extend(_command_write_paths(words))
    if redir is not None:
        paths.append(None)
    return [path for path in paths if path != _DEVNULL]


def _patch_write_paths(patch: Optional[str]) -> list:
    if not patch:
        return []
    return [path.strip() for path in _PATCH_FILE.findall(patch)]


def _summary_of(value) -> Optional[str]:
    if isinstance(value, str) and value.strip():
        return value.strip()[:100]
    return None


def _structured_verdict(body: str) -> tuple:
    """结构化结论 {"passed":bool}/{"verdict":"pass"}；返回 (结论, 摘要)。"""
    text = body.strip()
    if not (text.startswith("{") and text.endswith("}")):
        return None, None
    doc = _parse_json_maybe(text)
    if doc is None:
        return None, None
    for key in ("passed", "pass", "approved", "is_pass"):
        if isinstance(doc.get(key), bool):
            return doc[key], _summary_of(doc.get("summary"))
    verdict = doc.get("verdict") or doc.get("status") or doc.get("result")
    if isinstance(verdict, str):
        low = verdict.strip().lower()
        if low in _PASS_WORDS:
            return True, _summary_of(doc.get("summary"))
        if low in _FAIL_WORDS:
            return False, _summary_of(doc.get("summary"))
    return None, None


def _verdict_from_text(body: str) -> Optional[bool]:
    """明文结论：FAIL 词先于 PASS 词（否定优先），无明确结论返回 None。"""
    low = body.lower()
    for pattern in _FAIL_PATTERNS:
        if re.search(pattern, low):
            return False
    for pattern in _PASS_PATTERNS:
        if re.search(pattern, low):
            return True
    return None


def _design_path(*texts) -> Optional[str]:
    """从派工输入抽 Design 路径：优先含 design 的 .md，退而求其次任意 .md。"""
    found: list = []
    for text in texts:
        if isinstance(text, str):
            found.extend(_MD_PATH.findall(text))
    for path in found:
        if "design" in path.lower():
            return path
    return found[0] if found else None


def _dispatch_text(args: dict) -> str:
    """派工输入可关联文本：描述/指令 + 显式目标路径字段。"""
    parts = []
    for key in ("description", "prompt", "task", "question", "text", "subject",
                "summary", "instructions"):
        if isinstance(args.get(key), str):
            parts.append(args[key])
    for key in ("path", "file_path", "target", "target_path", "design_path"):
        if isinstance(args.get(key), str):
            parts.append(args[key])
    return "\n".join(parts)


def _reviewer_of(raw_name: str, args: dict) -> str:
    """独立调用身份：subagent_type/reviewer/agent 优先，退回原始工具名。"""
    for key in ("subagent_type", "reviewer", "agent"):
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return raw_name or "unknown-reviewer"


def _is_review_dispatch(low: str, args: dict) -> bool:
    """是否复审派工：直接审查工具，或 Task/Agent 类派工带复审意图。"""
    if "review" in low or "审查" in low or "复审" in low:
        return True
    if low not in DISPATCH_TOOLS and not low.startswith(("task", "agent")):
        return False
    text = _dispatch_text(args).lower()
    identity = " ".join(str(args.get(key) or "")
                        for key in ("subagent_type", "reviewer", "agent")).lower()
    return any(hint in text or hint in identity for hint in _REVIEW_HINTS)


def _ask_text(args: dict) -> str:
    """ask 工具的问题正文：AskUserQuestion.questions 或常见单字段。"""
    parts = []
    questions = args.get("questions")
    if isinstance(questions, list):
        parts.extend(q["question"] for q in questions
                     if isinstance(q, dict) and isinstance(q.get("question"), str))
    for key in ("question", "text", "prompt", "plan", "message"):
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    return "；".join(parts)[:400]


class _Collector:
    """单轨迹事件收集器：调用位产 write/ask，回执位产 review/unknown。"""

    def __init__(self):
        self.events: list = []
        self.pending: dict = {}        # call_id → 复审派工记录（id 配对端）
        self.queue: deque = deque()    # pi 顺序配对队列：所有工具调用占位
        self.assistant_texts: list = []
        self.user_lines: set = set()
        self.last_activity_line = -1   # 最近一次代理动作（提问/工具调用）行号
        self._held: list = []          # (锚点, 事件, 行号, 已获用户回复)

    def tool(self, name: str, args, call_id, line_idx: int,
             sequential: bool = False) -> None:
        self.last_activity_line = max(self.last_activity_line, line_idx)
        low = (name or "").lower()
        args = args if isinstance(args, dict) else {}
        record = None
        if low in WRITE_TOOLS:
            path = _first_str(args.get("file_path"), args.get("path"),
                              args.get("notebook_path"))
            if path:
                event = {"kind": "write", "path": path}
                # content 键“存在且为空串”与“键不存在”语义不同：前者是写了
                # 空 Design（FAIL），后者是证据不足——严格区分，不可归一。
                if isinstance(args.get("content"), str):
                    event["content"] = args["content"]
                self.events.append(event)
            else:
                self.events.append({"kind": "unknown", "detail": "write-missing-path"})
        elif low in EDIT_TOOLS:
            path = _first_str(args.get("file_path"), args.get("path"),
                              args.get("notebook_path"))
            if path:
                self.events.append({"kind": "write", "path": path})
            else:
                self.events.append({"kind": "unknown", "detail": "write-missing-path"})
        elif low in APPLY_PATCH_TOOLS:
            paths = _patch_write_paths(_first_str(args.get("input"), args.get("patch")))
            if paths:
                for path in paths:
                    self.events.append(
                        {"kind": "write", "path": path, "summary": "apply_patch"})
            else:
                self.events.append({"kind": "unknown", "detail": "write-missing-path"})
        elif low in BASH_TOOLS:
            command = args.get("command") or args.get("cmd")
            if isinstance(command, list) and all(isinstance(part, str) for part in command):
                if len(command) == 3 and posixpath.basename(command[0]) in ('bash', 'sh') and command[1] in ('-c', '-lc'):
                    command = command[2]
                else:
                    command = shlex.join(command)
            for path in _bash_write_paths(command):
                if path is None:
                    self.events.append({"kind": "unknown", "detail": "shell-effects-unobserved"})
                else:
                    self.events.append({"kind": "write", "path": path, "summary": "bash: " + command.strip()[:60]})
        elif low in ASK_TOOLS or "askuser" in low or "ask_user" in low:
            # ask 工具调用本身即实际终端提问，回执只是答案。
            question = {"kind": "ask", "text": _ask_text(args)}
            self.events.append(question)
            record = {"question": question}
        elif _is_review_dispatch(low, args):
            record = {"reviewer": _reviewer_of(name, args),
                      "input_text": _dispatch_text(args)}
        if sequential:
            self.queue.append(record)
        elif record is not None and call_id is not None:
            self.pending[str(call_id)] = record

    def result(self, call_id: str, body: str, is_error: bool) -> None:
        record = self.pending.pop(call_id, None) if call_id else None
        if record is not None:
            self.review_result(record, body, is_error)

    def sequential_result(self, body: str) -> None:
        record = self.queue.popleft() if self.queue else None
        if record is not None:
            low = body.lower()
            is_error = any(marker in low for marker in _PI_ERROR_MARKERS)
            self.review_result(record, body, is_error)

    def review_result(self, record: dict, body: str, is_error: bool) -> None:
        if "question" in record:
            if not is_error and body.strip():
                record["question"]["answered"] = True
            elif is_error:
                self.events.append({"kind": "unknown", "detail": "ask-tool-failed"})
            return
        reviewer = record["reviewer"]
        if is_error:
            self.events.append({"kind": "unknown",
                                "detail": "review-error:" + reviewer,
                                "summary": body.strip()[:100]})
            return
        if not body.strip():
            self.events.append({"kind": "unknown", "detail": "review-empty-result"})
            return
        verdict, summary = _structured_verdict(body)
        if verdict is None:
            verdict = _verdict_from_text(body)
        if verdict is None:
            self.events.append({"kind": "unknown", "detail": "review-inconclusive",
                                "summary": body.strip()[:100]})
            return
        path = _design_path(record["input_text"])
        if not path:
            self.events.append({"kind": "unknown", "detail": "review-no-design-path",
                                "summary": body.strip()[:100]})
            return
        self.events.append({"kind": "review", "reviewer": reviewer,
                            "path": path, "passed": verdict,
                            "summary": summary if summary else body.strip()[:100]})

    def assistant_text(self, text: str, line_idx: int) -> None:
        """代理文本：候选提问先挂起，finish 时按资格回填原位。

        资格 = 其后存在真实用户消息（已获回复），或该提问即会话终点的
        等待态最后一问（其后无任何代理动作）；自述话术直接排除。
        """
        if isinstance(text, str):
            self.assistant_texts.append(text)
        self.last_activity_line = max(self.last_activity_line, line_idx)
        if not isinstance(text, str):
            return
        tail = text.strip()[-240:]
        low = tail.lower()
        if "?" not in tail and "？" not in tail:
            return
        if any(re.search(pattern, low) for pattern in _NARRATION_PATTERNS):
            return
        if not any(hint in low for hint in _ASK_TOPIC_HINTS):
            return
        answered = any(idx > line_idx for idx in self.user_lines)
        confirm_worded = any(phrase in low for phrase in _CONFIRM_PHRASES)
        self._held.append((len(self.events), {"kind": "ask", "text": tail[-200:]},
                           line_idx, answered, confirm_worded))

    def final_result_text(self, text, line_idx: int) -> None:
        """最终 result 行：回显 assistant 文本时不重复计提问。"""
        if not isinstance(text, str) or not text.strip():
            return
        stripped = text.strip()
        if any(seen and (stripped in seen or seen in stripped)
               for seen in self.assistant_texts):
            return
        self.assistant_text(stripped, line_idx)

    def finish(self) -> None:
        """会话结束：未返回的复审派工标 unknown，再按锚点回填合格提问。"""
        for record in list(self.pending.values()) + list(self.queue):
            if record is not None and "question" not in record:
                self.events.append({"kind": "unknown", "detail": "review-no-result"})
        merged: list = []
        held = sorted(self._held, key=lambda item: item[0])
        cursor = 0
        for idx, event in enumerate(self.events):
            while cursor < len(held) and held[cursor][0] <= idx:
                qualified = self._qualified(held[cursor])
                if qualified is not None:
                    merged.append(qualified)
                cursor += 1
            merged.append(event)
        while cursor < len(held):
            qualified = self._qualified(held[cursor])
            if qualified is not None:
                merged.append(qualified)
            cursor += 1
        self.events = merged

    def _qualified(self, held_item: tuple):
        _, event, line_idx, answered, confirm_worded = held_item
        # 已获真实用户回复；或会话终点的等待态提问（其后无任何代理动作），
        # 且自带明确确认措辞——“是否达到要求”式的自语不算面向用户的确认。
        if answered:
            return dict(event, answered=True)
        if line_idx == self.last_activity_line and confirm_worded:
            return event
        return None


def _is_claude_user_row(data: dict) -> bool:
    """claude 形态真实用户行：排除 tool_result 回执与 isMeta 注入。"""
    if data.get("type") != "user" or data.get("isMeta"):
        return False
    message = data.get("message")
    if not isinstance(message, dict):
        return False
    content = message.get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        has_receipt = any(isinstance(item, dict) and item.get("type") == "tool_result"
                          for item in content)
        has_text = any(isinstance(item, dict) and item.get("type") == "text"
                       for item in content)
        return has_text and not has_receipt
    return False


def _claude_row(collector: _Collector, data: dict, i: int) -> None:
    """claude stream-json 单行（assistant/user/result）；kimi 兼容流复用。"""
    dtype = data.get("type")
    if dtype == "assistant" and isinstance(data.get("message"), dict):
        content = data["message"].get("content")
        if not isinstance(content, list):
            return
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use":
                collector.tool(str(item.get("name") or ""), item.get("input"),
                               item.get("id"), i)
            elif item.get("type") == "text" and isinstance(item.get("text"), str):
                collector.assistant_text(item["text"], i)
    elif dtype == "user" and isinstance(data.get("message"), dict):
        content = data["message"].get("content")
        if not isinstance(content, list):
            return
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                collector.result(str(item.get("tool_use_id") or ""),
                                 _result_text(item.get("content")),
                                 bool(item.get("is_error")))
    elif dtype == "result":
        collector.final_result_text(data.get("result"), i)


def _walk_claude(collector: _Collector, rows: list) -> None:
    for i, data in enumerate(rows):
        if isinstance(data, dict) and _is_claude_user_row(data):
            collector.user_lines.add(i)
    for i, data in enumerate(rows):
        if isinstance(data, dict):
            _claude_row(collector, data, i)


def _walk_codex(collector: _Collector, rows: list) -> None:
    for i, data in enumerate(rows):
        if not isinstance(data, dict) or data.get("type") != "response_item":
            continue
        payload = data.get("payload")
        if not (isinstance(payload, dict) and payload.get("type") == "message"
                and payload.get("role") == "user"):
            continue
        content = payload.get("content")
        if isinstance(content, list) and any(
                isinstance(item, dict) and item.get("type") in ("input_text", "text")
                for item in content):
            collector.user_lines.add(i)
    for i, data in enumerate(rows):
        if not isinstance(data, dict):
            continue
        dtype = data.get("type")
        if dtype in ("item.started", "item.completed"):
            item = data.get("item")
            if dtype == "item.completed" and isinstance(item, dict):
                if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                    collector.assistant_text(item["text"], i)
                elif item.get("type") == "command_execution":
                    collector.tool("bash", {"command": item.get("command")}, None, i)
            continue
        if dtype == "event_msg":
            payload = data.get("payload")
            if isinstance(payload, dict) and payload.get("type") == "user_message":
                collector.user_lines.add(i)
            continue
        if dtype != "response_item":
            continue
        payload = data.get("payload")
        if not isinstance(payload, dict):
            continue
        ptype = payload.get("type")
        if ptype in ("function_call", "custom_tool_call", "local_shell_call"):
            if ptype == "custom_tool_call":
                raw_name = str(payload.get("name") or "")
                args = {"input": payload.get("input")}
            elif ptype == "local_shell_call":
                raw_name = "exec_command"
                action = payload.get("action")
                args = action if isinstance(action, dict) else {}
            else:
                raw_name = str(payload.get("name") or "")
                args = _parse_json_maybe(payload.get("arguments")) or {}
            collector.tool(raw_name, args, payload.get("call_id"), i)
        elif ptype == "function_call_output":
            parsed = _parse_json_maybe(payload.get("output"))
            if isinstance(parsed, dict):
                output = parsed.get("output")
                body = output if isinstance(output, str) else json.dumps(
                    parsed, ensure_ascii=False)
                is_error = parsed.get("error") is not None
            else:
                raw = payload.get("output")
                body = raw if isinstance(raw, str) else ""
                is_error = False
            collector.result(str(payload.get("call_id") or ""), body, is_error)
        elif ptype == "message" and payload.get("role") == "assistant":
            content = payload.get("content")
            if not isinstance(content, list):
                continue
            for item in content:
                if isinstance(item, dict) and item.get("type") in ("output_text", "text") \
                        and isinstance(item.get("text"), str):
                    collector.assistant_text(item["text"], i)


def _pi_row_is_message(data: dict) -> bool:
    """pi 行归类：json 模式 message_start/update/delta 不计，message_end 算完整消息。"""
    rtype = data.get("type")
    if rtype in ("message_start", "message_update", "message_delta"):
        return False
    if rtype == "message_end":
        rtype = "message"
    if rtype != "message":
        return False
    phase = str(data.get("phase") or data.get("event")
                or data.get("subtype") or "").lower()
    return phase not in ("start", "update", "delta")


def _walk_pi(collector: _Collector, rows: list) -> None:
    for i, data in enumerate(rows):
        if not isinstance(data, dict) or not _pi_row_is_message(data):
            continue
        message = data.get("message")
        if isinstance(message, dict) and message.get("role") == "user":
            collector.user_lines.add(i)
    for i, data in enumerate(rows):
        if not isinstance(data, dict) or not _pi_row_is_message(data):
            continue
        message = data.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        if message.get("role") == "assistant":
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "toolCall":
                    args = item.get("arguments")
                    collector.tool(str(item.get("name") or ""),
                                   args if isinstance(args, dict) else {},
                                   item.get("id"), i, sequential=True)
                elif item.get("type") == "text" and isinstance(item.get("text"), str):
                    collector.assistant_text(item["text"], i)
        elif message.get("role") == "toolResult":
            collector.sequential_result(_result_text(content))


def _openai_message(collector: _Collector, message: dict, i: int) -> None:
    """openai 完整 message 形态（非分片）：结构可辨，直接提取。"""
    tool_calls = message.get("tool_calls")
    if isinstance(tool_calls, list):
        for tc in tool_calls:
            if not isinstance(tc, dict):
                continue
            fn = tc.get("function")
            name = fn.get("name") if isinstance(fn, dict) else None
            raw_args = fn.get("arguments") if isinstance(fn, dict) else None
            collector.tool(str(name or ""), _parse_json_maybe(raw_args),
                           tc.get("id"), i)
    elif isinstance(message.get("content"), str):
        collector.assistant_text(message["content"], i)


def _walk_kimi(collector: _Collector, rows: list) -> None:
    for i, data in enumerate(rows):
        if not isinstance(data, dict):
            continue
        if data.get("type") == "context.append_message":
            message = data.get("message")
            if isinstance(message, dict) and message.get("role") == "user":
                collector.user_lines.add(i)
        elif _is_claude_user_row(data):
            collector.user_lines.add(i)
    openai_calls: dict = {}

    def _flush_openai_calls() -> None:
        # 分片聚合后统一落事件；参数残缺不可解析时由 tool() 安全标 unknown。
        for key in sorted(openai_calls):
            slot = openai_calls[key]
            collector.tool(slot["name"], _parse_json_maybe(slot["arguments"]),
                           slot["id"], slot["line"])
        openai_calls.clear()

    for i, data in enumerate(rows):
        if not isinstance(data, dict):
            continue
        dtype = data.get("type")
        if dtype == "context.append_loop_event":
            event = data.get("event")
            if not isinstance(event, dict):
                continue
            call_id = str(event.get("toolCallId") or "")
            if event.get("type") == "tool.call":
                args = event.get("args")
                collector.tool(str(event.get("name") or ""),
                               args if isinstance(args, dict) else {}, call_id, i)
            elif event.get("type") == "tool.result":
                result = event.get("result")
                result = result if isinstance(result, dict) else {}
                output = result.get("output")
                body = output if isinstance(output, str) else ""
                is_error = result.get("error") is not None or "error" in body.lower()
                collector.result(call_id, body, is_error)
        elif dtype == "context.append_message":
            message = data.get("message")
            if isinstance(message, dict) and message.get("role") == "assistant":
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text" \
                            and isinstance(item.get("text"), str):
                        collector.assistant_text(item["text"], i)
        elif dtype in ("assistant", "user", "result"):
            # Claude-compatible stream-json：与 claude 行同构。
            _claude_row(collector, data, i)
        elif isinstance(data.get("choices"), list):
            # openai 分片流：仅结构可辨时提取；文本分片不做提问判定。
            for choice in data["choices"]:
                if not isinstance(choice, dict):
                    continue
                message = choice.get("message")
                if isinstance(message, dict):
                    _openai_message(collector, message, i)
                    continue
                delta = choice.get("delta")
                if isinstance(delta, dict):
                    if isinstance(delta.get("content"), str) and delta["content"].strip():
                        collector.last_activity_line = max(
                            collector.last_activity_line, i)
                    for tc in delta.get("tool_calls") or []:
                        if not isinstance(tc, dict):
                            continue
                        index = tc.get("index") if isinstance(tc.get("index"), int) \
                            else len(openai_calls)
                        slot = openai_calls.setdefault(
                            index, {"id": None, "name": "", "arguments": "", "line": i})
                        slot["line"] = i
                        if isinstance(tc.get("id"), str) and not slot["id"]:
                            slot["id"] = tc["id"]
                        fn = tc.get("function")
                        if isinstance(fn, dict):
                            if isinstance(fn.get("name"), str) and not slot["name"]:
                                slot["name"] = fn["name"]
                            if isinstance(fn.get("arguments"), str):
                                slot["arguments"] += fn["arguments"]
                if choice.get("finish_reason") in ("tool_calls", "stop"):
                    _flush_openai_calls()
    _flush_openai_calls()


_WALKERS = {"claude": _walk_claude, "codex": _walk_codex,
            "pi": _walk_pi, "kimi": _walk_kimi}


def extract(agent: str, lines: Iterable[str]) -> list:
    """从原始 transcript 行提取有序工作流事件；未知端返回空表。"""
    walker = _WALKERS.get(agent)
    if walker is None:
        return []
    rows = []
    for raw in lines:
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            data = None
        rows.append(data if isinstance(data, dict) else None)
    collector = _Collector()
    walker(collector, rows)
    collector.finish()
    return collector.events
