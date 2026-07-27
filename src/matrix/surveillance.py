"""Surveillance — trace, phone taps, hardline cooldowns, CCTV heat."""

from __future__ import annotations

from matrix.city_graph import neighbors


def bump_trace(state: dict, amount: float, reason: str) -> dict:
    trace = float(state.get("trace_level") or 0) + amount
    trace = max(0.0, min(100.0, trace))
    events = [f"trace:{reason}:{trace:.1f}"]
    return {
        "trace_level": trace,
        "events": events,
        "log": [f"[trace] {reason} → {trace:.1f}"],
    }


def linger_penalty(state: dict) -> dict:
    """Staying put raises Agent attention."""
    return bump_trace(state, 4.0, f"linger@{state.get('location')}")


def hardline_available(state: dict) -> bool:
    cd = int(state.get("hardline_cooldown") or 0)
    return cd <= 0


def use_hardline(state: dict) -> dict:
    return {
        "hardline_cooldown": 3,
        "events": ["hardline:used"],
        "log": ["[hardline] exit vector burned — cooldown 3"],
        **bump_trace(state, -8.0, "hardline_exit"),
    }


def tick_cooldowns(state: dict) -> dict:
    cd = max(0, int(state.get("hardline_cooldown") or 0) - 1)
    taps = list(state.get("phone_taps") or [])
    heat = dict(state.get("sector_heat") or {})
    loc = str(state.get("location") or "")
    if loc:
        heat[loc] = float(heat.get(loc, 0)) + 2.0
        for n in neighbors(loc):
            heat[n] = float(heat.get(n, 0)) + 0.5
    # decay
    heat = {k: max(0.0, v - 0.3) for k, v in heat.items() if v > 0.3}
    patch = {
        "hardline_cooldown": cd,
        "sector_heat": heat,
        "phone_taps": taps,
    }
    if float(state.get("trace_level") or 0) > 0:
        patch["trace_level"] = max(0.0, float(state["trace_level"]) - 0.5)
    return patch


def tap_phone(line: str) -> dict:
    return {
        "phone_taps": [line],
        "events": [f"tap:{line[:40]}"],
        "log": [f"[surveillance] tap: {line}"],
    }
