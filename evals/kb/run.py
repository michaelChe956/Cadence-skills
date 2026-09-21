#!/usr/bin/env python3
"""kb-eval 宿主机入口：podman 独立容器考场（与夜测零耦合）。

用法：
  python3 evals/kb/run.py --agent claude --variant full [--fast] [--model X] [--no-build]

流程：build → run -d 常驻容器（挂仓库只读+认证只读）→ exec kb_runner →
     成功：podman cp 结果 → rm；失败：容器保留并提示续跑命令。
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IMAGE = "cadence-kb-eval"


def sh(argv, **kw):
    print("+", " ".join(argv))
    return subprocess.run(argv, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="claude")
    ap.add_argument("--variant", default="full")
    ap.add_argument("--fixture", default="standard")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--model", default="")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--restore-kb", default="")
    ap.add_argument("--no-kb", action="store_true")
    ap.add_argument("--arm", default="", choices=["", "kb", "nokb"])
    ap.add_argument("--cases", default="")
    ap.add_argument("--batch", default="")
    ap.add_argument("--timeout-min", type=int, default=0)
    ap.add_argument("--probes", default="")
    a = ap.parse_args()

    agents = json.loads((REPO / "evals/kb/runner/agents.json").read_text(encoding="utf-8"))
    if a.agent not in agents:
        sys.exit(f"未知端 {a.agent}；可用：{list(agents)}")

    if not a.no_build:
        r = sh(["podman", "build", "-t", IMAGE, str(REPO / "evals/kb/docker")])
        if r.returncode != 0:
            sys.exit("镜像构建失败")

    name = f"kb-eval-{a.agent}"
    sh(["podman", "rm", "-f", name])  # 幂等：清掉旧考场

    argv = ["podman", "run", "-d", "--userns=keep-id", "--name", name,
            "-v", f"{REPO}:/opt/repo:ro"]
    # 认证按端挂载到中转区（只读；单文件直挂目标路径会让 podman 以 root 预建父目录，
    # 导致 tester 无法在其下建 skills——由 kb_runner 拷入最终位置）
    for src, dst in agents[a.agent]["auth_files"]:
        host = Path(src).expanduser()
        if host.exists():
            argv += ["-v", f"{host}:/mnt/auth/{host.name}:ro"]
        else:
            print(f"警告：认证文件不存在，跳过挂载 {host}")
    bf = agents[a.agent].get("binary_from")
    if bf:
        host_bin = Path(bf[0]).expanduser()
        if host_bin.exists():
            argv += ["-v", f"{host_bin}:/mnt/kimi-bin:ro"]
        else:
            print(f"警告：二进制不存在 {host_bin}")
    # overlay：工作树实态（含未提交改动与新文件）打包挂入，容器内覆盖 git clone
    # （clone 只含已提交对象；本仓库产物自动提交关闭，技能最新文本未提交）
    import tarfile
    overlay = Path(f"/tmp/kb-eval-overlay-{a.agent}.tar")
    with tarfile.open(overlay, "w") as tf:
        for item in ["cadence-init", "evals", "install.sh"]:
            tf.add(REPO / item, arcname=item)
    argv += ["-v", f"{overlay}:/mnt/overlay.tar:ro"]
    argv += [IMAGE, "sleep", "infinity"]
    r = sh(argv)
    if r.returncode != 0:
        sys.exit("容器启动失败")

    inner = (f"python3 /opt/repo/evals/kb/runner/kb_runner.py "
             f"--agent {a.agent} --variant {a.variant} --fixture {a.fixture}")
    if a.fast:
        inner += " --fast"
    if a.model:
        inner += f" --model {a.model}"
    if a.restore_kb:
        inner += f" --restore-kb {a.restore_kb}"
    if a.probes:
        inner += f" --probes {a.probes}"
    if a.no_kb:
        inner += " --no-kb"
    if getattr(a, "arm", ""):
        inner += f" --arm {a.arm}"
    if getattr(a, "cases", ""):
        inner += f" --cases {a.cases}"
    if getattr(a, "batch", ""):
        inner += f" --batch {a.batch}"
    if a.timeout_min:
        inner += f" --timeout-min {a.timeout_min}"
    r = sh(["podman", "exec", "-w", "/home/tester", name, "bash", "-lc", inner])

    if getattr(a, "arm", ""):
        batch = a.batch or time.strftime("exp-%Y%m%d-%H%M%S")
        out = REPO / f"evals/kb/results/exp/{batch}/{a.agent}-{a.arm}"
    else:
        out = REPO / f"evals/kb/results/{time.strftime('%Y-%m-%d')}/{a.agent}-{a.variant}"
    if r.returncode == 0:
        out.mkdir(parents=True, exist_ok=True)
        cp = sh(["podman", "cp", f"{name}:/home/tester/results/.", str(out)])
        if not getattr(a, "arm", ""):
            # 拷出知识库产物树（golden=阶段A原始态；无 golden 时用 project 终态）
            kb_src = f"{name}:/home/tester/work/project.golden"
            if sh(["podman", "exec", name, "test", "-d", "/home/tester/work/project.golden"]).returncode != 0:
                kb_src = f"{name}:/home/tester/work/project"
            sh(["podman", "cp", kb_src, str(out / "knowledge-base")])
        sh(["podman", "rm", "-f", name])
        print(f"完成：结果已拷出 → {out}")
        sys.exit(cp.returncode)
    else:
        print(f"\n失败：容器保留（{name}），排查后可续跑：")
        print(f"  podman exec -w /home/tester {name} bash -lc '{inner} --resume'")
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
