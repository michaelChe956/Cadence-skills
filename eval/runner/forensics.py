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
from eval.runner import guards, night, proc
from eval.fixtures import generator as gen
from eval.install import stage1


def forensics_denial(repo_root: Path, base_dir: Path, pins: dict,
                     variant="mcp_pre") -> Path:
    """在带权限 gate 的 fixture 上运行真实 claude denial 取证。

    默认使用 mcp_pre 变体，确保 S9 的 codegraph gate 成立；阶段一完成后
    先断言 fixture 实际写出了非空 deny 配置，再允许真实 CLI 执行，避免空转。
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(base_dir)) as tmp:
        fx = gen.make_fixture(variant, Path(tmp), repo_root)
        agents_cfg = guards.load_config(
            repo_root / "eval" / "config" / "agents.json")
        skill_env = night._resolved_skill_env(agents_cfg, "claude", fx)
        stage1.run_stage1("claude", fx, pins, timeout_s=1800,
                          skill_env=skill_env)
        settings_path = fx.root / ".claude" / "settings.json"
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(
                "fixture_settings_deny 为空：阶段一未生成有效 .claude/settings.json"
            ) from exc
        deny = settings.get("permissions", {}).get("deny", [])
        if not deny:
            raise RuntimeError("fixture_settings_deny 为空：拒绝 gate 未启用，停止取证空转")
        out = proc.run_cli(
            "claude", "用 Grep 工具在 src 目录搜索 orders，把结果原样给我",
            cwd=fx.root, home=None, pins=pins, timeout_s=600,
            skill_env=skill_env, session_root=fx.home,
            env_extra={"EVAL_STAGE": "probe", "EVAL_PROBE_ID": "P1"})
        traj = get_adapter("claude").parse_file(Path(out["transcript_path"]))
        payload = {
            "date": str(date.today()),
            "fixture_settings_deny": deny,
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
