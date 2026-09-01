#!/usr/bin/env bash
set -euo pipefail

readonly REPOSITORY_URL="https://github.com/michaelChe956/Cadence-skills.git"
readonly MIRRORS=(
  "https://ghfast.top/https://github.com/michaelChe956/Cadence-skills.git"
  "https://gh-proxy.com/https://github.com/michaelChe956/Cadence-skills.git"
  "https://mirror.ghproxy.com/https://github.com/michaelChe956/Cadence-skills.git"
)
readonly REPO_DIR="$HOME/.agents/Cadence-skills"
readonly SOURCE_ROOT="$REPO_DIR/cadence-init/skills"
readonly SHARED_ROOT="$HOME/.agents/skills"
readonly CLAUDE_ROOT="$HOME/.claude/skills"
readonly CODEX_ROOT="$HOME/.codex/skills/skills"

: "$REPOSITORY_URL"

DRY_RUN=0
PLAN_ACTIONS=()
declare -A PLANNED_DIRS=()

log() { printf '[cadence] %s\n' "$*"; }
warn() { printf '[cadence][警告] %s\n' "$*" >&2; }
fail() { printf '[cadence][错误] %s\n' "$*" >&2; return 1; }

clone_with_rotation() {
  if [[ -e "$REPO_DIR" || -L "$REPO_DIR" ]]; then
    fail "安装目标已存在，clone_with_rotation 不会覆盖：$REPO_DIR"
    return 1
  fi

  mkdir -p "$HOME/.agents"
  local staging_root url
  local -a attempted=()
  staging_root="$(mktemp -d "${TMPDIR:-/tmp}/cadence-skills-clone.XXXXXX")"

  for url in "${MIRRORS[@]}"; do
    attempted+=("$url")
    rm -rf -- "$staging_root/repo"
    log "尝试镜像：$url"
    if git clone "$url" "$staging_root/repo"; then
      mv -T -- "$staging_root/repo" "$REPO_DIR"
      rmdir "$staging_root"
      log "已从镜像安装到：$REPO_DIR"
      return 0
    fi
    warn "镜像失败：$url"
  done

  rm -rf -- "$staging_root"
  printf '[cadence][错误] 三个镜像均失败，已尝试：%s\n' "${attempted[*]}" >&2
  printf '[cadence][错误] 不使用直连 GitHub，也不提供离线安装。\n' >&2
  return 1
}

update_repo() {
  local origin_url start_index=0 url tracking_ref branch index offset
  local -a attempted=()

  origin_url="$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null)" || {
    fail "仓库缺少 origin remote，无法执行 fetch --all / pull --ff-only：$REPO_DIR"
    return 1
  }

  for index in "${!MIRRORS[@]}"; do
    if [[ "$origin_url" == "${MIRRORS[$index]}" ]]; then
      start_index="$index"
      break
    fi
  done

  for offset in "${!MIRRORS[@]}"; do
    index=$(( (start_index + offset) % ${#MIRRORS[@]} ))
    url="${MIRRORS[$index]}"
    attempted+=("$url")
    log "使用镜像更新：$url"
    if git -C "$REPO_DIR" remote set-url origin "$url" && git -C "$REPO_DIR" fetch --all; then
      tracking_ref="$(git -C "$REPO_DIR" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
      if [[ "$tracking_ref" != origin/* ]]; then
        fail "当前分支没有 origin 跟踪分支，无法安全执行 pull --ff-only"
        return 1
      fi
      branch="${tracking_ref#origin/}"
      if git -C "$REPO_DIR" pull --ff-only origin "$branch"; then
        log "仓库已 fast-forward 更新：origin/$branch"
        return 0
      fi
      fail "pull --ff-only 失败；请检查 origin/$branch 是否发生非 fast-forward 改写，必要时删除仓库后重新安装"
      return 1
    fi
    warn "remote 设置或 fetch --all 失败，继续轮换镜像：$url"
  done

  printf '[cadence][错误] 更新所需镜像均失败，已尝试：%s\n' "${attempted[*]}" >&2
  printf '[cadence][错误] 请检查网络；若 fast-forward 更新或远程历史被改写，请删除仓库后重新运行安装。\n' >&2
  return 1
}

ensure_repo() {
  if [[ -e "$REPO_DIR" || -L "$REPO_DIR" ]]; then
    if git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      update_repo
      return 0
    fi
    printf '[cadence][错误] 目标已存在但不是 git 仓库：%s\n' "$REPO_DIR" >&2
    printf '请删除 ~/.agents/Cadence-skills 后重新运行\n' >&2
    return 1
  fi
  clone_with_rotation
}

is_git_repo() {
  [[ -d "$REPO_DIR" && ! -L "$REPO_DIR" ]] &&
    git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

is_managed_link() {
  local link_path="$1" link_dir link_name link_target shared_target expected_source
  [[ -L "$link_path" ]] || return 1
  link_dir="$(dirname -- "$link_path")"
  link_name="$(basename -- "$link_path")"
  expected_source="$REPO_DIR/cadence-init/skills/$link_name"
  link_target="$(readlink -- "$link_path" 2>/dev/null)" || return 1

  case "$link_dir" in
    "$SHARED_ROOT")
      [[ "$link_target" == "$expected_source" ]]
      ;;
    "$CLAUDE_ROOT"|"$CODEX_ROOT")
      [[ "$link_target" == "$SHARED_ROOT/$link_name" ]] || return 1
      [[ -L "$SHARED_ROOT/$link_name" ]] || return 1
      shared_target="$(readlink -- "$SHARED_ROOT/$link_name" 2>/dev/null)" || return 1
      [[ "$shared_target" == "$expected_source" ]]
      ;;
    *)
      return 1
      ;;
  esac
}

add_action() {
  PLAN_ACTIONS+=("$1"$'\t'"$2"$'\t'"$3"$'\t'"$4")
}

plan_ensure_dir() {
  local path="$1" parent
  parent="$(dirname -- "$path")"
  if [[ ! -d "$parent" && -z "${PLANNED_DIRS[$parent]+present}" ]]; then
    PLANNED_DIRS["$parent"]=1
    add_action "ENSURE-DIR" "$parent" "-" "链接父目录不存在"
  fi
}

plan_link() {
  local link_path="$1" desired_target="$2" link_target
  if [[ ! -e "$link_path" && ! -L "$link_path" ]]; then
    plan_ensure_dir "$link_path"
    add_action "CREATE" "$link_path" "$desired_target" "目标链接不存在"
    return 0
  fi

  if [[ ! -L "$link_path" ]]; then
    add_action "SKIP-WARN" "$link_path" "-" "已有普通文件或目录，禁止覆盖"
    return 0
  fi

  link_target="$(readlink -- "$link_path" 2>/dev/null || true)"
  if ! is_managed_link "$link_path"; then
    add_action "WARN-MANUAL" "$link_path" "$link_target" "无法证明所有权，跳过覆盖"
    return 0
  fi

  if [[ "$link_target" == "$desired_target" ]]; then
    add_action "KEEP" "$link_path" "$desired_target" "受管链接目标已正确"
  else
    plan_ensure_dir "$link_path"
    add_action "REPLACE" "$link_path" "$desired_target" "受管链接目标需要更新"
  fi
}

sync_one_link() {
  plan_link "$@"
}

plan_remove_link() {
  local link_path="$1" link_target="-"
  if [[ ! -e "$link_path" && ! -L "$link_path" ]]; then
    return 0
  fi
  if [[ -L "$link_path" ]]; then
    link_target="$(readlink -- "$link_path" 2>/dev/null || true)"
  else
    add_action "SKIP-WARN" "$link_path" "-" "已有普通文件或目录，禁止删除"
    return 0
  fi
  if is_managed_link "$link_path"; then
    add_action "REMOVE" "$link_path" "$link_target" "精确所有权证明成立"
  else
    add_action "WARN-MANUAL" "$link_path" "$link_target" "无法证明所有权，跳过删除"
  fi
}

plan_sync_links() {
  local skill_file skill_dir skill_name layer_root entry entry_name
  local -a layer_roots=("$SHARED_ROOT" "$CLAUDE_ROOT" "$CODEX_ROOT")
  declare -A expected_skills=()

  [[ -d "$SOURCE_ROOT" ]] || {
    add_action "SKIP-WARN" "$SOURCE_ROOT" "-" "仓库缺少 skills 源目录"
    return 0
  }

  while IFS= read -r -d '' skill_file; do
    skill_dir="${skill_file%/SKILL.md}"
    skill_name="${skill_dir##*/}"
    expected_skills["$skill_name"]=1
    sync_one_link "$SHARED_ROOT/$skill_name" "$skill_dir"
    sync_one_link "$CLAUDE_ROOT/$skill_name" "$SHARED_ROOT/$skill_name"
    sync_one_link "$CODEX_ROOT/$skill_name" "$SHARED_ROOT/$skill_name"
  done < <(find "$SOURCE_ROOT" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' -print0)

  declare -A orphan_names=()
  if [[ -d "$SHARED_ROOT" ]]; then
    while IFS= read -r -d '' entry; do
      entry_name="${entry##*/}"
      if is_managed_link "$entry" && [[ -z "${expected_skills[$entry_name]+present}" ]]; then
        orphan_names["$entry_name"]=1
      fi
    done < <(find "$SHARED_ROOT" -mindepth 1 -maxdepth 1 -type l -print0)
  fi

  for layer_root in "${layer_roots[@]}"; do
    [[ -d "$layer_root" ]] || continue
    while IFS= read -r -d '' entry; do
      entry_name="${entry##*/}"
      if [[ -n "${expected_skills[$entry_name]+present}" || -n "${orphan_names[$entry_name]+present}" ]]; then
        continue
      fi
      if ! is_managed_link "$entry"; then
        add_action "WARN-MANUAL" "$entry" "$(readlink -- "$entry" 2>/dev/null || true)" "无法证明所有权，跳过清理"
      fi
    done < <(find "$layer_root" -mindepth 1 -maxdepth 1 -type l -print0)
  done

  for entry_name in "${!orphan_names[@]}"; do
    plan_remove_link "$CLAUDE_ROOT/$entry_name"
    plan_remove_link "$CODEX_ROOT/$entry_name"
    plan_remove_link "$SHARED_ROOT/$entry_name"
  done
}

execute_action() {
  local action="$1" type path target reason temp_link
  IFS=$'\t' read -r type path target reason <<< "$action"
    printf 'ACTION %s path=%s target=%s reason=%s\n' "$type" "$path" "$target" "$reason"

  case "$type" in
    ENSURE-DIR)
      mkdir -p -- "$path"
      ;;
    CREATE)
      if [[ -e "$path" || -L "$path" ]]; then
        warn "计划执行时目标已改变，跳过创建：$path"
      else
        ln -s -- "$target" "$path"
        log "已创建软链：$path -> $target"
      fi
      ;;
    REPLACE)
      if ! is_managed_link "$path"; then
        warn "计划执行时所有权证明失效，跳过替换：$path；请手动检查"
      elif [[ "$(readlink -- "$path")" == "$target" ]]; then
        log "软链已正确，无需修改：$path"
      else
        temp_link="${path}.cadence-tmp.$$.$RANDOM"
        while [[ -e "$temp_link" || -L "$temp_link" ]]; do
          temp_link="${path}.cadence-tmp.$$.$RANDOM"
        done
        ln -s -- "$target" "$temp_link"
        mv -T -- "$temp_link" "$path"
        log "已原子替换受管软链：$path -> $target"
      fi
      ;;
    REMOVE)
      if is_managed_link "$path"; then
        rm -f -- "$path"
        log "已卸载受管软链：$path"
      else
        warn "计划执行时所有权证明失效，跳过删除：$path；请手动检查"
      fi
      ;;
    REMOVE-REPO)
      if is_git_repo; then
        rm -rf -- "$REPO_DIR"
        log "已按 --delete-repo 删除仓库：$REPO_DIR"
      else
        warn "计划执行时仓库不再是可识别 Git 仓库，跳过删除：$REPO_DIR"
      fi
      ;;
    SKIP-WARN|WARN-MANUAL|KEEP)
      if [[ "$type" == "WARN-MANUAL" ]]; then
        warn "$reason：$path；请人工检查"
        printf '手动清理命令：rm -i -- %q\n' "$path" >&2
      fi
      ;;
    *)
      warn "未知动作类型，跳过：$type"
      ;;
  esac
}

execute_plan() {
  local action
  for action in "${PLAN_ACTIONS[@]}"; do
    execute_action "$action"
  done
}

plan_repository() {
  local url origin_url
  if [[ -e "$REPO_DIR" || -L "$REPO_DIR" ]]; then
    if is_git_repo; then
      origin_url="$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null || true)"
      add_action "KEEP" "$REPO_DIR" "$origin_url" "仅读取仓库状态，跳过网络更新"
    else
      add_action "SKIP-WARN" "$REPO_DIR" "-" "目标不是可识别 Git 仓库，保留并人工处理；请删除 ~/.agents/Cadence-skills 后重新运行"
    fi
  else
    for url in "${MIRRORS[@]}"; do
      add_action "CLONE" "$REPO_DIR" "$url" "预览镜像尝试，不执行网络操作"
    done
  fi
}

plan_uninstall() {
  local layer_root entry
  local -a layer_roots=("$CLAUDE_ROOT" "$CODEX_ROOT" "$SHARED_ROOT")
  for layer_root in "${layer_roots[@]}"; do
    [[ -d "$layer_root" ]] || continue
    while IFS= read -r -d '' entry; do
      plan_remove_link "$entry"
    done < <(find "$layer_root" -mindepth 1 -maxdepth 1 -type l -print0)
  done

  if [[ "${1:-0}" == 1 ]]; then
    if is_git_repo; then
      add_action "REMOVE-REPO" "$REPO_DIR" "-" "显式请求删除可识别 Git 仓库"
    else
      add_action "WARN-MANUAL" "$REPO_DIR" "-" "仓库不存在或无法证明为 Git 仓库，保留"
    fi
  fi
}

print_plan() {
  local action type path target reason
  while IFS= read -r action; do
    [[ -n "$action" ]] || continue
    IFS=$'\t' read -r type path target reason <<< "$action"
    printf 'DRY-RUN %s path=%s target=%s reason=%s\n' "$type" "$path" "$target" "$reason"
  done < <(printf '%s\n' "${PLAN_ACTIONS[@]}" | sort)
}

print_visibility() {
  cat <<'MESSAGE'
安装完成。四类 agent 的 Cadence skill 消费路径与验证命令：
  Claude Code: ~/.claude/skills/       验证：ls ~/.claude/skills/
  pi:          ~/.agents/skills/        验证：ls ~/.agents/skills/
  Codex:       ~/.agents/skills/        验证：ls ~/.agents/skills/；兼容层：ls ~/.codex/skills/skills/
  Kimi Code:   ~/.agents/skills/        验证：ls ~/.agents/skills/
示例验证：test -f ~/.claude/skills/pre-check/SKILL.md && test -f ~/.agents/skills/pre-check/SKILL.md
MESSAGE
}

detect_residue() {
  local residue_dir="$HOME/.claude/plugins/marketplaces/cadence-skills-local"
  local marketplaces_file="$HOME/.claude/plugins/known_marketplaces.json"
  local found=0

  if [[ -e "$residue_dir" || -L "$residue_dir" ]]; then
    found=1
    if (( DRY_RUN )); then
      add_action "WARN-MANUAL" "$residue_dir" "-" "检测到旧 marketplace 残留目录，保留并人工处理"
    else
      warn "检测到旧 marketplace 残留目录：$residue_dir"
      printf '手动清理命令：rm -rf -- %q\n' "$residue_dir"
    fi
  fi

  if [[ -f "$marketplaces_file" ]]; then
    if command -v jq >/dev/null 2>&1; then
      if ! jq -e 'type == "object"' "$marketplaces_file" >/dev/null 2>&1; then
        if (( DRY_RUN )); then
          add_action "WARN-MANUAL" "$marketplaces_file" "-" "JSON 无法解析，保留并人工确认旧键"
        else
          warn "known_marketplaces.json 不是可解析 JSON，未自动修改；请人工确认 cadence-skills-local 键"
        fi
      elif jq -e 'has("cadence-skills-local")' "$marketplaces_file" >/dev/null 2>&1; then
        found=1
        if (( DRY_RUN )); then
          add_action "WARN-MANUAL" "$marketplaces_file" "cadence-skills-local" "检测到旧 marketplace 键，保留并人工处理"
        else
          warn "检测到 known_marketplaces.json 残留键：cadence-skills-local"
          printf '手动清理命令：使用 jq 删除键后人工复核：jq "del(.\\\"cadence-skills-local\\\")" %q > %q.tmp && mv %q.tmp %q\n' "$marketplaces_file" "$marketplaces_file" "$marketplaces_file" "$marketplaces_file"
        fi
      fi
    elif grep -Eq '"cadence-skills-local"[[:space:]]*:' "$marketplaces_file"; then
      found=1
      if (( DRY_RUN )); then
        add_action "WARN-MANUAL" "$marketplaces_file" "cadence-skills-local" "疑似检测到旧 marketplace 键，保留并人工确认"
      else
        warn "检测到 known_marketplaces.json 疑似残留键：cadence-skills-local（请用 jq 人工确认）"
        printf '手动清理命令：请使用 jq 人工删除 cadence-skills-local 键并复核\n'
      fi
    elif (( ! DRY_RUN )); then
      warn "无法结构化检查 known_marketplaces.json；请安装 jq 后手动确认 cadence-skills-local 键"
    fi
  fi

  if (( found == 0 && ! DRY_RUN )); then
    log "未检测到旧 marketplace 残留"
  fi
}

run_dry_run() {
  local uninstall_mode="$1" delete_repo="$2"
  PLAN_ACTIONS=()
  PLANNED_DIRS=()
  DRY_RUN=1
  detect_residue
  if (( uninstall_mode )); then
    plan_uninstall "$delete_repo"
  else
    plan_repository
    if is_git_repo; then
      plan_sync_links
    elif [[ -e "$REPO_DIR" || -L "$REPO_DIR" ]]; then
      :
    else
      add_action "SKIP-WARN" "$SOURCE_ROOT" "-" "仓库尚不存在，无法计算链接动作"
    fi
  fi
  print_plan
}

sync_links() {
  PLAN_ACTIONS=()
  PLANNED_DIRS=()
  plan_sync_links
  execute_plan
}

uninstall() {
  PLAN_ACTIONS=()
  PLANNED_DIRS=()
  plan_uninstall "$1"
  execute_plan
}

run_install() {
  ensure_repo
  DRY_RUN=0
  sync_links
  print_visibility
}

run_uninstall() {
  DRY_RUN=0
  detect_residue
  uninstall "$1"
}

print_help() {
  cat <<'HELP'
用法：
  ./install.sh                         从固定镜像安装或更新 Cadence skills
  ./install.sh --help                  显示本帮助
  ./install.sh --dry-run               预览安装动作，不联网、不落盘
  ./install.sh --uninstall             仅卸载受管三层软链，保留仓库
  ./install.sh --uninstall --delete-repo
                                      卸载受管软链并删除仓库
  ./install.sh --dry-run --uninstall
                                      预览卸载动作并保留仓库
  ./install.sh --dry-run --uninstall --delete-repo
                                      预览卸载动作和显式仓库删除

说明：安装只使用 ghfast.top、gh-proxy.com、mirror.ghproxy.com，
不使用 GitHub 直连，也不提供离线模式。Windows 原生环境不支持。
HELP
}

main() {
  local dry_run=0 uninstall_mode=0 delete_repo=0 arg
  if (( $# == 0 )); then
    detect_residue
    run_install
    return 0
  fi

  for arg in "$@"; do
    case "$arg" in
      --dry-run) dry_run=1 ;;
      --uninstall) uninstall_mode=1 ;;
      --delete-repo) delete_repo=1 ;;
      --help|-h)
        (( $# == 1 )) || { print_help >&2; return 2; }
        print_help
        return 0
        ;;
      *) print_help >&2; return 2 ;;
    esac
  done
  if (( delete_repo && ! uninstall_mode )); then
    print_help >&2
    return 2
  fi
  if (( dry_run )); then
    run_dry_run "$uninstall_mode" "$delete_repo"
  elif (( uninstall_mode )); then
    run_uninstall "$delete_repo"
  else
    print_help >&2
    return 2
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
