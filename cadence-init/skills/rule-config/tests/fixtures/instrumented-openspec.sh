#!/usr/bin/env bash

set -u

printf '%s\n' "$*" >> "$CADENCE_OPENSPEC_LOG"

if [ -n "${CADENCE_EXPECT_BACKUP_TARGET-}" ] && ! compgen -G "$CADENCE_EXPECT_BACKUP_TARGET.cadence-backup-*" >/dev/null; then
  printf 'expected backup was not created before instructions: %s\n' "$CADENCE_EXPECT_BACKUP_TARGET" >&2
  exit 73
fi

if [ "${1-}" = instructions ] && [ "${2-}" = "${CADENCE_FAIL_OPENSPEC_ARTIFACT-}" ]; then
  printf 'injected instructions failure: %s\n' "$2" >&2
  exit 72
fi

exec "$CADENCE_REAL_OPENSPEC_BIN" "$@"
