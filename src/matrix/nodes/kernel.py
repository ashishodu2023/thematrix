from matrix.services.memory import SessionMemory
from matrix import story
from matrix.world import DEFAULT_PHYSICS, LOCATIONS


def simulation_kernel(state: dict) -> dict:
    """Boot shared reality + recall prior lives from Operator memory."""
    session = SessionMemory.load(state["human_id"])
    lives = len(session.lives)
    city = state.get("city") or "Mega City"
    rules = list(state.get("physics_rules") or DEFAULT_PHYSICS)
    loc = LOCATIONS["jack_point"]

    story.scene("JACK IN")
    story.say(f"{state['human_id']} plugs into the Matrix.")
    story.say(f"{loc.name}: {loc.description}")
    story.say(f"City: {city}  |  prior lives remembered: {lives}")

    return {
        "city": city,
        "cycle": state.get("cycle") or max(lives + 1, 1),
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
        "pursuit_round": 0,
        "pursuit_status": "idle",
        "pursuit_log": [],
        "pending_decision": "",
        "pill_choice": "",
        "fight_choice": "",
        "awakened": False,
        "training_skills": [],
        "training_score": 0,
        "outcome": "",
        "previous_lives": lives,
        "current_agent": "",
        "dialogue": [],
        "events": [f"jack_in@{loc.id}"],
        "log": [f"[kernel] jack-in for {state['human_id']} lives={lives}"],
        "locations_visited": [loc.id],
    }
