#!/usr/bin/env bash

set -u

BACKUP_CALL_COUNT=0

backup_file() {
  local source_file=$1
  local backup_result=$2
  local backup_path
  local fail_on

  BACKUP_CALL_COUNT=$((BACKUP_CALL_COUNT + 1))
  case "$backup_result" in
    fail)
      return 1
      ;;
    fail-*)
      fail_on=${backup_result#fail-}
      if [ "$BACKUP_CALL_COUNT" -eq "$fail_on" ]; then
        return 1
      fi
      ;;
  esac
  backup_path="$source_file.cadence-backup-$(date +%Y%m%d%H%M%S)-$$"
  cp "$source_file" "$backup_path"
}

prepare_l0_candidate() {
  local target=$1
  local kernel=$2
  local candidate=$3

  python - "$target" "$kernel" "$candidate" <<'PY'
import pathlib
import re
import sys

target_path, kernel_path, candidate_path = map(pathlib.Path, sys.argv[1:])
target = target_path.read_bytes()
kernel = kernel_path.read_bytes()
lines = target.splitlines(keepends=True)
marker = re.compile(
    br"^<!-- cadence-managed:openspec-superpowers-routing:v[0-9]+:(start|end) -->\r?\n?$"
)
markers = [(index, marker.match(line).group(1)) for index, line in enumerate(lines) if marker.match(line)]

valid = (
    len(markers) == 2
    and markers[0][1] == b"start"
    and markers[1][1] == b"end"
    and markers[0][0] < markers[1][0]
)

if valid:
    start, end = markers[0][0], markers[1][0]
    candidate = b"".join(lines[:start]) + kernel + b"".join(lines[end + 1 :])
else:
    marker_indexes = {index for index, _ in markers}
    insertion_index = markers[0][0] if markers else len(lines)
    before = b"".join(line for index, line in enumerate(lines[:insertion_index]) if index not in marker_indexes)
    after = b"".join(line for index, line in enumerate(lines[insertion_index:], insertion_index) if index not in marker_indexes)
    if before and not before.endswith((b"\n", b"\r")):
        before += b"\n"
    candidate = before + kernel + after

candidate_path.write_bytes(candidate)
PY
}

apply_l0() {
  local root=$1
  local kernel=$2
  local mode=$3
  local decision=$4
  local backup_result=$5
  local claude="$root/CLAUDE.md"
  local agents="$root/AGENTS.md"
  local claude_candidate="$root/.CLAUDE.md.cadence-candidate-$$"
  local agents_candidate="$root/.AGENTS.md.cadence-candidate-$$"
  local claude_action=replace
  local agents_action=replace

  prepare_l0_candidate "$claude" "$kernel" "$claude_candidate"
  prepare_l0_candidate "$agents" "$kernel" "$agents_candidate"
  cmp -s "$claude" "$claude_candidate" && claude_action=skip
  cmp -s "$agents" "$agents_candidate" && agents_action=skip

  if [ "$claude_action" = skip ] && [ "$agents_action" = skip ]; then
    rm -f "$claude_candidate" "$agents_candidate"
    return 0
  fi
  if [ "$mode" = normal ] && [ "$decision" = no-response ]; then
    rm -f "$claude_candidate" "$agents_candidate"
    return 0
  fi
  if [ "$claude_action" = replace ]; then
    backup_file "$claude" "$backup_result" || {
      rm -f "$claude_candidate" "$agents_candidate"
      return 41
    }
  fi
  if [ "$agents_action" = replace ]; then
    backup_file "$agents" "$backup_result" || {
      rm -f "$claude_candidate" "$agents_candidate"
      return 41
    }
  fi

  if [ "$claude_action" = replace ]; then
    mv "$claude_candidate" "$claude"
  else
    rm -f "$claude_candidate"
  fi
  if [ "$agents_action" = replace ]; then
    mv "$agents_candidate" "$agents"
  else
    rm -f "$agents_candidate"
  fi
}

apply_l1() {
  local target=$1
  local source_file=$2
  local mode=$3
  local decision=$4
  local backup_result=$5
  local candidate

  if cmp -s "$target" "$source_file"; then
    return 0
  fi
  if [ "$mode" = normal ] && [ "$decision" = no-response ]; then
    return 0
  fi
  backup_file "$target" "$backup_result" || return 42
  candidate="$target.cadence-candidate-$$"
  cp "$source_file" "$candidate"
  mv "$candidate" "$target"
}

build_openspec_candidate() {
  local target=$1
  local template=$2
  local candidate=$3
  local remove_apply=$4

  python - "$target" "$template" "$candidate" "$remove_apply" <<'PY'
import pathlib
import sys

import yaml

target_path, template_path, candidate_path = map(pathlib.Path, sys.argv[1:4])
remove_apply = sys.argv[4] == "yes"


class InvalidYaml(Exception):
    pass


class TypeConflict(Exception):
    pass


def load(path):
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise InvalidYaml(str(error)) from error
    if not isinstance(value, dict):
        raise TypeConflict("配置根节点必须是 mapping")
    schema = value.get("schema")
    if isinstance(schema, (dict, list)):
        raise TypeConflict("schema 必须是 scalar")
    context = value.get("context")
    if context is not None and not isinstance(context, str):
        raise TypeConflict("context 必须是 string")
    rules = value.get("rules", {})
    if rules is None:
        rules = {}
        value["rules"] = rules
    if not isinstance(rules, dict):
        raise TypeConflict("rules 必须是 mapping")
    for artifact in ("proposal", "design", "specs", "tasks"):
        artifact_rules = rules.get(artifact)
        if artifact_rules is not None and (
            not isinstance(artifact_rules, list)
            or any(not isinstance(item, str) for item in artifact_rules)
        ):
            raise TypeConflict(f"rules.{artifact} 必须是字符串数组")
    return value


def merge_context(current, supplied):
    lines = []
    for source in (current or "", supplied or ""):
        for line in source.splitlines():
            if line not in lines:
                lines.append(line)
    return "\n".join(lines).rstrip() + "\n" if lines else ""


def merge_string_lists(current, supplied):
    result = []
    for item in [*(current or []), *(supplied or [])]:
        if item not in result:
            result.append(item)
    return result


try:
    current = load(target_path)
    supplied = load(template_path)
except InvalidYaml as error:
    print(error, file=sys.stderr)
    raise SystemExit(51)
except TypeConflict as error:
    print(error, file=sys.stderr)
    raise SystemExit(52)

if current.get("schema") is None and supplied.get("schema") is not None:
    current["schema"] = supplied["schema"]
current["context"] = merge_context(current.get("context"), supplied.get("context"))

current_rules = current.setdefault("rules", {})
supplied_rules = supplied.get("rules", {})
if remove_apply:
    current_rules.pop("apply", None)
for artifact in ("proposal", "design", "specs", "tasks"):
    current_rules[artifact] = merge_string_lists(current_rules.get(artifact), supplied_rules.get(artifact))

candidate_path.write_text(
    yaml.safe_dump(current, allow_unicode=True, sort_keys=False, default_flow_style=False),
    encoding="utf-8",
)
PY
}

validate_openspec_candidate() {
  local candidate=$1
  local openspec_bin=${CADENCE_OPENSPEC_BIN:-openspec}
  local validation_root
  local change_name=cadence-rule-config-validation
  local artifact
  local output_file

  validation_root=$(mktemp -d)
  mkdir -p "$validation_root/openspec"
  cp "$candidate" "$validation_root/openspec/config.yaml"
  if ! (cd "$validation_root" && "$openspec_bin" new change "$change_name" --description "Temporary candidate validation" >/dev/null); then
    rm -rf "$validation_root"
    return 1
  fi

  for artifact in proposal design specs tasks; do
    output_file="$validation_root/$artifact.json"
    if ! (cd "$validation_root" && "$openspec_bin" instructions "$artifact" --change "$change_name" --json > "$output_file"); then
      rm -rf "$validation_root"
      return 1
    fi
    if ! python - "$candidate" "$output_file" "$artifact" <<'PY'
import json
import pathlib
import sys

import yaml

candidate_path, output_path = map(pathlib.Path, sys.argv[1:3])
artifact = sys.argv[3]
config = yaml.safe_load(candidate_path.read_text(encoding="utf-8"))
payload = json.loads(output_path.read_text(encoding="utf-8"))

expected_context_lines = (config.get("context") or "").splitlines()
actual_context = payload.get("context") or ""
expected_rules = config.get("rules", {}).get(artifact, [])
actual_rules = payload.get("rules")

if any(line not in actual_context.splitlines() for line in expected_context_lines):
    raise SystemExit(1)
if actual_rules != expected_rules:
    raise SystemExit(1)
PY
    then
      rm -rf "$validation_root"
      return 1
    fi
  done
  rm -rf "$validation_root"
  return 0
}

apply_openspec() {
  local target=$1
  local template=$2
  local mode=$3
  local decision=$4
  local backup_result=$5
  local target_dir
  local candidate
  local build_status
  local remove_apply=no
  local has_apply=no
  local backup_created=no

  target_dir=$(dirname -- "$target")
  candidate=$(mktemp "$target_dir/.config.yaml.cadence-candidate-XXXXXX")

  if python - "$target" <<'PY'
import pathlib
import sys
import yaml

try:
    value = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
except yaml.YAMLError:
    raise SystemExit(2)
if isinstance(value, dict) and isinstance(value.get("rules"), dict) and "apply" in value["rules"]:
    raise SystemExit(0)
raise SystemExit(1)
PY
  then
    has_apply=yes
  fi

  if [ "$has_apply" = yes ] && [ "$mode" = normal ] && [ "$decision" = no-response ]; then
    rm -f "$candidate"
    return 0
  fi
  if [ "$has_apply" = yes ]; then
    backup_file "$target" "$backup_result" || {
      rm -f "$candidate"
      return 55
    }
    backup_created=yes
    remove_apply=yes
  fi

  if build_openspec_candidate "$target" "$template" "$candidate" "$remove_apply"; then
    build_status=0
  else
    build_status=$?
  fi
  if [ "$build_status" -eq 51 ] || [ "$build_status" -eq 52 ]; then
    rm -f "$candidate"
    if [ "$mode" = normal ]; then
      return 0
    fi
    backup_file "$target" "$backup_result" || return 55
    return "$build_status"
  fi
  if [ "$build_status" -ne 0 ]; then
    rm -f "$candidate"
    return "$build_status"
  fi

  if ! validate_openspec_candidate "$candidate"; then
    rm -f "$candidate"
    return 53
  fi

  if cmp -s "$target" "$candidate"; then
    rm -f "$candidate"
    return 0
  fi
  if [ "$backup_created" = no ]; then
    backup_file "$target" "$backup_result" || {
      rm -f "$candidate"
      return 55
    }
  fi

  if [ -n "${CADENCE_BEFORE_PUBLISH_HOOK-}" ]; then
    "$CADENCE_BEFORE_PUBLISH_HOOK" "$target" "$candidate"
  fi
  if ! mv "$candidate" "$target"; then
    rm -f "$candidate"
    return 54
  fi
}

case ${1-} in
  l0)
    shift
    apply_l0 "$@"
    ;;
  l1)
    shift
    apply_l1 "$@"
    ;;
  openspec)
    shift
    apply_openspec "$@"
    ;;
  *)
    printf '未知命令: %s\n' "${1-}" >&2
    exit 64
    ;;
esac
