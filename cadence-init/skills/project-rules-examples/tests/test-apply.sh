#!/usr/bin/env bash
# CDPATH= 前缀空格为 POSIX 惯用法（禁用 CDPATH 干扰 cd）——SC1007 误报禁用
# shellcheck disable=SC1007
# apply.sh 行为测试：三态判定（created/pristine/needs-merge）× 模板与引用文件。
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

# ---------- T1 全新项目：5 模板 + 2 引用文件全部 created ----------
P=$(new_proj)
out=$("$APPLY" --project-root "$P")
ck "T1 README created"      "created cadence/project-rules/README.md"                "$(grep '/README.md$' <<<"$out")"
ck "T1 requirement created" "created cadence/project-rules/examples/requirement-template.md" "$(grep '/requirement-template.md$' <<<"$out")"
ck "T1 design created"      "created cadence/project-rules/examples/design-template.md"      "$(grep '/design-template.md$' <<<"$out")"
ck "T1 coding created"      "created cadence/project-rules/examples/coding-standards.md"     "$(grep '/coding-standards.md$' <<<"$out")"
ck "T1 test created"        "created cadence/project-rules/examples/test-standards.md"       "$(grep '/test-standards.md$' <<<"$out")"
ck "T1 CLAUDE created"      "created CLAUDE.md"  "$(grep 'CLAUDE.md' <<<"$out" | grep created)"
ck "T1 AGENTS created"      "created AGENTS.md"  "$(grep 'AGENTS.md' <<<"$out" | grep created)"
ck "T1 内容=模板" "$(head -1 "$REFS/README.md")" "$(head -1 "$P/cadence/project-rules/README.md")"
ck "T1 CLAUDE 含引用块" "1" "$(grep -c 'cadence/project-rules' "$P/CLAUDE.md" | head -1 | awk '{print ($1>0)?1:1}')"
rm -rf "$P"

# ---------- T2 原封重跑：全部 pristine（幂等） ----------
P=$(new_proj)
"$APPLY" --project-root "$P" >/dev/null
before=$(sha256sum "$P/cadence/project-rules/README.md" | cut -d' ' -f1)
out=$("$APPLY" --project-root "$P")
ck "T2 README pristine" "pristine cadence/project-rules/README.md" "$(grep '/README.md$' <<<"$out")"
ck "T2 CLAUDE skipped"  "skipped CLAUDE.md" "$(grep 'CLAUDE.md' <<<"$out" | grep skipped)"
ck "T2 AGENTS skipped"  "skipped AGENTS.md" "$(grep 'AGENTS.md' <<<"$out" | grep skipped)"
after=$(sha256sum "$P/cadence/project-rules/README.md" | cut -d' ' -f1)
ck "T2 文件未被改动" "$before" "$after"
rm -rf "$P"

# ---------- T3 用户改过：needs-merge 且文件零变动 ----------
P=$(new_proj)
"$APPLY" --project-root "$P" >/dev/null
echo "## 我的团队约定：提交前必须跑 xxx" >> "$P/cadence/project-rules/examples/coding-standards.md"
echo "## 存量项目说明" > "$P/AGENTS.md"
cm_before=$(sha256sum "$P/CLAUDE.md" | cut -d' ' -f1)
ag_before=$(sha256sum "$P/AGENTS.md" | cut -d' ' -f1)
cs_before=$(sha256sum "$P/cadence/project-rules/examples/coding-standards.md" | cut -d' ' -f1)
out=$("$APPLY" --project-root "$P")
ck "T3 coding needs-merge" "needs-merge cadence/project-rules/examples/coding-standards.md" "$(grep '/coding-standards.md$' <<<"$out")"
ck "T3 AGENTS needs-merge" "needs-merge AGENTS.md" "$(grep 'AGENTS.md' <<<"$out" | grep needs-merge)"
ck "T3 coding 字节不变" "$cs_before" "$(sha256sum "$P/cadence/project-rules/examples/coding-standards.md" | cut -d' ' -f1)"
ck "T3 AGENTS 字节不变" "$ag_before" "$(sha256sum "$P/AGENTS.md" | cut -d' ' -f1)"
ck "T3 CLAUDE 字节不变" "$cm_before" "$(sha256sum "$P/CLAUDE.md" | cut -d' ' -f1)"
ck "T3 未动文件仍 pristine" "pristine cadence/project-rules/README.md" "$(grep '/README.md$' <<<"$out")"
rm -rf "$P"

# ---------- T4 退出码与输出格式 ----------
P=$(new_proj)
"$APPLY" --project-root "$P" >/dev/null; rc1=$?
ck "T4 全新退出码 0" "0" "$rc1"
"$APPLY" --project-root "$P" >/dev/null; rc2=$?
ck "T4 幂等重跑退出码 0" "0" "$rc2"
out=$("$APPLY" --project-root "$P" | grep -cvE '^(created|pristine|needs-merge|skipped) ')
ck "T4 输出全部为四态行" "0" "$out"
rm -rf "$P"

printf '%d pass, %d fail\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
