"""Background field pulses — Agents / city tick while Neo's act advances."""

from __future__ import annotations

from matrix import story
from matrix.config import config
from matrix.parallel import act_many, merge_patches
from matrix.tick import world_tick


def field_pulse(state: dict, *, label: str = "field") -> dict:
    """
    Concurrent subplot: world tick + Agents decide in parallel.
    Designed to fan-out beside Neo story nodes in the graph.
    """
    live = dict(state)
    tick_patches: dict = {}
    for _ in range(max(1, config.world_ticks_per_scene)):
        tp = world_tick(live, neo_target=str(live.get("location") or "jack_point"))
        tick_patches.update(tp)
        live = {**live, **tp}

    agents = [
        a.strip().lower()
        for a in (state.get("agent_names") or ["Smith", "Jones", "Brown"])
    ]
    jobs = [
        (
            key,
            ["hunt", "patrol", "observe", "contain"],
            (
                f"Background field pulse while Neo's story continues elsewhere. "
                f"Neo last seen near {live.get('location')}. "
                f"Trace={live.get('trace_level')}. Act independently in the city."
            ),
        )
        for key in agents
    ]

    story.beat(f"∥ parallel track [{label}] — Agents thinking while Neo's act runs")
    results = act_many(jobs, state=live)

    dialogue = []
    patch_list = []
    for who, (decision, patches) in results.items():
        dialogue.append(f"Agent {who.title()}: {decision.speech}")
        story.speak_as(f"Agent {who.title()} (field)", decision.speech)
        patch_list.append(patches)

    merged = merge_patches(patch_list)
    return {
        "dialogue": dialogue,
        "events": [f"parallel:{label}:agents={len(results)}"],
        "log": [f"[parallel:{label}] agents={list(results)}"],
        "active_tracks": [f"agents:{label}"],
        **tick_patches,
        **merged,
    }


def field_pulse_a(state: dict) -> dict:
    return field_pulse(state, label="act0-rabbit")


def field_pulse_b(state: dict) -> dict:
    return field_pulse(state, label="act0-office")


def field_pulse_c(state: dict) -> dict:
    return field_pulse(state, label="act1-dream")


def field_pulse_d(state: dict) -> dict:
    return field_pulse(state, label="act2-cafe")


def field_pulse_e(state: dict) -> dict:
    return field_pulse(state, label="act4-combat")
