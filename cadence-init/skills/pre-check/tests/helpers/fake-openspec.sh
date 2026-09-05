#!/usr/bin/env bash
# OpenSpec CLI 测试替身：记录调用并按客户端创建确定性投影。
set -u

_CALLS="${FAKE_OPENSPEC_CALLS:-}"
if [ -n "$_CALLS" ]; then
  printf '%s\n' "$*" >> "$_CALLS"
fi

if [ "${1:-}" = "--version" ]; then
  printf 'openspec 1.2.0\n'
  exit 0
fi

if [ "${1:-}" = "init" ] && [ "${2:-}" = "--tools" ]; then
  _tools="${3:-}"
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
      for _name in execute plan review verify brainstorm; do
        mkdir -p "$PWD/.pi/skills/openspec-$_name"
        printf 'pi openspec skill %s\n' "$_name" > "$PWD/.pi/skills/openspec-$_name/SKILL.md"
        printf 'pi openspec %s\n' "$_name" > "$PWD/.pi/prompts/opsx-$_name.md"
      done ;;
  esac
  case ",$_tools," in
    *,kimi,*)
      mkdir -p "$PWD/.kimi-code/skills"
      for _name in execute plan review verify brainstorm; do
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
