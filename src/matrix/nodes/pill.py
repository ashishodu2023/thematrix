from typing import Literal

from langgraph.types import Command, interrupt

from matrix import story
from matrix.awareness import aware_node
from matrix.llm import character_speak


@aware_node
def morpheus_offer(state: dict) -> dict:
    """Morpheus offers the pills — runs once before the HITL interrupt."""
    story.scene("THE PILLS")
    morpheus = character_speak("morpheus",
        (
            f"Neo just {state.get('pursuit_status', 'survived')} a pursuit. "
            "Offer the red and blue pills in one profound sentence."
        ),
    )
    story.speak_as("Morpheus", morpheus)
    story.say("The simulation waits for your choice…")
    return {
        "scene": "pill",
        "dialogue": [f"Morpheus: {morpheus}"],
        "events": ["pill:offered"],
        "log": ["[pill] offered"],
    }


def pill_choice(
    state: dict,
) -> Command[Literal["blue_ending", "ship_awaken"]]:
    """HITL only — interrupt first so resume does not re-call Ollama."""
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

    story.scene("PILL CHOICE")
    story.say(f"Operator chose: {pill}")

    update = {
        "pill_choice": pill,
        "pending_decision": "",
        "events": [f"pill:{pill}"],
        "log": [f"[pill] {pill}"],
        "scene": "pill",
    }

    if pill == "red":
        return Command(
            update={**update, "awakened": True},
            goto="ship_awaken",
        )

    return Command(
        update={**update, "awakened": False},
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


@aware_node
def trinity_warn(state: dict) -> dict:
    """Trinity warns once before fight/flee interrupt."""
    story.scene("FIGHT OR FLEE")
    trinity = character_speak("trinity",
        "Smith is loading. Tell Neo to fight or run in one terse sentence.",
    )
    story.speak_as("Trinity", trinity)
    story.say("The simulation waits for your choice…")
    return {
        "dialogue": [f"Trinity: {trinity}"],
        "events": ["fight:warned"],
        "log": ["[fight] warned"],
    }


def fight_or_flee(state: dict) -> dict:
    """HITL only — interrupt first so resume does not re-call Ollama."""
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

    story.scene("YOUR MOVE")
    story.say(f"Operator chose: {decision}")
    return {
        "fight_choice": decision,
        "pending_decision": "",
        "events": [f"fight_or_flee:{decision}"],
        "log": [f"[fight_or_flee] {decision}"],
    }


def resolve_choice(state: dict) -> dict:
    story.scene("WAKE OR SLEEP")
    pill = state.get("pill_choice") or "blue"
    fight = state.get("fight_choice") or ""
    score = int(state.get("training_score") or 0)
    trust = state.get("trust_choice") or ""
    jump = state.get("jump_choice") or ""
    radio = state.get("radio_choice") or ""
    code = state.get("code_choice") or ""
    bug = state.get("bug_choice") or ""
    steak = state.get("steak_choice") or ""
    showdown = state.get("showdown_status") or ""

    if pill == "blue":
        outcome = (
            f"{state['human_id']} takes the blue pill — "
            "wakes in bed, believes what they want to believe."
        )
        awakened = False
    elif fight == "fight" and score >= 8 and code == "accept":
        outcome = (
            f"{state['human_id']} extracts_bug={bug}, trusts={trust}, "
            f"steak={steak}, jumps={jump}, score={score}, fights Smith "
            f"({showdown}), radio={radio}, sees the code — The One begins."
        )
        awakened = True
    elif fight == "fight" and score >= 6:
        outcome = (
            f"{state['human_id']} trusts={trust}, jumps={jump}, "
            f"trains (score={score}), fights Smith ({showdown}), "
            f"radio={radio}, code={code} — the beginning of belief."
        )
        awakened = True
    elif fight == "fight":
        outcome = (
            f"{state['human_id']} takes the red pill but undertrained "
            f"(score={score}); Smith nearly wins — rescued by Trinity "
            f"(radio={radio}, code={code})."
        )
        awakened = True
    elif fight == "flee":
        outcome = (
            f"{state['human_id']} takes the red pill, trains (score={score}), "
            f"flees to a hardline, radio={radio}, code={code} — "
            "lives to fight another cycle."
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
