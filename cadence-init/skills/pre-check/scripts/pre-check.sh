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
  # 安全：仅允许安全字符集（小写字母/数字/连字符/下划线），拒绝路径分隔符与 ../ 逃逸
  case "$_name" in
    *[!a-z0-9_-]*|"")
      err "❌ 非法 mirror 名称: $_name（仅允许 a-z、0-9、-、_）"
      exit 2 ;;
  esac
  _file="$MIRRORS_DIR/$_name.sh"
  if [ ! -f "$_file" ]; then
    err "❌ 未知 mirror: $_name（未找到 $_file）"
    exit 2
  fi
  # 目录边界校验：解析后的真实路径必须仍在 MIRRORS_DIR 内
  _resolved="$(cd "$(dirname "$_file")" 2>/dev/null && pwd -P)/$(basename "$_file")"
  _mirrors_resolved="$(cd "$MIRRORS_DIR" 2>/dev/null && pwd -P)"
  case "$_resolved" in
    "$_mirrors_resolved"/*) : ;;
    *)
      err "❌ mirror 路径越界: $_resolved（不在 $MIRRORS_DIR 内）"
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

load_mirror "$MIRROR"

# JSON 步骤累积（每项一行紧凑 JSON，由 Task 5 汇总）
STEPS_JSON=""

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
      # shellcheck disable=SC2046  # 刻意不引号：依赖单词拆分拆成两个 KEY=VAL
      if _try_install "uv（提供 uvx）" env $(uv_index_env) pip install uv; then :; fi
    fi
    if _v="$(probe_version uvx --version)"; then
      add_step "uvx" "installed" "installed-via-pip" "$_v" ""
      log "${C_GRN}✓ uvx 安装成功（$_v）${C_NC}"
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
    log "${C_GRN}✓ ast-grep 已安装（$_v）${C_NC}"
  else
    _try_install "ast-grep" npm i @ast-grep/cli -g "$(npm_registry_args)"
    if _v="$(probe_version ast-grep --version)"; then
      add_step "ast-grep" "installed" "installed-via-npm" "$_v" ""
      log "${C_GRN}✓ ast-grep 安装成功（$_v）${C_NC}"
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
    log "${C_GRN}✓ codegraph 已安装（$_v）${C_NC}"
  else
    _try_install "codegraph" npm i -g @colbymchenry/codegraph "$(npm_registry_args)"
    if _v="$(probe_version codegraph version)"; then
      add_step "codegraph" "installed" "installed-via-npm" "$_v" ""
      log "${C_GRN}✓ codegraph 安装成功（$_v）${C_NC}"
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
    log "${C_GRN}✓ openspec 已安装（$_v）${C_NC}"
  else
    _try_install "openspec" npm install -g @fission-ai/openspec@latest "$(npm_registry_args)"
    if _v="$(probe_version openspec --version)"; then
      add_step "openspec" "installed" "installed-via-npm" "$_v" ""
      log "${C_GRN}✓ openspec 安装成功（$_v）${C_NC}"
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
# 纯 bash 三段数字比较：不依赖 sort -V（BSD/mac sort 无 -V，曾致 mac 上静默判为不落后）。
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
    log "${C_YEL}⬆️  升级 $_name：$_cur → $_lat（来源 $CADENCE_NPM_REGISTRY）${C_NC}"
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
    log "${C_RED}❌ $_name 升级失败（目标 $_lat，当前 ${_new:-未知}）${C_NC}"
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
    log "${C_YEL}⬆️  升级 uv：$_cur → $_lat（来源 $CADENCE_PY_INDEX）${C_NC}"
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
    log "${C_RED}❌ uv 升级失败（目标 $_lat，当前 ${_new:-未知}）${C_NC}"
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
  _git="$(json_escape "$CADENCE_SUPERPOWERS_GIT")"
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
  printf '  "next_actions": ["superpowers-sync","openspec-clients","playwright-optional","apikey-placeholder"],\n'
  printf '  "hints": {"superpowers_git": "%s"}\n' "$_git"
  printf '}\n'
}

# --- 主流程 ---
do_npx
do_uvx
do_ast_grep
do_codegraph
do_openspec
do_pi_mcp_adapter

# 升级钩子：仅 UPGRADE=1 时执行；仅升级已 ready 的工具
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
