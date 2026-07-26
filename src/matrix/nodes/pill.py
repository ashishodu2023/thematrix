from typing import Literal

from langgraph.types import Command, interrupt

from matrix import story
from matrix.characters import PERSONAS
from matrix.llm import speak


def pill_choice(
    state: dict,
) -> Command[Literal["blue_ending", "construct_training"]]:
    """HITL — red / blue pill. Red → Construct; blue → illusion ending."""
    story.scene("THE PILLS")
    morpheus = speak(
        PERSONAS["morpheus"],
        (
            f"Neo just {state.get('pursuit_status', 'survived')} a pursuit. "
            "Offer the red and blue pills in one profound sentence."
        ),
    )
    story.speak_as("Morpheus", morpheus)

    choice = interrupt(
        {
            "kind": "pill",
            "message": "Choose red (truth) or blue (illusion).",
            "human_id": state["human_id"],
            "oracle_prophecy": state.get("oracle_prophecy"),
            "pursuit_status": state.get("pursuit_status"),
        }
    )
    pill = str(choice).strip().lower()
    if pill not in {"red", "blue"}:
        pill = "blue"

    story.say(f"Operator chose: {pill}")

    update = {
        "pill_choice": pill,
        "pending_decision": "pill",
        "dialogue": [f"Morpheus: {morpheus}"],
        "events": [f"pill:{pill}"],
        "log": [f"[pill] {pill}"],
        "scene": "pill",
    }

    if pill == "red":
        return Command(
            update={
                **update,
                "awakened": True,
                "pending_decision": "",
            },
            goto="construct_training",
        )

    return Command(
        update={
            **update,
            "awakened": False,
            "pending_decision": "",
        },
        goto="blue_ending",
    )


def blue_ending(state: dict) -> dict:
    story.scene("BLUE PILL")
    story.say(f"{state['human_id']} wakes in bed. The Matrix seals shut.")
    outcome = (
        f"{state['human_id']} takes the blue pill — "
        "wakes in bed, believes what they want to believe."
    )
    return {
        "outcome": outcome,
        "events": ["ending:blue"],
        "log": [f"[blue] {outcome}"],
    }


def fight_or_flee(state: dict) -> dict:
    """HITL after Construct — fight Smith or flee to hardline."""
    story.scene("FIGHT OR FLEE")
    trinity = speak(
        PERSONAS["trinity"],
        "Smith is loading. Tell Neo to fight or run in one terse sentence.",
    )
    story.speak_as("Trinity", trinity)

    choice = interrupt(
        {
            "kind": "fight_or_flee",
            "message": "Choose fight or flee.",
            "training_score": state.get("training_score", 0),
        }
    )
    decision = str(choice).strip().lower()
    if decision not in {"fight", "flee"}:
        decision = "flee"

    story.say(f"Operator chose: {decision}")
    return {
        "fight_choice": decision,
        "pending_decision": "",
        "dialogue": [f"Trinity: {trinity}"],
        "events": [f"fight_or_flee:{decision}"],
        "log": [f"[fight_or_flee] {decision}"],
    }


def resolve_choice(state: dict) -> dict:
    story.scene("WAKE OR SLEEP")
    pill = state.get("pill_choice") or "blue"
    fight = state.get("fight_choice") or ""
    score = int(state.get("training_score") or 0)

    if pill == "blue":
        outcome = (
            f"{state['human_id']} takes the blue pill — "
            "wakes in bed, believes what they want to believe."
        )
        awakened = False
    elif fight == "fight" and score >= 2:
        outcome = (
            f"{state['human_id']} takes the red pill, trains (score={score}), "
            "and stands against Smith — beginning of belief."
        )
        awakened = True
    elif fight == "fight":
        outcome = (
            f"{state['human_id']} takes the red pill but undertrained "
            f"(score={score}); Smith nearly wins — rescued by Trinity."
        )
        awakened = True
    elif fight == "flee":
        outcome = (
            f"{state['human_id']} takes the red pill, trains (score={score}), "
            "and flees to a hardline — lives to fight another cycle."
        )
        awakened = True
    else:
        outcome = (
            f"{state['human_id']} takes the red pill — "
            "unplugged; welcome to the desert of the real."
        )
        awakened = True

    story.say(outcome)
    return {
        "pill_choice": pill,
        "awakened": awakened,
        "outcome": outcome,
        "scene": "resolve",
        "events": ["resolve:done"],
        "log": [f"[resolve] {outcome}"],
    }
