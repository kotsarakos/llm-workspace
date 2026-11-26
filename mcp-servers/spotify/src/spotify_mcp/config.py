"""Settings, read from environment variables or the server's .env file.

Every value has a working default, so the server runs with no configuration.
Setting SPOTIFY_CLIENT_ID (and logging in once) enables the Spotify Web API.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = SERVER_DIR.parents[1]


class Settings(BaseSettings):
    # Real environment variables win, then the repo-wide workspace.env, then a server-local .env.
    model_config = SettingsConfigDict(
        env_file=(SERVER_DIR / ".env", REPO_DIR / "workspace.env"), env_file_encoding="utf-8", extra="ignore"
    )

    spotify_mcp_host: str = "127.0.0.1"
    spotify_mcp_port: int = 8765
    # Web UI origins allowed to read /now-playing (comma separated).
    spotify_mcp_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Spotify Web API (optional). Create an app at https://developer.spotify.com/dashboard
    spotify_client_id: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8766/callback"
    spotify_token_cache: Path = Path.home() / ".cache" / "llm-workspace" / "spotify-token.json"

    @property
    def api_configured(self) -> bool:
        return bool(self.spotify_client_id.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
