"""True multiplayer agency — per-seat command queues + shared world intents."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_AGENCY_FILE = _PROJECT_ROOT / ".matrix_agency.json"

# Seats that can inject independent world intents (not just HITL votes)
AGENCY_SEATS = frozenset({"neo", "trinity", "operator"})

# Commands each seat may issue as their own agency
SEAT_COMMANDS: dict[str, frozenset[str]] = {
    "neo": frozenset({"move", "linger", "dodge", "believe", "fight", "flee"}),
    "trinity": frozenset({"move", "cover", "hardline", "tap", "extract"}),
    "operator": frozenset(
        {"move", "linger", "hardline", "tap", "cctv", "emp", "jack_out", "load_skill"}
    ),
}


def multiplayer_agency_enabled() -> bool:
    return os.getenv("MATRIX_TRUE_MP", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _load() -> dict[str, Any]:
    if not _AGENCY_FILE.exists():
        return {"intents": [], "last_by_seat": {}}
    try:
        return json.loads(_AGENCY_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"intents": [], "last_by_seat": {}}


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = time.time()
    _AGENCY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def queue_intent(
    seat: str,
    command: str,
    *,
    target: str = "",
    detail: str = "",
) -> dict[str, Any]:
    """Queue an independent seat action (true agency, not a shared vote)."""
    seat_l = (seat or "operator").strip().lower()
    cmd = (command or "").strip().lower()
    allowed = SEAT_COMMANDS.get(seat_l) or frozenset()
    if seat_l not in AGENCY_SEATS:
        return {"ok": False, "error": f"unknown seat {seat_l}"}
    if cmd not in allowed:
        return {
            "ok": False,
            "error": f"seat {seat_l} cannot run {cmd}",
            "allowed": sorted(allowed),
        }
    data = _load()
    intent = {
        "id": f"{seat_l}-{int(time.time() * 1000)}",
        "seat": seat_l,
        "command": cmd,
        "target": (target or "").strip(),
        "detail": (detail or "").strip(),
        "at": time.time(),
    }
    intents = list(data.get("intents") or [])
    intents.append(intent)
    data["intents"] = intents[-40:]
    last = dict(data.get("last_by_seat") or {})
    last[seat_l] = intent
    data["last_by_seat"] = last
    _save(data)
    return {"ok": True, "intent": intent, "queued": len(data["intents"])}


def pop_intents(limit: int = 8) -> list[dict[str, Any]]:
    data = _load()
    intents = list(data.get("intents") or [])
    if not intents:
        return []
    take = intents[:limit]
    data["intents"] = intents[limit:]
    _save(data)
    return take


def peek() -> dict[str, Any]:
    data = _load()
    return {
        "queued": len(data.get("intents") or []),
        "last_by_seat": data.get("last_by_seat") or {},
        "enabled": multiplayer_agency_enabled(),
    }


def apply_intent_to_state(state: dict, intent: dict) -> dict[str, Any]:
    """Map a seat intent onto operator_commands / sticky patches."""
    from matrix.operator_commands import apply_command

    seat = str(intent.get("seat") or "operator")
    cmd = str(intent.get("command") or "")
    target = str(intent.get("target") or "")
    # Alias seat-flavored verbs onto operator command surface
    alias = {
        "dodge": "linger",
        "believe": "linger",
        "fight": "move",
        "flee": "move",
        "cover": "linger",
        "extract": "hardline",
    }
    mapped = alias.get(cmd, cmd)
    out = apply_command(state, command=mapped, target=target, seat=seat)
    sticky = dict(state.get("sticky_flags") or {})
    sticky[f"agency_{seat}"] = cmd
    out["sticky_flags"] = {**(out.get("sticky_flags") or {}), **sticky}
    out["events"] = list(out.get("events") or []) + [f"agency:{seat}:{cmd}"]
    out["feed_line"] = out.get("feed_line") or f"{seat.upper()} agency → {cmd} {target}".strip()
    return out


def merge_agency_into(state: dict, *, limit: int = 6) -> dict:
    """
    Drain queued seat intents into live graph state (true multiplayer).
    Mutates and returns `state` so nodes see player agency before acting.
    """
    if not multiplayer_agency_enabled():
        return state
    intents = pop_intents(limit=limit)
    if not intents:
        return state
    feed: list[str] = []
    for intent in intents:
        try:
            patch = apply_intent_to_state(state, intent)
        except Exception:  # noqa: BLE001
            continue
        if not patch.get("ok", True) and patch.get("error"):
            continue
        for k, v in patch.items():
            if k in {"ok", "error", "feed_line"}:
                continue
            if k in {
                "events",
                "log",
                "phone_taps",
                "locations_visited",
                "character_actions",
                "agent_memory",
            }:
                state[k] = list(state.get(k) or []) + list(v if isinstance(v, list) else [v])
            elif k == "sticky_flags" and isinstance(v, dict):
                state[k] = {**(state.get(k) or {}), **v}
            elif k == "faction_scoreboard" and isinstance(v, dict):
                board = dict(state.get(k) or {})
                for fk, fv in v.items():
                    board[fk] = int(board.get(fk) or 0) + int(fv or 0)
                state[k] = board
            else:
                state[k] = v
        if patch.get("feed_line"):
            feed.append(str(patch["feed_line"]))
    if feed:
        try:
            from matrix import dashboard

            dashboard.publish({"feed_append": feed, "status": "agency", "agency": peek()})
        except Exception:  # noqa: BLE001
            pass
    return state
