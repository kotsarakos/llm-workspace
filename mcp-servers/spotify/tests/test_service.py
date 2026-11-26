import pytest

from spotify_mcp import desktop as real_desktop
from spotify_mcp.config import Settings
from spotify_mcp.desktop import MediaKey
from spotify_mcp.service import SpotifyService
from spotify_mcp.web_api import ApiUnavailable, Device, Item, PlaybackRejected

SONG = Item(kind="track", id="abc123", name="Song", subtitle="Artist", uri="spotify:track:abc123")


class FakeDesktop:
    build_uri = staticmethod(real_desktop.build_uri)

    def __init__(self, running=True):
        self.running = running
        self.calls = []

    def is_running(self):
        return self.running

    def open_app(self):
        self.calls.append("open")
        self.running = True

    def close_app(self):
        self.calls.append("close")
        was, self.running = self.running, False
        return was

    def press(self, key):
        self.calls.append(key)

    def open_uri(self, uri):
        self.calls.append(uri)


class FakeApi:
    def __init__(self, premium=True, results=(SONG,), playing=False, active_device=True, devices=None):
        self.premium = premium
        self.results = list(results)
        self.playing = playing
        self.active_device = active_device
        self._devices = devices if devices is not None else [Device("pc1", "My-PC", "Computer", False)]
        self.calls = []

    def _cmd(self, name, *args):
        self.calls.append((name, *args))
        if not self.premium:
            raise PlaybackRejected("PREMIUM_REQUIRED", 403)

    def is_playing(self):
        return self.playing if self.active_device else None

    def devices(self):
        return self._devices

    def play(self, item=None, device_id=None):
        self._cmd("play", item, device_id)
        if not self.active_device and device_id is None:
            raise PlaybackRejected("NO_ACTIVE_DEVICE", 404)
        self.playing, self.active_device = True, True

    def pause(self):
        self._cmd("pause")

    def next(self):
        self._cmd("next")

    def previous(self):
        self._cmd("previous")

    def restart_track(self):
        self._cmd("restart_track")

    def search(self, query, kind, limit):
        self.calls.append(("search", query, kind, limit))
        return self.results[:limit]

    def now_playing(self):
        return "Song — Artist (playing on PC)"


def make(api=None, desk=None):
    def factory(_settings):
        if api is None:
            raise ApiUnavailable("not configured")
        return api

    desk = desk or FakeDesktop()
    return SpotifyService(Settings(), api_factory=factory, desk=desk, sleep=lambda s: None), desk


def test_open_close_restart():
    svc, desk = make()
    assert svc.open() == "Spotify is open."
    assert svc.close() == "Closed Spotify."
    assert svc.close() == "Spotify was not running."
    assert svc.restart() == "Restarted Spotify."
    assert desk.calls[-2:] == ["close", "open"]


@pytest.mark.parametrize("action", ["play", "pause", "next", "previous", "restart_track"])
def test_control_uses_api_with_premium(action):
    api = FakeApi(playing=(action == "pause"))
    svc, desk = make(api)
    svc.control(action)
    assert api.calls[0][0] == action
    assert not any(isinstance(c, MediaKey) for c in desk.calls)


def test_control_falls_back_to_media_keys_without_premium():
    api = FakeApi(premium=False)
    svc, desk = make(api)
    assert svc.control("next") == "Skipped to the next song."
    assert desk.calls == [MediaKey.NEXT]


def test_control_without_api_opens_spotify_first():
    svc, desk = make(desk=FakeDesktop(running=False))
    msg = svc.control("play")
    assert desk.calls == ["open", MediaKey.PLAY_PAUSE]
    assert "Opened Spotify first" in msg


def test_restart_track_falls_back_to_previous_key():
    svc, desk = make()
    svc.control("restart_track")
    assert desk.calls == [MediaKey.PREVIOUS]


def test_search_lists_api_results():
    svc, _ = make(FakeApi())
    out = svc.search("song")
    assert "1. Song — Artist [spotify:track:abc123]" in out


def test_search_without_api_opens_app_search():
    svc, desk = make()
    out = svc.search("daft punk")
    assert desk.calls == ["spotify:search:daft%20punk"]
    assert "Opened a Spotify search" in out


def test_search_requires_query():
    svc, desk = make()
    assert "what to search" in svc.search("  ")
    assert desk.calls == []


def test_play_music_with_premium():
    api = FakeApi()
    svc, desk = make(api)
    assert svc.play("song") == "Playing Song — Artist."
    assert ("play", SONG, None) in api.calls


def test_play_music_without_premium_opens_track_in_app():
    svc, desk = make(FakeApi(premium=False))
    out = svc.play("song")
    assert desk.calls == ["spotify:track:abc123"]
    assert "needs Spotify Premium" in out


def test_play_music_not_found():
    svc, _ = make(FakeApi(results=()))
    assert svc.play("zzz") == "No tracks found for 'zzz'."


def test_now_playing():
    assert make(FakeApi())[0].now_playing() == "Song — Artist (playing on PC)"
    assert "API is connected" in make()[0].now_playing()


def test_play_when_already_playing_does_not_toggle():
    """Regression: 'play' while music played sent the play/pause key and stopped it."""
    api = FakeApi(playing=True)
    svc, desk = make(api)
    assert svc.control("play") == "Already playing."
    assert api.calls == [] and desk.calls == []


def test_pause_when_already_paused_does_not_toggle():
    svc, desk = make(FakeApi(playing=False))
    assert svc.control("pause") == "Already paused."
    assert desk.calls == []


def test_play_music_without_active_device_plays_on_computer():
    """Regression: 404 NO_ACTIVE_DEVICE only opened the track page instead of playing."""
    api = FakeApi(active_device=False, devices=[Device("ph", "My-Phone", "Smartphone", False), Device("pc1", "My-PC", "Computer", False)])
    svc, desk = make(api)
    assert svc.play("song") == "Playing Song — Artist on My-PC."
    assert api.calls[-1] == ("play", SONG, "pc1")


def test_play_music_opens_spotify_when_no_device_is_available():
    api = FakeApi(active_device=False, devices=[])
    svc, desk = make(api)
    out = svc.play("song")
    assert desk.calls[0] == "open"
    assert desk.calls[-1] == "spotify:track:abc123" and "Opened" in out


def test_other_api_refusals_do_not_press_media_keys():
    class Refusing(FakeApi):
        def next(self):
            raise PlaybackRejected("Restriction violated", 403)

    svc, desk = make(Refusing())
    assert "refused" in svc.control("next")
    assert desk.calls == []


def test_now_playing_card_without_api():
    svc, _ = make()
    assert svc.now_playing_card() == {"available": False, "reason": "Spotify API not connected"}


def test_now_playing_card_with_api():
    class WithCard(FakeApi):
        def now_playing_card(self):
            return {"title": "Song", "artists": "Artist", "is_playing": True}

    svc, _ = make(WithCard())
    assert svc.now_playing_card() == {"available": True, "track": {"title": "Song", "artists": "Artist", "is_playing": True}}


def test_now_playing_card_never_raises():
    class Broken(FakeApi):
        def now_playing_card(self):
            raise RuntimeError("network down")

    svc, _ = make(Broken())
    assert svc.now_playing_card()["available"] is False
