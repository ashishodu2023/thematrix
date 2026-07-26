"""Mid-ship drama — Cypher temptation, sentinel scan, battery farm vision."""

from typing import Literal

from langgraph.types import Command, interrupt

from matrix import story
from matrix.awareness import aware_node
from matrix.llm import character_speak
from matrix.world import LOCATIONS


@aware_node
def battery_farm(state: dict) -> dict:
    loc = LOCATIONS["real_world"]
    story.scene("ACT III — THE FARM")
    story.say(f"{loc.name}: towers of pods. Lightning. Harvested bodies.")
    morpheus = character_speak("morpheus",
        "Show Neo humanity as batteries. One devastating sentence.",
    )
    story.speak_as("Morpheus", morpheus)
    neo = character_speak("neo",
        "You see the farm. One nauseated first-person sentence.",
    )
    story.speak_as("Neo", neo)
    return {
        "location": loc.id,
        "scene": "farm",
        "dialogue": [f"Morpheus: {morpheus}", f"Neo: {neo}"],
        "events": ["farm:vision"],
        "log": ["[farm] vision"],
        "locations_visited": [loc.id],
    }


@aware_node
def crew_dinner(state: dict) -> dict:
    loc = LOCATIONS["nebuchadnezzar"]
    story.scene("ACT III — CREW MESS")
    story.say(f"{loc.name}: protein goo. Jokes that try too hard.")
    tank = character_speak("tank",
        "Keep the crew mood light about the food in one warm sentence.",
    )
    story.speak_as("Tank", tank)
    cypher = character_speak("cypher",
        "Sneer about missing steak and the Matrix illusion in one bitter sentence.",
    )
    story.speak_as("Cypher", cypher)
    return {
        "location": loc.id,
        "dialogue": [f"Tank: {tank}", f"Cypher: {cypher}"],
        "events": ["mess:dinner"],
        "log": ["[mess] dinner"],
        "locations_visited": [loc.id],
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
    tank = character_speak("tank",
        "Sentinels are scanning. Whisper one urgent stay-quiet sentence.",
    )
    story.speak_as("Tank", tank)
    return {
        "dialogue": [f"Tank: {tank}"],
        "events": ["sentinel:scan"],
        "log": ["[sentinel] scan"],
        "sentinel_alert": True,
    }
