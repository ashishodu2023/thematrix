"""Digital rain — vertical cascades + vertical title decode."""

from __future__ import annotations

import os
import random
import sys
import time

from matrix.theme import enabled, paint, out, vertical_enabled, vertical_stack


_GLYPHS = (
    "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
    "0123456789<>*+-=:"
)


def rain(seconds: float = 0.55, cols: int = 14, rows: int = 8) -> None:
    """Falling vertical glyph columns."""
    from matrix.config import config

    if config.no_rain or os.getenv("MATRIX_NO_RAIN", "").strip() in {"1", "true", "yes"}:
        return
    if not enabled():
        return
    end = time.time() + max(0.05, seconds)
    streams = [[random.choice(_GLYPHS) for _ in range(rows)] for _ in range(cols)]
    while time.time() < end:
        for c in range(cols):
            streams[c] = [random.choice(_GLYPHS)] + streams[c][:-1]
        for r in range(rows):
            line = " ".join(streams[c][r] for c in range(cols))
            sys.stdout.write(paint(line) + "\n")
        sys.stdout.flush()
        time.sleep(0.05)
        sys.stdout.write(f"\033[{rows}A")
        sys.stdout.flush()
    for _ in range(rows):
        sys.stdout.write("\r" + " " * (cols * 2) + "\n")
    sys.stdout.write(f"\033[{rows}A")
    sys.stdout.flush()


def decode_title(title: str, delay: float = 0.04) -> None:
    """Reveal scene title one vertical glyph at a time."""
    from matrix import theme
    from matrix.config import config

    if not enabled() or config.no_rain or config.fast:
        theme.out(f"══ {title} ══", bold=True)
        return

    if vertical_enabled():
        out("═", bold=True)
        shown = ""
        for ch in title:
            shown += ch
            out(ch if ch != " " else "·", bold=True)
            time.sleep(delay)
        out("═", bold=True)
        out()
        return

    if os.getenv("MATRIX_NO_RAIN", "").strip() in {"1", "true", "yes"}:
        theme.out(f"══ {title} ══", bold=True)
        return
    prefix = "══ "
    suffix = " ══"
    shown = ""
    for ch in title:
        shown += ch
        sys.stdout.write("\r" + paint(prefix + shown + suffix, bold=True))
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()
