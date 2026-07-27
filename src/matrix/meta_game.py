"""Oracle vs Architect meta-game — competing systemic policies each cycle."""

from __future__ import annotations

from matrix.llm import character_act
from matrix.minds import MindStore
from matrix.awareness import use_state
from matrix import story


def meta_negotiate(state: dict) -> dict:
    """
    Architect seeks control; Oracle seeks choice. Their independent acts
    set meta_policy used later by Operator / routing flavor.
    """
    with use_state(state):
        arch, arch_p = character_act(
            "architect",
            ["control", "balance", "purge"],
            (
                f"Meta-layer. threat={state.get('threat_level')} "
                f"trace={state.get('trace_level')} anomaly={state.get('anomaly')}. "
                "Choose systemic policy for this cycle."
            ),
            state=state,
        )
        ora, ora_p = character_act(
            "oracle",
            ["guide", "test", "shield"],
            (
                f"Architect leans toward '{arch.action}'. "
                f"prior_lives={state.get('previous_lives')}. "
                "Choose how you counter-steer fate this cycle."
            ),
            state=state,
        )

    # Resolve meta tension
    if arch.action == "purge" and ora.action == "shield":
        policy = "contested"
        threat_delta = 0
    elif arch.action == "purge":
        policy = "purge"
        threat_delta = 2
    elif arch.action == "control":
        policy = "control"
        threat_delta = 1
    elif ora.action == "guide":
        policy = "choice"
        threat_delta = -1
    else:
        policy = "balance"
        threat_delta = 0

    threat = max(1, min(10, int(state.get("threat_level") or 4) + threat_delta))
    MindStore.remember("architect", f"policy={arch.action}; meta={policy}")
    MindStore.remember("oracle", f"policy={ora.action}; meta={policy}")

    story.scene("META LAYER")
    story.speak_as("Architect", arch.speech)
    story.speak_as("Oracle", ora.speech)
    story.beat(f"Meta policy this cycle: {policy}")

    patches: dict = {
        "meta_policy": policy,
        "threat_level": threat,
        "dialogue": [
            f"Architect: {arch.speech}",
            f"Oracle: {ora.speech}",
        ],
        "events": [f"meta:{policy}"],
        "log": [f"[meta] arch={arch.action} ora={ora.action} → {policy}"],
        "agent_memory": [],
        "character_actions": [],
    }
    for p in (arch_p, ora_p):
        for k, v in p.items():
            patches[k] = list(patches.get(k) or []) + list(v)
    return patches
