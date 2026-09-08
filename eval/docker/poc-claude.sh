#!/usr/bin/env bash
# POC: 一个容器 + claude 会话验证全链路
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONTAINER_NAME="cadence-poc-$$"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
WORK_DIR="/tmp/cadence-poc-${TIMESTAMP}"

echo "=== POC: 容器化 claude 全链路测试 ==="
mkdir -p "${WORK_DIR}"

# ── 1: 启动容器 ──
echo -e "\n[1/6] 启动容器..."
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

# ── 2: 安装 claude CLI ──
echo -e "\n[2/6] 安装 claude CLI..."
podman exec "${CONTAINER_NAME}" npm install -g @anthropic-ai/claude-code 2>&1 | tail -2
podman exec "${CONTAINER_NAME}" claude --version

# ── 3: 复制认证+模型配置 ──
echo -e "\n[3/6] 复制认证+模型配置..."
podman exec "${CONTAINER_NAME}" mkdir -p /home/tester/.claude
podman cp ~/.claude/settings.json "${CONTAINER_NAME}:/home/tester/.claude/settings.json"
if [ -f ~/.claude/.credentials.json ]; then
  podman cp ~/.claude/.credentials.json "${CONTAINER_NAME}:/home/tester/.claude/.credentials.json"
fi
podman cp ~/.gitconfig "${CONTAINER_NAME}:/home/tester/.gitconfig"
echo "  已复制认证配置"

# ── 4: 复制工作树代码 ──
echo -e "\n[4/6] 复制工作树代码..."
podman cp "${REPO_ROOT}/cadence-init" "${CONTAINER_NAME}:/home/tester/cadence-init"
echo "  已复制 cadence-init/"

# ── 5: 创建测试项目 ──
echo -e "\n[5/6] 创建测试项目..."
podman exec "${CONTAINER_NAME}" bash -c '
  mkdir -p /home/tester/project
  cd /home/tester/project
  git init -q
  git config user.email "test@test.local"
  git config user.name "tester"
  echo "{\"name\":\"test-app\",\"version\":\"1.0.0\"}" > package.json
  git add -A && git commit -qm "init"
'
echo "  测试项目已创建"

# ── 6: 运行 claude 会话 ──
echo -e "\n[6/6] 运行 claude 会话..."
echo "  prompt: 列出 cadence-init/skills/ 下有哪些技能目录"

podman exec -w /home/tester/project \
  "${CONTAINER_NAME}" \
  claude -p "列出 cadence-init/skills/ 下有哪些技能目录，只输出目录名列表" \
  --allowedTools "Bash(ls *)" \
  2>&1 | tee "${WORK_DIR}/claude-output.txt"

echo -e "\n=== POC 结果 ==="
if [ -s "${WORK_DIR}/claude-output.txt" ]; then
  echo "✅ claude 会话有输出"
  echo "--- 输出前 5 行 ---"
  head -5 "${WORK_DIR}/claude-output.txt"
else
  echo "❌ claude 会话无输出"
  exit 1
fi
