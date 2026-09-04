#!/usr/bin/env bash
# 冻结旧 pre-check 实现的隔离基线；不接触真实 HOME、真实网络或仓库根。
set -u

TEST_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BASELINE_DIR="$TEST_DIR/baselines/precheck-v1"
SCRIPT="$TEST_DIR/../scripts/pre-check.sh"
SKILL_MD="$TEST_DIR/../SKILL.md"
ROOT="$(mktemp -d "${TMPDIR:-/tmp}/precheck-baseline.XXXXXX")"
PROJECT="$ROOT/project"
HOME_DIR="$ROOT/home"
BIN="$ROOT/bin"
REMOTE="$ROOT/remote.git"
REPORT="$ROOT/report.json"
STDERR="$ROOT/stderr.log"
trap 'rm -rf "$ROOT"' EXIT HUP INT TERM

mkdir -p "$PROJECT" "$HOME_DIR" "$BIN"

# fake CLI 仅返回固定版本；旧脚本不会访问网络。
cat > "$BIN/npx" <<'FAKE_NPX'
#!/usr/bin/env bash
printf '10.9.0\n'
FAKE_NPX
cat > "$BIN/uvx" <<'FAKE_UVX'
#!/usr/bin/env bash
printf 'uvx 0.4.0\n'
FAKE_UVX
cat > "$BIN/ast-grep" <<'FAKE_AST_GREP'
#!/usr/bin/env bash
printf 'ast-grep 0.40.0\n'
FAKE_AST_GREP
cat > "$BIN/codegraph" <<'FAKE_CODEGRAPH'
#!/usr/bin/env bash
printf 'codegraph 0.8.0\n'
FAKE_CODEGRAPH
cat > "$BIN/openspec" <<'FAKE_OPENSPEC'
#!/usr/bin/env bash
printf 'openspec 1.2.0\n'
FAKE_OPENSPEC
cat > "$BIN/pi" <<'FAKE_PI'
#!/usr/bin/env bash
if [ "${1:-}" = "list" ]; then
  printf 'pi-mcp-adapter\n'
  exit 0
fi
exit 1
FAKE_PI
chmod +x "$BIN"/*

# 预置四端 OpenSpec 投影和一个非目标项目条目。
mkdir -p "$PROJECT/.claude/commands/opsx" \
  "$PROJECT/.claude/skills/openspec-brainstorm" \
  "$PROJECT/.agents/skills/openspec-execute" \
  "$PROJECT/.pi/skills" "$PROJECT/.pi/prompts" \
  "$PROJECT/.kimi-code/skills"
printf '%s\n' '# fixture propose' > "$PROJECT/.claude/commands/opsx/propose.md"
printf '%s\n' '# fixture skill' > "$PROJECT/.claude/skills/openspec-brainstorm/SKILL.md"
printf '%s\n' '# fixture execute' > "$PROJECT/.agents/skills/openspec-execute/SKILL.md"
for name in brainstorm write-plan execute review verify; do
  printf '# pi %s\n' "$name" > "$PROJECT/.pi/skills/$name.md"
  printf '# pi prompt %s\n' "$name" > "$PROJECT/.pi/prompts/$name.md"
  printf '# kimi %s\n' "$name" > "$PROJECT/.kimi-code/skills/$name.md"
done
printf '%s\n' 'project non-target sentinel' > "$PROJECT/project-sentinel.txt"

# 预置有效的本地 Superpowers Git worktree，origin 指向本地 bare remote。
git init --bare -q "$REMOTE"
git init -q -b main "$HOME_DIR/.agents/superpowers"
git -C "$HOME_DIR/.agents/superpowers" config user.email fixture@example.invalid
git -C "$HOME_DIR/.agents/superpowers" config user.name fixture
git -C "$HOME_DIR/.agents/superpowers" remote add origin "$REMOTE"
mkdir -p "$HOME_DIR/.agents/superpowers/skills"
SKILLS='brainstorming writing-plans executing-plans subagent-driven-development test-driven-development systematic-debugging verification-before-completion requesting-code-review receiving-code-review finishing-a-development-branch using-superpowers dispatching-parallel-agents creating-skills testing-skills'
for name in $SKILLS; do
  mkdir -p "$HOME_DIR/.agents/superpowers/skills/$name"
  printf '# %s\n' "$name" > "$HOME_DIR/.agents/superpowers/skills/$name/SKILL.md"
done
git -C "$HOME_DIR/.agents/superpowers" add skills
git -C "$HOME_DIR/.agents/superpowers" commit -qm 'fixture superpowers'
git -C "$HOME_DIR/.agents/superpowers" push -q -u origin main

# 预置四层 14 条直连软链；额外 HOME sentinel 用于非目标树校验。
for layer in \
  "$HOME_DIR/.agents/skills" \
  "$HOME_DIR/.codex/skills/skills" \
  "$HOME_DIR/.claude/skills" \
  "$HOME_DIR/.pi/agent/skills"; do
  mkdir -p "$layer"
  for name in $SKILLS; do
    ln -s "$HOME_DIR/.agents/superpowers/skills/$name" "$layer/$name"
  done
done
printf '%s\n' 'home non-target sentinel' > "$HOME_DIR/home-sentinel.txt"

# 前置门禁要求的旧脚本 run --no-interrupt：工作目录必须是隔离项目。
(
  cd "$PROJECT" || exit 1
  HOME="$HOME_DIR" PATH="$BIN:$PATH" bash "$SCRIPT" run --no-interrupt > "$REPORT" 2> "$STDERR"
)
RC=$?
[ "$RC" -eq 0 ] || { cat "$STDERR" >&2; cat "$REPORT" >&2; exit "$RC"; }

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

# 按固定格式生成项目/HOME 文件、四层软链和 Git 三字段快照。
snapshot_tree() {
  _out="$1"
  : > "$_out"
  (
    cd "$PROJECT" || exit 1
    find . -type f -not -path './.git/*' -not -path './.precheck-*' | LC_ALL=C sort
  ) | while IFS= read -r _path; do
    printf 'file project %s %s\n' "${_path#./}" "$(sha256_file "$PROJECT/$_path")" >> "$_out"
  done
  (
    cd "$HOME_DIR" || exit 1
    find . -type f -not -path './.git/*' -not -path './.agents/superpowers/.git/*' -not -path './.precheck-*' | LC_ALL=C sort
  ) | while IFS= read -r _path; do
    printf 'file home %s %s\n' "${_path#./}" "$(sha256_file "$HOME_DIR/$_path")" >> "$_out"
  done
  for _layer in \
    "$HOME_DIR/.agents/skills" \
    "$HOME_DIR/.codex/skills/skills" \
    "$HOME_DIR/.claude/skills" \
    "$HOME_DIR/.pi/agent/skills"; do
    [ -d "$_layer" ] || continue
    for _link in "$_layer"/*; do
      [ -L "$_link" ] || continue
      _raw="$(readlink "$_link")"
      case "$_raw" in
        /*) _resolved="$_raw" ;;
        *) _resolved="$(cd "$(dirname "$_link")" && pwd -P)/$_raw" ;;
      esac
      printf 'link %s %s readlink=%s resolved=%s\n' \
        "${_layer#$HOME_DIR/}" "${_link##*/}" "$_raw" "$_resolved" >> "$_out"
    done
  done
  printf 'git origin %s\n' "$(git -C "$HOME_DIR/.agents/superpowers" remote get-url origin)" >> "$_out"
  printf 'git branch %s\n' "$(git -C "$HOME_DIR/.agents/superpowers" rev-parse --abbrev-ref HEAD)" >> "$_out"
  printf 'git head %s\n' "$(git -C "$HOME_DIR/.agents/superpowers" rev-parse HEAD)" >> "$_out"
}

# 将随机隔离根转换为稳定占位符，供 Task 8 old/new 快照文本对照复用。
normalize_snapshot_file() {
  _source="$1"
  _destination="$2"
  _isolation_root="$3"
  sed "s|$_isolation_root|<ISOLATION_ROOT>|g" "$_source" > "$_destination"
}

mkdir -p "$BASELINE_DIR"
# 基线目录只写 tree/README；不覆盖既有基线，避免后续任务误替换。
if [ -e "$BASELINE_DIR/tree.txt" ] || [ -e "$BASELINE_DIR/README.md" ]; then
  echo '基线已存在，拒绝覆盖：precheck-v1' >&2
  exit 3
fi
snapshot_tree "$ROOT/tree.txt"
cp "$ROOT/tree.txt" "$BASELINE_DIR/tree.txt"
SCRIPT_SHA="$(sha256_file "$SCRIPT")"
SKILL_SHA="$(sha256_file "$SKILL_MD")"
GIT_HEAD="$(git -C "$HOME_DIR/.agents/superpowers" rev-parse HEAD)"
cat > "$BASELINE_DIR/README.md" <<EOF_README
# pre-check v1 旧实现基线

## 采集边界

- 采集日期：2026-09-04
- 旧脚本：\`cadence-init/skills/pre-check/scripts/pre-check.sh\`
- 旧脚本 SHA-256：\`$SCRIPT_SHA\`
- 旧 \`SKILL.md\`：\`cadence-init/skills/pre-check/SKILL.md\`
- 旧 \`SKILL.md\` SHA-256：\`$SKILL_SHA\`
- 隔离根目录：仓库外临时目录（本次为 \`$ROOT\`，脚本结束自动删除）
- 真实 HOME、真实 API Key、真实网络：均未使用

## Fixture 配置

- 项目根：临时 \`project/\`，预置四端 OpenSpec 投影：Claude/Codex、Pi 的 5 个 skill + 5 个 prompt、Kimi 的 5 个 skill。
- 项目非目标 sentinel：\`project-sentinel.txt\`。
- Superpowers：临时 \`home/.agents/superpowers/\` 有效 Git worktree；\`origin\` 为同一临时目录内的 bare remote，分支为 \`main\`，HEAD 为 \`$GIT_HEAD\`。
- 软链：\`~/.agents/skills\`、\`~/.codex/skills/skills\`、\`~/.claude/skills\`、\`~/.pi/agent/skills\` 各预置 14 条直连 Superpowers 源的软链。
- HOME 非目标 sentinel：\`home-sentinel.txt\`。
- fake CLI：\`npx 10.9.0\`、\`uvx 0.4.0\`、\`ast-grep 0.40.0\`、\`codegraph 0.8.0\`、\`openspec 1.2.0\`；fake \`pi list\` 报告 \`pi-mcp-adapter\`。

## 运行命令

\`HOME=<isolated-home> PATH=<fake-bin>:\$PATH bash <absolute-pre-check.sh> run --no-interrupt\`，cwd 为隔离项目根。
旧脚本 stdout 保存为临时报告并未写入快照；stderr、临时目录和测试日志均排除。

## 快照格式与排除项

- 文件：\`file <scope> <relative-path> <sha256>\`。
- 软链：\`link <layer> <name> readlink=<原始 readlink> resolved=<最终绝对目标>\`。
- Git：\`git origin ...\`、\`git branch ...\`、\`git head ...\`。
- 排除：各 Git 元数据目录、报告、临时目录、时间戳备份和测试日志；非目标项目/HOME 条目保留。

## 目标白名单与冻结口径

后续兼容性测试必须复用同一 fixture 配置与同一快照器。四端 OpenSpec 投影、Superpowers Git 和四层软链是已预置的完成态，旧脚本首跑预期为零写入且 \`overall=success\`；后续实现首跑以此基线做 1:1 对照。四端投影目标白名单为：\`.claude/commands/opsx/\`、\`.claude/skills/openspec-*\`、\`.agents/skills/openspec-*\`、\`.pi/skills/\`、\`.pi/prompts/\`、\`.kimi-code/skills/\`；HOME 侧白名单为 Superpowers 源目录和上述四层软链。不得以新实现快照覆盖本基线；如与审核结论冲突，保留此证据并在 Task 8 标注差异原因。
EOF_README
printf 'baseline captured: %s\n' "$BASELINE_DIR"
printf 'old_script_sha256=%s\n' "$SCRIPT_SHA"
printf 'skill_sha256=%s\n' "$SKILL_SHA"
printf 'tree_lines=%s\n' "$(wc -l < "$BASELINE_DIR/tree.txt" | tr -d ' ')"
