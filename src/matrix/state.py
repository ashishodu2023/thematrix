import operator
from typing import Annotated

from typing_extensions import TypedDict


def unique_extend(left: list[str] | None, right: list[str] | None) -> list[str]:
    """Reducer: append new locations without duplicating."""
    out = list(left or [])
    for item in right or []:
        if item not in out:
            out.append(item)
    return out


class MatrixState(TypedDict):
    """
    Shared simulation kernel — the Matrix itself.

    Annotated[..., operator.add] fields are reducers: parallel Agent
    workers APPEND instead of overwriting.
    """

    # Human jacked in
    human_id: str

    # Simulation kernel / world
    city: str
    cycle: int
    location: str
    scene: str
    physics_rules: list[str]
    anomaly: str  # spoon | glitch | none
    threat_level: int

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

    # Rule-bending
    spoon_exists: bool
    reality_rewritten: bool

    # Pursuit loop
    pursuit_round: int
    pursuit_status: str  # idle | chasing | escaped | caught
    pursuit_log: Annotated[list[str], operator.add]

    # HITL
    pending_decision: str
    # bug | trust | oracle_question | pill | steak | jump | fight_or_flee | radio | code | ""
    pill_choice: str
    trust_choice: str  # trust | walk | ""
    bug_choice: str  # extract | refuse | ""
    steak_choice: str  # steak | refuse | ""
    jump_choice: str  # jump | hesitate | ""
    fight_choice: str  # fight | flee | ""
    radio_choice: str  # call | silent | ""
    code_choice: str  # accept | deny | ""
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

    # Narrative
    dialogue: Annotated[list[str], operator.add]
    events: Annotated[list[str], operator.add]
    log: Annotated[list[str], operator.add]
    outcome: str
    previous_lives: int
    locations_visited: Annotated[list[str], unique_extend]
