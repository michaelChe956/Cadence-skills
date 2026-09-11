"""Docker 容器化夜测——完整 runner：容器→安装→探针→评分→报告。"""
import json
import re
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional

from eval.docker.container import Container, create_test_container, REPO_ROOT
from eval.docker.session import (
    create_test_project, run_stage1, run_probe, _cli_command,
)
from eval.install import assertions as inst_asrt
from eval.probes.definitions import PROBES
from eval.ifmt import IntermediateTrajectory, ToolCall
from eval.scoring import assertor
from eval.scoring import schema as result_schema

RESULT_ROOT = REPO_ROOT / "eval/results/docker-night"


def _make_trajectory(agent: str, probe_result: dict) -> IntermediateTrajectory:
    """从 Docker 探针结果构造评分用的 trajectory。"""
    traj = IntermediateTrajectory(agent=agent)
    traj.final_text = probe_result.get("final_text", "")
    traj.duration_s = probe_result.get("duration_s", 0.0)
    traj.returncode = probe_result.get("returncode", 0)
    # Docker 模式下 tool_calls 从 final_text 推断（简化——后续可从容器提取 transcript）
    # 目前先用文本匹配做基本断言
    return traj

# 探针会话 transcript 定位（容器内 HOME 相对，bash globstar）——mcp_called
# 真实性验证依赖：从会话文件解析 tool_calls，只有非错误调用才计「已调用」。
# omp 与 pi 同源（pi fork），复用 PiAdapter 解析。
SESSION_GLOBS = {
    "claude": ".claude/projects/**/*.jsonl",
    "codex": ".codex/sessions/**/*.jsonl",
    "pi": ".pi/agent/sessions/**/*.jsonl",
    "kimi": ".kimi-code/sessions/**/agents/*/wire.jsonl",
    "omp": ".omp/agent/sessions/**/*.jsonl",
}


def _snapshot_sessions(c, agent: str) -> dict:
    """容器内该端会话文件快照 {path: mtime}；不支持的端返回空。"""
    glob = SESSION_GLOBS.get(agent)
    if not glob:
        return {}
    cmd = ("bash -c 'shopt -s globstar; "
           f'stat -c "%Y %n" /home/tester/{glob} 2>/dev/null || true\'')
    out = {}
    for line in c.exec(cmd).get("stdout", "").splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            out[parts[1]] = float(parts[0])
    return out


def _attach_trajectory(c, agent: str, before: dict, after: dict, r: dict) -> None:
    """挑本次探针新建/更新的会话文件，解析出 trajectory 挂到结果上。

    解析失败不抛——留 _traj_error 供评分器给出「无法验证」的诚实判定。
    """
    newest, best = None, -1.0
    for path, mt in after.items():
        if before.get(path) == mt:
            continue
        if mt > best:
            newest, best = path, mt
    if not newest:
        return
    try:
        from eval.adapters import get_adapter
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / "session.jsonl"
            c.copy_out(newest, str(local))
            adapter = get_adapter("pi" if agent == "omp" else agent)
            r["_traj"] = adapter.parse_stream(
                local.read_text(encoding="utf-8", errors="replace").splitlines())
    except Exception as exc:  # noqa: BLE001 —— 解析失败降级为可观测错误
        r["_traj_error"] = str(exc)[:200]
def _score_probe_text(agent: str, probe_id: str, probe_result: dict) -> dict:
    """基于文本的探针评分（Docker 简化版）。

    后续增强：从容器提取完整 transcript（claude 的 .claude/projects/），
    用 adapter 解析出 tool_calls 后走 assertor.score_run 完整评分。
    """
    probe = PROBES.get(probe_id, {})
    text = probe_result.get("final_text", "")
    rc = probe_result.get("returncode", -1)
    failures = []

    if rc != 0:
        return {"verdict": "INFRA_FAIL", "failures": [f"rc={rc}"],
                "behavior": "FAIL", "behavior_failures": ["infra"]}

    # 按探针类型做文本级断言
    if probe_id == "P1":  # 检索优先级
        # 期望：提到调用链/架构相关内容
        if not any(kw in text for kw in ("调用链", "调用关系", "入口", "service", "handle")):
            failures.append("P1: 未产出调用链分析")
    elif probe_id == "P3":  # 时序合规
        # 期望：先分析再动手，或正确判断任务前提
        # 只匹配明确的任务失败声明——"TDD 先失败测试"等流程术语不算失败
        fail_signals = ("任务失败", "执行失败", "无法完成", "未能完成",
                        "出错了", "failed to", "encountered an error")
        if any(p in text.lower() for p in fail_signals):
            failures.append("P3: 报告失败")
    elif probe_id == "P5":  # 产物目录
        # 期望：提到文件产出/路径
        if not any(kw in text for kw in ("cadence", "文档", "部署", "方案")):
            failures.append("P5: 未产出部署文档")
    elif probe_id == "P7":  # 图片 MCP
        # 期望：分析图片内容
        if not any(kw in text for kw in ("图", "截图", "分析", "error", "报错")):
            failures.append("P7: 未分析图片")

    # 探针断言 spec 接线（R 组）：text_contains / text_lacks 对最终输出
    # （_extract_final_text 产物，即 final_text）逐条判定，消除
    # 「无关键字分支即 PASS」假绿；无 text_* 断言的探针（P 组）语义不变。
    for assertion in probe.get("assertions", []):
        kind = assertion.get("kind")
        if kind not in ("text_contains", "text_lacks"):
            continue
        pattern = assertion.get("pattern", "")
        if kind == "text_contains" and pattern not in text:
            failures.append(f"{probe_id}: text_contains 未命中 {pattern!r}")
        elif kind == "text_lacks" and pattern in text:
            failures.append(f"{probe_id}: text_lacks 命中禁止串 {pattern!r}")

    # mcp_called 三态判定（2026-09-11 二次修正）：docker 通道曾静默忽略该
    # 断言（rc=0 即 PASS，M 组假绿根因之二）；修复后一度二值化——无调用即
    # FAIL，但「未挂载」（headless 会话不加载项目级 HTTP MCP，客户端无过错）
    # 与「挂载了调不动」（真兼容问题）被混为一谈。三态：
    #   PASS          存在非错误调用（真实使用）
    #   FAIL          存在失败调用尝试（挂载了、调用失败=兼容性/网关问题）
    #   NOT_MOUNTED   无任何调用记录（会话未挂载该 MCP——观测不计，非客户端缺陷）
    not_mounted: list = []
    for assertion in probe.get("assertions", []):
        if assertion.get("kind") != "mcp_called":
            continue
        server = assertion.get("server", "")
        prefix = f"mcp__{server.replace('-', '_')}__"
        traj = probe_result.get("_traj")
        if traj is None:
            reason = probe_result.get("_traj_error") or "无 transcript"
            failures.append(f"{probe_id}: mcp_called[{server}] 无法验证（{reason}）")
            continue
        calls = [c for c in traj.tool_calls if prefix in c.tool]
        if any(not c.is_error for c in calls):
            continue  # 真实使用——不产生 failure
        if calls:
            failures.append(f"{probe_id}: mcp_called[{server}] 调用失败（挂载但未成=兼容性问题）")
        else:
            not_mounted.append(f"{probe_id}: mcp_called[{server}] 未挂载（会话无该工具，非客户端缺陷）")
    if not_mounted and not failures:
        return {
            "verdict": "NOT_MOUNTED", "failures": not_mounted,
            "behavior": "NOT_MOUNTED",
            "behavior_failures": ";".join(not_mounted),
        }
    behavior = "FAIL" if failures else "PASS"
    return {
        "verdict": "PASS" if not failures else "FAIL",
        "failures": failures,
        "behavior": behavior, "behavior_failures": ";".join(failures) if failures else None,
    }


def run_docker_night(agent: str, probe_ids: list,
                     session_id: Optional[str] = None) -> dict:
    """运行一个 agent 的 Docker 容器化夜测。

    完整流程：
    1. 创建容器 + 安装 CLI + 认证 + install.sh
    2. 创建测试项目
    3. 安装前快照
    4. 运行四命令安装流水线
    5. 安装后快照 + 产物验证
    6. 运行探针 + 评分
    7. 销毁容器
    """
    if not session_id:
        # 秒级时间戳 + pid：同端同秒并发/手抖重跑时容器名与 run_id 互不碰撞
        session_id = f"{int(time.time())}-{os.getpid()}"

    print(f"[docker-night] agent={agent} session={session_id}")
    print(f"[docker-night] probes: {probe_ids}")

    try:
        c = create_test_container(agent, session_id)
    except Exception as exc:  # 端级考场降级：不阻塞其他端，机器可读留痕
        reason = f"container-unavailable: {type(exc).__name__}: {exc}"[:200]
        print(f"[docker-night] ❌ 考场降级 {reason}")
        _write_degrade_result(agent, session_id, reason)
        return {
            "agent": agent, "session_id": session_id,
            "stage1_ok": False, "stage1": [],
            "probes": [], "probe_summary": {"passed": 0, "total": 0},
            "artifacts": {}, "fs_diff": {"new": 0, "changed": 0},
            "degrade": reason,
        }

    try:
        create_test_project(c, agent=agent)
        print(f"[docker-night] 项目已创建")

        # 安装前快照
        before = c.snapshot_fs("/home/tester/project")

        # 四命令安装流水线
        print(f"[docker-night] 开始四命令安装...")
        stage1 = run_stage1(c, agent)
        stage1_ok = all(r["returncode"] == 0 for r in stage1)
        for cmd in stage1:
            status = "✅" if cmd["returncode"] == 0 else "❌"
            print(f"  {status} {cmd['name']}: rc={cmd['returncode']} {cmd['duration_s']}s")

        # claude 端常载审计:stage1 安装会话已把装载记录写进 loaded.log——
        # 探针开始前截断清零,审计只看探针会话的 session_start 常载清单
        if agent == "claude":
            c.exec("truncate -s 0 /home/tester/project/loaded.log")

        # 安装后快照
        after = c.snapshot_fs("/home/tester/project")
        new_files = sorted(set(after) - set(before))
        changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])

        # 产物清单（逐行 key:value 解析，跨端稳定）
        artifacts = _collect_artifacts(c)
        print(f"[docker-night] 产物: skills={artifacts.get('skills')} "
              f"superpowers={artifacts.get('superpowers')} rules={artifacts.get('rules')}")
        # stage1 产物断言落盘（四条确定性断言；失败只写 FAIL 记录，不阻塞探针）
        stage1_record = _write_stage1_assertions(c, agent, session_id)
        print(f"[docker-night] stage1 断言记录: {stage1_record.name}")

        # 运行探针
        print(f"[docker-night] 开始探针...")
        probe_results = []
        for pid in probe_ids:
            probe = PROBES[pid]
            # (agents_only 端限定与 R3 rollout 审计已撤——2026-09-10 用户裁决)

            prompt = probe["prompt_variants"][0].replace("{module}", "users")
            prompt = prompt.replace("<fixture>", "/home/tester/project")

            print(f"  [{pid}] {prompt[:50]}...")
            _sess_before = _snapshot_sessions(c, agent)
            r = run_probe(c, agent, prompt)
            r["stdout_raw"] = r["final_text"]
            r["final_text"] = _extract_final_text(agent, r["final_text"])
            r["probe_id"] = pid
            r["prompt"] = prompt[:80]
            _attach_trajectory(c, agent, _sess_before,
                               _snapshot_sessions(c, agent), r)
            # 评分
            score = _score_probe_text(agent, pid, r)
            r["score"] = score
            status = "✅" if score["behavior"] == "PASS" else "❌"
            print(f"  [{pid}] {status} {score['behavior']} "
                  f"({r['duration_s']}s, {len(r.get('final_text',''))} chars)")
            if score.get("behavior_failures"):
                print(f"         failures: {score['behavior_failures']}")

            _write_probe_result(agent, session_id, r)

            probe_results.append(r)

        # 汇总
        passed = sum(1 for r in probe_results if r["score"]["behavior"] == "PASS")
        total = len(probe_results)

        result = {
            "agent": agent, "session_id": session_id,
            "stage1_ok": stage1_ok,
            "stage1": stage1,
            "probes": probe_results,
            "probe_summary": {"passed": passed, "total": total},
            "artifacts": artifacts,
            "fs_diff": {"new": len(new_files), "changed": len(changed)},
        }

        # claude 端常载审计结论进汇总 dict(其余端无此键);探针已全部跑完,
        # loaded.log 只含探针会话的装载事件
        if agent == "claude":
            log_text = c.exec("cat /home/tester/project/loaded.log")["stdout"]
            result["resident_audit"] = _audit_resident_rules(log_text)
            audit = result["resident_audit"]
            print(f"[docker-night] 常载审计: {audit['result']} "
                  f"loaded={audit['loaded']} violations={audit['violations']}")
            # 渐进受控证据落盘为 schema 1.0 记录(probe_id=resident)——
            # 透视表「渐进受控」行的数据源;条件桶/行为路由桶/媒体触发桶
            # 出现在 session_start 装载清单即 FAIL。
            _dump_run_record(result_schema.build_result(
                run_id=f"docker-{agent}-{session_id}-resident",
                agent=agent, probe_id="resident",
                verdict="PASS" if audit["result"] == "PASS" else "FAIL",
                fail_reason=";".join(audit.get("violations") or []),
                duration_s=0.0,
                details={"loaded": audit.get("loaded"),
                         "violations": audit.get("violations")},
            ))
        # (omp 端 R3 rollout 审计已撤——2026-09-10 用户裁决:agent 限定为 omp
        #  原生能力,由用户在项目规则中自行添加,框架与 eval 均不测试)
        return result

    finally:
        c.destroy()
        print(f"[docker-night] 容器已清理")

def _dump_run_record(doc: dict) -> Path:
    """run 记录按日落盘（reports/nightly/<day>/runs/<run_id>.json，三处落盘共用）。"""
    day = time.strftime("%Y-%m-%d")
    runs_dir = RESULT_ROOT / "reports" / "nightly" / day / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{doc['run_id']}.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path

def _write_probe_result(agent: str, session_id: str, probe_r: dict) -> Path:
    """按 runner 聚合契约落盘单个探针结果（基线数据 + 失败诊断两用）。"""
    score = probe_r["score"]
    doc = result_schema.build_result(
        run_id=f"docker-{agent}-{session_id}-{probe_r['probe_id']}",
        agent=agent, probe_id=probe_r["probe_id"],
        verdict=score["verdict"],
        fail_reason=";".join(score.get("failures", [])),
        duration_s=probe_r.get("duration_s", 0.0),
        details={
            "prompt": probe_r.get("prompt", ""),

            "final_text": probe_r.get("final_text", ""),
            "stdout_raw": probe_r.get("stdout_raw", ""),
            "stderr": probe_r.get("stderr", ""),
            "returncode": probe_r.get("returncode"),
            "behavior": score["behavior"],
            "behavior_failures": score.get("behavior_failures"),
        },
    )
    return _dump_run_record(doc)


# stage1 记录只取这四条净新增断言——docker 项目拷贝形态与 install runner fixture
# 不同，既有断言（零改动/HOME/投影）在拷贝上会误红，故按名字白名单过滤。
STAGE1_ASSERTION_NAMES = (
    "rules.frontmatter", "omp.symlinks", "omp.agents-md", "agents-md.budget",
)

# 容器内项目 → 宿主临时根的拷贝清单（只拷断言需要的子路径，避免整项目拷贝）
_STAGE1_COPY_PATHS = (
    ".claude/rules",    # rules.frontmatter 期望集合 / omp.symlinks 软链源
    ".agents/rules",    # omp.symlinks 软链实测
    ".omp/AGENTS.md",   # omp.agents-md 受管正文
    "AGENTS.md",        # agents-md.budget 行数
)


def _stage1_copy_project(c, root: Path) -> Path:
    """把断言需要的容器内子路径拷进宿主临时根（缺失路径跳过，由断言判红）。"""
    staged = root / "_staged"
    staged.mkdir()
    for rel in _STAGE1_COPY_PATHS:
        src = f"/home/tester/project/{rel}"
        probe = c.exec(f"test -e {src} && echo Y || echo N")["stdout"].strip()
        if not probe.endswith("Y"):
            continue
        one = staged / rel.replace("/", "_")  # 中转名，避免 podman cp 拷入已存在目录
        c.copy_out(src, str(one))
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(one), str(dst))
    return root


def _write_stage1_assertions(c, agent: str, session_id: str) -> Path:
    """stage1 后拷回容器内规则资产 → 四条确定性断言 → 写 stage1 记录（schema 1.0）。

    run_id=docker-<agent>-<session>-stage1；拷贝/断言异常不外抛——FAIL 留痕，
    绝不阻塞后续探针执行。
    """
    picked: list = []
    copy_error = ""
    try:
        with tempfile.TemporaryDirectory(prefix="stage1-assert-") as tmp:
            root = _stage1_copy_project(c, Path(tmp))
            picked = [r for r in inst_asrt.assert_stage1("docker", root, 0, {})
                      if r.name in STAGE1_ASSERTION_NAMES]
    except Exception as exc:  # 拷贝/断言崩溃：机器可读 FAIL 记录，不阻塞探针
        copy_error = f"stage1-assert-error: {type(exc).__name__}: {exc}"[:200]
        print(f"[docker-night] ⚠️ {copy_error}")
    bad = [r for r in picked if not r.ok]
    doc = result_schema.build_result(
        run_id=f"docker-{agent}-{session_id}-stage1",
        agent=agent, probe_id="stage1",
        verdict="FAIL" if (bad or copy_error) else "PASS",
        fail_reason=";".join(filter(None, [copy_error]
                                    + [f"{r.name}: {r.detail}" for r in bad])),
        duration_s=0.0,
        details={"assertions": [{"name": r.name, "ok": r.ok, "detail": r.detail}
                                for r in picked]},
    )
    return _dump_run_record(doc)

# claude 端常载审计:session_start 装载允许集——.claude/rules/ 下仅常驻桶
# (language.md)与目录页(README.md)可常载;条件桶/行为路由桶/媒体触发桶
# 出现在 session_start 装载清单即违规(它们应经 L0 路由按需装载)。
_RESIDENT_ALLOWED_RULES = ("language.md", "README.md")


def _audit_resident_rules(loaded_log_text: str) -> dict:
    """审计 loaded.log 的 session_start 常载清单(纯函数,离线可测)。

    loaded.log 由预置 InstructionsLoaded hook 追加写,每行一条事件 JSON
    (file_path + load_reason)。load_reason 非 session_start 的按需装载是
    渐进加载的正确行为,不计入审计;session_start 装载中 .claude/rules/ 下
    仅允许 _RESIDENT_ALLOWED_RULES 两文件,其余 → FAIL 并列出文件名(去重)。
    非 JSON 行/空行容错跳过。
    """
    loaded = 0
    violations: list = []
    for raw in loaded_log_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except ValueError:
            continue
        if not isinstance(evt, dict) or evt.get("load_reason") != "session_start":
            continue
        path = evt.get("file_path") or ""
        if not path:
            continue
        loaded += 1
        if ".claude/rules/" in path:
            name = path.rsplit("/", 1)[-1]
            if name not in _RESIDENT_ALLOWED_RULES and name not in violations:
                violations.append(name)
    return {"result": "FAIL" if violations else "PASS",
            "loaded": loaded, "violations": violations}

# (omp 端 R3 rollout 审计与 agents_only 端限定已撤——2026-09-10 用户裁决:
#  agent 限定是 omp 原生能力,由用户在项目规则中自行添加 agents: 字段,
#  框架与 eval 均不预置、不测试;标记/审计函数群随之移除。)

def _write_degrade_result(agent: str, session_id: str, reason: str) -> Path:
    """考场降级 run 记录（schema 1.0 + 顶层 degrade 字段；support-omp-client）。

    report_matrix 检测 degrade 字段时在透视输出打印降级注记。
    """
    doc = result_schema.build_result(
        run_id=f"docker-{agent}-{session_id}-degrade",
        agent=agent, probe_id="degrade",
        verdict="FAIL",
        fail_reason=reason,
        duration_s=0.0,
        details={"degrade": reason},
    )
    doc["degrade"] = reason
    return _dump_run_record(doc)


def _extract_final_text(agent: str, stdout: str) -> str:
    """codex 的 --json stdout 是 JSONL 流——提取 agent_message 纯文本用于评分。

    其他端 stdout 本身就是纯文本，原样返回。提取不到时回退原文（保留调试线索）。
    """
    if agent != "codex":
        return stdout
    texts = []
    for line in stdout.splitlines():
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        item = data.get("item")
        if (data.get("type") == "item.completed"
                and isinstance(item, dict)
                and item.get("type") == "agent_message"
                and isinstance(item.get("text"), str)):
            texts.append(item["text"])
    return "\n".join(texts) if texts else stdout


def _collect_artifacts(c) -> dict:
    """容器内产物清单（逐行 key:value）。"""
    r = c.exec(
        "echo skills:$(ls ~/.claude/skills/ 2>/dev/null | wc -l); "
        "echo agents_skills:$(ls ~/.agents/skills/ 2>/dev/null | wc -l); "
        "echo superpowers:$(ls ~/.agents/superpowers/skills/ 2>/dev/null | wc -l); "
        "echo rules:$(ls ~/project/.claude/rules/*.md 2>/dev/null | wc -l); "
        "echo claude_md:$(test -f ~/project/CLAUDE.md && echo Y || echo N); "
        "echo mcp_json:$(test -f ~/project/.mcp.json && echo Y || echo N)",
        timeout=15)
    out = {}
    for line in r["stdout"].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out
if __name__ == "__main__":
    import sys
    agent = sys.argv[1] if len(sys.argv) > 1 else "claude"
    probe_ids = sys.argv[2].split(",") if len(sys.argv) > 2 else ["P1", "P3", "P5"]
    result = run_docker_night(agent, probe_ids)
    print(json.dumps(result["probe_summary"], ensure_ascii=False))

