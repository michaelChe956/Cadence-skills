#!/usr/bin/env bash
# 在隔离 fixture 中运行 pre-check；供 Bash 集成测试复用。
set -u

TEST_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$TEST_DIR/../scripts/pre-check.sh"

if [ "$#" -lt 1 ]; then
  printf '用法: run-pre-check.sh <project-root> [run|check] [参数...]\n' >&2
  exit 2
fi

PROJECT_ROOT="$1"
shift
MODE="${1:-run}"
if [ "$#" -gt 0 ]; then
  shift
fi
REPORT="${PRECHECK_REPORT:-}"
if [ -z "$REPORT" ]; then
  REPORT="$(mktemp "${TMPDIR:-/tmp}/precheck-report.XXXXXX.json")"
  _CLEAN_REPORT=1
else
  _CLEAN_REPORT=0
fi
trap '[ "${_CLEAN_REPORT:-0}" -eq 1 ] && rm -f "$REPORT"' EXIT HUP INT TERM

cd "$PROJECT_ROOT" || exit 1
if [ "$#" -gt 0 ]; then
  bash "$SCRIPT" "$MODE" "$@" > "$REPORT"
else
  bash "$SCRIPT" "$MODE" > "$REPORT"
fi
_rc=$?
cat "$REPORT"
exit "$_rc"
