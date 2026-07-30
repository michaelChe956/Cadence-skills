#!/usr/bin/env bash
# Cadence pre-check 可重复冒烟验证脚本。
# 全部使用只读/无副作用命令：仅跑 check（不安装、不查远端 latest），
# 不执行 run 或 --upgrade（会下载/改全局环境）。
# 用法: bash test.sh   （任一断言失败即以非零退出）

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRE_CHECK="$SCRIPT_DIR/pre-check.sh"

# 临时目录：全部冒烟输出写入此目录，退出时自动清理，不在 /tmp 留固定文件
SMOKE_DIR="$(mktemp -d -t precheck-smoke.XXXXXX)"
trap 'rm -rf "$SMOKE_DIR"' EXIT
export SMOKE_DIR

PASS_COUNT=0
FAIL_COUNT=0

# check <描述> <实际值...>：最后两个参数为 <期望> <实际>；或单参数形式由调用方给 0/1
assert_eq() { # assert_eq <描述> <期望> <实际>
  _desc="$1"; _want="$2"; _got="$3"
  if [ "$_want" = "$_got" ]; then
    printf 'PASS %s\n' "$_desc"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    printf 'FAIL %s（期望 %s，实际 %s）\n' "$_desc" "$_want" "$_got"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

assert_true() { # assert_true <描述> <0/1>
  _desc="$1"; _rc="$2"
  if [ "$_rc" = "0" ]; then
    printf 'PASS %s\n' "$_desc"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    printf 'FAIL %s\n' "$_desc"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

# --- 1. 语法检查 ---
bash -n "$PRE_CHECK" 2>/dev/null
assert_true "bash -n pre-check.sh 语法通过" "$?"

# --- 2. check（default 与 cn）stdout 可被 python3 -m json.tool 解析 ---
bash "$PRE_CHECK" check 2>/dev/null > "$SMOKE_DIR/default.json"
_rc=$?
python3 -m json.tool "$SMOKE_DIR/default.json" >/dev/null 2>&1
assert_true "check(default) stdout 为合法 JSON（exit=$_rc）" "$?"

bash "$PRE_CHECK" check --mirror cn 2>/dev/null > "$SMOKE_DIR/cn.json"
_rc=$?
python3 -m json.tool "$SMOKE_DIR/cn.json" >/dev/null 2>&1
assert_true "check(cn) stdout 为合法 JSON（exit=$_rc）" "$?"

# --- 3. JSON 含 overall/steps/next_actions/hints.superpowers_git ---
_keys="$(python3 -c "
import json, os
d = json.load(open(os.environ['SMOKE_DIR'] + '/default.json'))
ok = ('overall' in d and 'steps' in d and 'next_actions' in d
      and 'hints' in d and 'superpowers_git' in d['hints'])
print('yes' if ok else 'no')
" 2>/dev/null)"
assert_eq "JSON 含 overall/steps/next_actions/hints.superpowers_git" "yes" "$_keys"

# --- 4. next_actions 恰为固定四项 ---
_na="$(python3 -c "
import json, os
d = json.load(open(os.environ['SMOKE_DIR'] + '/default.json'))
print(json.dumps(d.get('next_actions')))
" 2>/dev/null)"
assert_eq "next_actions 恰为固定四项" \
  '["superpowers-sync", "openspec-clients", "playwright-optional", "apikey-placeholder"]' "$_na"

# --- 5. default/cn 镜像 hints.superpowers_git 正确 ---
_git_default="$(python3 -c "
import json, os
print(json.load(open(os.environ['SMOKE_DIR'] + '/default.json'))['hints']['superpowers_git'])
" 2>/dev/null)"
assert_eq "default 镜像 hints.superpowers_git" "https://github.com/obra/superpowers" "$_git_default"

_git_cn="$(python3 -c "
import json, os
print(json.load(open(os.environ['SMOKE_DIR'] + '/cn.json'))['hints']['superpowers_git'])
" 2>/dev/null)"
assert_eq "cn 镜像 hints.superpowers_git" "https://gitee.com/michaelChe-World/superpowers.git" "$_git_cn"

# --- 6. 未知 mirror 退出码非零 ---
bash "$PRE_CHECK" check --mirror nonexistent >/dev/null 2>&1
[ $? -ne 0 ]
assert_true "未知 mirror --mirror nonexistent 退出码非零" "$?"

# --- 7. check --upgrade 互斥退出码非零 ---
bash "$PRE_CHECK" check --upgrade >/dev/null 2>&1
[ $? -ne 0 ]
assert_true "check --upgrade 互斥退出码非零" "$?"

# --- 8. 无 sort -V / declare -A / grep -P / sed -i 实际调用（排除注释行） ---
_bad8="$(grep -v '^[[:space:]]*#' "$PRE_CHECK" | grep -cE 'sort +-V|declare +-A|grep +-P|sed +-i' || true)"
assert_eq "无 sort -V/declare -A/grep -P/sed -i 实际调用" "0" "$_bad8"

# --- 9. 无全局配置写入（npm config set / git config --global / .npmrc / uv.toml） ---
_bad9="$(grep -v '^[[:space:]]*#' "$PRE_CHECK" | grep -cE 'npm +config +set|git +config +--global|\.npmrc|uv\.toml' || true)"
assert_eq "无 npm config set/git config --global/.npmrc/uv.toml 写入" "0" "$_bad9"

# --- 10. check 模式 stderr 无“正在安装”（不安装） ---
_inst="$(bash "$PRE_CHECK" check 2>&1 >/dev/null | grep -c '正在安装' || true)"
assert_eq "check 模式 stderr 无“正在安装”" "0" "$_inst"

# --- 11. SKILL.md 流程级：不 cd 进 skill 目录、报告独占、命令自包含 ---
SKILL_MD="$SCRIPT_DIR/../SKILL.md"

# 11a. SKILL.md 不出现相对脚本调用 "bash scripts/pre-check.sh"（应用 <PRE_CHECK_SH> 绝对路径）
_bad11a="$(grep -c 'bash scripts/pre-check\.sh' "$SKILL_MD" || true)"
assert_eq "SKILL.md 无 bash scripts/pre-check.sh 相对调用" "0" "$_bad11a"

# 11b. SKILL.md 不出现 "cd \$HOME/.agents/superpowers"（应用 git -C 自包含）
_bad11b="$(grep -c 'cd "\$HOME/\.agents/superpowers"' "$SKILL_MD" || true)"
assert_eq "SKILL.md 无 cd 进 superpowers 目录（用 git -C）" "0" "$_bad11b"

# 11c. SKILL.md 引导使用独占报告路径（含时间戳占位），不依赖固定相对 ./.precheck-report.json
_bad11c="$(grep -c '\./\.precheck-report\.json' "$SKILL_MD" || true)"
assert_eq "SKILL.md 无固定相对 ./.precheck-report.json（用独占路径）" "0" "$_bad11c"

# 11d. SKILL.md 含 <PROJECT_ROOT> 与 <REPORT> 占位（自包含绝对路径约定）
_has11d="$(grep -c 'PROJECT_ROOT' "$SKILL_MD" || true)"
[ "$_has11d" -gt 0 ]
assert_true "SKILL.md 含 <PROJECT_ROOT> 绝对路径约定" "$?"

# --- 12. 跨 cwd + 独占报告：在不同 cwd 执行脚本，报告写各自独占路径、互不影响 ---
# 模拟 Agent 独立 shell：在两个不同目录用绝对路径调用脚本，报告写到项目根独占路径
_PROJ_A="$(mktemp -d -t precheck-projA.XXXXXX)"
_PROJ_B="$(mktemp -d -t precheck-projB.XXXXXX)"
_REP_A="$_PROJ_A/.precheck-report-a.json"
_REP_B="$_PROJ_B/.precheck-report-b.json"
bash -c "cd '$_PROJ_A' && bash '$PRE_CHECK' check > '$_REP_A'" 2>/dev/null
bash -c "cd '$_PROJ_B' && bash '$PRE_CHECK' check > '$_REP_B'" 2>/dev/null
# 两报告都应存在且为合法 JSON（独占、互未覆盖）
_ok12=0
python3 -m json.tool "$_REP_A" >/dev/null 2>&1 && python3 -m json.tool "$_REP_B" >/dev/null 2>&1 && _ok12=1
assert_eq "跨 cwd 独占报告各自可解析（互未覆盖）" "1" "$_ok12"

# 12b. 跨独立 shell 读取：在第三个 shell（不同 cwd）用绝对路径读 _REP_A，
# 断言 JSON 可读且 overall 为合法枚举（不强制 success——check 不安装，受限 PATH/工具缺失时为 partial）
_ov12="$(bash -c "cd / && python3 -c \"import json;print(json.load(open('$_REP_A'))['overall'])\"" 2>/dev/null)"
case "$_ov12" in
  success|partial|failed) _ov12_ok=1 ;;
  *) _ov12_ok=0 ;;
esac
assert_eq "独立 shell（不同 cwd）按绝对路径读报告 overall 为合法枚举" "1" "$_ov12_ok"

# 12c. skill 目录不被写入报告（脚本绝对路径调用，报告写 /tmp）
[ ! -e "$SCRIPT_DIR/../.precheck-report.json" ] && [ ! -e "$SCRIPT_DIR/.precheck-report.json" ]
assert_true "skill 目录无报告残留（不污染源码）" "$?"

rm -rf "$_PROJ_A" "$_PROJ_B"

# --- 13. 同秒并发 mktemp 唯一性（date +%s 会重名，mktemp 原子唯一） ---
_m1="$(mktemp -t precheck-report.XXXXXX.json)"
_m2="$(mktemp -t precheck-report.XXXXXX.json)"
_m3="$(mktemp -t precheck-report.XXXXXX.json)"
_uniq=0
[ "$_m1" != "$_m2" ] && [ "$_m2" != "$_m3" ] && [ "$_m1" != "$_m3" ] && _uniq=1
assert_eq "同秒三次 mktemp 生成路径互不相同" "1" "$_uniq"
rm -f "$_m1" "$_m2" "$_m3"

# --- 14. 带空格路径加引号可用（模拟含空格的项目路径） ---
_SP="$(mktemp -d -t 'precheck space.XXXXXX')"
_SPREP="$(mktemp "$_SP/report.XXXXXX.json")"
bash -c "bash '$PRE_CHECK' check > \"$_SPREP\"" 2>/dev/null
_sp_ok=0
python3 -m json.tool "$_SPREP" >/dev/null 2>&1 && _sp_ok=1
assert_eq "带空格路径加引号写报告并解析" "1" "$_sp_ok"

# --- 15. 含空格的项目根 cd（模拟 cd "<PROJECT_ROOT>" && 相对路径检查） ---
cd_ok=0
bash -c "cd \"$_SP\" && mkdir -p .claude/commands/opsx && touch .claude/commands/opsx/propose.md && test -f .claude/commands/opsx/propose.md" && cd_ok=1
assert_eq "含空格项目根 cd 后相对路径检查可用" "1" "$cd_ok"
rm -rf "$_SP"

# --- 汇总 ---
_total=$((PASS_COUNT + FAIL_COUNT))
printf '%s/%s PASS\n' "$PASS_COUNT" "$_total"
if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
exit 0
