"""Spotify Web API client (optional).

Uses the Authorization Code + PKCE flow, so only a Client ID is needed (no
client secret). The user logs in once with ``uv run spotify-mcp-login``; the
token is cached outside the repo and refreshed automatically.

Search and "now playing" work on any account. Playback control through the
API needs Spotify Premium; callers fall back to the desktop media keys.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyPKCE

from spotify_mcp.config import Settings

log = logging.getLogger("spotify_mcp.web_api")

SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
Kind = Literal["track", "artist", "album", "playlist"]


class ApiUnavailable(RuntimeError):
    """The Web API is not configured or the user has not logged in."""


class PlaybackRejected(RuntimeError):
    """Spotify refused a playback command (no Premium, no active device, ...)."""

    def __init__(self, reason: str, status: int = 0):
        super().__init__(reason)
        self.reason = reason or ""
        self.status = status

    @property
    def no_active_device(self) -> bool:
        return self.status == 404 or "NO_ACTIVE_DEVICE" in self.reason

    @property
    def premium_required(self) -> bool:
        return "PREMIUM_REQUIRED" in self.reason


@dataclass(frozen=True)
class Device:
    id: str
    name: str
    type: str
    is_active: bool


@dataclass(frozen=True)
class Item:
    kind: str
    id: str
    name: str
    subtitle: str
    uri: str

    def describe(self) -> str:
        return f"{self.name} — {self.subtitle}" if self.subtitle else self.name


def make_auth(settings: Settings) -> SpotifyPKCE:
    settings.spotify_token_cache.parent.mkdir(parents=True, exist_ok=True)
    return SpotifyPKCE(
        client_id=settings.spotify_client_id,
        redirect_uri=settings.spotify_redirect_uri,
        scope=SCOPES,
        cache_handler=CacheFileHandler(cache_path=str(settings.spotify_token_cache)),
        open_browser=False,
    )


class SpotifyWebApi:
    def __init__(self, settings: Settings):
        if not settings.api_configured:
            raise ApiUnavailable("SPOTIFY_CLIENT_ID is not set.")
        self._auth = make_auth(settings)
        if not self._auth.validate_token(self._auth.cache_handler.get_cached_token()):
            raise ApiUnavailable("Not logged in to Spotify. Run: uv run spotify-mcp-login")
        self._sp = spotipy.Spotify(auth_manager=self._auth, requests_timeout=10, retries=1)

    def search(self, query: str, kind: Kind = "track", limit: int = 5) -> list[Item]:
        res = self._sp.search(q=query, type=kind, limit=max(1, min(limit, 10)))
        return [_to_item(kind, raw) for raw in (res.get(f"{kind}s", {}).get("items") or []) if raw]

    def now_playing(self) -> str | None:
        cur = self._sp.current_playback()
        if not cur or not cur.get("item"):
            return None
        item = _to_item("track", cur["item"])
        state = "playing" if cur.get("is_playing") else "paused"
        device = (cur.get("device") or {}).get("name", "unknown device")
        return f"{item.describe()} ({state} on {device})"

    def now_playing_card(self) -> dict | None:
        """Structured now-playing data for the web UI mini player."""
        cur = self._sp.current_playback()
        item = (cur or {}).get("item")
        if not item:
            return None
        images = (item.get("album") or {}).get("images") or []
        return {
            "title": item.get("name", ""),
            "artists": ", ".join(a["name"] for a in item.get("artists", [])),
            "album": (item.get("album") or {}).get("name", ""),
            "image": images[0]["url"] if images else "",
            "is_playing": bool(cur.get("is_playing")),
            "device": (cur.get("device") or {}).get("name", ""),
            "progress_ms": cur.get("progress_ms") or 0,
            "duration_ms": item.get("duration_ms") or 0,
        }

    def is_playing(self) -> bool | None:
        """True/False for the active device, None when nothing is active."""
        cur = self._sp.current_playback()
        return None if not cur else bool(cur.get("is_playing"))

    def devices(self) -> list[Device]:
        raw = self._sp.devices().get("devices") or []
        return [Device(d["id"], d.get("name", ""), d.get("type", ""), bool(d.get("is_active"))) for d in raw if d.get("id")]

    def play(self, item: Item | None = None, device_id: str | None = None) -> None:
        if item is None:
            self._playback(self._sp.start_playback, device_id=device_id)
        elif item.kind == "track":
            self._playback(self._sp.start_playback, device_id=device_id, uris=[item.uri])
        else:
            self._playback(self._sp.start_playback, device_id=device_id, context_uri=item.uri)

    def pause(self) -> None:
        self._playback(self._sp.pause_playback)

    def next(self) -> None:
        self._playback(self._sp.next_track)

    def previous(self) -> None:
        self._playback(self._sp.previous_track)

    def restart_track(self) -> None:
        self._playback(self._sp.seek_track, 0)

    @staticmethod
    def _playback(call, *args, **kwargs) -> None:
        try:
            call(*args, **kwargs)
        except spotipy.SpotifyException as exc:
            if exc.http_status in (403, 404):
                raise PlaybackRejected(f"{exc.reason or ''} {exc.msg or ''}".strip(), exc.http_status) from exc
            raise


def _to_item(kind: str, raw: dict) -> Item:
    if kind in ("track", "album"):
        subtitle = ", ".join(a["name"] for a in raw.get("artists", []))
    elif kind == "playlist":
        subtitle = "by " + (raw.get("owner") or {}).get("display_name", "unknown")
    else:
        subtitle = ", ".join(raw.get("genres", [])[:2])
    return Item(kind=kind, id=raw["id"], name=raw["name"], subtitle=subtitle, uri=raw["uri"])
