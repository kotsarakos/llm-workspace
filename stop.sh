#!/usr/bin/env bash
# Stop llm-workspace: the web UI container and the MCP servers. Data is kept.
set -uo pipefail
cd "$(dirname "$0")"

docker stop llm-workspace >/dev/null 2>&1 && echo "▸ Stopped the web UI" || echo "▸ Web UI was not running"

for pidfile in .run/*.pid; do
  [[ -e "$pidfile" ]] || continue
  name=$(basename "$pidfile" .pid)
  pid=$(cat "$pidfile")
  # Each server runs in its own process group (see start.sh): stop the whole group.
  if kill -0 "$pid" 2>/dev/null; then
    kill -TERM -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null
    echo "▸ Stopped MCP server '$name'"
  fi
  rm -f "$pidfile"
done
