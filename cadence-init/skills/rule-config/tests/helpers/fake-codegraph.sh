#!/usr/bin/env sh
#
# fake-codegraph.sh — codegraph CLI 替身（Task 3 引入）
#
# 模板，使用前由 run-script.sh 的 fake_codegraph() 把下列占位符替换为具体数值：
#   @INSTALL_RC@  codegraph install 期望退出码
#   @INIT_RC@     codegraph init 期望退出码（=0 时会 mkdir -p .codegraph）
#   @STATUS_RC@   codegraph status 期望退出码
#   @WRITE_CONFIG@ install 时是否向 cwd 写入 .mcp.json 与 .codex/config.toml（1 写，0 不写）
#
# 用法（按 $1 分发）：version / install / init / status

set -u

CODEGRAPH_MCP_JSON='{ "mcpServers": { "codegraph": { "command": "codegraph", "args": ["mcp"] } } }'
CODEGRAPH_TOML_TPL='[mcp_servers.codegraph]
command = "codegraph"
args = ["mcp"]'

case "${1-}" in
  version)
    printf 'codegraph fake 0.0.0\n'
    exit 0
    ;;
  install)
    if [ "@WRITE_CONFIG@" = "1" ]; then
      mkdir -p .codex
      printf '%s\n' "$CODEGRAPH_MCP_JSON" > .mcp.json
      printf '%s\n' "$CODEGRAPH_TOML_TPL" > .codex/config.toml
    fi
    exit @INSTALL_RC@
    ;;
  init)
    if [ "@INIT_RC@" = "0" ]; then
      mkdir -p .codegraph
    fi
    exit @INIT_RC@
    ;;
  status)
    printf 'codegraph status: initialized (fake)\n'
    exit @STATUS_RC@
    ;;
  *)
    printf 'fake-codegraph: unknown subcommand: %s\n' "${1-}" >&2
    exit 64
    ;;
esac
