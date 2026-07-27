"""HITL bridge — Operator Console can answer interrupts; daemon waits then falls back."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_HITL_PENDING = _PROJECT_ROOT / ".matrix_hitl_pending.json"
_HITL_CHOICE = _PROJECT_ROOT / ".matrix_hitl_choice.json"

HITL_OPTIONS: dict[str, list[str]] = {
    "bug": ["extract", "refuse"],
    "trust": ["trust", "walk"],
    "pill": ["red", "blue"],
    "steak": ["steak", "refuse"],
    "jump": ["jump", "hesitate"],
    "fight_or_flee": ["fight", "flee"],
    "radio": ["call", "silent"],
    "code": ["accept", "deny"],
    "key": ["take_key", "refuse_key"],
    "oracle_question": [
        "Am I the One?",
        "What is the Matrix?",
        "Why am I here?",
    ],
}

# Which seats may answer which HITL kinds
SEAT_KINDS: dict[str, set[str]] = {
    "neo": {"bug", "pill", "jump", "fight_or_flee", "code", "key", "oracle_question"},
    "trinity": {"trust", "fight_or_flee", "radio", "key"},
    "operator": set(HITL_OPTIONS.keys()),
}


def options_for(kind: str, *, seat: str = "operator") -> list[str]:
    base = list(HITL_OPTIONS.get(kind, ["red"]))
    seat_l = (seat or "operator").strip().lower()
    allowed_kinds = SEAT_KINDS.get(seat_l) or SEAT_KINDS["operator"]
    if kind and kind not in allowed_kinds and seat_l != "operator":
        # Seat can still see options but UI should prefer operator — return empty signal
        return base
    return base


def seat_may_answer(kind: str, seat: str) -> bool:
    seat_l = (seat or "operator").strip().lower()
    if seat_l == "operator":
        return True
    return kind in (SEAT_KINDS.get(seat_l) or set())


def preferred_seat(kind: str) -> str:
    if kind in {"trust", "radio"}:
        return "trinity"
    if kind in {"bug", "pill", "jump", "code", "key", "oracle_question", "fight_or_flee"}:
        return "neo"
    return "operator"


def publish_pending(
    *,
    thread_id: str,
    kind: str,
    message: str = "",
    seat: str = "",
) -> dict[str, Any]:
    prefer = seat or preferred_seat(kind)
    payload = {
        "thread_id": thread_id,
        "kind": kind,
        "options": options_for(kind, seat=prefer),
        "message": message or f"Choose for {kind}",
        "seat": prefer,
        "allowed_seats": [
            s for s, kinds in SEAT_KINDS.items() if kind in kinds or s == "operator"
        ],
        "opened_at": time.time(),
    }
    _HITL_PENDING.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if _HITL_CHOICE.exists():
        _HITL_CHOICE.unlink(missing_ok=True)
    return payload


def clear_pending() -> None:
    _HITL_PENDING.unlink(missing_ok=True)
    _HITL_CHOICE.unlink(missing_ok=True)


def read_pending() -> dict[str, Any] | None:
    if not _HITL_PENDING.exists():
        return None
    try:
        return json.loads(_HITL_PENDING.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def submit_choice(
    choice: str,
    *,
    thread_id: str | None = None,
    seat: str = "operator",
) -> dict[str, Any]:
    pending = read_pending() or {}
    tid = thread_id or pending.get("thread_id") or ""
    kind = str(pending.get("kind") or "")
    if kind and not seat_may_answer(kind, seat):
        raise ValueError(f"Seat {seat!r} cannot answer HITL kind {kind!r}")
    allowed = options_for(kind, seat=seat) if kind else []
    text = str(choice).strip()
    if kind and kind != "oracle_question" and allowed:
        lowered = text.lower()
        if lowered not in {a.lower() for a in allowed}:
            raise ValueError(f"Invalid choice {text!r}; expected one of {allowed}")
        text = next(a for a in allowed if a.lower() == lowered)
    payload = {
        "thread_id": tid,
        "kind": kind,
        "choice": text,
        "seat": seat,
        "submitted_at": time.time(),
    }
    _HITL_CHOICE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def wait_for_choice(
    thread_id: str,
    *,
    timeout: float = 45.0,
    poll: float = 0.35,
) -> str | None:
    """Block until console submits a choice for this thread, or timeout."""
    deadline = time.time() + max(0.0, timeout)
    while time.time() < deadline:
        if _HITL_CHOICE.exists():
            try:
                data = json.loads(_HITL_CHOICE.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                time.sleep(poll)
                continue
            if str(data.get("thread_id") or "") in {"", thread_id}:
                choice = str(data.get("choice") or "").strip()
                clear_pending()
                return choice or None
        time.sleep(poll)
    return None
