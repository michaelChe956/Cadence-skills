#!/usr/bin/env bash
# pre-check 离线集成验收：复用 Task 1 基线 fixture，验证首跑兼容性与二跑幂等。
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

# 复用 Task 1 基线的四端旧命名投影；新实现必须识别为就绪而不重写。
mkdir -p "$PROJECT/.claude/commands/opsx" "$PROJECT/.claude/skills/openspec-brainstorm" \
  "$PROJECT/.agents/skills/openspec-execute" "$PROJECT/.pi/skills" "$PROJECT/.pi/prompts" \
  "$PROJECT/.kimi-code/skills"
printf '%s\n' '# fixture propose' > "$PROJECT/.claude/commands/opsx/propose.md"
printf '%s\n' '# fixture skill' > "$PROJECT/.claude/skills/openspec-brainstorm/SKILL.md"
printf '%s\n' '# fixture execute' > "$PROJECT/.agents/skills/openspec-execute/SKILL.md"
for _name in brainstorm write-plan execute review verify; do
  printf '# pi %s\n' "$_name" > "$PROJECT/.pi/skills/$_name.md"
  printf '# pi prompt %s\n' "$_name" > "$PROJECT/.pi/prompts/$_name.md"
  printf '# kimi %s\n' "$_name" > "$PROJECT/.kimi-code/skills/$_name.md"
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

# 四层各 14 条直连软链，与冻结基线完全一致。
_SKILLS='brainstorming writing-plans executing-plans subagent-driven-development test-driven-development systematic-debugging verification-before-completion requesting-code-review receiving-code-review finishing-a-development-branch using-superpowers dispatching-parallel-agents creating-skills testing-skills'
for _layer in "$HOME_DIR/.agents/skills" "$HOME_DIR/.codex/skills/skills" "$HOME_DIR/.claude/skills" "$HOME_DIR/.pi/agent/skills"; do
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
  (cd "$HOME_DIR" && find . -type f -not -path './.git/*' -not -path './.agents/superpowers/.git/*' -not -path './.precheck-*' | LC_ALL=C sort) | while IFS= read -r _path; do
    printf 'file home %s %s\n' "${_path#./}" "$(sha256_file "$HOME_DIR/$_path")" >> "$_out"
  done
  for _layer in "$HOME_DIR/.agents/skills" "$HOME_DIR/.codex/skills/skills" "$HOME_DIR/.claude/skills" "$HOME_DIR/.pi/agent/skills"; do
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
BASELINE="$TEST_DIR/baselines/precheck-v1/tree.txt"
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
printf 'integration PASS\n'
