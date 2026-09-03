"""幂等双跑/三跑：同一 fixture 连续安装，末遍 workspace diff 必须 byte-identical。"""
import hashlib
from pathlib import Path
from typing import Callable, Optional

from eval.runner import proc


def snapshot_tree(root: Path) -> dict:
    """workspace 文件快照（相对路径→sha256）；排除 .git/ 与运行器自身产物 .eval-*。"""
    out = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if rel.startswith(".git/") or rel.startswith(".eval-"):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def diff_trees(before: dict, after: dict) -> dict:
    """after 相对 before 的变化集：{路径: 'added'|'removed'|'changed'}。"""
    diff = {}
    for path, digest in after.items():
        if path not in before:
            diff[path] = "added"
        elif before[path] != digest:
            diff[path] = "changed"
    for path in before:
        if path not in after:
            diff[path] = "removed"
    return diff


def run_idempotency(agent, fixture, pins, passes=2, *, cli=proc.run_cli,
                    verify=None, bin_dir=None, skill_env=None):
    """连续 N 遍安装；diffs[i] = 第 i+1 遍相对第 i 遍的差集；末遍空 → stable。"""
    from eval.install import stage1
    diffs = []
    prev = snapshot_tree(fixture.root)
    for _ in range(passes):
        stage1.run_stage1(agent, fixture, pins, cli=cli, verify=verify,
                          bin_dir=bin_dir, skill_env=skill_env)
        cur = snapshot_tree(fixture.root)
        diffs.append(diff_trees(prev, cur))
        prev = cur
    return {"passes": passes, "diffs": diffs, "stable": diffs[-1] == {}}
