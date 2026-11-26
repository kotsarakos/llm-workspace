#!/usr/bin/env bash
# Start llm-workspace: MCP servers on the host + the web UI in Docker.
#   ./start.sh            start (builds the image the first time)
#   ./start.sh --rebuild  rebuild the image from source first
set -euo pipefail
cd "$(dirname "$0")"

# Optional config: workspace.env overrides the defaults below.
if [[ -f workspace.env ]]; then set -a; . ./workspace.env; set +a; fi
PORT="${LLM_WORKSPACE_PORT:-3000}"
MODEL="${LLM_MODEL:-qwen3:4b}"
OLLAMA_URL="${OLLAMA_BASE_URL:-http://host.docker.internal:11434}"
export SPOTIFY_MCP_PORT="${SPOTIFY_MCP_PORT:-8765}"
IMAGE=llm-workspace
CONTAINER=llm-workspace
RUN_DIR="$PWD/.run"

say() { printf '\033[1;35m▸\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "$1 is required. Install: $2"; }

port_open() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

# --- 1. prerequisites ------------------------------------------------------
need docker "https://docs.docker.com/get-docker/"
need ollama "https://ollama.com/download"
need uv "curl -LsSf https://astral.sh/uv/install.sh | sh"
docker info >/dev/null 2>&1 || die "Docker is not running. Start Docker Desktop and try again."
ollama list >/dev/null 2>&1 || die "Ollama is not running. Start it (e.g. 'ollama serve') and try again."

# --- 2. model ----------------------------------------------------------------
if [[ "${SKIP_MODEL_PULL:-0}" != 1 ]] && ! ollama list | awk 'NR>1 {print $1}' | grep -qx "$MODEL"; then
  say "Pulling model $MODEL (first run only)..."
  ollama pull "$MODEL"
fi

# Tool-enabled variants of models that lack tool calling (see models/).
for dir in models/*/; do
  name=$(basename "$dir")
  base=$(awk '/^FROM/ {print $2; exit}' "$dir/Modelfile")
  if ollama list | awk 'NR>1 {print $1}' | grep -qx "$base" && ! ollama list | awk 'NR>1 {print $1}' | grep -q "^$name:"; then
    say "Creating $name from $base..."
    ollama create "$name" -f "$dir/Modelfile" >/dev/null
  fi
done

# --- 3. MCP servers ----------------------------------------------------------
mkdir -p "$RUN_DIR"
start_mcp() {  # name port
  local name=$1 port=$2
  if port_open "$port"; then say "MCP server '$name' already running on :$port"; return; fi
  say "Starting MCP server '$name' on :$port..."
  (cd "mcp-servers/$name" && uv sync -q) || die "Could not install MCP server '$name'"
  # Own process group, so ./stop.sh can stop uv and the server together.
  setsid nohup bash -c "cd 'mcp-servers/$name' && exec uv run '$name-mcp'" >"$RUN_DIR/$name.log" 2>&1 </dev/null &
  for _ in $(seq 1 60); do
    if port_open "$port"; then
      # Record the server's process group (used by ./stop.sh).
      local pid; pid=$(ss -ltnp 2>/dev/null | grep ":$port " | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2)
      [[ -n "$pid" ]] && ps -o pgid= -p "$pid" | tr -d ' ' >"$RUN_DIR/$name.pid"
      return
    fi
    sleep 0.5
  done
  die "MCP server '$name' did not start. See .run/$name.log"
}
start_mcp spotify "$SPOTIFY_MCP_PORT"

# Tool servers llm-workspace connects to automatically (applied on first start of a fresh install).
TOOL_SERVERS=$(cat <<JSON
[{"type":"mcp","url":"http://host.docker.internal:${SPOTIFY_MCP_PORT}/mcp","path":"","auth_type":"none","key":"",
  "config":{"enable":true},"info":{"id":"spotify","name":"Spotify","description":"Open, control and search Spotify"}}]
JSON
)

# --- 4. web UI ---------------------------------------------------------------
if [[ "${1:-}" == "--rebuild" ]] || ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  say "Building the $IMAGE image (about 10 minutes the first time)..."
  docker build -t "$IMAGE" .
fi

say "Starting the web UI..."
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER" \
  -p "127.0.0.1:${PORT}:8080" \
  -v llm-workspace-data:/app/backend/data \
  -e OLLAMA_BASE_URL="$OLLAMA_URL" \
  -e TOOL_SERVER_CONNECTIONS="$TOOL_SERVERS" \
  -e ENABLE_TAGS_GENERATION=False \
  -e ENABLE_FOLLOW_UP_GENERATION=False \
  -e DEFAULT_MODEL_PARAMS='{"keep_alive":"30m"}' \
  -e DEFAULT_MODEL_METADATA='{"toolIds":["server:mcp:spotify"]}' \
  --add-host host.docker.internal:host-gateway \
  --restart unless-stopped \
  "$IMAGE" >/dev/null

for _ in $(seq 1 120); do
  if curl -fs "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    say "Ready: http://localhost:${PORT}"
    exit 0
  fi
  sleep 2
done
die "The web UI did not become healthy. Check: docker logs $CONTAINER"
