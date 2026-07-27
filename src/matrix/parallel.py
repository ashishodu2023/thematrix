"""Parallel cast actions — multiple brains think at once (ThreadPool)."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from matrix.awareness import CharacterDecision, current_state
from matrix.config import config
from matrix.llm import character_act, character_speak


def parallel_enabled() -> bool:
    if os.getenv("MATRIX_PARALLEL", "").strip().lower() in {"0", "false", "no", "off"}:
        return False
    return True


def _workers(n: int) -> int:
    if n <= 1:
        return 1
    cap = 6 if config.fast else 4
    return max(1, min(n, cap))


def speak_many(
    jobs: list[tuple[str, str]],
    state: dict | None = None,
) -> dict[str, str]:
    """
    Run several character_speak calls concurrently.

    jobs: [(character_key, prompt), ...]
    returns: {character_key: spoken_line}
    """
    if not jobs:
        return {}
    ctx = state if state is not None else current_state()
    if not parallel_enabled() or len(jobs) == 1:
        return {
            who: character_speak(who, prompt, state=ctx, stream=False)
            for who, prompt in jobs
        }

    out: dict[str, str] = {}

    def _one(who: str, prompt: str) -> tuple[str, str]:
        return who, character_speak(who, prompt, state=ctx, stream=False)

    with ThreadPoolExecutor(max_workers=_workers(len(jobs))) as pool:
        futs = [pool.submit(_one, who, prompt) for who, prompt in jobs]
        for fut in as_completed(futs):
            who, line = fut.result()
            out[who] = line
    return out


def act_many(
    jobs: list[tuple[str, list[str], str]],
    state: dict | None = None,
) -> dict[str, tuple[CharacterDecision, dict]]:
    """
    Run several character_act calls concurrently (independent decisions).

    jobs: [(character_key, allowed_actions, situation), ...]
    returns: {character_key: (decision, patches)}
    """
    if not jobs:
        return {}
    ctx = state if state is not None else current_state()
    if not parallel_enabled() or len(jobs) == 1:
        return {
            who: character_act(who, allowed, situation, state=ctx)
            for who, allowed, situation in jobs
        }

    out: dict[str, tuple[CharacterDecision, dict]] = {}

    def _one(
        who: str, allowed: list[str], situation: str
    ) -> tuple[str, CharacterDecision, dict]:
        decision, patches = character_act(who, allowed, situation, state=ctx)
        return who, decision, patches

    with ThreadPoolExecutor(max_workers=_workers(len(jobs))) as pool:
        futs = [
            pool.submit(_one, who, allowed, situation)
            for who, allowed, situation in jobs
        ]
        for fut in as_completed(futs):
            who, decision, patches = fut.result()
            out[who] = (decision, patches)
    return out


def merge_patches(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge parallel character patches (list fields concatenate)."""
    merged: dict[str, Any] = {}
    for p in parts:
        for k, v in (p or {}).items():
            if isinstance(v, list):
                merged[k] = list(merged.get(k) or []) + list(v)
            else:
                merged[k] = v
    return merged
