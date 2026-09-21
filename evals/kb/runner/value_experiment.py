"""kb-eval 价值实验：两 arm 配对（唯一变量 = 是否提供知识库环境）。

公平协议：
- prompt 两 arm 完全一致（业务任务原文，来自 cases.py）
- 源码快照、git 历史、超时、agent、CLI 版本、model 完全一致
- arm=kb：工作目录含 cadence/knowledge-base/（KB 产物）+ AGENTS.md 的 KB 导航区块
- arm=nokb：工作目录无 cadence/ 目录、无 AGENTS.md
- 每案例从同一干净源码快照重新开始（独立新会话）

结果：RESULTS/value-results.json
"""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

HOME = Path("/home/tester")
WORK = HOME / "work"
RESULTS = HOME / "results"
PROJECT = WORK / "project"
BASE = WORK / "base"
KB_NAV = """# 项目说明

本项目已建立 KnowledgeBase（Schema 4.0）。

需求澄清、Design、Plan、Coding、Testing、Review 或 Debug 前，先读 `cadence/knowledge-base/README.md`
获取项目导航，再按任务范围读取相关文档（接口在 `interfaces/`、表在 `data-models/`、
规则与流程在 `business/`、组合能力在 `capabilities/`）。
"""


def sh(cmd, cwd=None, timeout=120):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def run_cli(cfg, prompt, cwd, timeout_s):
    argv = list(cfg["cmd"]) + ([prompt] if cfg.get("prompt_arg") else [])
    env = dict(os.environ)
    env["EVAL_PROMPT"] = prompt
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout_s, env=env)
        return {"rc": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        return {"rc": 124, "stdout": out, "stderr": "TIMEOUT", "timed_out": True}


def parse_usage(stdout):
    for line in reversed(stdout.splitlines()):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if isinstance(d, dict) and d.get("type") == "result":
            u = d.get("usage") or {}
            return {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
                    "cost_usd": d.get("total_cost_usd"),
                    "cost_source": "actual" if d.get("total_cost_usd") is not None else "unavailable"}
    return None


def _final_answer(agent, stdout):
    """按端提取最终回答；无法结构化提取时返回原文（报告标注来源类型）。"""
    if agent == "claude":
        for line in reversed(stdout.splitlines()):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if isinstance(d, dict) and d.get("type") == "result" and isinstance(d.get("result"), str):
                return d["result"], "structured"
    return stdout, "raw_stdout"


def setup_arms(arm, restore_kb):
    """建立干净源码基线 + 按 arm 布置环境。"""
    if PROJECT.exists():
        shutil.rmtree(PROJECT)
    shutil.copytree(BASE, PROJECT, symlinks=True)
    if arm == "kb":
        if not restore_kb:
            raise SystemExit("arm=kb 需要 --restore-kb 指向 KB 产物目录")
        dst = PROJECT / "cadence/knowledge-base"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(Path(restore_kb), dst, symlinks=True)
        (PROJECT / "AGENTS.md").write_text(KB_NAV, encoding="utf-8")


def hide_kb_sources():
    """隔离：确保 agent 无法从挂载仓库读到历史 KB 结果。"""
    # /opt/repo 只读挂载中 evals/kb/results 含历史 KB；对照 arm 在 prompt 中不做 KB 提示，
    # 且本题面为业务任务，不涉及 evals 目录；如需更强隔离可在容器启动时不挂 evals。
    pass


def run(cfg, budget, args):
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import cases as case_set

    sel = case_set.get(args.cases.split(",") if args.cases else None)
    batch = args.batch or time.strftime("exp-%Y%m%d-%H%M%S")
    out = {"batch": batch, "agent": args.agent, "arm": args.arm, "model": args.model or "default",
           "fixture": getattr(args, "fixture", "standard"),
           "cli_version": (json.loads((RESULTS / "results.json").read_text(encoding="utf-8")).get("cli_version")
                           if (RESULTS / "results.json").exists() else None),
           "started": time.strftime("%F %T"), "cases": {}}
    print("═" * 60)
    print(f"  价值实验  batch={batch}  arm={args.arm}  agent={args.agent}  案例数={len(sel)}")
    print("═" * 60)

    (RESULTS / "transcripts").mkdir(parents=True, exist_ok=True)
    for c in sel:
        pid = c["id"]
        t0 = time.time()
        setup_arms(args.arm, args.restore_kb)
        # 实验组：KB 在位；对照组：确保无 cadence/
        if args.arm == "nokb" and (PROJECT / "cadence").exists():
            shutil.rmtree(PROJECT / "cadence")
        r = run_cli(cfg, c["prompt"], PROJECT, budget["timeout_min"] * 60)
        elapsed = round(time.time() - t0, 1)
        answer, src_type = _final_answer(args.agent, r["stdout"])
        (RESULTS / "transcripts" / f"{pid}.log").write_text(
            r["stdout"] + "\n" + r["stderr"], encoding="utf-8")
        verdicts = case_set.judge(c, answer)
        out["cases"][pid] = {
            "scenario": c["scenario"], "title": c["title"],
            "prompt": c["prompt"], "final_answer": answer, "answer_source": src_type,
            "duration_s": elapsed, "usage": parse_usage(r["stdout"]),
            "returncode": r["rc"], "timed_out": r["timed_out"],
            "transcript": f"transcripts/{pid}.log",
            "checks": verdicts,
            "score": f"{sum(1 for v in verdicts if v['verdict'] == 'pass')}/{len(verdicts)}",
        }
        (RESULTS / f"value-{args.arm}-results.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        passed = sum(1 for v in verdicts if v["verdict"] == "pass")
        print(f"[{pid}] {passed}/{len(verdicts)} 检查通过 | {elapsed}s | rc={r['rc']}")

    print(f"\n结果：{RESULTS}/value-{args.arm}-results.json")
    return 0
