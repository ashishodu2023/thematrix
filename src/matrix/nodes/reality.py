from matrix import story
from matrix.tools.agent_tools import rewrite_local


def bend_reality(state: dict) -> dict:
    rules = [r for r in state["physics_rules"] if r != "spoon_exists"]
    if "belief_over_form" not in rules:
        rules.append("belief_over_form")

    story.scene("THERE IS NO SPOON")
    story.say("Local physics rewritten.")
    story.say("Removed: spoon_exists | Added: belief_over_form")
    return {
        "physics_rules": rules,
        "spoon_exists": False,
        "reality_rewritten": True,
        "scene": "reality",
        "events": ["reality:bent"],
        "log": ["[bend] belief_over_form"],
    }


def enforce_reality(state: dict) -> dict:
    rewrite = rewrite_local("Smith", state["city"])
    story.scene("ENFORCE REALITY")
    story.say("Agents stabilize the simulation.")
    story.say(rewrite)
    return {
        "reality_rewritten": False,
        "spoon_exists": True,
        "scene": "reality",
        "events": ["reality:enforced"],
        "log": [f"[enforce] {rewrite}"],
    }
