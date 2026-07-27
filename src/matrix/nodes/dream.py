"""Act I — dream glitch and first contact."""

from matrix import story
from matrix.awareness import aware_node
from matrix.parallel import speak_many
from matrix.physics import apply_event
from matrix.surveillance import bump_trace, tap_phone
from matrix.world import LOCATIONS


@aware_node
def dream_glitch(state: dict) -> dict:
    loc = LOCATIONS["apartment"]
    story.scene("ACT I — DREAM GLITCH")
    story.say(f"{loc.name}: {loc.description}")
    story.say("A black cat crosses the hallway. Then another — identical.")

    lines = speak_many(
        [
            (
                "neo",
                (
                    f"You just saw a deja-vu glitch. Anomaly={state['anomaly']}. "
                    "Say how unsettled you feel in one short first-person sentence."
                ),
            ),
            (
                "tank",
                "As an operator watching residual signals, warn about deja-vu in one sentence.",
            ),
        ],
        state=state,
    )
    neo, note = lines["neo"], lines["tank"]
    story.speak_as("Neo", neo)
    story.speak_as("Tank (ghost signal)", note)

    rules = apply_event(list(state.get("physics_rules") or []), "glitch")
    tap = tap_phone(f"deja-vu residual @ {loc.id}")
    trace = bump_trace(state, 5.0, "deja_vu")

    return {
        "location": loc.id,
        "scene": "dream",
        "anomaly": "glitch",
        "physics_rules": rules,
        "dream_note": note,
        "dialogue": [f"Neo: {neo}", f"Tank: {note}"],
        "events": ["dream:deja_vu", "physics:glitch"],
        "log": [f"[dream] {neo}", "[physics] deja_vu applied"],
        "locations_visited": [loc.id],
        "active_tracks": ["neo:dream"],
        "phone_taps": tap.get("phone_taps") or [],
        "trace_level": trace.get("trace_level", state.get("trace_level")),
        "faction_scoreboard": {"zion": 0, "agents": 1, "system": 1},
    }


@aware_node
def meet_trinity(state: dict) -> dict:
    loc = LOCATIONS["club"]
    story.scene("ACT I — FIRST CONTACT")
    story.say(f"{loc.name}: {loc.description}")

    lines = speak_many(
        [
            (
                "trinity",
                (
                    f"Find Neo in a club. Prior lives={state.get('previous_lives', 0)}. "
                    "Invite him to follow in one terse sentence."
                ),
            ),
            (
                "neo",
                "Trinity just found you. React with suspicion and curiosity in one sentence.",
            ),
        ],
        state=state,
    )
    trinity, neo = lines["trinity"], lines["neo"]
    story.speak_as("Trinity", trinity)
    story.speak_as("Neo", neo)

    return {
        "location": loc.id,
        "scene": "contact",
        "dialogue": [f"Trinity: {trinity}", f"Neo: {neo}"],
        "events": ["contact:trinity"],
        "log": ["[contact] trinity"],
        "locations_visited": [loc.id],
        "active_tracks": ["neo:contact"],
    }
