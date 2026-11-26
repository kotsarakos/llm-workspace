"""What each tool does, independent of MCP.

Every action tries the Spotify Web API first when it is set up, and falls
back to controlling the desktop app (media keys, spotify: URIs) otherwise.
So the tools work out of the box and get richer once the API is configured.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Literal

from spotify_mcp import desktop
from spotify_mcp.config import Settings
from spotify_mcp.desktop import DesktopError, MediaKey
from spotify_mcp.web_api import ApiUnavailable, Kind, PlaybackRejected, SpotifyWebApi

log = logging.getLogger("spotify_mcp.service")

Action = Literal["play", "pause", "next", "previous", "restart_track"]

_FALLBACK_KEYS: dict[str, MediaKey] = {
    "play": MediaKey.PLAY_PAUSE,
    "pause": MediaKey.PLAY_PAUSE,
    "next": MediaKey.NEXT,
    "previous": MediaKey.PREVIOUS,
    # "Previous" restarts the current song when it has played for a few seconds.
    "restart_track": MediaKey.PREVIOUS,
}

_DONE = {
    "play": "Playing.",
    "pause": "Paused.",
    "next": "Skipped to the next song.",
    "previous": "Went back to the previous song.",
    "restart_track": "Restarted the current song.",
}


class SpotifyService:
    def __init__(
        self,
        settings: Settings,
        *,
        api_factory: Callable[[Settings], SpotifyWebApi] = SpotifyWebApi,
        desk=desktop,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._settings = settings
        self._api_factory = api_factory
        self._desk = desk
        self._sleep = sleep

    # -- helpers ---------------------------------------------------------
    def _api(self) -> SpotifyWebApi | None:
        try:
            return self._api_factory(self._settings)
        except ApiUnavailable as exc:
            log.info("web api unavailable: %s", exc)
            return None

    def _ensure_running(self) -> bool:
        """Open Spotify if needed. Returns True if it had to be opened."""
        if self._desk.is_running():
            return False
        self._desk.open_app()
        self._sleep(4)
        return True

    # -- tools -----------------------------------------------------------
    def open(self) -> str:
        self._desk.open_app()
        return "Spotify is open."

    def close(self) -> str:
        return "Closed Spotify." if self._desk.close_app() else "Spotify was not running."

    def restart(self) -> str:
        self._desk.close_app()
        for _ in range(10):
            if not self._desk.is_running():
                break
            self._sleep(0.5)
        self._desk.open_app()
        return "Restarted Spotify."

    def _find_device(self, api: SpotifyWebApi):
        """Pick a device to play on, preferring this computer. Opens Spotify if none is available."""
        for attempt in range(4):
            devices = api.devices()
            if devices:
                return next((d for d in devices if d.type.lower() == "computer"), devices[0])
            if attempt == 0:
                self._desk.open_app()
            self._sleep(2)
        return None

    def _play_on_device(self, api: SpotifyWebApi, item=None) -> str:
        """Start playback; if no device is active, activate one. Returns the device name used, if any."""
        try:
            api.play(item)
            return ""
        except PlaybackRejected as exc:
            if not exc.no_active_device:
                raise
        device = self._find_device(api)
        if device is None:
            raise PlaybackRejected("NO_ACTIVE_DEVICE", 404)
        api.play(item, device_id=device.id)
        return device.name

    def control(self, action: Action) -> str:
        if action not in _DONE:
            return f"Unknown action '{action}'."
        api = self._api()
        if api is not None:
            playing = api.is_playing() if action in ("play", "pause") else None
            # Never send a play/pause toggle blindly: it would stop music that is already playing.
            if action == "play" and playing:
                return "Already playing."
            if action == "pause" and not playing:
                return "Nothing is playing." if playing is None else "Already paused."
            try:
                if action == "play":
                    device = self._play_on_device(api)
                    return f"Playing on {device}." if device else _DONE[action]
                getattr(api, action)()
                return _DONE[action]
            except PlaybackRejected as exc:
                if not (exc.premium_required or exc.no_active_device):
                    return f"Spotify refused '{action}': {exc}"
                log.info("api playback rejected (%s), using media keys", exc)
        opened = self._ensure_running()
        self._desk.press(_FALLBACK_KEYS[action])
        note = " (Opened Spotify first.)" if opened else ""
        if action in ("play", "pause"):
            return f"Toggled play/pause in the Spotify app.{note}"
        return _DONE[action] + note

    def search(self, query: str, kind: Kind = "track", limit: int = 5) -> str:
        query = query.strip()
        if not query:
            return "Tell me what to search for."
        api = self._api()
        if api is None:
            self._desk.open_uri(desktop.build_uri("search", query))
            return f"Opened a Spotify search for '{query}' in the app (connect the Spotify API to get results here)."
        items = api.search(query, kind, limit)
        if not items:
            return f"No {kind}s found for '{query}'."
        lines = [f"{i}. {item.describe()} [{item.uri}]" for i, item in enumerate(items, 1)]
        return f"Top {kind}s for '{query}':\n" + "\n".join(lines)

    def play(self, query: str, kind: Kind = "track") -> str:
        query = query.strip()
        if not query:
            return self.control("play")
        api = self._api()
        if api is None:
            self._desk.open_uri(desktop.build_uri("search", query))
            return f"Opened a Spotify search for '{query}'. Pick a result in the app to play it."
        items = api.search(query, kind, 1)
        if not items:
            return f"No {kind}s found for '{query}'."
        item = items[0]
        try:
            device = self._play_on_device(api, item)
            return f"Playing {item.describe()}" + (f" on {device}." if device else ".")
        except PlaybackRejected as exc:
            log.info("api playback rejected (%s), opening in app", exc)
            self._desk.open_uri(desktop.build_uri(item.kind, item.id))
            return f"Opened {item.describe()} in the Spotify app (playing directly needs Spotify Premium)."

    def now_playing(self) -> str:
        api = self._api()
        if api is None:
            return "I can only see what is playing once the Spotify API is connected (see the server README)."
        return api.now_playing() or "Nothing is playing right now."


def safe(fn: Callable[..., str]) -> Callable[..., str]:
    """Turn expected failures into a short message for the model."""

    def wrapper(*args, **kwargs) -> str:
        try:
            return fn(*args, **kwargs)
        except (DesktopError, ApiUnavailable, PlaybackRejected) as exc:
            return f"Failed: {exc}"

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper
