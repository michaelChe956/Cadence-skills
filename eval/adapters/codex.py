"""codex 适配器：解析 rollout JSONL 并产出统一中间轨迹。

rollout 中 session_meta/turn_context 提供模型回读，response_item 承载工具调用；
工具名使用 base 的跨端别名表归一，工具输出仅回填对应调用的错误状态。
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from eval import ifmt
from eval.adapters import base

TOOL_PAYLOADS = ("function_call", "custom_tool_call", "local_shell_call")


def _parse_json_maybe(value):
    """解析 JSON 字符串；已解析的对象直接返回。"""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return None
    if isinstance(value, dict):
        return value
    return None


def _ts(value) -> Optional[float]:
    """把 ISO-8601 时间转换为时间戳；无法解析时返回空值。"""
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


def _command_digest(tool: str, args: dict) -> str:
    """按 codex 口径生成摘要，保留字符串命令全文并剥离 bash -lc 头。"""
    command = args.get("command")
    if isinstance(command, list):
        joined = " ".join(str(item) for item in command)
        if joined.startswith("bash -lc "):
            joined = joined[len("bash -lc "):]
        return joined
    if isinstance(command, str):
        # codex rollout 的字符串 command 已是命令正文，不再按 base 截取前三词。
        return command
    if isinstance(args.get("file_path"), str):
        return args["file_path"]
    return base.args_digest(tool, args)


class CodexAdapter(base.AgentAdapter):
    """codex stdout/rollout 适配器。"""

    name = "codex"
    capture = "stdout"

    def parse_stream(self, lines: Iterable[str]) -> ifmt.IntermediateTrajectory:
        traj = ifmt.IntermediateTrajectory(agent=self.name)
        pending = {}
        texts = []
        first_ts = last_ts = None
        sequence = 0

        for raw in lines:
            try:
                data = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if not isinstance(data, dict):
                continue

            timestamp = data.get("timestamp")
            stamp = _ts(timestamp)
            if stamp is not None:
                if first_ts is None:
                    first_ts = stamp
                    traj.started_at = timestamp
                last_ts = stamp

            dtype = data.get("type")
            payload = data.get("payload")
            if not isinstance(payload, dict):
                payload = {}

            # stdout 流（codex exec --json）格式：顶层 {"type":"item.completed",
            # "item":{...}}——rollout 格式之外的主流形态
            if data.get("type") in ("item.started", "item.completed"):
                item = data.get("item")
                if isinstance(item, dict):
                    if item.get("type") == "agent_message" and data.get("type") == "item.completed" \
                            and isinstance(item.get("text"), str):
                        texts.append(item["text"])
                    elif item.get("type") in ("command_execution", "function_call") \
                            and data.get("type") == "item.completed":
                        raw_name = item.get("type")
                        tool = base.normalize_tool(self.name, raw_name)
                        cmd = item.get("command")
                        digest = " ".join(str(cmd).split()[:3]) if isinstance(cmd, str) else ""
                        traj.tool_calls.append(ifmt.ToolCall(
                            index=sequence, tool=tool, raw_tool=str(raw_name or ""),
                            args_digest=digest, is_error=item.get("status") == "failed",
                            ts=timestamp if isinstance(timestamp, str) else None))
                        sequence += 1
                continue

            if dtype in ("session_meta", "turn_context"):
                model = payload.get("model")
                if isinstance(model, str) and model:
                    # turn_context 后值覆盖 session_meta，保持 turn 级最新口径。
                    traj.model_readback = model
                continue

            if dtype == "event_msg" and payload.get("type") == "error":
                errors = traj.settings_snapshot.setdefault("_infra_errors", [])
                errors.append(str(payload.get("message"))[:200])
                traj.infra_errors.append(str(payload.get("message"))[:200])
                continue

            if dtype != "response_item":
                continue

            item_type = payload.get("type")
            if item_type in TOOL_PAYLOADS:
                raw_name = payload.get("name")
                if not isinstance(raw_name, str) or not raw_name:
                    # local_shell_call 的部分 rollout 没有 name，按 exec_command 归一。
                    raw_name = "exec_command" if item_type == "local_shell_call" else ""
                tool = base.normalize_tool(self.name, raw_name)
                args = _parse_json_maybe(payload.get("arguments"))
                if not isinstance(args, dict):
                    args = {}
                call = ifmt.ToolCall(
                    index=sequence,
                    tool=tool,
                    raw_tool=raw_name,
                    args_digest=_command_digest(tool, args),
                    is_error=False,
                    ts=timestamp if isinstance(timestamp, str) else None,
                )
                traj.tool_calls.append(call)
                if tool in ("Edit", "Write") and isinstance(args.get("file_path"), str):
                    traj.writes.append(ifmt.WriteEvent(
                        at_index=sequence, path=args["file_path"]))
                call_id = payload.get("call_id")
                if call_id is not None:
                    pending[str(call_id)] = sequence
                sequence += 1
                continue

            if item_type == "function_call_output":
                call_id = payload.get("call_id")
                index = pending.get(str(call_id)) if call_id is not None else None
                raw_output = payload.get("output")
                parsed_output = _parse_json_maybe(raw_output)
                error_value = None
                body = ""
                if isinstance(parsed_output, dict):
                    error_value = parsed_output.get("error")
                    output_text = parsed_output.get("output")
                    # 只按 output 文本判错；不能因序列化对象含 error 键且值为 null 误判。
                    body = output_text if isinstance(output_text, str) else ""
                elif isinstance(raw_output, str):
                    # 非 JSON 输出不是主格式，但保留错误标记的容错解析。
                    body = raw_output
                has_error = bool(error_value) or "error" in body.lower()
                if index is not None and has_error:
                    for call in traj.tool_calls:
                        if call.index == index:
                            call.is_error = True
                            break
                continue

            if item_type == "message" and payload.get("role") == "assistant":
                content = payload.get("content")
                if isinstance(content, list):
                    for item in content:
                        if (isinstance(item, dict)
                                and item.get("type") in ("output_text", "text")
                                and isinstance(item.get("text"), str)):
                            texts.append(item["text"])

        if first_ts is not None and last_ts is not None:
            traj.duration_s = max(0.0, last_ts - first_ts)
        traj.final_text = "\n".join(texts)
        return traj

    def find_latest_session(self, home: Path, since_ts: float) -> Optional[Path]:
        """定位 since_ts 之后修改的最新 codex rollout 文件。"""
        latest = None
        latest_mtime = -1.0
        for path in home.glob(".codex/sessions/**/rollout-*.jsonl"):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if mtime >= since_ts and mtime > latest_mtime:
                latest = path
                latest_mtime = mtime
        return latest
