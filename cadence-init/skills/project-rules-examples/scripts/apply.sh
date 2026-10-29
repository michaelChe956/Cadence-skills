#!/usr/bin/env bash
# project-rules-examples 确定性铺设/合并 wrapper。
# 实际逻辑在 apply.py；已存在文件的用户正文不被重写，入口文件只读。
set -u
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/apply.py" "$@"
