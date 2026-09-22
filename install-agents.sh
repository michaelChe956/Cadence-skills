#!/usr/bin/env bash
# 安装 / 备份 / 回滚用户级 subagent 规则与 agent 定义到 ~/.omp/agent/
#
# 分发策略（两者刻意不同）：
#   agent-rules/ → 符号链接：规则稳定，随仓库更新自动生效
#   agent-defs/  → 复制：模型链是本机配置，改动不应回流 git 工作区
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly RULES_SRC="$SCRIPT_DIR/agent-rules"
readonly DEFS_SRC="$SCRIPT_DIR/agent-defs"

readonly OMP_AGENT_DIR="${PI_CODING_AGENT_DIR:-$HOME/.omp/agent}"
readonly RULES_DST="$OMP_AGENT_DIR/rules"
readonly DEFS_DST="$OMP_AGENT_DIR/agents"
readonly BACKUP_ROOT="$OMP_AGENT_DIR/.backups"

DRY_RUN=0

log() { printf '[cadence-agents] %s\n' "$*"; }
warn() { printf '[cadence-agents][警告] %s\n' "$*" >&2; }
fail() { printf '[cadence-agents][错误] %s\n' "$*" >&2; return 1; }

run() {
  if (( DRY_RUN )); then
    printf '[cadence-agents][dry-run] %s\n' "$*"
  else
    "$@"
  fi
}

# 本脚本管理的符号链接判定：指向本仓库 agent-rules/ 才算，避免误删用户自有规则
is_managed_link() {
  local path="$1" target
  [[ -L "$path" ]] || return 1
  target="$(readlink "$path")" || return 1
  case "$target" in
    "$RULES_SRC"/*) return 0 ;;
    *) return 1 ;;
  esac
}

require_sources() {
  [[ -d "$RULES_SRC" ]] || { fail "规则源目录不存在：$RULES_SRC"; return 1; }
  [[ -d "$DEFS_SRC" ]] || { fail "定义源目录不存在：$DEFS_SRC"; return 1; }
  local n_rules n_defs
  n_rules="$(find "$RULES_SRC" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
  n_defs="$(find "$DEFS_SRC" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
  (( n_rules > 0 )) || { fail "规则源目录没有 .md 文件：$RULES_SRC"; return 1; }
  (( n_defs > 0 )) || { fail "定义源目录没有 .md 文件：$DEFS_SRC"; return 1; }
  log "源文件：规则 $n_rules 个，定义 $n_defs 个"
}

# ---------- 备份 ----------

do_backup() {
  local ts target
  ts="$(date +%Y%m%d-%H%M%S)"
  target="$BACKUP_ROOT/$ts"

  if [[ ! -d "$DEFS_DST" && ! -d "$RULES_DST" ]]; then
    log "无既有内容可备份（$OMP_AGENT_DIR 下无 agents/ 与 rules/）"
    return 0
  fi

  run mkdir -p "$target/agents" "$target/rules"

  if [[ -d "$DEFS_DST" ]]; then
    # 复制实体文件；符号链接解引用后存盘，保证备份自包含可回滚
    find "$DEFS_DST" -maxdepth 1 -name '*.md' -exec cp -aL {} "$target/agents/" \; 2>/dev/null || true
  fi
  if [[ -d "$RULES_DST" ]]; then
    find "$RULES_DST" -maxdepth 1 -name '*.md' -exec cp -aL {} "$target/rules/" \; 2>/dev/null || true
  fi
  [[ -f "$OMP_AGENT_DIR/config.yml" ]] && run cp -a "$OMP_AGENT_DIR/config.yml" "$target/" || true

  if (( ! DRY_RUN )); then
    # 记录哪些 rules 原本是本脚本管理的链接，回滚时才能还原成链接而非实体
    : > "$target/MANAGED_LINKS"
    if [[ -d "$RULES_DST" ]]; then
      local f
      for f in "$RULES_DST"/*.md; do
        [[ -e "$f" || -L "$f" ]] || continue
        is_managed_link "$f" && basename "$f" >> "$target/MANAGED_LINKS"
      done
    fi
    ( cd "$target" && find . -name '*.md' -exec md5sum {} \; > MANIFEST.md5 2>/dev/null ) || true
    log "备份完成：$target"
    log "  agents: $(find "$target/agents" -name '*.md' | wc -l | tr -d ' ') 个"
    log "  rules:  $(find "$target/rules" -name '*.md' | wc -l | tr -d ' ') 个"
  fi
  printf '%s\n' "$ts"
}

# ---------- 安装 ----------

do_install() {
  require_sources

  log "安装前自动备份"
  do_backup >/dev/null

  run mkdir -p "$RULES_DST" "$DEFS_DST"

  local f name dst
  log "分发规则（符号链接）→ $RULES_DST"
  for f in "$RULES_SRC"/*.md; do
    name="$(basename "$f")"
    dst="$RULES_DST/$name"
    if [[ -e "$dst" || -L "$dst" ]]; then
      if is_managed_link "$dst"; then
        run ln -sfn "$f" "$dst"
        log "  更新链接 $name"
        continue
      fi
      warn "  跳过 $name：已存在且非本脚本管理（如需替换请先手动移除）"
      continue
    fi
    run ln -sfn "$f" "$dst"
    log "  新建链接 $name"
  done

  log "分发定义（复制）→ $DEFS_DST"
  for f in "$DEFS_SRC"/*.md; do
    name="$(basename "$f")"
    dst="$DEFS_DST/$name"
    if [[ -f "$dst" ]] && cmp -s "$f" "$dst"; then
      log "  未变 $name"
      continue
    fi
    run cp -f "$f" "$dst"
    log "  写入 $name"
  done

  cat <<'EOF'

[cadence-agents] 安装完成。

⚠️  规则快照在会话启动时固定：正在运行的 omp 会话看不到新规则。
    请重启 omp，或在会话内执行 /clear 或 /new 后生效。
EOF
}

# ---------- 回滚 ----------

do_rollback() {
  local ts="${1:-}"
  [[ -d "$BACKUP_ROOT" ]] || { fail "无备份目录：$BACKUP_ROOT"; return 1; }

  if [[ -z "$ts" ]]; then
    ts="$(find "$BACKUP_ROOT" -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | sort | tail -1)"
    [[ -n "$ts" ]] || { fail "没有可用备份"; return 1; }
    log "未指定时间戳，使用最近一次备份：$ts"
  fi

  local src="$BACKUP_ROOT/$ts"
  [[ -d "$src" ]] || { fail "备份不存在：$src"; return 1; }

  run mkdir -p "$DEFS_DST" "$RULES_DST"

  local f name
  if [[ -d "$src/agents" ]]; then
    for f in "$src"/agents/*.md; do
      [[ -e "$f" ]] || continue
      run cp -f "$f" "$DEFS_DST/$(basename "$f")"
      log "  还原定义 $(basename "$f")"
    done
  fi

  if [[ -d "$src/rules" ]]; then
    for f in "$src"/rules/*.md; do
      [[ -e "$f" ]] || continue
      name="$(basename "$f")"
      # 备份时是本脚本管理的链接 → 还原为链接；否则还原为实体文件
      if [[ -f "$src/MANAGED_LINKS" ]] && grep -qxF "$name" "$src/MANAGED_LINKS" 2>/dev/null; then
        if [[ -f "$RULES_SRC/$name" ]]; then
          run ln -sfn "$RULES_SRC/$name" "$RULES_DST/$name"
          log "  还原链接 $name"
          continue
        fi
        warn "  $name 原为链接但源文件已不存在，改为还原实体副本"
      fi
      run cp -f "$f" "$RULES_DST/$name"
      log "  还原规则 $name"
    done
  fi

  log "回滚完成：$ts"
  log "⚠️  需重启 omp 会话（或 /clear、/new）才生效。"
}

list_backups() {
  [[ -d "$BACKUP_ROOT" ]] || { log "暂无备份"; return 0; }
  log "可用备份（$BACKUP_ROOT）："
  local d
  for d in "$BACKUP_ROOT"/*/; do
    [[ -d "$d" ]] || continue
    printf '  %s  (agents: %s, rules: %s)\n' \
      "$(basename "$d")" \
      "$(find "$d/agents" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')" \
      "$(find "$d/rules" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
  done
}

show_status() {
  log "目标目录：$OMP_AGENT_DIR"
  log "规则（$RULES_DST）："
  if [[ -d "$RULES_DST" ]]; then
    local f
    for f in "$RULES_DST"/*.md; do
      [[ -e "$f" || -L "$f" ]] || continue
      if is_managed_link "$f"; then
        printf '  [本脚本管理] %s\n' "$(basename "$f")"
      elif [[ -L "$f" ]]; then
        printf '  [外部链接]   %s -> %s\n' "$(basename "$f")" "$(readlink "$f")"
      else
        printf '  [实体文件]   %s\n' "$(basename "$f")"
      fi
    done
  else
    printf '  (目录不存在)\n'
  fi
  log "定义（$DEFS_DST）："
  if [[ -d "$DEFS_DST" ]]; then
    local f name
    for f in "$DEFS_DST"/*.md; do
      [[ -e "$f" ]] || continue
      name="$(basename "$f")"
      if [[ -f "$DEFS_SRC/$name" ]]; then
        if cmp -s "$f" "$DEFS_SRC/$name"; then
          printf '  [与源一致]   %s\n' "$name"
        else
          printf '  [本地已改]   %s\n' "$name"
        fi
      else
        printf '  [仅本地]     %s\n' "$name"
      fi
    done
  else
    printf '  (目录不存在)\n'
  fi
}

print_help() {
  cat <<'EOF'
用法: install-agents.sh <命令> [参数]

命令:
  install              备份后安装规则（符号链接）与 agent 定义（复制）
  backup               仅创建带时间戳的备份快照
  rollback [时间戳]    回滚到指定备份；省略时用最近一次
  list                 列出所有备份
  status               显示当前安装状态与本地改动
  help                 显示本帮助

选项:
  --dry-run            只打印将执行的动作，不落盘（可配合 install / backup / rollback）

分发策略:
  agent-rules/ → 符号链接到 ~/.omp/agent/rules/（规则随仓库更新）
  agent-defs/  → 复制到 ~/.omp/agent/agents/（模型链属本机配置，不回流 git）

注意:
  规则快照在会话启动时固定，安装后需重启 omp 或执行 /clear、/new 才生效。
EOF
}

main() {
  local cmd="" args=()
  while (( $# )); do
    case "$1" in
      --dry-run) DRY_RUN=1 ;;
      -h|--help|help) print_help; return 0 ;;
      *) if [[ -z "$cmd" ]]; then cmd="$1"; else args+=("$1"); fi ;;
    esac
    shift
  done

  case "$cmd" in
    install) do_install ;;
    backup) do_backup >/dev/null ;;
    rollback) do_rollback "${args[0]:-}" ;;
    list) list_backups ;;
    status) show_status ;;
    "") print_help; return 1 ;;
    *) fail "未知命令：$cmd"; print_help; return 1 ;;
  esac
}

main "$@"
