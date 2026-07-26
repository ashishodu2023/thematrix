from matrix import story
from matrix.characters import PERSONAS
from matrix.llm import speak
from matrix.world import LOCATIONS


def cafe_scene(state: dict) -> dict:
    """Spoon cafe — belief vs form."""
    loc = LOCATIONS["cafe"]
    story.scene("THE SPOON CAFE")
    story.say(f"{loc.name}: {loc.description}")

    boy = speak(
        PERSONAS["spoon_boy"],
        (
            f"Anomaly setting is '{state['anomaly']}'. "
            "Tell Neo the truth about the spoon in one short sentence."
        ),
    )
    story.speak_as("Spoon Boy", boy)

    return {
        "location": loc.id,
        "scene": "cafe",
        "dialogue": [f"Spoon Boy: {boy}"],
        "events": ["cafe:spoon"],
        "log": [f"[cafe] {boy}"],
        "locations_visited": [loc.id],
    }
