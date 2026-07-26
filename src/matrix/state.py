import operator
from typing import Annotated

from typing_extensions import TypedDict


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

    # Rule-bending
    spoon_exists: bool
    reality_rewritten: bool

    # Pursuit loop
    pursuit_round: int
    pursuit_status: str  # idle | chasing | escaped | caught
    pursuit_log: Annotated[list[str], operator.add]

    # HITL
    pending_decision: str  # oracle_question | pill | fight_or_flee | ""
    pill_choice: str
    fight_choice: str  # fight | flee | ""
    awakened: bool

    # Construct training subgraph
    training_skills: list[str]
    training_score: int

    # Narrative
    dialogue: Annotated[list[str], operator.add]
    events: Annotated[list[str], operator.add]
    log: Annotated[list[str], operator.add]
    outcome: str
    previous_lives: int
    locations_visited: Annotated[list[str], operator.add]
