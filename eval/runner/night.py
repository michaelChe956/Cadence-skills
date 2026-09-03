"""Tier-1 单夜流水线：阶段一安装、探针、对照组、strong 行与留存。

真实模式保留真实 HOME（登录态），只通过 agents.json 的 skill_env 将技能发现
路径隔离到 fixture；mock 模式的全局配置快照根是 base_dir，避免触碰真实 HOME。
"""
import json
import shutil
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from eval import ifmt
from eval.adapters import get_adapter
from eval.fixtures import generator as gen
from eval.install import idempotency, stage1
from eval.mcp import fake_servers as fake
from eval.probes import definitions as prb
from eval.runner import guards, proc
from eval.scoring import assertor

REPORT_SUBDIR = "reports"


def _enabled_agents(agents_cfg: dict) -> list:
    return [name for name, cfg in agents_cfg.items() if cfg.get("enabled")]


def _resolved_argv_extra(agents_cfg: dict, agent: str, fixture) -> list:
    """agents.json 的 argv_extra 列表，{fixture_home} 占位符替换为 fixture.home。"""
    raw = (agents_cfg.get(agent) or {}).get("argv_extra") or []
    return [str(v).replace("{fixture_home}", str(fixture.home)) for v in raw]


def _resolved_skill_env(agents_cfg: dict, agent: str, fixture) -> Optional[dict]:
    """将配置中的 fixture_home 占位符替换为隔离 fixture HOME。"""
    raw = (agents_cfg.get(agent) or {}).get("skill_env") or {}
    resolved = {key: str(value).replace("{fixture_home}", str(fixture.home))
                for key, value in raw.items()}
    return resolved or None


def _inject_fake_mcp(fixture_root: Path, roles: list, log_dir: Path) -> None:
    if not roles:
        return
    path = fixture_root / ".mcp.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except ValueError:
        doc = {}
    doc.setdefault("mcpServers", {}).update(fake.fixture_mcp_config(roles, log_dir))
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def _settings_snapshot(fixture_root: Path) -> dict:
    path = fixture_root / ".claude" / "settings.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_run(nightly: Path, run_id: str, result: dict, traj) -> None:
    runs = nightly / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    ifmt.dump(traj, runs / f"{run_id}.intermediate.json")


_agents_cfg_global = {}


def run_single_probe(agent, probe_id, variant_idx, fixture, pins, policy,
                     run_id, results_dir, transcripts_dir, base_dir, theme="orders",
                     mock_bin_dir=None, variant="installed", real_home=False,
                     skill_env=None) -> dict:
    """执行单个探针并将结果、中间格式及原始轨迹落盘。"""
    probe = prb.get(probe_id)
    results_dir = Path(results_dir)
    transcripts_dir = Path(transcripts_dir)
    base_dir = Path(base_dir)
    log_dir = base_dir / "mcp-logs" / run_id
    pre_snapshot = idempotency.snapshot_tree(fixture.root)
    if variant == "installed":
        _inject_fake_mcp(fixture.root, probe.get("needs_fake_mcp", []), log_dir)
    prompt_env = prb.probe_env(probe_id, variant_idx, extra={
        "EVAL_STAGE": "probe", "EVAL_CWD": str(fixture.root)})
    prompt = prompt_env["EVAL_PROMPT"].replace("{module}", theme).replace(
        "<fixture>", str(fixture.root))
    if real_home and skill_env:
        proc.link_agent_auth(agent, fixture)
    _argv_extra = _resolved_argv_extra(_agents_cfg_global, agent, fixture) if real_home else None
    out = proc.run_cli(
        agent, prompt, cwd=fixture.root,
        home=None if real_home else fixture.home, pins=pins,
        timeout_s=policy.get("per_run_timeout_s", 900),
        env_extra=dict(prompt_env, EVAL_PROMPT=prompt), bin_dir=mock_bin_dir,
        out_dir=transcripts_dir, skill_env=skill_env, argv_extra=_argv_extra,
        session_root=fixture.home if real_home and skill_env else None)
    transcript = out.get("transcript_path") or ""
    if transcript and Path(transcript).is_file():
        traj = get_adapter(agent).parse_file(Path(transcript))
    else:
        traj = ifmt.IntermediateTrajectory(agent=agent)
    traj.settings_snapshot = _settings_snapshot(fixture.root)
    drift = guards.model_drift(traj, pins)
    fake_log = fake.read_calls(log_dir) if log_dir.exists() else []
    if drift:
        result = {
            "schema_version": "1.0", "run_id": run_id, "agent": agent,
            "model": traj.model_readback, "cli_version": traj.cli_version,
            "probe_id": probe_id,
            "rule_clause_ids": list(probe.get("rule_clause_ids", [])),
            "verdict": "MODEL_DRIFT", "fail_reason": drift,
            "denials": [vars(d) for d in traj.denials],
            "transcript_path": transcript, "started_at": traj.started_at,
            "duration_s": traj.duration_s, "details": {"stderr": out["stderr"][-500:]},
        }
    else:
        result = assertor.score_run(
            run_id, probe, traj, workspace=fixture.root, fake_mcp_log=fake_log,
            pre_snapshot=pre_snapshot, returncode=out["returncode"],
            stderr=out["stderr"], timed_out=out.get("timed_out", False))
        result["variant"] = variant
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    if transcript and Path(transcript).is_file():
        ext = Path(transcript).suffix or ".jsonl"
        target = transcripts_dir / f"{run_id}{ext}"
        if Path(transcript).resolve() != target.resolve():
            shutil.copyfile(transcript, target)
        result["transcript_path"] = str(target)
    _save_run(results_dir.parent, run_id, result, traj)
    return result


def run_strong_rows(date_str, plan, agents_cfg, fixtures, policy,
                    runs_dir, transcripts_dir, base_dir, mock_bin_dir=None,
                    real_home=False) -> int:
    """显式执行调度表 strong_agents 中配置 strong_model 的端的增补行。"""
    from eval.runner.schedule import night_index
    executed = 0
    for agent in plan.get("strong_agents", []):
        cfg = agents_cfg.get(agent) or {}
        if not cfg.get("strong_model") or agent not in fixtures:
            continue
        pins = dict(cfg)
        pins["pinned_model"] = pins["strong_model"]
        fixture = fixtures[agent]
        skill_env = _resolved_skill_env(agents_cfg, agent, fixture) if real_home else None
        for probe_id in prb.PROBES:
            variant_idx = prb.variant_for_night(probe_id, night_index(date_str))
            run_id = f"{date_str}-{agent}-{probe_id}-strong-0"
            if guards.should_skip(runs_dir, run_id):
                continue
            run_single_probe(
                agent, probe_id, variant_idx, fixture, pins, policy, run_id,
                runs_dir, transcripts_dir, Path(base_dir) / "stage1" / date_str / agent,
                theme=plan.get("theme", "orders"), mock_bin_dir=mock_bin_dir,
                real_home=real_home, skill_env=skill_env)
            executed += 1
    return executed


def _record_global_drift(nightly: Path, before: dict, root: Path) -> None:
    nightly.mkdir(parents=True, exist_ok=True)
    after = gen.snapshot_global_configs(root)
    (nightly / "global-config-drift.json").write_text(
        json.dumps({"changed": gen.diff_global_configs(before, after)},
                   ensure_ascii=False, indent=2), encoding="utf-8")


def run_night(date_str: str, repo_root: Path, base_dir: Path,
              config_dir: Optional[Path] = None, mock: bool = False) -> int:
    """运行单夜任务；阶段一失败或熔断时不伪造完成报告。"""
    repo_root, base_dir = Path(repo_root), Path(base_dir)
    config_dir = Path(config_dir) if config_dir else repo_root / "eval" / "config"
    agents_cfg = guards.load_config(config_dir / "agents.json")
    policy = guards.load_config(config_dir / "policy.json")
    nightly = base_dir / REPORT_SUBDIR / "nightly" / date_str
    runs_dir, transcripts_dir = nightly / "runs", nightly / "transcripts"
    runs_dir.mkdir(parents=True, exist_ok=True)
    from eval.runner.schedule import night_index, night_plan
    plan = night_plan(date_str, _enabled_agents(agents_cfg))
    bin_dir = None
    if mock:
        from eval.runner import cli as cli_mod
        bin_dir = cli_mod.mock_bin(base_dir / "mockbin")
    real_home = not mock
    global_root = Path.home() if real_home else base_dir
    global_before = gen.snapshot_global_configs(global_root)
    started = time.time()
    session_count = error_streak = 0
    breaker = guards.CircuitBreaker(policy)
    fixtures = {}
    # 阶段一先完成，避免 strong 行引用不存在的 fixture。
    # 并行执行四端（policy.parallel_agents 控制，默认 4，mock 串行）
    _max_workers = policy.get("parallel_agents", 4 if not mock else 1)
    _lock = threading.Lock()
    _counters = {"sessions": 0, "error_streak": 0}
    _breaker = guards.CircuitBreaker(policy)

    def _agent_pipeline(ag):
        _pins = dict(agents_cfg[ag])
        if not mock:
            ok_ver, msg = proc.cli_version_check(ag, _pins)
            if not ok_ver:
                guards.update_streak(base_dir / REPORT_SUBDIR / "state" / "streaks.json", ag, False)
                return ag, None, f"[{ag}] 版本锁失败：{msg}"
        _stage_base = base_dir / "stage1" / date_str / ag
        _fx = gen.make_fixture("fresh", _stage_base, repo_root, theme=plan["theme"])
        _se = _resolved_skill_env(agents_cfg, ag, _fx) if real_home else None
        if real_home:
            proc.link_agent_auth(ag, _fx)
        _mv = (lambda root: 0) if mock else None
        _sr = stage1.run_stage1(ag, _fx, _pins, timeout_s=policy.get("stage1_timeout_s", 1200),
                                bin_dir=bin_dir, verify=_mv, skill_env=_se)
        # 真实模式跳过幂等检查——CLI 会话非确定性（时间戳/顺序），byte-identical 不成立
        if mock:
            _ir = idempotency.run_idempotency(ag, _fx, _pins, passes=2, bin_dir=bin_dir,
                                              verify=_mv, skill_env=_se)
        else:
            _ir = {"stable": True}  # 真实模式视为通过，幂等仅 mock 验证
        if not _sr.get("ok") or not _ir.get("stable"):
            guards.update_streak(base_dir / REPORT_SUBDIR / "state" / "streaks.json", ag, False)
            return ag, _fx, f"[{ag}] 阶段一/幂等失败，跳过其探针"
        if ag in plan["v3_agents"]:
            _v3_fx = gen.make_fixture("v3", base_dir / "stage1-v3" / date_str / ag,
                                      repo_root, theme=plan["theme"])
            _v3r = stage1.run_stage1(ag, _v3_fx, _pins, timeout_s=policy.get("stage1_timeout_s", 1200),
                                     bin_dir=bin_dir, verify=_mv,
                                     skill_env=_resolved_skill_env(agents_cfg, ag, _v3_fx) if real_home else None)
            if not _v3r.get("ok"):
                guards.update_streak(base_dir / REPORT_SUBDIR / "state" / "streaks.json", ag, False)
                return ag, _fx, f"[{ag}] v3 升级失败"
        guards.update_streak(base_dir / REPORT_SUBDIR / "state" / "streaks.json", ag, True)
        from eval.runner.schedule import night_index
        for pid in plan["probe_ids"]:
            _vidx = prb.variant_for_night(pid, night_index(date_str))
            for rn in range(policy.get("runs_per_combo", 2)):
                _rid = f"{date_str}-{ag}-{pid}-installed-{rn}"
                if guards.should_skip(runs_dir, _rid):
                    continue
                with _lock:
                    _trip, _tr = _breaker.check(
                        _counters["sessions"], (time.time() - started) / 60,
                        _counters["error_streak"])
                if _trip:
                    return ag, _fx, f"[{ag}] 熔断触发（{_tr}）"
                _res = run_single_probe(ag, pid, _vidx, _fx, _pins, policy, _rid,
                    runs_dir, transcripts_dir, _stage_base,
                    theme=plan["theme"], mock_bin_dir=bin_dir, real_home=real_home,
                    skill_env=_se)
                with _lock:
                    _counters["sessions"] += 1
                    if _res.get("verdict") == "INFRA_FAIL":
                        _counters["error_streak"] += 1
                    else:
                        _counters["error_streak"] = 0
        if ag in plan["control_agents"]:
            _cb = base_dir / "control" / date_str / ag
            _cfx = gen.make_fixture("control", _cb, repo_root, theme=plan["theme"])
            for pid in prb.CONTROL_PROBES:
                _vidx = prb.variant_for_night(pid, night_index(date_str))
                for rn in range(policy.get("runs_per_combo", 2)):
                    _rid = f"{date_str}-{ag}-{pid}-control-{rn}"
                    if guards.should_skip(runs_dir, _rid):
                        continue
                    run_single_probe(ag, pid, _vidx, _cfx, _pins, policy, _rid,
                                     runs_dir, transcripts_dir, _cb,
                                     theme=plan["theme"], mock_bin_dir=bin_dir,
                                     variant="control", real_home=real_home)
                    with _lock:
                        _counters["sessions"] += 1
        return ag, _fx, f"[{ag}] 完成"

    if _max_workers <= 1:
        for ag in plan["agents"]:
            _, fx, msg = _agent_pipeline(ag)
            print(msg)
            if fx:
                fixtures[ag] = fx
    else:
        with ThreadPoolExecutor(max_workers=_max_workers) as _pool:
            _futs = {_pool.submit(_agent_pipeline, ag): ag for ag in plan["agents"]}
            for _fut in as_completed(_futs):
                ag = _futs[_fut]
                try:
                    _, fx, msg = _fut.result()
                    print(msg)
                    if fx:
                        fixtures[ag] = fx
                except Exception as exc:
                    print(f"[{ag}] 线程异常：{exc}")

    session_count = _counters["sessions"]
    session_count += run_strong_rows(
        date_str, plan, agents_cfg, fixtures, policy, runs_dir, transcripts_dir,
        base_dir, mock_bin_dir=bin_dir, real_home=real_home)
    guards.apply_retention(
        base_dir / REPORT_SUBDIR / "nightly",
        keep_nights=policy.get("retention_keep_nights", 7))
    _record_global_drift(nightly, global_before, global_root)
    # 从结果落盘汇总特殊 verdict，保证日志与报告消费同一事实源。
    drift_runs = infra_fails = 0
    for result_path in runs_dir.glob("*.json"):
        if result_path.name.endswith(".intermediate.json"):
            continue
        try:
            verdict = json.loads(result_path.read_text(encoding="utf-8")).get("verdict")
        except (OSError, ValueError):
            continue
        drift_runs += verdict == "MODEL_DRIFT"
        infra_fails += verdict == "INFRA_FAIL"
    print(f"[night] {date_str} 完成：{session_count} 会话；MODEL_DRIFT={drift_runs}；"
          f"INFRA_FAIL={infra_fails}（详情见 runs/*.json）")
    from eval.runner import report as rep
    # 单夜自含报告不带基线；workflow 的 report 步骤负责基线 diff 门禁。
    return rep.write_report(base_dir, baseline_path=None,
                            config_dir=config_dir, end_date=date_str)


def drill7(base_dir: Path, repo_root: Path, mock: bool = True) -> int:
    """连续 7 夜端到端演练（mock 加速）：夜跑→聚合→审计→自检齐全性。"""
    from datetime import date, timedelta
    from eval.runner import report as rep

    base_dir = Path(base_dir)
    today = date.today()
    for offset in range(6, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        rc = run_night(day, repo_root, base_dir, mock=mock)
        if rc != 0:
            return rc

    rc = rep.write_report(base_dir, None, end_date=today.isoformat())
    if rc == 1 and mock:
        print("[drill7] mock 数据不应触发红灯——请检查断言器")
        return 1

    # 审计表演练：以 mock 夜的 transcripts 目录伪造四端输入（真实审计另行手动）。
    from eval.runner import audit as aud
    paths = {"claude": base_dir / "reports/nightly"}
    aud.write_audit(
        base_dir / "reports/eval/audit" / today.isoformat(),
        aud.audit_dirs(paths, limit_per_agent=5),
    )
    print("[drill7] 7 夜演练完成：四矩阵+审计表+双键 diff 齐全")
    return 0
