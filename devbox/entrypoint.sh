#!/usr/bin/env bash
# cadence-entrypoint —— 容器首启编排，顺序固定（Contract 3；设计 4.4/4.5/4.7）：
#   1) git 对齐默认 + 轮询 env + 卷内依赖源配置刷新
#   2) render-auth 渲染鉴权（失败即拒启 exit 2）
#   3) stack 模板同步（/opt/cadence/stack ↔ $CADENCE_STACK_DIR；CHANGES.md 存在=用户改过→保留）
#   4) skills 首启安装/幂等更新（软失败：日志落盘+下次启动重试）
#   5) exec "$@"
set -euo pipefail

HOME_DIR="${HOME:?HOME 未设置}"
CADENCE_STACK_DIR="${CADENCE_STACK_DIR:-/cadence/stack}"
CADENCE_STACK_TEMPLATE_DIR="${CADENCE_STACK_TEMPLATE_DIR:-/opt/cadence/stack}"
CADENCE_RENDER_AUTH="${CADENCE_RENDER_AUTH:-/usr/local/lib/cadence/render-auth.py}"
CADENCE_AUTH_FILE="${CADENCE_AUTH_FILE:-/cadence/auth.yaml}"
CADENCE_INSTALL_MIRRORS=(
  "https://ghfast.top/https://raw.githubusercontent.com/michaelChe956/Cadence-skills/main/install.sh"
  "https://gh-proxy.com/https://raw.githubusercontent.com/michaelChe956/Cadence-skills/main/install.sh"
  "https://raw.githubusercontent.com/michaelChe956/Cadence-skills/main/install.sh"
)
LOG_DIR="$HOME_DIR/.cadence/logs"
mkdir -p "$LOG_DIR"
log() { printf '[cadence-entrypoint] %s\n' "$*" | tee -a "$LOG_DIR/entrypoint.log" >&2; }

# ---------- 步骤 1：git 对齐默认 + 轮询 env + 卷内源配置 ----------
log "步骤 1/4：git 对齐与依赖源配置"
git config --global core.autocrlf true    # 与 git-for-windows 默认一致，避免换行符幻影 diff（设计 4.5）
git config --global core.filemode false   # Windows 盘无执行位语义，避免权限幻影 diff（设计 4.5）
export CHOKIDAR_USEPOLLING=1              # 跨挂载 inotify 不传播：vite/webpack 默认轮询（设计 4.5）
if ! grep -q 'cadence-entrypoint-env' "$HOME_DIR/.bashrc" 2>/dev/null; then
  cat >> "$HOME_DIR/.bashrc" <<'EOF'

# --- cadence-entrypoint-env：docker exec 会话同样拿到轮询与 PATH（幂等块）---
export CHOKIDAR_USEPOLLING=1
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$HOME/.kimi-code/bin:$PATH"
# --- cadence-entrypoint-env 结束 ---
EOF
fi
# ~/.m2、~/.gradle 是 named volume（首挂空卷会遮蔽镜像层）——每次启动幂等重写国内源配置
mkdir -p "$HOME_DIR/.m2" "$HOME_DIR/.gradle"
cat > "$HOME_DIR/.m2/settings.xml" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0">
  <mirrors>
    <mirror>
      <id>aliyun-central</id>
      <mirrorOf>central</mirrorOf>
      <name>aliyun public</name>
      <url>https://maven.aliyun.com/repository/public</url>
    </mirror>
  </mirrors>
</settings>
EOF
cat > "$HOME_DIR/.gradle/init.gradle" <<'EOF'
// aliyun maven 仓库镜像（gradle 发行版下载请看 devbox/README.md 的 tencent 镜像说明）
allprojects {
  repositories {
    maven { url 'https://maven.aliyun.com/repository/public' }
  }
}
buildscript {
  repositories {
    maven { url 'https://maven.aliyun.com/repository/public' }
  }
}
EOF

# ---------- 步骤 2：渲染鉴权（失败即拒启） ----------
log "步骤 2/4：渲染鉴权配置（cadence-box.yaml → 五端）"
if ! python3 "$CADENCE_RENDER_AUTH" --config "$CADENCE_AUTH_FILE" --home "$HOME_DIR"; then
  log "鉴权渲染失败（缺字段/格式错，明细见上方 render-auth 输出）——拒绝启动；请修正宿主侧 cadence-box.yaml 后重启容器"
  exit 2
fi

# ---------- 步骤 3：stack 模板同步 ----------
log "步骤 3/4：同步 stack 官方模板"
if [ -f "$CADENCE_STACK_DIR/CHANGES.md" ]; then
  log "检测到 CHANGES.md（用户/agent 已改动）：保留当前 $CADENCE_STACK_DIR，不自动覆盖；新版模板差异请人工比对 /opt/cadence/stack"
else
  mkdir -p "$CADENCE_STACK_DIR"
  cp -a "$CADENCE_STACK_TEMPLATE_DIR/catalog" "$CADENCE_STACK_DIR/"
  cp -f "$CADENCE_STACK_TEMPLATE_DIR/compose.yaml" "$CADENCE_STACK_DIR/compose.yaml"
  cp -f "$CADENCE_STACK_TEMPLATE_DIR/docker-compose.no-sock.yml" "$CADENCE_STACK_DIR/docker-compose.no-sock.yml"
  log "stack 模板已同步为镜像内置版本（.env 与 CHANGES.md 不在同步范围）"
fi

# ---------- 步骤 4：skills 首启安装/幂等更新（软失败） ----------
boot_skills() {
  local repo="$HOME_DIR/.agents/Cadence-skills" url
  if [ -d "$repo/.git" ]; then
    git -C "$repo" pull --ff-only || return 1
    bash "$repo/install.sh" || return 1
  else
    for url in "${CADENCE_INSTALL_MIRRORS[@]}"; do
      curl -fsSL --retry 2 --max-time 60 "$url" -o /tmp/cadence-install.sh || continue
      bash /tmp/cadence-install.sh && return 0
    done
    return 1
  fi
}

log "步骤 4/4：安装/更新 Cadence-skills（软失败不阻断）"
if ! boot_skills; then
  log "警告：skills 安装/更新失败——容器与 agent 仍可用；日志已落 $LOG_DIR/entrypoint.log，下次启动自动重试"
fi

# ---------- 步骤 5：移交主进程 ----------
log "就绪：exec $*"
exec "$@"
