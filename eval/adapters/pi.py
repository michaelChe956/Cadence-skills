"""pi 适配器：解析 session.jsonl 并产出统一中间轨迹。

session 行提供版本与开始时间，model_change 提供模型回读/漂移证据，assistant
消息中的 toolCall 与 toolResult 按顺序配对。
"""
import json
from pathlib import Path
from typing import Iterable, Optional

from eval import ifmt
from eval.adapters import base

ERROR_MARKERS = ("error", "failed", "permission", "denied", "错误", "拒绝")


def _result_text(content) -> str:
    """提取 toolResult 内容中的文本。"""
    if not isinstance(content, list):
        return ""
    return "\n".join(
        item["text"] for item in content
        if isinstance(item, dict) and isinstance(item.get("text"), str))


class PiAdapter(base.AgentAdapter):
    """pi session 捕获适配器。"""

    name = "pi"
    capture = "session"

    def parse_stream(self, lines: Iterable[str]) -> ifmt.IntermediateTrajectory:
        traj = ifmt.IntermediateTrajectory(agent=self.name)
        texts = []
        pending = []
        sequence = 0

        for raw in lines:
            try:
                data = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if not isinstance(data, dict):
                continue

            dtype = data.get("type")
            if dtype == "session":
                if not traj.started_at and isinstance(data.get("timestamp"), str):
                    traj.started_at = data["timestamp"]
                if traj.cli_version is None and isinstance(data.get("version"), str):
                    traj.cli_version = data["version"]
                continue

            if dtype == "model_change":
                model_id = data.get("modelId")
                if isinstance(model_id, str) and model_id:
                    traj.model_changes.append(model_id)
                    if not traj.model_readback:
                        traj.model_readback = model_id
                continue

            if dtype != "message" or not isinstance(data.get("message"), dict):
                continue
            message = data["message"]
            role = message.get("role")
            content = message.get("content")
            if not isinstance(content, list):
                continue

            if role == "assistant":
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "toolCall":
                        raw_name = item.get("name")
                        if not isinstance(raw_name, str):
                            raw_name = ""
                        tool = base.normalize_tool(self.name, raw_name)
                        args = item.get("arguments")
                        if not isinstance(args, dict):
                            args = {}
                        call = ifmt.ToolCall(
                            index=sequence,
                            tool=tool,
                            raw_tool=raw_name,
                            args_digest=base.args_digest(tool, args),
                            is_error=False,
                            ts=data.get("timestamp") if isinstance(data.get("timestamp"), str) else None,
                        )
                        traj.tool_calls.append(call)
                        path = args.get("path") or args.get("file_path")
                        if tool in ("Edit", "Write") and isinstance(path, str):
                            traj.writes.append(ifmt.WriteEvent(
                                at_index=sequence, path=path))
                        pending.append(sequence)
                        sequence += 1
                    elif (item.get("type") == "text"
                          and isinstance(item.get("text"), str)):
                        texts.append(item["text"])
                continue

            if role != "toolResult":
                continue
            body = _result_text(content)
            if not pending:
                continue
            # pi 轨迹采用最近未闭合调用的顺序配对。
            index = pending.pop(0)
            lowered = body.lower()
            if not any(marker in lowered for marker in ERROR_MARKERS):
                continue
            call = next((item for item in traj.tool_calls if item.index == index), None)
            if call is None:
                continue
            call.is_error = True
            traj.denials.append(ifmt.Denial(
                at_index=index,
                tool=call.tool,
                reason=body[:200],
                raw={"content": body[:400]},
            ))

        traj.final_text = "\n".join(texts)
        return traj

    def find_latest_session(self, home: Path, since_ts: float) -> Optional[Path]:
        """定位 since_ts 之后修改的最新 pi session 文件。"""
        latest = None
        latest_mtime = -1.0
        for path in home.glob(".pi/agent/sessions/**/run-*/session.jsonl"):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if mtime >= since_ts and mtime > latest_mtime:
                latest = path
                latest_mtime = mtime
        return latest
