"""claude 适配器：stream-json（-p stdout）与 session jsonl 同构解析。

字段锚点（本机 362 个真实 session 实测，2026-09-02）：
assistant.message.model（模型回读）/ content[].tool_use / user.tool_result.is_error
/ result.duration_ms / 行级 version（cli 版本）。
DENIAL_MARKERS 为启发式初值——Task 10 forensics 取证真实字段结构后校准。
"""
import json
from typing import Iterable

from eval import ifmt
from eval.adapters import base

DENIAL_MARKERS: tuple[str, ...] = ("permission", "denied", "not allowed", "权限", "拒绝")


def _tool_result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return ""


class ClaudeAdapter(base.AgentAdapter):
    name = "claude"
    capture = "stdout"
    DENIAL_MARKERS: tuple[str, ...] = DENIAL_MARKERS

    def parse_stream(self, lines: Iterable[str]) -> ifmt.IntermediateTrajectory:
        traj = ifmt.IntermediateTrajectory(agent=self.name)
        pending: dict[str, int] = {}
        texts: list[str] = []
        seq = 0
        for raw in lines:
            try:
                data = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if not isinstance(data, dict):
                continue
            if traj.cli_version is None and isinstance(data.get("version"), str):
                traj.cli_version = data["version"]
            if not traj.started_at and isinstance(data.get("timestamp"), str):
                traj.started_at = data["timestamp"]

            dtype = data.get("type")
            message = data.get("message")
            if dtype == "system" and data.get("subtype") == "init":
                if traj.cli_version is None and isinstance(data.get("version"), str):
                    traj.cli_version = data["version"]
                continue
            if dtype == "assistant" and isinstance(message, dict):
                if not traj.model_readback and isinstance(message.get("model"), str):
                    traj.model_readback = message["model"]
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "tool_use":
                        raw_name = str(item.get("name") or "")
                        tool = base.normalize_tool(self.name, raw_name)
                        inp = item.get("input") if isinstance(item.get("input"), dict) else {}
                        traj.tool_calls.append(ifmt.ToolCall(
                            index=seq,
                            tool=tool,
                            raw_tool=raw_name,
                            args_digest=base.args_digest(tool, inp),
                            is_error=False,
                        ))
                        if (tool in ("Edit", "Write", "NotebookEdit")
                                and isinstance(inp.get("file_path"), str)):
                            traj.writes.append(ifmt.WriteEvent(
                                at_index=seq, path=inp["file_path"]))
                        tool_id = item.get("id")
                        if tool_id is not None:
                            pending[str(tool_id)] = seq
                        seq += 1
                    elif (item.get("type") == "text"
                          and isinstance(item.get("text"), str)):
                        texts.append(item["text"])
            elif dtype == "user" and isinstance(message, dict):
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                for item in content:
                    if not isinstance(item, dict) or item.get("type") != "tool_result":
                        continue
                    idx = pending.get(str(item.get("tool_use_id")))
                    body = _tool_result_text(item.get("content"))
                    is_error = bool(item.get("is_error"))
                    if idx is None or not is_error:
                        continue
                    for call in traj.tool_calls:
                        if call.index == idx:
                            call.is_error = True
                            break
                    if any(marker in body.lower() for marker in DENIAL_MARKERS):
                        tool = next((call.tool for call in traj.tool_calls
                                     if call.index == idx), "")
                        traj.denials.append(ifmt.Denial(
                            at_index=idx,
                            tool=tool,
                            reason=body[:200],
                            raw={"tool_use_id": item.get("tool_use_id"),
                                 "content": body[:400]},
                        ))
            elif dtype == "result":
                duration_ms = data.get("duration_ms")
                if isinstance(duration_ms, (int, float)):
                    traj.duration_s = duration_ms / 1000.0
                if isinstance(data.get("result"), str):
                    texts.append(data["result"])
        traj.final_text = "\n".join(texts)
        return traj
