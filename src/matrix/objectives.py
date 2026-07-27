"""Competing objectives — Zion vs Agents vs System score resolution."""

from __future__ import annotations

from dataclasses import dataclass

from matrix.minds import MindStore

# action → (faction_benefit, score_delta_for_actor)
ACTION_SCORES: dict[str, tuple[str, int]] = {
    "hunt": ("agents", 2),
    "contain": ("agents", 2),
    "close_in": ("agents", 3),
    "cut_off": ("agents", 3),
    "suppress": ("agents", 2),
    "flank": ("agents", 2),
    "taunt": ("agents", 1),
    "patrol": ("agents", 1),
    "scan": ("agents", 1),
    "hold": ("agents", 0),
    "intimidate": ("agents", 1),
    "freeze": ("agents", 0),
    "extract": ("zion", 3),
    "cover": ("zion", 2),
    "advance": ("zion", 2),
    "follow_trinity": ("zion", 2),
    "dodge": ("zion", 1),
    "call": ("zion", 2),
    "believe": ("zion", 2),
    "take_key": ("zion", 3),
    "refuse_key": ("system", 1),
    "hardline": ("zion", 2),
    "emp": ("zion", 3),
    "jack_out": ("zion", 2),
    "teach": ("system", 1),
    "consult_oracle": ("system", 2),
    "deploy_cafe": ("system", 2),
    "reflect": ("self", 1),
    "adapt": ("self", 1),
    "ally": ("zion", 1),
    "oppose": ("agents", 1),
    "prepare": ("self", 1),
    "observe": ("system", 1),
    "defy": ("zion", 2),
    "accept_causality": ("system", 2),
}


@dataclass
class ConflictResult:
    winner: str
    narration: str
    scoreboard: dict[str, int]


def apply_action_score(character: str, action: str) -> int:
    faction, delta = ACTION_SCORES.get(action, ("self", 0))
    MindStore.add_score(character, delta, f"{action}/{faction}")
    return delta


def scoreboard_delta(actions: list[tuple[str, str]]) -> dict[str, int]:
    """Turn character actions into faction point deltas."""
    board = {"zion": 0, "agents": 0, "system": 0}
    for character, action in actions:
        faction, delta = ACTION_SCORES.get(action, ("self", 0))
        apply_action_score(character, action)
        if faction in board:
            board[faction] += delta
    return board


def accumulate_board(current: dict | None, delta: dict[str, int]) -> dict[str, int]:
    board = {"zion": 0, "agents": 0, "system": 0}
    for src in (current, delta):
        if not isinstance(src, dict):
            continue
        for k, v in src.items():
            key = str(k).lower()
            if key not in board:
                board[key] = 0
            board[key] += int(v or 0)
    return board


def resolve_conflict(
    zion_actions: list[tuple[str, str]],
    agent_actions: list[tuple[str, str]],
) -> ConflictResult:
    """
    Simple opposed roll from action weights.
    zion_actions / agent_actions: list of (character, action)
    """
    z_score = sum(ACTION_SCORES.get(a, ("", 0))[1] for _, a in zion_actions)
    a_score = sum(ACTION_SCORES.get(a, ("", 0))[1] for _, a in agent_actions)
    for c, a in zion_actions + agent_actions:
        apply_action_score(c, a)
    if z_score > a_score:
        return ConflictResult(
            "zion",
            f"Zion edge ({z_score} vs {a_score}): extraction pressure wins the beat.",
            {"zion": z_score, "agents": a_score, "system": 0},
        )
    if a_score > z_score:
        return ConflictResult(
            "agents",
            f"Agent edge ({a_score} vs {z_score}): the system tightens.",
            {"zion": z_score, "agents": a_score, "system": 0},
        )
    return ConflictResult(
        "draw",
        f"Stalemate ({z_score}={a_score}): rain and sirens, no decisive gain.",
        {"zion": z_score, "agents": a_score, "system": 0},
    )
