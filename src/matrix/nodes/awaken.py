"""Ship awakening, jump program HITL, combat beat, Zion radio, epilogue."""

from typing import Literal

from langgraph.types import Command, interrupt

from matrix import story
from matrix.awareness import aware_node
from matrix.llm import character_speak
from matrix.world import LOCATIONS


@aware_node
def ship_awaken(state: dict) -> dict:
    loc = LOCATIONS["nebuchadnezzar"]
    story.scene("ACT III — DESERT OF THE REAL")
    story.say(f"{loc.name}: {loc.description}")
    story.say("Fluid. Needles. Ribs aching. The sky is not a sky.")

    tank = character_speak("tank",
        "Welcome Neo aboard after the red pill in one warm urgent sentence.",
    )
    story.speak_as("Tank", tank)

    morpheus = character_speak("morpheus",
        "Welcome Neo to the real world in one profound sentence.",
    )
    story.speak_as("Morpheus", morpheus)

    return {
        "location": loc.id,
        "scene": "awaken",
        "dialogue": [f"Tank: {tank}", f"Morpheus: {morpheus}"],
        "events": ["awaken:ship"],
        "log": ["[awaken] ship"],
        "locations_visited": [loc.id, "real_world"],
    }


@aware_node
def jump_offer(state: dict) -> dict:
    loc = LOCATIONS["construct"]
    story.scene("ACT III — JUMP PROGRAM")
    story.say(f"{loc.name}: two skyscrapers, impossible gap.")
    morpheus = character_speak("morpheus",
        "Invite Neo to jump between buildings — free the mind — one sentence.",
    )
    story.speak_as("Morpheus", morpheus)
    story.say("The simulation waits for your choice…")
    return {
        "location": loc.id,
        "dialogue": [f"Morpheus: {morpheus}"],
        "events": ["jump:offered"],
        "log": ["[jump] offered"],
        "locations_visited": [loc.id],
    }


@aware_node
def jump_choice(state: dict) -> dict:
    choice = interrupt(
        {
            "kind": "jump",
            "message": "Jump the gap (jump) or hesitate (hesitate).",
            "training_score": state.get("training_score", 0),
        }
    )
    decision = str(choice).strip().lower()
    if decision not in {"jump", "hesitate"}:
        decision = "hesitate"

    story.scene("JUMP CHOICE")
    story.say(f"Operator chose: {decision}")

    score = int(state.get("training_score") or 0)
    if decision == "jump":
        score += 2
        story.say("You clear the gap. Belief hardens.")
        neo = character_speak("neo",
            "You jumped and landed. One breathless first-person sentence.",
        )
    else:
        story.say("You fall. The Construct soft-catches you. Doubt remains.")
        neo = character_speak("neo",
            "You hesitated and fell. One frustrated first-person sentence.",
        )
    story.speak_as("Neo", neo)

    return {
        "jump_choice": decision,
        "training_score": score,
        "dialogue": [f"Neo: {neo}"],
        "events": [f"jump:{decision}"],
        "log": [f"[jump] {decision} score={score}"],
    }


@aware_node
def post_jump_training(state: dict) -> dict:
    story.scene("ACT III — MORE TRAINING")
    story.say("Tank loads weapons. Then hand-to-hand. Then still more.")
    tank = character_speak("tank",
        f"Current score={state.get('training_score', 0)}. "
        "Announce loading more combat programs in one sentence.",
    )
    story.speak_as("Tank", tank)
    skills = list(state.get("training_skills") or [])
    for skill in ("weapons_advanced", "aerial_combat", "agent_tactics"):
        if skill not in skills:
            skills.append(skill)
    score = int(state.get("training_score") or 0) + 2
    story.say(f"Programs loaded. Training score → {score}")
    return {
        "training_skills": skills,
        "training_score": score,
        "dialogue": [f"Tank: {tank}"],
        "events": ["training:advanced"],
        "log": [f"[training] score={score}"],
    }


@aware_node
def combat_beat(state: dict) -> dict:
    story.scene("ACT IV — CONFRONTATION")
    fight = state.get("fight_choice") or "flee"
    score = int(state.get("training_score") or 0)

    if fight == "fight":
        story.say("Subway station. Rain of bullets. Time bends.")
        smith = character_speak("smith",
            f"Neo fights you (score={score}). Snarl one hunting sentence.",
        )
        neo = character_speak("neo",
            f"You chose to fight Smith with score={score}. One defiant sentence.",
        )
    else:
        story.say("Hardline booth. Fingers bleeding on the receiver.")
        smith = character_speak("smith",
            "Neo flees. Promise you will find him again in one sentence.",
        )
        neo = character_speak("neo",
            "You flee to the hardline. One urgent sentence.",
        )

    story.speak_as("Agent Smith", smith)
    story.speak_as("Neo", neo)
    return {
        "location": "subway",
        "dialogue": [f"Agent Smith: {smith}", f"Neo: {neo}"],
        "events": [f"combat:{fight}"],
        "log": [f"[combat] {fight}"],
        "locations_visited": ["subway"],
    }


@aware_node
def radio_prompt(state: dict) -> dict:
    story.scene("ACT IV — ZION UPLINK")
    story.say("Static. The Operator channel crackles open.")
    tank = character_speak("tank",
        "Ask Neo to call for extraction now or stay silent — one sentence.",
    )
    story.speak_as("Tank", tank)
    story.say("The simulation waits for your choice…")
    return {
        "dialogue": [f"Tank: {tank}"],
        "events": ["radio:prompted"],
        "log": ["[radio] prompted"],
    }


def radio_choice(state: dict) -> dict:
    choice = interrupt(
        {
            "kind": "radio",
            "message": "Call Tank for extraction (call) or stay silent (silent).",
        }
    )
    decision = str(choice).strip().lower()
    if decision not in {"call", "silent"}:
        decision = "call"

    story.scene("RADIO CHOICE")
    story.say(f"Operator chose: {decision}")
    if decision == "call":
        story.say("Nebuchadnezzar locks your signal. Exit vector opening.")
    else:
        story.say("You stay dark. Sentinels sniff the line anyway.")

    return {
        "radio_choice": decision,
        "events": [f"radio:{decision}"],
        "log": [f"[radio] {decision}"],
    }


@aware_node
def epilogue(state: dict) -> dict:
    story.scene("EPILOGUE")
    pill = state.get("pill_choice") or "blue"
    if pill == "blue":
        story.say("Morning traffic. Same cubicle. The cat does not cross twice.")
        line = character_speak("neo",
            "You took the blue pill. One hollow sentence about going back to sleep.",
        )
    else:
        story.say("Phone booth. City grid humming. A voice that will wake the others.")
        line = character_speak("neo",
            (
                f"You fight={state.get('fight_choice')} radio={state.get('radio_choice')} "
                f"score={state.get('training_score')}. "
                "Deliver a short awakening manifesto sentence."
            ),
        )
    story.speak_as("Neo", line)
    return {
        "dialogue": [f"Neo: {line}"],
        "events": ["epilogue"],
        "log": ["[epilogue] done"],
    }
