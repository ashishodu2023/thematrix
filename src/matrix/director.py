"""Director mode — pause continuous play, force branch hints, inject events."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DIR_FILE = _PROJECT_ROOT / ".matrix_director.json"


def _load() -> dict[str, Any]:
    if not _DIR_FILE.exists():
        return {"paused": False, "force_branch": "", "injects": [], "updated_at": 0}
    try:
        return json.loads(_DIR_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"paused": False, "force_branch": "", "injects": [], "updated_at": 0}


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = time.time()
    _DIR_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def status() -> dict[str, Any]:
    return _load()


def set_paused(paused: bool) -> dict[str, Any]:
    data = _load()
    data["paused"] = bool(paused)
    _save(data)
    return data


def force_branch(target: str) -> dict[str, Any]:
    data = _load()
    data["force_branch"] = (target or "").strip()
    _save(data)
    return data


def peek_force_branch() -> str:
    return str(_load().get("force_branch") or "")


def clear_force() -> dict[str, Any]:
    data = _load()
    data["force_branch"] = ""
    _save(data)
    return data


def consume_force_branch() -> str:
    data = _load()
    target = str(data.get("force_branch") or "")
    if target:
        data["force_branch"] = ""
        _save(data)
    return target


def inject(event: str, detail: str = "") -> dict[str, Any]:
    data = _load()
    injects = list(data.get("injects") or [])
    injects.append(
        {
            "event": (event or "glitch").strip(),
            "detail": (detail or "").strip(),
            "at": time.time(),
        }
    )
    data["injects"] = injects[-20:]
    _save(data)
    return data


def pop_injects() -> list[dict[str, Any]]:
    data = _load()
    items = list(data.get("injects") or [])
    data["injects"] = []
    _save(data)
    return items


def wait_if_paused(*, poll: float = 0.4) -> None:
    """Block daemon between lives while Director pause is on."""
    while _load().get("paused"):
        time.sleep(poll)
