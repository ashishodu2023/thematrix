"""Aggregate Operator metrics across lives / replays."""

from __future__ import annotations

from typing import Any

from matrix.replay import list_replays, load_replay
from matrix.services.memory import SessionMemory


def collect_metrics(human_id: str = "neo") -> dict[str, Any]:
    session = SessionMemory.load(human_id)
    lives = list(session.lives or [])
    red = sum(1 for life in lives if getattr(life, "pill_choice", "") == "red")
    blue = sum(1 for life in lives if getattr(life, "pill_choice", "") == "blue")
    awakened = int(getattr(session, "awakened_count", 0) or 0)

    replays = list_replays(limit=50)
    zion = agents = 0
    for item in replays:
        data = load_replay(str(item["id"])) or {}
        board = data.get("faction_scoreboard") or {}
        zion += int(board.get("zion") or 0)
        agents += int(board.get("agents") or 0)

    return {
        "human_id": human_id,
        "lives_recorded": len(lives),
        "awakened_count": awakened,
        "red_pills": red,
        "blue_pills": blue,
        "agent_knowledge_facts": len(getattr(session, "agent_knowledge", None) or []),
        "sticky_flags": dict(getattr(session, "sticky_flags", None) or {}),
        "replays_saved": len(replays),
        "faction_points": {"zion": zion, "agents": agents},
        "win_hint": (
            "Zion ahead" if zion > agents else "Agents ahead" if agents > zion else "Tied"
        ),
        "recent_replays": replays[:8],
    }
