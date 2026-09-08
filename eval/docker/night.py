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
        if "error" in text.lower() or "失败" in text:
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

        # 产物清单
        arts = c.exec(
            'bash -c \'echo "$(ls ~/.claude/skills/ 2>/dev/null | wc -l),'
            '$(ls ~/.agents/superpowers/skills/ 2>/dev/null | wc -l),'
            '$(ls ~/project/.claude/rules/*.md 2>/dev/null | wc -l),'
            '$(test -f ~/project/CLAUDE.md && echo Y || echo N),'
            '$(test -f ~/project/.mcp.json && echo Y || echo N)\'',
            timeout=15)
        arts_parts = arts["stdout"].strip().split(",")
        artifacts = {
            "skills": arts_parts[0] if len(arts_parts) > 0 else "?",
            "superpowers": arts_parts[1] if len(arts_parts) > 1 else "?",
            "rules": arts_parts[2] if len(arts_parts) > 2 else "?",
            "claude_md": arts_parts[3] if len(arts_parts) > 3 else "?",
            "mcp_json": arts_parts[4] if len(arts_parts) > 4 else "?",
        }
        print(f"[docker-night] 产物: skills={artifacts['skills']} "
              f"superpowers={artifacts['superpowers']} rules={artifacts['rules']}")

        # 运行探针
        print(f"[docker-night] 开始探针...")
        probe_results = []
        for pid in probe_ids:
            probe = PROBES[pid]
            prompt = probe["prompt_variants"][0].replace("{module}", "users")
            prompt = prompt.replace("<fixture>", "/home/tester/project")

            print(f"  [{pid}] {prompt[:50]}...")
            r = run_probe(c, agent, prompt)
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


if __name__ == "__main__":
    import sys
    agent = sys.argv[1] if len(sys.argv) > 1 else "claude"
    probe_ids = sys.argv[2].split(",") if len(sys.argv) > 2 else ["P1", "P3", "P5"]
    result = run_docker_night(agent, probe_ids)
    print(json.dumps(result["probe_summary"], ensure_ascii=False))
