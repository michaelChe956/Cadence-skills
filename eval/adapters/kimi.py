"""kimi 适配器：wire.jsonl（protocol_version 1.4 实测锚点）。

模型回读：usage.record.model（usage 级，后值覆盖）> config.update.modelAlias。
工具事件：context.append_loop_event.event 的 tool.call / tool.result（按
`toolCallId` 配对）。Kimi 无公开 headless 文档——本适配器必须先经
`eval verify-kimi` 单端验证后才允许入矩阵（agents.json enabled 门）。
"""
import json
from pathlib import Path
from typing import Iterable, Optional

from eval import ifmt
from eval.adapters import base

ERROR_MARKERS = ("error", "permission", "denied", "错误", "拒绝")


class KimiAdapter(base.AgentAdapter):
    """kimi session 捕获适配器。"""

    name = "kimi"
    capture = "session"

    def parse_stream(self, lines: Iterable[str]) -> ifmt.IntermediateTrajectory:
        traj = ifmt.IntermediateTrajectory(agent=self.name)
        texts = []
        sequence = 0
        pending = {}

        for raw in lines:
            try:
                data = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(data, dict):
                continue

            dtype = data.get("type")
            if dtype == "metadata":
                protocol_version = data.get("protocol_version")
                if isinstance(protocol_version, str):
                    traj.cli_version = "wire/" + protocol_version
                continue

            if dtype == "config.update":
                model_alias = data.get("modelAlias")
                if isinstance(model_alias, str) and not traj.model_readback:
                    traj.model_readback = model_alias
                continue

            if dtype == "usage.record":
                model = data.get("model")
                if isinstance(model, str):
                    traj.model_readback = model
                continue

            if dtype == "context.append_loop_event":
                event = data.get("event")
                if not isinstance(event, dict):
                    continue
                event_type = event.get("type")
                call_id = str(event.get("toolCallId"))
                if event_type == "tool.call":
                    raw_name = event.get("name")
                    if not isinstance(raw_name, str):
                        raw_name = ""
                    tool = base.normalize_tool(self.name, raw_name)
                    args = event.get("args")
                    if not isinstance(args, dict):
                        args = {}
                    traj.tool_calls.append(ifmt.ToolCall(
                        index=sequence,
                        tool=tool,
                        raw_tool=raw_name,
                        args_digest=base.args_digest(tool, args),
                        is_error=False,
                    ))
                    if tool in ("Edit", "Write"):
                        path = args.get("path") or args.get("file_path")
                        if isinstance(path, str):
                            traj.writes.append(ifmt.WriteEvent(
                                at_index=sequence, path=path))
                    pending[call_id] = sequence
                    sequence += 1
                elif event_type == "tool.result":
                    index = pending.get(call_id)
                    result = event.get("result")
                    if not isinstance(result, dict):
                        result = {}
                    output = str(result.get("output", ""))
                    error = result.get("error")
                    error_text = str(error) if error is not None else ""
                    if index is None or not (error or "error" in output.lower()):
                        continue
                    call = next((item for item in traj.tool_calls
                                 if item.index == index), None)
                    if call is None:
                        continue
                    call.is_error = True
                    lowered_output = output.lower()
                    lowered_error = error_text.lower()
                    if any(marker in lowered_output or marker in lowered_error
                           for marker in ERROR_MARKERS):
                        traj.denials.append(ifmt.Denial(
                            at_index=index,
                            tool=call.tool,
                            reason=(error_text or output)[:200],
                            raw={"toolCallId": call_id,
                                 "content": output[:400]},
                        ))
                continue

            if dtype == "context.append_message":
                message = data.get("message")
                if not isinstance(message, dict) or message.get("role") != "assistant":
                    continue
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                texts.extend(item["text"] for item in content
                             if isinstance(item, dict)
                             and item.get("type") == "text"
                             and isinstance(item.get("text"), str))

        traj.final_text = "\n".join(texts)
        return traj

    def find_latest_session(self, home: Path, since_ts: float) -> Optional[Path]:
        """定位 since_ts 之后修改的最新 kimi wire.jsonl。"""
        latest = None
        latest_mtime = -1.0
        for path in home.glob(".kimi-code/sessions/**/agents/*/wire.jsonl"):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if mtime >= since_ts and mtime > latest_mtime:
                latest = path
                latest_mtime = mtime
        return latest
