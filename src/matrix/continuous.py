"""Between-cycle learning — cast keeps deciding independently forever."""

from __future__ import annotations

from matrix.config import config
from matrix.parallel import act_many, merge_patches
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
    "niobe",
    "keymaker",
    "merovingian",
)

# Fast mode: fewer LLM calls between lives
FAST_LEARNERS: tuple[str, ...] = (
    "neo",
    "trinity",
    "smith",
    "oracle",
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
    learners = FAST_LEARNERS if config.fast else CONTINUOUS_LEARNERS

    jobs = [
        (
            name,
            ["reflect", "adapt", "ally", "oppose", "prepare"],
            (
                f"A Matrix cycle just ended. outcome={outcome!r} "
                f"awakened={awakened}. "
                "Review what other agents did. Choose your independent "
                "stance for the NEXT cycle and learn one fact about a peer."
            ),
        )
        for name in learners
    ]
    results = act_many(jobs, state=state)
    patch_list = []
    for name in learners:
        decision, patches = results[name]
        fact = (
            f"{name}: pulse action={decision.action} — {decision.speech[:100]}"
        )
        learned.append(fact)
        if decision.learned:
            learned.append(f"{name}: learned — {decision.learned}")
        patch_list.append(patches)

    merged = merge_patches(patch_list)
    for key in ("agent_memory", "character_actions"):
        extra = list(merged.get(key) or [])
        state[key] = list(state.get(key) or []) + extra

    SessionMemory.remember_agents(hid, learned)
    SessionMemory.remember_agents(hid, list(state.get("agent_memory") or [])[-40:])

    # MindStore: update goals/grudges from pulse stances
    try:
        from matrix.minds import MindStore

        loc = str(result.get("location") or "")
        for name in learners:
            decision, _ = results[name]
            if decision.action == "oppose":
                MindStore.remember(
                    name,
                    f"grudge after cycle outcome={outcome}",
                    neo_location=loc if name in {"smith", "jones", "brown"} else "",
                )
            elif decision.action == "ally":
                MindStore.remember(name, f"ally stance after {outcome}", neo_location=loc)
            elif decision.action == "prepare":
                MindStore.remember(name, f"preparing for next life ({outcome})")
            if name in {"smith", "jones", "brown"} and loc:
                MindStore.remember(name, f"last saw Neo near {loc}", neo_location=loc)
    except Exception:  # noqa: BLE001
        pass
    return learned
