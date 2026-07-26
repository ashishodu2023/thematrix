from typing import Literal

from langgraph.types import Command

from matrix import story
from matrix.awareness import use_state
from matrix.config import config
from matrix.llm import character_act


def architect(state: dict) -> Command[Literal["oracle_question", "cafe_scene"]]:
    """Architect independently chooses systemic routing from shared awareness."""
    threat = state["threat_level"]
    story.scene("THE ARCHITECT")
    story.say(f"Location overlay: systemic threat {threat}/10")

    # Hard floor: extreme threat always skips Oracle (systemic override).
    forced = threat >= config.threat_skip_oracle
    allowed = ["deploy_cafe", "consult_oracle"]
    if forced:
        allowed = ["deploy_cafe"]

    with use_state(state):
        decision, patches = character_act(
            "architect",
            allowed,
            (
                f"Human={state['human_id']} anomaly={state['anomaly']} "
                f"threat={threat} prior_lives={state['previous_lives']}. "
                "Choose the systemic response independently."
            ),
            state=state,
        )

    story.speak_as("Architect", decision.speech)
    if decision.learned:
        story.beat(f"Architect learned: {decision.learned}")

    if decision.action == "deploy_cafe" or forced:
        plan = (
            f"Threat {threat}/10 — Architect action={decision.action}: "
            "proceed to cafe anomaly site."
        )
        story.beat("Command API → cafe_scene")
        return Command(
            update={
                "architect_plan": plan,
                "scene": "architect",
                "dialogue": [f"Architect: {decision.speech}"],
                "events": ["architect:skip_oracle"],
                "log": [f"[architect] {plan}"],
                **patches,
            },
            goto="cafe_scene",
        )

    plan = (
        f"Threat {threat}/10 — Architect action={decision.action}: "
        "consult Oracle before cafe deployment."
    )
    story.beat("Command API → oracle_question (HITL)")
    return Command(
        update={
            "architect_plan": plan,
            "scene": "architect",
            "dialogue": [f"Architect: {decision.speech}"],
            "events": ["architect:consult_oracle"],
            "log": [f"[architect] {plan}"],
            **patches,
        },
        goto="oracle_question",
    )
