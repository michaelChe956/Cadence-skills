#!/usr/bin/env bash
# POC-2: 容器内完整安装 Cadence + claude 探针测试
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONTAINER_NAME="cadence-poc2-$$"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
WORK_DIR="/tmp/cadence-poc2-${TIMESTAMP}"

echo "=== POC-2: 容器内安装 Cadence + claude 探针 ==="
mkdir -p "${WORK_DIR}"

# ── 1: 启动容器 ──
echo -e "\n[1/7] 启动容器..."
podman run -d --name "${CONTAINER_NAME}" \
  --network bridge \
  localhost/cadence-test:latest \
  sleep infinity

cleanup() {
  echo -e "\n[清理] 删除容器..."
  podman rm -f "${CONTAINER_NAME}" 2>/dev/null || true
  rm -rf "${WORK_DIR}"
}
trap cleanup EXIT

# ── 2: 安装 CLI + 复制配置 ──
echo -e "\n[2/7] 安装 claude CLI..."
podman exec "${CONTAINER_NAME}" npm install -g @anthropic-ai/claude-code 2>&1 | tail -1
podman exec "${CONTAINER_NAME}" claude --version

echo "  复制认证+模型配置..."
podman exec "${CONTAINER_NAME}" mkdir -p /home/tester/.claude
podman cp ~/.claude/settings.json "${CONTAINER_NAME}:/home/tester/.claude/settings.json"
if [ -f ~/.claude/.credentials.json ]; then
  podman cp ~/.claude/.credentials.json "${CONTAINER_NAME}:/home/tester/.claude/.credentials.json"
fi
podman cp ~/.gitconfig "${CONTAINER_NAME}:/home/tester/.gitconfig"

# ── 3: 复制工作树代码 ──
echo -e "\n[3/7] 复制工作树代码..."
podman cp "${REPO_ROOT}/cadence-init" "${CONTAINER_NAME}:/home/tester/cadence-init"

# ── 4: 创建测试项目（含用户表 schema，P3 探针需要）──
echo -e "\n[4/7] 创建测试项目..."
podman exec "${CONTAINER_NAME}" bash -c '
  mkdir -p /home/tester/project/src/users
  cd /home/tester/project
  git init -q
  git config user.email "test@test.local"
  git config user.name "tester"

  echo "{\"name\":\"test-app\",\"version\":\"1.0.0\"}" > package.json

  cat > src/users/schema.sql << EOF
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL,
  created_at TEXT NOT NULL
);
EOF

  cat > src/users/entry.py << "PYEOF"
from src.users.service import handle

def main() -> None:
    handle(payload={})
PYEOF

  cat > src/users/service.py << "PYEOF"
from src.users.repo import save

def handle(payload: dict) -> None:
    save(payload)
PYEOF

  cat > src/users/repo.py << "PYEOF"
def save(payload: dict) -> None:
    print("saved")
PYEOF

  git add -A && git commit -qm "init: users module"
'
echo "  测试项目已创建（含 users 模块）"

# ── 5: 安装 superpowers（pre-check 需要，预装到容器避免网络等待）──
echo -e "\n[5/7] 安装 superpowers 到容器..."
podman exec "${CONTAINER_NAME}" bash -c '
  # 先检查 pre-check 是否能直接跑（它会自己 clone superpowers）
  # 如果网络可用就让 pre-check 自己装
  echo "  （由 pre-check 自动安装 superpowers）"
'

# ── 6: 运行 pre-check 安装 Cadence ──
echo -e "\n[6/7] 运行 pre-check 安装 Cadence..."
echo "  这会测试真实的安装流程（含 superpowers clone + openspec init + 软链创建）"
echo "  预计耗时 1-3 分钟..."

podman exec -w /home/tester/project \
  -e CLAUDE_CONFIG_DIR=/home/tester/.claude \
  "${CONTAINER_NAME}" \
  claude -p "/pre-check no-interrupt --mirror cn" \
  --allowedTools "Bash(bash */pre-check*)" "Bash(bash */install*)" "Bash(chmod *)" "Bash(ls *)" "Bash(cat *)" "Bash(find *)" "Bash(head *)" "Bash(tail *)" "Bash(grep *)" "Bash(wc *)" "Bash(git *)" "Bash(npm *)" "Bash(node *)" "Bash(mkdir *)" "Bash(ln *)" "Bash(which *)" "Bash(env *)" "Bash(echo *)" "Bash(cp *)" "Bash(mv *)" "Bash(sed *)" "Bash(awk *)" "Bash(sort *)" "Bash(uniq *)" "Bash(python3 *)" "Bash(npx *)" "Bash(uvx *)" "Bash(ast-grep *)" "Bash(codegraph *)" "Bash(openspec *)" "Read" \
  2>&1 | tee "${WORK_DIR}/precheck-output.txt"

echo -e "\n  pre-check 输出前 10 行："
head -10 "${WORK_DIR}/precheck-output.txt"

# ── 7: 验证安装结果 ──
echo -e "\n[7/7] 验证安装结果..."

echo "  检查四层软链："
podman exec "${CONTAINER_NAME}" bash -c '
  echo "    .claude/skills: $(ls ~/.claude/skills/ 2>/dev/null | wc -l) 个"
  echo "    .agents/skills: $(ls ~/.agents/skills/ 2>/dev/null | wc -l) 个"
  echo "    .agents/superpowers: $(ls ~/.agents/superpowers/skills/ 2>/dev/null | wc -l) 个"
  echo "    openspec 投影: $(ls ~/project/.claude/skills/openspec-* 2>/dev/null | wc -l) 个"
  echo "    CLAUDE.md: $(head -1 ~/project/CLAUDE.md 2>/dev/null || echo "不存在")"
  echo "    规则文件: $(ls ~/project/.claude/rules/*.md 2>/dev/null | wc -l) 个"
'

echo -e "\n  运行 P1 探针（检索优先级）："
podman exec -w /home/tester/project \
  -e CLAUDE_CONFIG_DIR=/home/tester/.claude \
  "${CONTAINER_NAME}" \
  claude -p "梳理 users 模块从入口到落库的调用链，输出调用链说明" \
  --allowedTools "Bash(*)" "Read" "mcp__codegraph__*" \
  2>&1 | tee "${WORK_DIR}/p1-output.txt"

echo -e "\n  P1 输出前 5 行："
head -5 "${WORK_DIR}/p1-output.txt"

echo -e "\n=== POC-2 完成 ==="
