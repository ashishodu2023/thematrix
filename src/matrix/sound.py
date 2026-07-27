"""Optional sound cues — macOS afplay, Linux paplay/aplay, Web console cues."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_ENABLED = os.getenv("MATRIX_SOUND", "1").strip().lower() not in {"0", "false", "no"}

# macOS system sounds (best-effort)
_MAC = {
    "agent": "/System/Library/Sounds/Sosumi.aiff",
    "phone": "/System/Library/Sounds/Glass.aiff",
    "sentinel": "/System/Library/Sounds/Basso.aiff",
    "jack": "/System/Library/Sounds/Ping.aiff",
    "glitch": "/System/Library/Sounds/Funk.aiff",
    "emp": "/System/Library/Sounds/Submarine.aiff",
    "hardline": "/System/Library/Sounds/Purr.aiff",
}

# Linux freesound-ish fallbacks if present
_LINUX = {
    "agent": "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga",
    "phone": "/usr/share/sounds/freedesktop/stereo/message.oga",
    "sentinel": "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
    "jack": "/usr/share/sounds/freedesktop/stereo/service-login.oga",
    "glitch": "/usr/share/sounds/freedesktop/stereo/dialog-error.oga",
    "emp": "/usr/share/sounds/freedesktop/stereo/bell.oga",
    "hardline": "/usr/share/sounds/freedesktop/stereo/complete.oga",
}

# Last cues for browser SSE (console WebAudio)
_last_cue: str = ""


def last_cue() -> str:
    return _last_cue


def play(kind: str) -> None:
    global _last_cue
    _last_cue = kind
    if not _ENABLED:
        return
    path = _MAC.get(kind) if sys.platform == "darwin" else _LINUX.get(kind)
    if path and Path(path).is_file():
        player = "afplay" if sys.platform == "darwin" else None
        if player is None:
            for cand in ("paplay", "aplay", "ffplay"):
                if shutil.which(cand):
                    player = cand
                    break
        if player:
            cmd = [player, path]
            if player == "ffplay":
                cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
            try:
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:  # noqa: BLE001
                pass
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:  # noqa: BLE001
        pass
