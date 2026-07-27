"""Mega City causal graph — locations + pathfinding for Agents / Neo."""

from __future__ import annotations

from collections import deque

from matrix.world import LOCATIONS

# Undirected travel edges (hardlines, streets, tunnels)
CITY_EDGES: dict[str, tuple[str, ...]] = {
    "jack_point": ("apartment", "subway", "hotel_lobby"),
    "apartment": ("jack_point", "club", "oracle_apartment"),
    "club": ("apartment", "cafe", "hotel_lobby", "club_vip"),
    "club_vip": ("club", "keymaker_hall"),
    "keymaker_hall": ("club_vip", "hotel_lobby"),
    "oracle_apartment": ("apartment", "cafe"),
    "cafe": ("club", "oracle_apartment", "subway"),
    "hotel_lobby": ("jack_point", "club", "rooftop", "subway", "keymaker_hall"),
    "subway": ("jack_point", "cafe", "hotel_lobby", "highway"),
    "rooftop": ("hotel_lobby", "highway"),
    "highway": ("subway", "rooftop"),
    "construct": ("nebuchadnezzar",),
    "nebuchadnezzar": ("construct", "real_world", "zion_dock"),
    "zion_dock": ("nebuchadnezzar",),
    "real_world": ("nebuchadnezzar",),
}


def neighbors(location_id: str) -> list[str]:
    return list(CITY_EDGES.get(location_id, ()))


def shortest_path(start: str, goal: str) -> list[str]:
    """BFS path inclusive of start and goal. Empty if unreachable."""
    if start == goal:
        return [start]
    if start not in CITY_EDGES or goal not in CITY_EDGES:
        return []
    q: deque[str] = deque([start])
    prev: dict[str, str | None] = {start: None}
    while q:
        cur = q.popleft()
        for nxt in CITY_EDGES.get(cur, ()):
            if nxt in prev:
                continue
            prev[nxt] = cur
            if nxt == goal:
                path = [goal]
                while path[-1] != start:
                    parent = prev[path[-1]]
                    if parent is None:
                        break
                    path.append(parent)
                path.reverse()
                return path
            q.append(nxt)
    return []


def step_toward(current: str, target: str) -> str:
    """One hop along shortest path toward target (or stay)."""
    path = shortest_path(current, target)
    if len(path) >= 2:
        return path[1]
    opts = neighbors(current)
    return opts[0] if opts else current


def location_name(loc_id: str) -> str:
    loc = LOCATIONS.get(loc_id)
    return loc.name if loc else loc_id
