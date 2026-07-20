#!/usr/bin/env bash

set -u

target=$1
candidate=$2

mv "$candidate" "$candidate.invalidated"
printf 'injected publish failure for %s\n' "$target" >&2
