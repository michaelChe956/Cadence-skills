#!/usr/bin/env bash
# timeout 测试替身：记录动态预算后直接执行命令，不制造额外等待。
set -u
_limit="$1"
shift
if [ -n "${FAKE_TIMEOUT_LOG:-}" ]; then
  printf '%s\n' "$_limit" >> "$FAKE_TIMEOUT_LOG"
fi
exec "$@"
