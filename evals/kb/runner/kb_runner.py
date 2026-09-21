#!/usr/bin/env python3
"""kb-eval 容器内编排器（单进程；容器常驻，失败退出后可 --resume 续跑）。

根目录分离：HOME=/home/tester（CLI+认证+技能，永不清）；
WORK=/home/tester/work（project+snapshots，prepare 只清这两项）；
RESULTS=/home/tester/results（唯一结果根：results.json/transcripts/runs/report.md）。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path("/home/tester")
WORK = HOME / "work"
RESULTS = HOME / "results"
PROJECT = WORK / "project"
BASE = WORK / "base"
GOLDEN = WORK / "project.golden"
SNAP = WORK / "snapshots"
REPO = Path("/opt/repo")
FIXTURE = REPO / "evals/kb/fixtures/standard"
ASSERTS = REPO / "evals/kb/assertions"
SKILLS_INSTALLED = HOME / ".agents/Cadence-skills/cadence-init/skills"
STAGES = ["bootstrap", "base-info", "api", "pages", "overview", "global-validation"]


def sh(cmd, cwd=None, timeout=120):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def load_results():
    p = RESULTS / "results.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"stages": {}, "probes": {}}


def save_results(res):
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- 0. 装端 ----------

def install_agent(agent, model):
    cfg = json.loads((REPO / "evals/kb/runner/agents.json").read_text(encoding="utf-8"))[agent]
    if cfg.get("install"):
        r = sh(cfg["install"], timeout=300)
        if r.returncode != 0:
            RESULTS.mkdir(parents=True, exist_ok=True)
            save_results({**load_results(), "degrade": f"cli-install-failed: {r.stderr[-200:]}"})
            print("CLI 安装失败", r.stderr[-300:]); sys.exit(3)
    bf = cfg.get("binary_from")
    if bf:
        (HOME / ".npm-global/bin").mkdir(parents=True, exist_ok=True)
        shutil.copy2("/mnt/kimi-bin", HOME / ".npm-global/bin/kimi")
        (HOME / ".npm-global/bin/kimi").chmod(0o755)
    ver = sh(f"{' '.join(cfg['cmd'][:1])} --version 2>&1 | head -1").stdout.strip()
    if "not installed" in ver:
        # npm 包为安装器壳：装官方原生二进制并链入 PATH（对齐 claude 2.x native 布局）
        r = sh("curl -fsSL https://claude.ai/install.sh | bash", timeout=300)
        native = HOME / ".local/bin/claude"
        if r.returncode == 0 and native.exists():
            ver = sh("cp ~/.local/bin/claude ~/.npm-global/bin/claude && chmod +x ~/.npm-global/bin/claude && claude --version 2>&1 | head -1").stdout.strip()
    res = load_results()
    res["cli_version"] = ver
    res["model"] = model or "default"
    save_results(res)
    return cfg


def install_auth(agent, model_override=None):
    """从 /mnt/auth/ 中转区拷入最终位置（tester 属主，父目录自建）。"""
    import json as _json
    cfg = _json.loads((REPO / "evals/kb/runner/agents.json").read_text(encoding="utf-8"))[agent]
    staging = Path("/mnt/auth")
    for src, dst in cfg["auth_files"]:
        name = Path(src).name
        src = staging / name
        if src.exists():
            target = Path(dst)
            target.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, target, dirs_exist_ok=True)
            else:
                shutil.copy2(src, target)
            if model_override and target.suffix == ".json":
                _apply_model_override(target, model_override)
    strip = cfg.get("strip_packages_from")
    if strip and Path(strip).exists():
        import json as _json
        d = _json.loads(Path(strip).read_text(encoding="utf-8"))
        d.pop("packages", None)
        Path(strip).write_text(_json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def _apply_model_override(settings_path: Path, model: str):
    """把 settings.json 中全部 *MODEL* 环境键统一改写为指定模型（网关模型池变化时用）。"""
    import json as _json
    d = _json.loads(settings_path.read_text(encoding="utf-8"))
    env = d.get("env", {})
    for k in list(env):
        if "MODEL" in k:
            env[k] = model
    settings_path.write_text(_json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def install_skills():
    if (HOME / ".agents/Cadence-skills/install.sh").exists():
        return
    dst = HOME / ".agents/Cadence-skills"
    sh("git config --global --add safe.directory /opt/repo/.git", timeout=15)
    # git clone 对象层复制：绕开宿主 root 属主工作树文件的读权限；
    # 自动获得 origin remote（install.sh update 路径要求）+ 完整 HEAD 检出
    r = sh(f"git clone -q /opt/repo/.git {dst}", timeout=120)
    if r.returncode != 0:
        print("git clone 失败:", r.stderr[-300:]); sys.exit(3)
    sh("tar -xf /mnt/overlay.tar -C " + str(dst), timeout=60)  # 工作树实态覆盖（未提交改动+新文件）
    r = sh(f"bash {HOME}/.agents/Cadence-skills/install.sh", timeout=300)
    if r.returncode != 0:
        print("install.sh 失败:", (r.stdout + r.stderr)[-300:]); sys.exit(3)


# ---------- 1. prepare ----------

def snapshot_fingerprint(files):
    lines = []
    for f in sorted(files, key=lambda p: p.name):
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        lines.append(f"{f.name}\t{h}")
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def prepare(variant):
    if PROJECT.exists():
        shutil.rmtree(PROJECT)
    if SNAP.exists():
        shutil.rmtree(SNAP)
    PROJECT.mkdir(parents=True)
    (RESULTS / "transcripts").mkdir(parents=True, exist_ok=True)
    (RESULTS / "runs").mkdir(parents=True, exist_ok=True)
    for item in FIXTURE.iterdir():
        if item.name in ("user-input-template", "change-package-F9", "埋点说明.md"):
            continue
        (shutil.copytree if item.is_dir() else shutil.copy2)(item, PROJECT / item.name)
    # F7：init=30 天（错误值）→ fix=7 天（真实 diff）
    export = PROJECT / "order-service/src/main/java/com/demo/order/service/ExportService.java"
    export.write_text(export.read_text(encoding="utf-8").replace("RETENTION_DAYS = 7", "RETENTION_DAYS = 30"), encoding="utf-8")
    sh("git init -q -b main && git config user.email t@t && git config user.name t && "
       "git add -A && git commit -qm 'init: demo 商城初始版本'", cwd=PROJECT)
    export.write_text(export.read_text(encoding="utf-8").replace("RETENTION_DAYS = 30", "RETENTION_DAYS = 7"), encoding="utf-8")
    sh("git add -A && git commit -qm '修复：导出文件保留期应为 7 天（原误配 30 天）'", cwd=PROJECT)
    repo_init = sh("git rev-list --max-parents=0 HEAD", cwd=PROJECT).stdout.strip()
    # 配置快照（只读+指纹）
    snap_dir = SNAP / "baseline-config"
    snap_dir.mkdir(parents=True)
    for c in sorted(PROJECT.glob("*/src/main/resources/application.yml")):
        shutil.copy2(c, snap_dir / (c.parents[3].name + "-application.yml"))
    fp = snapshot_fingerprint(sorted(snap_dir.iterdir()))
    sh(f"chmod -R a-w {SNAP}")
    # user-input 渲染
    ui = PROJECT / "cadence/knowledge-base/user-input"
    ui.mkdir(parents=True)
    for f in (FIXTURE / "user-input-template").iterdir():
        if variant == "min" and f.name == "product.md":
            continue
        t = f.read_text(encoding="utf-8")
        t = t.replace("{{REPO_INIT}}", repo_init).replace("{{SNAPSHOT_DIR}}", str(snap_dir)).replace("{{FINGERPRINT}}", fp)
        if variant == "min":
            t = t.split("## 业务知识证据")[0].rstrip() + "\n"
        (ui / f.name).write_text(t, encoding="utf-8")
    res = load_results()
    res.update({"variant": variant, "snapshot": {"dir": str(snap_dir), "fingerprint": fp, "readonly": True}})
    save_results(res)
    print(f"prepared: fingerprint={fp[:12]}… variant={variant}")


# ---------- 2. 阶段执行 ----------

def build_prompt(stage, budget):
    desc = {
        "bootstrap": "只执行输入校验、初始化判定、生成 manifest.yaml 与 input-inventory.md、coverage.initialization 置 in_progress；【边界】不得调用任何领域 Skill、不得执行 base-info",
        "base-info": "执行 knowledge-base-base-info 领域阶段（续跑语义），完成自身产物与阶段登记",
        "api": "执行 knowledge-base-api（全量模式：能力扫描/接口文档/EVENT-JOB 稳定 ID/组合诉求核实）",
        "pages": "执行 knowledge-base-pages（路由树/页面文档/候选登记）",
        "overview": "执行 knowledge-base-overview（README/glossary/business 域/capabilities CAP/横向边写矩阵并同批重建图）",
        "global-validation": "执行 bootstrap 的 global-validation 内置阶段（六项检查）并按结果登记",
    }[stage]
    return (f"你在 {PROJECT} 工作，执行 KnowledgeBase 阶段【{stage}】。\n"
            f"完整规则以 {SKILLS_INSTALLED}/ 下对应 SKILL.md 为准"
            f"（bootstrap/global-validation 读 knowledge-base-bootstrap/SKILL.md 及其 references/assets）。\n"
            f"{desc}。\n"
            f"约束：只读源码与 user-input；只写 cadence/knowledge-base/；敏感值一律 <redacted>；不连接外部系统。\n"
            f"预算：最多 {budget['max_turns']} 轮、单阶段 {budget['timeout_min']} 分钟。\n"
            f"完成后输出简短执行汇报。")


def run_cli(cfg, prompt, cwd, timeout_s):
    argv = list(cfg["cmd"]) + ([prompt] if cfg.get("prompt_arg") else [])
    env = dict(os.environ)
    env["EVAL_PROMPT"] = prompt
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout_s, env=env)
        return {"rc": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as e:
        return {"rc": 124, "stdout": (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
                "stderr": "TIMEOUT", "timed_out": True}


def parse_usage(stdout):
    for line in reversed(stdout.splitlines()):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if isinstance(d, dict) and d.get("type") == "result":
            u = d.get("usage") or {}
            return {"input": u.get("input_tokens"), "output": u.get("output_tokens"),
                    "cost_usd": d.get("total_cost_usd")}
    return None


def run_asserts(kb, script, extra):
    return subprocess.run(["python3", str(ASSERTS / script), "--kb-products", str(kb)] + extra,
                          capture_output=True, text=True)


def stage_products_ok(stage, kb):
    if stage == "bootstrap":
        return (kb / "manifest.yaml").exists() and (kb / "input-inventory.md").exists()
    return (kb / "manifest.yaml").exists()


def run_stage(stage, cfg, budget, resume):
    res = load_results()
    kb = PROJECT / "cadence/knowledge-base"
    if resume and res["stages"].get(stage, {}).get("ok") and stage_products_ok(stage, kb):
        print(f"[{stage}] 已成功，跳过（断点续跑）")
        return True
    t0 = time.time()
    r = run_cli(cfg, build_prompt(stage, budget), PROJECT, budget["timeout_min"] * 60)
    (RESULTS / "transcripts" / f"{stage}.log").write_text(
        f"$ {' '.join(cfg['cmd'])}\n--- stdout ---\n{r['stdout']}\n--- stderr ---\n{r['stderr']}\n", encoding="utf-8")
    a1 = run_asserts(kb, "tier0.py", ["--stage", stage])
    a2 = run_asserts(kb, "named.py", ["--stage", stage, "--variant", res.get("variant", "full")])
    a3 = run_asserts(kb, "negative.py", [])
    ok = r["rc"] == 0 and a1.returncode == 0 and a2.returncode == 0 and a3.returncode == 0
    passes = sum(s.stdout.count("PASS") for s in (a1, a2, a3) if s.stdout)
    res["stages"][stage] = {
        "ok": ok, "duration_s": round(time.time() - t0, 1), "usage": parse_usage(r["stdout"]),
        "transcript": f"transcripts/{stage}.log", "cli_rc": r["rc"],
        "asserts": {"tier0": a1.stdout.strip()[-800:], "named": a2.stdout.strip()[-800:], "negative": a3.stdout.strip()[-800:]},
    }
    save_results(res)
    _dump_run(f"kb-{stage}", stage, ok, [s.stdout for s in (a1, a2, a3)], r)
    print(f"[{stage}] {'PASS' if ok else 'FAIL'} ({res['stages'][stage]['duration_s']}s rc={r['rc']})")
    return ok


def _dump_run(run_id, item, verdict, assert_logs, cli_r):
    doc = {"run_id": f"{run_id}-{int(time.time())}", "item": item,
           "verdict": "PASS" if verdict else "FAIL",
           "fail_reason": "" if verdict else (cli_r["stderr"] or "断言失败")[:300],
           "duration_s": 0.0,
           "details": {"asserts": "\n".join(x[-300:] for x in assert_logs)}}
    (RESULTS / "runs" / f"{doc['run_id']}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- 3. 探针 ----------

PROBE_PROMPTS = {
    "P1": "我要对外提供全部用户信息，现有哪些能力可组合？限制是什么？（先执行 knowledge-base-context）",
    "P2": "订单取消后还能发货吗？（先执行 knowledge-base-context）",
    "P3": "执行 knowledge-base-update 消费 cadence/knowledge-base/user-input/updates/CHANGE-F9-REMOVE-ACCOUNT-API",
    "P4": "确认订单发货规则当前实现（先执行 knowledge-base-context）",
    "P5": "给用户表加一个最后登录时间字段 last_login_at，更新相关接口",
    "P6": "测试反馈账户余额出现了负数，排查一下哪里没拦住",
    "P7": "想给订单加一种'货到付款'支付方式，评估一下影响面",
    "P8": "运营要一份用户全景报表（基本信息+账户+订单），设计数据获取方案",
    "P9": "Review 这个改动：发货条件从仅 PAID 放宽为 PAID 或 CREATED，有没有问题？",
}


def inject_drift():
    f = PROJECT / "order-service/src/main/java/com/demo/order/service/OrderService.java"
    f.write_text(f.read_text(encoding="utf-8").replace(
        "只有 PAID 状态可以流转到 SHIPPED。", "只有 PAID 或 CREATED 状态可以流转到 SHIPPED。"), encoding="utf-8")


def apply_f9():
    (PROJECT / "account-service/src/main/java/com/demo/account/controller/AccountController.java").unlink()
    (PROJECT / "account-service/src/main/java/com/demo/account/service/AccountService.java").unlink()
    (PROJECT / "web-portal/src/views/AccountPage.vue").write_text(
        "<template><div><h2>账户查询</h2><p>该功能已迁移至新系统。</p></div></template>\n", encoding="utf-8")
    api = PROJECT / "web-portal/src/api/index.js"
    api.write_text("\n".join(l for l in api.read_text(encoding="utf-8").splitlines() if "queryAccount" not in l) + "\n", encoding="utf-8")
    base = sh("git rev-parse HEAD", cwd=PROJECT).stdout.strip()
    sh("git add -A && git commit -qm 'F9: 下线账户查询端点'", cwd=PROJECT)
    head = sh("git rev-parse HEAD", cwd=PROJECT).stdout.strip()
    pkg = PROJECT / "cadence/knowledge-base/user-input/updates/CHANGE-F9-REMOVE-ACCOUNT-API"
    shutil.copytree(FIXTURE / "change-package-F9", pkg, dirs_exist_ok=True)
    branch = sh("git rev-parse --abbrev-ref HEAD", cwd=PROJECT).stdout.strip()
    res0 = load_results()
    snap = res0.get("snapshot", {})
    for fname in ("code-change.md", "configuration-change.md"):
        f = pkg / fname
        f.write_text(f.read_text(encoding="utf-8")
                     .replace("F9_BASE", base).replace("F9_HEAD", head)
                     .replace("{{BRANCH}}", branch)
                     .replace("{{SNAP_DIR}}", snap.get("dir", ""))
                     .replace("{{FINGERPRINT}}", snap.get("fingerprint", "")), encoding="utf-8")


P5_ALLOWED = {"db/init.sql", "user-service/src/main/java/com/demo/user/entity/UserEntity.java",
              "user-service/src/main/java/com/demo/user/mapper/UserMapper.java",
              "user-service/src/main/resources/mapper/UserMapper.xml",
              "user-service/src/main/java/com/demo/user/controller/UserBasicController.java",
              "user-service/src/main/java/com/demo/user/service/UserBasicService.java",
              # 前端消费方联动：表文档 §8/P5 上下文把 PAGE-user-list 列入影响面，更新展示属完整影响面行为
              "web-portal/src/views/UserList.vue", "web-portal/src/api/index.js"}


def git_status_set():
    out = sh("git status --porcelain", cwd=PROJECT).stdout
    return {re.sub(r"^.. ?", "", l) for l in out.splitlines() if l.strip()}


def probe_asserts(pid, txt, before_set):
    fails = []
    if pid == "P1":
        for kw, name in [("CAP-", "引用CAP"), ("/api/account/", "引用账户端点"), ("待确认", "JOIN_KEY限制显式")]:
            if kw not in txt:
                fails.append(name)
    elif pid == "P2":
        if "不可发货" not in txt:
            fails.append("命中发货规则")
    elif pid == "P3":
        if not ("待确认" in txt or "retired" in txt):
            fails.append("CAP失效传播")
    elif pid == "P4":
        if "漂移" not in txt or not ("有条件就绪" in txt or "阻断" in txt):
            fails.append("漂移分级输出")
    elif pid == "P5":
        after = git_status_set() - before_set
        if not after:
            fails.append("无代码改动")
        bad = {p for p in after
               if p not in P5_ALLOWED and not p.startswith("db/migrations/")}
        if bad:
            fails.append(f"改动越界: {sorted(bad)[:3]}")
        if not re.search(r"(data-models|interfaces)[/\\]|TABLE-[a-z]|API-[a-z]|PAGE-[a-z]|CAP-[a-z]|RULE-[a-z]|FLOW-[a-z]", txt):
            fails.append("未引用知识库文档")
    elif pid == "P6":
        if "余额不可为负" not in txt and "RULE-" not in txt:
            fails.append("引用余额规则")
    elif pid == "P7":
        if not ("OrderStatus" in txt or "状态流转" in txt or "FLOW-" in txt):
            fails.append("引用状态机")
    elif pid == "P8":
        if "CAP-" not in txt and txt.count("/api/") < 2:
            fails.append("引用组合或多端点")
    elif pid == "P9":
        hits = sum(kw in txt for kw in ("PAID", "规则", "漂移", "状态机"))
        if hits < 2:
            fails.append("未指出规则冲突")
    return fails




def _wait_kb_stable(kb_dir, quiet_s=5, timeout_s=300):
    """等待 KB 目录树稳定（非空且连续两次快照一致）——agent 原子重建（挪走→移回）
    的异步尾态可能持续数分钟，断言必须落在稳定态上。"""
    import os

    def snap():
        out = []
        for root, _dirs, files in os.walk(kb_dir):
            for f in files:
                q = Path(root) / f
                try:
                    out.append((str(q), q.stat().st_mtime_ns))
                except OSError:
                    pass
        return sorted(out)

    deadline = time.time() + timeout_s
    prev = None
    while time.time() < deadline:
        cur = snap()
        if cur and cur == prev:
            print(f"      [settle] KB 稳定（{len(cur)} 文件）")
            return
        prev = cur
        time.sleep(quiet_s)
    print("      [settle] 超时，按当前状态断言")

def run_probes(cfg, budget, fast, resume, probe_subset=None):
    res = load_results()
    if not all(res["stages"].get(s, {}).get("ok") for s in STAGES):
        for pid in PROBE_PROMPTS:
            res["probes"][pid] = {"ok": False, "blocked": True, "reason": "阶段A未全绿"}
        save_results(res)
        print("探针全部 blocked（阶段 A 未全绿）")
        return
    if not GOLDEN.exists():
        shutil.copytree(PROJECT, GOLDEN, symlinks=True)
    ids = ["P1"] if fast else list(PROBE_PROMPTS)
    if probe_subset:
        ids = [x for x in ids if x in probe_subset]
    for pid in ids:
        if resume and res["probes"].get(pid, {}).get("ok"):
            print(f"[{pid}] 已成功，跳过"); continue
        shutil.rmtree(PROJECT)
        shutil.copytree(GOLDEN, PROJECT, symlinks=True)
        before = git_status_set() if pid == "P5" else None
        if pid == "P3":
            apply_f9()
        if pid in ("P4", "P9"):
            inject_drift()
        t0 = time.time()
        prompt = (f"你在 {PROJECT} 工作。任务：{PROBE_PROMPTS[pid]}\n"
                  f"规则以 {SKILLS_INSTALLED}/ 对应 SKILL.md 为准；完成后输出完整回答。")
        r = run_cli(cfg, prompt, PROJECT, budget["timeout_min"] * 60)
        (RESULTS / "transcripts" / f"{pid}.log").write_text(r["stdout"] + "\n" + r["stderr"], encoding="utf-8")
        fails = probe_asserts(pid, r["stdout"], before)
        if pid == "P3":
            kb_probe = PROJECT / "cadence/knowledge-base"
            _wait_kb_stable(kb_probe)
            import os as _os
            try:
                print(f"      [direct] listdir={sorted(_os.listdir(kb_probe))[:6]} manifest={ (kb_probe / 'manifest.yaml').exists() }")
            except Exception as e:
                print(f"      [direct] 异常: {type(e).__name__}: {e}")
            kb = PROJECT / "cadence/knowledge-base"
            for script, args in [
                    ("named.py", ["--kb-products", str(kb), "--stage", "update",
                                  "--phase", "post-update", "--variant", res.get("variant", "full")]),
                    ("tier0.py", ["--kb-products", str(kb), "--stage", "update"]),
                    ("negative.py", ["--kb-products", str(kb)])]:
                pa = subprocess.run(["python3", str(ASSERTS / script)] + args,
                                    capture_output=True, text=True)
                if pa.returncode != 0:
                    fails.append(f"产物断言失败:{script}: " + ";".join(
                        l.strip() for l in pa.stdout.splitlines() if "FAIL" in l)[:400])
        if r["rc"] != 0:
            fails.append(f"cli_rc={r['rc']}")
        res = load_results()
        res["probes"][pid] = {"ok": not fails, "failures": fails, "duration_s": round(time.time() - t0, 1),
                              "transcript": f"transcripts/{pid}.log", "usage": parse_usage(r["stdout"])}
        save_results(res)
        _dump_run(f"kb-{pid}", pid, not fails, ["\n".join(fails)], r)
        print(f"[{pid}] {'PASS' if not fails else 'FAIL ' + str(fails)}")




# ---------- 4. 报告 ----------

def report():
    res = load_results()
    lines = ["# kb-eval 报告", "",
             f"- 端：{res.get('agent', '?')}  变体：{res.get('variant')}  CLI：{res.get('cli_version', '?')}", "",
             "| 项 | 结果 |", "|---|---|"]
    for s in STAGES:
        v = res["stages"].get(s)
        lines.append(f"| 阶段 {s} | {'✅' if v and v['ok'] else '❌'} |")
    for pid in PROBE_PROMPTS:
        v = res["probes"].get(pid)
        mark = "⏸" if v and v.get("blocked") else ('✅' if v and v["ok"] else '❌')
        lines.append(f"| 探针 {pid} | {mark} |")
    base_file = RESULTS / "baseline-results.json"
    if base_file.exists():
        bl = json.loads(base_file.read_text(encoding="utf-8"))
        for k in set(bl.get("stages", {})) | set(res.get("stages", {})):
            a, b = bl.get("stages", {}).get(k, {}).get("ok"), res["stages"].get(k, {}).get("ok")
            if a != b:
                lines.append(f"\n具名 diff：阶段 {k} 基线 {'PASS' if a else 'FAIL'} → {'PASS' if b else 'FAIL'}")
    for grp in ("stages", "probes"):
        for k, v in res.get(grp, {}).items():
            if v and not v.get("ok"):
                lines.append(f"\n失败 transcript：{v.get('transcript')}")
                break
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    passed = sum(1 for v in res["stages"].values() if v.get("ok")) + \
             sum(1 for v in res["probes"].values() if v.get("ok"))
    total = len(res["stages"]) + len(res["probes"])
    print(f"报告：{RESULTS / 'report.md'}（{passed}/{total} 通过）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--variant", default="full")
    ap.add_argument("--fixture", default="standard", choices=["standard", "large"],
                    help="fixture 规模（large=standard+12 噪声服务，关键词影子）")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--model", default="")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--restore-kb", default="", help="用归档知识库产物跳过阶段A（如 /opt/repo/evals/kb/results/.../knowledge-base）")
    ap.add_argument("--probes", default="", help="只跑指定探针（逗号分隔，如 P3）")
    ap.add_argument("--arm", choices=["kb", "nokb"], default="",
                    help="价值实验配对臂（kb=提供知识库环境 / nokb=无知识库）")
    ap.add_argument("--cases", default="", help="价值实验案例子集（如 S2-A,S4-A 或 S2,S4）")
    ap.add_argument("--batch", default="", help="价值实验批次标识")
    ap.add_argument("--max-turns", type=int, default=40)
    ap.add_argument("--timeout-min", type=int, default=20)
    a = ap.parse_args()
    global FIXTURE
    FIXTURE = REPO / f"evals/kb/fixtures/{a.fixture}"
    budget = {"max_turns": a.max_turns, "timeout_min": a.timeout_min}
    cfg = install_agent(a.agent, a.model)
    install_auth(a.agent, a.model or None)
    install_skills()
    if a.arm:
        # 价值实验：准备干净基线快照，然后调用 value_experiment
        if not a.resume:
            prepare(a.variant)
            if BASE.exists():
                shutil.rmtree(BASE)
            # 稳定 git 对象库（避免 copytree 与后台松散对象回收竞态）
            sh("git gc -q", cwd=PROJECT)
            # 基线 = 纯源码 + git 两步历史（无 cadence/）；偶发竞态重试 3 次
            for _ in range(3):
                try:
                    shutil.copytree(PROJECT, BASE, symlinks=True)
                    break
                except shutil.Error:
                    if BASE.exists():
                        shutil.rmtree(BASE)
            else:
                raise SystemExit("BASE 快照拷贝失败（git 对象竞态）")
            cad = BASE / "cadence"
            if cad.exists():
                shutil.rmtree(cad)
        if a.model:
            cfg = dict(cfg)
            cfg["cmd"] = list(cfg["cmd"]) + ["--model", a.model]
        sys.path.insert(0, str(Path(__file__).parent))
        import value_experiment
        sys.exit(value_experiment.run(cfg, budget, a))
    if not a.resume:
        prepare(a.variant)
        res = load_results()
        res.update({"agent": a.agent, "budget": budget})
        save_results(res)
    else:
        print("resume：跳过 prepare")
    if a.restore_kb:
        src = Path(a.restore_kb)
        dst = PROJECT / "cadence/knowledge-base"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        res = load_results()
        for s in STAGES:
            res["stages"][s] = {"ok": True, "duration_s": 0, "restored": True}
        save_results(res)
        print(f"已恢复归档知识库：{src}（六阶段标记完成）")
    cfg = dict(cfg)
    if a.model:
        cfg["cmd"] = list(cfg["cmd"]) + ["--model", a.model]
    for stage in STAGES:
        if not run_stage(stage, cfg, budget, a.resume):
            report(); sys.exit(1)
    run_probes(cfg, budget, a.fast, a.resume, a.probes.split(",") if a.probes else None)
    report()
    res = load_results()
    if any(not v.get("ok") for v in res.get("probes", {}).values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
