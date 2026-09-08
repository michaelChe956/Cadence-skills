"""Docker 容器化夜测——完整 runner：容器→安装→探针→评分→报告。"""
import json
import time
from pathlib import Path
from typing import Optional

from eval.docker.container import Container, create_test_container, REPO_ROOT
from eval.docker.session import (
    create_test_project, run_stage1, run_probe, _cli_command,
)
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


def _score_probe_text(agent: str, probe_id: str, probe_result: dict) -> dict:
    """基于文本的探针评分（Docker 简化版）。

    后续增强：从容器提取完整 transcript（claude 的 .claude/projects/），
    用 adapter 解析出 tool_calls 后走 assertor.score_run 完整评分。
    """
    probe = PROBES[probe_id]
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
        session_id = str(int(time.time()))

    print(f"[docker-night] agent={agent} session={session_id}")
    print(f"[docker-night] probes: {probe_ids}")

    c = create_test_container(agent, session_id)
    try:
        # 创建测试项目
        create_test_project(c)
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

        # 安装后快照
        after = c.snapshot_fs("/home/tester/project")
        new_files = sorted(set(after) - set(before))
        changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])

        # 产物清单（逐行 key:value 解析，跨端稳定）
        artifacts = _collect_artifacts(c)
        print(f"[docker-night] 产物: skills={artifacts.get('skills')} "
              f"superpowers={artifacts.get('superpowers')} rules={artifacts.get('rules')}")

        # 运行探针
        print(f"[docker-night] 开始探针...")
        probe_results = []
        for pid in probe_ids:
            probe = PROBES[pid]
            prompt = probe["prompt_variants"][0].replace("{module}", "users")
            prompt = prompt.replace("<fixture>", "/home/tester/project")

            print(f"  [{pid}] {prompt[:50]}...")
            r = run_probe(c, agent, prompt)
            r["stdout_raw"] = r["final_text"]
            r["final_text"] = _extract_final_text(agent, r["final_text"])
            r["probe_id"] = pid
            r["prompt"] = prompt[:80]

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

        return {
            "agent": agent, "session_id": session_id,
            "stage1_ok": stage1_ok,
            "stage1": stage1,
            "probes": probe_results,
            "probe_summary": {"passed": passed, "total": total},
            "artifacts": artifacts,
            "fs_diff": {"new": len(new_files), "changed": len(changed)},
        }

    finally:
        c.destroy()
        print(f"[docker-night] 容器已清理")

def _write_probe_result(agent: str, session_id: str, probe_r: dict) -> Path:
    """按 runner 聚合契约落盘单个探针结果（基线数据 + 失败诊断两用）。"""
    day = time.strftime("%Y-%m-%d")
    runs_dir = RESULT_ROOT / "reports" / "nightly" / day / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
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
    path = runs_dir / f"{doc['run_id']}.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path



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

