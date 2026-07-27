"""Optional macOS / terminal sound cues."""

from __future__ import annotations

import os
import subprocess
import sys

_ENABLED = os.getenv("MATRIX_SOUND", "1").strip().lower() not in {"0", "false", "no"}

# macOS system sounds (best-effort)
_SOUNDS = {
    "agent": "/System/Library/Sounds/Sosumi.aiff",
    "phone": "/System/Library/Sounds/Glass.aiff",
    "sentinel": "/System/Library/Sounds/Basso.aiff",
    "jack": "/System/Library/Sounds/Ping.aiff",
    "glitch": "/System/Library/Sounds/Funk.aiff",
}


def play(kind: str) -> None:
    if not _ENABLED:
        return
    path = _SOUNDS.get(kind)
    if not path or not os.path.isfile(path):
        # terminal bell fallback
        try:
            sys.stdout.write("\a")
            sys.stdout.flush()
        except Exception:  # noqa: BLE001
            pass
        return
    try:
        subprocess.Popen(
            ["afplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:  # noqa: BLE001
        try:
            sys.stdout.write("\a")
            sys.stdout.flush()
        except Exception:  # noqa: BLE001
            pass
