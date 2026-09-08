#!/usr/bin/env bash
# POC-4: 容器内用 install.sh 安装 + pre-check + 探针
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONTAINER_NAME="cadence-poc4-$$"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
WORK_DIR="/tmp/cadence-poc4-${TIMESTAMP}"

echo "=== POC-4: install.sh 全流程安装 + 探针 ==="
mkdir -p "${WORK_DIR}"

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

# ── 1: 安装 CLI + 复制配置 ──
echo "[1/7] 安装 claude CLI..."
podman exec "${CONTAINER_NAME}" npm install -g @anthropic-ai/claude-code 2>&1 | tail -1
podman exec "${CONTAINER_NAME}" mkdir -p /home/tester/.claude
podman cp ~/.claude/settings.json "${CONTAINER_NAME}:/home/tester/.claude/settings.json"
[ -f ~/.claude/.credentials.json ] && podman cp ~/.claude/.credentials.json "${CONTAINER_NAME}:/home/tester/.claude/.credentials.json"
podman cp ~/.gitconfig "${CONTAINER_NAME}:/home/tester/.gitconfig"

# ── 2: 运行 install.sh 安装 Cadence ──
echo "[2/7] 运行 install.sh 安装 Cadence..."
echo "  （会从镜像 clone Cadence-skills + 建立所有软链）"

# 先把本地代码复制到容器（模拟已有 clone），install.sh 会检测到并只建链
podman exec "${CONTAINER_NAME}" mkdir -p /home/tester/.agents
podman cp "${REPO_ROOT}" "${CONTAINER_NAME}:/home/tester/.agents/Cadence-skills"

# 运行 install.sh（检测到已有 repo，走 update/link 路径）
podman exec "${CONTAINER_NAME}" bash /home/tester/.agents/Cadence-skills/install.sh 2>&1 | tee "${WORK_DIR}/install.txt"

echo "  install.sh 输出（前 10 行）："
head -10 "${WORK_DIR}/install.txt"

# ── 3: 验证安装结果 ──
echo -e "\n[3/7] 验证技能链..."
podman exec "${CONTAINER_NAME}" bash -c '
  echo "  ~/.claude/skills: $(ls ~/.claude/skills/ 2>/dev/null | wc -l) 个"
  echo "  ~/.agents/skills: $(ls ~/.agents/skills/ 2>/dev/null | wc -l) 个"
  echo "  ~/.codex/skills/skills: $(ls ~/.codex/skills/skills/ 2>/dev/null | wc -l) 个"
  echo "  技能列表: $(ls ~/.claude/skills/ 2>/dev/null | head -5 | tr "\n" " ")..."
'

# ── 4: 创建测试项目 ──
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

# ── 5: 运行 /pre-check（现在技能应该可发现了）──
echo -e "\n[5/7] 运行 /pre-check..."
echo "  （安装 openspec 投影 + superpowers + 软链，预计 1-3 分钟）"
podman exec -w /home/tester/project \
  "${CONTAINER_NAME}" \
  claude -p "/pre-check no-interrupt --mirror cn" \
  --allowedTools "Bash" "Read" \
  2>&1 | tee "${WORK_DIR}/precheck.txt"

echo "  pre-check 输出（前 15 行）："
head -15 "${WORK_DIR}/precheck.txt"

# ── 6: 验证 pre-check 结果 ──
echo -e "\n[6/7] 验证安装结果..."
podman exec "${CONTAINER_NAME}" bash -c '
  echo "  superpowers: $(ls ~/.agents/superpowers/skills/ 2>/dev/null | wc -l) 个"
  echo "  openspec 投影: $(ls ~/project/.claude/skills/openspec-* 2>/dev/null | wc -l) 个"
  echo "  CLAUDE.md: $(head -1 ~/project/CLAUDE.md 2>/dev/null || echo "不存在")"
  echo "  四层软链:"
  echo "    .claude: $(ls ~/.claude/skills/ 2>/dev/null | wc -l)"
  echo "    .agents: $(ls ~/.agents/skills/ 2>/dev/null | wc -l)"
  echo "    .codex: $(ls ~/.codex/skills/skills/ 2>/dev/null | wc -l)"
  echo "    .pi: $(ls ~/.pi/agent/skills/ 2>/dev/null | wc -l)"
'

# ── 7: 运行 P1 探针 ──
echo -e "\n[7/7] 运行 P1 探针..."
podman exec -w /home/tester/project \
  "${CONTAINER_NAME}" \
  claude -p "梳理 users 模块从入口到落库的调用链，输出调用链说明" \
  --allowedTools "Bash" "Read" \
  2>&1 | tee "${WORK_DIR}/p1.txt"

echo -e "\n  P1 输出（前 8 行）："
head -8 "${WORK_DIR}/p1.txt"

echo -e "\n=== POC-4 完成 ==="
