from matrix import story
from matrix.awareness import use_state
from matrix.llm import character_act
from matrix.world import LOCATIONS


def cafe_scene(state: dict) -> dict:
    """Spoon cafe — boy and Neo act independently with awareness of each other."""
    loc = LOCATIONS["cafe"]
    story.scene("ACT II — THE SPOON CAFE")
    story.say(f"{loc.name}: {loc.description}")

    patches: dict = {"agent_memory": [], "character_actions": []}

    with use_state(state):
        boy_d, boy_p = character_act(
            "spoon_boy",
            ["teach", "hint", "silence"],
            (
                f"Anomaly setting is '{state['anomaly']}'. "
                "Neo sits across from you. Act independently about the spoon."
            ),
            state=state,
        )
    story.speak_as("Spoon Boy", boy_d.speech)
    for k, v in boy_p.items():
        patches[k] = list(patches.get(k) or []) + list(v)

    # Neo hears the boy — update local awareness mid-scene
    mid = {
        **state,
        "dialogue": list(state.get("dialogue") or [])
        + [f"Spoon Boy: {boy_d.speech}"],
        "agent_memory": list(state.get("agent_memory") or [])
        + list(patches.get("agent_memory") or []),
        "character_actions": list(state.get("character_actions") or [])
        + list(patches.get("character_actions") or []),
    }

    if state.get("oracle_prophecy"):
        story.say("The Oracle's words still echo under the cafe noise.")

    with use_state(mid):
        neo_d, neo_p = character_act(
            "neo",
            ["believe", "doubt", "question"],
            (
                f"Spoon boy said: '{boy_d.speech}' (action={boy_d.action}). "
                "React and choose your independent stance."
            ),
            state=mid,
        )
    story.speak_as("Neo", neo_d.speech)
    for k, v in neo_p.items():
        patches[k] = list(patches.get(k) or []) + list(v)

    return {
        "location": loc.id,
        "scene": "cafe",
        "dialogue": [f"Spoon Boy: {boy_d.speech}", f"Neo: {neo_d.speech}"],
        "events": [f"cafe:spoon:{boy_d.action}:{neo_d.action}"],
        "log": [f"[cafe] boy={boy_d.action} neo={neo_d.action}"],
        "locations_visited": [loc.id],
        **patches,
    }
