from matrix import story
from matrix.models import PreviousLife
from matrix.services.memory import SessionMemory
from matrix.tools.operator_tools import radio
from matrix.world import LOCATIONS


def operator_persist(state: dict) -> dict:
    """Persist this life outside the Matrix (Redis session memory)."""
    loc = LOCATIONS["real_world"] if state.get("awakened") else state.get("location")
    story.scene("OPERATOR (OUTSIDE)")
    msg = radio(
        f"cycle={state.get('cycle')} pill={state.get('pill_choice')} "
        f"bug={state.get('bug_choice')} trust={state.get('trust_choice')} "
        f"steak={state.get('steak_choice')} jump={state.get('jump_choice')} "
        f"fight={state.get('fight_choice')} radio={state.get('radio_choice')} "
        f"code={state.get('code_choice')} showdown={state.get('showdown_status')} "
        f"score={state.get('training_score')}"
    )
    story.say(msg)

    # Deduplicate visited locations while preserving order
    visited = list(dict.fromkeys(state.get("locations_visited") or []))

    life = PreviousLife(
        cycle=state["cycle"],
        city=state["city"],
        pill_choice=state.get("pill_choice") or "",
        outcome=state.get("outcome") or "",
        reality_rewritten=bool(state.get("reality_rewritten")),
        training_score=int(state.get("training_score") or 0),
        fight_choice=state.get("fight_choice") or "",
        trust_choice=state.get("trust_choice") or "",
        jump_choice=state.get("jump_choice") or "",
        radio_choice=state.get("radio_choice") or "",
        bug_choice=state.get("bug_choice") or "",
        steak_choice=state.get("steak_choice") or "",
        code_choice=state.get("code_choice") or "",
        showdown_status=state.get("showdown_status") or "",
        locations_visited=visited,
    )
    session = SessionMemory.record_life(state["human_id"], life)
    session = SessionMemory.apply_sticky(state["human_id"], state)
    knowledge = list(state.get("agent_memory") or [])
    if knowledge:
        session = SessionMemory.remember_agents(state["human_id"], knowledge)
        story.beat(
            f"Persisted {len(session.agent_knowledge)} agent-learning facts for next cycle"
        )
    if session.sticky_flags:
        story.beat(f"Sticky flags: {session.sticky_flags}")
    story.say(
        f"Life #{len(session.lives)} saved "
        f"(awakened_count={session.awakened_count})."
    )
    return {
        "previous_lives": len(session.lives),
        "location": loc if isinstance(loc, str) else state.get("location"),
        "scene": "operator",
        "sticky_flags": dict(session.sticky_flags),
        "events": ["operator:persisted"],
        "log": [
            f"[operator] cycle={state['cycle']} pill={state.get('pill_choice')} "
            f"agent_memory={len(knowledge)} sticky={list(session.sticky_flags)}"
        ],
    }
