#!/usr/bin/env bash
# POC-3: 容器内技能安装 + pre-check + 探针测试
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONTAINER_NAME="cadence-poc3-$$"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
WORK_DIR="/tmp/cadence-poc3-${TIMESTAMP}"

echo "=== POC-3: 容器内技能安装 + pre-check + 探针 ==="
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
echo "[1/6] 安装 claude CLI..."
podman exec "${CONTAINER_NAME}" npm install -g @anthropic-ai/claude-code 2>&1 | tail -1
podman exec "${CONTAINER_NAME}" mkdir -p /home/tester/.claude
podman cp ~/.claude/settings.json "${CONTAINER_NAME}:/home/tester/.claude/settings.json"
[ -f ~/.claude/.credentials.json ] && podman cp ~/.claude/.credentials.json "${CONTAINER_NAME}:/home/tester/.claude/.credentials.json"
podman cp ~/.gitconfig "${CONTAINER_NAME}:/home/tester/.gitconfig"

# ── 2: 复制工作树 + 手动放技能链（模拟用户首次设置）──
echo "[2/6] 复制工作树 + 放技能链..."
podman cp "${REPO_ROOT}/cadence-init" "${CONTAINER_NAME}:/home/tester/cadence-init"
podman exec "${CONTAINER_NAME}" bash -c '
  # 模拟真实用户首次设置：把 Cadence 技能放到共享层+claude 层
  mkdir -p ~/.agents/skills ~/.claude/skills
  for skill in /home/tester/cadence-init/skills/*/; do
    name=$(basename "$skill")
    [ -f "$skill/SKILL.md" ] || continue
    ln -sf "$skill" ~/.agents/skills/"$name"
    ln -sf ~/.agents/skills/"$name" ~/.claude/skills/"$name"
  done
  echo "  技能链已创建: $(ls ~/.claude/skills/ | wc -l) 个"
'

# ── 3: 创建测试项目 ──
echo "[3/6] 创建测试项目..."
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

# ── 4: 运行 /pre-check（真实安装流程）──
echo "[4/6] 运行 /pre-check 安装..."
echo "  （含 superpowers clone + openspec init + 软链，预计 1-3 分钟）"
podman exec -w /home/tester/project \
  "${CONTAINER_NAME}" \
  claude -p "/pre-check no-interrupt --mirror cn" \
  --allowedTools "Bash" "Read" \
  2>&1 | tee "${WORK_DIR}/precheck.txt"

echo "  pre-check 输出（前 15 行）："
head -15 "${WORK_DIR}/precheck.txt"

# ── 5: 验证安装结果 ──
echo -e "\n[5/6] 验证安装结果..."
podman exec "${CONTAINER_NAME}" bash -c '
  echo "  superpowers: $(ls ~/.agents/superpowers/skills/ 2>/dev/null | wc -l) 个技能"
  echo "  openspec 投影: $(ls ~/project/.claude/skills/openspec-* 2>/dev/null | wc -l) 个"
  echo "  CLAUDE.md: $(head -1 ~/project/CLAUDE.md 2>/dev/null || echo "不存在")"
  echo "  规则文件: $(ls ~/project/.claude/rules/*.md 2>/dev/null | wc -l) 个"
  echo "  四层软链:"
  echo "    .claude/skills: $(ls ~/.claude/skills/ 2>/dev/null | wc -l)"
  echo "    .agents/skills: $(ls ~/.agents/skills/ 2>/dev/null | wc -l)"
  echo "    .codex/skills/skills: $(ls ~/.codex/skills/skills/ 2>/dev/null | wc -l)"
  echo "    .pi/agent/skills: $(ls ~/.pi/agent/skills/ 2>/dev/null | wc -l)"
'

# ── 6: 运行 P1 探针 ──
echo -e "\n[6/6] 运行 P1 探针（检索优先级）..."
podman exec -w /home/tester/project \
  "${CONTAINER_NAME}" \
  claude -p "梳理 users 模块从入口到落库的调用链，输出调用链说明" \
  --allowedTools "Bash" "Read" \
  2>&1 | tee "${WORK_DIR}/p1.txt"

echo -e "\n  P1 输出（前 8 行）："
head -8 "${WORK_DIR}/p1.txt"

echo -e "\n=== POC-3 完成 ==="
