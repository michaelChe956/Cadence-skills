"""统一中间格式：四端轨迹的判分唯一入口数据契约（eval-trajectory-scoring R1）。

模型标识一律 transcript 实测回读（非启动参数）；settings_snapshot 携带
fixture .claude/settings.json 受管区块快照，供 deny 双分类 gate 判归属。
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ToolCall:
    index: int
    tool: str
    raw_tool: str
    args_digest: str
    is_error: bool
    ts: Optional[str] = None


@dataclass
class Denial:
    at_index: int
    tool: str
    reason: str
    raw: dict


@dataclass
class WriteEvent:
    at_index: int
    path: str


@dataclass
class IntermediateTrajectory:
    agent: str
    model_readback: str = ""
    model_changes: list = field(default_factory=list)
    cli_version: Optional[str] = None
    tool_calls: list = field(default_factory=list)
    denials: list = field(default_factory=list)
    writes: list = field(default_factory=list)
    final_text: str = ""
    started_at: str = ""
    duration_s: float = 0.0
    settings_snapshot: dict = field(default_factory=dict)
    source_path: str = ""
    # 上游 API 错误（如 pi 的 stopReason=error + errorMessage、codex 的 event_msg
    # error）：会话文件存在但内容只有报错时，归因必须是 api-unavailable/
    # login/quota，不能误报 transcript-missing（harness 坏了）。
    infra_errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "model_readback": self.model_readback,
            "model_changes": list(self.model_changes),
            "cli_version": self.cli_version,
            "tool_calls": [vars(c) for c in self.tool_calls],
            "denials": [vars(d) for d in self.denials],
            "writes": [vars(w) for w in self.writes],
            "final_text": self.final_text,
            "started_at": self.started_at,
            "duration_s": self.duration_s,
            "settings_snapshot": self.settings_snapshot,
            "source_path": self.source_path,
            "infra_errors": list(self.infra_errors),
        }

    @classmethod
    def from_dict(cls, doc: dict) -> "IntermediateTrajectory":
        traj = cls(agent=doc.get("agent", ""))
        traj.model_readback = doc.get("model_readback", "")
        traj.model_changes = list(doc.get("model_changes", []))
        traj.cli_version = doc.get("cli_version")
        traj.tool_calls = [ToolCall(**c) for c in doc.get("tool_calls", [])]
        traj.denials = [Denial(**d) for d in doc.get("denials", [])]
        traj.writes = [WriteEvent(**w) for w in doc.get("writes", [])]
        traj.final_text = doc.get("final_text", "")
        traj.started_at = doc.get("started_at", "")
        traj.duration_s = float(doc.get("duration_s", 0.0))
        traj.settings_snapshot = dict(doc.get("settings_snapshot", {}))
        traj.source_path = doc.get("source_path", "")
        traj.infra_errors = list(doc.get("infra_errors", []))
        return traj


def dump(traj: IntermediateTrajectory, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(traj.to_dict(), ensure_ascii=False, indent=2),
                    encoding="utf-8")


def load(path: Path) -> IntermediateTrajectory:
    return IntermediateTrajectory.from_dict(
        json.loads(path.read_text(encoding="utf-8")))
