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

# 1x1 PNG（P7 探针用）
python3 -c "
import struct, zlib
def chunk(tag, data):
    c = tag + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c))
ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 0, 0, 0, 0)
raw = b'\x00\x00'
idat = zlib.compress(raw)
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')
open('assets/error.png', 'wb').write(png)
"

git add -A && git commit -qm 'init'
echo "project created: $THEME module"
"""


def create_test_project(c: Container, theme: str = "users") -> None:
    """在容器内创建测试项目。"""
    c.exec(PROJECT_INIT_SCRIPT, timeout=30)


def run_stage1(c: Container, agent: str) -> list:
    """运行四命令安装流水线，返回命令结果列表。"""
    results = []
    cli_cmd = _cli_command(agent)
    for name, prompt in STAGE1_COMMANDS:
        start = time.time()
        r = c.exec(
            f'{cli_cmd} "{prompt}" --dangerously-skip-permissions',
            cwd="/home/tester/project", timeout=600)
        duration = time.time() - start
        results.append({
            "name": name, "returncode": r["rc"],
            "duration_s": round(duration, 1),
            "final_text": r["stdout"],
            "stderr": r["stderr"][-500:] if r["stderr"] else "",
        })
    return results


def run_probe(c: Container, agent: str, prompt: str) -> dict:
    """运行单个探针会话。"""
    start = time.time()
    cli_cmd = _cli_command(agent)
    r = c.exec(
        f'{cli_cmd} "{prompt}" --dangerously-skip-permissions',
        cwd="/home/tester/project", timeout=900)
    duration = time.time() - start
    return {
        "returncode": r["rc"], "duration_s": round(duration, 1),
        "final_text": r["stdout"], "stderr": r["stderr"][-500:] if r["stderr"] else "",
    }


def _cli_command(agent: str) -> str:
    """返回指定 agent 的 CLI 调用命令。"""
    return {
        "claude": "claude -p",
        "codex": "codex exec --json -s danger-full-access",
        "pi": "pi -p",
        "kimi": "kimi -p",
    }.get(agent, "claude -p")


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
