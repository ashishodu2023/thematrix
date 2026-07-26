"""
Jack into the Matrix — runs until the first HITL interrupt.

Each jack-in starts a fresh thread_id so reducer lists do not pile up.
"""

from matrix import story
from matrix import theme
from matrix.graph import get_graph, reset_graph_cache
from matrix.thread_store import new_thread_id

INITIAL_STATE = {
    "human_id": "neo",
    "city": "Mega City",
    "cycle": 1,
    "location": "",
    "scene": "",
    "physics_rules": ["gravity", "solidity", "causality", "spoon_exists"],
    "anomaly": "spoon",
    "threat_level": 4,
    "architect_plan": "",
    "oracle_question": "",
    "oracle_prophecy": "",
    "agent_names": ["Smith", "Jones", "Brown"],
    "current_agent": "",
    "agent_reports": [],
    "sectors_scanned": [],
    "spoon_exists": True,
    "reality_rewritten": False,
    "pursuit_round": 0,
    "pursuit_status": "idle",
    "pursuit_log": [],
    "pending_decision": "",
    "pill_choice": "",
    "trust_choice": "",
    "bug_choice": "",
    "steak_choice": "",
    "jump_choice": "",
    "fight_choice": "",
    "radio_choice": "",
    "code_choice": "",
    "awakened": False,
    "bug_implanted": False,
    "sentinel_alert": False,
    "training_skills": [],
    "training_score": 0,
    "showdown_round": 0,
    "showdown_status": "",
    "dream_note": "",
    "briefing": "",
    "dialogue": [],
    "events": [],
    "log": [],
    "outcome": "",
    "previous_lives": 0,
    "locations_visited": [],
    "agent_memory": [],
    "character_actions": [],
}


def _interrupt_payload(result: dict) -> dict:
    interrupts = result.get("__interrupt__") if isinstance(result, dict) else None
    if not interrupts:
        return {}
    first = interrupts[0]
    value = getattr(first, "value", first)
    return value if isinstance(value, dict) else {"message": str(value)}


def main() -> None:
    reset_graph_cache()
    thread_id = new_thread_id(INITIAL_STATE["human_id"])
    config = {"configurable": {"thread_id": thread_id}}
    graph = get_graph()

    theme.banner()
    theme.out("Multi-act cinematic mode (Ollama)", bold=True)
    theme.out(f"Fresh thread: {thread_id}")
    theme.out()

    try:
        result = graph.invoke(INITIAL_STATE, config=config)
    except Exception as exc:  # noqa: BLE001
        from matrix.llm import OllamaUnavailableError

        if isinstance(exc, OllamaUnavailableError) or "Ollama" in str(exc):
            print()
            print(str(exc))
            raise SystemExit(1) from exc
        raise

    payload = _interrupt_payload(result)
    if payload:
        kind = payload.get("kind") or result.get("pending_decision") or "unknown"
        hint = payload.get("message") or payload.get("hint") or ""
        story.pause_for_interrupt(thread_id, kind, hint, result)
    else:
        story.ending(result)


if __name__ == "__main__":
    main()
