#!/usr/bin/env bash
# OpenSpec CLI 测试替身：记录调用并按客户端创建确定性投影。
set -u

_CALLS="${FAKE_OPENSPEC_CALLS:-}"
if [ -n "$_CALLS" ]; then
  printf '%s\n' "$*" >> "$_CALLS"
fi

if [ "${1:-}" = "--version" ]; then
  if [ "${FAKE_OPENSPEC_SHARED_LAYOUT:-0}" = "1" ]; then
    printf 'openspec 2.0.0\n'
  else
    printf 'openspec 1.2.0\n'
  fi
  exit 0
fi

if [ "${1:-}" = "init" ] && [ "${2:-}" = "--tools" ]; then
  _tools="${3:-}"
  if [ "${FAKE_OPENSPEC_SHARED_LAYOUT:-0}" = "1" ]; then
    # OpenSpec 2.x：所有工具共用 .agents/skills，marker 记录本次投影的工具并集。
    _shared_skills="$PWD/.agents/skills"
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
        mkdir -p "$PWD/.claude/skills"
        for _name in apply-change archive-change explore propose sync-specs update-change; do
          _link="$PWD/.claude/skills/openspec-$_name"
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
