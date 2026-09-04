#!/usr/bin/env bash
# Cadence pre-check 主脚本：基础工具探测/安装/复验与 OpenSpec 四端投影补齐。
# 职责边界：处理 npx/uvx/ast-grep/codegraph/openspec/pi-mcp-adapter，以及 OpenSpec 客户端投影。
# 不处理 Superpowers 软链、Superpowers Git、Playwright、API Key（由后续 phase/SKILL.md 处理）。
# 用法:
#   pre-check.sh run   [--mirror <name>] [--no-interrupt] [--upgrade]
#   pre-check.sh check [--mirror <name>] [--no-interrupt]
# 输出: stdout = 单份 JSON 报告；stderr = 彩色人类摘要。
# 兼容: mac bash 3.2 + BSD 工具 / Linux GNU 工具（POSIX 子集，无关联数组）。

set -u
# 不用 set -e：需逐项捕获失败并汇总进 JSON，而非中途退出。

# 脚本所在目录（用于定位 mirrors/）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIRRORS_DIR="$SCRIPT_DIR/mirrors"

# 默认值
MODE=""
MIRROR="default"
NO_INTERRUPT=0
UPGRADE=0

# 颜色（stderr 摘要）
if [ -t 2 ]; then
  C_RED='\033[0;31m'; C_GRN='\033[0;32m'; C_YEL='\033[1;33m'; C_BLU='\033[0;34m'; C_NC='\033[0m'
else
  C_RED=''; C_GRN=''; C_YEL=''; C_BLU=''; C_NC=''
fi

log()  { printf '%b\n' "$*" >&2; }
err()  { printf '%b\n' "${C_RED}$*${C_NC}" >&2; }

usage() {
  cat >&2 <<'USAGE'
用法:
  pre-check.sh run   [--mirror <name>] [--no-interrupt] [--upgrade]
  pre-check.sh check [--mirror <name>] [--no-interrupt]
  pre-check.sh --help
说明:
  run            探测并对缺失工具执行安装与复验
  check          仅探测就绪状态，不安装
  --mirror name  加载 scripts/mirrors/<name>.sh（默认 default）
  --no-interrupt 任一基础工具失败即非零退出（失败关闭）
  --upgrade      查询当前源 latest 并升级落后工具（npm 系 + uv 本体）
USAGE
}

# 加载镜像配置；未知 mirror 报错并非零退出
load_mirror() {
  _name="$1"
  # 安全：仅允许安全字符集（小写字母/数字/连字符/下划线），拒绝路径分隔符与 ../ 逃逸
  case "$_name" in
    *[!a-z0-9_-]*|"")
      err "❌ 非法 mirror 名称: ${_name}（仅允许 a-z、0-9、-、_）"
      exit 2 ;;
  esac
  _file="$MIRRORS_DIR/$_name.sh"
  if [ ! -f "$_file" ]; then
    err "❌ 未知 mirror: ${_name}（未找到 ${_file}）"
    exit 2
  fi
  # 目录边界校验：解析后的真实路径必须仍在 MIRRORS_DIR 内
  _resolved="$(cd "$(dirname "$_file")" 2>/dev/null && pwd -P)/$(basename "$_file")"
  _mirrors_resolved="$(cd "$MIRRORS_DIR" 2>/dev/null && pwd -P)"
  case "$_resolved" in
    "$_mirrors_resolved"/*) : ;;
    *)
      err "❌ mirror 路径越界: ${_resolved}（不在 $MIRRORS_DIR 内）"
      exit 2 ;;
  esac
  # shellcheck disable=SC1090
  . "$_file"
  : "${CADENCE_NPM_REGISTRY:?mirror 缺少 CADENCE_NPM_REGISTRY}"
  : "${CADENCE_PY_INDEX:?mirror 缺少 CADENCE_PY_INDEX}"
  : "${CADENCE_SUPERPOWERS_GIT:?mirror 缺少 CADENCE_SUPERPOWERS_GIT}"
}

# 命令级源注入助手
npm_registry_args() { printf '%s' "--registry=$CADENCE_NPM_REGISTRY"; }
# 同时输出 pip 与 uv 均识别的索引变量：脚本实际用 pip 装/查/升级 uv，pip 只认
# PIP_INDEX_URL；保留 UV_INDEX_URL 以备 uv/uvx 命令直接使用（如 uv pip / uvx 临时包）。
# 调用方形如 env $(uv_index_env) pip ...（刻意不加引号），依赖单词拆分拆成两个 KEY=VAL。
uv_index_env()      { printf '%s' "PIP_INDEX_URL=$CADENCE_PY_INDEX UV_INDEX_URL=$CADENCE_PY_INDEX"; }

# 解析参数
while [ $# -gt 0 ]; do
  case "$1" in
    run|check)
      if [ -n "$MODE" ]; then err "❌ 子命令重复：$1"; usage; exit 2; fi
      MODE="$1"; shift ;;
    --mirror)
      [ $# -ge 2 ] || { err "❌ --mirror 缺少参数"; exit 2; }
      MIRROR="$2"; shift 2 ;;
    --mirror=*)
      MIRROR="${1#--mirror=}"; shift ;;
    --no-interrupt)
      NO_INTERRUPT=1; shift ;;
    --upgrade)
      UPGRADE=1; shift ;;
    --help|-h)
      usage; exit 0 ;;
    *)
      err "❌ 未知参数: $1"; usage; exit 2 ;;
  esac
done

if [ -z "$MODE" ]; then
  err "❌ 缺少子命令 run 或 check"
  usage
  exit 2
fi

# check 模式不支持 --upgrade（无安装动作，升级无意义）
if [ "$MODE" = "check" ] && [ "$UPGRADE" = "1" ]; then
  err "❌ check 模式不支持 --upgrade"
  exit 2
fi

# 读取镜像配置后，阶段与既有工具均消费同一组源设置。
load_mirror "$MIRROR"

# JSON 步骤累积（每项一行紧凑 JSON，由报告汇总）。
STEPS_JSON=""

# 项目根固定为调用 cwd 的物理路径；所有阶段动作消费此根目录。
PROJECT_ROOT="$(pwd -P)"

# 五阶段报告累积（使用字符串，不使用 Bash 4 关联数组）。
PHASES_JSON=""
PHASE_CURRENT_STARTED_S=0
PHASE_CURRENT_CREATED=0
PHASE_CURRENT_UPDATED=0
PHASE_CURRENT_SKIPPED=0
PHASE_CURRENT_CONFLICTS=0
PHASE_CURRENT_RESULT=""
PHASE_CURRENT_ERROR=""
PHASE_CURRENT_SOURCE_ENTRIES=0
PHASE_CURRENT_LAYERS_JSON=""

# 当前阶段开始计时（Bash 3.2/macOS 以秒为粒度，统一序列化为毫秒整数）。
now_s() { date +%s; }

phase_begin() {
  PHASE_CURRENT_STARTED_S="$(now_s)"
  PHASE_CURRENT_CREATED=0
  PHASE_CURRENT_UPDATED=0
  PHASE_CURRENT_SKIPPED=0
  PHASE_CURRENT_CONFLICTS=0
  PHASE_CURRENT_RESULT=""
  PHASE_CURRENT_ERROR=""
  PHASE_CURRENT_SOURCE_ENTRIES=0
  PHASE_CURRENT_LAYERS_JSON=""
}

phase_finish() {
  _error_value="${9:-}"
  if [ -n "$_error_value" ]; then
    _error="\"$(json_escape "$_error_value")\""
  else
    _error=null
  fi
  _item="{\"phase\":\"$(json_escape "$1")\",\"result\":\"$(json_escape "$2")\",\"action\":\"$(json_escape "$3")\",\"duration_ms\":$4,\"created\":$5,\"updated\":$6,\"skipped\":$7,\"conflicts\":$8,\"error\":$_error"
  # Git phase 额外报告来源、分支和 revision；软链 phase 报告动态源条目及逐层状态。
  if [ "$1" = "superpowers-git" ]; then
    _item="${_item},\"origin\":\"$(json_escape "${GIT_ORIGIN:-}")\",\"branch\":\"$(json_escape "${GIT_BRANCH:-}")\",\"before_revision\":\"$(json_escape "${GIT_BEFORE_REVISION:-}")\",\"after_revision\":\"$(json_escape "${GIT_AFTER_REVISION:-}")\""
  elif [ "$1" = "superpowers-links" ]; then
    _item="${_item},\"source_entries\":${PHASE_CURRENT_SOURCE_ENTRIES:-0},\"layers\":[${PHASE_CURRENT_LAYERS_JSON:-}]"
  fi
  _item="${_item}}"
  if [ -z "$PHASES_JSON" ]; then
    PHASES_JSON="$_item"
  else
    PHASES_JSON="$PHASES_JSON,$_item"
  fi
}

run_phase() {
  _phase="$1"
  _function="$2"
  phase_begin
  _failed_before="$FAILED_COUNT"
  "$_function"
  _rc=$?
  _elapsed=$(((($(now_s) - PHASE_CURRENT_STARTED_S)) * 1000))
  if [ "$PHASE_CURRENT_CREATED" -eq 0 ] && [ "$PHASE_CURRENT_UPDATED" -eq 0 ] && [ "$PHASE_CURRENT_CONFLICTS" -eq 0 ]; then
    _default_result=skipped
  else
    _default_result=success
  fi
  if [ "$_rc" -eq 0 ]; then
    _result="${PHASE_CURRENT_RESULT:-$_default_result}"
  elif [ "$NO_INTERRUPT" = "1" ]; then
    _result=failed
  else
    # 普通模式允许阶段汇总后继续；非零代表该阶段部分完成。
    _result=partial
  fi
  # 阶段失败必须进入 overall 汇总；基础工具内部已逐项计数时避免重复累加。
  if [ "$_rc" -ne 0 ] && [ "$FAILED_COUNT" -eq "$_failed_before" ]; then
    FAILED_COUNT=$((FAILED_COUNT + 1))
  fi
  phase_finish "$_phase" "$_result" "${PHASE_CURRENT_ACTION:-$_function}" "$_elapsed" "$PHASE_CURRENT_CREATED" "$PHASE_CURRENT_UPDATED" "$PHASE_CURRENT_SKIPPED" "$PHASE_CURRENT_CONFLICTS" "${PHASE_CURRENT_ERROR:-}"
  return "$_rc"
}

# Task 1 将六个既有工具调用封装为基础工具 phase；返回值聚合但不短路。
do_base_tools() {
  _rc=0
  do_npx || _rc=1
  do_uvx || _rc=1
  do_ast_grep || _rc=1
  do_codegraph || _rc=1
  do_openspec || _rc=1
  do_pi_mcp_adapter || _rc=1
  return "$_rc"
}

# Task 2：OpenSpec 四端投影检测、增量初始化与数量复核。
count_dirs_named() {
  _base="$1"; _prefix="$2"; _count=0
  if [ -d "$_base" ]; then
    for _entry in "$_base/${_prefix}"*; do
      [ -d "$_entry" ] || continue
      _count=$((_count + 1))
    done
  fi
  printf '%s' "$_count"
}

count_files_named() {
  _base="$1"; _prefix="$2"; _suffix="$3"; _count=0
  if [ -d "$_base" ]; then
    for _entry in "$_base/${_prefix}"*"${_suffix}"; do
      [ -f "$_entry" ] || continue
      _count=$((_count + 1))
    done
  fi
  printf '%s' "$_count"
}

client_openspec_ready() {
  case "$1" in
    claude)
      [ -d "$PROJECT_ROOT/.claude/commands/opsx" ] || [ "$(count_dirs_named "$PROJECT_ROOT/.claude/skills" openspec-)" -gt 0 ] ;;
    codex)
      [ "$(count_dirs_named "$PROJECT_ROOT/.agents/skills" openspec-)" -gt 0 ] ;;
    pi)
      [ "$(count_dirs_named "$PROJECT_ROOT/.pi/skills" openspec-)" -eq 5 ] && [ "$(count_files_named "$PROJECT_ROOT/.pi/prompts" opsx- .md)" -eq 5 ] ;;
    kimi)
      [ "$(count_dirs_named "$PROJECT_ROOT/.kimi-code/skills" openspec-)" -eq 5 ] ;;
    *)
      return 2 ;;
  esac
}

detect_openspec_clients() {
  OPENSPEC_MISSING=""
  OPENSPEC_SKIPPED=0
  for _client in claude codex pi kimi; do
    if client_openspec_ready "$_client"; then
      OPENSPEC_SKIPPED=$((OPENSPEC_SKIPPED + 1))
    elif [ -z "$OPENSPEC_MISSING" ]; then
      OPENSPEC_MISSING="$_client"
    else
      OPENSPEC_MISSING="$OPENSPEC_MISSING,$_client"
    fi
  done
}

verify_openspec_clients() {
  client_openspec_ready claude && client_openspec_ready codex && client_openspec_ready pi && client_openspec_ready kimi
}

do_openspec_phase() {
  detect_openspec_clients
  if [ -n "$OPENSPEC_MISSING" ]; then
    if [ "$MODE" != "run" ]; then
      PHASE_CURRENT_SKIPPED=$((PHASE_CURRENT_SKIPPED + 1))
      return 1
    fi
    PHASE_CURRENT_ACTION="init-update-verify"
    _init_missing="$OPENSPEC_MISSING"
    PHASE_CURRENT_SKIPPED="$OPENSPEC_SKIPPED"
    log "${C_BLU}🧩 OpenSpec 补齐缺失客户端：$OPENSPEC_MISSING${C_NC}"
    openspec init --tools "$OPENSPEC_MISSING" >/dev/null 2>&1 || {
      PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + 1))
      PHASE_CURRENT_ERROR="openspec init 失败（tools=$OPENSPEC_MISSING）"
      return 1
    }
    # 只有 init 补齐了投影才允许一次 update；不可在齐全分支更新。
    detect_openspec_clients
    _init_ready=0
    for _client in claude codex pi kimi; do
      case ",${_init_missing}," in
        *,${_client},*) client_openspec_ready "$_client" && _init_ready=1 ;;
      esac
    done
    if [ "$_init_ready" -eq 1 ]; then
      openspec update >/dev/null 2>&1 || {
        PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + 1))
        PHASE_CURRENT_ERROR="openspec update 失败"
        return 1
      }
      PHASE_CURRENT_CREATED=$((PHASE_CURRENT_CREATED + 1))
    fi
  else
    PHASE_CURRENT_ACTION="verify-ready"
    PHASE_CURRENT_SKIPPED=$((PHASE_CURRENT_SKIPPED + 4))
    PHASE_CURRENT_RESULT="skipped"
  fi
  verify_openspec_clients || {
    PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + 1))
    PHASE_CURRENT_ERROR="OpenSpec 客户端投影数量或路径复核失败"
    return 1
  }
  return 0
}
# Superpowers Git 阶段字段（保持 Bash 3.2：不用关联数组）。
MAX_GIT_CANDIDATES=3
GIT_CANDIDATES_COUNT=0
GIT_CANDIDATE_0=""; GIT_CANDIDATE_1=""; GIT_CANDIDATE_2=""
GIT_ERROR=""
GIT_ACTION=""
GIT_ORIGIN=""
GIT_BRANCH=""
GIT_BEFORE_REVISION=""
GIT_AFTER_REVISION=""

parse_git_candidates() {
  # 镜像配置是空格分隔字符串；在脚本内部逐项解析，避免 zsh 外层先拼接/分词。
  GIT_CANDIDATES_COUNT=0
  GIT_CANDIDATE_0=""; GIT_CANDIDATE_1=""; GIT_CANDIDATE_2=""
  _raw="${CADENCE_SUPERPOWERS_GIT:-}"
  if [ -n "${CADENCE_TEST_GIT_CANDIDATES:-}" ]; then
    _raw="$CADENCE_TEST_GIT_CANDIDATES"
  fi
  while [ -n "$_raw" ]; do
    case "$_raw" in
      *' '*) _candidate="${_raw%% *}"; _raw="${_raw#* }" ;;
      *) _candidate="$_raw"; _raw="" ;;
    esac
    [ -n "$_candidate" ] || continue
    if [ "$GIT_CANDIDATES_COUNT" -ge "$MAX_GIT_CANDIDATES" ]; then
      GIT_ERROR="too-many-candidates:$MAX_GIT_CANDIDATES"
      return 1
    fi
    case "$GIT_CANDIDATES_COUNT" in
      0) GIT_CANDIDATE_0="$_candidate" ;;
      1) GIT_CANDIDATE_1="$_candidate" ;;
      2) GIT_CANDIDATE_2="$_candidate" ;;
    esac
    GIT_CANDIDATES_COUNT=$((GIT_CANDIDATES_COUNT + 1))
  done
  if [ "$GIT_CANDIDATES_COUNT" -eq 0 ]; then
    GIT_ERROR="missing-candidate"
    return 1
  fi
  return 0
}

git_candidate_at() {
  case "$1" in
    0) printf '%s' "$GIT_CANDIDATE_0" ;;
    1) printf '%s' "$GIT_CANDIDATE_1" ;;
    2) printf '%s' "$GIT_CANDIDATE_2" ;;
    *) return 1 ;;
  esac
}

validate_superpowers_repo() {
  [ -d "$SUPERPOWERS_DIR" ] || return 1
  [ "$(git -C "$SUPERPOWERS_DIR" rev-parse --is-inside-work-tree 2>/dev/null)" = "true" ]
}

# 运行带超时的命令。macOS 默认没有 timeout，因此提供 Bash PID watchdog 回退。
run_with_timeout() {
  _limit="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$_limit" "$@"
    return $?
  fi
  "$@" &
  _pid=$!
  _elapsed=0
  while kill -0 "$_pid" 2>/dev/null; do
    if [ "$_elapsed" -ge "$_limit" ]; then
      kill "$_pid" 2>/dev/null
      wait "$_pid" 2>/dev/null
      return 124
    fi
    sleep 1
    _elapsed=$((_elapsed + 1))
  done
  wait "$_pid"
}

phase_remaining_s() {
  _now="$(now_s)"
  _used=$((_now - PHASE_CURRENT_STARTED_S))
  _remaining=$((180 - _used))
  if [ -n "${CADENCE_TEST_GIT_PHASE_BUDGET_S:-}" ]; then
    _remaining=$((CADENCE_TEST_GIT_PHASE_BUDGET_S - _used))
  fi
  [ "$_remaining" -gt 0 ] && printf '%s' "$_remaining" || printf '0'
}

git_timeout_for() {
  _single="$1"
  _remaining="$(phase_remaining_s)"
  if [ "$_remaining" -lt "$_single" ]; then
    printf '%s' "$_remaining"
  else
    printf '%s' "$_single"
  fi
}

# 统一格式化 Git 子命令错误，确保 phase.error 始终是字符串。
git_error_with_output() {
  _label="$1"; _rc="$2"; _file="$3"
  _detail="$(cat "$_file" 2>/dev/null | tr '\n' ' ')"
  [ -n "$_detail" ] || _detail="无输出"
  printf '%s: %s (exit=%s)' "$_label" "$_detail" "$_rc"
}

clone_superpowers() {
  _tmp="$(mktemp -d "${TMPDIR:-/tmp}/cadence-superpowers.XXXXXX")" || {
    GIT_ERROR="clone-tempdir-failed"
    return 1
  }
  _selected=""
  _errors=""
  _index=0
  while [ "$_index" -lt "$GIT_CANDIDATES_COUNT" ]; do
    _candidate="$(git_candidate_at "$_index")"
    rm -rf "$_tmp/repo"
    : > "$_tmp/error"
    _timeout="$(git_timeout_for 60)"
    if [ "$_timeout" -le 0 ]; then
      _errors="${_errors}phase-timeout: no budget remaining"
      break
    fi
    run_with_timeout "$_timeout" git clone --depth 1 "$_candidate" "$_tmp/repo" >"$_tmp/error" 2>&1
    _rc=$?
    if [ "$_rc" -eq 0 ]; then
      _selected="$_candidate"
      break
    fi
    _entry_error="$(git_error_with_output "$_candidate" "$_rc" "$_tmp/error")"
    if [ -n "$_errors" ]; then _errors="${_errors}; ${_entry_error}"; else _errors="$_entry_error"; fi
    if [ "$(phase_remaining_s)" -le 0 ]; then
      _errors="${_errors}; phase-timeout: clone budget exhausted"
      break
    fi
    _index=$((_index + 1))
  done
  if [ -z "$_selected" ]; then
    rm -rf "$_tmp"
    GIT_ERROR="clone-failed: $_errors"
    return 1
  fi
  if ! mv "$_tmp/repo" "$SUPERPOWERS_DIR" 2>"$_tmp/mv-error"; then
    _mv_error="$(git_error_with_output move 1 "$_tmp/mv-error")"
    rm -rf "$_tmp"
    GIT_ERROR="clone-install-failed: $_mv_error"
    return 1
  fi
  rm -rf "$_tmp"
  GIT_ACTION="clone"
  GIT_ORIGIN="$_selected"
  GIT_BRANCH="$(git -C "$SUPERPOWERS_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)"
  GIT_BEFORE_REVISION=""
  GIT_AFTER_REVISION="$(git -C "$SUPERPOWERS_DIR" rev-parse HEAD 2>/dev/null)"
  PHASE_CURRENT_CREATED=$((PHASE_CURRENT_CREATED + 1))
  return 0
}

update_superpowers() {
  validate_superpowers_repo || { GIT_ERROR="not-git"; return 1; }
  GIT_BEFORE_REVISION="$(git -C "$SUPERPOWERS_DIR" rev-parse HEAD 2>/dev/null)"
  GIT_BRANCH="$(git -C "$SUPERPOWERS_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)"
  GIT_ORIGIN="$(git -C "$SUPERPOWERS_DIR" remote get-url origin 2>/dev/null)"
  [ -n "$GIT_BEFORE_REVISION" ] && [ -n "$GIT_BRANCH" ] || {
    GIT_ERROR="git-metadata-failed"
    return 1
  }

  _selected=""
  _errors=""
  _remote_changed=0
  _origin_matched=0
  _index=0
  # matched-first：当前 origin 命中任一候选时，优先只 fetch origin，不改写用户配置。
  while [ "$_index" -lt "$GIT_CANDIDATES_COUNT" ]; do
    _candidate="$(git_candidate_at "$_index")"
    if [ "$_candidate" = "$GIT_ORIGIN" ]; then
      _origin_matched=1
      break
    fi
    _index=$((_index + 1))
  done
  if [ "$_origin_matched" -eq 1 ]; then
    _timeout="$(git_timeout_for 180)"
    if [ "$_timeout" -gt 0 ]; then
      _fetch_file="${TMPDIR:-/tmp}/cadence-superpowers-fetch.$$"
      run_with_timeout "$_timeout" git -C "$SUPERPOWERS_DIR" fetch origin >"$_fetch_file" 2>&1
      _rc=$?
      if [ "$_rc" -eq 0 ]; then
        _selected="$GIT_ORIGIN"
      else
        _entry_error="$(git_error_with_output "$GIT_ORIGIN" "$_rc" "$_fetch_file")"
        _errors="$_entry_error"
      fi
      rm -f "$_fetch_file"
    else
      _errors="phase-timeout: no budget remaining"
    fi
  fi
  # origin 未命中，或命中 origin 的 fetch 失败时，才按候选顺序逐一尝试并必要时修复 origin。
  if [ -z "$_selected" ]; then
    _index=0
    while [ "$_index" -lt "$GIT_CANDIDATES_COUNT" ]; do
      _candidate="$(git_candidate_at "$_index")"
      _timeout="$(git_timeout_for 180)"
      if [ "$_timeout" -le 0 ]; then
        if [ -n "$_errors" ]; then _errors="${_errors}; phase-timeout: no budget remaining"; else _errors="phase-timeout: no budget remaining"; fi
        break
      fi
      _fetch_file="${TMPDIR:-/tmp}/cadence-superpowers-fetch.$$"
      if [ "$_candidate" = "$GIT_ORIGIN" ]; then
        run_with_timeout "$_timeout" git -C "$SUPERPOWERS_DIR" fetch origin >"$_fetch_file" 2>&1
      else
        # 候选 URL 作为独立 argv 传给 git fetch，不拼接命令字符串。
        run_with_timeout "$_timeout" git -C "$SUPERPOWERS_DIR" fetch "$_candidate" >"$_fetch_file" 2>&1
      fi
      _rc=$?
      if [ "$_rc" -eq 0 ]; then
        if [ "$_candidate" != "$GIT_ORIGIN" ]; then
          _timeout="$(git_timeout_for 180)"
          if [ "$_timeout" -le 0 ]; then
            rm -f "$_fetch_file"
            if [ -n "$_errors" ]; then _errors="${_errors}; phase-timeout: no budget remaining"; else _errors="phase-timeout: no budget remaining"; fi
            break
          fi
          run_with_timeout "$_timeout" git -C "$SUPERPOWERS_DIR" remote set-url origin "$_candidate" >"$_fetch_file" 2>&1
          _set_rc=$?
          if [ "$_set_rc" -ne 0 ]; then
            _entry_error="$(git_error_with_output "$_candidate" "$_set_rc" "$_fetch_file")"
            rm -f "$_fetch_file"
            if [ -n "$_errors" ]; then _errors="${_errors}; ${_entry_error}"; else _errors="$_entry_error"; fi
            _index=$((_index + 1))
            continue
          fi
          _remote_changed=1
          GIT_ORIGIN="$_candidate"
        fi
        _selected="$_candidate"
        rm -f "$_fetch_file"
        break
      fi
      _entry_error="$(git_error_with_output "$_candidate" "$_rc" "$_fetch_file")"
      rm -f "$_fetch_file"
      if [ -n "$_errors" ]; then _errors="${_errors}; ${_entry_error}"; else _errors="$_entry_error"; fi
      _index=$((_index + 1))
    done
  fi
  if [ -z "$_selected" ]; then
    GIT_ERROR="fetch-failed: $_errors"
    return 1
  fi

  _timeout="$(git_timeout_for 180)"
  if [ "$_timeout" -le 0 ]; then
    GIT_ERROR="phase-timeout: pull skipped (no budget remaining)"
    return 1
  fi
  _pull_file="${TMPDIR:-/tmp}/cadence-superpowers-pull.$$"
  run_with_timeout "$_timeout" git -C "$SUPERPOWERS_DIR" pull --ff-only origin "$GIT_BRANCH" >"$_pull_file" 2>&1
  _rc=$?
  if [ "$_rc" -ne 0 ]; then
    GIT_ERROR="$(git_error_with_output pull "$_rc" "$_pull_file")"
    rm -f "$_pull_file"
    return 1
  fi
  rm -f "$_pull_file"
  GIT_AFTER_REVISION="$(git -C "$SUPERPOWERS_DIR" rev-parse HEAD 2>/dev/null)"
  [ -n "$GIT_AFTER_REVISION" ] || { GIT_ERROR="git-after-revision-failed"; return 1; }
  GIT_ACTION="fetch-pull-ff-only"
  if [ "$GIT_BEFORE_REVISION" = "$GIT_AFTER_REVISION" ] && [ "$_remote_changed" -eq 0 ]; then
    PHASE_CURRENT_UPDATED=0
    PHASE_CURRENT_RESULT="skipped"
  else
    PHASE_CURRENT_UPDATED=$((PHASE_CURRENT_UPDATED + 1))
  fi
  return 0
}

do_superpowers_git_phase() {
  SUPERPOWERS_DIR="$HOME/.agents/superpowers"
  GIT_ERROR=""; GIT_ACTION="fetch-pull-ff-only"
  GIT_ORIGIN=""; GIT_BRANCH=""; GIT_BEFORE_REVISION=""; GIT_AFTER_REVISION=""
  PHASE_CURRENT_ACTION="fetch-pull-ff-only"
  parse_git_candidates || {
    PHASE_CURRENT_ERROR="${GIT_ERROR:-candidate-parse-failed}"
    PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + 1))
    return 1
  }
  if validate_superpowers_repo; then
    if [ "$MODE" = "check" ]; then
      GIT_ACTION="verify-ready"
      PHASE_CURRENT_ACTION="verify-ready"
      GIT_ORIGIN="$(git -C "$SUPERPOWERS_DIR" remote get-url origin 2>/dev/null)"
      GIT_BRANCH="$(git -C "$SUPERPOWERS_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)"
      GIT_BEFORE_REVISION="$(git -C "$SUPERPOWERS_DIR" rev-parse HEAD 2>/dev/null)"
      GIT_AFTER_REVISION="$GIT_BEFORE_REVISION"
      PHASE_CURRENT_SKIPPED=$((PHASE_CURRENT_SKIPPED + 1))
      PHASE_CURRENT_RESULT="skipped"
      return 0
    fi
    update_superpowers || {
      PHASE_CURRENT_ERROR="${GIT_ERROR:-git-update-failed}"
      PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + 1))
      return 1
    }
  elif [ -e "$SUPERPOWERS_DIR" ] || [ -L "$SUPERPOWERS_DIR" ]; then
    GIT_ACTION="not-git"
    PHASE_CURRENT_ACTION="not-git"
    GIT_ERROR="not-git"
    PHASE_CURRENT_ERROR="$GIT_ERROR"
    PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + 1))
    return 1
  elif [ "$MODE" = "check" ]; then
    GIT_ACTION="check-not-installed"
    PHASE_CURRENT_ACTION="check-not-installed"
    PHASE_CURRENT_SKIPPED=$((PHASE_CURRENT_SKIPPED + 1))
    PHASE_CURRENT_RESULT="skipped"
    return 0
  else
    PHASE_CURRENT_ACTION="clone"
    mkdir -p "$(dirname "$SUPERPOWERS_DIR")" || {
      PHASE_CURRENT_ERROR="mkdir-superpowers-parent-failed"
      PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + 1))
      return 1
    }
    clone_superpowers || {
      PHASE_CURRENT_ERROR="${GIT_ERROR:-clone-failed}"
      PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + 1))
      return 1
    }
  fi
  return 0
}

# Task 4：Superpowers 四层软链同步，仅处理源目录枚举出的条目。
enumerate_superpowers_entries() {
  _list=""
  for _source_entry in "$SUPERPOWERS_DIR/skills/"*; do
    [ -e "$_source_entry" ] || [ -L "$_source_entry" ] || continue
    _name="${_source_entry##*/}"
    [ -n "$_name" ] || continue
    [ -z "$_list" ] && _list="$_name" || _list="$_list\n$_name"
  done
  printf '%b\n' "$_list"
}

# 对绝对路径做物理父目录规范化；不依赖 GNU realpath/readlink -f。
canonical_absolute_path() {
  _path="$1"
  case "$_path" in
    /*) ;;
    *) _path="$(pwd -P)/$_path" ;;
  esac
  _base="${_path##*/}"
  _parent="${_path%/*}"
  [ -n "$_parent" ] || _parent=/
  _parent="$(cd "$_parent" 2>/dev/null && pwd -P)" || printf '%s' "$_path"
  [ -n "$_parent" ] && printf '%s/%s' "$_parent" "$_base"
}

# 将软链原文解析为绝对路径；不使用 GNU readlink -f。
absolute_link_target() {
  _target="$1"
  _raw="$(readlink "$_target" 2>/dev/null)" || return 1
  case "$_raw" in
    /*) canonical_absolute_path "$_raw" ;;
    *) canonical_absolute_path "$(dirname "$_target")/$_raw" ;;
  esac
}

# 递归解析软链至最终绝对目标；循环链以自身当前路径停止，避免无限循环。
resolve_final_link_target() {
  _current="$1"
  _depth=0
  while [ -L "$_current" ] && [ "$_depth" -lt 16 ]; do
    _next="$(absolute_link_target "$_current")" || break
    [ -n "$_next" ] || break
    _current="$_next"
    _depth=$((_depth + 1))
  done
  printf '%s' "$_current"
}

# 仅将最终路径位于 Superpowers 源目录下的条目视为本脚本所有权范围。
is_superpowers_target() {
  case "$1" in
    "$SUPERPOWERS_DIR/skills/"*/*) return 1 ;;
    "$SUPERPOWERS_DIR/skills/"*) return 0 ;;
    *) return 1 ;;
  esac
}

# 软链状态以递归解析后的最终绝对目标判定。
link_state() {
  _target="$1"
  _expected="$2"
  if [ -L "$_target" ]; then
    _actual="$(resolve_final_link_target "$_target")"
    [ "$_actual" = "$_expected" ] && { printf 'correct'; return 0; }
    is_superpowers_target "$_actual" && [ -e "$_actual" ] && { printf 'stale'; return 0; }
    is_superpowers_target "$_actual" && { printf 'broken'; return 0; }
    printf 'conflict'
    return 0
  fi
  [ -e "$_target" ] && printf 'conflict' || printf 'broken'
}

# 建立或修复单条 Superpowers 软链；冲突模式不删除原内容。
ensure_superpowers_link() {
  _source="$1"
  _target="$2"
  _mode="$3"
  _state="$(link_state "$_target" "$_source")"
  case "$_state" in
    correct)
      PHASE_CURRENT_SKIPPED=$((PHASE_CURRENT_SKIPPED + 1))
      printf 'skipped'
      ;;
    stale|broken)
      if [ "$_state" = "broken" ] && [ ! -L "$_target" ]; then
        _action=created
      else
        _action=updated
      fi
      rm -f "$_target" || return 1
      ln -s "$_source" "$_target" || return 1
      [ "$(resolve_final_link_target "$_target")" = "$_source" ] || return 1
      if [ "$_action" = "created" ]; then
        PHASE_CURRENT_CREATED=$((PHASE_CURRENT_CREATED + 1))
      else
        PHASE_CURRENT_UPDATED=$((PHASE_CURRENT_UPDATED + 1))
      fi
      printf '%s' "$_action"
      ;;
    conflict)
      if [ "$_mode" != "no-interrupt" ]; then
        log "${C_YEL}⚠️  保留非 Superpowers 冲突：$_target${C_NC}"
        PHASE_CURRENT_SKIPPED=$((PHASE_CURRENT_SKIPPED + 1))
        printf 'warning-skip'
        return 0
      fi
      _backup="${_target}.cadence-backup-$(date -u +%Y%m%d%H%M%S)"
      if [ -e "$_backup" ] || [ -L "$_backup" ]; then
        _backup="${_backup}-1"
      fi
      mv "$_target" "$_backup" || return 1
      ln -s "$_source" "$_target" || return 1
      [ "$(resolve_final_link_target "$_target")" = "$_source" ] || return 1
      PHASE_CURRENT_UPDATED=$((PHASE_CURRENT_UPDATED + 1))
      printf 'updated'
      ;;
    *) return 1 ;;
  esac
}

# 同步一层，并把所有权限定的状态写入该层报告。
link_layer() {
  _layer="$1"
  if [ "$MODE" = "check" ]; then
    [ -d "$_layer" ] || {
      # check 模式只探测，不为缺失的消费层创建目录。
      _entries="$(enumerate_superpowers_entries)"
      _links=0; _correct=0; _stale=0; _broken=0; _conflicts=0
      while IFS= read -r _name; do
        [ -n "$_name" ] || continue
        _links=$((_links + 1)); _broken=$((_broken + 1))
      done <<EOF
$_entries
EOF
      PHASE_CURRENT_SKIPPED=$((PHASE_CURRENT_SKIPPED + _links))
      PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + _conflicts))
      _layer_item="{\"path\":\"$(json_escape "$_layer")\",\"source_entries\":${PHASE_CURRENT_SOURCE_ENTRIES},\"superpowers_links\":$_links,\"correct\":$_correct,\"stale\":$_stale,\"broken\":$_broken,\"conflicts\":$_conflicts}"
      if [ -z "$PHASE_CURRENT_LAYERS_JSON" ]; then
        PHASE_CURRENT_LAYERS_JSON="$_layer_item"
      else
        PHASE_CURRENT_LAYERS_JSON="${PHASE_CURRENT_LAYERS_JSON},${_layer_item}"
      fi
      return 0
    }
  else
    mkdir -p "$_layer" || return 1
  fi
  _entries="$(enumerate_superpowers_entries)"
  _links=0; _correct=0; _stale=0; _broken=0; _conflicts=0
  _layer_failed=0
  _mode=normal
  [ "$NO_INTERRUPT" = "1" ] && _mode=no-interrupt
  while IFS= read -r _name; do
    [ -n "$_name" ] || continue
    _source="$SUPERPOWERS_DIR/skills/$_name"
    _target="$_layer/$_name"
    _links=$((_links + 1))
    _state="$(link_state "$_target" "$_source")"
    _initial_state="$_state"
    case "$_initial_state" in
      correct) _correct=$((_correct + 1)) ;;
      stale) _stale=$((_stale + 1)) ;;
      broken) _broken=$((_broken + 1)) ;;
      conflict) _conflicts=$((_conflicts + 1)) ;;
    esac
    if [ "$MODE" = "check" ]; then
      PHASE_CURRENT_SKIPPED=$((PHASE_CURRENT_SKIPPED + 1))
      continue
    fi
    ensure_superpowers_link "$_source" "$_target" "$_mode" >/dev/null || {
      PHASE_CURRENT_ERROR="软链创建或验证失败：$_target"
      _layer_failed=1
      break
    }
    # 写入后复核最终状态；冲突计数保留，表示曾发现用户内容冲突。
    _final_state="$(link_state "$_target" "$_source")"
    case "$_initial_state" in
      stale) _stale=$((_stale - 1)) ;;
      broken) _broken=$((_broken - 1)) ;;
    esac
    if [ "$_initial_state" != "correct" ]; then
      case "$_final_state" in
        correct) _correct=$((_correct + 1)) ;;
        stale) [ "$_initial_state" = "stale" ] || _stale=$((_stale + 1)) ;;
        broken) [ "$_initial_state" = "broken" ] || _broken=$((_broken + 1)) ;;
        conflict) [ "$_initial_state" = "conflict" ] || _conflicts=$((_conflicts + 1)) ;;
      esac
    fi

  done <<EOF
$_entries
EOF
  PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + _conflicts))
  _layer_item="{\"path\":\"$(json_escape "$_layer")\",\"source_entries\":${PHASE_CURRENT_SOURCE_ENTRIES},\"superpowers_links\":$_links,\"correct\":$_correct,\"stale\":$_stale,\"broken\":$_broken,\"conflicts\":$_conflicts}"
  if [ -z "$PHASE_CURRENT_LAYERS_JSON" ]; then
    PHASE_CURRENT_LAYERS_JSON="$_layer_item"
  else
    PHASE_CURRENT_LAYERS_JSON="${PHASE_CURRENT_LAYERS_JSON},${_layer_item}"
  fi
  [ "$_layer_failed" -eq 0 ] || return 1
  return 0
}

do_superpowers_links_phase() {
  SUPERPOWERS_DIR="$HOME/.agents/superpowers"
  PHASE_CURRENT_ACTION="sync-four-layers"
  validate_superpowers_repo || {
    PHASE_CURRENT_ERROR="Superpowers 来源不是有效 Git work tree"
    PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + 1))
    return 1
  }
  _entries="$(enumerate_superpowers_entries)"
  PHASE_CURRENT_SOURCE_ENTRIES=0
  while IFS= read -r _name; do
    [ -n "$_name" ] && PHASE_CURRENT_SOURCE_ENTRIES=$((PHASE_CURRENT_SOURCE_ENTRIES + 1))
  done <<EOF
$_entries
EOF
  [ "$PHASE_CURRENT_SOURCE_ENTRIES" -gt 0 ] || {
    PHASE_CURRENT_ERROR="Superpowers skills 源目录为空"
    PHASE_CURRENT_CONFLICTS=$((PHASE_CURRENT_CONFLICTS + 1))
    return 1
  }
  for _layer in "$HOME/.agents/skills" "$HOME/.codex/skills/skills" "$HOME/.claude/skills" "$HOME/.pi/agent/skills"; do
    link_layer "$_layer" || return 1
  done
  if [ "$PHASE_CURRENT_CREATED" -eq 0 ] && [ "$PHASE_CURRENT_UPDATED" -eq 0 ] && [ "$PHASE_CURRENT_CONFLICTS" -eq 0 ]; then
    PHASE_CURRENT_RESULT="skipped"
    PHASE_CURRENT_ACTION="all-skipped"
  fi
  return 0
}
do_verify_phase() { PHASE_CURRENT_ACTION="all-skipped"; return 0; }


log "${C_BLU}🔧 pre-check${C_NC} mode=$MODE mirror=$MIRROR no_interrupt=$NO_INTERRUPT upgrade=$UPGRADE"
log "${C_BLU}📡 npm registry:${C_NC} $CADENCE_NPM_REGISTRY"
log "${C_BLU}🐍 python index:${C_NC} $CADENCE_PY_INDEX"

# --- 通用辅助 ---

FAILED_COUNT=0

# 执行命令并输出首行版本号；命令退出码非零或无输出时返回非零，不打印到 stdout/stderr（避免污染 JSON）
probe_version() {
  # 先单独执行命令并保留退出码（管道会丢失原命令退出码，导致误判 ready）
  _out="$("$@" 2>/dev/null)"
  _rc=$?
  [ "$_rc" -eq 0 ] || return 1
  _out="$(printf '%s' "$_out" | head -n 1 | tr -d '\r')"
  [ -n "$_out" ] || return 1
  printf '%s' "$_out"
}

# JSON 字符串转义（最小集：反斜杠、双引号、控制字符）
# 用 bash 参数展开处理真实控制字符（$'\n'/$'\t'），避免 sed 的 \t/\n 是 GNU 扩展、
# 在 BSD/mac sed 上会把字面字母 t 误转义（bash 3.2 兼容，GNU/BSD 行为一致）
json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"      # 反斜杠（须最先处理）
  s="${s//\"/\\\"}"      # 双引号
  s="${s//$'\n'/\\n}"      # 真实换行符 -> 两字符 \n
  s="${s//$'\t'/\\t}"      # 真实 Tab 符 -> 两字符 \t
  printf '%s' "$s"
}

# 追加一个步骤到 STEPS_JSON（name/status/action/version/error）
add_step() {
  _n="$(json_escape "$1")"; _s="$(json_escape "$2")"; _a="$(json_escape "$3")"
  _v="$(json_escape "$4")"; _e="$(json_escape "$5")"
  _item="{\"name\":\"$_n\",\"status\":\"$_s\",\"action\":\"$_a\",\"version\":\"$_v\",\"error\":\"$_e\"}"
  if [ -z "$STEPS_JSON" ]; then STEPS_JSON="$_item"; else STEPS_JSON="$STEPS_JSON,$_item"; fi
}

# 从 STEPS_JSON 删除指定 name 的旧步骤项（升级后用于替换 do_* 已加的 ready 项，避免重复）。
# 每项均为无嵌套花括号的紧凑 JSON，可按 {"name":"<n>"...} 精确匹配删除后清理多余逗号。
remove_step() {
  _n="$(json_escape "$1")"
  [ -n "$STEPS_JSON" ] || return 0
  STEPS_JSON="$(printf '%s' "$STEPS_JSON" | sed -e "s|{\"name\":\"$_n\"[^{}]*}||g" -e 's/,,*/,/g' -e 's/^,//' -e 's/,$//')"
}

# 失败处理：记录失败项并返回非零；阶段编排器负责统一报告和 no-interrupt 快返。
handle_failure() {
  _name="$1"; _msg="$2"
  FAILED_COUNT=$((FAILED_COUNT + 1))
  PHASE_CURRENT_ERROR="$_msg"
  err "❌ $_name 失败：$_msg"
  return 1
}

# --- 六工具处理 ---
# 每个 do_<tool>：探测版本→已装则 ready 秒跳过；未装则 run 模式安装并复验，check 模式标记 failed。
# 安装命令输出全部重定向，避免污染 stdout 的 JSON。

INSTALL_TRIED=0   # 标记本次是否执行过安装（供摘要）

_try_install() {  # _try_install <描述> <安装命令...>
  _desc="$1"; shift
  if [ "$MODE" != "run" ]; then return 1; fi
  INSTALL_TRIED=1
  log "${C_YEL}⬇️  正在安装 $_desc ...${C_NC}"
  "$@" >/dev/null 2>&1
}

do_npx() {
  if _v="$(probe_version npx --version)"; then
    add_step "npx" "ready" "already-installed" "$_v" ""
    log "${C_GRN}✓ npx 已安装（${_v}）${C_NC}"
  else
    # npx 随 Node.js/npm 提供，无法独立安装
    add_step "npx" "failed" "install-unavailable" "" "npx 未安装；需先安装 Node.js（脚本不自动安装 Node 运行时）"
    handle_failure "npx" "未检测到 npx，请先安装 Node.js"
  fi
}

do_uvx() {
  if _v="$(probe_version uvx --version)"; then
    add_step "uvx" "ready" "already-installed" "$_v" ""
    log "${C_GRN}✓ uvx 已安装（${_v}）${C_NC}"
  else
    if [ "$MODE" = "run" ]; then
      # 经 pip 安装 uv（提供 uvx），走当前源
      # shellcheck disable=SC2046  # 刻意不引号：依赖单词拆分拆成两个 KEY=VAL
      if _try_install "uv（提供 uvx）" env $(uv_index_env) pip install uv; then :; fi
    fi
    if _v="$(probe_version uvx --version)"; then
      add_step "uvx" "installed" "installed-via-pip" "$_v" ""
      log "${C_GRN}✓ uvx 安装成功（${_v}）${C_NC}"
    else
      if [ "$MODE" = "check" ]; then
        add_step "uvx" "failed" "not-ready" "" "uvx 未就绪（check 模式未安装）"
      else
        add_step "uvx" "failed" "install-attempted" "" "uvx 安装失败或未就绪；可手动执行 pip install uv"
      fi
      handle_failure "uvx" "安装后复验失败"
    fi
  fi
}

do_ast_grep() {
  if _v="$(probe_version ast-grep --version)"; then
    add_step "ast-grep" "ready" "already-installed" "$_v" ""
    log "${C_GRN}✓ ast-grep 已安装（${_v}）${C_NC}"
  else
    _try_install "ast-grep" npm i @ast-grep/cli -g "$(npm_registry_args)"
    if _v="$(probe_version ast-grep --version)"; then
      add_step "ast-grep" "installed" "installed-via-npm" "$_v" ""
      log "${C_GRN}✓ ast-grep 安装成功（${_v}）${C_NC}"
    else
      if [ "$MODE" = "check" ]; then
        add_step "ast-grep" "failed" "not-ready" "" "ast-grep 未就绪（check 模式未安装）"
      else
        add_step "ast-grep" "failed" "install-attempted" "" "ast-grep 安装失败；可手动执行 npm i @ast-grep/cli -g"
      fi
      handle_failure "ast-grep" "安装后复验失败"
    fi
  fi
}

do_codegraph() {
  if _v="$(probe_version codegraph version)"; then
    add_step "codegraph" "ready" "already-installed" "$_v" ""
    log "${C_GRN}✓ codegraph 已安装（${_v}）${C_NC}"
  else
    _try_install "codegraph" npm i -g @colbymchenry/codegraph "$(npm_registry_args)"
    if _v="$(probe_version codegraph version)"; then
      add_step "codegraph" "installed" "installed-via-npm" "$_v" ""
      log "${C_GRN}✓ codegraph 安装成功（${_v}）${C_NC}"
    else
      if [ "$MODE" = "check" ]; then
        add_step "codegraph" "failed" "not-ready" "" "codegraph 未就绪（check 模式未安装）"
      else
        add_step "codegraph" "failed" "install-attempted" "" "codegraph 安装失败；可手动执行 npm i -g @colbymchenry/codegraph"
      fi
      handle_failure "codegraph" "安装后复验失败"
    fi
  fi
}

do_openspec() {
  if _v="$(probe_version openspec --version)"; then
    add_step "openspec" "ready" "already-installed" "$_v" ""
    log "${C_GRN}✓ openspec 已安装（${_v}）${C_NC}"
  else
    _try_install "openspec" npm install -g @fission-ai/openspec@latest "$(npm_registry_args)"
    if _v="$(probe_version openspec --version)"; then
      add_step "openspec" "installed" "installed-via-npm" "$_v" ""
      log "${C_GRN}✓ openspec 安装成功（${_v}）${C_NC}"
    else
      if [ "$MODE" = "check" ]; then
        add_step "openspec" "failed" "not-ready" "" "openspec 未就绪（check 模式未安装）"
      else
        add_step "openspec" "failed" "install-attempted" "" "openspec 安装失败；可手动执行 npm install -g @fission-ai/openspec@latest"
      fi
      handle_failure "openspec" "安装后复验失败"
    fi
  fi
}

do_pi_mcp_adapter() {
  # 条件项：pi 不存在则跳过（不算失败）
  if ! command -v pi >/dev/null 2>&1; then
    add_step "pi-mcp-adapter" "skipped" "pi-not-found" "" "未检测到 pi 可执行文件，跳过"
    log "${C_BLU}ℹ️  未检测到 pi，跳过 pi-mcp-adapter${C_NC}"
    return 0
  fi
  if pi list 2>/dev/null | grep -q "pi-mcp-adapter" || [ -d "$HOME/.pi/agent/npm/node_modules/pi-mcp-adapter" ]; then
    add_step "pi-mcp-adapter" "ready" "already-installed" "" ""
    log "${C_GRN}✓ pi-mcp-adapter 已安装${C_NC}"
  else
    _try_install "pi-mcp-adapter" pi install npm:pi-mcp-adapter
    if pi list 2>/dev/null | grep -q "pi-mcp-adapter" || [ -d "$HOME/.pi/agent/npm/node_modules/pi-mcp-adapter" ]; then
      add_step "pi-mcp-adapter" "installed" "installed-via-pi" "" ""
      log "${C_GRN}✓ pi-mcp-adapter 安装成功${C_NC}"
    else
      if [ "$MODE" = "check" ]; then
        add_step "pi-mcp-adapter" "failed" "not-ready" "" "pi-mcp-adapter 未就绪（check 模式未安装）"
      else
        add_step "pi-mcp-adapter" "failed" "install-attempted" "" "pi-mcp-adapter 安装失败；可手动执行 pi install npm:pi-mcp-adapter"
      fi
      handle_failure "pi-mcp-adapter" "安装后复验失败"
    fi
  fi
}

# --- 升级（opt-in）---
# 仅在 UPGRADE=1 时调用。范围：ast-grep/codegraph/openspec（npm 系）+ uv 本体。
# 不含 pi-mcp-adapter、uvx 临时包、playwright-cli。以当前源 latest 为准，不跨源比对。

# 规范化版本号为可比较的三段数字（取首个形如 x.y.z 的子串）
_norm_ver() { printf '%s' "$1" | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -n1; }

# 版本比较：返回 0 表示 $1 < $2（落后需升级），否则非 0。
# 纯 bash 三段数字比较：不依赖 GNU 专属版本排序选项（BSD/mac sort 无此选项，曾致 mac 上静默判为不落后）。
_ver_lt() {
  _a="$(_norm_ver "$1")"; _b="$(_norm_ver "$2")"
  [ -n "$_a" ] && [ -n "$_b" ] || return 1
  [ "$_a" = "$_b" ] && return 1
  _a1="${_a%%.*}"; _ar="${_a#*.}"; _a2="${_ar%%.*}"; _a3="${_ar#*.}"
  _b1="${_b%%.*}"; _br="${_b#*.}"; _b2="${_br%%.*}"; _b3="${_br#*.}"
  # 空段兜底为 0；10# 强制十进制，避免前导零被当八进制
  [ -n "$_a1" ] || _a1=0; [ -n "$_a2" ] || _a2=0; [ -n "$_a3" ] || _a3=0
  [ -n "$_b1" ] || _b1=0; [ -n "$_b2" ] || _b2=0; [ -n "$_b3" ] || _b3=0
  _a1=$((10#$_a1)); _a2=$((10#$_a2)); _a3=$((10#$_a3))
  _b1=$((10#$_b1)); _b2=$((10#$_b2)); _b3=$((10#$_b3))
  [ "$_a1" -lt "$_b1" ] && return 0; [ "$_a1" -gt "$_b1" ] && return 1
  [ "$_a2" -lt "$_b2" ] && return 0; [ "$_a2" -gt "$_b2" ] && return 1
  [ "$_a3" -lt "$_b3" ] && return 0
  return 1
}

# 查询 npm 包当前源 latest 版本
npm_latest() {
  npm view "$1" version "$(npm_registry_args)" 2>/dev/null | head -n1 | tr -d '\r'
}

# 升级某个 npm 工具：<显示名> <包名> <探测命令...>
upgrade_npm_tool() {
  _name="$1"; _pkg="$2"; shift 2
  _cur="$(probe_version "$@")" || return 0   # 未安装则跳过升级（安装归 do_*）
  _lat="$(npm_latest "$_pkg")"
  [ -n "$_lat" ] || { log "${C_YEL}⚠️  $_name 无法查询 latest，跳过升级${C_NC}"; return 0; }
  if _ver_lt "$_cur" "$_lat"; then
    log "${C_YEL}⬆️  升级 ${_name}：$_cur → ${_lat}（来源 ${CADENCE_NPM_REGISTRY}）${C_NC}"
    if npm install -g "$_pkg@latest" "$(npm_registry_args)" >/dev/null 2>&1; then
      _new="$(probe_version "$@")"
      # 校验升级结果：版本非空且已追到 latest 才记 upgraded
      if [ -n "$_new" ] && ! _ver_lt "$_new" "$_lat"; then
        remove_step "$_name"   # 替换 do_* 已加的 ready 项，保证 steps[] 中同名仅一项
        add_step "$_name" "upgraded" "upgraded" "$_new" "from=$_cur to=$_new source=$CADENCE_NPM_REGISTRY"
        return 2   # 返回 2 表示已升级
      fi
    fi
    # 升级失败：计入 FAILED_COUNT 让 overall 反映失败；记录 failed，不谎报 upgraded
    _new="$(probe_version "$@")"
    FAILED_COUNT=$((FAILED_COUNT + 1))
    remove_step "$_name"
    add_step "$_name" "failed" "upgrade-failed" "$_new" "升级 $_lat 失败，当前 ${_new:-未知}"
    log "${C_RED}❌ $_name 升级失败（目标 ${_lat}，当前 ${_new:-未知}）${C_NC}"
    if [ "$NO_INTERRUPT" = "1" ]; then
      err "🛑 no-interrupt 模式：升级失败立即终止"
      emit_report "failed"
      exit 1
    fi
    return 0
  fi
  return 0
}

# 升级 uv 本体
upgrade_uv() {
  _cur="$(probe_version uv --version)" || return 0
  _lat="$(env $(uv_index_env) pip index versions uv 2>/dev/null | sed -n 's/.*(\([0-9][^)]*\)).*/\1/p' | head -n1)"
  [ -n "$_lat" ] || { log "${C_YEL}⚠️  uv 无法查询 latest，跳过升级${C_NC}"; return 0; }
  if _ver_lt "$_cur" "$_lat"; then
    log "${C_YEL}⬆️  升级 uv：$_cur → ${_lat}（来源 ${CADENCE_PY_INDEX}）${C_NC}"
    if env $(uv_index_env) pip install -U uv >/dev/null 2>&1; then
      _new="$(probe_version uv --version)"
      # 校验升级结果：版本非空且已追到 latest 才记 upgraded
      if [ -n "$_new" ] && ! _ver_lt "$_new" "$_lat"; then
        remove_step "uv"
        add_step "uv" "upgraded" "upgraded" "$_new" "from=$_cur to=$_new source=$CADENCE_PY_INDEX"
        return 2
      fi
    fi
    # 升级失败：计入 FAILED_COUNT 让 overall 反映失败；记录 failed，不谎报 upgraded
    _new="$(probe_version uv --version)"
    FAILED_COUNT=$((FAILED_COUNT + 1))
    remove_step "uv"
    add_step "uv" "failed" "upgrade-failed" "$_new" "升级 $_lat 失败，当前 ${_new:-未知}"
    log "${C_RED}❌ uv 升级失败（目标 ${_lat}，当前 ${_new:-未知}）${C_NC}"
    if [ "$NO_INTERRUPT" = "1" ]; then
      err "🛑 no-interrupt 模式：升级失败立即终止"
      emit_report "failed"
      exit 1
    fi
    return 0
  fi
  return 0
}

# --- 报告 ---

# 计算整体状态：有失败→failed（no-interrupt）或 partial；否则 success
compute_overall() {
  if [ "$FAILED_COUNT" -gt 0 ]; then
    if [ "$NO_INTERRUPT" = "1" ]; then printf 'failed'; else printf 'partial'; fi
  else
    printf 'success'
  fi
}

# 输出单份 JSON 到 stdout。<overall> 可由 handle_failure 强制传 failed。
emit_report() {
  _overall="${1:-$(compute_overall)}"
  _ts="$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")"
  # CADENCE_SUPERPOWERS_GIT 使用空格分隔候选；逐项转义后输出 JSON 数组。
  _git_candidates="["
  _git_first=1
  for _candidate in $CADENCE_SUPERPOWERS_GIT; do
    _candidate="$(json_escape "$_candidate")"
    if [ "$_git_first" -eq 1 ]; then
      _git_first=0
    else
      _git_candidates="$_git_candidates,"
    fi
    _git_candidates="$_git_candidates\"$_candidate\""
  done
  _git_candidates="$_git_candidates]"
  _mirror="$(json_escape "$MIRROR")"
  _mode="$(json_escape "$MODE")"
  printf '{\n'
  printf '  "mirror": "%s",\n' "$_mirror"
  printf '  "mode": "%s",\n' "$_mode"
  printf '  "no_interrupt": %s,\n' "$NO_INTERRUPT"
  printf '  "upgrade": %s,\n' "$UPGRADE"
  printf '  "finished_at": "%s",\n' "$_ts"
  printf '  "overall": "%s",\n' "$_overall"
  printf '  "steps": [%s],\n' "$STEPS_JSON"
  printf '  "phases": [%s],\n' "$PHASES_JSON"
  printf '  "next_actions": ["superpowers-sync","openspec-clients","playwright-optional","apikey-placeholder"],\n'
  printf '  "hints": {"superpowers_git_candidates": %s}\n' "$_git_candidates"
  printf '}\n'
}

# --- 主流程：固定五阶段顺序 ---
run_phase "base-tools" do_base_tools
_BASE_RC=$?
if [ "$_BASE_RC" -ne 0 ] && [ "$NO_INTERRUPT" = "1" ]; then
  emit_report "failed"
  exit 1
fi
run_phase "openspec" do_openspec_phase
_OPENSPEC_RC=$?
if [ "$_OPENSPEC_RC" -ne 0 ] && [ "$NO_INTERRUPT" = "1" ]; then
  emit_report "failed"
  exit 1
fi
run_phase "superpowers-git" do_superpowers_git_phase
_GIT_RC=$?
if [ "$_GIT_RC" -ne 0 ] && [ "$NO_INTERRUPT" = "1" ]; then
  emit_report "failed"
  exit 1
fi
run_phase "superpowers-links" do_superpowers_links_phase
_LINKS_RC=$?
if [ "$_LINKS_RC" -ne 0 ] && [ "$NO_INTERRUPT" = "1" ]; then
  emit_report "failed"
  exit 1
fi
run_phase "verify" do_verify_phase
_VERIFY_RC=$?
if [ "$_VERIFY_RC" -ne 0 ] && [ "$NO_INTERRUPT" = "1" ]; then
  emit_report "failed"
  exit 1
fi

# 升级钩子：仅 UPGRADE=1 时执行；仅升级已 ready 的工具。
if [ "$UPGRADE" = "1" ]; then
  log "${C_BLU}⬆️  升级模式（来源：当前 mirror）${C_NC}"
  upgrade_npm_tool "ast-grep" "@ast-grep/cli" ast-grep --version
  upgrade_npm_tool "codegraph" "@colbymchenry/codegraph" codegraph version
  upgrade_npm_tool "openspec" "@fission-ai/openspec" openspec --version
  upgrade_uv
fi

# 汇总输出
_OVERALL="$(compute_overall)"
emit_report "$_OVERALL"

if [ "$_OVERALL" = "failed" ]; then
  exit 1
elif [ "$_OVERALL" = "partial" ]; then
  exit 0   # 普通模式部分失败仍以 0 结束，由 SKILL.md 读 overall 判定
else
  exit 0
fi
