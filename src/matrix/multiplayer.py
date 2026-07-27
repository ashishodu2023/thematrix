"""Multi-seat coordination — Neo + Trinity can both be required for some HITLs."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SEATS_FILE = _PROJECT_ROOT / ".matrix_seats.json"

# Decisions that need Neo + Trinity when MATRIX_MULTI_SEAT=1
DUAL_SEAT_KINDS = frozenset({"fight_or_flee", "key"})


def _load() -> dict[str, Any]:
    if not _SEATS_FILE.exists():
        return {"online": {}, "votes": {}}
    try:
        return json.loads(_SEATS_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"online": {}, "votes": {}}


def _save(data: dict[str, Any]) -> None:
    _SEATS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def heartbeat(seat: str) -> dict[str, Any]:
    data = _load()
    online = dict(data.get("online") or {})
    online[seat] = time.time()
    # drop stale (>90s)
    now = time.time()
    online = {s: t for s, t in online.items() if now - float(t) < 90}
    data["online"] = online
    _save(data)
    return {"ok": True, "online": list(online.keys())}


def online_seats() -> list[str]:
    data = _load()
    now = time.time()
    return [
        s
        for s, t in (data.get("online") or {}).items()
        if now - float(t) < 90
    ]


def clear_votes(kind: str = "") -> None:
    data = _load()
    if kind:
        votes = dict(data.get("votes") or {})
        votes.pop(kind, None)
        data["votes"] = votes
    else:
        data["votes"] = {}
    _save(data)


def record_vote(kind: str, seat: str, choice: str) -> dict[str, Any]:
    data = _load()
    votes = dict(data.get("votes") or {})
    bucket = dict(votes.get(kind) or {})
    bucket[seat] = {"choice": choice, "at": time.time()}
    votes[kind] = bucket
    data["votes"] = votes
    _save(data)
    return resolve_votes(kind)


def resolve_votes(kind: str) -> dict[str, Any]:
    data = _load()
    bucket = dict((data.get("votes") or {}).get(kind) or {})
    online = set(online_seats())
    needed = {"neo", "trinity"} if kind in DUAL_SEAT_KINDS else {"operator"}
    # If dual seats not online, operator alone can decide
    if kind in DUAL_SEAT_KINDS and not ({"neo", "trinity"} <= online):
        if "operator" in bucket:
            return {
                "ready": True,
                "choice": bucket["operator"]["choice"],
                "votes": bucket,
                "mode": "operator_fallback",
            }
        return {"ready": False, "needed": ["operator"], "votes": bucket}

    missing = [s for s in needed if s not in bucket]
    if missing:
        return {"ready": False, "needed": missing, "votes": bucket}

    # Prefer agreement; else Neo wins for dual
    choices = {s: bucket[s]["choice"] for s in needed if s in bucket}
    vals = list(choices.values())
    if len(set(vals)) == 1:
        choice = vals[0]
    else:
        choice = choices.get("neo") or choices.get("operator") or vals[0]
    return {"ready": True, "choice": choice, "votes": bucket, "mode": "multi"}
