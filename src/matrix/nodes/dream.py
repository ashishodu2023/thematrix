"""Act I — dream glitch and first contact."""

from matrix import story
from matrix.awareness import aware_node
from matrix.llm import character_speak
from matrix.world import LOCATIONS


@aware_node
def dream_glitch(state: dict) -> dict:
    loc = LOCATIONS["apartment"]
    story.scene("ACT I — DREAM GLITCH")
    story.say(f"{loc.name}: {loc.description}")
    story.say("A black cat crosses the hallway. Then another — identical.")

    neo = character_speak("neo",
        (
            f"You just saw a deja-vu glitch. Anomaly={state['anomaly']}. "
            "Say how unsettled you feel in one short first-person sentence."
        ),
    )
    story.speak_as("Neo", neo)

    note = character_speak("tank",
        "As an operator watching residual signals, warn about deja-vu in one sentence.",
    )
    story.speak_as("Tank (ghost signal)", note)

    return {
        "location": loc.id,
        "scene": "dream",
        "dream_note": note,
        "dialogue": [f"Neo: {neo}", f"Tank: {note}"],
        "events": ["dream:deja_vu"],
        "log": [f"[dream] {neo}"],
        "locations_visited": [loc.id],
    }


@aware_node
def meet_trinity(state: dict) -> dict:
    loc = LOCATIONS["club"]
    story.scene("ACT I — FIRST CONTACT")
    story.say(f"{loc.name}: {loc.description}")

    trinity = character_speak("trinity",
        (
            f"Find Neo in a club. Prior lives={state.get('previous_lives', 0)}. "
            "Invite him to follow in one terse sentence."
        ),
    )
    story.speak_as("Trinity", trinity)

    neo = character_speak("neo",
        "Trinity just found you. React with suspicion and curiosity in one sentence.",
    )
    story.speak_as("Neo", neo)

    return {
        "location": loc.id,
        "scene": "contact",
        "dialogue": [f"Trinity: {trinity}", f"Neo: {neo}"],
        "events": ["contact:trinity"],
        "log": ["[contact] trinity"],
        "locations_visited": [loc.id],
    }
