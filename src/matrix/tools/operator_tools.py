"""Operator-side helpers (outside the Matrix) — radio, EMP, jack-out, CCTV."""

from __future__ import annotations

from typing import Any


def radio(message: str) -> str:
    return f"[Zion uplink] {message}"


def emp_pulse(state: dict) -> dict[str, Any]:
    """Clear local machine pressure; burns hardline cooldown."""
    from matrix.surveillance import bump_trace

    patch = bump_trace(state, -15.0, "emp_pulse")
    patch.update(
        {
            "sentinel_alert": False,
            "hardline_cooldown": max(int(state.get("hardline_cooldown") or 0), 2),
            "events": ["operator:emp"],
            "log": ["[operator] EMP pulse — Sentinels blinded briefly"],
            "faction_scoreboard": {"zion": 3, "agents": 0, "system": 0},
        }
    )
    return patch


def jack_out_vector(state: dict) -> dict[str, Any]:
    """Force an exit attempt if hardline is available."""
    from matrix.surveillance import hardline_available, use_hardline

    if not hardline_available(state):
        return {
            "events": ["operator:jack_out_blocked"],
            "log": ["[operator] jack-out blocked — hardline cooling"],
        }
    patch = use_hardline(state)
    patch["events"] = list(patch.get("events") or []) + ["operator:jack_out"]
    patch["log"] = list(patch.get("log") or []) + ["[operator] jack-out vector opened"]
    patch["faction_scoreboard"] = {"zion": 2, "agents": 0, "system": 0}
    return patch


def watch_cctv(state: dict, sector: str) -> dict[str, Any]:
    """Operator CCTV linger — raises heat on a watched sector, drops trace slightly."""
    from matrix.surveillance import bump_trace

    heat = dict(state.get("sector_heat") or {})
    heat[sector] = float(heat.get(sector, 0)) + 5.0
    patch = bump_trace(state, -2.0, f"cctv@{sector}")
    patch.update(
        {
            "sector_heat": heat,
            "events": [f"operator:cctv:{sector}"],
            "log": [f"[operator] CCTV locked on {sector}"],
        }
    )
    return patch


def load_skill(state: dict, skill: str) -> dict[str, Any]:
    skills = list(state.get("training_skills") or [])
    name = (skill or "combat").strip().lower()
    if name not in skills:
        skills.append(name)
    score = int(state.get("training_score") or 0) + 1
    return {
        "training_skills": skills,
        "training_score": score,
        "events": [f"operator:load:{name}"],
        "log": [f"[operator] loaded skill program: {name}"],
        "faction_scoreboard": {"zion": 1, "agents": 0, "system": 0},
    }
