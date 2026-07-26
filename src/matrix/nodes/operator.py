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
        f"fight={state.get('fight_choice')} score={state.get('training_score')}"
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
        locations_visited=visited,
    )
    session = SessionMemory.record_life(state["human_id"], life)
    story.say(
        f"Life #{len(session.lives)} saved "
        f"(awakened_count={session.awakened_count})."
    )
    return {
        "previous_lives": len(session.lives),
        "location": loc if isinstance(loc, str) else state.get("location"),
        "scene": "operator",
        "events": ["operator:persisted"],
        "log": [
            f"[operator] cycle={state['cycle']} pill={state.get('pill_choice')}"
        ],
    }
