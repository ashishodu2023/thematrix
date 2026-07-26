"""Active LangGraph thread id — fresh each jack-in, shared with resume."""

from __future__ import annotations

import uuid
from pathlib import Path

# Project root: .../matrix/ (src/matrix/thread_store.py → parents[2])
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_THREAD_FILE = _PROJECT_ROOT / ".active_thread"


def new_thread_id(human_id: str = "neo") -> str:
    thread_id = f"matrix-{human_id}-{uuid.uuid4().hex[:8]}"
    save_active_thread(thread_id)
    return thread_id


def save_active_thread(thread_id: str) -> None:
    _THREAD_FILE.write_text(thread_id.strip() + "\n", encoding="utf-8")


def load_active_thread() -> str:
    if not _THREAD_FILE.exists():
        raise FileNotFoundError(
            "No active jack-in found. Run `uv run matrix-jack-in` first."
        )
    thread_id = _THREAD_FILE.read_text(encoding="utf-8").strip()
    if not thread_id:
        raise FileNotFoundError(
            "Active thread file is empty. Run `uv run matrix-jack-in` first."
        )
    return thread_id
