"""适配器协议与跨端工具名归一（eval-trajectory-scoring R1：断言器只吃中间格式）。"""
import abc
from pathlib import Path
from typing import Iterable, Optional

from eval import ifmt

AGENTS = ("claude", "codex", "pi", "kimi")

TOOL_ALIASES = {
    "codex": {"exec_command": "Bash", "exec": "Bash", "shell": "Bash",
              "apply_patch": "Edit", "view": "Read", "read_file": "Read"},
    "pi": {"bash": "Bash", "read": "Read", "write": "Write",
           "edit": "Edit", "grep": "Grep", "glob": "Glob"},
    "claude": {},
    "kimi": {},
}


def normalize_tool(agent: str, raw_tool: str) -> str:
    return TOOL_ALIASES.get(agent, {}).get(raw_tool, raw_tool)


def args_digest(tool: str, inp: dict) -> str:
    """参数摘要：Bash→命令头前 3 词；文件写入→路径；其余→入参键名。"""
    if not isinstance(inp, dict):
        return ""
    if tool == "Bash" and isinstance(inp.get("command"), str):
        return " ".join(inp["command"].split()[:3])
    if tool in ("Edit", "Write") and isinstance(inp.get("file_path"), str):
        return inp["file_path"]
    return ",".join(sorted(map(str, inp.keys()))[:5])


class AgentAdapter(abc.ABC):
    """四端适配器协议：parse_stream 只消费文本行，产出中间格式。"""

    name: str = ""
    capture: str = "stdout"  # stdout（标准输出）或 session（会话文件）

    @abc.abstractmethod
    def parse_stream(self, lines: Iterable[str]) -> ifmt.IntermediateTrajectory:
        ...

    def parse_file(self, path: Path) -> ifmt.IntermediateTrajectory:
        traj = self.parse_stream(
            line for line in path.read_text(encoding="utf-8",
                                            errors="replace").splitlines() if line.strip())
        traj.source_path = str(path)
        return traj

    def find_latest_session(self, home: Path, since_ts: float) -> Optional[Path]:
        return None  # stdout 捕获端无需定位 session 文件
