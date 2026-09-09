#!/usr/bin/env bash
# CDPATH= 前缀空格为 POSIX 惯用法（禁用 CDPATH 干扰 cd）——SC1007 误报禁用
# shellcheck disable=SC1007
# project-rules-examples 幂等铺设脚本——三态判定，永修改既有文件。
#
# 状态语义（每行输出一条）：
#   created     目标不存在，已复制模板/创建引用文件
#   pristine    目标与模板原版逐字节一致（从未被用户改过），跳过
#   needs-merge 目标存在且与模板不同（用户内容），不碰，交模型语义合并
#   skipped     CLAUDE.md/AGENTS.md 已含等价引用，跳过
#
# 退出码：0 正常（含 needs-merge）；2 用法错误；3 内部错误。
# 修改本脚本时必须保持核心安全不变量：已存在的文件绝不被写入。
set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RULES_SRC="$SCRIPT_DIR/../references/project-rules"
PROJECT_ROOT=""

err() { printf '[prx-apply][错误] %s\n' "$*" >&2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --project-root) [ $# -ge 2 ] || { err "--project-root 需要参数"; exit 2; }
                    PROJECT_ROOT="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) err "未知参数：$1"; exit 2 ;;
  esac
done
PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
[ -d "$RULES_SRC" ] || { err "模板源缺失：$RULES_SRC"; exit 3; }
[ -d "$PROJECT_ROOT" ] || { err "项目根不存在：$PROJECT_ROOT"; exit 2; }

# 模板三态铺设：layout <相对模板源路径> <相对项目路径>
layout() {
  local src="$RULES_SRC/$1" dst="$PROJECT_ROOT/$2" rel="$2"
  [ -f "$src" ] || { err "模板文件缺失：$src"; exit 3; }
  if [ ! -e "$dst" ]; then
    mkdir -p "$(dirname -- "$dst")"
    cp -- "$src" "$dst"
    printf 'created %s\n' "$rel"
  elif cmp -s -- "$src" "$dst"; then
    printf 'pristine %s\n' "$rel"
  else
    printf 'needs-merge %s\n' "$rel"
  fi
}

layout "README.md"                          "cadence/project-rules/README.md"
layout "examples/requirement-template.md"   "cadence/project-rules/examples/requirement-template.md"
layout "examples/design-template.md"        "cadence/project-rules/examples/design-template.md"
layout "examples/coding-standards.md"       "cadence/project-rules/examples/coding-standards.md"
layout "examples/test-standards.md"         "cadence/project-rules/examples/test-standards.md"

# 引用文件（CLAUDE.md/AGENTS.md）——存在即用户领地，仅"不存在"和"已有等价引用"可脚本处理：
# 不存在 → 创建最小文件写入引用块；已有等价引用 → skipped；其余 → needs-merge（模型按位置插入）。
REFERENCE_BLOCK="$RULES_SRC/CLAUDE-RULE.md"
ref_anchor() {  # 等价引用判定：含"项目个性化规则"标题且指向 project-rules 目录
  grep -q '项目个性化规则' -- "$1" 2>/dev/null && grep -q 'cadence/project-rules' -- "$1" 2>/dev/null
}

for ref in CLAUDE.md AGENTS.md; do
  dst="$PROJECT_ROOT/$ref"
  if [ ! -e "$dst" ]; then
    { printf '# %s\n\n' "$ref"; cat -- "$REFERENCE_BLOCK"; } > "$dst"
    printf 'created %s\n' "$ref"
  elif ref_anchor "$dst"; then
    printf 'skipped %s\n' "$ref"
  else
    printf 'needs-merge %s\n' "$ref"
  fi
done

exit 0
