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
