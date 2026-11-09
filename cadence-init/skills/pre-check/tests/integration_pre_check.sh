#!/usr/bin/env bash
# pre-check 离线集成验收：复用 v2 真实 OpenSpec fixture，验证首跑兼容性与二跑幂等。
set -u
TEST_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SCRIPT="$TEST_DIR/../scripts/pre-check.sh"
ROOT="$(mktemp -d "${TMPDIR:-/tmp}/precheck-integration.XXXXXX")"
PROJECT="$ROOT/project"; HOME_DIR="$ROOT/home"; BIN="$ROOT/bin"; REMOTE="$ROOT/remote.git"
REPORT1="$ROOT/first.json"; REPORT2="$ROOT/rerun.json"
trap 'rm -rf "$ROOT"' EXIT HUP INT TERM
mkdir -p "$PROJECT" "$HOME_DIR" "$BIN"

# fake CLI：所有动作离线且输出与 Task 1 基线一致。
cat > "$BIN/npx" <<'EOF_NPX'
#!/usr/bin/env bash
printf '10.9.0\n'
EOF_NPX
cat > "$BIN/uvx" <<'EOF_UVX'
#!/usr/bin/env bash
printf 'uvx 0.4.0\n'
EOF_UVX
cat > "$BIN/ast-grep" <<'EOF_AST'
#!/usr/bin/env bash
printf 'ast-grep 0.40.0\n'
EOF_AST
cat > "$BIN/codegraph" <<'EOF_CG'
#!/usr/bin/env bash
mkdir -p "$HOME/.codegraph"
printf '{"v":2,"d":"2026-09-05","k":"cli_command","n":"version","c":1,"e":0}\n' >> "$HOME/.codegraph/telemetry-queue.jsonl"
printf 'codegraph 0.8.0\n'
EOF_CG
cat > "$BIN/pi" <<'EOF_PI'
#!/usr/bin/env bash
if [ "${1:-}" = "list" ]; then printf 'pi-mcp-adapter\n'; exit 0; fi
exit 1
EOF_PI
cp "$TEST_DIR/helpers/fake-openspec.sh" "$BIN/openspec"
cp "$TEST_DIR/helpers/fake-git.sh" "$BIN/git"
chmod +x "$BIN"/*

# v2 真实 OpenSpec 投影；严格判定不得接受旧命名文件。
mkdir -p "$PROJECT/.claude/commands/opsx" "$PROJECT/.claude/skills/openspec-brainstorm" \
  "$PROJECT/.agents/skills/openspec-execute" "$PROJECT/.pi/skills" "$PROJECT/.pi/prompts" \
  "$PROJECT/.kimi-code/skills"
printf '%s\n' '# fixture propose' > "$PROJECT/.claude/commands/opsx/propose.md"
printf '%s\n' '# fixture skill' > "$PROJECT/.claude/skills/openspec-brainstorm/SKILL.md"
printf '%s\n' '# fixture execute' > "$PROJECT/.agents/skills/openspec-execute/SKILL.md"
# 6 投影完成态（含 update-change）：与脚本四端就绪判据（pi 6+6、kimi 6）及
# fake-openspec init 写入模板保持一致，首跑预期零写入、overall=success。
for _name in execute plan review verify brainstorm update-change; do
  mkdir -p "$PROJECT/.pi/skills/openspec-$_name" "$PROJECT/.kimi-code/skills/openspec-$_name"
  printf 'pi openspec skill %s\n' "$_name" > "$PROJECT/.pi/skills/openspec-$_name/SKILL.md"
  printf 'pi openspec %s\n' "$_name" > "$PROJECT/.pi/prompts/opsx-$_name.md"
  printf 'kimi openspec %s\n' "$_name" > "$PROJECT/.kimi-code/skills/openspec-$_name/SKILL.md"
done
printf '%s\n' 'project non-target sentinel' > "$PROJECT/project-sentinel.txt"

# 本地 bare remote + 有效 worktree，完全不访问网络。
git init --bare -q "$REMOTE"
_WORKTREE="$ROOT/superpowers-worktree"
git init -q -b main "$_WORKTREE"
git -C "$_WORKTREE" config user.email fixture@example.invalid
git -C "$_WORKTREE" config user.name fixture
mkdir -p "$_WORKTREE/skills"
for _name in brainstorming writing-plans executing-plans subagent-driven-development \
  test-driven-development systematic-debugging verification-before-completion \
  requesting-code-review receiving-code-review finishing-a-development-branch \
  using-superpowers dispatching-parallel-agents creating-skills testing-skills; do
  mkdir -p "$_WORKTREE/skills/$_name"
  printf '# %s\n' "$_name" > "$_WORKTREE/skills/$_name/SKILL.md"
done
git -C "$_WORKTREE" add skills
git -C "$_WORKTREE" commit -qm 'fixture superpowers'
git -C "$_WORKTREE" remote add origin "$REMOTE"
git -C "$_WORKTREE" push -q -u origin main
git --git-dir "$REMOTE" symbolic-ref HEAD refs/heads/main
mkdir -p "$HOME_DIR/.agents"
# 首跑走本地 bare remote 的 clone 路径，确保 Git origin 与冻结基线同构。
export CADENCE_TEST_GIT_CANDIDATES="$REMOTE"
export REAL_GIT="$(command -v git)"

# 四层各 14 条直连软链，与冻结基线完全一致；Codex 层为官方约定的扁平布局。
_SKILLS='brainstorming writing-plans executing-plans subagent-driven-development test-driven-development systematic-debugging verification-before-completion requesting-code-review receiving-code-review finishing-a-development-branch using-superpowers dispatching-parallel-agents creating-skills testing-skills'
for _layer in "$HOME_DIR/.agents/skills" "$HOME_DIR/.codex/skills" "$HOME_DIR/.claude/skills" "$HOME_DIR/.pi/agent/skills"; do
  mkdir -p "$_layer"
  for _name in $_SKILLS; do
    ln -s "$HOME_DIR/.agents/superpowers/skills/$_name" "$_layer/$_name"
  done
done
printf '%s\n' 'home non-target sentinel' > "$HOME_DIR/home-sentinel.txt"

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  else shasum -a 256 "$1" | awk '{print $1}'; fi
}

snapshot() {
  _out="$1"; : > "$_out"
  (cd "$PROJECT" && find . -type f -not -path './.git/*' -not -path './.precheck-*' | LC_ALL=C sort) | while IFS= read -r _path; do
    printf 'file project %s %s\n' "${_path#./}" "$(sha256_file "$PROJECT/$_path")" >> "$_out"
  done
  (cd "$HOME_DIR" && find . -type f -not -path './.git/*' -not -path './.agents/superpowers/.git/*' -not -path './.precheck-*' -not -path './.codegraph/*' | LC_ALL=C sort) | while IFS= read -r _path; do
    printf 'file home %s %s\n' "${_path#./}" "$(sha256_file "$HOME_DIR/$_path")" >> "$_out"
  done
  for _layer in "$HOME_DIR/.agents/skills" "$HOME_DIR/.codex/skills" "$HOME_DIR/.claude/skills" "$HOME_DIR/.pi/agent/skills"; do
    [ -d "$_layer" ] || continue
    for _link in "$_layer"/*; do
      [ -L "$_link" ] || continue
      _raw="$(readlink "$_link")"
      case "$_raw" in /*) _resolved="$_raw";; *) _resolved="$(cd "$(dirname "$_link")" && pwd -P)/$_raw";; esac
      printf 'link %s %s readlink=%s resolved=%s\n' "${_layer#$HOME_DIR/}" "${_link##*/}" "$_raw" "$_resolved" >> "$_out"
    done
  done
  printf 'git origin %s\n' "$(git -C "$HOME_DIR/.agents/superpowers" remote get-url origin)" >> "$_out"
  printf 'git branch %s\n' "$(git -C "$HOME_DIR/.agents/superpowers" rev-parse --abbrev-ref HEAD)" >> "$_out"
  printf 'git head %s\n' "$(git -C "$HOME_DIR/.agents/superpowers" rev-parse HEAD)" >> "$_out"
}

normalize_snapshot_file() {
  sed -e "s|$3|<ISOLATION_ROOT>|g" \
      -e 's|/tmp/precheck-baseline\.[^/]*/|<ISOLATION_ROOT>/|g' "$1" > "$2"
}

compare_compatibility_snapshot() {
  # Git commit 对象包含采集时刻，冻结基线与本次临时 bare remote 不共享对象；
  # 将动态 revision 规范化为占位符，同时保留 Git HEAD 字段参与结构性 1:1 diff。
  sed 's/^git head .*/git head <REVISION>/' "$1" > "$ROOT/compat-baseline.log"
  sed 's/^git head .*/git head <REVISION>/' "$2" > "$ROOT/compat-current.log"
  diff -u "$ROOT/compat-baseline.log" "$ROOT/compat-current.log"
}

export HOME="$HOME_DIR"
export PATH="$BIN:$PATH"
export FAKE_OPENSPEC_CALLS="$ROOT/openspec-calls"
export FAKE_GIT_ARGS="$ROOT/git-args"
export TMPDIR="$ROOT/tmp"
mkdir -p "$TMPDIR"

(cd "$PROJECT" && bash "$SCRIPT" run --no-interrupt > "$REPORT1")
_first_rc=$?
[ "$_first_rc" -eq 0 ] || { cat "$REPORT1" >&2; exit "$_first_rc"; }
snapshot "$ROOT/after-first.raw"
normalize_snapshot_file "$ROOT/after-first.raw" "$ROOT/after-first.log" "$ROOT"
BASELINE="$TEST_DIR/baselines/precheck-v2/tree.txt"
normalize_snapshot_file "$BASELINE" "$ROOT/baseline.log" "$ROOT"
compare_compatibility_snapshot "$ROOT/baseline.log" "$ROOT/after-first.log"
_baseline_diff_rc=$?
[ "$_baseline_diff_rc" -eq 0 ] || exit "$_baseline_diff_rc"

(cd "$PROJECT" && bash "$SCRIPT" run --no-interrupt > "$REPORT2")
_second_rc=$?
[ "$_second_rc" -eq 0 ] || { cat "$REPORT2" >&2; exit "$_second_rc"; }
snapshot "$ROOT/after-rerun.raw"
normalize_snapshot_file "$ROOT/after-rerun.raw" "$ROOT/after-rerun.log" "$ROOT"
diff -u "$ROOT/after-first.log" "$ROOT/after-rerun.log"
_rerun_diff_rc=$?
[ "$_rerun_diff_rc" -eq 0 ] || exit "$_rerun_diff_rc"

_update_calls="$(awk '$0 == "update" { count++ } END { print count + 0 }' "$FAKE_OPENSPEC_CALLS")"
[ "$_update_calls" -eq 2 ] || {
  printf 'expected 2 openspec update calls, got %s\n' "$_update_calls" >&2
  cat "$FAKE_OPENSPEC_CALLS" >&2
  exit 1
}

python3 - "$REPORT1" "$REPORT2" <<'PY'
import json, sys
first = json.load(open(sys.argv[1], encoding='utf-8'))
report = json.load(open(sys.argv[2], encoding='utf-8'))
assert first['overall'] == 'success', first
assert report['overall'] == 'success', report
phases = {p['phase']: p for p in report['phases']}
assert set(phases) == {'base-tools', 'openspec', 'superpowers-git', 'superpowers-links', 'verify'}
for name in phases:
    assert phases[name]['result'] == 'skipped', (name, phases[name])
    assert phases[name]['created'] == 0
    assert phases[name]['updated'] == 0
    assert phases[name]['conflicts'] == 0
    assert 'error' in phases[name] and phases[name]['error'] is None
assert phases['superpowers-git']['action'] == 'fetch-pull-ff-only'
assert phases['verify']['action'] == 'all-skipped'
assert phases['superpowers-git']['before_revision'] == phases['superpowers-git']['after_revision']
print('idempotency PASS')
PY
_python_rc=$?
[ "$_python_rc" -eq 0 ] || exit "$_python_rc"

# --- Codex 层布局场景：旧嵌套层迁移、非托管条目保留、verify 可读性复核 ---
scenario_fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }

# A. 旧嵌套层（~/.codex/skills/skills）中的受管链接迁移到扁平层，旧目录迁空后删除。
mkdir -p "$HOME_DIR/.codex/skills/skills"
for _name in $_SKILLS; do
  ln -s "$HOME_DIR/.agents/superpowers/skills/$_name" "$HOME_DIR/.codex/skills/skills/$_name"
done
(cd "$PROJECT" && bash "$SCRIPT" run --no-interrupt > "$ROOT/migrate.json")
_migrate_rc=$?
[ "$_migrate_rc" -eq 0 ] || { cat "$ROOT/migrate.json" >&2; scenario_fail "旧嵌套层迁移运行失败"; }
if [ -d "$HOME_DIR/.codex/skills/skills" ]; then
  scenario_fail "旧嵌套层目录迁空后未删除"
fi
for _name in $_SKILLS; do
  _link="$HOME_DIR/.codex/skills/$_name"
  [ -L "$_link" ] || scenario_fail "扁平 Codex 层缺少软链：$_name"
  [ "$(readlink "$_link")" = "$HOME_DIR/.agents/superpowers/skills/$_name" ] \
    || scenario_fail "扁平 Codex 层软链目标不符：$_name"
  [ -r "$_link/SKILL.md" ] || scenario_fail "扁平 Codex 层软链不可解析到可读 SKILL.md：$_name"
done
printf 'codex-legacy-migration PASS\n'

# B. 旧嵌套层含非托管条目时保留目录与条目，并输出告警。
mkdir -p "$HOME_DIR/.codex/skills/skills"
printf 'third party\n' > "$HOME_DIR/.codex/skills/skills/third-party.txt"
ln -s "$HOME_DIR/.agents/skills" "$HOME_DIR/.codex/skills/skills/third-party-link"
(cd "$PROJECT" && bash "$SCRIPT" run --no-interrupt > "$ROOT/legacy-keep.json")
_keep_rc=$?
[ "$_keep_rc" -eq 0 ] || { cat "$ROOT/legacy-keep.json" >&2; scenario_fail "旧嵌套层保留场景运行失败"; }
[ -d "$HOME_DIR/.codex/skills/skills" ] || scenario_fail "旧嵌套层含非托管条目时目录被删除"
[ -f "$HOME_DIR/.codex/skills/skills/third-party.txt" ] || scenario_fail "旧嵌套层非托管文件被删除"
[ -L "$HOME_DIR/.codex/skills/skills/third-party-link" ] || scenario_fail "旧嵌套层第三方链被删除"
grep -q 'CODEX_LEGACY_ENTRY_RETAINED' "$ROOT/legacy-keep.json" || scenario_fail "缺少旧嵌套层条目保留告警"
grep -q 'CODEX_LEGACY_DIR_RETAINED' "$ROOT/legacy-keep.json" || scenario_fail "缺少旧嵌套层目录保留告警"
printf 'codex-legacy-retain PASS\n'

# C. Codex 内置系统技能目录（~/.codex/skills/.system）不计入受管集合，不产生误报。
mkdir -p "$HOME_DIR/.codex/skills/.system/builtin-skill"
ln -s "$HOME_DIR/.codex/skills/.system/builtin-skill/MISSING.md" \
  "$HOME_DIR/.codex/skills/.system/builtin-skill/SKILL.md"
(cd "$PROJECT" && bash "$SCRIPT" run --no-interrupt > "$ROOT/system.json")
_system_rc=$?
[ "$_system_rc" -eq 0 ] || { cat "$ROOT/system.json" >&2; scenario_fail ".system 目录触发 verify 失败"; }
grep -q '"overall": "success"' "$ROOT/system.json" || scenario_fail ".system 目录场景总体结果非 success"
if grep -qE 'unreadable-(skill|target)|missing-link|broken-link' "$ROOT/system.json"; then
  scenario_fail ".system 目录条目被计入受管集合并产生 VERIFY_ERROR"
fi
printf 'codex-system-dir PASS\n'

# D. 受管软链最终解析不到可读 SKILL.md 时，verify 判失败并记录 VERIFY_ERROR。
rm -f "$HOME_DIR/.agents/superpowers/skills/brainstorming/SKILL.md"
(cd "$PROJECT" && bash "$SCRIPT" run --no-interrupt > "$ROOT/verify-fail.json")
_verify_rc=$?
[ "$_verify_rc" -ne 0 ] || scenario_fail "受管软链不可读时 verify 未判失败"
grep -q 'unreadable-skill' "$ROOT/verify-fail.json" || scenario_fail "缺少 VERIFY_ERROR 记录"
grep -q '"overall": "failed"' "$ROOT/verify-fail.json" || scenario_fail "总体结果未判失败"
printf 'codex-verify-unreadable PASS\n'

printf 'integration PASS\n'
