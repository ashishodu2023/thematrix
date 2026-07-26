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


def pursue_step(
    agent: str,
    round_no: int,
    reality_rewritten: bool,
    preferred: str | None = None,
) -> tuple[str, str]:
    """
    Return (status_delta, narration).

    status_delta is one of: continue | escaped | caught
    `preferred` is Smith's independent LLM action biasing the chase.
    """
    escape_chance = 0.55 if reality_rewritten else 0.35
    catch_chance = 0.25 if reality_rewritten else 0.45

    # Independent Agent tactics bias the odds.
    if preferred == "close_in":
        catch_chance += 0.12
        escape_chance -= 0.08
    elif preferred == "cut_off":
        catch_chance += 0.08
        escape_chance -= 0.05
    elif preferred == "intimidate":
        escape_chance += 0.05
    elif preferred == "hold":
        escape_chance += 0.10
        catch_chance -= 0.08

    escape_chance = max(0.05, min(0.85, escape_chance))
    catch_chance = max(0.05, min(0.85, catch_chance))
    # renormalize if sum > 1
    total = escape_chance + catch_chance
    if total > 0.95:
        escape_chance *= 0.95 / total
        catch_chance *= 0.95 / total

    roll = random.random()
    if roll < escape_chance:
        return (
            "escaped",
            f"Round {round_no}: {agent} ({preferred or 'pursue'}) "
            f"loses Neo in the crowd — escape!",
        )
    if roll < escape_chance + catch_chance:
        return (
            "caught",
            f"Round {round_no}: {agent} ({preferred or 'pursue'}) "
            f"corners Neo — captured.",
        )
    return (
        "continue",
        f"Round {round_no}: {agent} ({preferred or 'pursue'}) "
        f"closes distance — chase continues.",
    )
