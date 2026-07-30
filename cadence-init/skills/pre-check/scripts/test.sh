#!/usr/bin/env bash
# Cadence pre-check 可重复冒烟验证脚本。
# 全部使用只读/无副作用命令：仅跑 check（不安装、不查远端 latest），
# 不执行 run 或 --upgrade（会下载/改全局环境）。
# 用法: bash test.sh   （任一断言失败即以非零退出）

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRE_CHECK="$SCRIPT_DIR/pre-check.sh"

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
bash "$PRE_CHECK" check 2>/dev/null > /tmp/precheck_smoke_default.json
_rc=$?
python3 -m json.tool /tmp/precheck_smoke_default.json >/dev/null 2>&1
assert_true "check(default) stdout 为合法 JSON（exit=$_rc）" "$?"

bash "$PRE_CHECK" check --mirror cn 2>/dev/null > /tmp/precheck_smoke_cn.json
_rc=$?
python3 -m json.tool /tmp/precheck_smoke_cn.json >/dev/null 2>&1
assert_true "check(cn) stdout 为合法 JSON（exit=$_rc）" "$?"

# --- 3. JSON 含 overall/steps/next_actions/hints.superpowers_git ---
_keys="$(python3 -c "
import json
d = json.load(open('/tmp/precheck_smoke_default.json'))
ok = ('overall' in d and 'steps' in d and 'next_actions' in d
      and 'hints' in d and 'superpowers_git' in d['hints'])
print('yes' if ok else 'no')
" 2>/dev/null)"
assert_eq "JSON 含 overall/steps/next_actions/hints.superpowers_git" "yes" "$_keys"

# --- 4. next_actions 恰为固定四项 ---
_na="$(python3 -c "
import json
d = json.load(open('/tmp/precheck_smoke_default.json'))
print(json.dumps(d.get('next_actions')))
" 2>/dev/null)"
assert_eq "next_actions 恰为固定四项" \
  '["superpowers-sync", "openspec-clients", "playwright-optional", "apikey-placeholder"]' "$_na"

# --- 5. default/cn 镜像 hints.superpowers_git 正确 ---
_git_default="$(python3 -c "
import json
print(json.load(open('/tmp/precheck_smoke_default.json'))['hints']['superpowers_git'])
" 2>/dev/null)"
assert_eq "default 镜像 hints.superpowers_git" "https://github.com/obra/superpowers" "$_git_default"

_git_cn="$(python3 -c "
import json
print(json.load(open('/tmp/precheck_smoke_cn.json'))['hints']['superpowers_git'])
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

# --- 汇总 ---
_total=$((PASS_COUNT + FAIL_COUNT))
printf '%s/%s PASS\n' "$PASS_COUNT" "$_total"
if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
exit 0
