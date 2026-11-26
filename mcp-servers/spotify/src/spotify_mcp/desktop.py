"""Control the Spotify desktop app on Windows from WSL, through PowerShell.

Works with any Spotify account (free or Premium) and needs no API keys.
Every PowerShell script here is a fixed string; user or model text only
ever appears percent-encoded inside a spotify: URI, so it cannot inject
commands.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from urllib.parse import quote

log = logging.getLogger("spotify_mcp.desktop")

_POWERSHELL_FALLBACK = Path("/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe")
_PROCESS = "Spotify"


class DesktopError(RuntimeError):
    """Raised when a desktop action fails."""


class MediaKey(Enum):
    """Windows virtual-key codes for the global media keys."""

    PLAY_PAUSE = 0xB3
    NEXT = 0xB0
    PREVIOUS = 0xB1


_MEDIA_KEY_SCRIPT = (
    "Add-Type -Namespace LlmWorkspace -Name Keys -MemberDefinition "
    "'[DllImport(\"user32.dll\")] public static extern void keybd_event(byte k, byte s, uint f, System.UIntPtr e);'; "
    "[LlmWorkspace.Keys]::keybd_event({code}, 0, 1, [System.UIntPtr]::Zero); "
    "[LlmWorkspace.Keys]::keybd_event({code}, 0, 3, [System.UIntPtr]::Zero)"
)


def find_powershell() -> str:
    found = shutil.which("powershell.exe")
    if found:
        return found
    if _POWERSHELL_FALLBACK.exists():
        return str(_POWERSHELL_FALLBACK)
    raise DesktopError("Windows PowerShell not found. The Spotify desktop controls need WSL on Windows.")


def _run(script: str, *, timeout: float = 15.0) -> str:
    cmd = [find_powershell(), "-NoProfile", "-NonInteractive", "-Command", script]
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise DesktopError("Timed out talking to Windows.") from exc
    if done.returncode != 0:
        detail = (done.stderr or done.stdout).strip()
        raise DesktopError(detail or f"PowerShell exited with code {done.returncode}")
    return done.stdout.strip()


def build_uri(kind: str, value: str = "") -> str:
    """Build a spotify: URI. ``value`` is percent-encoded so it is always inert."""
    if kind == "app":
        return "spotify:"
    if kind == "search":
        return "spotify:search:" + quote(value.strip(), safe="")
    if kind in ("track", "album", "artist", "playlist"):
        if not value.isalnum():
            raise DesktopError(f"Invalid Spotify {kind} id.")
        return f"spotify:{kind}:{value}"
    raise DesktopError(f"Unknown URI kind: {kind}")


def open_uri(uri: str) -> None:
    if not uri.startswith("spotify:") or "'" in uri:
        raise DesktopError("Refusing to open a non-Spotify URI.")
    log.info("open uri=%s", uri)
    _run(f"Start-Process '{uri}'")


def open_app() -> None:
    open_uri(build_uri("app"))


def is_running() -> bool:
    out = _run(f"if (Get-Process -Name {_PROCESS} -ErrorAction SilentlyContinue) {{ 'yes' }} else {{ 'no' }}")
    return out == "yes"


def close_app() -> bool:
    """Close Spotify. Returns False if it was not running."""
    if not is_running():
        return False
    log.info("close app")
    _run(f"Stop-Process -Name {_PROCESS}")
    return True


def press(key: MediaKey) -> None:
    log.info("media key=%s", key.name)
    _run(_MEDIA_KEY_SCRIPT.format(code=key.value))
