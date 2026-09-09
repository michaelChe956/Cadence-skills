#!/usr/bin/env bash
# Git 测试替身：保留真实 git 语义，同时记录独立 argv 并可模拟网络阻塞。
set -u

if [ -n "${FAKE_GIT_ARGS:-}" ]; then
  {
    printf 'argc=%s' "$#"
    for _arg in "$@"; do printf ' [%s]' "$_arg"; done
    printf '\n'
  } >> "$FAKE_GIT_ARGS"
fi

# 仅模拟 clone/fetch/pull 的远程阻塞；metadata 和本地 git 操作仍委托真实 git。
_case="${1:-}"
for _arg in "$@"; do
  case "$_arg" in
    clone|fetch|pull) _case="$_arg"; break ;;
  esac
done
# 测试可控延迟：用于验证 phase 剩余预算逐次衰减。
if [ -n "${FAKE_GIT_DELAY:-}" ]; then
  sleep "$FAKE_GIT_DELAY"
fi
if [ -n "${FAKE_GIT_BLOCK:-}" ] && [ "$_case" = "$FAKE_GIT_BLOCK" ]; then
  sleep "${FAKE_GIT_BLOCK_SECONDS:-300}"
  exit 124
fi
if [ -n "${FAKE_GIT_FAIL:-}" ] && [ "$_case" = "$FAKE_GIT_FAIL" ]; then
  printf 'fake git forced failure (%s)\n' "$_case" >&2
  exit 42
fi

_REAL_GIT="${REAL_GIT:-/usr/bin/git}"
# 隔离测试将默认镜像候选重写为本地 bare 源；不改变脚本收到的候选 argv。
if [ -n "${FAKE_GIT_CLONE_SOURCE:-}" ] && [ "$_case" = "clone" ]; then
  _args=("$@")
  # clone 参数固定为 clone [options] <candidate> <destination>，取倒数第二个参数。
  _candidate_index=$(($# - 2))
  _args[$_candidate_index]="$FAKE_GIT_CLONE_SOURCE"
  exec "$_REAL_GIT" "${_args[@]}"
fi
exec "$_REAL_GIT" "$@"
