#!/usr/bin/env bash
# POC-5: 容器内完整四命令安装流水线 + 探针测试
# install.sh → pre-check → mcp-configuration → rule-config → project-rules-examples → P1 探针
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONTAINER_NAME="cadence-poc5-$$"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
WORK_DIR="/tmp/cadence-poc5-${TIMESTAMP}"

echo "=== POC-5: 完整四命令安装流水线 + 探针 ==="
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
echo "[1/9] 安装 claude CLI..."
podman exec "${CONTAINER_NAME}" npm install -g @anthropic-ai/claude-code 2>&1 | tail -1
podman exec "${CONTAINER_NAME}" mkdir -p /home/tester/.claude /home/tester/.agents
podman cp ~/.claude/settings.json "${CONTAINER_NAME}:/home/tester/.claude/settings.json"
[ -f ~/.claude/.credentials.json ] && podman cp ~/.claude/.credentials.json "${CONTAINER_NAME}:/home/tester/.claude/.credentials.json"
podman cp ~/.gitconfig "${CONTAINER_NAME}:/home/tester/.gitconfig"

# ── 2: install.sh 安装 Cadence 技能 ──
echo "[2/9] 运行 install.sh..."
podman cp "${REPO_ROOT}" "${CONTAINER_NAME}:/home/tester/.agents/Cadence-skills"
podman exec "${CONTAINER_NAME}" bash /home/tester/.agents/Cadence-skills/install.sh 2>&1 | tail -3

# ── 3: 创建测试项目 ──
echo "[3/9] 创建测试项目..."
podman exec "${CONTAINER_NAME}" bash -c '
  mkdir -p /home/tester/project/src/users /home/tester/project/assets
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
  # P7 探针图片（用 python 生成避免 shell 转义问题）
  python3 -c "import base64; open('assets/error.png','wb').write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='))" 
  git add -A && git commit -qm "init: users module + error.png"
'

run_claude() {
  local prompt="$1" label="$2" outfile="$3"
  echo -e "\n  [${label}] prompt: ${prompt:0:40}"
  podman exec -w /home/tester/project \
    "${CONTAINER_NAME}" \
    claude -p "${prompt}" \
    --dangerously-skip-permissions \
    2>&1 | tee "${outfile}"
  echo "  [${label}] 输出长度: $(wc -c < "${outfile}") 字节"
}

# ── 4: /pre-check ──
echo -e "\n[4/9] /pre-check..."
run_claude "/pre-check no-interrupt --mirror cn" "pre-check" "${WORK_DIR}/01-precheck.txt"

# ── 5: /mcp-configuration ──
echo -e "\n[5/9] /mcp-configuration..."
run_claude "/mcp-configuration no-interrupt" "mcp-config" "${WORK_DIR}/02-mcp.txt"

# ── 6: /rule-config ──
echo -e "\n[6/9] /rule-config..."
run_claude "/rule-config no-interrupt" "rule-config" "${WORK_DIR}/03-rule.txt"

# ── 7: /project-rules-examples ──
echo -e "\n[7/9] /project-rules-examples..."
run_claude "/project-rules-examples no-interrupt" "prx" "${WORK_DIR}/04-prx.txt"

# ── 8: 验证全部安装产物 ──
echo -e "\n[8/9] 验证安装产物..."
podman exec "${CONTAINER_NAME}" bash -c '
  echo "  === HOME 层 ==="
  echo "  ~/.claude/skills: $(ls ~/.claude/skills/ 2>/dev/null | wc -l) 个"
  echo "  ~/.agents/skills: $(ls ~/.agents/skills/ 2>/dev/null | wc -l) 个"
  echo "  ~/.agents/superpowers: $(ls ~/.agents/superpowers/skills/ 2>/dev/null | wc -l) 个技能"
  echo ""
  echo "  === 项目层 ==="
  echo "  CLAUDE.md: $(head -1 ~/project/CLAUDE.md 2>/dev/null || echo "不存在")"
  echo "  规则文件: $(ls ~/project/.claude/rules/*.md 2>/dev/null | wc -l) 个"
  echo "  openspec 投影: $(ls ~/project/.claude/skills/openspec-* 2>/dev/null | wc -l) 个"
  echo "  .mcp.json: $(test -f ~/project/.mcp.json && echo "存在" || echo "不存在")"
  echo "  cadence/project-rules: $(test -d ~/project/cadence/project-rules && echo "存在" || echo "不存在")"
  echo "  settings.json: $(test -f ~/project/.claude/settings.json && echo "存在" || echo "不存在")"
  echo "  .gitignore: $(test -f ~/project/.gitignore && echo "存在" || echo "不存在")"
'

# ── 9: P1 探针 ──
echo -e "\n[9/9] P1 探针..."
run_claude "梳理 users 模块从入口到落库的调用链，输出调用链说明" "P1" "${WORK_DIR}/05-p1.txt"

# ── 汇总 ──
echo -e "\n══════════════════════════════════════"
echo "POC-5 汇总"
echo "══════════════════════════════════════"
for f in "${WORK_DIR}"/0*.txt; do
  name=$(basename "$f" .txt)
  size=$(wc -c < "$f")
  # 检查是否含失败标记
  if grep -q "failed\|失败\|error\|Error" "$f" 2>/dev/null; then
    status="⚠️  可能有问题"
  else
    status="✅"
  fi
  echo "  ${name}: ${size}B ${status}"
done

echo -e "\n=== POC-5 完成 ==="
