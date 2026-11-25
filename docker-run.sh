#!/usr/bin/env bash
set -euo pipefail

# Build llm-workspace from source and run it on http://localhost:3000,
# connected to the Ollama server running on this machine.

readonly IMAGE="llm-workspace"
readonly CONTAINER="llm-workspace"
readonly HOST_PORT="${LLM_WORKSPACE_PORT:-3000}"
readonly OLLAMA_URL="${OLLAMA_BASE_URL:-http://host.docker.internal:11434}"

echo "Building ${IMAGE} image..."
docker build -t "$IMAGE" .

echo "Replacing any existing ${CONTAINER} container..."
docker rm -f "$CONTAINER" 2>/dev/null || true

echo "Starting ${CONTAINER} (localhost only)..."
docker run -d \
  --name "$CONTAINER" \
  -p "127.0.0.1:${HOST_PORT}:8080" \
  -v llm-workspace-data:/app/backend/data \
  -e OLLAMA_BASE_URL="$OLLAMA_URL" \
  --add-host host.docker.internal:host-gateway \
  --restart unless-stopped \
  "$IMAGE"

echo "llm-workspace is starting at http://localhost:${HOST_PORT}"
