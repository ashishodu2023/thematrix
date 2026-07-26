from typing import Literal

from langgraph.types import Command

from matrix import story
from matrix.characters import PERSONAS
from matrix.config import config
from matrix.llm import speak


def architect(state: dict) -> Command[Literal["oracle_question", "cafe_scene"]]:
    """Architect routes via Command API based on threat level."""
    threat = state["threat_level"]
    story.scene("THE ARCHITECT")
    story.say(f"Location overlay: systemic threat {threat}/10")

    voice = speak(
        PERSONAS["architect"],
        (
            f"Human={state['human_id']} anomaly={state['anomaly']} "
            f"threat={threat} prior_lives={state['previous_lives']}. "
            "State the systemic response in one sentence."
        ),
    )
    story.speak_as("Architect", voice)

    if threat >= config.threat_skip_oracle:
        plan = f"Threat {threat}/10 — skip Oracle, proceed to cafe anomaly site."
        story.beat("Command API → cafe_scene")
        return Command(
            update={
                "architect_plan": plan,
                "scene": "architect",
                "dialogue": [f"Architect: {voice}"],
                "events": ["architect:skip_oracle"],
                "log": [f"[architect] {plan}"],
            },
            goto="cafe_scene",
        )

    plan = f"Threat {threat}/10 — consult Oracle before cafe deployment."
    story.beat("Command API → oracle_question (HITL)")
    return Command(
        update={
            "architect_plan": plan,
            "scene": "architect",
            "dialogue": [f"Architect: {voice}"],
            "events": ["architect:consult_oracle"],
            "log": [f"[architect] {plan}"],
        },
        goto="oracle_question",
    )
