"""Open-world / branch routing + live branch map for the Operator Console."""

from __future__ import annotations

import os
from typing import Any

# Static story DAG for Act II open-world (console visualization)
BRANCH_GRAPH: dict[str, dict[str, Any]] = {
    "cafe_scene": {
        "label": "Cafe",
        "next": ["merovingian_vip", "city_wander", "club_hel_fight"],
        "act": "II",
        "fork": True,
    },
    "merovingian_vip": {
        "label": "Merovingian",
        "next": ["club_hel_fight", "keymaker_doors"],
        "act": "II",
        "fork": True,
    },
    "club_hel_fight": {
        "label": "Club Hel",
        "next": ["keymaker_doors"],
        "act": "II",
    },
    "keymaker_doors": {
        "label": "Keymaker",
        "next": ["highway_chase", "city_wander", "prepare_swarm"],
        "act": "II",
        "fork": True,
    },
    "city_wander": {
        "label": "Wander",
        "next": [
            "highway_chase",
            "prepare_swarm",
            "merovingian_vip",
            "city_wander",
            "club_hel_fight",
        ],
        "act": "II",
        "fork": True,
    },
    "highway_chase": {
        "label": "Highway",
        "next": ["prepare_swarm"],
        "act": "II",
    },
    "prepare_swarm": {
        "label": "Agent Swarm",
        "next": ["reconcile"],
        "act": "II",
    },
    "reconcile": {
        "label": "Reconcile",
        "next": ["bend_reality", "enforce_reality"],
        "act": "II",
        "fork": True,
    },
    "bend_reality": {
        "label": "Bend",
        "next": ["lobby_breach"],
        "act": "II",
    },
    "enforce_reality": {
        "label": "Enforce",
        "next": ["lobby_breach"],
        "act": "II",
    },
    "lobby_breach": {
        "label": "Lobby",
        "next": ["burly_brawl", "pursuit_loop"],
        "act": "II",
        "fork": True,
    },
    "burly_brawl": {
        "label": "Burly Brawl",
        "next": ["pursuit_loop"],
        "act": "II",
    },
    "pursuit_loop": {
        "label": "Pursuit",
        "next": ["morpheus_offer"],
        "act": "II",
    },
    "morpheus_offer": {
        "label": "Pills",
        "next": ["pill_choice"],
        "act": "II",
        "fork": True,
    },
}


def open_city_enabled() -> bool:
    return os.getenv("MATRIX_OPEN_CITY", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _director_force(*, commit: bool = True) -> str:
    try:
        from matrix.director import consume_force_branch, peek_force_branch

        target = peek_force_branch()
        if target and commit:
            consume_force_branch()
        return target
    except Exception:  # noqa: BLE001
        return ""


def route_after_cafe(state: dict, *, commit: bool = True) -> str:
    forced = _director_force(commit=commit)
    if forced in {"merovingian_vip", "city_wander", "club_hel_fight"}:
        return forced
    if not open_city_enabled():
        return "merovingian_vip"
    sticky = state.get("sticky_flags") or {}
    loc = str(state.get("location") or "")
    if sticky.get("persephone_kiss") or loc == "club_vip":
        return "club_hel_fight"
    if int(state.get("wander_hops") or 0) == 0 and (state.get("previous_lives") or 0) % 2 == 1:
        return "city_wander"
    return "merovingian_vip"


def route_after_merovingian(state: dict, *, commit: bool = True) -> str:
    forced = _director_force(commit=commit)
    if forced in {"club_hel_fight", "keymaker_doors"}:
        return forced
    sticky = state.get("sticky_flags") or {}
    if sticky.get("defy_merovingian") or sticky.get("persephone_kiss"):
        return "club_hel_fight"
    if open_city_enabled() and int(state.get("world_tick") or 0) % 3 == 0:
        return "club_hel_fight"
    return "keymaker_doors"


def route_after_keymaker(state: dict, *, commit: bool = True) -> str:
    """
    After Keymaker: free-roam branch.
    - took_key → highway (chase door)
    - refused_key → city wander
    - operator parked Neo elsewhere → follow location
    """
    forced = _director_force(commit=commit)
    if forced in {"highway_chase", "city_wander", "prepare_swarm"}:
        return forced
    sticky = state.get("sticky_flags") or {}
    loc = str(state.get("location") or "")
    key = str(state.get("key_choice") or "")

    if loc in {"highway", "rooftop", "subway"}:
        return "highway_chase"
    if loc in {"hotel_lobby", "lobby"}:
        return "prepare_swarm"
    if loc in {"oracle_apartment", "cafe", "club", "apartment"}:
        return "city_wander"
    if sticky.get("took_key") or key == "take_key":
        return "highway_chase"
    if sticky.get("refused_key") or key == "refuse_key":
        return "city_wander"
    return "highway_chase"


def route_after_wander(state: dict, *, commit: bool = True) -> str:
    forced = _director_force(commit=commit)
    if forced in {
        "highway_chase",
        "prepare_swarm",
        "merovingian_vip",
        "city_wander",
        "club_hel_fight",
    }:
        return forced
    loc = str(state.get("location") or "")
    hops = int(state.get("wander_hops") or 0)
    if open_city_enabled() and hops < 2 and loc not in {"highway", "hotel_lobby"}:
        if float(state.get("trace_level") or 0) < 55:
            return "city_wander"
    if loc == "highway":
        return "highway_chase"
    if loc in {"hotel_lobby"}:
        return "prepare_swarm"
    if loc in {"club_vip", "club"}:
        return "club_hel_fight" if open_city_enabled() else "merovingian_vip"
    return "prepare_swarm"


def route_after_lobby(state: dict, *, commit: bool = True) -> str:
    forced = _director_force(commit=commit)
    if forced in {"burly_brawl", "pursuit_loop"}:
        return forced
    sticky = state.get("sticky_flags") or {}
    if sticky.get("burly_brawl"):
        return "pursuit_loop"
    try:
        from matrix.season import status as season_status

        arc = season_status().get("arc") or "none"
        if arc == "smith_infection":
            return "burly_brawl"
    except Exception:  # noqa: BLE001
        pass
    if open_city_enabled() and int(state.get("threat_level") or 0) >= 6:
        return "burly_brawl"
    if (state.get("anomaly") or "") == "spoon" and int(state.get("previous_lives") or 0) > 0:
        return "burly_brawl"
    return "pursuit_loop"


def _scene_to_node(scene: str, status: str = "") -> str:
    s = (scene or status or "").lower().replace(" ", "_")
    aliases = {
        "cafe": "cafe_scene",
        "merovingian": "merovingian_vip",
        "club_hel": "club_hel_fight",
        "keymaker": "keymaker_doors",
        "wander": "city_wander",
        "highway": "highway_chase",
        "lobby": "lobby_breach",
        "burly": "burly_brawl",
        "pursuit": "pursuit_loop",
        "pill": "morpheus_offer",
        "swarm": "prepare_swarm",
        "bend": "bend_reality",
        "enforce": "enforce_reality",
    }
    if s in BRANCH_GRAPH:
        return s
    for key, node in aliases.items():
        if key in s:
            return node
    return s


def predict_next(state: dict, node: str) -> str | None:
    """Best-effort predicted next branch from current state."""
    if node == "cafe_scene":
        return route_after_cafe(state, commit=False)
    if node == "merovingian_vip":
        return route_after_merovingian(state, commit=False)
    if node == "keymaker_doors":
        return route_after_keymaker(state, commit=False)
    if node == "city_wander":
        return route_after_wander(state, commit=False)
    if node == "lobby_breach":
        return route_after_lobby(state, commit=False)
    if node == "reconcile":
        rules = set(state.get("physics_rules") or [])
        if state.get("reality_rewritten") or "belief_over_rules" in rules:
            return "bend_reality"
        if state.get("anomaly") == "spoon":
            return "bend_reality"
        return "enforce_reality"
    info = BRANCH_GRAPH.get(node) or {}
    nxt = info.get("next") or []
    return nxt[0] if len(nxt) == 1 else None


def branch_snapshot(state: dict) -> dict[str, Any]:
    """Live branch tree payload for the Operator Console."""
    scene = str(state.get("scene") or "")
    status = str(state.get("status") or "")
    current = _scene_to_node(scene, status)
    history = list(state.get("branch_path") or [])
    if current and (not history or history[-1] != current):
        pass

    events = list(state.get("events") or [])
    path: list[str] = []
    for ev in events:
        e = str(ev).lower()
        for node in BRANCH_GRAPH:
            label = BRANCH_GRAPH[node]["label"].lower()
            if node.replace("_", "") in e.replace("_", "") or label in e:
                if not path or path[-1] != node:
                    path.append(node)
        if "wander:" in e and (not path or path[-1] != "city_wander"):
            path.append("city_wander")
        if "act2:keymaker" in e and (not path or path[-1] != "keymaker_doors"):
            path.append("keymaker_doors")
        if "act2:merovingian" in e and (not path or path[-1] != "merovingian_vip"):
            path.append("merovingian_vip")
        if "act2:club_hel" in e and (not path or path[-1] != "club_hel_fight"):
            path.append("club_hel_fight")
        if "act2:burly" in e and (not path or path[-1] != "burly_brawl"):
            path.append("burly_brawl")
        if "act2:highway" in e and (not path or path[-1] != "highway_chase"):
            path.append("highway_chase")
        if "lobby:breach" in e and (not path or path[-1] != "lobby_breach"):
            path.append("lobby_breach")

    if current in BRANCH_GRAPH and (not path or path[-1] != current):
        path.append(current)

    options = list((BRANCH_GRAPH.get(current) or {}).get("next") or [])
    predicted = predict_next(state, current) if current in BRANCH_GRAPH else None

    why = ""
    if current == "keymaker_doors":
        key = state.get("key_choice") or ""
        sticky = state.get("sticky_flags") or {}
        if sticky.get("took_key") or key == "take_key":
            why = "took the key → highway"
        elif sticky.get("refused_key") or key == "refuse_key":
            why = "refused key → wander"
        else:
            why = f"loc={state.get('location')} · default highway"
    elif current == "city_wander":
        why = f"open city @ {state.get('location')} hops={state.get('wander_hops', 0)} → {predicted}"
    elif current == "reconcile":
        why = f"physics → {predicted}"
    elif current == "cafe_scene":
        why = f"open-city cafe fork → {predicted}"
    elif current == "merovingian_vip":
        why = f"court fork → {predicted}"
    elif current == "lobby_breach":
        why = f"lobby fork → {predicted}"

    nodes = []
    for nid, meta in BRANCH_GRAPH.items():
        nodes.append(
            {
                "id": nid,
                "label": meta["label"],
                "fork": bool(meta.get("fork")),
                "next": list(meta.get("next") or []),
                "state": (
                    "current"
                    if nid == current
                    else "taken"
                    if nid in path
                    else "ahead"
                    if predicted == nid or nid in options
                    else "idle"
                ),
            }
        )

    edges = []
    for nid, meta in BRANCH_GRAPH.items():
        for dst in meta.get("next") or []:
            kind = "idle"
            if nid in path and dst in path:
                try:
                    i = path.index(nid)
                    if i + 1 < len(path) and path[i + 1] == dst:
                        kind = "taken"
                    elif dst in path and nid in path:
                        kind = "taken"
                except ValueError:
                    kind = "taken"
            if nid == current and dst == predicted:
                kind = "predicted"
            elif nid == current and dst in options:
                kind = "option"
            edges.append({"from": nid, "to": dst, "kind": kind})

    return {
        "current": current,
        "predicted": predicted,
        "options": options,
        "path": path[-12:],
        "why": why,
        "key_choice": state.get("key_choice") or "",
        "location": state.get("location") or "",
        "nodes": nodes,
        "edges": edges,
        "fork_active": bool((BRANCH_GRAPH.get(current) or {}).get("fork")),
        "open_city": open_city_enabled(),
    }
