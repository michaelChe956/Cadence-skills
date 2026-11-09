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
# Codex 用户技能层：与 Codex 官方约定一致（$CODEX_HOME/skills/<skill>/SKILL.md），
# 与 Codex 自带系统技能目录 $CODEX_HOME/skills/.system/<skill> 同构；旧版嵌套布局在下方迁移。
readonly CODEX_ROOT="$HOME/.codex/skills"
readonly LEGACY_CODEX_ROOT="$HOME/.codex/skills/skills"
# 本脚本自身路径：仓库更新后脚本内容可能已变，需要用新版本重跑一次（见 run_install）
readonly INSTALLER_SELF="${BASH_SOURCE[0]}"

: "$REPOSITORY_URL"

# bash 3.2 兼容（macOS 自带）：不用 declare -A；
# 空数组展开用 ${arr[@]+"${arr[@]}"} 防 set -u 报未绑定变量
DRY_RUN=0
PLAN_ACTIONS=()
PLANNED_DIRS=()

log() { printf '[cadence] %s\n' "$*"; }
warn() { printf '[cadence][警告] %s\n' "$*" >&2; }
fail() { printf '[cadence][错误] %s\n' "$*" >&2; return 1; }

# 集合查找辅助：关联数组替代品，元素量级为几十个技能名，线性查找足够
list_has() {
  local needle="$1" item
  shift
  for item in "$@"; do
    [[ "$item" == "$needle" ]] && return 0
  done
  return 1
}

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
      # 极窄竞态下 REPO_DIR 可能被并发创建：mv 会把 repo 嵌套移入而非报错，落位后校验兜底
      mv -- "$staging_root/repo" "$REPO_DIR"
      if [[ -d "$REPO_DIR/repo" ]]; then
        fail "检测到 $REPO_DIR 被并发创建导致嵌套安装，请删除该目录后重新运行"
        return 1
      fi
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

# 下游层（Claude/Codex）条目是否为指向共享层同名词的投影链：
# - 共享层条目存在时，要求共享层条目自身通过所有权证明（指向仓库源）；
# - 共享层条目已不存在时，视为本机制遗留投影（目标必然不可达），
#   用于清理共享层先被删除后残留的下游断链。
is_projection_link() {
  local link_path="$1" link_name link_target shared_target
  [[ -L "$link_path" ]] || return 1
  link_name="$(basename -- "$link_path")"
  link_target="$(readlink -- "$link_path" 2>/dev/null)" || return 1
  [[ "$link_target" == "$SHARED_ROOT/$link_name" ]] || return 1
  if [[ -L "$SHARED_ROOT/$link_name" ]]; then
    shared_target="$(readlink -- "$SHARED_ROOT/$link_name" 2>/dev/null)" || return 1
    [[ "$shared_target" == "$REPO_DIR/cadence-init/skills/$link_name" ]]
    return
  fi
  [[ ! -e "$SHARED_ROOT/$link_name" ]]
}

is_managed_link() {
  local link_path="$1" link_dir link_name link_target expected_source
  [[ -L "$link_path" ]] || return 1
  link_dir="$(dirname -- "$link_path")"
  link_name="$(basename -- "$link_path")"
  expected_source="$REPO_DIR/cadence-init/skills/$link_name"
  link_target="$(readlink -- "$link_path" 2>/dev/null)" || return 1

  case "$link_dir" in
    "$SHARED_ROOT")
      [[ "$link_target" == "$expected_source" ]]
      ;;
    "$CLAUDE_ROOT"|"$CODEX_ROOT"|"$LEGACY_CODEX_ROOT")
      is_projection_link "$link_path"
      ;;
    *)
      return 1
      ;;
  esac
}

# 动作字段用 \x1f（单元分隔符）连接：tab 属 IFS 空白类字符，连续 tab 会塌缩，
# 空 target 字段会让 reason 错位、末变量落空（macOS bash 3.2 下触发 unbound）
ACTION_SEP=$'\x1f'
add_action() {
  PLAN_ACTIONS+=("$1${ACTION_SEP}$2${ACTION_SEP}$3${ACTION_SEP}$4")
}

plan_ensure_dir() {
  local path="$1" parent
  parent="$(dirname -- "$path")"
  if [[ ! -d "$parent" ]] && ! list_has "$parent" ${PLANNED_DIRS[@]+"${PLANNED_DIRS[@]}"}; then
    PLANNED_DIRS+=("$parent")
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

# 旧版 Codex 嵌套层（~/.codex/skills/skills）迁移到扁平 Codex 层（~/.codex/skills）。
# 只迁移本阶段托管的条目（链接目标精确等于共享层同名词）；非托管条目保留并告警。
plan_migrate_legacy_codex() {
  local -a expected=("$@")
  local entry entry_name target new_path new_target
  [[ -d "$LEGACY_CODEX_ROOT" ]] || return 0

  while IFS= read -r -d '' entry; do
    entry_name="${entry##*/}"
    if ! list_has "$entry_name" ${expected[@]+"${expected[@]}"}; then
      continue
    fi
    target="$(readlink -- "$entry" 2>/dev/null || true)"
    if [[ "$target" != "$SHARED_ROOT/$entry_name" ]]; then
      add_action "WARN-MANUAL" "$entry" "$target" "旧 Codex 嵌套层含非托管条目，保留"
      continue
    fi
    # 共享层同名条目已存在时，必须自身通过所有权证明，否则旧条目不可认领
    if [[ -e "$SHARED_ROOT/$entry_name" || -L "$SHARED_ROOT/$entry_name" ]]; then
      if ! is_managed_link "$SHARED_ROOT/$entry_name"; then
        add_action "WARN-MANUAL" "$entry" "$target" "旧 Codex 嵌套层条目的共享层目标无法证明归属，保留"
        continue
      fi
    fi
    new_path="$CODEX_ROOT/$entry_name"
    if [[ -e "$new_path" || -L "$new_path" ]]; then
      if [[ ! -L "$new_path" ]]; then
        add_action "WARN-MANUAL" "$entry" "$target" "扁平 Codex 层同名条目为普通文件或目录，保留旧条目"
        continue
      fi
      new_target="$(readlink -- "$new_path" 2>/dev/null || true)"
      if [[ "$new_target" != "$SHARED_ROOT/$entry_name" ]]; then
        add_action "WARN-MANUAL" "$entry" "$target" "扁平 Codex 层同名条目无法证明归属，保留旧条目"
        continue
      fi
    fi
    add_action "MIGRATE-CODEX" "$entry" "$new_path" "旧嵌套层条目迁移到扁平 Codex 层"
  done < <(find "$LEGACY_CODEX_ROOT" -mindepth 1 -maxdepth 1 -type l -print0)
}

# 只读扫描 Codex 技能根：报告不可读入口（含嵌套命名空间目录下的条目）。
# 仅报告非本机制托管的条目，避免与同步阶段的修复动作重复告警。
# Codex 自带的系统技能目录（.system）不在报告范围；旧嵌套层（skills）中的
# 受管条目由迁移与孤儿清理负责，其余失效入口仍需报告。
plan_scan_codex_root() {
  local entry relative base ancestor target
  [[ -d "$CODEX_ROOT" ]] || return 0

  while IFS= read -r -d '' entry; do
    relative="${entry#"$CODEX_ROOT"/}"
    case "$relative" in
      ".system"|".system/"*) continue ;;
    esac
    # 深度 2 条目若其深度 1 祖先本身是可读技能目录，则属于技能内部资源，不再单独报告
    if [[ "$relative" == */* ]]; then
      base="${relative%%/*}"
      ancestor="$CODEX_ROOT/$base"
      if [[ -d "$ancestor" && -r "$ancestor/SKILL.md" ]]; then
        continue
      fi
    fi
    if [[ -L "$entry" ]]; then
      # 指向普通文件的软链不是技能入口
      if [[ -e "$entry" && ! -d "$entry" ]]; then
        continue
      fi
      if [[ -r "$entry/SKILL.md" ]]; then
        continue
      fi
    elif [[ -d "$entry" ]]; then
      # 普通目录：清单不存在（非技能入口）或清单不可读（失效入口）才处理
      if [[ ! -e "$entry/SKILL.md" && ! -L "$entry/SKILL.md" ]]; then
        continue
      fi
      if [[ -r "$entry/SKILL.md" ]]; then
        continue
      fi
    else
      continue
    fi
    target="$(readlink -- "$entry" 2>/dev/null || true)"
    if is_managed_link "$entry"; then
      continue
    fi
    add_action "WARN-MANUAL" "$entry" "$target" "Codex 技能根条目不可读，需人工确认后清理"
  done < <(find "$CODEX_ROOT" -mindepth 1 -maxdepth 2 -print0)
}

plan_sync_links() {
  local skill_file skill_dir skill_name layer_root entry entry_name
  local -a layer_roots=("$SHARED_ROOT" "$CLAUDE_ROOT" "$CODEX_ROOT" "$LEGACY_CODEX_ROOT")
  local -a expected_skills=()

  [[ -d "$SOURCE_ROOT" ]] || {
    add_action "SKIP-WARN" "$SOURCE_ROOT" "-" "仓库缺少 skills 源目录"
    return 0
  }

  while IFS= read -r -d '' skill_file; do
    skill_dir="${skill_file%/SKILL.md}"
    skill_name="${skill_dir##*/}"
    expected_skills+=("$skill_name")
    if [[ ! -r "$skill_file" ]]; then
      add_action "WARN-UNREADABLE" "$skill_file" "-" "技能源 SKILL.md 不可读，投影后入口将不可用"
    fi
    sync_one_link "$SHARED_ROOT/$skill_name" "$skill_dir"
    sync_one_link "$CLAUDE_ROOT/$skill_name" "$SHARED_ROOT/$skill_name"
    sync_one_link "$CODEX_ROOT/$skill_name" "$SHARED_ROOT/$skill_name"
  done < <(find "$SOURCE_ROOT" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' -print0)

  plan_migrate_legacy_codex ${expected_skills[@]+"${expected_skills[@]}"}

  local -a orphan_names=()
  if [[ -d "$SHARED_ROOT" ]]; then
    while IFS= read -r -d '' entry; do
      entry_name="${entry##*/}"
      if is_managed_link "$entry" && ! list_has "$entry_name" ${expected_skills[@]+"${expected_skills[@]}"}; then
        orphan_names+=("$entry_name")
      fi
    done < <(find "$SHARED_ROOT" -mindepth 1 -maxdepth 1 -type l -print0)
  fi

  # 下游层遗留投影：共享层已无该条目，但本层仍指向共享层同名词（必然不可达）
  for layer_root in "$CLAUDE_ROOT" "$CODEX_ROOT" "$LEGACY_CODEX_ROOT"; do
    [[ -d "$layer_root" ]] || continue
    while IFS= read -r -d '' entry; do
      entry_name="${entry##*/}"
      if list_has "$entry_name" ${expected_skills[@]+"${expected_skills[@]}"}; then
        continue
      fi
      if list_has "$entry_name" ${orphan_names[@]+"${orphan_names[@]}"}; then
        continue
      fi
      if [[ -e "$SHARED_ROOT/$entry_name" || -L "$SHARED_ROOT/$entry_name" ]]; then
        continue
      fi
      if is_projection_link "$entry"; then
        orphan_names+=("$entry_name")
      fi
    done < <(find "$layer_root" -mindepth 1 -maxdepth 1 -type l -print0)
  done

  for layer_root in "${layer_roots[@]}"; do
    [[ -d "$layer_root" ]] || continue
    while IFS= read -r -d '' entry; do
      entry_name="${entry##*/}"
      if list_has "$entry_name" ${expected_skills[@]+"${expected_skills[@]}"} ||
         list_has "$entry_name" ${orphan_names[@]+"${orphan_names[@]}"}; then
        continue
      fi
      if ! is_managed_link "$entry"; then
        add_action "WARN-MANUAL" "$entry" "$(readlink -- "$entry" 2>/dev/null || true)" "无法证明所有权，跳过清理"
      fi
    done < <(find "$layer_root" -mindepth 1 -maxdepth 1 -type l -print0)
  done

  for entry_name in ${orphan_names[@]+"${orphan_names[@]}"}; do
    plan_remove_link "$CLAUDE_ROOT/$entry_name"
    plan_remove_link "$CODEX_ROOT/$entry_name"
    plan_remove_link "$LEGACY_CODEX_ROOT/$entry_name"
    plan_remove_link "$SHARED_ROOT/$entry_name"
  done

  # 旧 Codex 嵌套层的清理安排在迁移与孤儿删除之后，确保迁空后目录可被删除
  if [[ -d "$LEGACY_CODEX_ROOT" ]]; then
    add_action "RMDIR-EMPTY" "$LEGACY_CODEX_ROOT" "-" "旧 Codex 嵌套层迁空后删除目录"
  fi

  plan_scan_codex_root
}

execute_action() {
  local action="$1" type path target reason temp_link replaced_atomically _mig_name
  type='' path='' target='' reason=''
  IFS="$ACTION_SEP" read -r type path target reason <<< "$action" || true
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
        # 优先 mv -T 原子替换（GNU）；BSD mv 无 -T、部分实现拒绝软链到目录目标，
        # 失败时清理临时链接并用 ln -sfn 落地（unlink+建链，窗口极短）
        replaced_atomically=0
        if mv -T -- "$temp_link" "$path" 2>/dev/null; then
          replaced_atomically=1
        else
          rm -f -- "$temp_link"
          ln -sfn -- "$target" "$path"
        fi
        if (( replaced_atomically )); then
          log "已原子替换受管软链：$path -> $target"
        else
          log "已替换受管软链（非原子回退）：$path -> $target"
        fi
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
    MIGRATE-CODEX)
      # path = 旧嵌套层条目；target = 扁平层新条目。
      # 删除前复核：旧条目仍是软链且目标未变、新条目已建立且清单可读。
      _mig_name="${path##*/}"
      if [[ ! -L "$path" ]]; then
        warn "旧 Codex 嵌套层条目已不是软链，跳过移除：$path"
      elif [[ "$(readlink -- "$path" 2>/dev/null || true)" != "$SHARED_ROOT/$_mig_name" ]]; then
        warn "旧 Codex 嵌套层条目目标已变化，跳过移除：$path"
      elif [[ ! -L "$target" ]] ||
        [[ "$(readlink -- "$target" 2>/dev/null || true)" != "$SHARED_ROOT/$_mig_name" ]]; then
        warn "扁平 Codex 层条目未建立成功，保留旧条目：$path"
      elif [[ ! -r "$target/SKILL.md" ]]; then
        warn "扁平 Codex 层条目不可读，保留旧条目：$path"
      else
        rm -f -- "$path"
        log "已移除旧 Codex 嵌套层条目：$path"
      fi
      ;;
    RMDIR-EMPTY)
      if [[ -d "$path" ]]; then
        if rmdir -- "$path" 2>/dev/null; then
          log "已删除空的旧 Codex 嵌套层目录：$path"
        else
          warn "旧 Codex 嵌套层目录仍含条目，保留：$path"
        fi
      fi
      ;;
    SKIP-WARN|WARN-MANUAL|KEEP)
      if [[ "$type" == "WARN-MANUAL" ]]; then
        warn "$reason：$path；请人工检查"
        printf '手动清理命令：rm -i -- %q\n' "$path" >&2
      fi
      ;;
    WARN-UNREADABLE)
      warn "$reason：$path；请修复该文件的读权限后重新运行安装"
      ;;
    *)
      warn "未知动作类型，跳过：$type"
      ;;
  esac
}

execute_plan() {
  local action
  for action in ${PLAN_ACTIONS[@]+"${PLAN_ACTIONS[@]}"}; do
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
  local -a layer_roots=("$CLAUDE_ROOT" "$CODEX_ROOT" "$LEGACY_CODEX_ROOT" "$SHARED_ROOT")
  for layer_root in "${layer_roots[@]}"; do
    [[ -d "$layer_root" ]] || continue
    while IFS= read -r -d '' entry; do
      plan_remove_link "$entry"
    done < <(find "$layer_root" -mindepth 1 -maxdepth 1 -type l -print0)
  done

  if [[ -d "$LEGACY_CODEX_ROOT" ]]; then
    add_action "RMDIR-EMPTY" "$LEGACY_CODEX_ROOT" "-" "卸载后清理空的旧 Codex 嵌套层目录"
  fi

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
    type='' path='' target='' reason=''
    IFS="$ACTION_SEP" read -r type path target reason <<< "$action" || true
    printf 'DRY-RUN %s path=%s target=%s reason=%s\n' "$type" "$path" "$target" "$reason"
  done < <(printf '%s\n' ${PLAN_ACTIONS[@]+"${PLAN_ACTIONS[@]}"} | sort)
}

print_visibility() {
  cat <<'MESSAGE'
安装完成。四类 agent 的 Cadence skill 消费路径与验证命令：
  Claude Code: ~/.claude/skills/       验证：ls ~/.claude/skills/
  pi:          ~/.agents/skills/        验证：ls ~/.agents/skills/
  Codex:       ~/.agents/skills/        验证：ls ~/.agents/skills/；用户层：ls ~/.codex/skills/
  Kimi Code:   ~/.agents/skills/        验证：ls ~/.agents/skills/
Codex 用户层为扁平目录 ~/.codex/skills/<skill>/SKILL.md（与 Codex 自带系统技能目录
~/.codex/skills/.system/ 并列，互不覆盖）；旧版嵌套层 ~/.codex/skills/skills/ 已在本次安装中迁移。
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

# 同步完成后复核各层投影入口的可读性：
# 清单里的每个入口都必须能读到 SKILL.md，避免注入不可解析的技能路径。
verify_projected_entries() {
  local skill_file skill_dir skill_name layer_root entry unreadable=0
  [[ -d "$SOURCE_ROOT" ]] || return 0

  while IFS= read -r -d '' skill_file; do
    skill_dir="${skill_file%/SKILL.md}"
    skill_name="${skill_dir##*/}"
    for layer_root in "$SHARED_ROOT" "$CLAUDE_ROOT" "$CODEX_ROOT"; do
      entry="$layer_root/$skill_name"
      if [[ ! -r "$entry/SKILL.md" ]]; then
        warn "投影入口不可读：$entry/SKILL.md"
        unreadable=$((unreadable + 1))
      fi
    done
  done < <(find "$SOURCE_ROOT" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' -print0)

  if (( unreadable > 0 )); then
    log "投影入口可读性校验：$unreadable 个入口不可读（详见上方告警）"
  else
    log "投影入口可读性校验：全部入口可读"
  fi
}

sync_links() {
  PLAN_ACTIONS=()
  PLANNED_DIRS=()
  plan_sync_links
  execute_plan
  verify_projected_entries
}

uninstall() {
  PLAN_ACTIONS=()
  PLANNED_DIRS=()
  plan_uninstall "$1"
  execute_plan
}

# 脚本自身指纹（cksum 为 POSIX 工具，macOS 自带）：用于判断仓库更新是否改写了本脚本
installer_fingerprint() {
  cksum "$INSTALLER_SELF" 2>/dev/null || true
}

run_install() {
  local fingerprint_before fingerprint_after
  fingerprint_before="$(installer_fingerprint)"
  ensure_repo
  fingerprint_after="$(installer_fingerprint)"
  # 仓库更新可能带来新版本安装脚本：旧脚本在内存中继续执行会漏掉新逻辑
  # （如 Codex 层扁平化迁移），此处用新版本重跑一次，保证一次调用即完成更新与迁移
  if [[ -n "$fingerprint_before" && "$fingerprint_before" != "$fingerprint_after" &&
        "${CADENCE_INSTALLER_REEXEC:-0}" != "1" ]]; then
    log "安装脚本已更新为新版本，改用新版本重新执行"
    export CADENCE_INSTALLER_REEXEC=1
    exec bash "$INSTALLER_SELF" "$@"
  fi
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
    run_install "$@"
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
