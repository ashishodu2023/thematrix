"""Aggregate Operator metrics across lives / replays — outcome analytics."""

from __future__ import annotations

from collections import Counter
from typing import Any

from matrix.replay import list_replays, load_replay
from matrix.services.memory import SessionMemory


def _bucket_outcome(outcome: str) -> str:
    o = (outcome or "unknown").strip().lower()
    if not o:
        return "unknown"
    if "blue" in o:
        return "blue_pill"
    if "red" in o or "awaken" in o:
        return "awakened"
    if "catch" in o or "captured" in o or "smith" in o:
        return "agent_catch"
    if "zion" in o:
        return "zion"
    if "flee" in o or "escape" in o:
        return "escape"
    if "die" in o or "dead" in o or "kill" in o:
        return "death"
    return o[:40]


def collect_metrics(human_id: str = "neo") -> dict[str, Any]:
    session = SessionMemory.load(human_id)
    lives = list(session.lives or [])
    red = sum(1 for life in lives if getattr(life, "pill_choice", "") == "red")
    blue = sum(1 for life in lives if getattr(life, "pill_choice", "") == "blue")
    awakened = int(getattr(session, "awakened_count", 0) or 0)

    outcome_counts: Counter[str] = Counter()
    for life in lives:
        outcome_counts[_bucket_outcome(str(getattr(life, "outcome", "") or ""))] += 1

    replays = list_replays(limit=80)
    zion = agents = 0
    branch_freq: Counter[str] = Counter()
    catch_hits = 0
    catch_total = 0
    ending_buckets: Counter[str] = Counter()

    for item in replays:
        data = load_replay(str(item["id"])) or {}
        board = data.get("faction_scoreboard") or {}
        zion += int(board.get("zion") or 0)
        agents += int(board.get("agents") or 0)
        ending_buckets[_bucket_outcome(str(data.get("outcome") or ""))] += 1
        events = list(data.get("events") or [])
        for ev in events:
            e = str(ev).lower()
            if "wander:" in e:
                branch_freq["wander"] += 1
            if "act2:highway" in e or "highway" in e:
                branch_freq["highway"] += 1
            if "act2:club_hel" in e:
                branch_freq["club_hel"] += 1
            if "act2:burly" in e:
                branch_freq["burly_brawl"] += 1
            if "act2:keymaker" in e:
                branch_freq["keymaker"] += 1
            if "architect:" in e:
                branch_freq[e.split(":")[0] + ":" + e.split(":")[-1]] += 1
        # chase catch heuristic
        sticky = data.get("sticky_flags") or {}
        if "pursuit" in str(data.get("events") or []).lower() or data.get("fight_choice"):
            catch_total += 1
            if sticky.get("caught") or "catch" in str(data.get("outcome") or "").lower():
                catch_hits += 1

    catch_rate = (catch_hits / catch_total) if catch_total else None

    season = {}
    try:
        from matrix.season import status as season_status

        season = season_status()
    except Exception:  # noqa: BLE001
        season = {}

    timeline_n = 0
    try:
        from matrix.timeline import list_timeline

        timeline_n = len(list_timeline(200))
    except Exception:  # noqa: BLE001
        pass

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
        "analytics": {
            "ending_buckets": dict(ending_buckets),
            "life_outcomes": dict(outcome_counts),
            "branch_frequencies": dict(branch_freq.most_common(20)),
            "chase_catch_rate": catch_rate,
            "chase_samples": catch_total,
            "timeline_events": timeline_n,
            "season": season,
        },
    }
