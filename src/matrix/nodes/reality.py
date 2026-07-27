from matrix import story
from matrix import sound as matrix_sound
from matrix.physics import apply_event
from matrix.tools.agent_tools import rewrite_local


def bend_reality(state: dict) -> dict:
    rules = apply_event(list(state.get("physics_rules") or []), "bend_spoon")
    matrix_sound.play("glitch")
    story.scene("THERE IS NO SPOON")
    story.say("Local physics rewritten.")
    story.say(f"Rules now: {', '.join(rules)}")
    return {
        "physics_rules": rules,
        "spoon_exists": False,
        "reality_rewritten": True,
        "scene": "reality",
        "events": ["reality:bent"],
        "log": ["[bend] belief_over_rules"],
    }


def enforce_reality(state: dict) -> dict:
    rules = apply_event(list(state.get("physics_rules") or []), "enforce")
    rewrite = rewrite_local("Smith", state["city"])
    story.scene("ENFORCE REALITY")
    story.say("Agents stabilize the simulation.")
    story.say(rewrite)
    return {
        "physics_rules": rules,
        "reality_rewritten": False,
        "spoon_exists": True,
        "scene": "reality",
        "events": ["reality:enforced"],
        "log": [f"[enforce] {rewrite}"],
    }
