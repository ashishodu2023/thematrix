"""Agent-side tools (programs inside the Matrix)."""

from __future__ import annotations

import random


def scan_sector(agent: str, city: str, sector: str) -> str:
    return f"Agent {agent} scanned {city}/{sector}: residual self-image nominal"


def detect_anomaly(agent: str, anomaly: str) -> str:
    if anomaly == "spoon":
        return (
            f"Agent {agent} DETECTED anomaly: bent spoon at cafe "
            f"(subject may be The One)"
        )
    if anomaly == "glitch":
        return f"Agent {agent} DETECTED deja-vu glitch (black cat ×2)"
    return f"Agent {agent}: sector clear — no anomaly"


def rewrite_local(agent: str, target: str) -> str:
    return f"Agent {agent} rewrote local physics around '{target}'"


def pursue_step(agent: str, round_no: int, reality_rewritten: bool) -> tuple[str, str]:
    """
    Return (status_delta, narration).

    status_delta is one of: continue | escaped | caught
    """
    # Belief bends odds in Neo's favor after spoon scene.
    escape_chance = 0.55 if reality_rewritten else 0.35
    catch_chance = 0.25 if reality_rewritten else 0.45
    roll = random.random()
    if roll < escape_chance:
        return (
            "escaped",
            f"Round {round_no}: {agent} loses Neo in the crowd — escape!",
        )
    if roll < escape_chance + catch_chance:
        return (
            "caught",
            f"Round {round_no}: {agent} corners Neo — captured.",
        )
    return (
        "continue",
        f"Round {round_no}: {agent} closes distance — chase continues.",
    )
