"""Operator Console commands — move Neo, hardline, linger, tools."""

from __future__ import annotations

from typing import Any

from matrix.city_graph import neighbors, shortest_path
from matrix.surveillance import bump_trace, hardline_available, linger_penalty, tap_phone, use_hardline
from matrix.tools import operator_tools


def available_moves(state: dict) -> list[str]:
    loc = str(state.get("location") or "")
    return list(neighbors(loc)) if loc else []


def apply_command(
    state: dict,
    *,
    command: str,
    target: str = "",
    seat: str = "operator",
) -> dict[str, Any]:
    """
    Apply an Operator / seat command as a state patch.
    Commands: move, linger, hardline, tap, emp, jack_out, cctv, load_skill
    """
    cmd = (command or "").strip().lower()
    tgt = (target or "").strip()
    seat_l = (seat or "operator").strip().lower()

    # Seat permissions
    if seat_l == "neo" and cmd in {"emp", "load_skill", "cctv"}:
        return {"ok": False, "error": "Neo seat cannot use Operator-only tools"}
    if seat_l == "trinity" and cmd in {"emp", "load_skill"}:
        return {"ok": False, "error": "Trinity seat: move / hardline / tap / linger only"}

    if cmd == "move":
        loc = str(state.get("location") or "")
        if not tgt:
            return {"ok": False, "error": "move requires target sector"}
        if tgt not in neighbors(loc) and tgt != loc:
            # allow path if connected
            path = shortest_path(loc, tgt)
            if not path or len(path) < 2:
                return {"ok": False, "error": f"no route {loc} → {tgt}"}
            # take one hop toward target
            nxt = path[1]
        else:
            nxt = tgt
        positions = dict(state.get("agent_positions") or {})
        positions["neo"] = nxt
        if seat_l in positions or seat_l in {"trinity"}:
            positions[seat_l if seat_l != "operator" else "trinity"] = nxt
        patch = bump_trace(state, 3.0, f"move:{loc}->{nxt}")
        patch.update(
            {
                "ok": True,
                "location": nxt,
                "agent_positions": positions,
                "locations_visited": [nxt],
                "events": [f"operator:move:{nxt}"],
                "log": [f"[operator/{seat_l}] moved Neo {loc} → {nxt}"],
                "feed_line": f"OPERATOR ({seat_l}): move → {nxt}",
            }
        )
        return patch

    if cmd == "linger":
        patch = linger_penalty(state)
        patch["ok"] = True
        patch["feed_line"] = f"OPERATOR ({seat_l}): linger @ {state.get('location')}"
        return patch

    if cmd == "hardline":
        if not hardline_available(state):
            return {
                "ok": False,
                "error": "hardline cooling down",
                "hardline_cooldown": state.get("hardline_cooldown"),
            }
        patch = use_hardline(state)
        patch["ok"] = True
        patch["feed_line"] = f"OPERATOR ({seat_l}): hardline exit"
        patch["faction_scoreboard"] = {"zion": 2, "agents": 0, "system": 0}
        return patch

    if cmd == "tap":
        line = tgt or f"line@{state.get('location')}"
        patch = tap_phone(line)
        extra = bump_trace(state, 6.0, f"tap:{line[:24]}")
        patch.update({k: v for k, v in extra.items() if k != "events"})
        patch["events"] = list(patch.get("events") or []) + list(extra.get("events") or [])
        patch["ok"] = True
        patch["feed_line"] = f"OPERATOR ({seat_l}): tap {line}"
        patch["faction_scoreboard"] = {"zion": 0, "agents": 1, "system": 0}
        return patch

    if cmd == "emp":
        patch = operator_tools.emp_pulse(state)
        patch["ok"] = True
        patch["feed_line"] = f"OPERATOR ({seat_l}): EMP"
        return patch

    if cmd == "jack_out":
        patch = operator_tools.jack_out_vector(state)
        patch["ok"] = "operator:jack_out" in (patch.get("events") or [])
        if not patch["ok"]:
            patch["error"] = "jack-out blocked"
        patch["feed_line"] = f"OPERATOR ({seat_l}): jack-out"
        return patch

    if cmd == "cctv":
        sector = tgt or str(state.get("location") or "jack_point")
        patch = operator_tools.watch_cctv(state, sector)
        patch["ok"] = True
        patch["feed_line"] = f"OPERATOR ({seat_l}): CCTV {sector}"
        return patch

    if cmd == "load_skill":
        patch = operator_tools.load_skill(state, tgt or "jujitsu")
        patch["ok"] = True
        patch["feed_line"] = f"OPERATOR ({seat_l}): load {tgt or 'jujitsu'}"
        return patch

    return {"ok": False, "error": f"unknown command {cmd}"}
