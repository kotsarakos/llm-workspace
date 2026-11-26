# Spotify MCP server

Lets llm-workspace's local model control Spotify on your computer: open, close and restart the app, play/pause/skip, restart a song, search for music and play it.

It works **out of the box** by driving the Spotify desktop app on Windows (from WSL). Connecting the **Spotify Web API** is optional and adds real search results, "now playing" and direct playback.

## Tools

| Tool | Arguments | Without the API | With the API |
|---|---|---|---|
| `open_spotify` | – | Opens the app | same |
| `close_spotify` | – | Quits the app | same |
| `restart_spotify` | – | Quits and reopens the app | same |
| `playback` | `action`: `play` `pause` `next` `previous` `restart_track` | Media keys (play/pause toggle) | Direct control (Premium); falls back to media keys |
| `search_music` | `query`, `kind` (track/artist/album/playlist), `limit` | Opens the search in the app | Returns the top results |
| `play_music` | `query`, `kind` | Opens the search in the app | Plays the top result (Premium), otherwise opens it in the app |
| `now_playing` | – | Not available | Current song, state and device |

## Run
From the repo root, `./start.sh` starts this server and connects it to llm-workspace automatically. To run it on its own:
```bash
cd mcp-servers/spotify
uv run spotify-mcp          # http://127.0.0.1:8765/mcp
```

## Connect the Spotify Web API (optional, ~3 minutes)
1. Open the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) → **Create app**.
2. Redirect URI: `http://127.0.0.1:8766/callback`. API: **Web API**.
3. Copy the **Client ID** into `workspace.env` at the repo root (`cp workspace.env.example workspace.env`):
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   ```
4. Log in once:
   ```bash
   cd mcp-servers/spotify && uv run spotify-mcp-login
   ```
   Your browser opens; approve, and the token is saved to `~/.cache/llm-workspace/spotify-token.json` (outside the repo) and refreshed automatically.
5. Restart: `./stop.sh && ./start.sh`.

Uses Authorization Code with **PKCE**, so no client secret is stored anywhere. Playback control through the API needs **Spotify Premium**; on free accounts the server falls back to the desktop controls automatically.

## Configuration
Read from environment variables, `workspace.env` (repo root) or `mcp-servers/spotify/.env`. All optional.

| Variable | Default |
|---|---|
| `SPOTIFY_MCP_HOST` | `127.0.0.1` |
| `SPOTIFY_MCP_PORT` | `8765` |
| `SPOTIFY_CLIENT_ID` | *(empty: desktop-only mode)* |
| `SPOTIFY_REDIRECT_URI` | `http://127.0.0.1:8766/callback` |
| `SPOTIFY_TOKEN_CACHE` | `~/.cache/llm-workspace/spotify-token.json` |

## Safety
- No free-form commands: every PowerShell script is fixed; search text is percent-encoded into a `spotify:` URI, so it cannot inject commands (covered by tests).
- Listens on `127.0.0.1` only and accepts only local/Docker hosts (DNS-rebinding protection).
- Every action is logged (`.run/spotify.log` when started by `./start.sh`).

## Tests
```bash
uv run pytest
```
The tests use fakes for Spotify and Windows, so nothing on your computer is opened or closed.

## Code layout
```
spotify/
├── pyproject.toml          # package, dependencies, commands: spotify-mcp, spotify-mcp-login
├── src/spotify_mcp/
│   ├── server.py           # MCP layer: tool names, descriptions, arguments
│   ├── service.py          # what each tool does: Web API first, desktop fallback
│   ├── web_api.py          # Spotify Web API client (spotipy, PKCE)
│   ├── desktop.py          # Windows desktop control from WSL (PowerShell)
│   ├── auth.py             # one-time login command
│   └── config.py           # settings from env / workspace.env
└── tests/                  # unit tests for every module
```
