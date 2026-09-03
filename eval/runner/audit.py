"""既有 session 审计表（第五张观测表）：复用四端适配器离线解析本机存量。

定位（oracle §2-d / eval-ci-matrix R6）：真实生产分布的观测参考——
不进 gate、不入基线、不入 git；不替代受控探针（样本非受控）。
"""
import json
from collections import Counter
from pathlib import Path
from typing import Optional

from eval.adapters import get_adapter
from eval.scoring.assertor import bash_heads


DEFAULT_GLOBS = {
    "claude": ["**/*.jsonl"],
    "codex": ["**/rollout-*.jsonl"],
    "pi": ["**/session.jsonl"],
    "kimi": ["**/wire.jsonl"],
}


def audit_dirs(paths: dict[str, Path], limit_per_agent: int = 200,
               glob_patterns: Optional[dict[str, list[str]]] = None) -> dict:
    """扫描各端既有 session，并聚合工具、命令头、模型、拒绝和时长分布。

    只读取调用方明确传入的目录，测试和维护者可用合成目录替代真实 HOME。
    每端先按 mtime 取最近的 ``limit_per_agent`` 个文件，避免全量解析存量。
    """
    patterns = glob_patterns or DEFAULT_GLOBS
    per_agent = {}
    for agent, root in paths.items():
        root = Path(root)
        adapter = get_adapter(agent)
        files = []
        seen = set()
        for pattern in patterns.get(agent, ["**/*.jsonl"]):
            for path in root.glob(pattern):
                # 多个 glob 交叠时，同一个 session 只计一次。
                if path in seen or not path.is_file():
                    continue
                seen.add(path)
                files.append(path)
        files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
        files = files[:max(0, limit_per_agent)]

        tools, heads, models = Counter(), Counter(), Counter()
        denials = 0
        durations = []
        for path in files:
            try:
                traj = adapter.parse_file(path)
            except (OSError, ValueError):
                # 单个损坏或并发写入中的 session 不应阻断其他样本观测。
                continue
            tools.update(c.tool for c in traj.tool_calls)
            heads.update(bash_heads(traj))
            if traj.model_readback:
                models[traj.model_readback] += 1
            denials += len(traj.denials)
            if traj.duration_s:
                durations.append(traj.duration_s)

        ordered_durations = sorted(durations)
        per_agent[agent] = {
            "sessions": len(files),
            "tools": dict(tools.most_common(20)),
            "bash_heads": dict(heads.most_common(20)),
            "models": dict(models.most_common(10)),
            "denials": denials,
            "durations": {
                "median": ordered_durations[len(ordered_durations) // 2]
                if ordered_durations else None,
                "p90": ordered_durations[int(len(ordered_durations) * 0.9)]
                if ordered_durations else None,
            },
        }
    totals = {agent: value["sessions"] for agent, value in per_agent.items()}
    return {"per_agent": per_agent, "totals": totals}


def write_audit(out_dir: Path, data: dict) -> Path:
    """写出 JSON/Markdown 审计产物；目录由 CLI 按日期分层。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "audit.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# eval 审计表（既有 session 观测）", "",
        "> 仅作观测参考：不进 gate、不入基线、不入 git；样本非受控，",
        "> 不替代受控探针。发现（如漫游形态）作为探针题库迭代输入。", "",
    ]
    for agent, per in data.get("per_agent", {}).items():
        lines.append(f"## {agent}（{per['sessions']} 会话）")
        lines.append(f"- 模型分布：{per['models']}")
        lines.append(f"- 工具 Top：{dict(list(per['tools'].items())[:8])}")
        ls_find = {
            key: value for key, value in per["bash_heads"].items()
            if key.split(" ")[0] in ("ls", "find")
        }
        lines.append(f"- ls/find 命令头：{ls_find}")
        lines.append(f"- denial 事件：{per['denials']}")
        lines.append(
            f"- 时长：median={per['durations']['median']}s "
            f"p90={per['durations']['p90']}s"
        )
        lines.append("")
    (out_dir / "audit.md").write_text("\n".join(lines), encoding="utf-8")
    return out_dir
