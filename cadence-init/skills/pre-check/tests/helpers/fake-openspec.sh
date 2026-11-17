#!/usr/bin/env bash
# OpenSpec CLI 测试替身：记录调用并按客户端创建确定性投影。
set -u

_CALLS="${FAKE_OPENSPEC_CALLS:-}"
if [ -n "$_CALLS" ]; then
  printf '%s\n' "$*" >> "$_CALLS"
fi
# 记录子进程环境里的 git url 改写，供测试断言镜像/加速代理是否生效（--version 探测不记）。
if [ -n "${FAKE_OPENSPEC_ENVLOG:-}" ] && [ "${1:-}" != "--version" ]; then
  printf '%s | GIT_CONFIG_COUNT=%s KEY_0=%s VALUE_0=%s\n' "$*" \
    "${GIT_CONFIG_COUNT:-}" "${GIT_CONFIG_KEY_0:-}" "${GIT_CONFIG_VALUE_0:-}" >> "$FAKE_OPENSPEC_ENVLOG"
fi

# 版本号：FAKE_OPENSPEC_VERSION 优先；否则 2.x 共享布局为 2.0.0，旧布局为 1.2.0。
if [ -n "${FAKE_OPENSPEC_VERSION:-}" ]; then
  _version="$FAKE_OPENSPEC_VERSION"
elif [ "${FAKE_OPENSPEC_SHARED_LAYOUT:-0}" = "1" ]; then
  _version="2.0.0"
else
  _version="1.2.0"
fi
# 2.1.0 起引入 --scope 与"默认全局作用域"；更早版本不认识 --scope。
_major="${_version%%.*}"
_rest="${_version#*.}"
_minor="${_rest%%.*}"
_scope_aware=0
if [ "$_major" -gt 2 ] || { [ "$_major" -eq 2 ] && [ "$_minor" -ge 1 ]; }; then
  _scope_aware=1
fi

if [ "${1:-}" = "--version" ]; then
  printf 'openspec %s\n' "$_version"
  exit 0
fi

if [ "${1:-}" = "init" ] && [ "${2:-}" = "--tools" ]; then
  _tools="${3:-}"
  _scope=""
  if [ "${4:-}" = "--scope" ]; then
    [ "$_scope_aware" -eq 1 ] || exit 1   # 旧版 CLI：未知选项
    _scope="${5:-}"
  elif [ "$#" -gt 3 ]; then
    exit 1
  fi
  # 模拟 init 退出 0 却没有写出任何投影的 CLI。
  [ "${FAKE_OPENSPEC_NOOP_INIT:-0}" = "1" ] && exit 0
  # 模拟 GitHub 不可达（2.1.0+ 的 init 要克隆 GitHub）：未经 FAKE_OPENSPEC_GITHUB_OK_VIA 指定的
  # 加速代理改写时，hang 表示一直挂起，fail 表示立即失败。
  if [ -n "${FAKE_OPENSPEC_UNREACHABLE:-}" ] && [ "$_scope_aware" -eq 1 ]; then
    case "${GIT_CONFIG_KEY_0:-}" in
      *"${FAKE_OPENSPEC_GITHUB_OK_VIA:-@@none@@}"*) ;;
      *)
        if [ "$FAKE_OPENSPEC_UNREACHABLE" = "hang" ]; then exec sleep 60; fi
        exit 1 ;;
    esac
  fi
  if [ "${FAKE_OPENSPEC_SHARED_LAYOUT:-0}" = "1" ]; then
    # 2.1.0+ 未显式 project 作用域时默认装进 $HOME（项目根不生成任何投影）。
    _root="$PWD"
    if [ "$_scope_aware" -eq 1 ] && [ "$_scope" != "project" ]; then
      _root="$HOME"
    fi
    # OpenSpec 2.x：所有工具共用 .agents/skills，marker 记录本次投影的工具并集。
    _shared_skills="$_root/.agents/skills"
    mkdir -p "$_shared_skills"
    for _name in apply-change archive-change explore propose sync-specs update-change; do
      mkdir -p "$_shared_skills/openspec-$_name"
      printf 'shared openspec skill %s\n' "$_name" > "$_shared_skills/openspec-$_name/SKILL.md"
    done
    _marker="$_shared_skills/.openspec-target"
    _union=""
    if [ -f "$_marker" ]; then
      _union="$(cat "$_marker")"
    fi
    _rest="$_tools"
    while [ -n "$_rest" ]; do
      _tool="${_rest%%,*}"
      case "$_rest" in
        *,*) _rest="${_rest#*,}" ;;
        *) _rest="" ;;
      esac
      [ -n "$_tool" ] && _union="$_union
$_tool"
    done
    printf '%s\n' "$_union" | awk 'NF { print $1 }' | sort -u > "$_marker"
    case ",$_tools," in
      *,claude,*)
        mkdir -p "$_root/.claude/skills"
        for _name in apply-change archive-change explore propose sync-specs update-change; do
          _link="$_root/.claude/skills/openspec-$_name"
          rm -f "$_link" 2>/dev/null
          [ -e "$_link" ] && rm -rf "$_link"
          ln -s "../../.agents/skills/openspec-$_name" "$_link"
        done ;;
    esac
    exit 0
  fi
  # ready 端禁止被错误覆盖，专门锁定 init 参数必须是缺失端集合。
  case ",$_tools," in
    *,claude,*)
      _claude_ready=0
      [ -d "$PWD/.claude/commands/opsx" ] && _claude_ready=1
      if [ "$_claude_ready" -eq 0 ] && [ -d "$PWD/.claude/skills" ]; then
        for _entry in "$PWD/.claude/skills/openspec-"*; do
          [ -d "$_entry" ] || continue
          _claude_ready=1
          break
        done
      fi
      [ "$_claude_ready" -eq 1 ] && exit 42
      mkdir -p "$PWD/.claude/commands/opsx"
      printf 'claude openspec projection\n' > "$PWD/.claude/commands/opsx/propose.md" ;;
  esac
  case ",$_tools," in
    *,codex,*)
      _codex_ready=0
      if [ -d "$PWD/.agents/skills" ]; then
        for _entry in "$PWD/.agents/skills/openspec-"*; do
          [ -d "$_entry" ] || continue
          _codex_ready=1
          break
        done
      fi
      [ "$_codex_ready" -eq 1 ] && exit 42
      mkdir -p "$PWD/.agents/skills/openspec-execute"
      printf 'codex openspec projection\n' > "$PWD/.agents/skills/openspec-execute/SKILL.md" ;;
  esac
  case ",$_tools," in
    *,pi,*)
      mkdir -p "$PWD/.pi/skills" "$PWD/.pi/prompts"
      for _name in execute plan review verify brainstorm update-change; do
        mkdir -p "$PWD/.pi/skills/openspec-$_name"
        printf 'pi openspec skill %s\n' "$_name" > "$PWD/.pi/skills/openspec-$_name/SKILL.md"
        printf 'pi openspec %s\n' "$_name" > "$PWD/.pi/prompts/opsx-$_name.md"
      done ;;
  esac
  case ",$_tools," in
    *,kimi,*)
      mkdir -p "$PWD/.kimi-code/skills"
      for _name in execute plan review verify brainstorm update-change; do
        mkdir -p "$PWD/.kimi-code/skills/openspec-$_name"
        printf 'kimi openspec %s\n' "$_name" > "$PWD/.kimi-code/skills/openspec-$_name/SKILL.md"
      done ;;
  esac
  exit 0
fi

if [ "${1:-}" = "update" ] && [ "$#" -eq 1 ]; then
  [ "${FAKE_OPENSPEC_UPDATE_FAIL:-0}" = "1" ] && exit 1
  exit 0
fi
exit 2
