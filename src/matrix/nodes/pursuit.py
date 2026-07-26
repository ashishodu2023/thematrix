from typing import Literal

from langgraph.types import Command

from matrix import story
from matrix.awareness import use_state
from matrix.config import config
from matrix.llm import character_act
from matrix.tools.agent_tools import pursue_step
from matrix.world import LOCATIONS


def pursuit_loop(
    state: dict,
) -> Command[Literal["pursuit_loop", "morpheus_offer"]]:
    """
    Agent Smith chase — independent LLM action each round + Command self-loop.
    """
    round_no = int(state.get("pursuit_round") or 0) + 1
    cycle = ["subway", "rooftop", "highway"]
    loc = LOCATIONS[cycle[(round_no - 1) % len(cycle)]]

    if round_no == 1:
        story.scene("PURSUIT")
        story.say("Sirens fold into Agent footsteps.")

    story.say(f"Round {round_no}/{config.pursuit_max_rounds} @ {loc.name}")

    with use_state(state):
        decision, patches = character_act(
            "smith",
            ["close_in", "cut_off", "intimidate", "hold"],
            (
                f"Pursuit round {round_no}/{config.pursuit_max_rounds} at {loc.name}. "
                f"Reality rewritten={state.get('reality_rewritten')}. "
                f"Prior pursuit log: {list(state.get('pursuit_log') or [])[-3:]}. "
                "Choose your independent hunting action."
            ),
            state=state,
        )

    story.speak_as("Agent Smith", decision.speech)
    if decision.learned:
        story.beat(f"Smith learned: {decision.learned}")

    status, narration = pursue_step(
        "Smith",
        round_no,
        bool(state.get("reality_rewritten")),
        preferred=decision.action,
    )
    story.beat(narration)

    base_update = {
        "pursuit_round": round_no,
        "location": loc.id,
        "scene": "pursuit",
        "dialogue": [f"Agent Smith: {decision.speech}"],
        "pursuit_log": [f"{narration} (action={decision.action})"],
        "events": [f"pursuit:r{round_no}:{status}:{decision.action}"],
        "log": [f"[pursuit] {narration}"],
        "locations_visited": [loc.id],
        **patches,
    }

    if status in {"escaped", "caught"}:
        return Command(
            update={
                **base_update,
                "pursuit_status": status,
            },
            goto="morpheus_offer",
        )

    if round_no >= config.pursuit_max_rounds:
        return Command(
            update={
                **base_update,
                "pursuit_status": "escaped",
                "pursuit_log": ["Max rounds — Neo escapes through a hardline."],
            },
            goto="morpheus_offer",
        )

    return Command(
        update={
            **base_update,
            "pursuit_status": "chasing",
        },
        goto="pursuit_loop",
    )
