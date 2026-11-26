import pytest
import spotipy

from spotify_mcp.config import Settings
from spotify_mcp.web_api import ApiUnavailable, PlaybackRejected, SpotifyWebApi, _to_item


def test_requires_client_id():
    with pytest.raises(ApiUnavailable, match="SPOTIFY_CLIENT_ID"):
        SpotifyWebApi(Settings(spotify_client_id=""))


def test_requires_login(tmp_path):
    settings = Settings(spotify_client_id="abc", spotify_token_cache=tmp_path / "token.json")
    with pytest.raises(ApiUnavailable, match="spotify-mcp-login"):
        SpotifyWebApi(settings)


def test_track_item_formatting():
    raw = {"id": "1", "name": "One", "uri": "spotify:track:1", "artists": [{"name": "A"}, {"name": "B"}]}
    assert _to_item("track", raw).describe() == "One — A, B"


def test_playlist_item_formatting():
    raw = {"id": "2", "name": "Mix", "uri": "spotify:playlist:2", "owner": {"display_name": "me"}}
    assert _to_item("playlist", raw).describe() == "Mix — by me"


@pytest.mark.parametrize("status", [403, 404])
def test_premium_or_device_errors_become_playback_rejected(status):
    def call():
        raise spotipy.SpotifyException(status, -1, "nope", reason="PREMIUM_REQUIRED")

    with pytest.raises(PlaybackRejected):
        SpotifyWebApi._playback(call)


def test_other_errors_propagate():
    def call():
        raise spotipy.SpotifyException(500, -1, "server")

    with pytest.raises(spotipy.SpotifyException):
        SpotifyWebApi._playback(call)
