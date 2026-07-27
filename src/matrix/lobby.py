"""Networked lobby — join codes so Neo / Trinity / Operator claim seats."""

from __future__ import annotations

import json
import random
import string
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_FILE = _PROJECT_ROOT / ".matrix_lobby.json"

SEATS = ("neo", "trinity", "operator")


def _code(n: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def _load() -> dict[str, Any]:
    if not _FILE.exists():
        return {"code": "", "seats": {}, "created_at": 0, "host": ""}
    try:
        return json.loads(_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"code": "", "seats": {}, "created_at": 0, "host": ""}


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = time.time()
    _FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def status() -> dict[str, Any]:
    data = _load()
    now = time.time()
    seats = {}
    for seat, info in (data.get("seats") or {}).items():
        last = float((info or {}).get("seen_at") or 0)
        seats[seat] = {
            **(info or {}),
            "online": (now - last) < 90 if last else False,
        }
    return {
        "code": data.get("code") or "",
        "host": data.get("host") or "",
        "seats": seats,
        "created_at": data.get("created_at") or 0,
        "open": bool(data.get("code")),
    }


def create(*, host: str = "operator") -> dict[str, Any]:
    data = {
        "code": _code(),
        "host": (host or "operator").strip().lower(),
        "seats": {},
        "created_at": time.time(),
    }
    _save(data)
    return status()


def join(code: str, seat: str, *, name: str = "") -> dict[str, Any]:
    data = _load()
    want = (code or "").strip().upper()
    if not data.get("code") or want != str(data["code"]).upper():
        return {"ok": False, "error": "invalid lobby code", **status()}
    seat_l = (seat or "").strip().lower()
    if seat_l not in SEATS:
        return {"ok": False, "error": f"seat must be one of {SEATS}", **status()}
    seats = dict(data.get("seats") or {})
    existing = seats.get(seat_l) or {}
    # Allow reclaim if same name or stale
    if existing.get("name") and name and existing["name"] != name:
        last = float(existing.get("seen_at") or 0)
        if time.time() - last < 90:
            return {"ok": False, "error": f"{seat_l} already claimed", **status()}
    seats[seat_l] = {
        "name": (name or seat_l).strip()[:40],
        "seen_at": time.time(),
        "joined_at": float(existing.get("joined_at") or time.time()),
    }
    data["seats"] = seats
    _save(data)
    try:
        from matrix.multiplayer import heartbeat

        heartbeat(seat_l)
    except Exception:  # noqa: BLE001
        pass
    return {"ok": True, "seat": seat_l, **status()}


def leave(seat: str) -> dict[str, Any]:
    data = _load()
    seats = dict(data.get("seats") or {})
    seats.pop((seat or "").strip().lower(), None)
    data["seats"] = seats
    _save(data)
    return {"ok": True, **status()}


def close() -> dict[str, Any]:
    _save({"code": "", "seats": {}, "created_at": 0, "host": ""})
    return {"ok": True, **status()}


def touch(seat: str) -> dict[str, Any]:
    data = _load()
    seat_l = (seat or "").strip().lower()
    seats = dict(data.get("seats") or {})
    if seat_l in seats:
        seats[seat_l]["seen_at"] = time.time()
        data["seats"] = seats
        _save(data)
    return status()
