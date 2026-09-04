#!/usr/bin/env bash
# pre-check 测试目录入口；先执行 Bash smoke，再执行 Python 阶段测试。
set -u
TEST_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PASS=0
FAIL=0

if bash "$TEST_DIR/../scripts/test.sh"; then
  PASS=$((PASS + 1))
else
  FAIL=$((FAIL + 1))
fi
if (cd "$TEST_DIR" && python3 -m unittest discover -s . -p 'test_*.py' -v); then
  PASS=$((PASS + 1))
else
  FAIL=$((FAIL + 1))
fi
printf 'test.sh: %s pass, %s fail\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
