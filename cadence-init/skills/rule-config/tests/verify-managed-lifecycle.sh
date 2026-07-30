#!/usr/bin/env bash

set -u

TEST_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL="$TEST_DIR/../SKILL.md"
REPO_ROOT=$(CDPATH= cd -- "$TEST_DIR/../../../.." && pwd)
REFERENCE="$TEST_DIR/helpers/managed-lifecycle-reference.sh"
KERNEL="$TEST_DIR/../references/rules/agent-routing-kernel.md"
L1_SOURCE="$TEST_DIR/../references/rules/openspec-superpowers-workflow.md"
CONFIG_TEMPLATE="$TEST_DIR/../references/openspec/config.yaml"
OPENSPEC_WRAPPER="$TEST_DIR/fixtures/instrumented-openspec.sh"
PUBLISH_HOOK="$TEST_DIR/fixtures/invalidate-candidate.sh"

assert_fresh_change_contract() {
  local missing=0
  for needle in \
    'openspec new change cadence-rule-config-validation' \
    '--change cadence-rule-config-validation --json'; do
    if ! rg -Fq -- "$needle" "$SKILL"; then
      printf '缺少 rule-config 候选验证约定: %s\n' "$needle" >&2
      missing=1
    fi
  done
  return "$missing"
}

if ! assert_fresh_change_contract; then
  exit 1
fi

for required in "$REFERENCE" "$KERNEL" "$L1_SOURCE" "$CONFIG_TEMPLATE" "$OPENSPEC_WRAPPER" "$PUBLISH_HOOK"; do
  if [ ! -e "$required" ]; then
    printf '缺少测试依赖: %s\n' "$required" >&2
    exit 1
  fi
done

TEST_ROOT=$(mktemp -d)
trap 'rm -rf "$TEST_ROOT"' EXIT HUP INT TERM

PASS_COUNT=0
FAIL_COUNT=0

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

sha256_pair() {
  sha256sum "$1" "$2" | awk '{print $1}' | paste -sd: -
}

managed_block_hash() {
  awk '/cadence-managed:openspec-superpowers-routing:v1:start/{inside=1} inside{print} /cadence-managed:openspec-superpowers-routing:v1:end/{inside=0; exit}' "$1" | sha256sum | awk '{print $1}'
}

outside_l0_hash() {
  awk '
    /cadence-managed:openspec-superpowers-routing:v[0-9]+:start/ { inside=1; next }
    /cadence-managed:openspec-superpowers-routing:v[0-9]+:end/ { inside=0; next }
    !inside { print }
  ' "$1" | sha256sum | awk '{print $1}'
}

record_result() {
  name=$1
  status=$2
  before=$3
  after=$4
  result=$5
  if [ "$result" = pass ]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    printf 'PASS %-38s status=%s before=%s after=%s\n' "$name" "$status" "$before" "$after"
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf 'FAIL %-38s status=%s before=%s after=%s\n' "$name" "$status" "$before" "$after" >&2
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

run_reference() {
  set +e
  bash "$REFERENCE" "$@"
  RUN_STATUS=$?
  set -e
}

set -e

# 1. 真实入口复制件在当前版本下必须幂等，不能退化为纯 kernel。
case_root="$TEST_ROOT/actual-entry-idempotent"
mkdir -p "$case_root"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_reference l0 "$case_root" "$KERNEL" no-interrupt replace ok
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
assert_same actual-entry-idempotent "$RUN_STATUS" "$before" "$after" 0

# 2. 当前 L0 漂移在普通模式无响应时必须保留真实入口全文。
case_root="$TEST_ROOT/l0-drift-normal"
mkdir -p "$case_root"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
sed -i '0,/首个用户可见段落/s//本地漂移段落/' "$case_root/CLAUDE.md"
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_reference l0 "$case_root" "$KERNEL" normal no-response ok
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
assert_same l0-drift-normal-preserved "$RUN_STATUS" "$before" "$after" 0

# 3. no-interrupt 修复漂移时，任意区块外内容必须逐字保留。
case_root="$TEST_ROOT/l0-drift-replace"
mkdir -p "$case_root"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
sed -i '0,/首个用户可见段落/s//本地漂移段落/' "$case_root/CLAUDE.md"
sed -i '0,/首个用户可见段落/s//另一个漂移段落/' "$case_root/AGENTS.md"
outside_claude_before=$(outside_l0_hash "$case_root/CLAUDE.md")
outside_agents_before=$(outside_l0_hash "$case_root/AGENTS.md")
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_reference l0 "$case_root" "$KERNEL" no-interrupt replace ok
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$(managed_block_hash "$case_root/CLAUDE.md")" = "$(sha256_file "$KERNEL")" ] \
  && [ "$(managed_block_hash "$case_root/AGENTS.md")" = "$(sha256_file "$KERNEL")" ] \
  && [ "$outside_claude_before" = "$(outside_l0_hash "$case_root/CLAUDE.md")" ] \
  && [ "$outside_agents_before" = "$(outside_l0_hash "$case_root/AGENTS.md")" ]; then
  assert_changed l0-drift-replaced-outside-preserved "$RUN_STATUS" "$before" "$after"
else
  record_result l0-drift-replaced-outside-preserved "$RUN_STATUS" "$before" "$after" fail
fi

# 4. 单侧与乱序标记修复必须保留所有非标记行。
case_root="$TEST_ROOT/l0-broken-markers"
mkdir -p "$case_root"
printf '# CLAUDE.md\n任意前置内容\n<!-- cadence-managed:openspec-superpowers-routing:v1:start -->\n无法判定归属的本地内容\n任意后置内容\n' > "$case_root/CLAUDE.md"
printf '# AGENTS.md\n任意前置内容\n<!-- cadence-managed:openspec-superpowers-routing:v1:end -->\n无法判定归属的本地内容\n<!-- cadence-managed:openspec-superpowers-routing:v1:start -->\n任意后置内容\n' > "$case_root/AGENTS.md"
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_reference l0 "$case_root" "$KERNEL" no-interrupt replace ok
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$(rg -c 'cadence-managed:openspec-superpowers-routing:v1:start' "$case_root/CLAUDE.md")" -eq 1 ] \
  && [ "$(rg -c 'cadence-managed:openspec-superpowers-routing:v1:end' "$case_root/CLAUDE.md")" -eq 1 ] \
  && [ "$(rg -c 'cadence-managed:openspec-superpowers-routing:v1:start' "$case_root/AGENTS.md")" -eq 1 ] \
  && [ "$(rg -c 'cadence-managed:openspec-superpowers-routing:v1:end' "$case_root/AGENTS.md")" -eq 1 ] \
  && rg -q '任意前置内容' "$case_root/CLAUDE.md" \
  && rg -q '无法判定归属的本地内容' "$case_root/CLAUDE.md" \
  && rg -q '任意后置内容' "$case_root/CLAUDE.md" \
  && rg -q '任意前置内容' "$case_root/AGENTS.md" \
  && rg -q '无法判定归属的本地内容' "$case_root/AGENTS.md" \
  && rg -q '任意后置内容' "$case_root/AGENTS.md"; then
  assert_changed l0-broken-markers-preserve-arbitrary "$RUN_STATUS" "$before" "$after"
else
  record_result l0-broken-markers-preserve-arbitrary "$RUN_STATUS" "$before" "$after" fail
fi

# 5. 第一个 L0 备份成功、第二个实际失败时双入口都不得写入。
case_root="$TEST_ROOT/l0-backup-barrier"
mkdir -p "$case_root"
cp "$REPO_ROOT/CLAUDE.md" "$case_root/CLAUDE.md"
cp "$REPO_ROOT/AGENTS.md" "$case_root/AGENTS.md"
sed -i '0,/首个用户可见段落/s//漂移-CLAUDE/' "$case_root/CLAUDE.md"
sed -i '0,/首个用户可见段落/s//漂移-AGENTS/' "$case_root/AGENTS.md"
before=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
run_reference l0 "$case_root" "$KERNEL" no-interrupt replace fail-2
after=$(sha256_pair "$case_root/CLAUDE.md" "$case_root/AGENTS.md")
if [ "$RUN_STATUS" -eq 41 ] \
  && [ "$before" = "$after" ] \
  && compgen -G "$case_root/CLAUDE.md.cadence-backup-*" >/dev/null \
  && ! compgen -G "$case_root/AGENTS.md.cadence-backup-*" >/dev/null; then
  record_result l0-second-backup-failure-barrier "$RUN_STATUS" "$before" "$after" pass
else
  record_result l0-second-backup-failure-barrier "$RUN_STATUS" "$before" "$after" fail
fi

# 6. L1 普通保留、no-interrupt 替换和备份失败。
case_root="$TEST_ROOT/l1"
mkdir -p "$case_root"
cp "$L1_SOURCE" "$case_root/workflow.md"
printf '\n本地漂移\n' >> "$case_root/workflow.md"
before=$(sha256_file "$case_root/workflow.md")
run_reference l1 "$case_root/workflow.md" "$L1_SOURCE" normal no-response ok
after=$(sha256_file "$case_root/workflow.md")
assert_same l1-drift-normal-preserved "$RUN_STATUS" "$before" "$after" 0
run_reference l1 "$case_root/workflow.md" "$L1_SOURCE" no-interrupt replace fail
after_fail=$(sha256_file "$case_root/workflow.md")
assert_same l1-backup-failure-preserved "$RUN_STATUS" "$after" "$after_fail" 42
run_reference l1 "$case_root/workflow.md" "$L1_SOURCE" no-interrupt replace ok
after_replace=$(sha256_file "$case_root/workflow.md")
if [ "$RUN_STATUS" -eq 0 ] && cmp -s "$case_root/workflow.md" "$L1_SOURCE" && compgen -G "$case_root/workflow.md.cadence-backup-*" >/dev/null; then
  assert_changed l1-backed-up-and-replaced "$RUN_STATUS" "$after_fail" "$after_replace"
else
  record_result l1-backed-up-and-replaced "$RUN_STATUS" "$after_fail" "$after_replace" fail
fi

# OpenSpec 调用参数：target template mode decision backup-result。
run_openspec() {
  run_reference openspec "$1" "$CONFIG_TEMPLATE" "$2" "$3" "$4"
}

# 7. 普通模式 rules.apply 无响应时必须保留。
case_root="$TEST_ROOT/apply-normal"
mkdir -p "$case_root"
printf 'schema: spec-driven\nrules:\n  apply:\n    - invalid-artifact\n' > "$case_root/config.yaml"
before=$(sha256_file "$case_root/config.yaml")
run_openspec "$case_root/config.yaml" normal no-response ok
after=$(sha256_file "$case_root/config.yaml")
assert_same rules-apply-normal-preserved "$RUN_STATUS" "$before" "$after" 0

# 8. 不可解析 YAML 与字符串类型冲突必须由真实 YAML 解析发现并失败关闭。
case_root="$TEST_ROOT/yaml-errors"
mkdir -p "$case_root"
printf 'schema: spec-driven\nrules: [\n' > "$case_root/invalid.yaml"
before=$(sha256_file "$case_root/invalid.yaml")
run_openspec "$case_root/invalid.yaml" no-interrupt replace ok
after=$(sha256_file "$case_root/invalid.yaml")
if [ "$RUN_STATUS" -eq 51 ] && [ "$before" = "$after" ] && compgen -G "$case_root/invalid.yaml.cadence-backup-*" >/dev/null; then
  record_result invalid-yaml-backed-up-preserved "$RUN_STATUS" "$before" "$after" pass
else
  record_result invalid-yaml-backed-up-preserved "$RUN_STATUS" "$before" "$after" fail
fi
printf 'schema: spec-driven\nrules:\n  proposal: invalid-string\n' > "$case_root/type.yaml"
before=$(sha256_file "$case_root/type.yaml")
run_openspec "$case_root/type.yaml" no-interrupt replace ok
after=$(sha256_file "$case_root/type.yaml")
if [ "$RUN_STATUS" -eq 52 ] && [ "$before" = "$after" ] && compgen -G "$case_root/type.yaml.cadence-backup-*" >/dev/null; then
  record_result yaml-type-conflict-backed-up-preserved "$RUN_STATUS" "$before" "$after" pass
else
  record_result yaml-type-conflict-backed-up-preserved "$RUN_STATUS" "$before" "$after" fail
fi

# 9. 成功合并必须执行真实四类 instructions，保留自定义项，并在第二次运行幂等。
case_root="$TEST_ROOT/openspec-success"
mkdir -p "$case_root"
printf 'schema: spec-driven\ncontext: |\n  custom-context\nx-project-metadata:\n  owner: custom-owner\nrules:\n  proposal:\n    - custom-proposal\n' > "$case_root/config.yaml"
export CADENCE_REAL_OPENSPEC_BIN
CADENCE_REAL_OPENSPEC_BIN=$(command -v openspec)
export CADENCE_OPENSPEC_BIN="$OPENSPEC_WRAPPER"
export CADENCE_OPENSPEC_LOG="$case_root/instructions.log"
unset CADENCE_FAIL_OPENSPEC_ARTIFACT CADENCE_BEFORE_PUBLISH_HOOK
before=$(sha256_file "$case_root/config.yaml")
run_openspec "$case_root/config.yaml" no-interrupt replace ok
after_first=$(sha256_file "$case_root/config.yaml")
run_openspec "$case_root/config.yaml" no-interrupt replace ok
after_second=$(sha256_file "$case_root/config.yaml")
instructions_logged=yes
for artifact in proposal design specs tasks; do
  if ! rg -Fq "instructions $artifact --change cadence-rule-config-validation --json" "$case_root/instructions.log"; then
    instructions_logged=no
    break
  fi
done
if [ "$RUN_STATUS" -eq 0 ] \
  && [ "$after_first" = "$after_second" ] \
  && rg -q 'custom-context|custom-proposal|x-project-metadata|custom-owner' "$case_root/config.yaml" \
  && [ "$instructions_logged" = yes ] \
  && rg -Fq 'new change cadence-rule-config-validation' "$case_root/instructions.log"; then
  assert_changed openspec-real-instructions-idempotent "$RUN_STATUS" "$before" "$after_first"
else
  record_result openspec-real-instructions-idempotent "$RUN_STATUS" "$before" "$after_second" fail
fi

# 10. no-interrupt rules.apply 必须备份后移除，并通过真实 instructions。
case_root="$TEST_ROOT/apply-remove"
mkdir -p "$case_root"
printf 'schema: spec-driven\nrules:\n  proposal:\n    - custom-proposal\n  apply:\n    - invalid-artifact\n' > "$case_root/config.yaml"
export CADENCE_OPENSPEC_LOG="$case_root/instructions.log"
export CADENCE_EXPECT_BACKUP_TARGET="$case_root/config.yaml"
unset CADENCE_FAIL_OPENSPEC_ARTIFACT CADENCE_BEFORE_PUBLISH_HOOK
before=$(sha256_file "$case_root/config.yaml")
run_openspec "$case_root/config.yaml" no-interrupt replace ok
after=$(sha256_file "$case_root/config.yaml")
if [ "$RUN_STATUS" -eq 0 ] && ! rg -q '^  apply:' "$case_root/config.yaml" && rg -q 'custom-proposal' "$case_root/config.yaml" && compgen -G "$case_root/config.yaml.cadence-backup-*" >/dev/null; then
  assert_changed rules-apply-backed-up-removed "$RUN_STATUS" "$before" "$after"
else
  record_result rules-apply-backed-up-removed "$RUN_STATUS" "$before" "$after" fail
fi
unset CADENCE_EXPECT_BACKUP_TARGET

# 11. 真实 instructions 命令失败时不得发布候选。
case_root="$TEST_ROOT/instructions-fail"
mkdir -p "$case_root"
cp "$CONFIG_TEMPLATE" "$case_root/config.yaml"
export CADENCE_OPENSPEC_LOG="$case_root/instructions.log"
export CADENCE_FAIL_OPENSPEC_ARTIFACT=design
unset CADENCE_BEFORE_PUBLISH_HOOK
before=$(sha256_file "$case_root/config.yaml")
run_openspec "$case_root/config.yaml" no-interrupt replace ok
after=$(sha256_file "$case_root/config.yaml")
assert_same instructions-failure-preserved "$RUN_STATUS" "$before" "$after" 53
unset CADENCE_FAIL_OPENSPEC_ARTIFACT

# 12. 发布前 Hook 使候选消失，实际原子 mv 失败时原文件必须不变。
case_root="$TEST_ROOT/publish-fail"
mkdir -p "$case_root"
printf 'schema: spec-driven\ncontext: custom\n' > "$case_root/config.yaml"
export CADENCE_OPENSPEC_LOG="$case_root/instructions.log"
export CADENCE_BEFORE_PUBLISH_HOOK="$PUBLISH_HOOK"
before=$(sha256_file "$case_root/config.yaml")
run_openspec "$case_root/config.yaml" no-interrupt replace ok
after=$(sha256_file "$case_root/config.yaml")
assert_same atomic-publish-failure-preserved "$RUN_STATUS" "$before" "$after" 54
unset CADENCE_BEFORE_PUBLISH_HOOK

printf 'SUMMARY pass=%s fail=%s\n' "$PASS_COUNT" "$FAIL_COUNT"
test "$FAIL_COUNT" -eq 0
