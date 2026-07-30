#!/usr/bin/env bash
# Cadence pre-check 主脚本：六个基础工具的探测/安装/复验。
# 职责边界：仅处理 npx/uvx/ast-grep/codegraph/openspec/pi-mcp-adapter。
# 不处理 Superpowers 软链、OpenSpec 三客户端产物、Playwright、API Key（由 SKILL.md 处理）。
# 用法:
#   pre-check.sh run   [--mirror <name>] [--no-interrupt] [--upgrade]
#   pre-check.sh check [--mirror <name>] [--no-interrupt]
# 输出: stdout = 单份 JSON 报告；stderr = 彩色人类摘要。
# 兼容: mac bash 3.2 + BSD 工具 / Linux GNU 工具（POSIX 子集，无关联数组/grep -P）。

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
  _file="$MIRRORS_DIR/$_name.sh"
  if [ ! -f "$_file" ]; then
    err "❌ 未知 mirror: $_name（未找到 $_file）"
    exit 2
  fi
  # shellcheck disable=SC1090
  . "$_file"
  : "${CADENCE_NPM_REGISTRY:?mirror 缺少 CADENCE_NPM_REGISTRY}"
  : "${CADENCE_PY_INDEX:?mirror 缺少 CADENCE_PY_INDEX}"
  : "${CADENCE_SUPERPOWERS_GIT:?mirror 缺少 CADENCE_SUPERPOWERS_GIT}"
}

# 命令级源注入助手
npm_registry_args() { printf '%s' "--registry=$CADENCE_NPM_REGISTRY"; }
uv_index_env()      { printf '%s' "UV_INDEX_URL=$CADENCE_PY_INDEX"; }

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

load_mirror "$MIRROR"

# JSON 步骤累积（每项一行紧凑 JSON，由 Task 5 汇总）
STEPS_JSON=""

log "${C_BLU}🔧 pre-check${C_NC} mode=$MODE mirror=$MIRROR no_interrupt=$NO_INTERRUPT upgrade=$UPGRADE"
log "${C_BLU}📡 npm registry:${C_NC} $CADENCE_NPM_REGISTRY"
log "${C_BLU}🐍 python index:${C_NC} $CADENCE_PY_INDEX"

# --- 通用辅助 ---

FAILED_COUNT=0

# 执行命令并输出首行版本号；失败返回非零，不打印到 stdout/stderr（避免污染 JSON）
probe_version() {
  _out="$("$@" 2>/dev/null | head -n 1 | tr -d '\r')" || return 1
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

# 失败处理：no-interrupt 立即非零退出；否则计数并继续
handle_failure() {
  _name="$1"; _msg="$2"
  FAILED_COUNT=$((FAILED_COUNT + 1))
  err "❌ $_name 失败：$_msg"
  if [ "$NO_INTERRUPT" = "1" ]; then
    err "🛑 no-interrupt 模式：立即终止"
    # 输出当前已累积 JSON 后退出（overall 由 Task 5 标记为 failed）
    emit_report "failed"
    exit 1
  fi
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
    log "${C_GRN}✓ npx 已安装（$_v）${C_NC}"
  else
    # npx 随 Node.js/npm 提供，无法独立安装
    add_step "npx" "failed" "install-unavailable" "" "npx 未安装；需先安装 Node.js（脚本不自动安装 Node 运行时）"
    handle_failure "npx" "未检测到 npx，请先安装 Node.js"
  fi
}

do_uvx() {
  if _v="$(probe_version uvx --version)"; then
    add_step "uvx" "ready" "already-installed" "$_v" ""
    log "${C_GRN}✓ uvx 已安装（$_v）${C_NC}"
  else
    if [ "$MODE" = "run" ]; then
      # 经 pip 安装 uv（提供 uvx），走当前源
      if _try_install "uv（提供 uvx）" env "$(uv_index_env)" pip install uv; then :; fi
    fi
    if _v="$(probe_version uvx --version)"; then
      add_step "uvx" "installed" "installed-via-pip" "$_v" ""
      log "${C_GRN}✓ uvx 安装成功（$_v）${C_NC}"
    else
      add_step "uvx" "failed" "install-attempted" "" "uvx 安装失败或未就绪；可手动执行 pip install uv"
      handle_failure "uvx" "安装后复验失败"
    fi
  fi
}

do_ast_grep() {
  if _v="$(probe_version ast-grep --version)"; then
    add_step "ast-grep" "ready" "already-installed" "$_v" ""
    log "${C_GRN}✓ ast-grep 已安装（$_v）${C_NC}"
  else
    _try_install "ast-grep" npm i @ast-grep/cli -g "$(npm_registry_args)"
    if _v="$(probe_version ast-grep --version)"; then
      add_step "ast-grep" "installed" "installed-via-npm" "$_v" ""
      log "${C_GRN}✓ ast-grep 安装成功（$_v）${C_NC}"
    else
      add_step "ast-grep" "failed" "install-attempted" "" "ast-grep 安装失败；可手动执行 npm i @ast-grep/cli -g"
      handle_failure "ast-grep" "安装后复验失败"
    fi
  fi
}

do_codegraph() {
  if _v="$(probe_version codegraph version)"; then
    add_step "codegraph" "ready" "already-installed" "$_v" ""
    log "${C_GRN}✓ codegraph 已安装（$_v）${C_NC}"
  else
    _try_install "codegraph" npm i -g @colbymchenry/codegraph "$(npm_registry_args)"
    if _v="$(probe_version codegraph version)"; then
      add_step "codegraph" "installed" "installed-via-npm" "$_v" ""
      log "${C_GRN}✓ codegraph 安装成功（$_v）${C_NC}"
    else
      add_step "codegraph" "failed" "install-attempted" "" "codegraph 安装失败；可手动执行 npm i -g @colbymchenry/codegraph"
      handle_failure "codegraph" "安装后复验失败"
    fi
  fi
}

do_openspec() {
  if _v="$(probe_version openspec --version)"; then
    add_step "openspec" "ready" "already-installed" "$_v" ""
    log "${C_GRN}✓ openspec 已安装（$_v）${C_NC}"
  else
    _try_install "openspec" npm install -g @fission-ai/openspec@latest "$(npm_registry_args)"
    if _v="$(probe_version openspec --version)"; then
      add_step "openspec" "installed" "installed-via-npm" "$_v" ""
      log "${C_GRN}✓ openspec 安装成功（$_v）${C_NC}"
    else
      add_step "openspec" "failed" "install-attempted" "" "openspec 安装失败；可手动执行 npm install -g @fission-ai/openspec@latest"
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
      add_step "pi-mcp-adapter" "failed" "install-attempted" "" "pi-mcp-adapter 安装失败；可手动执行 pi install npm:pi-mcp-adapter"
      handle_failure "pi-mcp-adapter" "安装后复验失败"
    fi
  fi
}

# --- 升级（opt-in）---
# 仅在 UPGRADE=1 时调用。范围：ast-grep/codegraph/openspec（npm 系）+ uv 本体。
# 不含 pi-mcp-adapter、uvx 临时包、playwright-cli。以当前源 latest 为准，不跨源比对。

# 规范化版本号为可比较的三段数字（取首个形如 x.y.z 的子串）
_norm_ver() { printf '%s' "$1" | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -n1; }

# 版本比较：返回 0 表示 $1 < $2（落后需升级），否则非 0。依赖 sort -V（GNU/BSD 均有）。
_ver_lt() {
  _a="$(_norm_ver "$1")"; _b="$(_norm_ver "$2")"
  [ -n "$_a" ] && [ -n "$_b" ] || return 1
  [ "$_a" = "$_b" ] && return 1
  [ "$(printf '%s\n%s\n' "$_a" "$_b" | sort -V | head -n1)" = "$_a" ]
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
    log "${C_YEL}⬆️  升级 $_name：$_cur → $_lat（来源 $CADENCE_NPM_REGISTRY）${C_NC}"
    npm install -g "$_pkg@latest" "$(npm_registry_args)" >/dev/null 2>&1
    _new="$(probe_version "$@")"
    add_step "$_name" "upgraded" "upgraded" "$_new" "from=$_cur to=$_lat source=$CADENCE_NPM_REGISTRY"
    return 2   # 返回 2 表示已升级（供调用方覆盖原 ready 项）
  fi
  return 0
}

# 升级 uv 本体
upgrade_uv() {
  _cur="$(probe_version uv --version)" || return 0
  _lat="$(env "$(uv_index_env)" pip index versions uv 2>/dev/null | sed -n 's/.*(\([0-9][^)]*\)).*/\1/p' | head -n1)"
  [ -n "$_lat" ] || { log "${C_YEL}⚠️  uv 无法查询 latest，跳过升级${C_NC}"; return 0; }
  if _ver_lt "$_cur" "$_lat"; then
    log "${C_YEL}⬆️  升级 uv：$_cur → $_lat（来源 $CADENCE_PY_INDEX）${C_NC}"
    env "$(uv_index_env)" pip install -U uv >/dev/null 2>&1
    _new="$(probe_version uv --version)"
    add_step "uv" "upgraded" "upgraded" "$_new" "from=$_cur to=$_lat source=$CADENCE_PY_INDEX"
    return 2
  fi
  return 0
}
