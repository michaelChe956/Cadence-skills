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

    # npm 国内源（CLI 安装 + pi 首启装 mcp-adapter 都走 npm，默认源国内不稳）
    c.exec("npm config set registry https://registry.npmmirror.com", timeout=30)
    # uv/uvx 国内源（默认 PyPI 国内慢——MCP server 冷下载瓶颈）
    c.exec("mkdir -p ~/.config/uv && printf '[[index]]\\n"
           "url = \"https://pypi.tuna.tsinghua.edu.cn/simple\"\\n"
           "default = true\\n' > ~/.config/uv/uv.toml", timeout=30)

    cli_map = {
        "claude": "npm install -g @anthropic-ai/claude-code",
        "codex": "npm install -g @openai/codex",
        "pi": "npm install -g @earendil-works/pi-coding-agent",
        "kimi": "",  # kimi 是 ELF 二进制（非 npm），下方从宿主机直接复制
    }
    if cli_map.get(agent):
        c.exec(cli_map[agent], timeout=300)

    if agent == "kimi":
        kimi_bin = Path.home() / ".kimi-code/bin/kimi"
        c.copy_in(str(kimi_bin), "/usr/local/bin/kimi")
        c.exec("chmod +x /usr/local/bin/kimi")

    # MCP server 包预热——避免会话启动时 npx/uvx 冷下载：npm 进度输出会污染
    # stdio JSON-RPC 通道（rmcp Deserialize error → codex 间歇性启动 hang 实测根因）。
    # 清单对应 mcp-configuration 生成的标准 server 集。
    for pkg in ("@z_ai/mcp-server", "@upstash/context7-mcp",
                "@modelcontextprotocol/server-sequential-thinking"):
        c.exec(f"npx -y {pkg} --version >/dev/null 2>&1 || true", timeout=180)
    for uvx_pkg in ("mcp-server-time", "minimax-coding-plan-mcp"):
        c.exec(f"uvx {uvx_pkg} --help >/dev/null 2>&1 || true", timeout=180)

    _copy_auth(c, agent)

    # 复制工作树并运行 install.sh
    c.exec("mkdir -p /home/tester/.agents")
    c.copy_in(str(REPO_ROOT), "/home/tester/.agents/Cadence-skills")
    # 工作树当前分支可能无 origin 跟踪（本地特性分支），install.sh 的 update
    # 路径要求 tracking 分支否则 set -e 提前退出、技能层完全不装（skills=0）
    c.exec("git -C /home/tester/.agents/Cadence-skills branch "
           "--set-upstream-to=origin/main", timeout=30)
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
            # provider 网关+密钥在 models.json（auth.json 实测为空对象）
            (home / ".pi/agent/models.json", "/home/tester/.pi/agent/models.json"),
            # settings.json 需去掉 packages 清单——见下方特殊处理
        ],
        "kimi": [
            (home / ".kimi-code/credentials", "/home/tester/.kimi-code/credentials"),
            (home / ".kimi-code/config.toml", "/home/tester/.kimi-code/config.toml"),
            (home / ".kimi-code/device_id", "/home/tester/.kimi-code/device_id"),
            (home / ".kimi-code/region", "/home/tester/.kimi-code/region"),
            (home / ".kimi-code/oauth", "/home/tester/.kimi-code/oauth"),
        ],
    }
    # 通用
    auth_files["__common__"] = [
        (home / ".gitconfig", "/home/tester/.gitconfig"),
    ]

    for src, dst in auth_files.get(agent, []) + auth_files["__common__"]:
        if src.exists():
            c.copy_in(str(src), dst)

    if agent == "pi":
        _copy_pi_settings_without_packages(c)


def _copy_pi_settings_without_packages(c: Container) -> None:
    """复制 pi settings.json 但去掉 packages 清单（否则首启装 275MB 扩展包）。"""
    import json
    import tempfile
    src = Path.home() / ".pi/agent/settings.json"
    if not src.exists():
        return
    data = json.loads(src.read_text())
    data.pop("packages", None)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f, ensure_ascii=False)
        tmp = f.name
    c.copy_in(tmp, "/home/tester/.pi/agent/settings.json")
    Path(tmp).unlink()
