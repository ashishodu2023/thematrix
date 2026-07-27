"""Cast placement on the Mega City graph (Neo, crew, Agents, programs)."""

from __future__ import annotations

# Default spawn points when a life boots
CAST_HOME: dict[str, str] = {
    "neo": "jack_point",
    "trinity": "club",
    "morpheus": "nebuchadnezzar",
    "tank": "nebuchadnezzar",
    "cypher": "nebuchadnezzar",
    "oracle": "oracle_apartment",
    "spoon_boy": "oracle_apartment",
    "architect": "construct",
    "smith": "subway",
    "jones": "hotel_lobby",
    "brown": "highway",
    "operator": "nebuchadnezzar",
    "merovingian": "club_vip",
    "keymaker": "keymaker_hall",
    "sentinel": "real_world",
    "niobe": "zion_dock",
    "persephone": "club_vip",
    "seraph": "oracle_apartment",
}

AGENTS = frozenset({"smith", "jones", "brown"})
CREW = frozenset({"trinity", "morpheus", "tank", "cypher", "operator", "niobe"})
PROGRAMS = frozenset(
    {"oracle", "spoon_boy", "architect", "merovingian", "keymaker", "persephone", "seraph"}
)
MACHINES = frozenset({"sentinel"})

# Faction colors for the Operator Console
CAST_STYLE: dict[str, dict[str, str]] = {
    "neo": {"faction": "zion", "color": "#39FF14", "short": "N", "label": "Neo"},
    "trinity": {"faction": "zion", "color": "#7CFF7C", "short": "T", "label": "Trinity"},
    "morpheus": {"faction": "zion", "color": "#66BB6A", "short": "M", "label": "Morpheus"},
    "tank": {"faction": "zion", "color": "#43A047", "short": "Tk", "label": "Tank"},
    "cypher": {"faction": "zion", "color": "#A5D6A7", "short": "C", "label": "Cypher"},
    "operator": {"faction": "zion", "color": "#81C784", "short": "Op", "label": "Operator"},
    "niobe": {"faction": "zion", "color": "#C5E1A5", "short": "Nb", "label": "Niobe"},
    "smith": {"faction": "agents", "color": "#FF3B4E", "short": "S", "label": "Smith"},
    "jones": {"faction": "agents", "color": "#FF6B7A", "short": "J", "label": "Jones"},
    "brown": {"faction": "agents", "color": "#FF8A95", "short": "B", "label": "Brown"},
    "oracle": {"faction": "system", "color": "#FFD54F", "short": "O", "label": "Oracle"},
    "spoon_boy": {"faction": "system", "color": "#FFE082", "short": "Sb", "label": "Spoon Boy"},
    "architect": {"faction": "system", "color": "#80DEEA", "short": "A", "label": "Architect"},
    "merovingian": {"faction": "system", "color": "#CE93D8", "short": "Mv", "label": "Merovingian"},
    "keymaker": {"faction": "system", "color": "#B39DDB", "short": "K", "label": "Keymaker"},
    "persephone": {"faction": "system", "color": "#F48FB1", "short": "P", "label": "Persephone"},
    "seraph": {"faction": "system", "color": "#FFF59D", "short": "Sr", "label": "Seraph"},
    "sentinel": {"faction": "machines", "color": "#FF7043", "short": "Sq", "label": "Sentinel"},
}

# Soft scene hints — pull relevant cast toward the active node
SCENE_PULL: dict[str, tuple[str, ...]] = {
    "jack_in": ("neo", "trinity"),
    "interrogation": ("neo", "smith", "jones"),
    "club": ("neo", "trinity", "cypher"),
    "merovingian": ("neo", "trinity", "merovingian", "persephone"),
    "keymaker": ("neo", "keymaker", "seraph"),
    "highway": ("neo", "trinity", "smith", "brown", "niobe"),
    "oracle": ("neo", "oracle", "spoon_boy", "trinity", "seraph"),
    "construct": ("neo", "morpheus", "tank"),
    "pursuit": ("neo", "smith", "jones", "brown", "trinity"),
    "lobby": ("neo", "trinity", "smith"),
    "subway": ("neo", "smith", "morpheus"),
    "ship": ("neo", "morpheus", "tank", "cypher", "trinity", "niobe"),
    "pill": ("neo", "morpheus", "trinity"),
    "showdown": ("neo", "smith", "trinity"),
    "zion": ("neo", "morpheus", "tank", "niobe"),
}


def seed_positions() -> dict[str, str]:
    return dict(CAST_HOME)


def ensure_cast(state: dict) -> dict[str, str]:
    """Fill missing cast seats and pin Neo (+ co-pilot) to current location."""
    positions = dict(state.get("agent_positions") or {})
    for name, home in CAST_HOME.items():
        positions.setdefault(name, home)

    loc = str(state.get("location") or positions.get("neo") or "jack_point")
    positions["neo"] = loc

    co = str(state.get("co_human_id") or "").strip().lower()
    if co and co in CAST_HOME:
        # Co-pilot rides with Neo when jacked in
        positions[co] = loc

    scene = str(state.get("scene") or "").lower()
    for key, names in SCENE_PULL.items():
        if key in scene:
            for who in names:
                if who == "neo":
                    continue
                if who in AGENTS:
                    continue  # Agents pathfind via world_tick
                # Pull allies/programs one hop toward Neo's sector if far
                if who in ("oracle", "spoon_boy") and "oracle" in scene:
                    positions[who] = "oracle_apartment"
                elif who in ("morpheus", "tank", "cypher") and any(
                    s in scene for s in ("ship", "construct", "pill")
                ):
                    if "construct" in scene:
                        positions[who] = "construct" if who != "tank" else "nebuchadnezzar"
                    elif "ship" in scene or "pill" in scene:
                        positions[who] = "nebuchadnezzar" if who != "neo" else loc
                elif who == "trinity":
                    positions[who] = loc
            break

    return positions
