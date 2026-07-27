"""Mid-ship drama — Cypher temptation, sentinel scan, battery farm vision."""

from typing import Literal

from langgraph.types import Command, interrupt

from matrix import story
from matrix.awareness import aware_node
from matrix.llm import character_speak
from matrix.parallel import speak_many
from matrix.world import LOCATIONS


@aware_node
def battery_farm(state: dict) -> dict:
    loc = LOCATIONS["real_world"]
    story.scene("ACT III — THE FARM")
    story.say(f"{loc.name}: towers of pods. Lightning. Harvested bodies.")
    lines = speak_many(
        [
            (
                "morpheus",
                "Show Neo humanity as batteries. One devastating sentence.",
            ),
            (
                "neo",
                "You see the farm. One nauseated first-person sentence.",
            ),
        ],
        state=state,
    )
    morpheus, neo = lines["morpheus"], lines["neo"]
    story.speak_as("Morpheus", morpheus)
    story.speak_as("Neo", neo)
    return {
        "location": loc.id,
        "scene": "farm",
        "dialogue": [f"Morpheus: {morpheus}", f"Neo: {neo}"],
        "events": ["farm:vision"],
        "log": ["[farm] vision"],
        "locations_visited": [loc.id],
        "active_tracks": ["neo:farm"],
    }


@aware_node
def crew_dinner(state: dict) -> dict:
    loc = LOCATIONS["nebuchadnezzar"]
    story.scene("ACT III — CREW MESS")
    story.say(f"{loc.name}: protein goo. Jokes that try too hard.")
    lines = speak_many(
        [
            (
                "tank",
                "Keep the crew mood light about the food in one warm sentence.",
            ),
            (
                "cypher",
                "Sneer about missing steak and the Matrix illusion in one bitter sentence.",
            ),
        ],
        state=state,
    )
    tank, cypher = lines["tank"], lines["cypher"]
    story.speak_as("Tank", tank)
    story.speak_as("Cypher", cypher)
    return {
        "location": loc.id,
        "scene": "dinner",
        "dialogue": [f"Tank: {tank}", f"Cypher: {cypher}"],
        "events": ["dinner:goo"],
        "log": ["[dinner] mess"],
        "locations_visited": [loc.id],
        "active_tracks": ["neo:dinner"],
    }


@aware_node
def steak_prompt(state: dict) -> dict:
    story.scene("ACT III — THE STEAK")
    story.say("Later. Alone with Cypher. He paints a picture of a juicy steak.")
    cypher = character_speak("cypher",
        "Tempt Neo to wish he never woke up — steak, ignorance, comfort — one sentence.",
    )
    story.speak_as("Cypher", cypher)
    story.say("The simulation waits for your choice…")
    return {
        "dialogue": [f"Cypher: {cypher}"],
        "events": ["steak:prompted"],
        "log": ["[steak] prompted"],
    }


def steak_choice(
    state: dict,
) -> Command[Literal["sentinel_scan", "steak_regret"]]:
    choice = interrupt(
        {
            "kind": "steak",
            "message": "Refuse the lie (refuse) or crave the steak illusion (steak).",
        }
    )
    decision = str(choice).strip().lower()
    if decision not in {"steak", "refuse"}:
        decision = "refuse"

    story.scene("STEAK CHOICE")
    story.say(f"Operator chose: {decision}")

    if decision == "refuse":
        return Command(
            update={
                "steak_choice": "refuse",
                "events": ["steak:refused"],
                "log": ["[steak] refuse"],
            },
            goto="sentinel_scan",
        )

    return Command(
        update={
            "steak_choice": "steak",
            "threat_level": min(10, int(state.get("threat_level") or 4) + 1),
            "events": ["steak:craved"],
            "log": ["[steak] crave"],
        },
        goto="steak_regret",
    )


@aware_node
def steak_regret(state: dict) -> dict:
    story.scene("ACT III — DOUBT ON THE SHIP")
    cypher = character_speak("cypher",
        "Neo almost wants the steak. Mock his weakness in one sentence.",
    )
    story.speak_as("Cypher", cypher)
    neo = character_speak("neo",
        "You admitted craving the lie. One ashamed sentence.",
    )
    story.speak_as("Neo", neo)
    return {
        "dialogue": [f"Cypher: {cypher}", f"Neo: {neo}"],
        "events": ["steak:doubt"],
        "log": ["[steak] doubt"],
    }


@aware_node
def sentinel_scan(state: dict) -> dict:
    story.scene("ACT III — SENTINELS")
    story.say("EMP charged. Squiddies scrape the hull. Everyone holds breath.")
    emp_patch: dict = {}
    try:
        from matrix.emp_game import apply_to_ship_state

        emp_patch = apply_to_ship_state(state)
        heat = emp_patch.get("emp_heat")
        if emp_patch.get("ship_destroyed"):
            story.beat("EMP BOARD: hull breached — ship destroyed")
        elif heat is not None:
            story.beat(f"EMP BOARD: heat={float(heat):.0f} charges={emp_patch.get('emp_charges')}")
    except Exception:  # noqa: BLE001
        emp_patch = {}
    hint = ""
    if emp_patch.get("ship_destroyed"):
        hint = " The hull is already cracking — whisper panic."
    elif emp_patch.get("sticky_flags", {}).get("hull_critical"):
        hint = " Hull is critical — one breath from scrap."
    tank = character_speak(
        "tank",
        "Sentinels are scanning. Whisper one urgent stay-quiet sentence." + hint,
    )
    story.speak_as("Tank", tank)
    sticky = dict(state.get("sticky_flags") or {})
    sticky.update(emp_patch.get("sticky_flags") or {})
    return {
        "dialogue": [f"Tank: {tank}"],
        "events": ["sentinel:scan"] + list(emp_patch.get("events") or []),
        "log": ["[sentinel] scan"] + list(emp_patch.get("log") or []),
        "sentinel_alert": emp_patch.get("sentinel_alert", True),
        "sticky_flags": sticky,
        "ship_destroyed": bool(emp_patch.get("ship_destroyed")),
        "emp_heat": emp_patch.get("emp_heat"),
        "emp_charges": emp_patch.get("emp_charges"),
    }
