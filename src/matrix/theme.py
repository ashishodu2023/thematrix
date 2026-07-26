"""Matrix terminal theme — green text on black background (ANSI)."""

from __future__ import annotations

import os
import sys

# Bright Matrix green on black
_RESET = "\033[0m"
_GREEN = "\033[92m"
_DIM_GREEN = "\033[32m"
_BOLD_GREEN = "\033[1;92m"
_BLACK_BG = "\033[40m"
_PREFIX = f"{_BLACK_BG}{_GREEN}"


def enabled() -> bool:
    if os.getenv("MATRIX_NO_COLOR", "").strip() in {"1", "true", "yes"}:
        return False
    if os.getenv("NO_COLOR", "").strip():
        return False
    return sys.stdout.isatty()


def paint(text: str, *, bold: bool = False, dim: bool = False) -> str:
    if not enabled():
        return text
    color = _BOLD_GREEN if bold else (_DIM_GREEN if dim else _GREEN)
    return f"{_BLACK_BG}{color}{text}{_RESET}"


def out(text: str = "", *, bold: bool = False, dim: bool = False) -> None:
    """Print one Matrix-styled line (green on black)."""
    print(paint(text, bold=bold, dim=dim), flush=True)


def banner() -> None:
    """Boot splash for jack-in / daemon."""
    lines = [
        "",
        "╔══════════════════════════════════════════════════════════╗",
        "║                    T H E   M A T R I X                   ║",
        "║         LangGraph · Ollama · Multi-Agent Simulation      ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
    ]
    for line in lines:
        out(line, bold=True)
