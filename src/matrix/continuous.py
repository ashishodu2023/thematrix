"""Between-cycle learning — cast keeps deciding independently forever."""

from __future__ import annotations

from matrix.awareness import use_state
from matrix.llm import character_act
from matrix.services.memory import SessionMemory

# Main cast that reflects after every finished life
CONTINUOUS_LEARNERS: tuple[str, ...] = (
    "neo",
    "trinity",
    "morpheus",
    "smith",
    "oracle",
    "architect",
    "tank",
    "cypher",
    "jones",
    "brown",
)


def learning_pulse(result: dict, *, human_id: str | None = None) -> list[str]:
    """
    After a cycle ends, every major character independently reviews peers,
    chooses a stance, and stores LEARN facts for the next jack-in.
    """
    hid = human_id or str(result.get("human_id") or "neo")
    state = {
        **result,
        "agent_memory": list(result.get("agent_memory") or []),
        "character_actions": list(result.get("character_actions") or []),
        "dialogue": list(result.get("dialogue") or [])[-20:],
        "agent_reports": list(result.get("agent_reports") or [])[-12:],
    }
    learned: list[str] = []
    outcome = result.get("outcome") or "(unknown)"
    awakened = result.get("awakened")

    for name in CONTINUOUS_LEARNERS:
        with use_state(state):
            decision, patches = character_act(
                name,
                ["reflect", "adapt", "ally", "oppose", "prepare"],
                (
                    f"A Matrix cycle just ended. outcome={outcome!r} "
                    f"awakened={awakened}. "
                    "Review what other agents did. Choose your independent "
                    "stance for the NEXT cycle and learn one fact about a peer."
                ),
                state=state,
            )
        fact = (
            f"{name}: pulse action={decision.action} — {decision.speech[:100]}"
        )
        learned.append(fact)
        if decision.learned:
            learned.append(f"{name}: learned — {decision.learned}")
        # Grow shared awareness for subsequent learners in this pulse
        for key in ("agent_memory", "character_actions"):
            extra = list(patches.get(key) or [])
            state[key] = list(state.get(key) or []) + extra

    SessionMemory.remember_agents(hid, learned)
    # Also fold any in-cycle memory
    SessionMemory.remember_agents(hid, list(state.get("agent_memory") or [])[-40:])
    return learned
