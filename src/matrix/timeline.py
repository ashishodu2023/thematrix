"""Decision timeline — every fork / HITL / director action with why."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_FILE = _PROJECT_ROOT / ".matrix_timeline.json"


def _load() -> list[dict[str, Any]]:
    if not _FILE.exists():
        return []
    try:
        return list(json.loads(_FILE.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    _FILE.write_text(json.dumps(rows[-200:], indent=2, default=str), encoding="utf-8")


def record(
    *,
    kind: str,
    choice: str = "",
    why: str = "",
    scene: str = "",
    cycle: int | None = None,
    meta: dict | None = None,
) -> dict[str, Any]:
    row = {
        "at": time.time(),
        "kind": kind,
        "choice": choice,
        "why": why,
        "scene": scene,
        "cycle": cycle,
        "meta": meta or {},
    }
    rows = _load()
    rows.append(row)
    _save(rows)
    return row


def list_timeline(limit: int = 80) -> list[dict[str, Any]]:
    rows = _load()
    return rows[-limit:]


def clear() -> None:
    _save([])
