#!/usr/bin/env bash
#
# run-script.sh — rule-config 脚本 CLI 驱动 helper（Task 3 引入）
#
# 由 verify-managed-lifecycle.sh 顶部定义 TEST_DIR 后 source；提供：
#   - SKILL_DIR / SCRIPT / SKILL_MD 等路径常量
#   - run_script <dry-run|apply> <fixture_root> [extra args]：调用脚本并捕获退出码
#   - jqr "<python subscript>"：从最新 REPORT 读取 JSON 字段
#   - fake_codegraph <bin_dir> <install_rc> <init_rc> <status_rc> <write_config 0|1>：
#     生成可注入 PATH 的 fake codegraph 可执行文件
#
# 注意：脚本尚不存在时（RED 阶段）run_script 会失败、REPORT 为空、jqr 报错——属预期。

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # tests/
SKILL_DIR="$(cd "$TEST_DIR/.." && pwd)"                        # rule-config/
SCRIPT="$SKILL_DIR/scripts/rule-config.py"
SKILL_MD="$SKILL_DIR/SKILL.md"

run_script() {  # run_script <dry-run|apply> <fixture_root> [extra args]
  # 可选 PATH 注入：调用前导出 RC_FAKE_PATH=<dir> 即把该目录前置到子进程 PATH。
  # 用于 it-s8-codegraph-* 矩阵把 fake codegraph bin 暴露给脚本（简报要求 PATH 前置 fake bin）。
  local mode="$1" root="$2"; shift 2
  REPORT="$(mktemp /tmp/rule-config-report.XXXXXX)"
  set +e
  if [ -n "${RC_FAKE_PATH:-}" ]; then
    PATH="$RC_FAKE_PATH:$PATH" python3 "$SCRIPT" "$mode" --project-root "$root" --report "$REPORT" "$@"
  else
    python3 "$SCRIPT" "$mode" --project-root "$root" --report "$REPORT" "$@"
  fi
  RUN_STATUS=$?
  set -e
}

jqr() { python3 -c "import json,sys;print(json.load(open('$REPORT'))$1)"; }  # 用法: jqr "['overall']"

fake_codegraph() {  # fake_codegraph <bin_dir> <install_rc> <init_rc> <status_rc> <write_config 0|1>
  sed -e "s/@INSTALL_RC@/$2/" -e "s/@INIT_RC@/$3/" -e "s/@STATUS_RC@/$4/" -e "s/@WRITE_CONFIG@/$5/" \
    "$TEST_DIR/helpers/fake-codegraph.sh" > "$1/codegraph"; chmod +x "$1/codegraph"
}
