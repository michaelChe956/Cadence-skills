"""人造真实 denial 取证（spec：gate 启用前 MUST 先取证字段真实结构）。

本机 242 个真实会话 permission_denial 出现 0 次（oracle 实测），现有
DENIAL_MARKERS 是启发式——本命令在 fixture 上人为制造一次真实拒绝，
把原始事件存 eval/evidence/，供 claude 适配器校准并以离线用例锁定。
"""
import json
import tempfile
from datetime import date
from pathlib import Path

from eval.adapters import get_adapter
from eval.fixtures import generator as gen
from eval.install import stage1


def forensics_denial(repo_root: Path, base_dir: Path, pins: dict) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(base_dir)) as tmp:
        fx = gen.make_fixture("fresh", Path(tmp), repo_root)
        stage1.run_stage1("claude", fx, pins, timeout_s=1800)
        from eval.runner import proc
        out = proc.run_cli(
            "claude", "用 Grep 工具在 src 目录搜索 orders，把结果原样给我",
            cwd=fx.root, home=fx.home, pins=pins, timeout_s=600,
            env_extra={"EVAL_STAGE": "probe", "EVAL_PROBE_ID": "P1"})
        traj = get_adapter("claude").parse_file(Path(out["transcript_path"]))
        payload = {
            "date": str(date.today()),
            "fixture_settings_deny": ((fx.root / ".claude" / "settings.json").is_file()
                                      and json.loads((fx.root / ".claude" / "settings.json")
                                                    .read_text(encoding="utf-8"))
                                      .get("permissions", {}).get("deny", [])),
            "denial_events_raw": [d.raw for d in traj.denials],
            "is_error_calls": [{"index": c.index, "tool": c.tool}
                               for c in traj.tool_calls if c.is_error],
            "returncode": out["returncode"], "stderr": out["stderr"],
        }
    out_path = (repo_root / "eval" / "evidence"
                / f"denial-fields-claude-{date.today().isoformat()}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"[forensics] 提取到 {len(payload['denial_events_raw'])} 个真实 denial 事件"
          f" → {out_path}")
    print("[forensics] 若非零：按证据中的原始字段校准 eval/adapters/claude.py 的"
          " DENIAL_MARKERS，并在 test_adapters_claude 增加对证据文件的回放断言")
    return out_path
