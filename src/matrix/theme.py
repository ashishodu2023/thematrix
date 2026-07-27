"""Matrix terminal theme — bright green vertical text on black."""

from __future__ import annotations

import os
import sys

_RESET = "\033[0m"
_BLACK_BG = "\033[40m"
_GREEN = "\033[38;2;57;255;20m"
_DIM_GREEN = "\033[38;2;0;220;70m"
_BOLD_GREEN = "\033[1;38;2;120;255;80m"


def enabled() -> bool:
    if os.getenv("MATRIX_NO_COLOR", "").strip() in {"1", "true", "yes"}:
        return False
    if os.getenv("NO_COLOR", "").strip():
        return False
    return sys.stdout.isatty()


def vertical_enabled() -> bool:
    """Vertical Matrix text. Default off in fast mode; MATRIX_VERTICAL=1 to force."""
    fast = os.getenv("MATRIX_FAST", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    default = "0" if fast else "1"
    return os.getenv("MATRIX_VERTICAL", default).strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def paint(text: str, *, bold: bool = False, dim: bool = False) -> str:
    if not enabled():
        return text
    color = _BOLD_GREEN if bold else (_DIM_GREEN if dim else _GREEN)
    return f"{_BLACK_BG}{color}{text}{_RESET}"


def out(text: str = "", *, bold: bool = False, dim: bool = False) -> None:
    print(paint(text, bold=bold, dim=dim), flush=True)


def vertical_stack(
    text: str,
    *,
    bold: bool = False,
    dim: bool = False,
) -> None:
    """Write each character on its own line (top → bottom)."""
    for ch in text:
        if ch == "\n":
            out("", bold=bold, dim=dim)
        elif ch == " ":
            out("·", bold=bold, dim=True)
        else:
            out(ch, bold=bold, dim=dim)


def vertical_columns(
    text: str,
    *,
    n_cols: int | None = None,
    bold: bool = False,
    dim: bool = False,
    gutter: str = " ",
) -> None:
    """
    Matrix rain layout: top→bottom per column, columns left→right.
    """
    chars = [c if c != "\t" else " " for c in text.replace("\n", " ")]
    if not chars:
        out("", bold=bold, dim=dim)
        return

    if n_cols is None:
        n_cols = max(4, min(14, (len(chars) + 5) // 6))

    height = (len(chars) + n_cols - 1) // n_cols
    while len(chars) < height * n_cols:
        chars.append(" ")

    cols: list[list[str]] = []
    idx = 0
    for _ in range(n_cols):
        cols.append(chars[idx : idx + height])
        idx += height

    for r in range(height):
        cells = []
        for c in range(n_cols):
            ch = cols[c][r]
            cells.append("·" if ch == " " else ch)
        out(gutter.join(cells), bold=bold, dim=dim)


def out_styled(
    text: str = "",
    *,
    bold: bool = False,
    dim: bool = False,
    vertical: bool | None = None,
) -> None:
    """
    Vertical by default:
      - short lines → one glyph per row (stack)
      - longer lines → multi-column rain
    """
    use_v = vertical_enabled() if vertical is None else vertical
    if not use_v or not text.strip():
        out(text, bold=bold, dim=dim)
        return
    stripped = text.strip()
    if len(stripped) <= 36:
        vertical_stack(stripped, bold=bold, dim=dim)
    else:
        vertical_columns(stripped, bold=bold, dim=dim)
    out()  # spacer after a vertical block


def banner() -> None:
    """Boot splash — THE MATRIX stacked vertically."""
    out()
    if vertical_enabled():
        out("╔══╗", bold=True)
        vertical_stack("THE MATRIX", bold=True)
        out("╚══╝", bold=True)
    else:
        out("╔══════════════════════════════════════════════════════════╗", bold=True)
        out("║                    T H E   M A T R I X                   ║", bold=True)
        out("╚══════════════════════════════════════════════════════════╝", bold=True)
    out()
