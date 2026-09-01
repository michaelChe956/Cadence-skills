#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLER="$ROOT_DIR/install.sh"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/cadence-install-tests.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

CURRENT_CASE=unknown
LAST_OUTPUT=
LAST_STATUS=未记录

on_error() {
  local status="$1"
  printf 'FAIL %s\n' "$CURRENT_CASE" >&2
  printf '命令失败，退出码：%s\n' "$status" >&2
  if [[ -n "$LAST_OUTPUT" && -f "$LAST_OUTPUT" ]]; then
    printf '命令输出（%s）：\n' "$LAST_OUTPUT" >&2
    cat "$LAST_OUTPUT" >&2
  fi
  exit "$status"
}
trap 'on_error "$?"' ERR

pass() { printf 'PASS %s\n' "$1"; }
fail_test() {
  printf 'FAIL %s\n' "$CURRENT_CASE" >&2
  printf '原因：%s\n' "$1" >&2
  if [[ -n "$LAST_OUTPUT" && -f "$LAST_OUTPUT" ]]; then
    printf '命令输出（%s）：\n' "$LAST_OUTPUT" >&2
    cat "$LAST_OUTPUT" >&2
  fi
  printf '退出码：%s\n' "$LAST_STATUS" >&2
  exit 1
}
assert_contains() { grep -F -- "$2" "$1" >/dev/null || fail_test "未找到 [$2] 于 $1"; }
assert_not_exists() { [[ ! -e "$1" && ! -L "$1" ]] || fail_test "不应存在：$1"; }
snapshot_home() {
  local root="$1" out="$2"
  {
    find "$root/.agents" "$root/.claude" "$root/.codex" -mindepth 1 -maxdepth 8 -printf '%y %p\n' 2>/dev/null | sort
    find "$root/.agents" "$root/.claude" "$root/.codex" -type l -print0 2>/dev/null |
      while IFS= read -r -d '' link; do
        printf 'LINK %s -> %s\n' "$link" "$(readlink -- "$link")"
      done | sort
    sha256sum "$root/.claude/plugins/known_marketplaces.json" 2>/dev/null || true
  } > "$out"
}
new_home() {
  CURRENT_CASE="$1"
  HOME="$TEST_ROOT/home-$1"
  export HOME
  mkdir -p "$HOME"
}

run_installer() {
  local output="$1"
  shift
  set +e
  "$@" > "$output" 2>&1
  LAST_STATUS=$?
  set -e
  LAST_OUTPUT="$output"
}

make_fake_git() {
  local bin_dir="$1"
  mkdir -p "$bin_dir"
  cat > "$bin_dir/git" <<'FAKE_GIT'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$GIT_LOG"
command="$1"
shift
case "$command" in
  clone)
    url="$1"; target="$2"
    case "${CLONE_MODE:-first-success}:$url" in
      all-fail:*) exit 1 ;;
      first-success:https://ghfast.top/*)
        mkdir -p "$target/.git" "$target/cadence-init/skills/pre-check"
        printf 'fixture\n' > "$target/cadence-init/skills/pre-check/SKILL.md"
        printf '%s\n' "$url" > "$target/.fake-origin"
        exit 0 ;;
      first-success:*) exit 1 ;;
      *) exit 1 ;;
    esac
    ;;
  -C)
    repo="$1"; shift
    subcommand="$1"; shift
    state="$repo/.fake-origin"
    case "$subcommand" in
      rev-parse)
        if [[ "${1:-}" == "--is-inside-work-tree" ]]; then
          [[ -d "$repo/.git" ]] || exit 1
          printf 'true\n'
          exit 0
        fi
        if [[ "${1:-}" == "--abbrev-ref" ]]; then printf 'origin/main\n'; exit 0; fi
        ;;
      remote)
        case "$1 $2" in
          'get-url origin') cat "$state"; exit 0 ;;
          'set-url origin') printf '%s\n' "$3" > "$state"; exit 0 ;;
        esac
        ;;
      fetch)
        current_origin="$(cat "$state")"
        [[ "${UPDATE_MODE:-success}" == "rotate" && "$current_origin" == *ghfast.top* ]] && exit 1
        exit 0
        ;;
      pull)
        [[ "${UPDATE_MODE:-success}" != "pull-fail" ]] && exit 0
        exit 1
        ;;
      *) exit 0 ;;
    esac
    ;;
esac
exit 1
FAKE_GIT
  chmod +x "$bin_dir/git"
}

test_first_and_repeat_install() {
  local case_name=first-repeat git_bin first_target
  new_home "$case_name"
  git_bin="$HOME/fake-bin"; export GIT_LOG="$HOME/git.log"; : > "$GIT_LOG"
  make_fake_git "$git_bin"; PATH="$git_bin:$PATH"; export PATH

  CLONE_MODE=first-success bash "$INSTALLER" > "$HOME/first.out" 2>&1
  test -L "$HOME/.agents/skills/pre-check"
  test -L "$HOME/.claude/skills/pre-check"
  test -L "$HOME/.codex/skills/skills/pre-check"
  test "$(readlink "$HOME/.agents/skills/pre-check")" = "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check"
  test "$(readlink "$HOME/.claude/skills/pre-check")" = "$HOME/.agents/skills/pre-check"
  test "$(readlink "$HOME/.codex/skills/skills/pre-check")" = "$HOME/.agents/skills/pre-check"
  first_target="$(readlink "$HOME/.agents/skills/pre-check")"

  UPDATE_MODE=success CURRENT_ORIGIN="https://ghfast.top/https://github.com/michaelChe956/Cadence-skills.git" bash "$INSTALLER" > "$HOME/repeat.out" 2>&1
  test "$(readlink "$HOME/.agents/skills/pre-check")" = "$first_target"
  if [ -n "$(find "$HOME" -name '*.cadence-tmp.*' -print -quit)" ]; then
    echo "FAIL: 临时软链残留"
    exit 1
  fi
  assert_contains "$GIT_LOG" 'fetch --all'
  assert_contains "$GIT_LOG" 'pull --ff-only origin main'
  pass "$case_name"
}

test_clone_failure() {
  local case_name=clone-failure status=0
  new_home "$case_name"
  export GIT_LOG="$HOME/git.log"; : > "$GIT_LOG"
  make_fake_git "$HOME/fake-bin"; PATH="$HOME/fake-bin:$PATH"; export PATH
  set +e
  CLONE_MODE=all-fail bash "$INSTALLER" > "$HOME/out" 2>&1
  status=$?
  set -e
  test "$status" -ne 0
  assert_contains "$HOME/out" 'ghfast.top'
  assert_contains "$HOME/out" 'gh-proxy.com'
  assert_contains "$HOME/out" 'mirror.ghproxy.com'
  assert_contains "$HOME/out" '不使用直连 GitHub，也不提供离线安装'
  assert_not_exists "$HOME/.agents/Cadence-skills"
  pass "$case_name"
}

test_non_git_target() {
  local case_name=non-git status=0 before
  new_home "$case_name"
  mkdir -p "$HOME/.agents/Cadence-skills"
  printf 'keep\n' > "$HOME/.agents/Cadence-skills/user-file"
  before="$(sha256sum "$HOME/.agents/Cadence-skills/user-file")"
  set +e
  bash "$INSTALLER" > "$HOME/out" 2>&1
  status=$?
  set -e
  test "$status" -ne 0
  assert_contains "$HOME/out" '请删除 ~/.agents/Cadence-skills 后重新运行'
  test "$before" = "$(sha256sum "$HOME/.agents/Cadence-skills/user-file")"
  pass "$case_name"
}

test_update_rotation() {
  local case_name=update-rotation
  new_home "$case_name"
  export GIT_LOG="$HOME/git.log"; : > "$GIT_LOG"
  make_fake_git "$HOME/fake-bin"; PATH="$HOME/fake-bin:$PATH"; export PATH
  mkdir -p "$HOME/.agents/Cadence-skills/.git" "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check"
  printf 'fixture\n' > "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check/SKILL.md"
  printf '%s\n' 'https://ghfast.top/https://github.com/michaelChe956/Cadence-skills.git' > "$HOME/.agents/Cadence-skills/.fake-origin"
  UPDATE_MODE=rotate CURRENT_ORIGIN="https://ghfast.top/https://github.com/michaelChe956/Cadence-skills.git" bash "$INSTALLER" > "$HOME/out" 2>&1
  assert_contains "$GIT_LOG" 'remote set-url origin https://ghfast.top/https://github.com/michaelChe956/Cadence-skills.git'
  assert_contains "$GIT_LOG" 'remote set-url origin https://gh-proxy.com/https://github.com/michaelChe956/Cadence-skills.git'
  assert_contains "$GIT_LOG" 'fetch --all'
  assert_contains "$GIT_LOG" 'pull --ff-only origin main'
  test -L "$HOME/.agents/skills/pre-check"
  pass "$case_name"
}

test_conflict_orphan_uninstall_residue() {
  local case_name=conflict-uninstall
  new_home "$case_name"
  mkdir -p "$HOME/.agents/Cadence-skills/.git" "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check"
  printf 'fixture\n' > "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check/SKILL.md"
  printf '%s\n' 'https://ghfast.top/https://github.com/michaelChe956/Cadence-skills.git' > "$HOME/.agents/Cadence-skills/.fake-origin"
  mkdir -p "$HOME/.claude/skills/pre-check/user-dir" "$HOME/.agents/skills/user-skill" "$HOME/.codex/skills/skills"
  printf 'user\n' > "$HOME/.agents/skills/user-skill/keep"
  ln -s /tmp/not-cadence "$HOME/.claude/skills/non-managed"
  mkdir -p "$HOME/.agents/Cadence-skills/cadence-init/skills/managed-old"
  ln -s "$HOME/.agents/Cadence-skills/cadence-init/skills/managed-old" "$HOME/.agents/skills/managed-old"
  ln -s "$HOME/.agents/skills/managed-old" "$HOME/.claude/skills/managed-old"
  ln -s "$HOME/.agents/skills/managed-old" "$HOME/.codex/skills/skills/managed-old"
  mkdir -p "$HOME/.claude/plugins/marketplaces/cadence-skills-local"
  printf '{"cadence-skills-local":{}}\n' > "$HOME/.claude/plugins/known_marketplaces.json"
  export GIT_LOG="$HOME/git.log"; : > "$GIT_LOG"
  make_fake_git "$HOME/fake-bin"; PATH="$HOME/fake-bin:$PATH"; export PATH
  UPDATE_MODE=success CURRENT_ORIGIN="https://ghfast.top/https://github.com/michaelChe956/Cadence-skills.git" bash "$INSTALLER" > "$HOME/install.out" 2>&1
  test -d "$HOME/.claude/skills/pre-check/user-dir"
  test -L "$HOME/.claude/skills/non-managed"
  assert_contains "$HOME/install.out" 'cadence-skills-local'
  test ! -e "$HOME/.agents/skills/managed-old"
  test ! -e "$HOME/.claude/skills/managed-old"
  test ! -e "$HOME/.codex/skills/skills/managed-old"
  bash "$INSTALLER" --uninstall > "$HOME/uninstall.out" 2>&1
  test -e "$HOME/.agents/Cadence-skills"
  test -e "$HOME/.agents/skills/user-skill/keep"
  test -L "$HOME/.claude/skills/non-managed"
  test ! -e "$HOME/.agents/skills/pre-check"
  bash "$INSTALLER" --uninstall --delete-repo >/dev/null 2>&1
  assert_not_exists "$HOME/.agents/Cadence-skills"
  pass "$case_name"
}

test_dry_run_plan_and_uninstall() {
  local case_name=dry-run-plan dry_output real_output uninstall_output delete_repo_output before after uninstall_before uninstall_after delete_repo_before delete_repo_after
  new_home "$case_name"
  mkdir -p "$HOME/.agents/Cadence-skills/.git" \
    "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check" \
    "$HOME/.agents/Cadence-skills/cadence-init/skills/new-skill" \
    "$HOME/.agents/Cadence-skills/cadence-init/skills/managed-old" \
    "$HOME/.agents/Cadence-skills/cadence-init/skills/ordinary-file" \
    "$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.codex/skills/skills" \
    "$HOME/.claude/plugins/marketplaces"
  printf 'fixture\n' > "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check/SKILL.md"
  printf 'fixture\n' > "$HOME/.agents/Cadence-skills/cadence-init/skills/new-skill/SKILL.md"
  printf 'fixture\n' > "$HOME/.agents/Cadence-skills/cadence-init/skills/ordinary-file/SKILL.md"
  printf '%s\n' 'https://ghfast.top/https://github.com/michaelChe956/Cadence-skills.git' > "$HOME/.agents/Cadence-skills/.fake-origin"
  printf '{"cadence-skills-local":{}}\n' > "$HOME/.claude/plugins/known_marketplaces.json"
  ln -s "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check" "$HOME/.agents/skills/pre-check"
  ln -s "$HOME/.agents/skills/pre-check" "$HOME/.claude/skills/pre-check"
  ln -s "$HOME/.agents/skills/pre-check" "$HOME/.codex/skills/skills/pre-check"
  ln -s "$HOME/.agents/Cadence-skills/cadence-init/skills/managed-old" "$HOME/.agents/skills/managed-old"
  ln -s "$HOME/.agents/skills/managed-old" "$HOME/.claude/skills/managed-old"
  ln -s "$HOME/.agents/skills/managed-old" "$HOME/.codex/skills/skills/managed-old"
  mkdir -p "$HOME/.agents/skills/ordinary-dir" "$HOME/.claude/skills/ordinary-dir"
  printf 'keep\n' > "$HOME/.agents/skills/ordinary-file"
  printf 'keep\n' > "$HOME/.claude/skills/ordinary-dir/file"
  mkdir -p "$HOME/.agents/third-party/skills"
  ln -s "$HOME/.agents/third-party/skills/missing" "$HOME/.agents/skills/dangling-x"
  ln -s "$HOME/.agents/skills/dangling-x" "$HOME/.claude/skills/dangling-x"
  ln -s "$HOME/.agents/skills/dangling-x" "$HOME/.codex/skills/skills/dangling-x"
  export GIT_LOG="$HOME/git.log"; : > "$GIT_LOG"
  make_fake_git "$HOME/fake-bin"; PATH="$HOME/fake-bin:$PATH"; export PATH

  before="$TEST_ROOT/$case_name.before"; after="$TEST_ROOT/$case_name.after"
  dry_output="$TEST_ROOT/$case_name.dry-run.out"
  real_output="$TEST_ROOT/$case_name.real.out"
  snapshot_home "$HOME" "$before"
  HOME="$HOME" bash "$INSTALLER" --dry-run > "$dry_output" 2>&1
  snapshot_home "$HOME" "$after"
  cmp "$before" "$after"
  assert_contains "$dry_output" 'DRY-RUN CREATE'
  assert_contains "$dry_output" 'DRY-RUN KEEP'
  assert_contains "$dry_output" 'DRY-RUN REMOVE'
  assert_contains "$dry_output" 'DRY-RUN SKIP-WARN'
  assert_contains "$dry_output" 'DRY-RUN WARN-MANUAL'
  ! grep -E '(^|[[:space:]])(clone|fetch|pull|mkdir|ln|mv|rm)([[:space:]]|$)' "$dry_output"
  ! grep -E '(^|[[:space:]])(clone|fetch|pull)([[:space:]]|$)' "$GIT_LOG"

  HOME="$HOME" bash "$INSTALLER" > "$real_output" 2>&1
  grep '^DRY-RUN ' "$dry_output" |
    grep -E 'path=.*/(\.agents/skills|\.claude/skills|\.codex/skills/skills)/' |
    sed -E 's/^DRY-RUN /ACTION /; s/ reason=.*$//' | sort > "$TEST_ROOT/$case_name.plan-actions"
  grep '^ACTION ' "$real_output" |
    grep -E 'path=.*/(\.agents/skills|\.claude/skills|\.codex/skills/skills)/' |
    sed -E 's/^\[cadence\] //; s/ reason=.*$//' | sort > "$TEST_ROOT/$case_name.real-actions"
  diff -u "$TEST_ROOT/$case_name.plan-actions" "$TEST_ROOT/$case_name.real-actions"
  ! grep -E 'ACTION (REMOVE|REPLACE).*superpowers-x' "$real_output"

  uninstall_before="$TEST_ROOT/$case_name.uninstall-before"
  uninstall_after="$TEST_ROOT/$case_name.uninstall-after"
  uninstall_output="$TEST_ROOT/$case_name.uninstall-dry-run.out"
  delete_repo_before="$TEST_ROOT/$case_name.delete-repo-before"
  delete_repo_after="$TEST_ROOT/$case_name.delete-repo-after"
  delete_repo_output="$TEST_ROOT/$case_name.delete-repo-dry-run.out"
  snapshot_home "$HOME" "$uninstall_before"
  HOME="$HOME" bash "$INSTALLER" --dry-run --uninstall > "$uninstall_output" 2>&1
  snapshot_home "$HOME" "$uninstall_after"
  cmp "$uninstall_before" "$uninstall_after"
  ! grep -E 'DRY-RUN REMOVE.*(superpowers-x|dangling-x)' "$uninstall_output"
  snapshot_home "$HOME" "$delete_repo_before"
  HOME="$HOME" bash "$INSTALLER" --dry-run --uninstall --delete-repo > "$delete_repo_output" 2>&1
  snapshot_home "$HOME" "$delete_repo_after"
  cmp "$delete_repo_before" "$delete_repo_after"
  assert_contains "$delete_repo_output" 'DRY-RUN REMOVE-REPO'
  test -e "$HOME/.agents/Cadence-skills"
  pass "$case_name"
}

test_third_party_projection_survives_install() {
  local case_name=third-party-install git_bin
  new_home "$case_name"
  mkdir -p "$HOME/.agents/superpowers/skills/superpowers-x"
  mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.codex/skills/skills"
  ln -s "$HOME/.agents/superpowers/skills/superpowers-x" "$HOME/.agents/skills/superpowers-x"
  ln -s "$HOME/.agents/skills/superpowers-x" "$HOME/.claude/skills/superpowers-x"
  ln -s "$HOME/.agents/skills/superpowers-x" "$HOME/.codex/skills/skills/superpowers-x"
  git_bin="$HOME/fake-bin"; export GIT_LOG="$HOME/git.log"; : > "$GIT_LOG"
  make_fake_git "$git_bin"; PATH="$git_bin:$PATH"; export PATH

  CLONE_MODE=first-success bash "$INSTALLER" > "$HOME/install.out" 2>&1
  test -L "$HOME/.agents/skills/superpowers-x"
  test -L "$HOME/.claude/skills/superpowers-x"
  test -L "$HOME/.codex/skills/skills/superpowers-x"
  test "$(readlink "$HOME/.agents/skills/superpowers-x")" = "$HOME/.agents/superpowers/skills/superpowers-x"
  test "$(readlink "$HOME/.claude/skills/superpowers-x")" = "$HOME/.agents/skills/superpowers-x"
  test "$(readlink "$HOME/.codex/skills/skills/superpowers-x")" = "$HOME/.agents/skills/superpowers-x"
  pass "$case_name"
}

test_third_party_projection_survives_uninstall() {
  local case_name=third-party-uninstall
  new_home "$case_name"
  mkdir -p "$HOME/.agents/Cadence-skills/.git" "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check"
  printf 'fixture\n' > "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check/SKILL.md"
  mkdir -p "$HOME/.agents/superpowers/skills/superpowers-x"
  mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.codex/skills/skills"
  ln -s "$HOME/.agents/superpowers/skills/superpowers-x" "$HOME/.agents/skills/superpowers-x"
  ln -s "$HOME/.agents/skills/superpowers-x" "$HOME/.claude/skills/superpowers-x"
  ln -s "$HOME/.agents/skills/superpowers-x" "$HOME/.codex/skills/skills/superpowers-x"
  ln -s "$HOME/.agents/Cadence-skills/cadence-init/skills/pre-check" "$HOME/.agents/skills/pre-check"
  ln -s "$HOME/.agents/skills/pre-check" "$HOME/.claude/skills/pre-check"
  ln -s "$HOME/.agents/skills/pre-check" "$HOME/.codex/skills/skills/pre-check"

  bash "$INSTALLER" --uninstall > "$HOME/uninstall.out" 2>&1
  test -L "$HOME/.agents/skills/superpowers-x"
  test -L "$HOME/.claude/skills/superpowers-x"
  test -L "$HOME/.codex/skills/skills/superpowers-x"
  assert_not_exists "$HOME/.agents/skills/pre-check"
  assert_not_exists "$HOME/.claude/skills/pre-check"
  assert_not_exists "$HOME/.codex/skills/skills/pre-check"
  test -e "$HOME/.agents/Cadence-skills"
  pass "$case_name"
}

test_third_party_projection_survives_install
test_third_party_projection_survives_uninstall
test_dry_run_plan_and_uninstall
test_first_and_repeat_install
test_clone_failure
test_non_git_target
test_update_rotation
test_conflict_orphan_uninstall_residue
printf '全部 install.sh 隔离场景通过\n'
