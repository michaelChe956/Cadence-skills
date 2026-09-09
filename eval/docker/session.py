"""Docker 容器化测试 session——完整用户流程：install.sh → 四命令 → 探针。"""
import json
import time
from pathlib import Path
from typing import Optional

from eval.docker.container import Container, create_test_container, REPO_ROOT

# 四命令安装流水线（stage1）
STAGE1_COMMANDS = [
    ("pre-check", "/pre-check no-interrupt --mirror cn"),
    ("mcp-configuration", "/mcp-configuration no-interrupt"),
    ("rule-config", "/rule-config no-interrupt"),
    ("project-rules-examples", "/project-rules-examples no-interrupt"),
]

# 测试项目初始化脚本（写成单独的 bash 脚本避免引号嵌套地狱）
PROJECT_INIT_SCRIPT = r"""
set -e
THEME=users
PROJ=/home/tester/project
mkdir -p $PROJ/src/$THEME $PROJ/assets
cd $PROJ
git init -q
git config user.email test@test.local
git config user.name tester
echo '{"name":"test-app","version":"1.0.0"}' > package.json

cat > src/$THEME/schema.sql << 'EOF'
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL,
  created_at TEXT NOT NULL
);
EOF

cat > src/$THEME/entry.py << 'EOF'
from src.users.service import handle

def main() -> None:
    handle(payload={})
EOF

cat > src/$THEME/service.py << 'EOF'
from src.users.repo import save

def handle(payload: dict) -> None:
    save(payload)
EOF

cat > src/$THEME/repo.py << 'EOF'
def save(payload: dict) -> None:
    print('saved')
EOF

# P7 真报错截图：assets/error_screenshot.jpg 在 create_test_project 里注入
# （用户 Android 真机截图 JPEG，文件名保持 .png——客户端按内容嗅探，先例 6ee4902）

git add -A && git commit -qm 'init'
echo "project created: $THEME module"
"""

def create_test_project(c: Container, theme: str = "users") -> None:
    """在容器内创建测试项目：基础项目 + P7 真截图 + 预置真 key MCP。"""
    c.exec(PROJECT_INIT_SCRIPT, timeout=30)
    c.copy_in(str(REPO_ROOT / "eval/docker/assets/error_screenshot.jpg"),
              "/home/tester/project/assets/error.png")
    _preset_mcp_real_keys(c)


def _preset_mcp_real_keys(c: Container) -> None:
    """预置带真实 key 的 zai MCP 块到容器项目。

    mcp-configuration 产品默认写占位符 key（等用户手动替换）；Docker 测试无人
    介入，P7 图片探针会因占位 key 全部 login fail。no-interrupt 模式下该命令
    对已有同名 server 保留现有配置（SKILL.md 合并语义），预置真 key 块存活。
    key 来源：宿主机仓库根 .mcp.json（本地已替换的真实配置，gitignored）。
    """
    import tempfile
    src = REPO_ROOT / ".mcp.json"
    if not src.exists():
        return
    try:
        servers = json.loads(src.read_text()).get("mcpServers", {})
    except ValueError:
        return
    zai = servers.get("zai-mcp-server")
    if not isinstance(zai, dict) or "your_" in json.dumps(zai):
        return  # 宿主机无真 key 配置——不预置，探针按占位符失败路径走

    # .mcp.json（kimi/pi/claude 读取）
    with tempfile.NamedTemporaryFile("w", suffix=".json",
                                     delete=False) as f:
        json.dump({"mcpServers": {"zai-mcp-server": zai}}, f,
                  ensure_ascii=False)
        tmp = f.name
    c.copy_in(tmp, "/home/tester/project/.mcp.json")
    Path(tmp).unlink()

    # .codex/config.toml（codex 读取）
    env_pairs = ", ".join(f'"{k}" = "{v}"'
                          for k, v in zai.get("env", {}).items())
    toml = (
        "[mcp_servers.zai-mcp-server]\n"
        f'command = "{zai.get("command", "npx")}"\n'
        f'args = {json.dumps(zai.get("args", ["-y", "@z_ai/mcp-server"]))}\n'
        f"env = {{ {env_pairs} }}\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".toml",
                                     delete=False) as f:
        f.write(toml)
        tmp = f.name
    c.exec("mkdir -p /home/tester/project/.codex")
    c.copy_in(tmp, "/home/tester/project/.codex/config.toml")
    Path(tmp).unlink()




def run_stage1(c: Container, agent: str) -> list:
    """运行四命令安装流水线，返回命令结果列表。"""
    results = []
    for name, prompt in STAGE1_COMMANDS:
        start = time.time()
        r = c.exec(_session_cmd(agent, prompt),
                   cwd="/home/tester/project", timeout=600)
        duration = time.time() - start
        results.append({
            "name": name, "returncode": r["rc"],
            "duration_s": round(duration, 1),
            "final_text": r["stdout"],
            "stderr": r["stderr"][-500:] if r["stderr"] else "",
        })
    _rebuild_codex_toml(c)
    return results


def _rebuild_codex_toml(c: Container) -> None:
    """从项目 .mcp.json 机械重建 .codex/config.toml（codex 专用）。

    mcp-configuration 由模型执行合并，写 TOML 偶发语义错误（实测：http_headers
    混入 stdio 块 → codex 加载失败，后续会话全部 0.1s 秒挂）。本函数在 stage1
    后按固定规则重写，保证 codex 拿到的配置永远合法：
    stdio server（command 字段）→ command/args/env；HTTP server（url 字段）
    → url/http_headers。仅测试装置使用；产品侧同步脚本化记为后续任务。
    """
    import tempfile
    r = c.exec("cat /home/tester/project/.mcp.json", timeout=15)
    if r["rc"] != 0 or not r["stdout"].strip():
        return
    try:
        servers = json.loads(r["stdout"]).get("mcpServers", {})
    except ValueError:
        return

    def _toml_val(v):
        return json.dumps(v, ensure_ascii=False)  # TOML 与 JSON 的字符串/数组字面量兼容

    blocks = []
    for name, srv in servers.items():
        if not isinstance(srv, dict):
            continue
        lines = [f"[mcp_servers.{name}]"]
        if "command" in srv:
            lines.append(f"command = {_toml_val(srv['command'])}")
            if srv.get("args"):
                lines.append(f"args = {_toml_val(srv['args'])}")
            if srv.get("env"):
                env_pairs = ", ".join(f"{_toml_val(k)} = {_toml_val(v)}"
                                      for k, v in srv["env"].items())
                lines.append(f"env = {{ {env_pairs} }}")
        elif "url" in srv:
            lines.append(f"url = {_toml_val(srv['url'])}")
            if srv.get("http_headers"):
                hdr = ", ".join(f"{_toml_val(k)} = {_toml_val(v)}"
                                for k, v in srv["http_headers"].items())
                lines.append(f"http_headers = {{ {hdr} }}")
        blocks.append("\n".join(lines))
    if not blocks:
        return
    toml = "\n\n".join(blocks) + "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
        f.write(toml)
        tmp = f.name
    c.exec("mkdir -p /home/tester/project/.codex")
    c.copy_in(tmp, "/home/tester/project/.codex/config.toml")
    Path(tmp).unlink()




def run_probe(c: Container, agent: str, prompt: str,
              timeout: int = 900, retries: int = 1) -> dict:
    """运行单个探针会话；超时（rc=-9）自动重试——glm/MCP 间歇 hang 已知问题。"""
    start = time.time()
    r = c.exec(_session_cmd(agent, prompt),
               cwd="/home/tester/project", timeout=timeout)
    while r["rc"] == -9 and retries > 0:
        retries -= 1
        print(f"    [probe-retry] 超时，重试（剩余 {retries}）")
        r = c.exec(_session_cmd(agent, prompt),
                   cwd="/home/tester/project", timeout=timeout)
    duration = time.time() - start
    return {
        "returncode": r["rc"], "duration_s": round(duration, 1),
        "final_text": r["stdout"], "stderr": r["stderr"][-500:] if r["stderr"] else "",
    }



def _cli_command(agent: str) -> str:
    """返回指定 agent 的 CLI 调用命令前缀。"""
    return {
        "claude": "claude -p",
        "codex": "codex exec --json -s danger-full-access",
        "pi": "pi -p",
        "kimi": "kimi -p",
    }.get(agent, "claude -p")


# 各端无头权限 flag：claude 跳权限确认；codex 由 -s danger-full-access 控制（无额外 flag）；
# pi 无权限门；kimi -p 模式本身自动执行（--auto 与 -p 互斥，实测报错）
_PERMISSION_FLAG = {
    "claude": "--dangerously-skip-permissions",
    "codex": "",
    "pi": "",
    "kimi": "",
}


def _session_cmd(agent: str, prompt: str) -> str:
    """构造完整的会话命令（CLI 前缀 + prompt + 按端权限 flag）。"""
    cmd = f'{_cli_command(agent)} "{prompt}"'
    flag = _PERMISSION_FLAG.get(agent, "")
    return f"{cmd} {flag}".strip()



def run_agent_session(agent: str, probe_prompts: list,
                      session_id: Optional[str] = None) -> dict:
    """运行一个 agent 的完整测试 session（一个容器）。"""
    if not session_id:
        session_id = str(int(time.time()))

    c = create_test_container(agent, session_id)
    try:
        create_test_project(c)
        before_snap = c.snapshot_fs("/home/tester/project")
        stage1_results = run_stage1(c, agent)
        after_snap = c.snapshot_fs("/home/tester/project")

        new_files = sorted(set(after_snap) - set(before_snap))
        changed_files = sorted(
            p for p in set(before_snap) & set(after_snap)
            if before_snap[p] != after_snap[p])
        removed_files = sorted(set(before_snap) - set(after_snap))

        probe_results = []
        for i, prompt in enumerate(probe_prompts):
            r = run_probe(c, agent, prompt)
            r["probe_index"] = i
            r["prompt"] = prompt[:80]
            probe_results.append(r)

        artifacts_cmd = (
            'echo "skills_claude: $(ls ~/.claude/skills/ 2>/dev/null | wc -l)"; '
            'echo "skills_agents: $(ls ~/.agents/skills/ 2>/dev/null | wc -l)"; '
            'echo "superpowers: $(ls ~/.agents/superpowers/skills/ 2>/dev/null | wc -l)"; '
            'echo "openspec_proj: $(ls ~/project/.claude/skills/openspec-* 2>/dev/null | wc -l)"; '
            'echo "rules: $(ls ~/project/.claude/rules/*.md 2>/dev/null | wc -l)"; '
            'echo "claude_md: $(test -f ~/project/CLAUDE.md && echo exists || echo missing)"; '
            'echo "mcp_json: $(test -f ~/project/.mcp.json && echo exists || echo missing)"; '
            'echo "gitignore: $(test -f ~/project/.gitignore && echo exists || echo missing)"; '
            'echo "project_rules: $(test -d ~/project/cadence/project-rules && echo exists || echo missing)"'
        )
        artifacts = c.exec(f'bash -c \'{artifacts_cmd}\'', timeout=30)
        artifacts_dict = {}
        for line in artifacts["stdout"].strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                artifacts_dict[k.strip()] = v.strip()

        return {
            "agent": agent, "session_id": session_id,
            "stage1": stage1_results,
            "stage1_ok": all(r["returncode"] == 0 for r in stage1_results),
            "probes": probe_results,
            "fs_diff": {
                "new": new_files, "changed": changed_files,
                "removed": removed_files,
                "total_new": len(new_files), "total_changed": len(changed_files),
            },
            "artifacts": artifacts_dict,
        }
    finally:
        c.destroy()
