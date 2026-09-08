"""Docker 容器生命周期管理——每个测试 session 一个新容器，用完销毁。"""
import subprocess
import time
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_NAME = "localhost/cadence-test:latest"


class Container:
    """一个测试容器实例。用完调 destroy()。"""

    def __init__(self, name: str, agent: str):
        self.name = name
        self.agent = agent
        self._started = False

    def start(self) -> None:
        """启动容器。"""
        subprocess.run(
            ["podman", "run", "-d", "--name", self.name,
             "--network", "bridge", IMAGE_NAME, "sleep", "infinity"],
            check=True, capture_output=True)
        self._started = True

    def exec(self, cmd: str, cwd: str = "/home/tester",
             env: Optional[dict] = None, timeout: int = 300) -> dict:
        """在容器内执行命令，返回 {rc, stdout, stderr}。"""
        argv = ["podman", "exec", "-w", cwd]
        if env:
            for k, v in env.items():
                argv += ["-e", f"{k}={v}"]
        argv += [self.name, "bash", "-c", cmd]
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
            return {"rc": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
        except subprocess.TimeoutExpired:
            return {"rc": -9, "stdout": "", "stderr": f"timeout after {timeout}s"}

    def copy_in(self, src: str, dst: str) -> None:
        """从宿主机复制文件/目录到容器。"""
        # 确保目标父目录存在
        parent = str(Path(dst).parent)
        self.exec(f"mkdir -p {parent}")
        subprocess.run(["podman", "cp", src, f"{self.name}:{dst}"],
                       check=True, capture_output=True)

    def copy_out(self, src: str, dst: str) -> None:
        """从容器复制文件/目录到宿主机。"""
        subprocess.run(["podman", "cp", f"{self.name}:{src}", dst],
                       check=True, capture_output=True)

    def destroy(self) -> None:
        """停止并删除容器。"""
        if self._started:
            subprocess.run(["podman", "rm", "-f", self.name],
                           capture_output=True)
            self._started = False

    def snapshot_fs(self, path: str = "/home/tester") -> dict:
        """文件系统快照（路径→hash），用于前后对比。"""
        r = self.exec(
            f"find {path} -type f -not -path '*/.git/*' -not -path '*/node_modules/*' "
            f"-not -path '*/__pycache__/*' | sort | xargs sha256sum 2>/dev/null",
            timeout=60)
        snap = {}
        for line in r["stdout"].strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("  ", 1)
            if len(parts) == 2:
                snap[parts[1].strip()] = parts[0]
        return snap


def create_test_container(agent: str, session_id: str) -> Container:
    """创建测试容器并完成基础设置（CLI 安装+认证复制）。

    完整流程：
    1. 启动 Arch 容器
    2. 安装指定 agent 的 CLI
    3. 复制认证+模型配置（从宿主机 ~/.claude 等目录）
    4. 复制工作树代码（install.sh 源）
    5. 运行 install.sh 安装 Cadence 技能
    6. 创建测试项目
    """
    name = f"cadence-{agent}-{session_id}"
    c = Container(name, agent)
    c.start()

    # 安装 CLI
    cli_map = {
        "claude": "npm install -g @anthropic-ai/claude-code",
        "codex": "npm install -g @openai/codex",
        "pi": "",   # pi 通过 npm 全局安装，路径不同
        "kimi": "",  # kimi 安装方式待确认
    }
    if cli_map.get(agent):
        c.exec(cli_map[agent], timeout=120)

    # 复制认证+模型配置（按 agent 不同）
    _copy_auth(c, agent)

    # 复制工作树并运行 install.sh
    c.exec("mkdir -p /home/tester/.agents")
    c.copy_in(str(REPO_ROOT), "/home/tester/.agents/Cadence-skills")
    c.exec("bash /home/tester/.agents/Cadence-skills/install.sh", timeout=120)

    return c


def _copy_auth(c: Container, agent: str) -> None:
    """从宿主机复制认证+模型配置到容器（只复制'能用'的最小集）。"""
    home = Path.home()
    auth_files = {
        "claude": [
            (home / ".claude/settings.json", "/home/tester/.claude/settings.json"),
            (home / ".claude/.credentials.json", "/home/tester/.claude/.credentials.json"),
        ],
        "codex": [
            (home / ".codex/auth.json", "/home/tester/.codex/auth.json"),
            (home / ".codex/config.toml", "/home/tester/.codex/config.toml"),
            (home / ".codex/models.json", "/home/tester/.codex/models.json"),
        ],
        "pi": [
            (home / ".pi/agent/auth.json", "/home/tester/.pi/agent/auth.json"),
            (home / ".pi/agent/settings.json", "/home/tester/.pi/agent/settings.json"),
        ],
        "kimi": [
            (home / ".kimi-code/credentials", "/home/tester/.kimi-code/credentials"),
        ],
    }
    # 通用
    auth_files["__common__"] = [
        (home / ".gitconfig", "/home/tester/.gitconfig"),
    ]

    for src, dst in auth_files.get(agent, []) + auth_files["__common__"]:
        if src.exists():
            c.copy_in(str(src), dst)
