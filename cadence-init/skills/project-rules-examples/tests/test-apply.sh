#!/usr/bin/env bash
# CDPATH= 前缀空格为 POSIX 惯用法（禁用 CDPATH 干扰 cd）——SC1007 误报禁用
# shellcheck disable=SC1007
# apply.sh 行为测试：确定性章节合并（created/pristine/merged/unchanged）
# × 入口只读（skipped/needs-rule-config）× 备份与幂等。
# 用法: bash tests/test-apply.sh   （任一断言失败以非零退出）
set -u

TEST_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APPLY="$TEST_DIR/../scripts/apply.sh"
REFS="$TEST_DIR/../references/project-rules"

PASS=0; FAIL=0
ck() {  # ck <描述> <期望> <实际>
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); else
    FAIL=$((FAIL+1)); printf 'FAIL: %s\n  期望: %s\n  实际: %s\n' "$1" "$2" "$3"
  fi
}

new_proj() { mktemp -d "${TMPDIR:-/tmp}/prx-apply-test.XXXXXX"; }
hash_of() { sha256sum -- "$1" | cut -d' ' -f1; }

drop_section() {  # drop_section <文件> <标题token>：fence 感知删除标题含 token 的章节
  python3 - "$1" "$2" <<'PYEOF'
import re
import sys
from pathlib import Path

path, token = Path(sys.argv[1]), sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
out, fence, skipping, found = [], None, False, False
for line in lines:
    stripped = line.lstrip()
    fence_hit = stripped.startswith("```") or stripped.startswith("~~~")
    if fence is None and fence_hit:
        fence = stripped[0]
    elif fence is not None and fence_hit and stripped[0] == fence:
        fence = None
    if fence is None and re.match(r"^#{1,6}\s+", line):
        skipping = token in line
        found = found or skipping
    if not skipping:
        out.append(line)
assert found, f"未找到章节：{token}"
path.write_text("".join(out), encoding="utf-8")
PYEOF
}

# ---------- T1 全新项目：5 模板 created；入口文件只读报告，绝不创建 ----------
P=$(new_proj)
out=$("$APPLY" --project-root "$P"); rc=$?
ck "T1 退出码 0" "0" "$rc"
ck "T1 README created"      "created cadence/project-rules/README.md"                      "$(grep '/README.md$' <<<"$out")"
ck "T1 requirement created" "created cadence/project-rules/examples/requirement-template.md" "$(grep '/requirement-template.md$' <<<"$out")"
ck "T1 design created"      "created cadence/project-rules/examples/design-template.md"      "$(grep '/design-template.md$' <<<"$out")"
ck "T1 coding created"      "created cadence/project-rules/examples/coding-standards.md"     "$(grep '/coding-standards.md$' <<<"$out")"
ck "T1 test created"        "created cadence/project-rules/examples/test-standards.md"       "$(grep '/test-standards.md$' <<<"$out")"
ck "T1 CLAUDE needs-rule-config" "needs-rule-config CLAUDE.md" "$(grep 'CLAUDE.md' <<<"$out" | grep needs-rule-config)"
ck "T1 AGENTS needs-rule-config" "needs-rule-config AGENTS.md" "$(grep 'AGENTS.md' <<<"$out" | grep needs-rule-config)"
ck "T1 未创建 CLAUDE.md" "missing" "$([ -e "$P/CLAUDE.md" ] && echo exists || echo missing)"
ck "T1 未创建 AGENTS.md" "missing" "$([ -e "$P/AGENTS.md" ] && echo exists || echo missing)"
ck "T1 内容=模板" "$(head -1 "$REFS/README.md")" "$(head -1 "$P/cadence/project-rules/README.md")"
ck "T1 无备份目录" "missing" "$([ -e "$P/cadence/legacy" ] && echo exists || echo missing)"
rm -rf "$P"

# ---------- T2 原封重跑：全部 pristine（幂等、零写入） ----------
P=$(new_proj)
"$APPLY" --project-root "$P" >/dev/null
before=$(hash_of "$P/cadence/project-rules/README.md")
out=$("$APPLY" --project-root "$P")
ck "T2 README pristine" "pristine cadence/project-rules/README.md" "$(grep '/README.md$' <<<"$out")"
ck "T2 文件未被改动" "$before" "$(hash_of "$P/cadence/project-rules/README.md")"
ck "T2 无备份目录" "missing" "$([ -e "$P/cadence/legacy" ] && echo exists || echo missing)"
rm -rf "$P"

# ---------- T3 用户定制：无缺失→unchanged；有缺失→merged 追加+备份；入口只读 ----------
P=$(new_proj)
"$APPLY" --project-root "$P" >/dev/null
CS="$P/cadence/project-rules/examples/coding-standards.md"
printf '\n## 我的团队约定\n\n- 提交前必须跑全量回归\n\n```text\n# 围栏内伪标题\n```\n' >> "$CS"
RM="$P/cadence/project-rules/README.md"
drop_section "$RM" "💡 提示"
cp -- "$RM" "$P/.orig-readme"
printf '# AGENTS.md\n\n## 项目个性化规则\n\n详见 cadence/project-rules/README.md\n' > "$P/AGENTS.md"
printf '# CLAUDE.md\n\n没有引用。\n' > "$P/CLAUDE.md"
cs_before=$(hash_of "$CS"); cm_before=$(hash_of "$P/CLAUDE.md"); ag_before=$(hash_of "$P/AGENTS.md")
rm_size=$(wc -c < "$P/.orig-readme")
out=$("$APPLY" --project-root "$P")
ck "T3 coding unchanged" "unchanged cadence/project-rules/examples/coding-standards.md" "$(grep '/coding-standards.md$' <<<"$out")"
ck "T3 README merged"    "merged cadence/project-rules/README.md" "$(grep '/README.md$' <<<"$out")"
ck "T3 coding 字节不变"  "$cs_before" "$(hash_of "$CS")"
ck "T3 CLAUDE needs-rule-config" "needs-rule-config CLAUDE.md" "$(grep 'CLAUDE.md' <<<"$out" | grep needs-rule-config)"
ck "T3 AGENTS skipped"   "skipped AGENTS.md" "$(grep 'AGENTS.md' <<<"$out" | grep skipped)"
ck "T3 CLAUDE 哈希不变"  "$cm_before" "$(hash_of "$P/CLAUDE.md")"
ck "T3 AGENTS 哈希不变"  "$ag_before" "$(hash_of "$P/AGENTS.md")"
ck "T3 用户行逐字保留"  "1" "$(grep -c '提交前必须跑全量回归' "$CS")"
ck "T3 缺失章节已补齐"  "1" "$(grep -c '## 💡 提示' "$RM")"
head -c "$rm_size" "$RM" > "$P/.prefix.tmp"
if cmp -s -- "$P/.prefix.tmp" "$P/.orig-readme"; then ck "T3 原文前缀逐字节保留" "0" "0"
else ck "T3 原文前缀逐字节保留" "0" "1"; fi
backup=$(find "$P/cadence/legacy" -path '*/cadence/project-rules/README.md' | head -1)
ck "T3 备份存在" "1" "$([ -n "$backup" ] && echo 1 || echo 0)"
if [ -n "$backup" ]; then
  ts=$(basename "$(dirname "$(dirname "$(dirname "$backup")")")")
  ck "T3 备份目录14位时间戳" "14" "${#ts}"
  ck "T3 备份为写入前原像" "$(hash_of "$P/.orig-readme")" "$(hash_of "$backup")"
fi
rm -rf "$P"

# ---------- T4 第二次运行零写入、零备份、输出格式 ----------
P=$(new_proj)
"$APPLY" --project-root "$P" >/dev/null
TS="$P/cadence/project-rules/examples/test-standards.md"
drop_section "$TS" "测试 React 组件"
"$APPLY" --project-root "$P" > "$P/.first-out"
ck "T4 首次 merged" "1" "$(grep -cE '^merged cadence/project-rules/examples/test-standards.md$' "$P/.first-out")"
legacy_before=$(find "$P/cadence/legacy" -maxdepth 1 -mindepth 1 -type d | wc -l)
ck "T4 首次有备份" "1" "$([ "$legacy_before" -ge 1 ] && echo 1 || echo 0)"
snap=$(find "$P/cadence" -type f -exec sha256sum {} + | sort)
out=$("$APPLY" --project-root "$P"); rc=$?
ck "T4 重跑退出码 0" "0" "$rc"
ck "T4 无新增写入状态" "0" "$(grep -cE '^(created|merged) ' <<<"$out")"
ck "T4 文件内容零变化" "$snap" "$(find "$P/cadence" -type f -exec sha256sum {} + | sort)"
ck "T4 备份目录零新增" "$legacy_before" "$(find "$P/cadence/legacy" -maxdepth 1 -mindepth 1 -type d | wc -l)"
ck "T4 输出全部为六态行" "0" "$(grep -cvE '^(created|pristine|merged|unchanged|skipped|needs-rule-config) ' <<<"$out")"
rm -rf "$P"

# ---------- T5 用法错误 ----------
"$APPLY" --project-root /nonexistent-prx-sh >/dev/null 2>&1; rc=$?
ck "T5 项目根不存在退出码 2" "2" "$rc"
"$APPLY" --unknown-flag >/dev/null 2>&1; rc2=$?
ck "T5 未知参数退出码 2" "2" "$rc2"

# ---------- T6 Python 单元/端到端测试 ----------
py_out=$(python3 "$TEST_DIR/test_apply.py" 2>&1); py_rc=$?
if [ "$py_rc" -eq 0 ]; then PASS=$((PASS+1)); else
  FAIL=$((FAIL+1)); printf 'FAIL: T6 python 测试未通过\n%s\n' "$py_out"
fi

printf '%d pass, %d fail\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
