#!/usr/bin/env bash
# stack —— devbox 中间件栈 CLI（Contract 2；实现见 stack-lib.sh）
set -euo pipefail
_lib="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)/stack-lib.sh"
[ -f "$_lib" ] || _lib=/usr/local/lib/cadence/stack-lib.sh
# shellcheck source=stack-lib.sh
source "$_lib"

usage() {
  cat <<'EOF'
用法：stack <子命令> [参数]（环境变量 CADENCE_STACK_DIR，默认 /cadence/stack）
  status                    服务运行状态（按 label 直查 docker，双运行时兼容）
  ls                        官方目录 + 当前启用 profile + CHANGES.md 摘要
  enable <svc|profile>      启用目录内服务（写 COMPOSE_PROFILES 并尝试拉起）
  disable <svc|profile>     停用（profile 服务移出 COMPOSE_PROFILES；默认服务仅 stop）
  restart <svc>             重启服务
  logs <svc>                跟随日志（--tail 100）
  conn <svc>                打印标准连接串 + application.yaml 片段
  add <name> [--tpl <T>]    目录外自加服务（模板默认取官方目录同名项；自动留痕 CHANGES.md）
  rm <name> [--purge]       删除服务（--purge 连数据卷，二次确认）
  app run <name> <cmd…>     本地应用后台启动（nohup；pid/log 落 stack/../run/app/）
  app stop <name>           停止本地应用
  app logs <name> [N]       查看本地应用日志（默认尾 100 行）
  app port <name> <port>    端口探活（默认 30s 超时）
EOF
}

stack_add_cli() {
  local name="" tpl=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --tpl) tpl="$2"; shift 2 ;;
      *) name="$1"; shift ;;
    esac
  done
  [ -n "$name" ] || { usage >&2; return 2; }
  stack_add_service "$name" "${tpl:-$name}"
}

stack_rm_cli() {
  local name="" purge=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --purge) purge="--purge"; shift ;;
      *) name="$1"; shift ;;
    esac
  done
  [ -n "$name" ] || { usage >&2; return 2; }
  stack_rm_service "$name" "$purge"
}

main() {
  [ $# -ge 1 ] || { usage >&2; return 2; }
  local cmd="$1"; shift
  case "$cmd" in
    status)   stack_status ;;
    ls)       stack_ls ;;
    enable)   [ $# -eq 1 ] || { usage >&2; return 2; }; stack_enable "$1" ;;
    disable)  [ $# -eq 1 ] || { usage >&2; return 2; }; stack_disable "$1" ;;
    restart)  [ $# -eq 1 ] || { usage >&2; return 2; }; stack_restart "$1" ;;
    logs)     [ $# -eq 1 ] || { usage >&2; return 2; }; stack_logs "$1" --tail 100 -f ;;
    conn)     [ $# -eq 1 ] || { usage >&2; return 2; }; stack_conn_print "$1" ;;
    add)      stack_add_cli "$@" ;;
    rm)       stack_rm_cli "$@" ;;
    app)
      [ $# -ge 2 ] || { usage >&2; return 2; }
      case "$1" in
        run)  [ $# -ge 3 ] || { usage >&2; return 2; }; shift; app_run "$@" ;;
        stop) app_stop "$2" ;;
        logs) app_logs "$2" "${3:-100}" ;;
        port) [ $# -ge 3 ] || { usage >&2; return 2; }; app_port "$2" "$3" "${4:-30}" ;;
        *) printf '未知 app 子命令：%s\n' "$1" >&2; usage >&2; return 2 ;;
      esac ;;
    -h|--help|help) usage ;;
    *) printf '未知子命令：%s\n' "$cmd" >&2; usage >&2; return 2 ;;
  esac
}

main "$@"
