"""Season arcs — multi-life plot continuity (Smith infection, Zion siege)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_FILE = _PROJECT_ROOT / ".matrix_season.json"

ARCS = ("none", "smith_infection", "zion_siege", "architect_reset")

# Per-arc phase beats — unique content for phases 0–5
PHASE_BEATS: dict[str, list[str]] = {
    "smith_infection": [
        "A cough of code in the rain — one copy too many of Smith.",
        "Phone lines echo with his voice before the receiver lifts.",
        "Crowds begin to wear the same suit. Infection phase rising.",
        "The anomaly fights replication; every choice risks a clone.",
        "City sectors report simultaneous Smith sightings — cascade.",
        "Infection climax: either Neo severs the pattern or Zion falls silent.",
    ],
    "zion_siege": [
        "Dock sensors tick. Machines map tunnels under Zion.",
        "Council debates EMP reserves while diggers scrape closer.",
        "Hovercraft sorties thin. Every life spent raises siege heat.",
        "Sentinel nets tighten around the Nebuchadnezzar's last lanes.",
        "Zion's outer docks burn. Only the One's path may still matter.",
        "Siege endgame: hold the dock or lose the last free city.",
    ],
    "architect_reset": [
        "The Architect opens a new choice tree — prior Anomalies archived.",
        "Systemic reset timers pulse beneath cafe and oracle alike.",
        "Quarantine protocols lock soft exits; control policy hardens.",
        "Meta-game: Oracle and Architect negotiate the next cycle's skew.",
        "Reset pressure: awaken or reintegrate — the equation demands balance.",
        "Reset climax: systemic purge or a flawed peace for Zion.",
    ],
}


def _load() -> dict[str, Any]:
    if not _FILE.exists():
        return {
            "arc": "none",
            "phase": 0,
            "progress": 0,
            "notes": [],
            "updated_at": 0,
        }
    try:
        return json.loads(_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"arc": "none", "phase": 0, "progress": 0, "notes": [], "updated_at": 0}


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = time.time()
    _FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def status() -> dict[str, Any]:
    data = _load()
    data["beat"] = current_beat(data)
    return data


def set_arc(arc: str) -> dict[str, Any]:
    data = _load()
    name = (arc or "none").strip().lower()
    if name not in ARCS:
        name = "none"
    data["arc"] = name
    data["phase"] = 0
    data["progress"] = 0
    data["notes"] = [f"Season arc set → {name}"]
    _save(data)
    return status()


def current_beat(data: dict[str, Any] | None = None) -> str:
    d = data or _load()
    arc = d.get("arc") or "none"
    if arc == "none":
        return ""
    phase = int(d.get("phase") or 0)
    beats = PHASE_BEATS.get(arc) or []
    if not beats:
        return ""
    return beats[min(phase, len(beats) - 1)]


def advance_from_life(result: dict) -> dict[str, Any]:
    """Bump season progress from a finished life."""
    data = _load()
    arc = data.get("arc") or "none"
    if arc == "none":
        return status()
    progress = int(data.get("progress") or 0) + 1
    notes = list(data.get("notes") or [])
    outcome = str(result.get("outcome") or "")
    awakened = bool(result.get("awakened"))
    sticky = result.get("sticky_flags") or {}

    if arc == "smith_infection":
        if "Smith" in outcome or sticky.get("bug_implanted"):
            progress += 2
            notes.append("Infection spreads — Smith pattern strengthens")
        if awakened:
            notes.append("Awakened host resists infection briefly")
            progress = max(0, progress - 1)
        phase = min(5, progress // 2)
    elif arc == "zion_siege":
        if result.get("sentinel_alert") or "flee" in outcome.lower():
            progress += 2
            notes.append("Siege pressure rises — Sentinels close on Zion")
        if result.get("ship_destroyed"):
            progress += 3
            notes.append("A ship was lost — siege accelerates")
        if awakened:
            progress += 1
        phase = min(5, progress // 2)
    elif arc == "architect_reset":
        if str(result.get("meta_policy") or "") in {"control", "purge"}:
            progress += 2
            notes.append("Architect tightens the reset protocol")
        if sticky.get("architect_reset") or sticky.get("architect_quarantine"):
            progress += 1
            notes.append("Architect tree choice echoes into the season")
        phase = min(5, progress // 2)
    else:
        phase = 0

    data["progress"] = progress
    data["phase"] = phase
    beat = current_beat({"arc": arc, "phase": phase})
    if beat:
        notes.append(f"Phase {phase}: {beat}")
    data["notes"] = notes[-30:]
    _save(data)
    return status()


def prompt_flavor() -> str:
    data = _load()
    arc = data.get("arc") or "none"
    if arc == "none":
        return ""
    beat = current_beat(data)
    return (
        f"Season arc={arc} phase={data.get('phase')}/5 "
        f"progress={data.get('progress')}. "
        f"Current beat: {beat} "
        "Factor this long-running plot into your choice."
    )


def phase_event_tag() -> str:
    data = _load()
    arc = data.get("arc") or "none"
    if arc == "none":
        return ""
    return f"season:{arc}:phase{int(data.get('phase') or 0)}"
