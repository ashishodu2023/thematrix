"""Sentinel / EMP mini-game — real-time heat when jacked toward the Real."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_FILE = _PROJECT_ROOT / ".matrix_emp_game.json"


def _load() -> dict[str, Any]:
    if not _FILE.exists():
        return {
            "heat": 40.0,
            "charges": 3,
            "alive": True,
            "score": 0,
            "updated_at": 0,
            "log": [],
            "ship_outcome": "",
        }
    try:
        return json.loads(_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {
            "heat": 40.0,
            "charges": 3,
            "alive": True,
            "score": 0,
            "updated_at": 0,
            "log": [],
            "ship_outcome": "",
        }


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = time.time()
    _FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def status() -> dict[str, Any]:
    data = _load()
    # Passive heat creep while alive
    if data.get("alive") and data.get("updated_at"):
        dt = max(0.0, time.time() - float(data["updated_at"]))
        if dt > 0.8:
            data["heat"] = min(100.0, float(data.get("heat") or 0) + dt * 2.5)
            if data["heat"] >= 100:
                data["alive"] = False
                data["ship_outcome"] = "destroyed"
                data["log"] = list(data.get("log") or []) + ["Sentinels cracked the hull"]
            _save(data)
    return data


def reset() -> dict[str, Any]:
    data = {
        "heat": 35.0,
        "charges": 3,
        "alive": True,
        "score": 0,
        "updated_at": time.time(),
        "log": ["EMP board armed"],
        "ship_outcome": "",
    }
    _save(data)
    return data


def pulse() -> dict[str, Any]:
    data = status()
    if not data.get("alive"):
        return {**data, "ok": False, "error": "ship destroyed — reset"}
    charges = int(data.get("charges") or 0)
    if charges <= 0:
        return {**data, "ok": False, "error": "no EMP charges"}
    data["charges"] = charges - 1
    data["heat"] = max(0.0, float(data.get("heat") or 0) - 28.0)
    data["score"] = int(data.get("score") or 0) + 10
    data["ship_outcome"] = "emp_cleared"
    data["log"] = list(data.get("log") or []) + [f"EMP pulse — heat {data['heat']:.0f}"]
    _save(data)
    return {**data, "ok": True}


def sync_from_state(state: dict) -> dict[str, Any]:
    """Nudge mini-game heat from live sentinel_alert / sector heat."""
    data = status()
    if state.get("sentinel_alert"):
        data["heat"] = min(100.0, float(data.get("heat") or 0) + 8.0)
    heat_map = state.get("sector_heat") or {}
    if heat_map:
        avg = sum(float(v) for v in heat_map.values()) / max(1, len(heat_map))
        data["heat"] = min(100.0, max(float(data.get("heat") or 0), avg * 0.4))
    if data["heat"] >= 100:
        data["alive"] = False
        data["ship_outcome"] = "destroyed"
    _save(data)
    return data


def apply_to_ship_state(state: dict) -> dict[str, Any]:
    """
    Couple EMP mini-game → graph ship outcomes for sentinel_scan / hunt.
    Returns a state patch consumed by Act III nodes.
    """
    data = sync_from_state(state)
    heat = float(data.get("heat") or 0)
    alive = bool(data.get("alive", True))
    patch: dict[str, Any] = {
        "emp_heat": heat,
        "emp_charges": int(data.get("charges") or 0),
        "emp_score": int(data.get("score") or 0),
    }
    sticky = dict(state.get("sticky_flags") or {})
    events: list[str] = []
    log: list[str] = []

    if not alive or heat >= 100:
        sticky["ship_destroyed"] = True
        patch["ship_destroyed"] = True
        patch["sentinel_alert"] = True
        patch["outcome_hint"] = "Sentinels cracked the hull — ship lost"
        events.append("emp:ship_destroyed")
        log.append("[emp] hull breached — ship destroyed")
        data["ship_outcome"] = "destroyed"
    elif heat >= 75:
        sticky["hull_critical"] = True
        patch["sentinel_alert"] = True
        events.append("emp:hull_critical")
        log.append(f"[emp] hull critical heat={heat:.0f}")
        data["ship_outcome"] = "critical"
    elif str(data.get("ship_outcome") or "") == "emp_cleared" or heat < 40:
        sticky.pop("hull_critical", None)
        if heat < 35 and int(data.get("charges") or 0) < 3:
            # Successful recent pulse — clear alert briefly
            patch["sentinel_alert"] = False
            events.append("emp:cleared")
            log.append("[emp] pulse bought silence")
            sticky["emp_cleared"] = True
            data["ship_outcome"] = "held"

    patch["sticky_flags"] = sticky
    patch["events"] = events
    patch["log"] = log
    _save(data)
    return patch
