"""Act 0 — white rabbit, office, interrogation, bug."""

from typing import Literal

from langgraph.types import Command, interrupt

from matrix import story
from matrix.awareness import aware_node
from matrix.llm import character_speak
from matrix.world import LOCATIONS


@aware_node
def white_rabbit(state: dict) -> dict:
    loc = LOCATIONS["apartment"]
    story.scene("ACT 0 — FOLLOW THE WHITE RABBIT")
    story.say(f"{loc.name}: knock at the door. Party people. A tattoo.")
    story.say("On a woman's shoulder: a white rabbit.")

    neo = character_speak("neo",
        "Strangers invite you to a club because of a rabbit tattoo. One hesitant sentence.",
    )
    story.speak_as("Neo", neo)
    return {
        "location": loc.id,
        "scene": "rabbit",
        "dialogue": [f"Neo: {neo}"],
        "events": ["act0:rabbit"],
        "log": ["[rabbit] follow"],
        "locations_visited": [loc.id],
    }


@aware_node
def office_cube(state: dict) -> dict:
    story.scene("ACT 0 — META CORTECKS")
    story.say("Cubicle farm. Deadlines. A FedEx envelope that should not exist.")
    story.say("Inside: a Nokia brick phone. It rings once.")

    neo = character_speak("neo",
        "Your boss threatens you while a mysterious phone rings. One stressed sentence.",
    )
    story.speak_as("Neo", neo)

    morpheus = character_speak("morpheus",
        "On the phone, guide Neo out of the office past Agents in one calm sentence.",
    )
    story.speak_as("Morpheus (phone)", morpheus)

    return {
        "scene": "office",
        "dialogue": [f"Neo: {neo}", f"Morpheus: {morpheus}"],
        "events": ["act0:office"],
        "log": ["[office] phone"],
    }


@aware_node
def interrogation(state: dict) -> dict:
    story.scene("ACT 0 — INTERROGATION")
    story.say("Green-tinted room. Mirror. Agents who do not blink.")

    smith = character_speak("smith",
        "Interrogate Neo about Morpheus. One contemptuous sentence ending in Mr. Anderson.",
    )
    story.speak_as("Agent Smith", smith)

    neo = character_speak("neo",
        "Agents have you. Demand a phone call or lawyer in one stubborn sentence.",
    )
    story.speak_as("Neo", neo)

    story.say("Smith places a robotic bug against your belly. It burrows.")
    return {
        "scene": "interrogation",
        "dialogue": [f"Agent Smith: {smith}", f"Neo: {neo}"],
        "events": ["act0:interrogation"],
        "log": ["[interrogation] bug"],
        "bug_implanted": True,
    }


@aware_node
def bug_prompt(state: dict) -> dict:
    loc = LOCATIONS["club"]
    story.scene("ACT 0 — THE BUG")
    story.say("Later. A car. Trinity holds a device that looks like a medical nightmare.")
    trinity = character_speak("trinity",
        "Tell Neo you must extract the tracking bug now — one terse sentence.",
    )
    story.speak_as("Trinity", trinity)
    story.say("The simulation waits for your choice…")
    return {
        "location": loc.id,
        "dialogue": [f"Trinity: {trinity}"],
        "events": ["bug:prompted"],
        "log": ["[bug] prompted"],
        "locations_visited": [loc.id],
    }


def bug_choice(
    state: dict,
) -> Command[Literal["dream_glitch", "bug_refuse"]]:
    choice = interrupt(
        {
            "kind": "bug",
            "message": "Let Trinity extract the bug (extract) or refuse (refuse).",
        }
    )
    decision = str(choice).strip().lower()
    if decision not in {"extract", "refuse"}:
        decision = "extract"

    story.scene("BUG CHOICE")
    story.say(f"Operator chose: {decision}")

    if decision == "extract":
        story.say("The bug tears free — metal legs still twitching.")
        return Command(
            update={
                "bug_choice": "extract",
                "bug_implanted": False,
                "events": ["bug:extracted"],
                "log": ["[bug] extracted"],
            },
            goto="dream_glitch",
        )

    return Command(
        update={
            "bug_choice": "refuse",
            "threat_level": min(10, int(state.get("threat_level") or 4) + 3),
            "events": ["bug:refused"],
            "log": ["[bug] refused"],
        },
        goto="bug_refuse",
    )


@aware_node
def bug_refuse(state: dict) -> dict:
    story.scene("ACT 0 — TRACKED")
    story.say("You keep the bug. Agents already know your vector.")
    smith = character_speak("smith",
        "Neo refused extraction. Promise the hunt in one sentence.",
    )
    story.speak_as("Agent Smith", smith)
    return {
        "dialogue": [f"Agent Smith: {smith}"],
        "events": ["bug:still_tracked"],
        "log": ["[bug] tracked"],
    }
