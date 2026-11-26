# MCP servers

Custom [Model Context Protocol](https://modelcontextprotocol.io) servers that give llm-workspace's local models tools to act on your computer. `./start.sh` (repo root) starts every server and connects it to the web UI automatically.

| Folder | MCP server | Tools | Port |
|---|---|---|---|
| [`spotify/`](spotify/) | **Spotify** | `open_spotify`, `close_spotify`, `restart_spotify`, `playback`, `search_music`, `play_music`, `now_playing` | 8765 |

## How it fits together
```
llm-workspace (Docker) ──MCP / Streamable HTTP──► spotify MCP server (host) ──┬─► Spotify Web API
       ▲                                                                       └─► Spotify desktop app (PowerShell)
  local model (Ollama) decides which tool to call
```

## Conventions for new servers
- **One folder per server, named after what it controls** (`spotify/`, `email/`, ...). Package `<name>_mcp`, command `<name>-mcp`.
- `server.py` only declares MCP tools; the logic lives in plain modules so it is unit-tested without MCP.
- Works with zero configuration where possible; optional settings come from env / `workspace.env`.
- Actions come from fixed allowlists, never free-form commands. Irreversible actions (e.g. sending email) require user approval.
- Bind to `127.0.0.1`. Register the server in `start.sh` (`start_mcp <name> <port>` and the `TOOL_SERVERS` list).
