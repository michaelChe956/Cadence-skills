"""eval 子命令入口。用法：python3 -m eval.runner.cli <subcommand> [options]。"""
import argparse
import stat
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def mock_bin(base: Path) -> Path:
    """生成四个 mock CLI 可执行（转发 eval.runner.mock_cli），返回 bin 目录。"""
    bin_dir = base / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for agent in ("claude", "codex", "pi", "kimi"):
        wrapper = bin_dir / agent
        wrapper.write_text(
            "#!/usr/bin/env python3\nimport sys\n"
            f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
            "from eval.runner import mock_cli\n"
            f"sys.exit(mock_cli.main(['--agent', '{agent}']))\n", encoding="utf-8")
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
    return bin_dir


def cmd_smoke(args):
    """mock 冒烟：四端 × 阶段一全绿（Tier-0 / Tier-1 付费前自检）。"""
    from eval.fixtures import generator as gen
    from eval.install import stage1
    import json
    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        bin_dir = mock_bin(base)
        for agent in ("claude", "codex", "pi", "kimi"):
            fx = gen.make_fixture("fresh", base / agent, REPO_ROOT)
            report = stage1.run_stage1(agent, fx, {"pinned_model": "mock"},
                                       bin_dir=bin_dir, verify=lambda root: 0)
            print(f"[smoke] {agent}: {'OK' if report['ok'] else 'FAIL'}")
            if not report["ok"]:
                failed.extend(f"{agent}:{a['name']}" for a in report["assertions"]
                              if not a["ok"])
    if failed:
        print("[smoke] 失败项：", json.dumps(failed, ensure_ascii=False))
        return 1
    return 0


def cmd_stage1(args):
    from eval.fixtures import generator as gen
    from eval.install import stage1
    fx = gen.make_fixture(args.variant, Path(args.base).resolve(), REPO_ROOT)
    report = stage1.run_stage1(args.agent, fx, {"pinned_model": args.model})
    import json
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def cmd_forensics_denial(args):
    """调用真实 claude 取证并要求至少捕获一个 denial 事件。"""
    from eval.runner import forensics
    path = forensics.forensics_denial(
        REPO_ROOT, Path(args.base).resolve(), {"pinned_model": args.model},
        variant=args.variant)
    import json
    doc = json.loads(path.read_text(encoding="utf-8"))
    return 0 if doc["denial_events_raw"] else 1


def cmd_verify_kimi(args):
    """运行 kimi 单端验证；通过后由维护者显式启用矩阵。"""
    from eval.runner import verify_kimi
    return verify_kimi.verify(REPO_ROOT, Path(args.base).resolve(),
                              {"pinned_model": args.model})


def cmd_night(args):
    """运行单夜流水线。"""
    from eval.runner import night
    return night.run_night(
        args.date, REPO_ROOT, Path(args.base).resolve(),
        config_dir=Path(args.config_dir).resolve() if args.config_dir else None,
        mock=args.mock)


def cmd_report(args):
    """生成滚动窗口报告并按具名 diff 返回门禁码。"""
    from eval.runner import report
    return report.write_report(
        Path(args.base).resolve(),
        Path(args.baseline).resolve() if args.baseline else None,
        config_dir=Path(args.config_dir).resolve() if args.config_dir else None,
        end_date=args.end_date,
    )


def cmd_audit(args):
    """扫描既有 session 并写出本机观测审计表。"""
    from datetime import date as _date
    from eval.runner import audit

    paths = {
        name: Path(getattr(args, f"{name}_dir")).expanduser()
        for name in ("claude", "codex", "pi", "kimi")
        if Path(getattr(args, f"{name}_dir")).expanduser().is_dir()
    }
    data = audit.audit_dirs(paths, limit_per_agent=args.limit)
    out = audit.write_audit(
        Path(args.out).expanduser() / _date.today().isoformat(), data)
    print(f"[audit] 输出 {out}/audit.md（不入 git，仅本机观测）")
    return 0


def cmd_baseline(args):
    """生成候选基线；候选文件不会自动替换生效基线。"""
    from eval.runner import report
    return report.candidate_baseline(
        Path(args.base).resolve(), Path(args.out).resolve(), end_date=args.end_date)


def cmd_pins_audit(args):
    """探活四端版本并打印可固化到 agents.json 的版本信息。"""
    import subprocess
    from eval.runner import proc
    for agent, template in proc.INVOCATIONS.items():
        try:
            output = subprocess.run(
                [template["argv"][0], "--version"], capture_output=True,
                text=True, timeout=30, shell=False).stdout.strip().splitlines()
            version = output[0] if output else ""
        except Exception as exc:  # noqa: BLE001 —— 探活命令，失败也须可审计
            version = f"检查失败：{exc}"
        print(f'{agent}: "{version}"')
    print("[pins-audit] 将以上版本填入 eval/config/agents.json 的 cli_version 后提交")
    return 0


def cmd_rerun(args):
    """离线重跑历史轨迹并与 golden 登记判定做 diff。"""
    from eval.runner import offline_rerun
    return offline_rerun.run_rerun(Path(args.transcripts), Path(args.golden))


def cmd_drill7(args):
    """运行连续 7 夜 mock/真实演练。"""
    from eval.runner import night
    return night.drill7(Path(args.base).resolve(), REPO_ROOT, mock=args.mock)


def build_parser():
    parser = argparse.ArgumentParser(prog="eval")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("smoke", help="mock 冒烟（零真实 CLI）")
    p.set_defaults(func=cmd_smoke)
    p = sub.add_parser("stage1", help="单端阶段一安装流水线（真实 CLI，self-hosted）")
    p.add_argument("--agent", required=True, choices=["claude", "codex", "pi", "kimi"])
    p.add_argument("--variant", default="fresh", choices=["fresh", "v3", "mcp_pre"])
    p.add_argument("--base", required=True, help="fixture 基目录（临时目录）")
    p.add_argument("--model", default="")
    p.set_defaults(func=cmd_stage1)
    p = sub.add_parser("forensics-denial",
                       help="fixture 人造真实 denial 取证（真实 claude，self-hosted）")
    p.add_argument("--base", required=True, help="工作基目录（临时目录）")
    p.add_argument("--variant", default="mcp_pre", choices=["fresh", "v3", "mcp_pre"],
                    help="取证 fixture 变体（默认 mcp_pre，确保 codegraph gate 成立）")
    p.add_argument("--model", default="glm-5.3")
    p.set_defaults(func=cmd_forensics_denial)
    p = sub.add_parser("verify-kimi", help="kimi 单端先行验证（真实 CLI）")
    p.add_argument("--base", required=True, help="工作基目录（临时目录）")
    p.add_argument("--model", default="kimi-code/kimi-for-coding")
    p.set_defaults(func=cmd_verify_kimi)
    p = sub.add_parser("night", help="Tier-1 单夜流水线（self-hosted；--mock 冒烟）")
    p.add_argument("--date", required=True)
    p.add_argument("--base", required=True, help="运行基目录（报告落其下 reports/）")
    p.add_argument("--config-dir", default=None)
    p.add_argument("--mock", action="store_true")
    p.set_defaults(func=cmd_night)
    p = sub.add_parser("report", help="四矩阵聚合 + 双键基线具名 diff")
    p.add_argument("--base", required=True)
    p.add_argument("--baseline", default="eval/baselines/baseline.json")
    p.add_argument("--config-dir", default=None)
    p.add_argument("--end-date", default=None)
    p.set_defaults(func=cmd_report)
    p = sub.add_parser("baseline", help="生成候选基线（维护者审阅后显式提交）")
    p.add_argument("--base", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--end-date", default=None)
    p.set_defaults(func=cmd_baseline)
    p = sub.add_parser("audit", help="既有 session 审计表（本机存量，观测参考）")
    p.add_argument("--out", default="cadence/reports/eval/audit")
    p.add_argument("--claude-dir", default="~/.claude/projects")
    p.add_argument("--codex-dir", default="~/.codex/sessions")
    p.add_argument("--pi-dir", default="~/.pi/agent/sessions")
    p.add_argument("--kimi-dir", default="~/.kimi-code/sessions")
    p.add_argument("--limit", type=int, default=200)
    p.set_defaults(func=cmd_audit)
    p = sub.add_parser("pins-audit", help="打印四端当前 --version 与模型")
    p.set_defaults(func=cmd_pins_audit)
    p = sub.add_parser("rerun", help="离线重跑——历史轨迹重判并 diff（Tier-0 job）")
    p.add_argument("--transcripts", default="eval/transcripts")
    p.add_argument("--golden", default="eval/transcripts/golden-verdicts.json")
    p.set_defaults(func=cmd_rerun)
    p = sub.add_parser("drill7", help="连续 7 夜端到端演练（默认 mock 加速）")
    p.add_argument("--base", required=True)
    p.add_argument("--no-mock", dest="mock", action="store_false", default=True)
    p.set_defaults(func=cmd_drill7)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
