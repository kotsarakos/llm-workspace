"""One-time Spotify login: ``uv run spotify-mcp-login``.

Opens the Spotify consent page in the Windows browser, catches the redirect on
the local callback port and stores the token in SPOTIFY_TOKEN_CACHE.
"""

from __future__ import annotations

import sys

from spotify_mcp import desktop
from spotify_mcp.config import get_settings
from spotify_mcp.web_api import make_auth


def main() -> None:
    settings = get_settings()
    if not settings.api_configured:
        sys.exit(
            "SPOTIFY_CLIENT_ID is not set.\n"
            "1. Create an app at https://developer.spotify.com/dashboard\n"
            f"2. Add the redirect URI {settings.spotify_redirect_uri}\n"
            "3. Put SPOTIFY_CLIENT_ID=<your client id> in mcp-servers/spotify/.env"
        )

    auth = make_auth(settings)
    auth._open_auth_url = lambda state=None: None  # we open the Windows browser ourselves
    url = auth.get_authorize_url()
    print("Opening the Spotify login page. If it does not open, visit:\n" + url)
    try:
        desktop._run(f"Start-Process '{url}'")
    except desktop.DesktopError:
        pass

    port = int(settings.spotify_redirect_uri.rsplit(":", 1)[1].split("/")[0])
    code = auth._get_auth_response_local_server(port)
    auth.get_access_token(code)
    print(f"Logged in. Token saved to {settings.spotify_token_cache}")


if __name__ == "__main__":
    main()
