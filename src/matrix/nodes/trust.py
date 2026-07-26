"""Trust Trinity — HITL before Morpheus briefing."""

from typing import Literal

from langgraph.types import Command, interrupt

from matrix import story
from matrix.awareness import aware_node
from matrix.llm import character_speak


@aware_node
def trust_prompt(state: dict) -> dict:
    story.scene("ACT I — TRUST?")
    story.say("Rain on the car roof. Trinity waits for your answer.")
    trinity = character_speak("trinity",
        "Ask Neo to trust you and meet Morpheus — one terse sentence.",
    )
    story.speak_as("Trinity", trinity)
    story.say("The simulation waits for your choice…")
    return {
        "dialogue": [f"Trinity: {trinity}"],
        "events": ["trust:prompted"],
        "log": ["[trust] prompted"],
    }


def trust_choice(
    state: dict,
) -> Command[Literal["morpheus_briefing", "early_doubt"]]:
    choice = interrupt(
        {
            "kind": "trust",
            "message": "Trust Trinity (trust) or walk away (walk).",
        }
    )
    decision = str(choice).strip().lower()
    if decision not in {"trust", "walk"}:
        decision = "trust"

    story.scene("TRUST CHOICE")
    story.say(f"Operator chose: {decision}")

    if decision == "trust":
        return Command(
            update={
                "trust_choice": "trust",
                "events": ["trust:yes"],
                "log": ["[trust] yes"],
            },
            goto="morpheus_briefing",
        )

    return Command(
        update={
            "trust_choice": "walk",
            "threat_level": min(10, int(state.get("threat_level") or 4) + 2),
            "events": ["trust:walk"],
            "log": ["[trust] walk"],
        },
        goto="early_doubt",
    )


@aware_node
def morpheus_briefing(state: dict) -> dict:
    story.scene("ACT I — MORPHEUS BRIEFING")
    story.say("A chair. Leather. Lightning in the sky outside.")
    morpheus = character_speak("morpheus",
        (
            "Brief Neo about the Matrix as a prison for the mind "
            "in two short profound sentences."
        ),
    )
    story.speak_as("Morpheus", morpheus)
    return {
        "briefing": morpheus,
        "scene": "briefing",
        "dialogue": [f"Morpheus: {morpheus}"],
        "events": ["briefing:morpheus"],
        "log": ["[briefing] morpheus"],
    }


@aware_node
def early_doubt(state: dict) -> dict:
    story.scene("ACT I — DOUBT")
    story.say("You almost walk back into the crowd. A whisper finds you anyway.")
    cypher = character_speak("cypher",
        "Tempt Neo to ignore Trinity and keep the comfortable lie — one sentence.",
    )
    story.speak_as("Cypher (whisper)", cypher)
    neo = character_speak("neo",
        "You refused Trinity at first but curiosity still burns. One sentence.",
    )
    story.speak_as("Neo", neo)
    return {
        "scene": "doubt",
        "dialogue": [f"Cypher: {cypher}", f"Neo: {neo}"],
        "events": ["doubt:cypher"],
        "log": ["[doubt] cypher"],
        "threat_level": int(state.get("threat_level") or 4),
    }
