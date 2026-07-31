#!/usr/bin/env bash
#
# verify-managed-lifecycle.sh — rule-config 脚本 CLI 集成 harness（Task 3 改造）
#
# 用法：bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
#
# 驱动对象：cadence-init/skills/rule-config/scripts/rule-config.py（Task 4+ 实现）
#   CLI: rule-config.py {dry-run|apply} --project-root <path> --report <path> \
#        [--no-interrupt] [--decisions <file>] [--project-type coding|non-coding] \
#        [--ignore-cadence] [--enable-playwright] [--enable-codegraph]
#
# 报告 JSON schema（契约期冻结，供后续 Task 实现）：
#   { "overall": "ok|fail|degraded",
#     "mode": "normal|no-interrupt",
#     "budget_seconds_excluding_codegraph": <number>,
#     "steps": [ { "name": "s1_detect|s2_locate_templates|s3_rules_files|s4_entry_files|
#                          s5_scaffold|s6_gitignore|s7_openspec_config|s8_codegraph",
#                  "status": "ok|skip|degraded|fail",
#                  "action": "<create|merge|replace|skip|...>",
#                  "reason": "<string>",
#                  "elapsed_ms": <number, s8 必含>,
#                  "assets": [ { "path": "<rel>", "action": "...",
#                                "conflict": "<kind|null>", "backup_needed": <bool> } ],
#                  "conflicts": [ { "conflict_id": "<id>", "kind": "...", "decision": "..." } ] } ],
#     "hints": { "next": "mcp-configuration" },
#     "project_type": "coding|non-coding",
#     "techstack": { "language": "...", "pkg_manager": "...", "test": "...",
#                    "lint": "...", "format": "...", "coverage": "80%" },
#     "history_detected": [ "<dir>", ... ],
#     "decisions_applied": [ { "conflict_id": "...", "decision": "..." } ] }
#
# RED 阶段（脚本不存在）：所有 run_script 调用失败、REPORT 为空、jqr 报错、
# 静态 sc-script-exists 失败 → SUMMARY fail>0、整体退出码非零。属预期。

set -u

TEST_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=helpers/run-script.sh
. "$TEST_DIR/helpers/run-script.sh"

REPO_ROOT=$(CDPATH= cd -- "$TEST_DIR/../../../.." && pwd)
KERNEL="$TEST_DIR/../references/rules/agent-routing-kernel.md"
L1_SOURCE="$TEST_DIR/../references/rules/openspec-superpowers-workflow.md"
CONFIG_TEMPLATE="$TEST_DIR/../references/openspec/config.yaml"

# 静态契约：脚本 PRUNE_DIRS 常量必须与 SKILL.md 的 find 剪枝清单一致。
# 脚本尚不存在时（RED）该检查 fail，属预期。
assert_bounded_source_scan_contract() {
  if [ ! -f "$SCRIPT" ]; then
    printf '脚本不存在，无法核对 PRUNE_DIRS 常量: %s\n' "$SCRIPT" >&2
    return 1
  fi
  python3 - "$SCRIPT" "$SKILL_MD" <<'PY'
import pathlib
import re
import sys

# codex 终审 I6 修复：map(func, iterable) 单可迭代用法（原 sys.argv[1:2]/[2:3]
# 双可迭代会 TypeError，检查永远失败但只打印不计 fail → 假绿）。
script_path, skill_path = map(pathlib.Path, sys.argv[1:3])
script_text = script_path.read_text(encoding="utf-8")
skill_text = skill_path.read_text(encoding="utf-8")

# 期望脚本中存在 PRUNE_DIRS 常量（列表或集合形式）
m = re.search(r"PRUNE_DIRS\s*[:=]\s*\[([^\]]*)\]|PRUNE_DIRS\s*[:=]\s*\{([^}]*)\}", script_text)
if not m:
    print("脚本缺少 PRUNE_DIRS 常量定义", file=sys.stderr)
    raise SystemExit(1)
raw = m.group(1) or m.group(2)
prune = sorted(
    tok.strip().strip('"').strip("'")
    for tok in raw.split(",")
    if tok.strip().strip('"').strip("'")
)

# 从 SKILL.md 的 find 命令提取 -name <dir> 剪枝项（find 到 -prune 之间为 -type d 段）
find_block = re.search(r"find\s+\.\s.*?-prune", skill_text, re.S)
if not find_block:
    print("无法从 SKILL.md 提取 find 剪枝清单", file=sys.stderr)
    raise SystemExit(1)
skill_prune = sorted(set(re.findall(r"-name\s+([\w.-]+)", find_block.group(0))))

# SKILL.md 约定「剪枝目录清单与脚本 PRUNE_DIRS 常量逐项一致，不得增删」→ 双向一致
if prune != skill_prune:
    print(f"脚本 PRUNE_DIRS 与 SKILL.md 剪枝清单不一致: script={prune} skill={skill_prune}", file=sys.stderr)
    raise SystemExit(1)
raise SystemExit(0)
PY
}

for required in "$KERNEL" "$L1_SOURCE" "$CONFIG_TEMPLATE" "$SKILL_MD"; do
  if [ ! -e "$required" ]; then
    printf '缺少测试依赖: %s\n' "$required" >&2
    exit 1
  fi
done

# codex 终审 I6：PRUNE_DIRS 静态契约移入 D 区 record_result 计数（见 D10），
# 不再提前只打印不计 fail（原实现假绿）。

TEST_ROOT=$(mktemp -d)
trap 'rm -rf "$TEST_ROOT"' EXIT HUP INT TERM

PASS_COUNT=0
FAIL_COUNT=0

sha256_file() {
  local hash_line
  local hash

  if command -v sha256sum >/dev/null 2>&1; then
    hash_line=$(sha256sum "$1") || return $?
  elif command -v shasum >/dev/null 2>&1; then
    hash_line=$(shasum -a 256 "$1") || return $?
  else
    printf '缺少 SHA-256 工具：需要 sha256sum 或 shasum -a 256\n' >&2
    return 127
  fi
  hash=$(awk 'NR == 1 { print $1; exit }' <<<"$hash_line") || return $?
  if [ -z "$hash" ]; then
    printf 'SHA-256 工具未返回文件哈希：%s\n' "$1" >&2
    return 1
  fi
  printf '%s\n' "$hash"
}

sha256_pair() {
  local first_hash
  local second_hash

  first_hash=$(sha256_file "$1") || return $?
  second_hash=$(sha256_file "$2") || return $?
  printf '%s:%s\n' "$first_hash" "$second_hash"
}

# 对 fixture 全树取 sha256（用于 dry-run 零写入、失败关闭零写入断言）。
# codex 终审 I6：不再硬编码 sha256sum——逐文件哈希复用 harness 已有的
# sha256_file 工具选择函数（sha256sum 优先、shasum -a 256 回退），
# 最终聚合哈希同样按 PATH 选择工具，无 macOS 缺失风险。
tree_hash() {
  local root=$1
  local listing
  # 排除 .git 与 cadence 备份文件（<file>.cadence-backup-<ts>）；
  # 备份是脚本恢复产物，非对项目源文件的修改，「零写入」断言应聚焦源文件。
  listing=$(
    cd "$root" || exit 1
    find . -type f -not -path './.git/*' \
      -not -name '*.cadence-backup-*' | sort | while IFS= read -r f; do
      h=$(sha256_file "$f") || exit $?
      printf '%s  %s\n' "$h" "$f"
    done
  ) || return $?
  if command -v sha256sum >/dev/null 2>&1; then
    printf '%s\n' "$listing" | sha256sum | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    printf '%s\n' "$listing" | shasum -a 256 | awk '{print $1}'
  else
    printf '缺少 SHA-256 工具：需要 sha256sum 或 shasum -a 256\n' >&2
    return 127
  fi
}

managed_block_hash() {
  local hash_input
  local hash
  local status

  hash_input=$(mktemp "$TEST_ROOT/.managed-block-hash-XXXXXX") || return $?
  if ! awk '/cadence-managed:openspec-superpowers-routing:v1:start/{inside=1} inside{print} /cadence-managed:openspec-superpowers-routing:v1:end/{inside=0; exit}' "$1" > "$hash_input"; then
    rm -f "$hash_input"
    return 1
  fi
  hash=$(sha256_file "$hash_input")
  status=$?
  rm -f "$hash_input"
  [ "$status" -eq 0 ] || return "$status"
  printf '%s\n' "$hash"
}

outside_l0_hash() {
  local hash_input
  local hash
  local status

  hash_input=$(mktemp "$TEST_ROOT/.outside-l0-hash-XXXXXX") || return $?
  if ! awk '
    /cadence-managed:openspec-superpowers-routing:v[0-9]+:start/ { inside=1; next }
    /cadence-managed:openspec-superpowers-routing:v[0-9]+:end/ { inside=0; next }
    !inside { print }
  ' "$1" > "$hash_input"; then
    rm -f "$hash_input"
    return 1
  fi
  hash=$(sha256_file "$hash_input")
  status=$?
  rm -f "$hash_input"
  [ "$status" -eq 0 ] || return "$status"
  printf '%s\n' "$hash"
}

replace_first_visible_paragraph() {
  local source_file=$1
  local replacement=$2
  local source_dir
  local temporary_file

  source_dir=$(dirname "$source_file") || return 1
  temporary_file=$(mktemp "$source_dir/.${source_file##*/}.cadence-replace-XXXXXX") || return 1
  if ! awk -v replacement="$replacement" '
    {
      if (!replaced) {
        match_position = index($0, "首个用户可见段落")
        if (match_position > 0) {
          $0 = substr($0, 1, match_position - 1) replacement substr($0, match_position + length("首个用户可见段落"))
          replaced = 1
        }
      }
      print
    }
    END {
      exit !replaced
    }
  ' "$source_file" > "$temporary_file"; then
    rm -f "$temporary_file"
    return 1
  fi
  if ! mv "$temporary_file" "$source_file"; then
    rm -f "$temporary_file"
    return 1
  fi
  return 0
}

record_result() {
  name=$1
  status=$2
  before=$3
  after=$4
  result=$5
  if [ "$result" = pass ]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    printf 'PASS %-48s status=%s before=%s after=%s\n' "$name" "$status" "$before" "$after"
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf 'FAIL %-48s status=%s before=%s after=%s\n' "$name" "$status" "$before" "$after" >&2
  fi
}

assert_same() {
  name=$1
  status=$2
  before=$3
  after=$4
  expected_status=$5
  if [ "$status" -eq "$expected_status" ] && [ "$before" = "$after" ]; then
    record_result "$name" "$status" "$before" "$after" pass
  else
    record_result "$name" "$status" "$before" "$after" fail
  fi
}

assert_changed() {
  name=$1
  status=$2
  before=$3
  after=$4
  if [ "$status" -eq 0 ] && [ "$before" != "$after" ]; then
    record_result "$name" "$status" "$before" "$after" pass
  else
    record_result "$name" "$status" "$before" "$after" fail
  fi
}

is_single_application_source() {
  printf '%s\n' "$1" | awk '
    NF {
      nonempty_line_count += 1
      source_path = $0
    }
    END {
      exit !(nonempty_line_count == 1 && source_path ~ /^\.\/application\/[^\/]+\.(py|ts)$/)
    }
  '
}

# 决策文件 helper：把 decisions 数组写成 JSON 文件（项目根之外）。
write_decisions() {  # write_decisions <path> <json-array-string>
  printf '%s\n' "$2" > "$1"
}

# fixture：从仓库真实入口复制（带漂移注入）。
mk_entry_fixture() {  # mk_entry_fixture <name> [drift-claude] [drift-agents]
  local root="$TEST_ROOT/$1"
  local drift_c="${2-}"
  local drift_a="${3-}"
  mkdir -p "$root"
  cp "$REPO_ROOT/CLAUDE.md" "$root/CLAUDE.md"
  cp "$REPO_ROOT/AGENTS.md" "$root/AGENTS.md"
  [ -z "$drift_c" ] || replace_first_visible_paragraph "$root/CLAUDE.md" "$drift_c"
  [ -z "$drift_a" ] || replace_first_visible_paragraph "$root/AGENTS.md" "$drift_a"
  printf '%s\n' "$root"
}

# codex 终审 I2 适配：仓库真实入口复制件缺规范摘要行/技术栈块（L0 skip 但未收敛）。
# I2 后 S4 对 skip 状态也会补齐摘要/技术栈（SM-02/DF-02），未收敛入口复制件在
# apply 后必然变化。需要先证明「其余内容不变」的用例，改用本 helper 预收敛：
# 对入口复制件先跑一次 apply --no-interrupt（收敛摘要/技术栈），再供用例使用。
mk_converged_entries() {  # mk_converged_entries <target_root> [coding]：向目标根写入收敛态 CLAUDE.md/AGENTS.md
  # 第二参数 coding 时 scratch 预置 application/app.py，使收敛态匹配 coding 项目入口
  # 描述（RULE2_TEXT_CODING），避免 coding fixture 第二次 apply 触发 S4 upgrade。
  local target="$1"
  local kind="${2-}"
  local scratch
  scratch="$(mk_entry_fixture ".converge-scratch-$(basename "$target")")"
  if [ "$kind" = "coding" ]; then
    mkdir -p "$scratch/application"
    printf 'def main():\n    pass\n' > "$scratch/application/app.py"
  fi
  local saved_report="${REPORT-}"
  run_script apply "$scratch" --no-interrupt
  REPORT="$saved_report"
  cp "$scratch/CLAUDE.md" "$target/CLAUDE.md"
  cp "$scratch/AGENTS.md" "$target/AGENTS.md"
}

# OpenSpec config 合并结果逐字段比对：以模板与旧值合并，断言字段集合。
assert_openspec_merged_fields() {  # assert_openspec_merged_fields <config-path> <expected-substring...>
  local config="$1"
  shift
  local ok=1
  python3 - "$config" "$@" <<'PY'
import pathlib
import sys

import yaml

config_path = pathlib.Path(sys.argv[1])
expected = sys.argv[2:]
try:
    doc = yaml.safe_load(config_path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(2)
if not isinstance(doc, dict):
    raise SystemExit(3)
rules = doc.get("rules") or {}
for group in ("proposal", "design", "specs", "tasks"):
    if group not in rules or not isinstance(rules[group], list) or not rules[group]:
        raise SystemExit(4)
text = config_path.read_text(encoding="utf-8")
for needle in expected:
    if needle not in text:
        raise SystemExit(5)
raise SystemExit(0)
PY
  return $?
}

# codex 终审 I4：报告完整性——conflicts 条目含 allowed_decisions（非空）、
# 各 step 含数值型 elapsed_ms（>=0 真实计时值）。
assert_report_completeness() {  # assert_report_completeness <report-json>
  python3 - "$1" <<'PY'
import json
import sys

d = json.load(open(sys.argv[1]))
for c in d.get("conflicts", []):
    if not c.get("allowed_decisions"):
        raise SystemExit(f"conflict 缺 allowed_decisions: {c}")
for s in d.get("steps", []):
    if not (isinstance(s.get("elapsed_ms"), (int, float)) and s["elapsed_ms"] >= 0):
        raise SystemExit(f"step 缺真实 elapsed_ms: {s}")
raise SystemExit(0)
PY
}

# ============================================================================
# A. SHA-256 工具契约（沿用，不依赖脚本）
# ============================================================================

assert_sha256_tool_contract() {
  local hash_file
  local sha256_tools
  local shasum_tools
  local failing_tools
  local no_hash_tools
  local output
  local status
  local error_file

  hash_file="$TEST_ROOT/hash-input"
  printf 'managed lifecycle hash fixture\n' > "$hash_file"

  sha256_tools="$TEST_ROOT/hash-tools-sha256sum"
  mkdir -p "$sha256_tools"
  ln -s "$(command -v awk)" "$sha256_tools/awk"
  printf '%s\n' '#!/bin/sh' 'printf "%s\\n" sha256sum-selected' > "$sha256_tools/sha256sum"
  printf '%s\n' '#!/bin/sh' 'printf "%s\\n" shasum-selected' > "$sha256_tools/shasum"
  chmod +x "$sha256_tools/sha256sum" "$sha256_tools/shasum"
  if output=$(PATH="$sha256_tools" sha256_file "$hash_file"); then
    status=0
  else
    status=$?
  fi
  if [ "$status" -eq 0 ] && [ "$output" = 'sha256sum-selected' ]; then
    record_result hash-prefers-sha256sum "$status" "$output" sha256sum-selected pass
  else
    record_result hash-prefers-sha256sum "$status" "$output" sha256sum-selected fail
  fi

  shasum_tools="$TEST_ROOT/hash-tools-shasum"
  mkdir -p "$shasum_tools"
  ln -s "$(command -v awk)" "$shasum_tools/awk"
  printf '%s\n' '#!/bin/sh' 'printf "%s\\n" shasum-selected' > "$shasum_tools/shasum"
  chmod +x "$shasum_tools/shasum"
  if output=$(PATH="$shasum_tools" sha256_file "$hash_file"); then
    status=0
  else
    status=$?
  fi
  if [ "$status" -eq 0 ] && [ "$output" = 'shasum-selected' ]; then
    record_result hash-falls-back-to-shasum "$status" "$output" shasum-selected pass
  else
    record_result hash-falls-back-to-shasum "$status" "$output" shasum-selected fail
  fi

  failing_tools="$TEST_ROOT/hash-tools-failing"
  mkdir -p "$failing_tools"
  ln -s "$(command -v awk)" "$failing_tools/awk"
  printf '%s\n' '#!/bin/sh' 'printf "%s\\n" sha256sum-failed >&2' 'exit 75' > "$failing_tools/sha256sum"
  chmod +x "$failing_tools/sha256sum"
  error_file="$TEST_ROOT/hash-failure.stderr"
  if output=$(PATH="$failing_tools" sha256_file "$hash_file" 2> "$error_file"); then
    status=0
  else
    status=$?
  fi
  if [ "$status" -eq 75 ] && grep -Fq 'sha256sum-failed' "$error_file"; then
    record_result hash-command-failure-propagates "$status" "$output" 75 pass
  else
    record_result hash-command-failure-propagates "$status" "$output" 75 fail
  fi

  no_hash_tools="$TEST_ROOT/hash-tools-missing"
  mkdir -p "$no_hash_tools"
  error_file="$TEST_ROOT/hash-missing.stderr"
  if output=$(PATH="$no_hash_tools" sha256_file "$hash_file" 2> "$error_file"); then
    status=0
  else
    status=$?
  fi
  if [ "$status" -eq 127 ] && grep -Fq '缺少 SHA-256 工具：需要 sha256sum 或 shasum -a 256' "$error_file"; then
    record_result hash-missing-tools-fails "$status" "$output" 127 pass
  else
    record_result hash-missing-tools-fails "$status" "$output" 127 fail
  fi
}

set -e

assert_sha256_tool_contract

# A2. tree_hash 工具路径契约（codex 终审 I6）：sha256sum 优先、shasum -a 256 回退
# 两条路径结果一致；无工具时非零失败并给提示（受控 PATH 用例）。
th_fixture="$TEST_ROOT/tree-hash-fixture"
mkdir -p "$th_fixture/sub"
printf 'alpha\n' > "$th_fixture/a.txt"
printf 'beta\n' > "$th_fixture/sub/b.txt"

th_tools_sum="$TEST_ROOT/tree-hash-tools-sha256sum"
mkdir -p "$th_tools_sum"
for t in find sort awk sha256sum; do ln -s "$(command -v "$t")" "$th_tools_sum/$t"; done

th_tools_shasum="$TEST_ROOT/tree-hash-tools-shasum"
mkdir -p "$th_tools_shasum"
for t in find sort awk; do ln -s "$(command -v "$t")" "$th_tools_shasum/$t"; done
# fake shasum：仅支持 `-a 256` 形式，转发到真实 sha256sum（绝对路径）
printf '%s\n' '#!/bin/sh' 'if [ "$1" = "-a" ]; then shift 2; fi' \
  "exec $(command -v sha256sum) \"\$@\"" > "$th_tools_shasum/shasum"
chmod +x "$th_tools_shasum/shasum"

if th_hash_sum=$(PATH="$th_tools_sum" tree_hash "$th_fixture"); then
  th_sum_status=0
else
  th_sum_status=$?
fi
if th_hash_shasum=$(PATH="$th_tools_shasum" tree_hash "$th_fixture"); then
  th_shasum_status=0
else
  th_shasum_status=$?
fi
if [ "$th_sum_status" -eq 0 ] && [ "$th_shasum_status" -eq 0 ] \
  && [ -n "$th_hash_sum" ] && [ "$th_hash_sum" = "$th_hash_shasum" ]; then
  record_result tree-hash-tool-paths-equal 0 "$th_hash_sum" "$th_hash_shasum" pass
else
  record_result tree-hash-tool-paths-equal 1 "$th_hash_sum" "$th_hash_shasum" fail
fi

th_tools_none="$TEST_ROOT/tree-hash-tools-none"
mkdir -p "$th_tools_none"
for t in find sort awk; do ln -s "$(command -v "$t")" "$th_tools_none/$t"; done
th_err="$TEST_ROOT/tree-hash-missing.stderr"
if th_output=$(PATH="$th_tools_none" tree_hash "$th_fixture" 2> "$th_err"); then
  th_status=0
else
  th_status=$?
fi
if [ "$th_status" -ne 0 ] && grep -Fq '缺少 SHA-256 工具' "$th_err"; then
  record_result tree-hash-missing-tools-fails "$th_status" "$th_output" nonzero pass
else
  record_result tree-hash-missing-tools-fails "$th_status" "$th_output" nonzero fail
fi

# ============================================================================
# B. 迁移既有 22 用例 → CLI 驱动（it-* 命名）
# ============================================================================

# B1. 真实入口复制件收敛后必须幂等（it-s4-idempotent / L0-P6+L0-02+SM-01）。
# codex 终审 I2：skip 状态也补齐缺失摘要/技术栈——首次 apply 为收敛写入（属
# I2 预期行为），第二次 apply 起双入口 sha256 不变才是幂等断言点。
case_root="$(mk_entry_fixture fx-entry-idempotent)"
run_script apply "$case_root" --no-interrupt
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_script apply "$case_root" --no-interrupt
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
assert_same it-s4-idempotent "$RUN_STATUS" "$before" "$after" 0

# B2. 当前 L0 漂移在普通模式无响应时必须 fail closed + 零写入（it-s4-drift-normal / L0-P7）。
# 评审裁决修正：与 it-decisions-missing 语义对齐——普通模式 apply 遇 conflict 无 --decisions
# 必须 status≠0 且零写入（fail closed）。原期望 status=0 与权威用例矛盾。
case_root="$(mk_entry_fixture fx-l0-drift '本地漂移段落' '')"
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_script apply "$case_root"
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
if [ "$RUN_STATUS" -ne 0 ] && [ "$before" = "$after" ]; then
  record_result it-s4-drift-normal "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s4-drift-normal "$RUN_STATUS" "$before" "$after" fail
fi

# B3. no-interrupt 修复漂移时，区块外内容必须逐字保留（it-s4-drift-replace-outside-preserved / L0-P7+L0-B2）。
# codex 终审 I2 适配：入口先收敛（摘要/技术栈补齐），再注入 L0 区块内漂移，
# 使「区块外逐字保留」断言不被 I2 的缺失摘要补齐扰动。
case_root="$TEST_ROOT/fx-l0-drift-replace"
mkdir -p "$case_root"
mk_converged_entries "$case_root"
replace_first_visible_paragraph "$case_root/CLAUDE.md" '本地漂移段落'
replace_first_visible_paragraph "$case_root/AGENTS.md" '另一个漂移段落'
outside_claude_before=$(outside_l0_hash "$case_root/CLAUDE.md")
outside_agents_before=$(outside_l0_hash "$case_root/AGENTS.md")
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_script apply "$case_root" --no-interrupt
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$(managed_block_hash "$case_root/CLAUDE.md")" = "$(sha256_file "$KERNEL")" ] \
  && [ "$(managed_block_hash "$case_root/AGENTS.md")" = "$(sha256_file "$KERNEL")" ] \
  && [ "$outside_claude_before" = "$(outside_l0_hash "$case_root/CLAUDE.md")" ] \
  && [ "$outside_agents_before" = "$(outside_l0_hash "$case_root/AGENTS.md")" ]; then
  assert_changed it-s4-drift-replaced-outside-preserved "$RUN_STATUS" "$before" "$after"
else
  record_result it-s4-drift-replaced-outside-preserved "$RUN_STATUS" "$before" "$after" fail
fi

# B4. 单侧与乱序标记修复必须保留所有非标记行（it-s4-broken-markers / L0-P10）。
case_root="$TEST_ROOT/fx-l0-broken-markers"
mkdir -p "$case_root"
printf '# CLAUDE.md\n任意前置内容\n<!-- cadence-managed:openspec-superpowers-routing:v1:start -->\n无法判定归属的本地内容\n任意后置内容\n' > "$case_root/CLAUDE.md"
printf '# AGENTS.md\n任意前置内容\n<!-- cadence-managed:openspec-superpowers-routing:v1:end -->\n无法判定归属的本地内容\n<!-- cadence-managed:openspec-superpowers-routing:v1:start -->\n任意后置内容\n' > "$case_root/AGENTS.md"
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_script apply "$case_root" --no-interrupt
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$(grep -c 'cadence-managed:openspec-superpowers-routing:v1:start' "$case_root/CLAUDE.md")" -eq 1 ] \
  && [ "$(grep -c 'cadence-managed:openspec-superpowers-routing:v1:end' "$case_root/CLAUDE.md")" -eq 1 ] \
  && [ "$(grep -c 'cadence-managed:openspec-superpowers-routing:v1:start' "$case_root/AGENTS.md")" -eq 1 ] \
  && [ "$(grep -c 'cadence-managed:openspec-superpowers-routing:v1:end' "$case_root/AGENTS.md")" -eq 1 ] \
  && grep -q '任意前置内容' "$case_root/CLAUDE.md" \
  && grep -q '无法判定归属的本地内容' "$case_root/CLAUDE.md" \
  && grep -q '任意后置内容' "$case_root/CLAUDE.md" \
  && grep -q '任意前置内容' "$case_root/AGENTS.md" \
  && grep -q '无法判定归属的本地内容' "$case_root/AGENTS.md" \
  && grep -q '任意后置内容' "$case_root/AGENTS.md"; then
  assert_changed it-s4-broken-markers-preserve-arbitrary "$RUN_STATUS" "$before" "$after"
else
  record_result it-s4-broken-markers-preserve-arbitrary "$RUN_STATUS" "$before" "$after" fail
fi

# B5. 第一个 L0 备份成功、第二个实际失败时双入口都不得写入（it-s4-backup-barrier / L0-P4）。
# 故障注入：AGENTS.md 父目录设为只读复现第二个备份失败。
case_root="$(mk_entry_fixture fx-readonly-parent '漂移-CLAUDE' '漂移-AGENTS')"
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
saved_mode=$(stat -c %a "$case_root" 2>/dev/null || stat -f %Lp "$case_root")
chmod 555 "$case_root"
run_script apply "$case_root" --no-interrupt
inject_status=$RUN_STATUS
chmod "$saved_mode" "$case_root"
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
if [ "$inject_status" -ne 0 ] && [ "$before" = "$after" ]; then
  record_result it-s4-backup-barrier "$inject_status" "$before" "$after" pass
else
  record_result it-s4-backup-barrier "$inject_status" "$before" "$after" fail
fi

# B6. L1 漂移普通保留、no-interrupt 替换和备份失败保留（it-s3-l1-* / L1-02~07）。
case_root="$TEST_ROOT/fx-l1"
mkdir -p "$case_root/.claude/rules"
cp "$L1_SOURCE" "$case_root/.claude/rules/openspec-superpowers-workflow.md"
printf '\n本地漂移\n' >> "$case_root/.claude/rules/openspec-superpowers-workflow.md"
l1_target="$case_root/.claude/rules/openspec-superpowers-workflow.md"
before=$(sha256_file "$l1_target")
run_script apply "$case_root"
after=$(sha256_file "$l1_target")
# 评审裁决修正：与 it-decisions-missing 语义对齐——普通模式 apply 遇 L1 conflict
# 无 --decisions 必须 status≠0 且零写入（fail closed）。原期望 status=0 与权威用例矛盾。
if [ "$RUN_STATUS" -ne 0 ] && [ "$before" = "$after" ]; then
  record_result it-s3-l1-drift-normal "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s3-l1-drift-normal "$RUN_STATUS" "$before" "$after" fail
fi
# 备份失败：父目录只读
# 注意（评审 M3）：原实现用上一段的 $after（普通模式运行后状态）作为备份失败比对基准，
# 隐含「L1-02 普通模式零写入」假设。改为显式取故障注入运行前的目标 hash（before_fail）
# 作为独立比对基准，使断言语义自洽——不依赖普通模式是否真的零写入。
saved_mode=$(stat -c %a "$case_root/.claude/rules" 2>/dev/null || stat -f %Lp "$case_root/.claude/rules")
before_fail=$(sha256_file "$l1_target")
chmod 555 "$case_root/.claude/rules"
run_script apply "$case_root" --no-interrupt
l1_fail_status=$RUN_STATUS
chmod "$saved_mode" "$case_root/.claude/rules"
after_fail=$(sha256_file "$l1_target")
if [ "$l1_fail_status" -ne 0 ] && [ "$before_fail" = "$after_fail" ]; then
  record_result it-s3-l1-backup-failure-preserved "$l1_fail_status" "$before_fail" "$after_fail" pass
else
  record_result it-s3-l1-backup-failure-preserved "$l1_fail_status" "$before_fail" "$after_fail" fail
fi
# no-interrupt 替换成功
run_script apply "$case_root" --no-interrupt
after_replace=$(sha256_file "$l1_target")
if [ "$RUN_STATUS" -eq 0 ] && cmp -s "$l1_target" "$L1_SOURCE" && compgen -G "$l1_target.cadence-backup-*" >/dev/null; then
  assert_changed it-s3-l1-backed-up-and-replaced "$RUN_STATUS" "$after_fail" "$after_replace"
else
  record_result it-s3-l1-backed-up-and-replaced "$RUN_STATUS" "$after_fail" "$after_replace" fail
fi

# B7. 普通模式 openspec config 无冲突必须保留（it-s7-openspec-normal / OS 行）。
case_root="$TEST_ROOT/fx-openspec-existing"
mkdir -p "$case_root/openspec"
printf 'schema: spec-driven\nrules:\n  apply:\n    - invalid-artifact\n' > "$case_root/openspec/config.yaml"
before=$(sha256_file "$case_root/openspec/config.yaml")
run_script apply "$case_root"
after=$(sha256_file "$case_root/openspec/config.yaml")
assert_same it-s7-openspec-normal-preserved "$RUN_STATUS" "$before" "$after" 0

# B8. 不可解析 YAML 必须先备份后终止、原文件不变（it-s7-openspec-unparseable / OS-N9）。
case_root="$TEST_ROOT/fx-openspec-unparseable"
mkdir -p "$case_root/openspec"
printf 'schema: spec-driven\nrules: [\n' > "$case_root/openspec/config.yaml"
before=$(sha256_file "$case_root/openspec/config.yaml")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/openspec/config.yaml")
if [ "$RUN_STATUS" -ne 0 ] && [ "$before" = "$after" ] && compgen -G "$case_root/openspec/config.yaml.cadence-backup-*" >/dev/null; then
  record_result it-s7-openspec-invalid-yaml-backed-up-preserved "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s7-openspec-invalid-yaml-backed-up-preserved "$RUN_STATUS" "$before" "$after" fail
fi
# 类型冲突
printf 'schema: spec-driven\nrules:\n  proposal: invalid-string\n' > "$case_root/openspec/config.yaml"
before=$(sha256_file "$case_root/openspec/config.yaml")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/openspec/config.yaml")
if [ "$RUN_STATUS" -ne 0 ] && [ "$before" = "$after" ] && compgen -G "$case_root/openspec/config.yaml.cadence-backup-*" >/dev/null; then
  record_result it-s7-openspec-yaml-type-conflict-backed-up-preserved "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s7-openspec-yaml-type-conflict-backed-up-preserved "$RUN_STATUS" "$before" "$after" fail
fi

# B9. 成功合并必须保留 schema/context/额外规则，四 artifact 分组补齐，且第二次运行幂等（it-s7-openspec-merge / OS-02）。
case_root="$TEST_ROOT/fx-openspec-merge"
mkdir -p "$case_root/openspec"
printf 'schema: spec-driven\ncontext: |\n  custom-context\nx-project-metadata:\n  owner: custom-owner\nrules:\n  proposal:\n    - custom-proposal\n' > "$case_root/openspec/config.yaml"
before=$(sha256_file "$case_root/openspec/config.yaml")
run_script apply "$case_root" --no-interrupt
after_first=$(sha256_file "$case_root/openspec/config.yaml")
run_script apply "$case_root" --no-interrupt
after_second=$(sha256_file "$case_root/openspec/config.yaml")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$after_first" = "$after_second" ] \
  && assert_openspec_merged_fields "$case_root/openspec/config.yaml" 'custom-context' 'custom-proposal' 'x-project-metadata' 'custom-owner'; then
  assert_changed it-s7-openspec-merge-idempotent "$RUN_STATUS" "$before" "$after_first"
else
  record_result it-s7-openspec-merge-idempotent "$RUN_STATUS" "$before" "$after_second" fail
fi

# B10. no-interrupt rules.apply 必须备份后移除（it-s7-openspec-apply-remove / OS-N8）。
case_root="$TEST_ROOT/fx-openspec-apply-key"
mkdir -p "$case_root/openspec"
printf 'schema: spec-driven\nrules:\n  proposal:\n    - custom-proposal\n  apply:\n    - invalid-artifact\n' > "$case_root/openspec/config.yaml"
before=$(sha256_file "$case_root/openspec/config.yaml")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/openspec/config.yaml")
if [ "$RUN_STATUS" -eq 0 ] && ! grep -q '^  apply:' "$case_root/openspec/config.yaml" && grep -q 'custom-proposal' "$case_root/openspec/config.yaml" && compgen -G "$case_root/openspec/config.yaml.cadence-backup-*" >/dev/null; then
  assert_changed it-s7-openspec-apply-backed-up-removed "$RUN_STATUS" "$before" "$after"
else
  record_result it-s7-openspec-apply-backed-up-removed "$RUN_STATUS" "$before" "$after" fail
fi

# B11. 原子发布失败：目标目录只读复现，原文件不变（it-s7-openspec-publish-fail / OS-N13）。
case_root="$TEST_ROOT/fx-readonly-target"
mkdir -p "$case_root/openspec"
printf 'schema: spec-driven\ncontext: custom\n' > "$case_root/openspec/config.yaml"
before=$(sha256_file "$case_root/openspec/config.yaml")
saved_mode=$(stat -c %a "$case_root/openspec" 2>/dev/null || stat -f %Lp "$case_root/openspec")
chmod 555 "$case_root/openspec"
run_script apply "$case_root" --no-interrupt
inject_status=$RUN_STATUS
chmod "$saved_mode" "$case_root/openspec"
after=$(sha256_file "$case_root/openspec/config.yaml")
if [ "$inject_status" -ne 0 ] && [ "$before" = "$after" ]; then
  record_result it-s7-openspec-publish-failure-preserved "$inject_status" "$before" "$after" pass
else
  record_result it-s7-openspec-publish-failure-preserved "$inject_status" "$before" "$after" fail
fi

# ============================================================================
# C. 新增缺口用例 it-*
# ============================================================================

# C1. dry-run 零写入（it-dry-run-zero-write / XC-01）。
case_root="$TEST_ROOT/fx-empty-project"
mkdir -p "$case_root"
printf '# placeholder\n' > "$case_root/README.md"
before=$(tree_hash "$case_root")
run_script dry-run "$case_root" --no-interrupt
after=$(tree_hash "$case_root")
if [ "$RUN_STATUS" -eq 0 ] && [ "$before" = "$after" ] \
  && jqr "['steps']" >/dev/null 2>&1; then
  record_result it-dryrun-zero-write "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-dryrun-zero-write "$RUN_STATUS" "$before" "$after" fail
fi

# C2. decisions 四类异常（it-decisions-* / XC-03）：普通模式各自非零退出、零写入。
mk_drift_fixture() {
  local root="$TEST_ROOT/$1"
  mkdir -p "$root"
  cp "$REPO_ROOT/CLAUDE.md" "$root/CLAUDE.md"
  cp "$REPO_ROOT/AGENTS.md" "$root/AGENTS.md"
  replace_first_visible_paragraph "$root/CLAUDE.md" '漂移-CLAUDE'
  printf '%s\n' "$root"
}

# C2a. 决策文件缺失（有冲突却未提供 --decisions）
case_root="$(mk_drift_fixture fx-decisions-missing)"
before=$(tree_hash "$case_root")
run_script apply "$case_root"
after=$(tree_hash "$case_root")
if [ "$RUN_STATUS" -ne 0 ] && [ "$before" = "$after" ]; then
  record_result it-decisions-missing "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-decisions-missing "$RUN_STATUS" "$before" "$after" fail
fi

# C2b. 决策文件含未知 conflict_id
case_root="$(mk_drift_fixture fx-decisions-unknown)"
dec_file="$TEST_ROOT/decisions-unknown.json"
write_decisions "$dec_file" '[{"conflict_id":"s4:unknown:id","decision":"replace"}]'
before=$(tree_hash "$case_root")
run_script apply "$case_root" --decisions "$dec_file"
after=$(tree_hash "$case_root")
if [ "$RUN_STATUS" -ne 0 ] && [ "$before" = "$after" ]; then
  record_result it-decisions-unknown "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-decisions-unknown "$RUN_STATUS" "$before" "$after" fail
fi

# C2c. 冲突缺少决策（决策文件存在但漏掉该冲突）
case_root="$(mk_drift_fixture fx-decisions-lacking)"
dec_file="$TEST_ROOT/decisions-lacking.json"
write_decisions "$dec_file" '[]'
before=$(tree_hash "$case_root")
run_script apply "$case_root" --decisions "$dec_file"
after=$(tree_hash "$case_root")
if [ "$RUN_STATUS" -ne 0 ] && [ "$before" = "$after" ]; then
  record_result it-decisions-lacking "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-decisions-lacking "$RUN_STATUS" "$before" "$after" fail
fi

# C2d. 决策与新鲜计划不符（decision=keep-foreign-value 不在冲突允许集内 → 「过期」违规）
# 注：decisions 完整覆盖两个冲突（s4:CLAUDE.md 用非法 decision、s4:AGENTS.md 用合法 keep），
# 使唯一违规为 s4:CLAUDE.md 的「过期」，确保真正经 allowed_decisions 过期路径判定，
# 而非靠「缺失 s4:AGENTS.md」绕过。
case_root="$(mk_drift_fixture fx-decisions-stale)"
dec_file="$TEST_ROOT/decisions-stale.json"
write_decisions "$dec_file" '[{"conflict_id":"s4:CLAUDE.md","decision":"keep-foreign-value"},{"conflict_id":"s4:AGENTS.md","decision":"keep"}]'
before=$(tree_hash "$case_root")
run_script apply "$case_root" --decisions "$dec_file"
after=$(tree_hash "$case_root")
if [ "$RUN_STATUS" -ne 0 ] && [ "$before" = "$after" ]; then
  record_result it-decisions-stale "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-decisions-stale "$RUN_STATUS" "$before" "$after" fail
fi

# C2e. --report 指向项目根内 → 越权拒绝（it-usage-report-inside-root / XC + Plan L22）。
# Plan L22 全局约束：--report 与 --decisions 路径 MUST 在项目根外（脚本拒绝根内路径）。
# 断言退出码 2（usage）、fixture 零写入（不产生报告文件，因路径本身非法）。
# 注：run_script helper 硬编码 --report 为 /tmp 外部路径，无法覆盖测试；本用例直接调脚本。
case_root="$TEST_ROOT/fx-report-inside-root"
mkdir -p "$case_root"
printf '# placeholder\n' > "$case_root/README.md"
before=$(tree_hash "$case_root")
set +e
python3 "$SCRIPT" dry-run --project-root "$case_root" --report "$case_root/report.json" --no-interrupt >/dev/null 2>&1
report_status=$?
set -e
after=$(tree_hash "$case_root")
if [ "$report_status" -eq 2 ] && [ "$before" = "$after" ] && [ ! -f "$case_root/report.json" ]; then
  record_result it-usage-report-inside-root "$report_status" "$before" "$after" pass
else
  record_result it-usage-report-inside-root "$report_status" "$before" "$after" fail
fi

# C3. 历史目录两模式（it-s5-history-* / NH-01~03）。
# 构建 HISTORY_DIRS 清单内部分目录存在的 fixture（.claude/<dir> 形式）。
# 重要：fixture 必须预置与模板一致的 .claude/rules/（使 S3 幂等），否则 S3 创建 rules
# 会扰动 .claude 树，与「no-interrupt 不迁移历史」断言语义冲突（NH-02 比较 .claude 树）。
# 历史目录取清单内 3 个：prds / plans / docs（不在禁止迁移清单 rules/commands/skills）。
mk_history_fixture() {
  local root="$TEST_ROOT/$1"
  mkdir -p "$root/.claude/rules"
  cp "$REPO_ROOT/CLAUDE.md" "$root/CLAUDE.md"
  cp "$REPO_ROOT/AGENTS.md" "$root/AGENTS.md"
  # 预置与模板一致的规则文件，保证 S3 幂等（不创建新文件）
  cp "$TEST_DIR/../references/rules"/*.md "$root/.claude/rules/" 2>/dev/null || true
  cp "$TEST_DIR/../references/rules/README.md" "$root/.claude/rules/" 2>/dev/null || true
  # HISTORY_DIRS 清单内历史目录（3 个）：prds / plans / docs
  for d in prds plans docs; do
    mkdir -p "$root/.claude/$d"
    printf 'legacy-%s\n' "$d" > "$root/.claude/$d/file.md"
  done
  printf '%s\n' "$root"
}

# C3a. no-interrupt 只写报告不迁移（it-s5-history-no-interrupt / NH-02）
case_root="$(mk_history_fixture fx-history-dirs)"
before_claude=$(tree_hash "$case_root/.claude")
run_script apply "$case_root" --no-interrupt
after_claude=$(tree_hash "$case_root/.claude")
if [ "$RUN_STATUS" -eq 0 ] && [ "$before_claude" = "$after_claude" ]; then
  record_result it-s5-history-no-interrupt "$RUN_STATUS" "$before_claude" "$after_claude" pass
else
  record_result it-s5-history-no-interrupt "$RUN_STATUS" "$before_claude" "$after_claude" fail
fi

# C3b. 普通模式按 HM 表迁移（it-s5-history-normal / NH-03）
case_root="$(mk_history_fixture fx-history-dirs-normal)"
before_claude=$(tree_hash "$case_root/.claude")
run_script apply "$case_root"
after_claude=$(tree_hash "$case_root/.claude")
if [ "$RUN_STATUS" -eq 0 ] && [ "$before_claude" != "$after_claude" ]; then
  record_result it-s5-history-normal "$RUN_STATUS" "$before_claude" "$after_claude" pass
else
  record_result it-s5-history-normal "$RUN_STATUS" "$before_claude" "$after_claude" fail
fi

# C3b-2. HM-01 真实可达：普通模式下目标不存在的历史目录迁移后 action hm-01/moved、
# 源目录消失、目标含原内容（评审 I-1 修复验证：迁移前只 mkdir cadence 根使三分支可达）。
# 复用 C3b 的 fixture/REPORT：三个历史目录（prds/plans/docs）迁移前 cadence 下均不存在，
# 修复后必须落入 HM-01（整目录 mv），而修复前全部落入 HM-02（merged）。
hm01_status=$(python3 - "$case_root" "$REPORT" <<'PY' || printf '%s' 'fail')
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
report = json.load(open(sys.argv[2]))
steps = report.get("steps", [])
scaffold = next((s for s in steps if s.get("name") == "s5_scaffold"), {})
actions = scaffold.get("actions", [])
# 三个历史目录都必须标 hm-01/moved
expected = {"prds", "plans", "docs"}
hm01 = {
    a.get("to", "").split("/")[-1]
    for a in actions
    if a.get("branch") == "hm-01" and a.get("action") == "moved"
}
if expected - hm01:
    print("fail", file=sys.stderr)
    sys.exit(1)
# 源目录消失、目标含原内容
for d in expected:
    src = root / ".claude" / d
    dst = root / "cadence" / d
    if src.exists():
        sys.exit(1)
    if not dst.exists() or not (dst / "file.md").exists():
        sys.exit(1)
print("pass")
PY
record_result it-s5-history-hm01-reachable "$RUN_STATUS" hm-01 reachable "$([ "$hm01_status" = pass ] && printf pass || printf fail)"


# C3c. 历史目录仅检测并报告（it-s5-history-report-only / NH-01 报告字段）
case_root="$(mk_history_fixture fx-history-report)"
run_script dry-run "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] && jqr "['history_detected']" >/dev/null 2>&1; then
  record_result it-s5-history-report-only "$RUN_STATUS" present present pass
else
  record_result it-s5-history-report-only "$RUN_STATUS" present missing fail
fi

# C3d. 普通模式历史目标非空跳过（it-s5-history-conflict-skip / DF-03+HM-03）
# 用 HISTORY_DIRS 清单内目录（prds）+ 预置 rules 幂等 + cadence/prds 非空。
case_root="$TEST_ROOT/fx-history-target-nonempty"
mkdir -p "$case_root/.claude/rules"
# codex 终审 I2 适配：入口预收敛（全树零写入断言不被摘要/技术栈补齐扰动）
mk_converged_entries "$case_root"
cp "$TEST_DIR/../references/rules"/*.md "$case_root/.claude/rules/" 2>/dev/null || true
cp "$TEST_DIR/../references/rules/README.md" "$case_root/.claude/rules/" 2>/dev/null || true
mkdir -p "$case_root/.claude/prds" "$case_root/cadence/prds"
printf 'legacy\n' > "$case_root/.claude/prds/old.md"
printf 'existing\n' > "$case_root/cadence/prds/keep.md"
# 预置幂等的 openspec/config.yaml（merge_yaml 的安全输出点），
# 使 S7 merge 后字节不变，不干扰 S5 HM-03 的全树零写入断言。
mkdir -p "$case_root/openspec"
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('rc', '$SCRIPT')
rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
tpl = open('$CONFIG_TEMPLATE').read()
m, _ = rc.merge_yaml(tpl, '')
open('$case_root/openspec/config.yaml', 'w').write(m)
"
before=$(tree_hash "$case_root")
run_script apply "$case_root"
after=$(tree_hash "$case_root")
if [ "$RUN_STATUS" -eq 0 ] && [ "$before" = "$after" ]; then
  record_result it-s5-history-conflict-skip "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s5-history-conflict-skip "$RUN_STATUS" "$before" "$after" fail
fi

# C4. 普通规则已存在不覆盖（it-s3-normal-keep-decision / RF-02+DF-08）
case_root="$TEST_ROOT/fx-existing-rules"
mkdir -p "$case_root/.claude/rules"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
cp "$TEST_DIR/../references/rules/language.md" "$case_root/.claude/rules/language.md"
printf '\n# 用户自定义补充\n不覆盖我\n' >> "$case_root/.claude/rules/language.md"
before=$(sha256_file "$case_root/.claude/rules/language.md")
dec_file="$TEST_ROOT/decisions-keep.json"
write_decisions "$dec_file" '[{"conflict_id":"s3:.claude/rules/language.md","decision":"keep"}]'
run_script apply "$case_root" --decisions "$dec_file"
after=$(sha256_file "$case_root/.claude/rules/language.md")
assert_same it-s3-normal-keep-decision "$RUN_STATUS" "$before" "$after" 0

# C5. Markdown 不可解析回退（it-s3-markdown-unparseable-fallback / NC-08）
case_root="$TEST_ROOT/fx-markdown-unparseable"
mkdir -p "$case_root/.claude/rules"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
printf '\x00\x01binary garbage\n' > "$case_root/.claude/rules/language.md"
before=$(sha256_file "$case_root/.claude/rules/language.md")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/.claude/rules/language.md")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$before" != "$after" ] \
  && compgen -G "$case_root/.claude/rules/language.md.cadence-backup-*" >/dev/null \
  && grep -q '原项目补充' "$case_root/.claude/rules/language.md"; then
  record_result it-s3-markdown-unparseable-fallback "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s3-markdown-unparseable-fallback "$RUN_STATUS" "$before" "$after" fail
fi

# C6. L1 漂移替换与未知替换（it-l1-drift-replace / it-l1-unknown-replace / L1-04~06，no-interrupt）
# 注：upgrade 分支仅由 Task 2 单测参数注入覆盖（仓库仅存在 v1 规范源），本集成不覆盖。
case_root="$TEST_ROOT/fx-l1-v1-marker-drift"
mkdir -p "$case_root/.claude/rules"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
# v1 标记存在但内容不同（L1-05）
printf '<!-- cadence-framework-rule:openspec-superpowers-workflow:v1 -->\n# 被篡改的内容\n漂移正文\n' > "$case_root/.claude/rules/openspec-superpowers-workflow.md"
l1_target="$case_root/.claude/rules/openspec-superpowers-workflow.md"
before=$(sha256_file "$l1_target")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$l1_target")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$before" != "$after" ] \
  && cmp -s "$l1_target" "$L1_SOURCE" \
  && compgen -G "$l1_target.cadence-backup-*" >/dev/null; then
  record_result it-l1-drift-replace "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-l1-drift-replace "$RUN_STATUS" "$before" "$after" fail
fi

# 无标记文件（L1-06 unmarked → no-interrupt 备份后替换）
case_root="$TEST_ROOT/fx-l1-unmarked"
mkdir -p "$case_root/.claude/rules"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
printf '# 无标记的旧协作规则\n未知正文\n' > "$case_root/.claude/rules/openspec-superpowers-workflow.md"
l1_target="$case_root/.claude/rules/openspec-superpowers-workflow.md"
before=$(sha256_file "$l1_target")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$l1_target")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$before" != "$after" ] \
  && cmp -s "$l1_target" "$L1_SOURCE" \
  && compgen -G "$l1_target.cadence-backup-*" >/dev/null; then
  record_result it-l1-unknown-replace "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-l1-unknown-replace "$RUN_STATUS" "$before" "$after" fail
fi

# C7. 技术栈写入（it-s1-techstack-written / DF-02+S4-02）
case_root="$TEST_ROOT/fx-techstack-frontend"
mkdir -p "$case_root/application"
printf 'console.log("hi")\n' > "$case_root/application/app.ts"
cat > "$case_root/package.json" <<'JSON'
{
  "name": "demo",
  "scripts": { "test": "vitest", "lint": "eslint .", "format": "prettier --write ." }
}
JSON
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && grep -q 'pnpm' "$case_root/CLAUDE.md" \
  && grep -q '80%' "$case_root/CLAUDE.md" \
  && grep -q 'vitest' "$case_root/CLAUDE.md"; then
  record_result it-s1-techstack-written "$RUN_STATUS" present present pass
else
  record_result it-s1-techstack-written "$RUN_STATUS" present missing fail
fi

# C8. gitignore 两分支（it-s6-gitignore-* / S7-01+02+CG-07/08）
# C8a. 默认不加入 cadence/（it-s6-gitignore-default）
case_root="$TEST_ROOT/fx-empty-gitignore"
mkdir -p "$case_root"
printf 'node_modules/\n' > "$case_root/.gitignore"
before=$(sha256_file "$case_root/.gitignore")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/.gitignore")
if [ "$RUN_STATUS" -eq 0 ] && ! grep -q '^cadence/' "$case_root/.gitignore"; then
  record_result it-s6-gitignore-default "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s6-gitignore-default "$RUN_STATUS" "$before" "$after" fail
fi

# C8b. --ignore-cadence 追加 cadence/（it-s6-gitignore-ignore）
case_root="$TEST_ROOT/fx-gitignore-ignore"
mkdir -p "$case_root"
printf 'node_modules/\n' > "$case_root/.gitignore"
run_script apply "$case_root" --no-interrupt --ignore-cadence
if [ "$RUN_STATUS" -eq 0 ] && grep -q '^cadence/' "$case_root/.gitignore"; then
  record_result it-s6-gitignore-ignore "$RUN_STATUS" present present pass
else
  record_result it-s6-gitignore-ignore "$RUN_STATUS" present missing fail
fi

# C8c. .codegraph/ 加入 gitignore 且 codegraph.json 不加入（it-s6-gitignore-codegraph / S9-04）
case_root="$TEST_ROOT/fx-gitignore-codegraph"
mkdir -p "$case_root/application"
printf 'x = 1\n' > "$case_root/application/app.py"
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] && grep -q '^\.codegraph/' "$case_root/.gitignore" && ! grep -q 'codegraph\.json' "$case_root/.gitignore"; then
  record_result it-s6-gitignore-codegraph "$RUN_STATUS" present present pass
else
  record_result it-s6-gitignore-codegraph "$RUN_STATUS" present missing fail
fi

# C9. Playwright 两分支（it-s3-playwright-* / S10-01~03）
# C9a. 默认跳过（it-s3-playwright-skip）
case_root="$TEST_ROOT/fx-playwright-skip"
mkdir -p "$case_root"
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] && [ ! -f "$case_root/.claude/rules/playwright.md" ]; then
  record_result it-s3-playwright-skip "$RUN_STATUS" absent absent pass
else
  record_result it-s3-playwright-skip "$RUN_STATUS" absent present fail
fi

# C9b. --enable-playwright 创建规则（it-s3-playwright-enable）
case_root="$TEST_ROOT/fx-playwright-enable"
mkdir -p "$case_root"
run_script apply "$case_root" --no-interrupt --enable-playwright
if [ "$RUN_STATUS" -eq 0 ] && [ -f "$case_root/.claude/rules/playwright.md" ]; then
  record_result it-s3-playwright-enable "$RUN_STATUS" absent present pass
else
  record_result it-s3-playwright-enable "$RUN_STATUS" absent absent fail
fi

# C9c. 已存在不覆盖（it-s3-playwright-no-overwrite）
case_root="$TEST_ROOT/fx-playwright-existing"
mkdir -p "$case_root/.claude/rules"
printf '# 自定义 playwright 规则\n保留\n' > "$case_root/.claude/rules/playwright.md"
before=$(sha256_file "$case_root/.claude/rules/playwright.md")
run_script apply "$case_root" --no-interrupt --enable-playwright
after=$(sha256_file "$case_root/.claude/rules/playwright.md")
assert_same it-s3-playwright-no-overwrite "$RUN_STATUS" "$before" "$after" 0

# C10. CodeGraph 矩阵（it-s8-* / CS-01~08、CG-01~08），用 fake_codegraph 覆盖 PATH。
# 简报明文要求（line 43）：it-s8-* 用 fake_codegraph 覆盖 install_rc/init_rc/status_rc=1，
# 且 PATH 前置 fake bin。此处每个 C10 用例均：① 调 fake_codegraph 生成对应退出码的 bin；
# ② 通过 RC_FAKE_PATH 将该 bin 目录前置注入 run_script 子进程 PATH。
mk_coding_fixture() {
  local root="$TEST_ROOT/$1"
  mkdir -p "$root/application"
  printf 'def main():\n    pass\n' > "$root/application/app.py"
  printf '%s\n' "$root"
}

# C10a. install_rc=1 仍补双配置 degraded（it-s8-codegraph-install-fail / CS-07）
case_root="$(mk_coding_fixture fx-codegraph-install-fail)"
fake_bin="$TEST_ROOT/fake-bin-install-fail"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 1 0 0 0
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/.mcp.json" ] \
  && [ -f "$case_root/.codex/config.toml" ] \
  && jqr "['overall']" 2>/dev/null | grep -qi 'degraded'; then
  record_result it-s8-codegraph-install-fail "$RUN_STATUS" present present pass
else
  record_result it-s8-codegraph-install-fail "$RUN_STATUS" present missing fail
fi

# C10b. init_rc=1 degraded（it-s8-codegraph-init-fail / CS-08）
case_root="$(mk_coding_fixture fx-codegraph-init-fail)"
fake_bin="$TEST_ROOT/fake-bin-init-fail"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 0 1 0 0
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] && jqr "['overall']" 2>/dev/null | grep -qi 'degraded'; then
  record_result it-s8-codegraph-init-fail "$RUN_STATUS" present present pass
else
  record_result it-s8-codegraph-init-fail "$RUN_STATUS" present missing fail
fi

# C10c. status_rc=1 degraded（it-s8-codegraph-status-fail）
case_root="$TEST_ROOT/fx-codegraph-existing-status"
mkdir -p "$case_root/.codegraph" "$case_root/application"
printf 'x=1\n' > "$case_root/application/app.py"
fake_bin="$TEST_ROOT/fake-bin-status-fail"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 0 0 1 1
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] && jqr "['overall']" 2>/dev/null | grep -qi 'degraded'; then
  record_result it-s8-codegraph-status-fail "$RUN_STATUS" present present pass
else
  record_result it-s8-codegraph-status-fail "$RUN_STATUS" present missing fail
fi

# C10d. .codegraph/ 已存在只 status 不重复 init（it-s8-codegraph-existing / CS-02）
case_root="$TEST_ROOT/fx-codegraph-existing"
mkdir -p "$case_root/.codegraph" "$case_root/application"
printf 'x=1\n' > "$case_root/application/app.py"
before=$(sha256_file "$case_root/.codegraph" 2>/dev/null || printf 'dir')
fake_bin="$TEST_ROOT/fake-bin-existing"
mkdir -p "$fake_bin"
# .codegraph 已存在 → 脚本只调 status；status_rc=0 → overall=ok（与 C10c status_rc=1 degraded 区分）
fake_codegraph "$fake_bin" 0 0 0 1
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] && jqr "['overall']" 2>/dev/null | grep -qix 'ok'; then
  record_result it-s8-codegraph-existing "$RUN_STATUS" present present pass
else
  record_result it-s8-codegraph-existing "$RUN_STATUS" present missing fail
fi

# C10e. write_config=0 时脚本补双方配置（it-s8-codegraph-write-config-zero）
case_root="$(mk_coding_fixture fx-codegraph-write-zero)"
fake_bin="$TEST_ROOT/fake-bin-write-zero"
mkdir -p "$fake_bin"
# fake codegraph install 成功但不写配置（write_config=0）→ 脚本应自行补齐双配置
fake_codegraph "$fake_bin" 0 0 0 0
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/.mcp.json" ] \
  && [ -f "$case_root/.codex/config.toml" ]; then
  record_result it-s8-codegraph-write-config-zero "$RUN_STATUS" absent present pass
else
  record_result it-s8-codegraph-write-config-zero "$RUN_STATUS" absent absent fail
fi

# C10f. 非 Coding + --enable-codegraph 仍执行 S8（it-s8-codegraph-explicit-enable / S9-02）
case_root="$TEST_ROOT/fx-noncoding-enable-codegraph"
mkdir -p "$case_root"
printf 'docs only\n' > "$case_root/README.md"
fake_bin="$TEST_ROOT/fake-bin-explicit-enable"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 0 0 0 1
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt --enable-codegraph
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/.mcp.json" ] \
  && [ -f "$case_root/.codex/config.toml" ]; then
  record_result it-s8-codegraph-explicit-enable "$RUN_STATUS" absent present pass
else
  record_result it-s8-codegraph-explicit-enable "$RUN_STATUS" absent absent fail
fi

# C11. s1 项目类型冲突（it-s1-conflict-noncoding-default / IA-02）
# 检测矛盾（源码检出 coding 与用户声明 non-coding 冲突）→ no-interrupt 按 non-coding 决策。
# 修复（Task 11）：原 fixture 仅有 application/app.py + docs/，不构成矛盾（有源码即应判 coding）；
# 补 --project-type non-coding 作为非 coding 标识，使 fixture 真正触发 s1:project-type-conflict。
case_root="$TEST_ROOT/fx-contradict-detection"
mkdir -p "$case_root/application" "$case_root/docs"
printf 'x=1\n' > "$case_root/application/app.py"
run_script apply "$case_root" --no-interrupt --project-type non-coding
if [ "$RUN_STATUS" -eq 0 ] && jqr "['project_type']" 2>/dev/null | grep -qi 'non-coding' \
  && jqr "['conflicts']" 2>/dev/null | grep -q 's1:project-type-conflict'; then
  record_result it-s1-conflict-noncoding-default "$RUN_STATUS" present present pass
else
  record_result it-s1-conflict-noncoding-default "$RUN_STATUS" present missing fail
fi

# C12. 用户意图四参数透传（it-intent-params / XC-02）
case_root="$TEST_ROOT/fx-intent-params"
mkdir -p "$case_root"
run_script apply "$case_root" --no-interrupt --project-type non-coding --ignore-cadence --enable-playwright --enable-codegraph
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/.claude/rules/playwright.md" ] \
  && grep -q '^cadence/' "$case_root/.gitignore"; then
  record_result it-intent-params "$RUN_STATUS" present present pass
else
  record_result it-intent-params "$RUN_STATUS" present missing fail
fi

# C13. 摘要编号冲突保留原文+追加缺失（it-entry-summary-number-conflict / SM-03）
case_root="$TEST_ROOT/fx-summary-number-conflict"
mkdir -p "$case_root"
# 构造 CLAUDE.md：有强制规则区但编号已被用户占用
cat > "$case_root/CLAUDE.md" <<'MD'
# CLAUDE.md

## 强制规则

1. 用户自定义第一条
2. 用户自定义第二条
8. 用户占用的编号
MD
printf '# AGENTS.md\n\n## 强制规则\n\n1. 自定义\n' > "$case_root/AGENTS.md"
before=$(sha256_file "$case_root/CLAUDE.md")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/CLAUDE.md")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$before" != "$after" ] \
  && grep -q '用户自定义第一条' "$case_root/CLAUDE.md" \
  && grep -q '必须使用中文回答' "$case_root/CLAUDE.md"; then
  record_result it-entry-summary-number-conflict "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-entry-summary-number-conflict "$RUN_STATUS" "$before" "$after" fail
fi

# C14. 基础入口创建（it-entry-base-created / L0-P5+L0-01）
case_root="$TEST_ROOT/fx-entry-base-created"
mkdir -p "$case_root"
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/CLAUDE.md" ] \
  && [ -f "$case_root/AGENTS.md" ] \
  && grep -q 'cadence-managed:openspec-superpowers-routing:v1:start' "$case_root/CLAUDE.md" \
  && grep -q '强制规则' "$case_root/CLAUDE.md"; then
  record_result it-entry-base-created "$RUN_STATUS" absent present pass
else
  record_result it-entry-base-created "$RUN_STATUS" absent absent fail
fi

# C15. 预算断言（it-budget / XC-05）：空项目 apply --no-interrupt budget < 60
case_root="$TEST_ROOT/fx-budget"
mkdir -p "$case_root"
printf 'print("hi")\n' > "$case_root/app.py"
run_script apply "$case_root" --no-interrupt
budget_val=$(jqr "['budget_seconds_excluding_codegraph']" 2>/dev/null || printf '%s' 'none')
# codegraph 步骤必须含独立 elapsed_ms
# 注意：不可复用 jqr（其模板 json.load(open('$REPORT'))$1 把 $1 直接拼在 json.load(...) 后，
# next(...) 会拼成 json.load(...)next(...) 导致 SyntaxError，cg_elapsed 永远兜底为 'none'
# 使 S8 独立 elapsed_ms 断言永久失效）。改用独立 python3 -c 表达式。
cg_elapsed=$(python3 -c "import json;d=json.load(open('$REPORT'));print(next((s.get('elapsed_ms') for s in d.get('steps',[]) if s.get('name')=='s8_codegraph'),'none'))" 2>/dev/null || printf '%s' 'none')
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$budget_val" != 'none' ] \
  && [ "$budget_val" != 'None' ] \
  && python3 -c "import sys; sys.exit(0 if float(sys.argv[1]) < 60 else 1)" "$budget_val" 2>/dev/null \
  && [ "$cg_elapsed" != 'none' ]; then
  record_result it-budget "$RUN_STATUS" "$budget_val" '<60' pass
else
  record_result it-budget "$RUN_STATUS" "$budget_val" '<60' fail
fi

# ============================================================================
# C16. 终审修复回归（C-1/C-2/I-2/I-4 集成证据 + I-3 缺口补齐）
# ============================================================================

# C16a. L0 insert 两模式确定性：普通模式无 decisions 直接插入（it-s4-insert / L0-05 + 终审 I-2）。
# 修复前：insert 被冲突化，普通模式 keep 决策 → L0 永不插入。
case_root="$TEST_ROOT/fx-entry-no-markers"
mkdir -p "$case_root"
printf '# CLAUDE.md\n\n我的项目说明，无 L0 标记。\n\n## 强制规则\n\n1. 用户规则\n' > "$case_root/CLAUDE.md"
printf '# AGENTS.md\n\n自定义 agents 内容。\n' > "$case_root/AGENTS.md"
run_script apply "$case_root"
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$(grep -c 'cadence-managed:openspec-superpowers-routing:v1:start' "$case_root/CLAUDE.md")" -eq 1 ] \
  && [ "$(grep -c 'cadence-managed:openspec-superpowers-routing:v1:start' "$case_root/AGENTS.md")" -eq 1 ] \
  && grep -q '我的项目说明' "$case_root/CLAUDE.md" \
  && grep -q '自定义 agents 内容' "$case_root/AGENTS.md"; then
  record_result it-s4-insert "$RUN_STATUS" absent present pass
else
  record_result it-s4-insert "$RUN_STATUS" absent absent fail
fi

# C16b. L0 upgrade 两模式确定性：普通模式无 decisions 备份后升级（it-s4-upgrade / L0-04 + 终审 I-2）。
case_root="$TEST_ROOT/fx-entry-v0-markers"
mkdir -p "$case_root"
printf '# CLAUDE.md\n\n前置\n\n<!-- cadence-managed:openspec-superpowers-routing:v0:start -->\n旧版\n<!-- cadence-managed:openspec-superpowers-routing:v0:end -->\n\n后置\n' > "$case_root/CLAUDE.md"
printf '# AGENTS.md\n\n<!-- cadence-managed:openspec-superpowers-routing:v0:start -->\n旧\n<!-- cadence-managed:openspec-superpowers-routing:v0:end -->\n' > "$case_root/AGENTS.md"
run_script apply "$case_root"
if [ "$RUN_STATUS" -eq 0 ] \
  && compgen -G "$case_root/CLAUDE.md.cadence-backup-*" >/dev/null \
  && compgen -G "$case_root/AGENTS.md.cadence-backup-*" >/dev/null \
  && [ "$(managed_block_hash "$case_root/CLAUDE.md")" = "$(sha256_file "$KERNEL")" ] \
  && ! grep -q 'routing:v0' "$case_root/CLAUDE.md" \
  && grep -q '后置' "$case_root/CLAUDE.md"; then
  record_result it-s4-upgrade "$RUN_STATUS" v0 v1 pass
else
  record_result it-s4-upgrade "$RUN_STATUS" v0 v0 fail
fi

# C16c. codegraph 二进制缺失 → install 失败降级路径（it-s8-codegraph-binary-missing / CS-07 + 终审 C-2）。
# PATH 换为全空目录（python3 以绝对路径调用），subprocess 必抛 FileNotFoundError。
case_root="$(mk_coding_fixture fx-codegraph-binary-missing)"
empty_bin="$TEST_ROOT/empty-bin"
mkdir -p "$empty_bin"
REPORT="$(mktemp /tmp/rule-config-report.XXXXXX)"
set +e
PATH="$empty_bin" "$(command -v python3)" "$SCRIPT" apply --project-root "$case_root" --report "$REPORT" --no-interrupt >/dev/null 2>&1
RUN_STATUS=$?
set -e
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/.mcp.json" ] \
  && [ -f "$case_root/.codex/config.toml" ] \
  && jqr "['overall']" 2>/dev/null | grep -qi 'degraded'; then
  record_result it-s8-codegraph-binary-missing "$RUN_STATUS" present present pass
else
  record_result it-s8-codegraph-binary-missing "$RUN_STATUS" present missing fail
fi

# C16d. 失败报告 schema（it-apply-failure-report-fields / NR-05 + 终审 I-4）：
# overall 收敛 ok/degraded/fail 三值（不得为 crashed）；failure.file 填实际失败文件。
case_root="$TEST_ROOT/fx-failure-report-fields"
mkdir -p "$case_root/openspec"
printf 'schema: spec-driven\nrules: [\n' > "$case_root/openspec/config.yaml"
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -ne 0 ] && python3 - "$REPORT" <<'PY'
import json
import sys

d = json.load(open(sys.argv[1]))
assert d.get("overall") in ("ok", "degraded", "fail"), "overall 必须收敛三值"
assert d.get("overall") == "fail", "执行异常落 fail（非 crashed）"
f = d.get("failure") or {}
assert f.get("file") == "openspec/config.yaml", f"failure.file 应为实际失败文件: {f.get('file')}"
assert f.get("reason"), "failure.reason 必填"
assert f.get("recovery"), "failure.recovery 必填"
assert d.get("backups"), "已完成项目（backups）必须逐项列出"
PY
then
  record_result it-apply-failure-report-fields "$RUN_STATUS" present present pass
else
  record_result it-apply-failure-report-fields "$RUN_STATUS" present missing fail
fi

# C16e. 模板全缺 → fail closed 非零退出、目标项目零写入（it-s2-templates-missing / §11.5 S1b-04）。
# HOME 换为空目录使在线/离线/glob 回退候选全部不完整。
case_root="$TEST_ROOT/fx-templates-missing"
mkdir -p "$case_root"
printf '# placeholder\n' > "$case_root/README.md"
fake_home="$TEST_ROOT/fake-home-empty"
mkdir -p "$fake_home"
before=$(tree_hash "$case_root")
REPORT="$(mktemp /tmp/rule-config-report.XXXXXX)"
set +e
HOME="$fake_home" "$(command -v python3)" "$SCRIPT" apply --project-root "$case_root" --report "$REPORT" --no-interrupt >/dev/null 2>&1
RUN_STATUS=$?
set -e
after=$(tree_hash "$case_root")
if [ "$RUN_STATUS" -ne 0 ] && [ "$before" = "$after" ] \
  && jqr "['overall']" 2>/dev/null | grep -qix 'fail'; then
  record_result it-s2-templates-missing "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s2-templates-missing "$RUN_STATUS" "$before" "$after" fail
fi

# C16f. 空项目创建全套（it-s3-create / NC-01；it-s3-rules-create / RF-01；
# it-s3-code-reading-backfill / RF-03+OP-02；it-s3-l1-create / L1-01；it-s3-l1-idempotent / L1-02）。
case_root="$TEST_ROOT/fx-empty-create-all"
mkdir -p "$case_root"
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] && [ -f "$case_root/.claude/rules/language.md" ] \
  && cmp -s "$case_root/.claude/rules/language.md" "$TEST_DIR/../references/rules/language.md"; then
  record_result it-s3-create "$RUN_STATUS" absent present pass
else
  record_result it-s3-create "$RUN_STATUS" absent missing fail
fi
rules_all_present=1
for f in agent-routing-kernel.md language.md document-storage.md markdown-format.md \
         mcp-servers.md code-reading.md code-usage-coding.md code-usage-noncoding.md; do
  [ -f "$case_root/.claude/rules/$f" ] || rules_all_present=0
done
if [ "$RUN_STATUS" -eq 0 ] && [ "$rules_all_present" -eq 1 ]; then
  record_result it-s3-rules-create "$RUN_STATUS" absent present pass
else
  record_result it-s3-rules-create "$RUN_STATUS" absent missing fail
fi
if [ "$RUN_STATUS" -eq 0 ] && [ -f "$case_root/.claude/rules/code-reading.md" ] \
  && cmp -s "$case_root/.claude/rules/code-reading.md" "$TEST_DIR/../references/rules/code-reading.md"; then
  record_result it-s3-code-reading-backfill "$RUN_STATUS" absent present pass
else
  record_result it-s3-code-reading-backfill "$RUN_STATUS" absent missing fail
fi
if [ "$RUN_STATUS" -eq 0 ] && cmp -s "$case_root/.claude/rules/openspec-superpowers-workflow.md" "$L1_SOURCE"; then
  record_result it-s3-l1-create "$RUN_STATUS" absent present pass
else
  record_result it-s3-l1-create "$RUN_STATUS" absent missing fail
fi
l1_target="$case_root/.claude/rules/openspec-superpowers-workflow.md"
before=$(sha256_file "$l1_target")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$l1_target")
assert_same it-s3-l1-idempotent "$RUN_STATUS" "$before" "$after" 0

# C16g. openspec/config.yaml 不存在 → 从模板原子创建（it-s7-openspec-create / OS-01）。
case_root="$TEST_ROOT/fx-openspec-create"
mkdir -p "$case_root"
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] && [ -f "$case_root/openspec/config.yaml" ] \
  && assert_openspec_merged_fields "$case_root/openspec/config.yaml" 'spec-driven'; then
  record_result it-s7-openspec-create "$RUN_STATUS" absent present pass
else
  record_result it-s7-openspec-create "$RUN_STATUS" absent missing fail
fi

# C16h. codegraph 全新初始化（it-s8-codegraph-fresh / CS-01+CG-03）。
case_root="$(mk_coding_fixture fx-codegraph-fresh)"
fake_bin="$TEST_ROOT/fake-bin-fresh"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 0 0 0 1
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -d "$case_root/.codegraph" ] \
  && [ -f "$case_root/.mcp.json" ] \
  && [ -f "$case_root/.codex/config.toml" ] \
  && jqr "['overall']" 2>/dev/null | grep -qix 'ok'; then
  record_result it-s8-codegraph-fresh "$RUN_STATUS" absent present pass
else
  record_result it-s8-codegraph-fresh "$RUN_STATUS" absent missing fail
fi

# C16i. 双配置已齐全 → 跳过不重复写入（it-s8-codegraph-both-present / CS-03+CG-04）。
case_root="$TEST_ROOT/fx-codegraph-both-present"
mkdir -p "$case_root/.codegraph" "$case_root/.codex" "$case_root/application"
printf 'x=1\n' > "$case_root/application/app.py"
printf '{ "mcpServers": { "codegraph": { "command": "codegraph", "args": ["mcp"] } } }\n' > "$case_root/.mcp.json"
printf '[mcp_servers.codegraph]\ncommand = "codegraph"\nargs = ["mcp"]\n' > "$case_root/.codex/config.toml"
before=$(sha256_pair "$case_root/.mcp.json" "$case_root/.codex/config.toml")
fake_bin="$TEST_ROOT/fake-bin-both-present"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 0 0 0 1
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
after=$(sha256_pair "$case_root/.mcp.json" "$case_root/.codex/config.toml")
if [ "$RUN_STATUS" -eq 0 ] && [ "$before" = "$after" ] \
  && jqr "['overall']" 2>/dev/null | grep -qix 'ok'; then
  record_result it-s8-codegraph-both-present "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s8-codegraph-both-present "$RUN_STATUS" "$before" "$after" fail
fi

# C16j. .mcp.json 有、.codex/config.toml 缺 → 仅补 toml，.mcp.json 不动
# （it-s8-codegraph-toml-missing / CS-04+CG-05）。
case_root="$(mk_coding_fixture fx-codegraph-toml-missing)"
printf '{ "mcpServers": { "codegraph": { "command": "codegraph", "args": ["mcp"] }, "other": { "command": "other" } } }\n' > "$case_root/.mcp.json"
before=$(sha256_file "$case_root/.mcp.json")
fake_bin="$TEST_ROOT/fake-bin-toml-missing"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 0 0 0 0
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/.mcp.json")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/.codex/config.toml" ] \
  && grep -q '\[mcp_servers.codegraph\]' "$case_root/.codex/config.toml" \
  && [ "$before" = "$after" ]; then
  record_result it-s8-codegraph-toml-missing "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s8-codegraph-toml-missing "$RUN_STATUS" "$before" "$after" fail
fi

# C16k. .mcp.json 缺 → 兜底 JSON 合并补齐，.codex/config.toml 不动
# （it-s8-codegraph-mcp-missing / CS-05）。
case_root="$(mk_coding_fixture fx-codegraph-mcp-missing)"
mkdir -p "$case_root/.codex"
printf '[mcp_servers.codegraph]\ncommand = "codegraph"\nargs = ["mcp"]\n' > "$case_root/.codex/config.toml"
before=$(sha256_file "$case_root/.codex/config.toml")
fake_bin="$TEST_ROOT/fake-bin-mcp-missing"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 0 0 0 0
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/.codex/config.toml")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/.mcp.json" ] \
  && python3 -c "import json;d=json.load(open('$case_root/.mcp.json'));assert 'codegraph' in d['mcpServers']" \
  && [ "$before" = "$after" ]; then
  record_result it-s8-codegraph-mcp-missing "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s8-codegraph-mcp-missing "$RUN_STATUS" "$before" "$after" fail
fi

# C16l. install 后二次核验、只补缺失方（it-s8-codegraph-install-reverify / CS-06+CG-06）。
# .mcp.json 含 codegraph + 其他 server；install 成功（不写配置）→ 仅新建 toml，.mcp.json 逐字不变。
case_root="$(mk_coding_fixture fx-codegraph-install-reverify)"
printf '{ "mcpServers": { "codegraph": { "command": "codegraph", "args": ["mcp"] }, "keep-me": { "command": "keep" } } }\n' > "$case_root/.mcp.json"
before=$(sha256_file "$case_root/.mcp.json")
fake_bin="$TEST_ROOT/fake-bin-install-reverify"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 0 0 0 0
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/.mcp.json")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$before" = "$after" ] \
  && [ -f "$case_root/.codex/config.toml" ] \
  && grep -q '\[mcp_servers.codegraph\]' "$case_root/.codex/config.toml"; then
  record_result it-s8-codegraph-install-reverify "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s8-codegraph-install-reverify "$RUN_STATUS" "$before" "$after" fail
fi

# C16m. 老项目补齐 CodeGraph（it-s8-codegraph-backfill / CG-01）：
# 已跑过 rule-config（入口/规则/openspec 均幂等）但无 codegraph 配置 → 只补 codegraph 相关项，
# 入口、规则、openspec 配置 sha256 不变。
case_root="$TEST_ROOT/fx-codegraph-backfill"
mkdir -p "$case_root/.claude/rules" "$case_root/openspec" "$case_root/application"
printf 'x=1\n' > "$case_root/application/app.py"
# codex 终审 I2 适配：入口预收敛（coding 收敛态，避免 S4 upgrade 扰动「其余文件 sha256 不变」断言）
mk_converged_entries "$case_root" coding
cp "$TEST_DIR/../references/rules"/*.md "$case_root/.claude/rules/" 2>/dev/null || true
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('rc', '$SCRIPT')
rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
tpl = open('$CONFIG_TEMPLATE').read()
m, _ = rc.merge_yaml(tpl, '')
open('$case_root/openspec/config.yaml', 'w').write(m)
"
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
before_cfg=$(sha256_file "$case_root/openspec/config.yaml")
before_rules=$(sha256_file "$case_root/.claude/rules/language.md")
fake_bin="$TEST_ROOT/fake-bin-backfill"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 0 0 0 0
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/.mcp.json" ] \
  && [ -f "$case_root/.codex/config.toml" ] \
  && grep -q '^\.codegraph/' "$case_root/.gitignore" \
  && [ "$before" = "$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")" ] \
  && [ "$before_cfg" = "$(sha256_file "$case_root/openspec/config.yaml")" ] \
  && [ "$before_rules" = "$(sha256_file "$case_root/.claude/rules/language.md")" ]; then
  record_result it-s8-codegraph-backfill "$RUN_STATUS" present present pass
else
  record_result it-s8-codegraph-backfill "$RUN_STATUS" present missing fail
fi

# C16n. HM-02：cadence/<dir> 已存在且为空 → 内容移入 + 清理空源目录（it-s5-history-merge-empty）。
case_root="$TEST_ROOT/fx-history-merge-empty"
mkdir -p "$case_root/.claude/rules" "$case_root/.claude/plans" "$case_root/cadence/plans" "$case_root/openspec"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
cp "$TEST_DIR/../references/rules"/*.md "$case_root/.claude/rules/" 2>/dev/null || true
printf 'legacy-plan\n' > "$case_root/.claude/plans/old.md"
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('rc', '$SCRIPT')
rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
tpl = open('$CONFIG_TEMPLATE').read()
m, _ = rc.merge_yaml(tpl, '')
open('$case_root/openspec/config.yaml', 'w').write(m)
"
run_script apply "$case_root"
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/cadence/plans/old.md" ] \
  && grep -q 'legacy-plan' "$case_root/cadence/plans/old.md" \
  && [ ! -e "$case_root/.claude/plans" ]; then
  record_result it-s5-history-merge-empty "$RUN_STATUS" present moved pass
else
  record_result it-s5-history-merge-empty "$RUN_STATUS" present present fail
fi

# C16o. 禁止迁移 rules/commands/skills（it-s5-history-forbidden / S6-01）。
case_root="$TEST_ROOT/fx-history-forbidden"
mkdir -p "$case_root/.claude/rules" "$case_root/.claude/commands" "$case_root/.claude/skills" "$case_root/openspec"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
cp "$TEST_DIR/../references/rules"/*.md "$case_root/.claude/rules/" 2>/dev/null || true
printf 'user-command\n' > "$case_root/.claude/commands/custom.md"
printf 'user-skill\n' > "$case_root/.claude/skills/custom.md"
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('rc', '$SCRIPT')
rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
tpl = open('$CONFIG_TEMPLATE').read()
m, _ = rc.merge_yaml(tpl, '')
open('$case_root/openspec/config.yaml', 'w').write(m)
"
before=$(sha256_pair "$case_root/.claude/commands/custom.md" "$case_root/.claude/skills/custom.md")
run_script apply "$case_root"
after=$(sha256_pair "$case_root/.claude/commands/custom.md" "$case_root/.claude/skills/custom.md")
if [ "$RUN_STATUS" -eq 0 ] && [ "$before" = "$after" ] \
  && [ ! -e "$case_root/cadence/commands" ] && [ ! -e "$case_root/cadence/skills" ]; then
  record_result it-s5-history-forbidden "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s5-history-forbidden "$RUN_STATUS" "$before" "$after" fail
fi

# C16p. .codegraph/ gitignore 幂等（it-s6-gitignore-codegraph-idempotent / CG-07）。
case_root="$(mk_coding_fixture fx-gitignore-codegraph-idempotent)"
run_script apply "$case_root" --no-interrupt
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$(grep -c '^\.codegraph/' "$case_root/.gitignore")" -eq 1 ]; then
  record_result it-s6-gitignore-codegraph-idempotent "$RUN_STATUS" once once pass
else
  record_result it-s6-gitignore-codegraph-idempotent "$RUN_STATUS" once duplicated fail
fi

# C16q. codegraph.json 保留且不入 gitignore（it-s6-codegraph-json-keep / CG-08）。
case_root="$(mk_coding_fixture fx-codegraph-json-keep)"
printf '{ "index": true }\n' > "$case_root/codegraph.json"
before=$(sha256_file "$case_root/codegraph.json")
run_script apply "$case_root" --no-interrupt
after=$(sha256_file "$case_root/codegraph.json")
if [ "$RUN_STATUS" -eq 0 ] && [ "$before" = "$after" ] \
  && ! grep -q 'codegraph\.json' "$case_root/.gitignore"; then
  record_result it-s6-codegraph-json-keep "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-s6-codegraph-json-keep "$RUN_STATUS" "$before" "$after" fail
fi

# C16r. openspec 必要备份失败 → 终止零写入（it-s7-openspec-backup-fail-modes / OS-08 + OS-N4）。
case_root="$TEST_ROOT/fx-openspec-backup-fail"
mkdir -p "$case_root/openspec"
printf 'schema: spec-driven\nrules:\n  apply:\n    - invalid-artifact\n' > "$case_root/openspec/config.yaml"
before=$(sha256_file "$case_root/openspec/config.yaml")
saved_mode=$(stat -c %a "$case_root/openspec" 2>/dev/null || stat -f %Lp "$case_root/openspec")
chmod 555 "$case_root/openspec"
run_script apply "$case_root" --no-interrupt
inject_status=$RUN_STATUS
chmod "$saved_mode" "$case_root/openspec"
after=$(sha256_file "$case_root/openspec/config.yaml")
if [ "$inject_status" -ne 0 ] && [ "$before" = "$after" ] \
  && [ ! -f "$case_root/CLAUDE.md" ] \
  && jqr "['overall']" 2>/dev/null | grep -qix 'fail'; then
  record_result it-s7-openspec-backup-fail-modes "$inject_status" "$before" "$after" pass
else
  record_result it-s7-openspec-backup-fail-modes "$inject_status" "$before" "$after" fail
fi

# ============================================================================
# C17. codex 终审修复回归（C2/I1/I2/I3/I4/I5 集成证据）
# ============================================================================

# C17a. 无效 .mcp.json 重写前备份（it-s8-mcpjson-invalid-backed-up / codex 终审 C2）。
case_root="$(mk_coding_fixture fx-mcpjson-invalid)"
printf '{invalid json\n' > "$case_root/.mcp.json"
fake_bin="$TEST_ROOT/fake-bin-mcpjson-invalid"
mkdir -p "$fake_bin"
# install 失败 → degraded 路径仍补齐双配置；既有无效 .mcp.json 重写前必须备份
fake_codegraph "$fake_bin" 1 0 0 0
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && jqr "['overall']" 2>/dev/null | grep -qi 'degraded' \
  && compgen -G "$case_root/.mcp.json.cadence-backup-*" >/dev/null \
  && grep -q 'invalid json' "$case_root"/.mcp.json.cadence-backup-* \
  && python3 -c "import json;d=json.load(open('$case_root/.mcp.json'));assert 'codegraph' in d['mcpServers']"; then
  record_result it-s8-mcpjson-invalid-backed-up "$RUN_STATUS" invalid backed-up pass
else
  record_result it-s8-mcpjson-invalid-backed-up "$RUN_STATUS" invalid missing fail
fi

# C17b. .codegraph/ 已存在 + 缺 .codex/config.toml → 补齐（it-s8-codegraph-existing-mcp-backfill / codex 终审 I1 + CS-04/CG-05）。
case_root="$TEST_ROOT/fx-codegraph-existing-mcp-backfill"
mkdir -p "$case_root/.codegraph" "$case_root/application"
printf 'x=1\n' > "$case_root/application/app.py"
printf '{ "mcpServers": { "codegraph": { "command": "codegraph", "args": ["mcp"] } } }\n' > "$case_root/.mcp.json"
before=$(sha256_file "$case_root/.mcp.json")
fake_bin="$TEST_ROOT/fake-bin-existing-backfill"
mkdir -p "$fake_bin"
fake_codegraph "$fake_bin" 0 0 0 0
RC_FAKE_PATH="$fake_bin" run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && [ -f "$case_root/.codex/config.toml" ] \
  && grep -q '\[mcp_servers.codegraph\]' "$case_root/.codex/config.toml" \
  && [ "$before" = "$(sha256_file "$case_root/.mcp.json")" ] \
  && ! compgen -G "$case_root/.mcp.json.cadence-backup-*" >/dev/null; then
  record_result it-s8-codegraph-existing-mcp-backfill "$RUN_STATUS" missing present pass
else
  record_result it-s8-codegraph-existing-mcp-backfill "$RUN_STATUS" missing missing fail
fi

# C17c. L0 skip + 缺摘要/技术栈 → 补齐且 L0 区块不变（it-s4-skip-summary-backfill / codex 终审 I2 + SM-02）。
case_root="$(mk_entry_fixture fx-skip-summary-backfill)"
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$before" != "$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")" ] \
  && grep -q '### 项目技术栈' "$case_root/CLAUDE.md" \
  && grep -q '### 项目技术栈' "$case_root/AGENTS.md" \
  && [ "$(managed_block_hash "$case_root/CLAUDE.md")" = "$(sha256_file "$KERNEL")" ] \
  && [ "$(managed_block_hash "$case_root/AGENTS.md")" = "$(sha256_file "$KERNEL")" ]; then
  record_result it-s4-skip-summary-backfill "$RUN_STATUS" missing backfilled pass
else
  record_result it-s4-skip-summary-backfill "$RUN_STATUS" missing missing fail
fi

# C17d. keep 决策 → 不生成备份（it-s3-keep-decision-no-backup / codex 终审 I3）。
case_root="$TEST_ROOT/fx-keep-no-backup"
mkdir -p "$case_root/.claude/rules"
cp "$TEST_DIR/../references/rules/language.md" "$case_root/.claude/rules/language.md"
printf '\n# 用户自定义补充\n不覆盖我\n' >> "$case_root/.claude/rules/language.md"
dec_file="$TEST_ROOT/decisions-keep-nobackup.json"
write_decisions "$dec_file" '[{"conflict_id":"s3:.claude/rules/language.md","decision":"keep"}]'
run_script apply "$case_root" --decisions "$dec_file"
if [ "$RUN_STATUS" -eq 0 ] \
  && ! compgen -G "$case_root/.claude/rules/language.md.cadence-backup-*" >/dev/null \
  && grep -q '不覆盖我' "$case_root/.claude/rules/language.md"; then
  record_result it-s3-keep-decision-no-backup "$RUN_STATUS" keep no-backup pass
else
  record_result it-s3-keep-decision-no-backup "$RUN_STATUS" keep backup fail
fi

# C17e. 幂等重跑 → 零备份零变更（it-idempotent-rerun-zero-backup / codex 终审 I3）。
case_root="$TEST_ROOT/fx-idempotent-rerun"
mkdir -p "$case_root"
run_script apply "$case_root" --no-interrupt
before=$(tree_hash "$case_root")
run_script apply "$case_root" --no-interrupt
after=$(tree_hash "$case_root")
backup_count=$(find "$case_root" -name '*.cadence-backup-*' | wc -l)
if [ "$RUN_STATUS" -eq 0 ] && [ "$before" = "$after" ] && [ "$backup_count" -eq 0 ]; then
  record_result it-idempotent-rerun-zero-backup "$RUN_STATUS" "$before" "$after" pass
else
  record_result it-idempotent-rerun-zero-backup "$RUN_STATUS" "$before" "$after" fail
fi

# C17f. dry-run 报告完整性：conflicts 含 allowed_decisions、steps 含真实 elapsed_ms
# （it-dryrun-report-completeness / codex 终审 I4）。
case_root="$(mk_drift_fixture fx-dryrun-completeness)"
run_script dry-run "$case_root"
if [ "$RUN_STATUS" -eq 0 ] \
  && jqr "['conflicts']" 2>/dev/null | grep -q 'allowed_decisions' \
  && assert_report_completeness "$REPORT"; then
  record_result it-dryrun-report-completeness "$RUN_STATUS" present present pass
else
  record_result it-dryrun-report-completeness "$RUN_STATUS" present missing fail
fi

# C17g. apply 报告各步真实计时（it-apply-steps-real-elapsed / codex 终审 I4）。
dec_file="$TEST_ROOT/decisions-elapsed.json"
write_decisions "$dec_file" '[{"conflict_id":"s4:CLAUDE.md","decision":"keep"}]'
run_script apply "$case_root" --decisions "$dec_file"
if [ "$RUN_STATUS" -eq 0 ] && assert_report_completeness "$REPORT"; then
  record_result it-apply-steps-real-elapsed "$RUN_STATUS" present present pass
else
  record_result it-apply-steps-real-elapsed "$RUN_STATUS" present missing fail
fi

# C17h. 老项目 code-reading.md 缺 CodeGraph 段落 → 不覆盖，报告手动合并
# （it-s3-codegraph-section-missing / codex 终审 I5 + RF-04）。
case_root="$TEST_ROOT/fx-codegraph-section-missing"
mkdir -p "$case_root/.claude/rules"
printf '# 旧版代码阅读规则\n\n仅 ast-grep，无其他内容。\n' > "$case_root/.claude/rules/code-reading.md"
before=$(sha256_file "$case_root/.claude/rules/code-reading.md")
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$before" = "$(sha256_file "$case_root/.claude/rules/code-reading.md")" ] \
  && ! compgen -G "$case_root/.claude/rules/code-reading.md.cadence-backup-*" >/dev/null \
  && jqr "['steps']" 2>/dev/null | grep -q 'codegraph-section-missing' \
  && jqr "['steps']" 2>/dev/null | grep -q '需用户手动合并 CodeGraph 段落'; then
  record_result it-s3-codegraph-section-missing "$RUN_STATUS" present reported pass
else
  record_result it-s3-codegraph-section-missing "$RUN_STATUS" present missing fail
fi

# C17i. 可选规则完整性检查（it-s3-optional-complete / codex 终审 I5 + OP-01）：
# 规则文件+摘要均存在 → 报告完整性检查 ok，二次运行零重写。
case_root="$TEST_ROOT/fx-optional-complete"
mkdir -p "$case_root"
run_script apply "$case_root" --no-interrupt
before=$(tree_hash "$case_root")
run_script apply "$case_root" --no-interrupt
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$before" = "$(tree_hash "$case_root")" ] \
  && jqr "['steps']" 2>/dev/null | grep -q 'optional-integrity' \
  && jqr "['steps']" 2>/dev/null | grep -q "'result': 'ok'"; then
  record_result it-s3-optional-complete "$RUN_STATUS" present ok pass
else
  record_result it-s3-optional-complete "$RUN_STATUS" present missing fail
fi

# ============================================================================
# D. 静态契约检查 sc-*（全部可执行，record_result 五参逐字调用）
# ============================================================================

# D1. frontmatter disable-model-invocation: true（FM-01）
if grep -q 'disable-model-invocation: true' "$SKILL_MD"; then
  record_result sc-disable-model-invocation 0 present present pass
else
  record_result sc-disable-model-invocation 1 present missing fail
fi

# D2. 裸 token 必须出现完整 token 规范化说明（PM-01）
if grep -qE 'no-interrupt.*--no-interrupt|--no-interrupt.*no-interrupt' "$SKILL_MD"; then
  record_result sc-bare-token 0 present present pass
else
  record_result sc-bare-token 1 present missing fail
fi

# D3. 两阶段 dry-run/apply 文本（XC-01 + design D3）
if grep -q 'dry-run' "$SKILL_MD" && grep -q 'apply' "$SKILL_MD"; then
  record_result sc-two-phase 0 present present pass
else
  record_result sc-two-phase 1 present missing fail
fi

# D4. 剪枝目录清单（sc-prune-list-<dir>，沿用 find 块）
for d in .venv venv env .env node_modules vendor; do
  if grep -q -- "$d" "$SKILL_MD"; then
    record_result "sc-prune-list-$d" 0 present present pass
  else
    record_result "sc-prune-list-$d" 1 present missing fail
  fi
done

# D5. 脚本存在（XC-07 + sc-script-exists）
if test -f "$SCRIPT"; then
  record_result sc-script-exists 0 present present pass
else
  record_result sc-script-exists 1 present missing fail
fi

# D6. routing-conformance delta：L1 源副本与仓库根同步（sc-l1-source-copy-sync）
if diff -q "$SKILL_DIR/references/rules/openspec-superpowers-workflow.md" \
          "$REPO_ROOT/.claude/rules/openspec-superpowers-workflow.md" >/dev/null 2>&1; then
  record_result sc-l1-source-copy-sync 0 same same pass
else
  record_result sc-l1-source-copy-sync 1 same diff fail
fi

# D7. 仓库根 openspec/config.yaml 不得含 rules.apply（sc-no-rules-apply）
if python3 -c "import yaml;d=yaml.safe_load(open('$REPO_ROOT/openspec/config.yaml'));assert 'apply' not in (d.get('rules') or {})" 2>/dev/null; then
  record_result sc-no-rules-apply 0 absent absent pass
else
  record_result sc-no-rules-apply 1 absent present fail
fi

# D8. L0 引用的规则文件存在性（sc-l0-rule-refs-exist）：提取 CLAUDE.md L0 区块内 .claude/rules/*.md 引用逐一 test -f
if python3 - "$REPO_ROOT/CLAUDE.md" <<'EOF'
import re,sys,os
text=open(sys.argv[1]).read()
refs=set(re.findall(r'\.claude/rules/[\w.-]+\.md', text))
missing=[r for r in refs if not os.path.exists(os.path.join(os.path.dirname(sys.argv[1]), r))]
print('\n'.join(missing)); sys.exit(1 if missing else 0)
EOF
then
  record_result sc-l0-rule-refs-exist 0 none none pass
else
  record_result sc-l0-rule-refs-exist 1 none missing fail
fi

# D9. 瘦身 SKILL 不得含直接读写目标项目文件的操作指令（sc-no-direct-target-writes）
if ! grep -qE '读取内容，写入项目的|将以下文件从.*写入' "$SKILL_MD"; then
  record_result sc-no-direct-target-writes 0 absent absent pass
else
  record_result sc-no-direct-target-writes 1 absent present fail
fi

# D10. 脚本 PRUNE_DIRS 与 SKILL.md find 剪枝清单一致（sc-prune-dirs-contract）。
# codex 终审 I6：修复 map() 误用导致的检查恒失败，且失败计入 fail（不再假绿）。
if assert_bounded_source_scan_contract; then
  record_result sc-prune-dirs-contract 0 consistent consistent pass
else
  record_result sc-prune-dirs-contract 1 consistent inconsistent fail
fi

printf 'SUMMARY pass=%s fail=%s\n' "$PASS_COUNT" "$FAIL_COUNT"
test "$FAIL_COUNT" -eq 0
