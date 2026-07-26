from matrix.services.memory import SessionMemory
from matrix import story
from matrix.world import DEFAULT_PHYSICS, LOCATIONS


def simulation_kernel(state: dict) -> dict:
    """Boot shared reality + recall prior lives and agent knowledge."""
    session = SessionMemory.load(state["human_id"])
    lives = len(session.lives)
    city = state.get("city") or "Mega City"
    rules = list(state.get("physics_rules") or DEFAULT_PHYSICS)
    loc = LOCATIONS["jack_point"]
    prior_knowledge = list(getattr(session, "agent_knowledge", None) or [])

    story.scene("JACK IN")
    story.say(f"{state['human_id']} plugs into the Matrix.")
    story.say(f"{loc.name}: {loc.description}")
    story.say(f"City: {city}  |  prior lives remembered: {lives}")
    if prior_knowledge:
        story.beat(
            f"Cast memories of other agents: {len(prior_knowledge)} facts carried over"
        )

    return {
        "city": city,
        "cycle": lives + 1,
        "location": loc.id,
        "scene": "jack_in",
        "physics_rules": rules,
        "spoon_exists": "spoon_exists" in rules,
        "reality_rewritten": False,
        "architect_plan": "",
        "oracle_question": "",
        "oracle_prophecy": "",
        "agent_reports": [],
        "sectors_scanned": [],
        "agent_memory": prior_knowledge,
        "character_actions": [],
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
        "outcome": "",
        "previous_lives": lives,
        "current_agent": "",
        "dialogue": [],
        "events": [f"jack_in@{loc.id}"],
        "log": [
            f"[kernel] jack-in for {state['human_id']} lives={lives} "
            f"agent_memory={len(prior_knowledge)}"
        ],
        "locations_visited": [loc.id],
    }
