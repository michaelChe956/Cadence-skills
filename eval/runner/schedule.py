"""分夜轮转调度表（eval-ci-matrix R2 / oracle 拍板点 3）。

夜序号以 SCHED_START（首个调度夜 2026-09-07，周一）起算：
night_index = (date - SCHED_START).days——历法无关，不随 toordinal 漂移。
"""
from datetime import date

SCHED_START = date(2026, 9, 7)  # 首个调度夜（周一）

ODD_PROBES = ("P1", "P3", "P5", "P7")
EVEN_PROBES = ("P2", "P4", "P6", "P8")
THEMES = ("orders", "billing", "users")


def night_index(date_str: str) -> int:
    """距首个调度日起算的夜序号（负值=首个调度夜之前，模运算仍确定性）。"""
    return (date.fromisoformat(date_str) - SCHED_START).days


def _rotate(agents: list, night: int, offset: int, count: int) -> list:
    if len(agents) <= count:
        return list(agents)
    return [agents[(night + offset + i) % len(agents)] for i in range(count)]


def night_plan(date_str: str, agents: list) -> dict:
    night = night_index(date_str)
    return {
        "night": date_str,
        "parity": "odd" if night % 2 else "even",
        "probe_ids": list(ODD_PROBES if night % 2 else EVEN_PROBES),
        "agents": list(agents),
        "control_agents": _rotate(agents, night, 0, 2),
        "v3_agents": _rotate(agents, night, 2, 2) if night % 7 == 0 else [],
        "strong_agents": _rotate(agents, night, 4, 2) if night % 7 == 3 else [],
        "runs": 2,
        "theme": THEMES[night % len(THEMES)],
    }
