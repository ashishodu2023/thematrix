import operator
from typing import Annotated, Any

from typing_extensions import TypedDict


def unique_extend(left: list[str] | None, right: list[str] | None) -> list[str]:
    """Reducer: append new locations without duplicating."""
    out = list(left or [])
    for item in right or []:
        if item not in out:
            out.append(item)
    return out


def merge_scoreboard(
    left: dict[str, Any] | None, right: dict[str, Any] | None
) -> dict[str, int]:
    """Reducer: accumulate faction points across parallel / sequential nodes."""
    out = {"zion": 0, "agents": 0, "system": 0}
    for src in (left, right):
        if not isinstance(src, dict):
            continue
        for k, v in src.items():
            key = str(k).lower()
            if key not in out:
                out[key] = 0
            try:
                out[key] += int(v)
            except (TypeError, ValueError):
                continue
    return out


def last_value(left: Any, right: Any) -> Any:
    """Reducer: last writer wins (safe under accidental parallel updates)."""
    return right if right is not None else left


def or_bool(left: bool | None, right: bool | None) -> bool:
    """Reducer: True if any parallel branch says True."""
    return bool(left) or bool(right)


class MatrixState(TypedDict):
    """
    Shared simulation kernel — the Matrix itself.

    Annotated[..., operator.add] fields are reducers: parallel Agent
    workers APPEND instead of overwriting.
    """

    # Human jacked in
    human_id: str
    co_human_id: str  # optional second Operator / Trinity seat

    # Simulation kernel / world
    city: str
    cycle: int
    location: str
    scene: str
    physics_rules: list[str]
    anomaly: str  # spoon | glitch | none
    threat_level: int
    world_tick: int
    trace_level: float
    hardline_cooldown: int
    phone_taps: Annotated[list[str], operator.add]
    sector_heat: dict
    agent_positions: dict
    sticky_flags: dict
    meta_policy: str
    faction_scoreboard: Annotated[dict, merge_scoreboard]

    # Architect / Oracle
    architect_plan: str
    oracle_question: str
    oracle_prophecy: str

    # Swarm of Agents (Send API + reducers)
    agent_names: list[str]
    current_agent: str
    agent_reports: Annotated[list[str], operator.add]
    sectors_scanned: Annotated[list[str], operator.add]

    # Multi-agent awareness — every brain learns about others & acts alone
    agent_memory: Annotated[list[str], operator.add]
    character_actions: Annotated[list[str], operator.add]
    dialogue: Annotated[list[str], operator.add]

    # Rule-bending (reducers — parallel fan-in must not crash the cycle)
    spoon_exists: Annotated[bool, last_value]
    reality_rewritten: Annotated[bool, last_value]

    # Pursuit loop
    pursuit_round: int
    pursuit_status: str  # idle | chasing | escaped | caught
    pursuit_log: Annotated[list[str], operator.add]

    # HITL
    pending_decision: str
    pill_choice: str
    trust_choice: str  # trust | walk | ""
    bug_choice: str  # extract | refuse | ""
    steak_choice: str  # steak | refuse | ""
    jump_choice: str  # jump | hesitate | ""
    fight_choice: str  # fight | flee | ""
    radio_choice: str  # call | silent | ""
    code_choice: str  # accept | deny | ""
    key_choice: str  # take_key | refuse_key | ""
    awakened: bool
    bug_implanted: bool
    sentinel_alert: bool

    # Construct / combat
    training_skills: list[str]
    training_score: int
    showdown_round: int
    showdown_status: str  # "" | won | escaped
    dream_note: str
    briefing: str

    # Parallel subplot labels (neo story + agent field, etc.)
    active_tracks: Annotated[list[str], operator.add]
    events: Annotated[list[str], operator.add]
    log: Annotated[list[str], operator.add]
    outcome: str
    previous_lives: int
    locations_visited: Annotated[list[str], unique_extend]
    wander_hops: int
    tool_results: Annotated[list[str], operator.add]
