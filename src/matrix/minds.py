"""Persistent per-character minds in Redis — with in-memory fallback for tests."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

_DEFAULT_GOALS: dict[str, tuple[str, str]] = {
    "smith": ("Eliminate the anomaly", "agents"),
    "jones": ("Contain residual anomalies", "agents"),
    "brown": ("Secure sectors", "agents"),
    "neo": ("Discover what is real", "zion"),
    "trinity": ("Extract and protect Neo", "zion"),
    "morpheus": ("Free minds; find The One", "zion"),
    "oracle": ("Guide choice without forcing it", "system"),
    "architect": ("Preserve systemic balance", "system"),
    "tank": ("Keep hardlines open", "zion"),
    "cypher": ("Return to comfortable illusion", "self"),
    "operator": ("Keep the crew alive", "zion"),
    "spoon_boy": ("Teach belief over form", "system"),
    "niobe": ("Defend Zion ships", "zion"),
    "persephone": ("Find sincerity in a false world", "system"),
    "seraph": ("Protect the Oracle", "system"),
    "merovingian": ("Enforce causality", "system"),
    "keymaker": ("Open the correct door", "system"),
    "sentinel": ("Destroy hovercraft signatures", "machines"),
}

_MEMORY: dict[str, "AgentMind"] = {}


class AgentMind(BaseModel):
    character: str
    goal: str = ""
    grudge: str = ""
    last_known_neo_location: str = ""
    allegiance: str = ""
    facts: list[str] = Field(default_factory=list)
    score: int = 0
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


def _blank(name: str) -> AgentMind:
    goal, allegiance = _DEFAULT_GOALS.get(name, ("Survive the cycle", "self"))
    return AgentMind(character=name, goal=goal, allegiance=allegiance)


class MindStore:
    PREFIX = "matrix:mind"

    @classmethod
    def key(cls, character: str) -> str:
        return f"{cls.PREFIX}:{character.strip().lower()}"

    @classmethod
    def load(cls, character: str) -> AgentMind:
        name = character.strip().lower()
        try:
            from matrix.services.redis_client import redis_client

            raw = redis_client.get(cls.key(name))
            if raw:
                return AgentMind.model_validate_json(raw)
        except Exception:  # noqa: BLE001
            if name in _MEMORY:
                return _MEMORY[name]
        return _MEMORY.get(name) or _blank(name)

    @classmethod
    def save(cls, mind: AgentMind) -> None:
        mind.updated_at = datetime.now(timezone.utc)
        _MEMORY[mind.character] = mind
        try:
            from matrix.services.redis_client import redis_client

            redis_client.set(cls.key(mind.character), mind.model_dump_json())
        except Exception:  # noqa: BLE001
            pass

    @classmethod
    def remember(cls, character: str, fact: str, *, neo_location: str = "") -> AgentMind:
        mind = cls.load(character)
        text = (fact or "").strip()
        if text and text not in mind.facts:
            mind.facts.append(text)
        mind.facts = mind.facts[-40:]
        if neo_location:
            mind.last_known_neo_location = neo_location
        if "grudge" in text.lower() or "escaped" in text.lower():
            mind.grudge = text[:160]
        cls.save(mind)
        return mind

    @classmethod
    def add_score(cls, character: str, delta: int, note: str = "") -> AgentMind:
        mind = cls.load(character)
        mind.score += delta
        if note:
            mind.facts.append(f"score{delta:+d}: {note}")
            mind.facts = mind.facts[-40:]
        cls.save(mind)
        return mind

    @classmethod
    def dossier(cls, character: str) -> str:
        mind = cls.load(character)
        lines = [
            f"goal={mind.goal}",
            f"allegiance={mind.allegiance}",
            f"score={mind.score}",
        ]
        if mind.grudge:
            lines.append(f"grudge={mind.grudge}")
        if mind.last_known_neo_location:
            lines.append(f"last_neo@{mind.last_known_neo_location}")
        if mind.facts:
            lines.append("facts: " + " | ".join(mind.facts[-5:]))
        return "; ".join(lines)

    @classmethod
    def all_summaries(cls, names: list[str]) -> dict[str, str]:
        return {n: cls.dossier(n) for n in names}
