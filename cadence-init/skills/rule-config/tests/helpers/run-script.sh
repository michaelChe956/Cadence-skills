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

# 默认 fake codegraph（harness 隔离屏障）
#
# 背景（codex 复审二轮 Important「harness 非隔离」）：run_script 此前只在调用方显式导出
# RC_FAKE_PATH 时才前置 fake codegraph；大量 Coding fixture（C7 app.ts、C8c app.py、C16m 等）
# 未注入 fake，脚本 S8 会 fallback 到开发机真实 codegraph install/init，违反 Plan「不得依赖开发机
# 真实 codegraph」，且会向 fixture 写入真实 .codegraph/、.mcp.json（args=["serve","--mcp"]）
# 与 .claude/settings.json/CLAUDE.md 副产物，污染用例。
#
# 修复（默认 fake 方案，改动最小）：未设 RC_FAKE_PATH 时，run_script 在唯一固定目录生成一个
# 「全成功 + 写配置」的默认 fake，并前置到子进程 PATH，屏蔽开发机真实 codegraph；
# 需要自定义退出码的 it-s8-* 矩阵仍可通过 RC_FAKE_PATH 覆盖。
# 显式要测真实 codegraph 的用例（目前无）可导出 RC_REAL_CODEGRAPH=1 绕过本屏障。
RC_DEFAULT_FAKE_DIR="/tmp/rule-config-default-fake-codegraph"

_ensure_default_fake_codegraph() {
  # 幂等：目录与可执行文件已存在则直接返回。
  if [ -x "$RC_DEFAULT_FAKE_DIR/codegraph" ]; then
    return 0
  fi
  mkdir -p "$RC_DEFAULT_FAKE_DIR"
  fake_codegraph "$RC_DEFAULT_FAKE_DIR" 0 0 0 1  # install_rc=0 init_rc=0 status_rc=0 write_config=1
}

run_script() {  # run_script <dry-run|apply> <fixture_root> [extra args]
  # 可选 PATH 注入：调用前导出 RC_FAKE_PATH=<dir> 即把该目录前置到子进程 PATH。
  # 用于 it-s8-codegraph-* 矩阵把 fake codegraph bin 暴露给脚本（简报要求 PATH 前置 fake bin）。
  #
  # harness 隔离（codex 复审二轮 Important）：未设 RC_FAKE_PATH 时，默认前置一个「全成功 + 写配置」
  # 的 fake codegraph，屏蔽开发机真实 codegraph；避免 Coding fixture 调用真实 install/init 污染用例。
  # 显式要测真实 codegraph 的用例（目前无）可导出 RC_REAL_CODEGRAPH=1 绕过默认 fake。
  local mode="$1" root="$2"; shift 2
  REPORT="$(mktemp /tmp/rule-config-report.XXXXXX)"
  set +e
  if [ -n "${RC_FAKE_PATH:-}" ]; then
    PATH="$RC_FAKE_PATH:$PATH" python3 "$SCRIPT" "$mode" --project-root "$root" --report "$REPORT" "$@"
  elif [ "${RC_REAL_CODEGRAPH:-0}" = "1" ]; then
    python3 "$SCRIPT" "$mode" --project-root "$root" --report "$REPORT" "$@"
  else
    _ensure_default_fake_codegraph
    PATH="$RC_DEFAULT_FAKE_DIR:$PATH" python3 "$SCRIPT" "$mode" --project-root "$root" --report "$REPORT" "$@"
  fi
  RUN_STATUS=$?
  set -e
}

jqr() { python3 -c "import json,sys;print(json.load(open('$REPORT'))$1)"; }  # 用法: jqr "['overall']"

fake_codegraph() {  # fake_codegraph <bin_dir> <install_rc> <init_rc> <status_rc> <write_config 0|1>
  sed -e "s/@INSTALL_RC@/$2/" -e "s/@INIT_RC@/$3/" -e "s/@STATUS_RC@/$4/" -e "s/@WRITE_CONFIG@/$5/" \
    "$TEST_DIR/helpers/fake-codegraph.sh" > "$1/codegraph"; chmod +x "$1/codegraph"
}
