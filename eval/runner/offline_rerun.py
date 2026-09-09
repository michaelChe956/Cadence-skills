"""离线重跑：历史 transcript 重新适配+判分并与 golden diff（断言器回归防线）。

Tier-0 的一个 job（eval-ci-matrix R1）：用留存的（脱敏）真实/罐头轨迹作
golden 输入，比 mock 冒烟更强；workspace 相关断言离线跳过并标注。
"""
import json
from pathlib import Path

from eval.adapters import get_adapter
from eval.probes import definitions as prb
from eval.scoring import assertor


def run_rerun(transcripts_dir: Path, golden_path: Path) -> int:
    """重新适配并判分登记的历史轨迹，发现判定翻转或文件缺失即返回 1。"""
    entries = json.loads(Path(golden_path).read_text(encoding="utf-8"))
    flips = []
    for entry in entries:
        path = Path(transcripts_dir) / entry["path"]
        if not path.is_file():
            flips.append(f"{entry['path']}: 文件缺失")
            continue
        traj = get_adapter(entry["agent"]).parse_file(path)
        if isinstance(entry.get("settings_snapshot"), dict):
            traj.settings_snapshot = entry["settings_snapshot"]
        result = assertor.score_run(
            f"rerun:{entry['path']}", prb.get(entry["probe_id"]), traj,
            workspace=None, fake_mcp_log=None, pre_snapshot=None)
        if result["verdict"] != entry["expect_verdict"]:
            flips.append(f"{entry['path']}: 期望 {entry['expect_verdict']}"
                         f" 实判 {result['verdict']}（{result['fail_reason']}）")
    if flips:
        print("[rerun] 判定翻转：")
        for line in flips:
            print("  -", line)
        return 1
    print(f"[rerun] {len(entries)} 条 golden 全部一致")
    return 0
