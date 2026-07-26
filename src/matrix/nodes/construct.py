"""Construct training subgraph nodes."""

from matrix import story
from matrix.world import LOCATIONS


def load_skills(state: dict) -> dict:
    loc = LOCATIONS["construct"]
    skills = ["kung_fu", "jujitsu", "weapons_training"]
    story.scene("THE CONSTRUCT")
    story.say(f"{loc.name}: {loc.description}")
    story.say(f"Tank loads: {', '.join(skills)}")
    return {
        "location": loc.id,
        "scene": "construct",
        "training_skills": skills,
        "events": ["construct:load"],
        "log": [f"[construct] loaded {skills}"],
        "locations_visited": [loc.id],
    }


def spar(state: dict) -> dict:
    skills = state.get("training_skills") or []
    # Simple score: number of skills loaded (belief already helps outside).
    base = len(skills)
    bonus = 1 if state.get("reality_rewritten") else 0
    score = base + bonus
    story.say(f"Sparring complete. Training score = {score}")
    return {
        "training_score": score,
        "events": [f"construct:spar:{score}"],
        "log": [f"[construct] score={score}"],
    }


def score_training(state: dict) -> dict:
    story.beat(f"Construct ready — score {state.get('training_score', 0)}")
    return {
        "events": ["construct:ready"],
        "log": ["[construct] ready"],
    }
