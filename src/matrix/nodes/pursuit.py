from typing import Literal

from langgraph.types import Command

from matrix import story
from matrix.characters import PERSONAS
from matrix.config import config
from matrix.llm import speak
from matrix.tools.agent_tools import pursue_step
from matrix.world import LOCATIONS


def pursuit_loop(
    state: dict,
) -> Command[Literal["pursuit_loop", "pill_choice"]]:
    """
    Agent Smith chase — Command API self-loop until escape/caught/max rounds.
    """
    round_no = int(state.get("pursuit_round") or 0) + 1
    loc = LOCATIONS["subway"] if round_no % 2 else LOCATIONS["rooftop"]

    if round_no == 1:
        story.scene("PURSUIT")
        story.say("Sirens fold into Agent footsteps.")

    story.say(f"Round {round_no}/{config.pursuit_max_rounds} @ {loc.name}")

    voice = speak(
        PERSONAS["smith"],
        (
            f"Pursuit round {round_no}. Reality rewritten="
            f"{state.get('reality_rewritten')}. "
            "Growl one hunting sentence."
        ),
    )
    story.speak_as("Agent Smith", voice)

    status, narration = pursue_step(
        "Smith",
        round_no,
        bool(state.get("reality_rewritten")),
    )
    story.beat(narration)

    base_update = {
        "pursuit_round": round_no,
        "location": loc.id,
        "scene": "pursuit",
        "dialogue": [f"Agent Smith: {voice}"],
        "pursuit_log": [narration],
        "events": [f"pursuit:r{round_no}:{status}"],
        "log": [f"[pursuit] {narration}"],
        "locations_visited": [loc.id],
    }

    if status in {"escaped", "caught"}:
        return Command(
            update={
                **base_update,
                "pursuit_status": status,
            },
            goto="pill_choice",
        )

    if round_no >= config.pursuit_max_rounds:
        # Time runs out — Neo slips away.
        return Command(
            update={
                **base_update,
                "pursuit_status": "escaped",
                "pursuit_log": ["Max rounds — Neo escapes through a hardline."],
            },
            goto="pill_choice",
        )

    return Command(
        update={
            **base_update,
            "pursuit_status": "chasing",
        },
        goto="pursuit_loop",
    )
