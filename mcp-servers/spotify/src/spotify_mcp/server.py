"""Spotify MCP server: declares the tools and serves them over Streamable HTTP.

Run:  uv run spotify-mcp
URL:  http://127.0.0.1:8765/mcp   (from Docker: http://host.docker.internal:8765/mcp)
"""

from __future__ import annotations

import logging

import anyio
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from spotify_mcp.config import get_settings
from spotify_mcp.service import Action, SpotifyService
from spotify_mcp.service import safe as _safe
from spotify_mcp.web_api import Kind

log = logging.getLogger("spotify_mcp.tools")
settings = get_settings()


def safe(fn):
    """Run a tool safely and log the call, its arguments and its result (audit trail)."""
    guarded = _safe(fn)

    def wrapper(*args, **kwargs):
        result = guarded(*args, **kwargs)
        log.info("tool=%s args=%s kwargs=%s -> %s", fn.__name__, args, kwargs, result.replace("\n", " | "))
        return result

    return wrapper


service = SpotifyService(settings)

server = MCPServer(
    name="spotify",
    instructions=(
        "Control Spotify on the user's computer: open, close or restart the app, "
        "play/pause/skip, restart the current song, search for music and play it."
    ),
)


def _hints(title: str, *, read_only: bool = False) -> ToolAnnotations:
    return ToolAnnotations(title=title, readOnlyHint=read_only, destructiveHint=False, openWorldHint=False)


@server.tool(description="Open (start) the Spotify app.", annotations=_hints("Open Spotify"))
def open_spotify() -> str:
    return safe(service.open)()


@server.tool(description="Close (quit) the Spotify app.", annotations=_hints("Close Spotify"))
def close_spotify() -> str:
    return safe(service.close)()


@server.tool(description="Restart the Spotify app (close it and open it again).", annotations=_hints("Restart Spotify"))
def restart_spotify() -> str:
    return safe(service.restart)()


@server.tool(
    description=(
        "Control what is already playing. action: 'play' = resume paused music, 'pause' = pause, "
        "'next' = skip to the next song in the queue, 'previous' = go back one song, "
        "'restart_track' = replay the current song from the beginning (only when the user explicitly asks to restart it). "
        "Do NOT use this to play a specific or different song, artist or playlist: use play_music for that."
    ),
    annotations=_hints("Playback control"),
)
def playback(action: Action) -> str:
    return safe(service.control)(action)


@server.tool(
    description=(
        "Search Spotify and list the top results without playing anything. Use only when the user wants to see or "
        "choose results; to play music use play_music. kind is track, artist, album or playlist."
    ),
    annotations=_hints("Search music", read_only=True),
)
def search_music(query: str, kind: Kind = "track", limit: int = 5) -> str:
    return safe(service.search)(query, kind, limit)


@server.tool(
    description=(
        "Play a specific song, artist, album or playlist right away, replacing what is playing. "
        "Use this whenever the user names music or asks to change/switch to a different song. "
        "Example: query='Bohemian Rhapsody', or query='Michael Jackson' with kind='artist'."
    ),
    annotations=_hints("Play music"),
)
def play_music(query: str, kind: Kind = "track") -> str:
    return safe(service.play)(query, kind)


@server.tool(description="Tell what song is playing right now.", annotations=_hints("Now playing", read_only=True))
def now_playing() -> str:
    return safe(service.now_playing)()


@server.custom_route("/now-playing", methods=["GET"], include_in_schema=False)
async def now_playing_http(request: Request) -> JSONResponse:
    """Read-only now-playing data for the web UI mini player (no MCP session needed)."""
    data = await anyio.to_thread.run_sync(service.now_playing_card)
    headers = {"Cache-Control": "no-store", "Vary": "Origin"}
    origin = request.headers.get("origin", "")
    allowed = {o.strip() for o in settings.spotify_mcp_cors_origins.split(",") if o.strip()}
    if origin in allowed:
        headers["Access-Control-Allow-Origin"] = origin
    return JSONResponse(data, headers=headers)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    port = settings.spotify_mcp_port
    allowed = [f"{h}:{port}" for h in ("127.0.0.1", "localhost", "host.docker.internal", settings.spotify_mcp_host)]
    mode = "Web API + desktop" if settings.api_configured else "desktop only (no SPOTIFY_CLIENT_ID)"
    logging.getLogger("spotify_mcp").info("starting on %s:%s, mode: %s", settings.spotify_mcp_host, port, mode)
    server.run(
        transport="streamable-http",
        host=settings.spotify_mcp_host,
        port=port,
        transport_security=TransportSecuritySettings(allowed_hosts=sorted(set(allowed))),
    )


if __name__ == "__main__":
    main()
