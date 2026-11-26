from spotify_mcp.config import Settings


def test_defaults_need_no_configuration(monkeypatch):
    for var in ("SPOTIFY_MCP_HOST", "SPOTIFY_MCP_PORT", "SPOTIFY_CLIENT_ID"):
        monkeypatch.delenv(var, raising=False)
    s = Settings(_env_file=None)
    assert (s.spotify_mcp_host, s.spotify_mcp_port) == ("127.0.0.1", 8765)
    assert s.api_configured is False


def test_environment_overrides(monkeypatch):
    monkeypatch.setenv("SPOTIFY_MCP_PORT", "9999")
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "abc")
    s = Settings(_env_file=None)
    assert s.spotify_mcp_port == 9999
    assert s.api_configured is True
