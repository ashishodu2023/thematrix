from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class PreviousLife(BaseModel):
    """One completed jack-in cycle — Operator-side history."""

    cycle: int
    city: str
    pill_choice: str
    outcome: str
    reality_rewritten: bool = False
    training_score: int = 0
    fight_choice: str = ""
    locations_visited: list[str] = Field(default_factory=list)


class MatrixSession(BaseModel):
    """Long-term memory of a human across Matrix cycles (Redis)."""

    human_id: str
    lives: list[PreviousLife] = Field(default_factory=list)
    awakened_count: int = 0
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class SceneEvent(BaseModel):
    """A timeline event appended via reducers."""

    scene: str
    location: str
    summary: str


class AgentReport(BaseModel):
    agent: str
    sector: str
    scan: str
    anomaly: str
    voice: str = ""


PursuitStatus = Literal["idle", "chasing", "escaped", "caught"]
PendingDecision = Literal[
    "",
    "oracle_question",
    "pill",
    "fight_or_flee",
]
