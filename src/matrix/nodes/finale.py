"""Final act — subway showdown loop, code vision, Zion."""

from typing import Literal

from langgraph.types import Command, interrupt

from matrix import story
from matrix.awareness import aware_node
from matrix.config import config
from matrix.llm import character_speak
from matrix.world import LOCATIONS


@aware_node
def subway_showdown(
    state: dict,
) -> Command[Literal["subway_showdown", "phone_booth"]]:
    """Command-loop fight rounds after radio extraction attempt."""
    round_no = int(state.get("showdown_round") or 0) + 1
    max_rounds = config.showdown_max_rounds
    loc = LOCATIONS["subway"]

    if round_no == 1:
        story.scene("ACT V — SUBWAY SHOWDOWN")
        story.say(f"{loc.name}: empty platform. Rain through broken glass.")

    story.say(f"Showdown round {round_no}/{max_rounds}")

    smith = character_speak("smith",
        (
            f"Showdown round {round_no}. Neo fight_choice={state.get('fight_choice')}. "
            "One contemptuous combat sentence."
        ),
    )
    neo = character_speak("neo",
        (
            f"Round {round_no}, training_score={state.get('training_score', 0)}. "
            "One defiant combat sentence."
        ),
    )
    story.speak_as("Agent Smith", smith)
    story.speak_as("Neo", neo)

    score = int(state.get("training_score") or 0)
    # Higher score ends the fight sooner.
    done = round_no >= max_rounds or (score >= 8 and round_no >= 2)

    update = {
        "showdown_round": round_no,
        "location": loc.id,
        "dialogue": [f"Agent Smith: {smith}", f"Neo: {neo}"],
        "events": [f"showdown:r{round_no}"],
        "log": [f"[showdown] r{round_no}"],
        "locations_visited": [loc.id],
    }

    if done:
        if score >= 6:
            story.beat("Neo stands. Smith staggers. The booth light flickers.")
            update["showdown_status"] = "won"
        else:
            story.beat("Neo barely makes the booth as Smith closes in.")
            update["showdown_status"] = "escaped"
        return Command(update=update, goto="phone_booth")

    return Command(update=update, goto="subway_showdown")


@aware_node
def phone_booth(state: dict) -> dict:
    story.scene("ACT V — HARDLINE")
    story.say("Phone ringing. Exit vector locked. Fingers on metal.")
    trinity = character_speak("trinity",
        "Urge Neo to pick up before Smith reaches him — one urgent sentence.",
    )
    story.speak_as("Trinity", trinity)
    return {
        "dialogue": [f"Trinity: {trinity}"],
        "events": ["hardline:ring"],
        "log": ["[hardline] ring"],
    }


@aware_node
def code_prompt(state: dict) -> dict:
    story.scene("ACT V — THE CODE")
    story.say("For a heartbeat the world is not brick — it is falling green symbols.")
    oracle = character_speak("oracle",
        "Hint that Neo can see the code if he chooses belief — one cryptic sentence.",
    )
    story.speak_as("Oracle (echo)", oracle)
    story.say("The simulation waits for your choice…")
    return {
        "dialogue": [f"Oracle: {oracle}"],
        "events": ["code:prompted"],
        "log": ["[code] prompted"],
    }


@aware_node
def code_choice(state: dict) -> dict:
    choice = interrupt(
        {
            "kind": "code",
            "message": "Accept the code vision (accept) or deny it (deny).",
        }
    )
    decision = str(choice).strip().lower()
    if decision not in {"accept", "deny"}:
        decision = "accept"

    story.scene("CODE CHOICE")
    story.say(f"Operator chose: {decision}")

    score = int(state.get("training_score") or 0)
    if decision == "accept":
        score += 3
        neo = character_speak("neo",
            "You see Agents as code. One awed first-person sentence.",
        )
        rules = list(state.get("physics_rules") or [])
        if "code_sight" not in rules:
            rules.append("code_sight")
    else:
        neo = character_speak("neo",
            "You blink the code away. One doubtful sentence.",
        )
        rules = list(state.get("physics_rules") or [])

    story.speak_as("Neo", neo)
    return {
        "code_choice": decision,
        "training_score": score,
        "physics_rules": rules,
        "dialogue": [f"Neo: {neo}"],
        "events": [f"code:{decision}"],
        "log": [f"[code] {decision}"],
    }


@aware_node
def zion_arrival(state: dict) -> dict:
    story.scene("ACT V — ZION SIGNAL")
    story.say("Docking clamps. Warm air. A city buried near the Earth's core.")
    tank = character_speak("tank",
        (
            f"Welcome Neo after code={state.get('code_choice')} "
            f"showdown={state.get('showdown_status')}. One hopeful sentence."
        ),
    )
    story.speak_as("Tank", tank)
    morpheus = character_speak("morpheus",
        "Tell Neo his journey is only beginning — one profound sentence.",
    )
    story.speak_as("Morpheus", morpheus)
    return {
        "location": "real_world",
        "dialogue": [f"Tank: {tank}", f"Morpheus: {morpheus}"],
        "events": ["zion:signal"],
        "log": ["[zion] signal"],
        "locations_visited": ["real_world"],
    }
