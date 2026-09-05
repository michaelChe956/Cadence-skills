#!/usr/bin/env bash
# 捕获结构化 report 后清理调用方创建的独占报告文件。
# 用法：report-cleanup.sh <report-path> [command [args...]]
set -u

REPORT="${1:?用法：report-cleanup.sh <report-path> [command [args...]]}"
shift
trap 'rm -f "$REPORT"' EXIT HUP INT TERM

if [ "$#" -gt 0 ]; then
  "$@" >"$REPORT"
  _rc=$?
else
  _rc=0
fi

# 先让调用方读取结构化结果，再由退出/信号 trap 删除独占报告。
cat "$REPORT"
exit "$_rc"
