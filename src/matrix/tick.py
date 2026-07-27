"""World clock — Agents patrol the city graph; full cast stays visible on the map."""

from __future__ import annotations

from matrix import cast as matrix_cast
from matrix import sound as matrix_sound
from matrix import story
from matrix.city_graph import location_name, step_toward
from matrix.minds import MindStore
from matrix.surveillance import linger_penalty, tick_cooldowns


def world_tick(state: dict, *, neo_target: str | None = None) -> dict:
    """
    One simulation tick:
    - cooldowns / sector heat / trace decay
    - Agents pathfind toward Neo
    - Zion crew drifts toward Neo when in-city
    - cast map stays fully populated
    """
    patches: dict = dict(tick_cooldowns(state))
    loc = str(neo_target or state.get("location") or "jack_point")

    live = {**state, **patches, "location": loc}
    agent_positions = matrix_cast.ensure_cast(live)
    moves: list[str] = []
    events: list[str] = list(patches.get("events") or [])
    logs: list[str] = list(patches.get("log") or [])

    for agent in state.get("agent_names") or ["Smith", "Jones", "Brown"]:
        key = agent.strip().lower()
        mind = MindStore.load(key)
        hunt = mind.last_known_neo_location or loc
        cur = agent_positions.get(key) or "subway"
        nxt = step_toward(cur, hunt)
        agent_positions[key] = nxt
        if nxt != cur:
            moves.append(f"{agent}: {location_name(cur)} → {location_name(nxt)}")
            MindStore.remember(key, f"Patrolled toward {hunt}", neo_location=loc)
        if nxt == loc:
            lp = linger_penalty({**state, **patches, "location": loc})
            if "trace_level" in lp:
                patches["trace_level"] = lp["trace_level"]
            events.extend(lp.get("events") or [])
            logs.extend(lp.get("log") or [])
            moves.append(f"{agent} heat-lock on Neo's sector")
            matrix_sound.play("agent")

    # Zion extraction team drifts toward Neo when inside Mega City
    city_nodes = {
        "jack_point",
        "apartment",
        "club",
        "oracle_apartment",
        "cafe",
        "hotel_lobby",
        "subway",
        "rooftop",
        "highway",
    }
    if loc in city_nodes:
        for who in ("trinity", "morpheus"):
            cur = agent_positions.get(who) or matrix_cast.CAST_HOME[who]
            if cur in city_nodes or cur == "nebuchadnezzar":
                # Exit ship → jack_point then hunt
                start = "jack_point" if cur == "nebuchadnezzar" else cur
                nxt = step_toward(start, loc)
                if nxt != cur:
                    moves.append(
                        f"{who}: {location_name(cur)} → {location_name(nxt)}"
                    )
                agent_positions[who] = nxt

    agent_positions["neo"] = loc
    co = str(state.get("co_human_id") or "").strip().lower()
    if co and co in matrix_cast.CAST_HOME:
        agent_positions[co] = loc

    tick_no = int(state.get("world_tick") or 0) + 1
    threat = int(state.get("threat_level") or 0)
    trace = float(patches.get("trace_level", state.get("trace_level") or 0))
    if trace >= 70:
        threat = min(10, threat + 1)

    story.beat(f"World tick #{tick_no} — trace={trace:.1f} threat={threat}")
    for m in moves[:8]:
        story.beat(m)

    events.append(f"tick:{tick_no}")
    logs.append(f"[tick] #{tick_no} moves={len(moves)} cast={len(agent_positions)}")
    patches.update(
        {
            "world_tick": tick_no,
            "agent_positions": agent_positions,
            "threat_level": threat,
            "events": events,
            "log": logs,
        }
    )
    return patches
