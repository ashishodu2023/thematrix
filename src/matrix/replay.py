"""Replay theater — save finished lives and scrub them in the console."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_DIR = _PROJECT_ROOT / ".matrix_replays"


def _dir() -> Path:
    _REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    return _REPLAY_DIR


def save_life(result: dict[str, Any], *, feed: list[str] | None = None) -> Path:
    """Persist one finished life for later replay."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    cycle = result.get("cycle") or 0
    path = _dir() / f"life-{cycle}-{stamp}.json"
    payload = {
        "saved_at": time.time(),
        "cycle": cycle,
        "outcome": result.get("outcome"),
        "awakened": result.get("awakened"),
        "pill": result.get("pill_choice"),
        "location": result.get("location"),
        "scene": result.get("scene"),
        "threat": result.get("threat_level"),
        "trace": result.get("trace_level"),
        "meta": result.get("meta_policy"),
        "training_score": result.get("training_score"),
        "faction_scoreboard": result.get("faction_scoreboard") or {},
        "agent_positions": result.get("agent_positions") or {},
        "sector_heat": result.get("sector_heat") or {},
        "physics": result.get("physics_rules") or [],
        "dialogue": list(result.get("dialogue") or [])[-80:],
        "feed": list(feed or result.get("dialogue") or [])[-80:],
        "events": list(result.get("events") or [])[-40:],
        "locations_visited": list(result.get("locations_visited") or []),
        "human_id": result.get("human_id") or "neo",
        "co_human_id": result.get("co_human_id") or "",
        "frames": _build_frames(result, feed),
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def _build_frames(result: dict[str, Any], feed: list[str] | None) -> list[dict]:
    """Scrub timeline: advance location along visited path as lines play."""
    lines = list(feed or result.get("dialogue") or [])[-40:]
    visited = list(result.get("locations_visited") or [])
    if not visited:
        visited = [result.get("location") or "jack_point"]
    final_pos = dict(result.get("agent_positions") or {})
    heat = dict(result.get("sector_heat") or {})
    frames = []
    n = max(1, len(lines))
    for i, line in enumerate(lines or [result.get("outcome") or "empty life"]):
        # Progress through visited sectors as the scrub advances
        vi = min(len(visited) - 1, int(i * len(visited) / n))
        loc = visited[vi]
        positions = dict(final_pos)
        positions["neo"] = loc
        # Approximate Agent pressure near Neo mid-life
        if i > n // 2:
            for agent in ("smith", "jones", "brown"):
                if agent in positions and i > (n * 2) // 3:
                    positions[agent] = loc
        frames.append(
            {
                "i": i,
                "line": line,
                "location": loc,
                "positions": positions,
                "threat": result.get("threat_level"),
                "trace": float(result.get("trace_level") or 0) * (i + 1) / n,
                "sector_heat": heat,
                "meta": result.get("meta_policy"),
                "faction_scoreboard": result.get("faction_scoreboard") or {},
            }
        )
    return frames


def list_replays(limit: int = 30) -> list[dict[str, Any]]:
    files = sorted(_dir().glob("life-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for path in files[:limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        out.append(
            {
                "id": path.name,
                "cycle": data.get("cycle"),
                "outcome": data.get("outcome"),
                "awakened": data.get("awakened"),
                "saved_at": data.get("saved_at"),
                "frames": len(data.get("frames") or []),
            }
        )
    return out


def load_replay(replay_id: str) -> dict[str, Any] | None:
    path = _dir() / replay_id
    if not path.exists() or ".." in replay_id:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
