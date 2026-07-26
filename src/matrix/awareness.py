"""Shared awareness — characters learn about others and act independently."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator

_STATE: ContextVar[dict | None] = ContextVar("matrix_awareness_state", default=None)


@contextmanager
def use_state(state: dict) -> Iterator[dict]:
    """Bind graph state so character_speak / character_act see other agents."""
    token = _STATE.set(state)
    try:
        yield state
    finally:
        _STATE.reset(token)


def aware_node(fn):
    """Decorator: bind Matrix state for the duration of a node function."""
    from functools import wraps

    @wraps(fn)
    def wrapper(state, *args, **kwargs):
        with use_state(state):
            return fn(state, *args, **kwargs)

    return wrapper


def current_state() -> dict | None:
    return _STATE.get()


def dossier_of_others(character: str, state: dict | None, *, limit: int = 12) -> str:
    """
    Build a short multi-agent awareness brief for `character`.

    Pulls recent dialogue, Agent reports, actions, and persistent memories
    so each brain can learn what other agents are doing.
    """
    if not state:
        return "No shared Matrix awareness yet."

    key = character.strip().lower()
    lines: list[str] = []

    city = state.get("city") or "?"
    threat = state.get("threat_level")
    anomaly = state.get("anomaly")
    scene = state.get("scene") or "?"
    lines.append(
        f"World: city={city} scene={scene} anomaly={anomaly} threat={threat}"
    )

    agents = state.get("agent_names") or []
    if agents:
        others = [a for a in agents if a.strip().lower() != key]
        if others:
            lines.append(f"Known Agents in field: {', '.join(others)}")

    # Persistent cross-cycle / prior observations
    memory = list(state.get("agent_memory") or [])
    if memory:
        lines.append("Learned about others:")
        for item in memory[-limit:]:
            if key and f"{key}:" == str(item).split(" ", 1)[0].lower():
                continue
            lines.append(f"  - {item}")

    # Peer independent actions this cycle
    actions = list(state.get("character_actions") or [])
    peer_actions = [
        a for a in actions if not str(a).lower().startswith(f"{key}:")
    ]
    if peer_actions:
        lines.append("Recent independent actions by others:")
        for item in peer_actions[-limit:]:
            lines.append(f"  - {item}")

    # Swarm reports (other Agents)
    reports = list(state.get("agent_reports") or [])
    if reports:
        lines.append("Agent field reports:")
        for item in reports[-limit:]:
            lines.append(f"  - {item}")

    # Dialogue from other mouths
    dialogue = list(state.get("dialogue") or [])
    others_lines = []
    for line in dialogue:
        speaker = str(line).split(":", 1)[0].strip().lower()
        speaker_key = speaker.replace("agent ", "").replace(" ", "_")
        if speaker_key == key or speaker == key:
            continue
        others_lines.append(line)
    if others_lines:
        lines.append("What others said:")
        for item in others_lines[-limit:]:
            lines.append(f"  - {item}")

    prophecy = state.get("oracle_prophecy") or ""
    if prophecy and key != "oracle":
        lines.append(f"Oracle prophecy echo: {prophecy}")

    plan = state.get("architect_plan") or ""
    if plan and key != "architect":
        lines.append(f"Architect plan known: {plan}")

    return "\n".join(lines)


def remember(character: str, observation: str) -> dict:
    """State patch: character learned a fact about the Matrix / others."""
    text = observation.strip()
    if not text:
        return {}
    return {
        "agent_memory": [f"{character}: learned — {text}"],
    }


def record_action(character: str, action: str, detail: str = "") -> dict:
    """State patch: character took an independent action."""
    bit = f"{character}: {action}"
    if detail:
        bit = f"{bit} — {detail}"
    return {
        "character_actions": [bit],
        "agent_memory": [f"{character}: observed action {action}"],
    }


@dataclass
class CharacterDecision:
    action: str
    speech: str
    learned: str = ""


def parse_decision(raw: str, allowed: list[str]) -> tuple[str, str, str]:
    """
    Parse LLM output of the form:
      ACTION: <option>
      SAY: <line>
      LEARN: <fact about another agent>
    """
    action = allowed[0]
    speech = raw.strip()
    learned = ""
    lower = raw.lower()
    for opt in allowed:
        token = f"action: {opt}"
        if token in lower or lower.strip().startswith(opt) or f"\n{opt}" in lower:
            action = opt
            break
        # also accept ACTION: opt on its own line
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    say_parts: list[str] = []
    for ln in lines:
        low = ln.lower()
        if low.startswith("action:"):
            cand = ln.split(":", 1)[1].strip().lower().split()[0].strip(",.")
            if cand in allowed:
                action = cand
            continue
        if low.startswith("say:"):
            say_parts.append(ln.split(":", 1)[1].strip())
            continue
        if low.startswith("learn:"):
            learned = ln.split(":", 1)[1].strip()
            continue
        if not low.startswith("action"):
            say_parts.append(ln)
    if say_parts:
        speech = " ".join(say_parts).strip().strip('"')
    # fallback: first matching option token anywhere
    tokens = raw.lower().replace(".", " ").replace(",", " ").split()
    for t in tokens:
        if t in allowed:
            action = t
            break
    if not speech:
        speech = raw.strip()
    return action, speech, learned
