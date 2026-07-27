from matrix.services.memory import SessionMemory
from matrix import story
from matrix import sound as matrix_sound
from matrix.minds import MindStore
from matrix.world import DEFAULT_PHYSICS, LOCATIONS


def simulation_kernel(state: dict) -> dict:
    """Boot shared reality + recall prior lives, sticky flags, agent knowledge."""
    session = SessionMemory.load(state["human_id"])
    lives = len(session.lives)
    city = state.get("city") or "Mega City"
    rules = list(state.get("physics_rules") or DEFAULT_PHYSICS)
    loc = LOCATIONS["jack_point"]
    prior_knowledge = list(getattr(session, "agent_knowledge", None) or [])
    sticky = dict(getattr(session, "sticky_flags", None) or {})
    co = state.get("co_human_id") or getattr(session, "co_human_id", "") or ""

    if sticky.get("saw_code") and "code_sight" not in rules:
        rules.append("code_sight")
    bug_implanted = bool(sticky.get("bug_implanted"))

    matrix_sound.play("jack")
    story.scene("JACK IN")
    story.say(f"{state['human_id']} plugs into the Matrix.")
    if co:
        story.say(f"Co-pilot jacked in: {co}")
    story.say(f"{loc.name}: {loc.description}")
    story.say(f"City: {city}  |  prior lives remembered: {lives}")
    if sticky:
        story.beat(f"Sticky branches active: {', '.join(sticky)}")
    if prior_knowledge:
        story.beat(
            f"Cast memories of other agents: {len(prior_knowledge)} facts carried over"
        )

    # Seed full cast on the city graph (Agents + Zion + programs)
    from matrix.cast import seed_positions

    agent_positions = seed_positions()
    agent_positions["neo"] = loc.id
    if co:
        agent_positions[str(co).lower()] = loc.id
    for name in agent_positions:
        MindStore.load(name)  # ensure mind exists

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
        "key_choice": "",
        "awakened": False,
        "bug_implanted": bug_implanted,
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
            f"[kernel] jack-in for {state['human_id']} co={co or '-'} "
            f"lives={lives} sticky={list(sticky)}"
        ],
        "locations_visited": [loc.id],
        "co_human_id": co,
        "world_tick": 0,
        "trace_level": 5.0 if bug_implanted else 0.0,
        "hardline_cooldown": 0,
        "phone_taps": [],
        "sector_heat": {},
        "agent_positions": agent_positions,
        "sticky_flags": sticky,
        "meta_policy": "",
        "faction_scoreboard": {"zion": 0, "agents": 0, "system": 0},
    }
