import subprocess

import pytest

from spotify_mcp import desktop
from spotify_mcp.desktop import DesktopError, MediaKey, build_uri


@pytest.fixture
def ran(monkeypatch):
    """Capture PowerShell scripts instead of running them."""
    scripts = []
    monkeypatch.setattr(desktop, "find_powershell", lambda: "ps")

    def fake_run(cmd, **kw):
        scripts.append(cmd[-1])
        return subprocess.CompletedProcess(cmd, 0, "no", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return scripts


def test_search_uri_is_percent_encoded():
    assert build_uri("search", "daft punk") == "spotify:search:daft%20punk"


@pytest.mark.parametrize("evil", ["x'; Remove-Item C:\\ -Recurse; '", "a\"b", "$(calc)", "`whoami`"])
def test_search_uri_neutralises_injection(evil):
    uri = build_uri("search", evil)
    assert all(ch not in uri for ch in "'\";$` ")


def test_item_uri_requires_alphanumeric_id():
    assert build_uri("track", "4uLU6hMCjMI75M1A2tKUQC") == "spotify:track:4uLU6hMCjMI75M1A2tKUQC"
    with pytest.raises(DesktopError):
        build_uri("track", "abc'; rm")


def test_open_uri_refuses_non_spotify(ran):
    with pytest.raises(DesktopError):
        desktop.open_uri("https://evil.example")
    with pytest.raises(DesktopError):
        desktop.open_uri("spotify:x'; calc")
    assert ran == []


def test_open_app_runs_start_process(ran):
    desktop.open_app()
    assert ran == ["Start-Process 'spotify:'"]


def test_close_app_when_not_running(ran):
    assert desktop.close_app() is False
    assert not any("Stop-Process" in s for s in ran)


def test_media_key_uses_fixed_code(ran):
    desktop.press(MediaKey.NEXT)
    assert str(MediaKey.NEXT.value) in ran[0] and "keybd_event" in ran[0]


def test_powershell_failure_raises(monkeypatch):
    monkeypatch.setattr(desktop, "find_powershell", lambda: "ps")
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "boom"))
    with pytest.raises(DesktopError, match="boom"):
        desktop.open_app()
