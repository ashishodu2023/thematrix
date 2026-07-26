"""Construct training subgraph — multi-step programs."""

from matrix import story
from matrix.awareness import aware_node
from matrix.llm import character_speak
from matrix.world import LOCATIONS


@aware_node
def load_skills(state: dict) -> dict:
    loc = LOCATIONS["construct"]
    skills = ["kung_fu", "jujitsu", "weapons_training"]
    story.scene("ACT III — THE CONSTRUCT")
    story.say(f"{loc.name}: {loc.description}")
    tank = character_speak("tank",
        f"Load {', '.join(skills)} into Neo — one excited sentence.",
    )
    story.speak_as("Tank", tank)
    story.say(f"Tank loads: {', '.join(skills)}")
    return {
        "location": loc.id,
        "scene": "construct",
        "training_skills": skills,
        "dialogue": [f"Tank: {tank}"],
        "events": ["construct:load"],
        "log": [f"[construct] loaded {skills}"],
        "locations_visited": [loc.id],
    }


@aware_node
def spar_morpheus(state: dict) -> dict:
    story.scene("CONSTRUCT — SPAR WITH MORPHEUS")
    story.say("Dojo. Wooden floor. Morpheus circles.")
    morpheus = character_speak("morpheus",
        "During a dojo spar, urge Neo to stop trying to hit you and hit you — one sentence.",
    )
    neo = character_speak("neo",
        "You are sparring Morpheus and losing. One strained sentence.",
    )
    story.speak_as("Morpheus", morpheus)
    story.speak_as("Neo", neo)
    score = int(state.get("training_score") or 0) + 2
    return {
        "training_score": score,
        "dialogue": [f"Morpheus: {morpheus}", f"Neo: {neo}"],
        "events": [f"construct:spar_morpheus:{score}"],
        "log": [f"[construct] spar_morpheus score={score}"],
    }


@aware_node
def spar_agent_sim(state: dict) -> dict:
    story.scene("CONSTRUCT — AGENT SIM")
    story.say("A simulated Agent materializes. Rules are optional here.")
    smith = character_speak("smith",
        "You are a training sim of Smith. Challenge Neo in one sentence.",
    )
    neo = character_speak("neo",
        f"Training score so far={state.get('training_score', 0)}. "
        "Face a simulated Agent — one determined sentence.",
    )
    story.speak_as("Agent Smith (sim)", smith)
    story.speak_as("Neo", neo)
    bonus = 1 if state.get("reality_rewritten") else 0
    score = int(state.get("training_score") or 0) + 2 + bonus
    skills = list(state.get("training_skills") or [])
    if "agent_sim" not in skills:
        skills.append("agent_sim")
    return {
        "training_skills": skills,
        "training_score": score,
        "dialogue": [f"Agent Smith: {smith}", f"Neo: {neo}"],
        "events": [f"construct:agent_sim:{score}"],
        "log": [f"[construct] agent_sim score={score}"],
    }


def score_training(state: dict) -> dict:
    score = int(state.get("training_score") or 0)
    story.beat(f"Construct block complete — score {score}")
    story.say(f"Skills: {', '.join(state.get('training_skills') or [])}")
    return {
        "events": ["construct:ready"],
        "log": [f"[construct] ready score={score}"],
    }
