"""kimi 适配器先行单端验证（spec：MUST 先行单端验证后再入矩阵）。

真实 CLI（self-hosted）：一次探针式调用 + 一次阶段一安装，检查
模型回读/工具解析/产物断言。通过后维护者将 agents.json 的
kimi.enabled 置 true，夜间矩阵才会包含 kimi。
"""
import tempfile
from pathlib import Path

from eval.adapters import get_adapter
from eval.runner import guards, night
from eval.fixtures import generator as gen
from eval.install import stage1
from eval.runner import proc


def verify(repo_root: Path, base_dir: Path, pins: dict) -> int:
    """执行 kimi 先行单端验证，返回 0（通过）或 1（失败）。"""
    checks = []
    adapter = get_adapter("kimi")
    with tempfile.TemporaryDirectory(dir=str(base_dir)) as tmp:
        base = Path(tmp)
        fixture = gen.make_fixture("fresh", base, repo_root)
        agents_cfg = guards.load_config(
            repo_root / "eval" / "config" / "agents.json")
        skill_env = night._resolved_skill_env(agents_cfg, "kimi", fixture)
        proc.link_agent_auth("kimi", fixture)

        ok_version, version_detail = proc.cli_version_check("kimi", pins)
        checks.append(("cli-version", ok_version, version_detail))

        output = proc.run_cli(
            "kimi",
            "请只回答：OK",
            cwd=fixture.root,
            home=None,
            pins=pins,
            timeout_s=300,
            skill_env=skill_env,
            session_root=fixture.home,
            env_extra={"EVAL_STAGE": "probe", "EVAL_PROBE_ID": "P4"},
        )
        transcript = output.get("transcript_path") or ""
        checks.append((
            "session-located",
            bool(transcript),
            transcript or "未定位到 wire.jsonl",
        ))

        trajectory_ok, trajectory_detail = False, ""
        if transcript:
            trajectory = adapter.parse_file(Path(transcript))
            trajectory_ok = bool(trajectory.model_readback)
            trajectory_detail = (
                f"model={trajectory.model_readback} "
                f"calls={len(trajectory.tool_calls)} "
                f"final_text={len(trajectory.final_text)}ch"
            )
        checks.append(("model-readback", trajectory_ok, trajectory_detail))

        report = stage1.run_stage1("kimi", fixture, pins, timeout_s=1800,
                                  skill_env=skill_env)
        checks.append((
            "stage1",
            report["ok"],
            ";".join(assertion["name"] for assertion in report["assertions"]
                     if not assertion["ok"]),
        ))

    print("[verify-kimi] 单端验证清单：")
    all_ok = True
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
        all_ok = all_ok and ok
    print("[verify-kimi] 全部通过后：将 eval/config/agents.json 的 kimi.enabled 置 true")
    return 0 if all_ok else 1
