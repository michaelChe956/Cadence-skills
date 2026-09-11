#!/usr/bin/env bash
# stack-lib.sh —— devbox 中间件栈函数库（可 source；仅依赖 bash + docker CLI）
# 环境变量：CADENCE_STACK_DIR（默认 /cadence/stack）
#           CADENCE_STACK_CATALOG_DIR（默认 /opt/cadence/stack/catalog，测试可覆盖）
stack_lib_self_dir() { cd "$(dirname "${BASH_SOURCE[0]}")" && pwd; }
: "${CADENCE_STACK_DIR:=/cadence/stack}"
: "${CADENCE_STACK_CATALOG_DIR:=/opt/cadence/stack/catalog}"
STACK_COMPOSE_FILE="$CADENCE_STACK_DIR/compose.yaml"
STACK_ENV_FILE="$CADENCE_STACK_DIR/.env"
STACK_CHANGES_FILE="$CADENCE_STACK_DIR/CHANGES.md"

stack_compose() {
  docker compose --project-directory "$CADENCE_STACK_DIR" -f "$STACK_COMPOSE_FILE" "$@"
}

# ---------- 纯函数：COMPOSE_PROFILES 读写 ----------

stack_profiles_add() {  # $1=当前串 $2=profile → 新串（幂等）
  local cur="$1" add="$2" item
  [ -z "$cur" ] && { printf '%s\n' "$add"; return 0; }
  for item in ${cur//,/ }; do
    [ "$item" = "$add" ] && { printf '%s\n' "$cur"; return 0; }
  done
  printf '%s,%s\n' "$cur" "$add"
}

stack_profiles_remove() {  # $1=当前串 $2=profile → 新串
  local cur="$1" del="$2" item first=1 out=""
  for item in ${cur//,/ }; do
    [ "$item" = "$del" ] && continue
    if [ "$first" = 1 ]; then out="$item"; first=0; else out="$out,$item"; fi
  done
  printf '%s\n' "$out"
}

stack_read_profiles() {  # 从 stack/.env 读 COMPOSE_PROFILES（无文件→空）
  [ -f "$STACK_ENV_FILE" ] || { printf ''; return 0; }
  sed -n 's/^COMPOSE_PROFILES=//p' "$STACK_ENV_FILE" | tail -1
}

stack_write_profiles() {  # $1=新值：写入/覆盖 .env 的 COMPOSE_PROFILES 行
  local val="$1"
  if [ -f "$STACK_ENV_FILE" ] && grep -q '^COMPOSE_PROFILES=' "$STACK_ENV_FILE"; then
    sed -i "s/^COMPOSE_PROFILES=.*/COMPOSE_PROFILES=${val}/" "$STACK_ENV_FILE"
  else
    printf 'COMPOSE_PROFILES=%s\n' "$val" >> "$STACK_ENV_FILE"
  fi
}

# ---------- 纯函数：catalog ----------

stack_catalog_names() {
  local d
  for d in "$CADENCE_STACK_CATALOG_DIR"/*/; do
    [ -d "$d" ] && basename "$d"
  done
}

stack_is_catalog() { [ -n "${1:-}" ] && [ -d "$CADENCE_STACK_CATALOG_DIR/$1" ]; }

stack_resolve_profile() {  # $1=服务名或 profile 名 → 输出 profile；默认服务报错
  local arg="$1" prof
  if stack_is_catalog "$arg"; then
    prof="$(cat "$CADENCE_STACK_CATALOG_DIR/$arg/profile" 2>/dev/null || true)"
  else
    prof="$arg"
  fi
  if [ "$prof" = "default" ] || [ -z "$prof" ]; then
    printf '%s 为默认启用服务（无需 profile）；如未运行请执行 stack restart %s\n' "$arg" "$arg" >&2
    return 1
  fi
  printf '%s\n' "$prof"
}

stack_services_of_profile() {  # $1=profile → 目录内归属该 profile 的服务名列表
  local d p
  for d in "$CADENCE_STACK_CATALOG_DIR"/*/; do
    [ -d "$d" ] || continue
    p="$(cat "$d/profile" 2>/dev/null || true)"
    [ "$p" = "$1" ] && basename "$d"
  done
}

# ---------- 纯函数：compose 项目/容器解析（label 直连 docker，Docker Desktop 与 podman 双兼容） ----------

compose_project_name() {  # compose.yaml 顶层 name → $CADENCE_COMPOSE_PROJECT → cadence
  local name=""
  if [ -f "$STACK_COMPOSE_FILE" ]; then
    name="$(python3 -c '
import sys
try:
    import yaml
    with open(sys.argv[1], encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    n = doc.get("name") if isinstance(doc, dict) else None
    if isinstance(n, str) and n:
        print(n)
except Exception:
    pass
' "$STACK_COMPOSE_FILE" 2>/dev/null || true)"
  fi
  if [ -z "$name" ] && [ -f "$STACK_COMPOSE_FILE" ]; then   # 无 python3+yaml 时的文本兜底
    name="$(sed -n 's/^name:[[:space:]]*//p' "$STACK_COMPOSE_FILE" | head -1 || true)"
    name="${name#\"}"; name="${name%\"}"
  fi
  if [ -n "$name" ]; then printf '%s\n' "$name"; return 0; fi
  if [ -n "${CADENCE_COMPOSE_PROJECT:-}" ]; then printf '%s\n' "$CADENCE_COMPOSE_PROJECT"; return 0; fi
  printf 'cadence\n'
}

stack_cid_of() {  # $1=服务名 → 该服务首个容器 ID（label 过滤；空=无容器）
  docker ps -aq \
    --filter "label=com.docker.compose.project=$(compose_project_name)" \
    --filter "label=com.docker.compose.service=$1" 2>/dev/null | head -1 || true
}

# ---------- 纯函数：conn / CHANGES / compose 文本操作 ----------

stack_conn_print() {  # $1=服务名：打印标准连接串+application 片段（静态模板，直出）
  local f="$CADENCE_STACK_CATALOG_DIR/$1/conn.txt"
  if [ ! -f "$f" ]; then
    printf '未找到服务 %s 的连接模板（可用：%s）\n' "$1" "$(stack_catalog_names | tr '\n' ' ')" >&2
    return 1
  fi
  cat "$f"
}

stack_changes_append() {  # $1=add|rm|enable|disable $2=name —— CHANGES.md 唯一写入口
  printf -- '- %s %s %s\n' "$(date +%F)" "$1" "$2" >> "$STACK_CHANGES_FILE"
}

stack_add_service() {  # $1=新服务名 $2=catalog 模板名（默认=$1）
  local name="$1" tpl="${2:-$1}" frag tmpblock
  frag="$CADENCE_STACK_CATALOG_DIR/$tpl/service.fragment.yaml"
  if [ ! -f "$frag" ]; then
    printf '目录内无模板 %s（可用：%s）；无模板的自加请以最接近的模板为底再手改\n' \
      "$tpl" "$(stack_catalog_names | tr '\n' ' ')" >&2
    return 1
  fi
  if grep -qE "^  ${name}:" "$STACK_COMPOSE_FILE"; then
    printf '服务 %s 已存在于 %s\n' "$name" "$STACK_COMPOSE_FILE" >&2
    return 1
  fi
  tmpblock="$(mktemp)"
  sed "1s/^  [A-Za-z0-9_-]*:/  ${name}:/" "$frag" > "$tmpblock"
  printf '\n' >> "$STACK_COMPOSE_FILE"
  cat "$tmpblock" >> "$STACK_COMPOSE_FILE"     # services: 为模板最后一个顶层键，纯文本追加安全
  rm -f "$tmpblock"
  mkdir -p "$CADENCE_STACK_DIR/data/$name"     # 自加服务数据走 bind（官方四件套才用外部卷）
  stack_changes_append add "$name"
  printf '已追加服务 %s（模板 %s）到 compose.yaml，数据落 stack/data/%s；提醒：临时配置，建议反馈维护者固化入官方目录\n' \
    "$name" "$tpl" "$name"
}

stack_rm_service_block() {  # $1=服务名：从 compose.yaml 删除 "  name:" 块（纯文本）
  local name="$1" file="$STACK_COMPOSE_FILE"
  grep -qE "^  ${name}:" "$file" || { printf '未找到服务 %s\n' "$name" >&2; return 1; }
  awk -v svc="  ${name}:" '
    $0 == svc { skip = 1; next }
    skip && (/^  [A-Za-z0-9_.-]+:/ || /^[A-Za-z_#]/) { skip = 0 }
    !skip { print }
  ' "$file" > "$file.cadence-tmp" && mv "$file.cadence-tmp" "$file"
}

stack_rm_service() {  # $1=服务名 [$2=--purge]：停删容器+删块+留痕；--purge 二次确认后连数据
  local name="$1" purge="${2:-}" cid
  if [ "$purge" = "--purge" ]; then
    printf '将删除服务 %s 及其数据（stack/data/%s 与外部卷 cadence_%s-data）且不可恢复，确认请输入 y：' \
      "$name" "$name" "$name" >&2
    local reply
    read -r reply
    if [ "$reply" != "y" ]; then
      printf '已取消\n' >&2
      return 1
    fi
    rm -rf "${CADENCE_STACK_DIR:?}/data/$name"
    docker volume rm "cadence_${name}-data" >/dev/null 2>&1 || true   # 官方目录服务的外部卷；docker 依赖腿 T9 验
  fi
  cid="$(stack_cid_of "$name")"                     # label 直连：podman-compose 容器名风格不同，不靠 compose 插件
  if [ -n "$cid" ]; then
    docker rm -f "$cid" >/dev/null 2>&1 \
      || printf '[警告] 服务 %s 容器删除失败（宿主侧手动 docker rm %s）\n' "$name" "$cid" >&2
  fi
  stack_rm_service_block "$name" || return 1
  stack_changes_append rm "$name"
  printf '已删除服务 %s（CHANGES.md 已留痕）\n' "$name"
}

# ---------- 命令实现（enable/disable 含 docker 拉起/停止腿）----------

stack_enable() {  # $1=目录内服务名或 profile 名
  local target="$1" profile cur new
  profile="$(stack_resolve_profile "$target")" || return 0   # 默认服务：提示后成功返回
  cur="$(stack_read_profiles)"
  new="$(stack_profiles_add "$cur" "$profile")"
  stack_write_profiles "$new"
  stack_changes_append enable "$target"
  printf '已启用 profile=%s（COMPOSE_PROFILES=%s），尝试拉起……\n' "$profile" "$new"
  # --profile 按 compose 文件取该 profile 的完整服务集（含 stack add 自加的同 profile 服务），不依赖 catalog 枚举（评审 F2）
  stack_compose up -d --profile "$profile" \
    || printf '[警告] 容器内拉起失败（将在宿主侧下次 compose up 时生效）：见上方错误\n' >&2
  return 0
}

stack_disable() {  # $1=目录内服务名或 profile 名
  local target="$1" profile cur new svc
  if stack_is_catalog "$target"; then
    profile="$(cat "$CADENCE_STACK_CATALOG_DIR/$target/profile" 2>/dev/null || echo "$target")"
  else
    profile="$target"
  fi
  if [ "$profile" = "default" ]; then
    printf '停用默认服务 %s：仅停止容器，保留数据卷\n' "$target" >&2
    stack_compose stop "$target" || printf '[警告] 停止失败（宿主侧执行 docker compose stop %s）\n' "$target" >&2
  else
    cur="$(stack_read_profiles)"
    new="$(stack_profiles_remove "$cur" "$profile")"
    stack_write_profiles "$new"
    for svc in $(stack_services_of_profile "$profile"); do
      stack_compose stop "$svc" >/dev/null 2>&1 \
        || printf '[警告] 停止 %s 失败（宿主侧下次 up 收敛）\n' "$svc" >&2
    done
  fi
  stack_changes_append disable "$target"
  printf '已停用 %s（COMPOSE_PROFILES=%s）\n' "$target" "$(stack_read_profiles)"
  return 0
}

stack_ls() {
  printf '== 官方目录（%s）==\n' "$CADENCE_STACK_CATALOG_DIR"
  local d
  for d in "$CADENCE_STACK_CATALOG_DIR"/*/; do
    [ -d "$d" ] || continue
    printf '  %-12s profile=%s\n' "$(basename "$d")" "$(cat "$d/profile" 2>/dev/null || echo '?')"
  done
  printf '== 当前 COMPOSE_PROFILES ==\n  %s\n（为空=仅默认服务 mysql+redis）\n' "$(stack_read_profiles)"
  if [ -f "$STACK_CHANGES_FILE" ]; then
    printf '== CHANGES.md（最近 5 条）==\n'
    tail -5 "$STACK_CHANGES_FILE" | sed 's/^/  /'
  else
    printf '== CHANGES.md：无（未被用户/agent 改动，容器启动时自动同步官方模板）==\n'
  fi
}

# ---------- status/restart/logs：label 直连 docker API ----------
# podman-compose 不设 docker compose v2 过滤所用的 config-hash 标签（容器名风格也不同），
# compose ps/restart/logs 子命令在 podman socket 下静默失效；两运行时都设 project/service 标签，故按 label 直查。

stack_service_status_line() {  # $1=项目名 $2=服务名：打印单行状态（无容器→未启动）
  local info state ports
  info="$(docker ps -a \
    --filter "label=com.docker.compose.project=$1" \
    --filter "label=com.docker.compose.service=$2" \
    --format '{{.Status}}|{{.Ports}}' 2>/dev/null | head -1 || true)"
  if [ -z "$info" ]; then
    printf '  %-12s 未启动\n' "$2"
    return 0
  fi
  state="${info%%|*}"
  ports="${info#*|}"
  [ "$ports" = "$info" ] && ports=""                      # 输出无 |（无端口）：不把状态串误当端口
  if [ -n "$ports" ]; then
    printf '  %-12s %s（端口 %s）\n' "$2" "$state" "$ports"
  else
    printf '  %-12s %s\n' "$2" "$state"
  fi
}

stack_status() {  # 按服务枚举（catalog + docker 中带项目 label 的自加服务），label 过滤 docker ps
  local proj svc extra
  proj="$(compose_project_name)"
  printf '== compose 项目 %s 服务状态 ==\n' "$proj"
  for svc in $(stack_catalog_names); do
    stack_service_status_line "$proj" "$svc"
  done
  extra="$(docker ps -a --filter "label=com.docker.compose.project=$proj" \
    --format '{{.Label "com.docker.compose.service"}}' 2>/dev/null | sort -u || true)"
  for svc in $extra; do                    # stack add 的自加服务不在 catalog，单独补列
    if stack_catalog_names | grep -x "$svc" >/dev/null; then continue; fi   # 不用 -q：-q 早退令上游 SIGPIPE，pipefail 下误判未命中
    stack_service_status_line "$proj" "$svc"
  done
}

stack_restart() {  # $1=服务名：stack_cid_of 定位容器后 docker restart（双运行时兼容）
  local cid
  cid="$(stack_cid_of "$1")"
  if [ -z "$cid" ]; then
    printf '未找到服务 %s 的运行容器（compose 项目 %s）；请确认服务已拉起后再试\n' \
      "$1" "$(compose_project_name)" >&2
    return 1
  fi
  docker restart "$cid"
}

stack_logs() {  # $1=服务名 $2...=透传给 docker logs 的参数（如 --tail 100 -f）
  local svc="$1"; shift
  local cid
  cid="$(stack_cid_of "$svc")"
  if [ -z "$cid" ]; then
    printf '未找到服务 %s 的运行容器，无法读取日志\n' "$svc" >&2
    return 1
  fi
  docker logs "$@" "$cid"
}

# ---------- app 本地应用生命周期（设计 4.8 一期命令组；pid/日志在 $CADENCE_STACK_DIR/../run/app/） ----------
STACK_APP_DIR="$CADENCE_STACK_DIR/../run/app"

app_pidfile() { printf '%s/%s.pid\n' "$STACK_APP_DIR" "$1"; }
app_logfile() { printf '%s/%s.log\n' "$STACK_APP_DIR" "$1"; }

app_run() {  # $1=应用名；$2...=启动命令（nohup 后台；pid 落盘；幂等）
  local name="$1"; shift
  [ $# -ge 1 ] || { printf '用法：app_run <name> <命令…>\n' >&2; return 2; }
  mkdir -p "$STACK_APP_DIR"
  if [ -f "$(app_pidfile "$name")" ] && kill -0 "$(cat "$(app_pidfile "$name")")" 2>/dev/null; then
    printf '应用 %s 已在运行（pid %s）\n' "$name" "$(cat "$(app_pidfile "$name")")"
    return 0
  fi
  nohup "$@" >>"$(app_logfile "$name")" 2>&1 </dev/null &
  printf '%s\n' "$!" >"$(app_pidfile "$name")"
  printf '应用 %s 已后台启动（pid %s，日志 %s）\n' "$name" "$!" "$(app_logfile "$name")"
}

app_stop() {  # $1=应用名
  local name="$1" pf pid
  pf="$(app_pidfile "$name")"
  if [ ! -f "$pf" ]; then
    printf '应用 %s 未在运行（无 pid 文件）\n' "$name" >&2
    return 1
  fi
  pid="$(cat "$pf")"
  if kill "$pid" 2>/dev/null; then
    rm -f "$pf"
    printf '应用 %s 已停止（pid %s）\n' "$name" "$pid"
  else
    rm -f "$pf"
    printf '应用 %s 的 pid %s 已不存在，清理 pid 文件\n' "$name" "$pid"
  fi
}

app_logs() {  # $1=应用名 [$2=行数，默认 100]
  local name="$1" n="${2:-100}"
  [ -f "$(app_logfile "$name")" ] || { printf '应用 %s 暂无日志（%s）\n' "$name" "$(app_logfile "$name")" >&2; return 1; }
  tail -n "$n" "$(app_logfile "$name")"
}

app_port() {  # $1=应用名 $2=端口 [$3=超时秒，默认 30]——探活带超时
  local name="$1" port="$2" t="${3:-30}" i=0
  while [ "$i" -lt "$t" ]; do
    if (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then
      printf '应用 %s 端口 %s 已就绪（等待 %ss）\n' "$name" "$port" "$i"
      return 0
    fi
    sleep 1; i=$((i + 1))
  done
  printf '应用 %s 端口 %s 在 %ss 内未就绪；看日志：%s\n' "$name" "$port" "$t" "$(app_logfile "$name")" >&2
  return 1
}
