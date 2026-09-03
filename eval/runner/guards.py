"""运行器工程面：断点续跑、多层熔断、双 pin 核验、MODEL_DRIFT、保留策略。"""
import json
import time
from pathlib import Path
from typing import Optional


def load_config(path: Path) -> dict:
    """读取 JSON 配置并保留结构化错误，供 CLI 在启动阶段暴露配置问题。"""
    return json.loads(path.read_text(encoding="utf-8"))


def model_drift(traj, pins) -> Optional[str]:
    """核验 transcript 实测模型；pi 会话内变更优先作为漂移。"""
    if traj.model_changes:
        return "pi-model-change:" + ",".join(traj.model_changes)
    if not traj.model_readback:
        return "model-unreadable"
    pinned = (pins or {}).get("pinned_model")
    if traj.model_readback != pinned:
        return f"MODEL_DRIFT:{traj.model_readback}!={pinned}"
    return None


def should_skip(results_dir: Path, run_id: str) -> bool:
    """结果 JSON 已存在即跳过，支持中断夜间任务的断点续跑。"""
    return (Path(results_dir) / f"{run_id}.json").is_file()


class CircuitBreaker:
    """多层熔断：轮次上限、墙钟上限、连续错误上限。"""

    def __init__(self, policy: dict):
        self.policy = policy

    def check(self, session_count: int, wall_minutes: float,
              error_streak: int) -> tuple[bool, str]:
        max_sessions = self.policy.get("max_sessions_per_night", 80)
        if session_count >= max_sessions:
            return True, f"sessions>={max_sessions}"
        max_wall = self.policy.get("max_wall_minutes", 420)
        if wall_minutes >= max_wall:
            return True, f"wall_minutes>={max_wall}"
        max_errors = self.policy.get("max_error_streak", 6)
        if error_streak >= max_errors:
            return True, f"error_streak>={max_errors}"
        return False, ""


def apply_retention(nightly_root: Path, keep_nights: int = 7) -> list[str]:
    """仅清理超窗且通过 run 的原始 transcript，保留结果和中间格式。"""
    pruned: list[str] = []
    root = Path(nightly_root)
    cutoff = time.time() - keep_nights * 86400
    if not root.is_dir():
        return pruned
    for night_dir in sorted(root.iterdir()):
        if not night_dir.is_dir():
            continue
        results_dir = night_dir / "runs"
        raw_dir = night_dir / "transcripts"
        if not results_dir.is_dir() or not raw_dir.is_dir():
            continue
        for result in results_dir.glob("*.json"):
            try:
                doc = json.loads(result.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if doc.get("verdict") != "PASS" or result.stat().st_mtime >= cutoff:
                continue
            run_id = result.stem
            for raw in raw_dir.glob(f"{run_id}.*"):
                try:
                    raw.unlink()
                except OSError:
                    continue
                pruned.append(str(raw))
    return pruned


def _load_state(state_path: Path) -> dict:
    if not Path(state_path).is_file():
        return {}
    try:
        return json.loads(Path(state_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def update_streak(state_path: Path, agent: str, ok: bool) -> int:
    """更新端级连续失败夜数；成功即清零。"""
    state = _load_state(state_path)
    streaks = state.setdefault("streaks", {})
    streaks[agent] = 0 if ok else int(streaks.get(agent, 0)) + 1
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    return streaks[agent]


def streak_alerts(state_path: Path) -> list[str]:
    """返回连续三夜失败端，排序以便报告确定性。"""
    return sorted(agent for agent, streak in
                  _load_state(state_path).get("streaks", {}).items()
                  if streak >= 3)
