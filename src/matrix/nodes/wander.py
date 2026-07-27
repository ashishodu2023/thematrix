"""City wander — open-world beat between Keymaker and swarm."""

from __future__ import annotations

from matrix import story
from matrix.awareness import aware_node, use_state
from matrix.city_graph import neighbors
from matrix.llm import character_act
from matrix.minds import MindStore
from matrix.objectives import scoreboard_delta
from matrix.parallel import speak_many
from matrix.rag import retrieve_block
from matrix.surveillance import bump_trace
from matrix.world import LOCATIONS


@aware_node
def city_wander(state: dict) -> dict:
    """Neo chooses a nearby sector; Agents react — free-roam flavor."""
    here = str(state.get("location") or "keymaker_hall")
    options = list(neighbors(here))[:4] or ["highway", "hotel_lobby", "cafe"]
    action_map = {f"go_{i}": loc for i, loc in enumerate(options)}
    allowed = list(action_map.keys()) + ["linger"]

    mem = retrieve_block(
        f"wander from {here} meta={state.get('meta_policy')}",
        human_id=str(state.get("human_id") or "neo"),
        character="neo",
        k=3,
    )
    with use_state(state):
        neo_d, neo_p = character_act(
            "neo",
            allowed,
            (
                f"You are free in Mega City at {here}. Neighbors: {options}. "
                f"{mem}\n"
                "Choose go_N to move to that neighbor index, or linger."
            ),
            state=state,
            tools="agent",
        )

    if neo_d.action == "linger":
        dest = here
        story.beat(f"Neo lingers in {here}.")
        trace = bump_trace(state, 5.0, f"wander_linger@{here}")
    else:
        dest = action_map.get(neo_d.action, options[0])
        story.beat(f"Neo moves toward {dest}.")
        trace = bump_trace(state, 3.0, f"wander:{here}->{dest}")

    loc = LOCATIONS.get(dest) or LOCATIONS.get(here)
    loc_id = loc.id if loc else dest
    story.scene("OPEN CITY — WANDER")
    story.say(f"Free roam. From {here} the streets lead to {', '.join(options)}.")
    story.speak_as("Neo", neo_d.speech)

    lines = speak_many(
        [
            (
                "trinity",
                f"Neo is wandering near {loc_id}. Give one terse extraction tip.",
            ),
            (
                "smith",
                f"Neo relocated toward {loc_id}. One hunting sentence.",
            ),
        ],
        state={**state, "location": loc_id},
    )
    story.speak_as("Trinity", lines["trinity"])
    story.speak_as("Agent Smith", lines["smith"])
    story.beat(f"BRANCH wander {here} → {loc_id}")
    MindStore.remember("smith", f"wander hunt toward {loc_id}", neo_location=loc_id)
    board = scoreboard_delta(
        [("neo", "dodge"), ("trinity", "cover"), ("smith", "hunt")]
    )
    hops = int(state.get("wander_hops") or 0) + 1

    return {
        "location": loc_id,
        "scene": "wander",
        "wander_hops": hops,
        "dialogue": [
            f"Neo: {neo_d.speech}",
            f"Trinity: {lines['trinity']}",
            f"Agent Smith: {lines['smith']}",
        ],
        "events": [f"wander:{here}->{loc_id}"],
        "log": [f"[wander] {here} → {loc_id} hop={hops}"],
        "locations_visited": [loc_id],
        "active_tracks": ["neo:wander", "agents:wander"],
        "faction_scoreboard": board,
        "trace_level": trace.get("trace_level", state.get("trace_level")),
        "agent_positions": {
            **(state.get("agent_positions") or {}),
            "neo": loc_id,
            "trinity": loc_id if neo_d.action != "linger" else (state.get("agent_positions") or {}).get("trinity", loc_id),
            "smith": loc_id,
        },
        "character_actions": list(neo_p.get("character_actions") or []),
        "agent_memory": list(neo_p.get("agent_memory") or []),
    }
