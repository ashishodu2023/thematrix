"""Lobby breach — extraction firefight; each fighter acts independently."""

from matrix import story
from matrix.awareness import use_state
from matrix.llm import character_act
from matrix.world import LOCATIONS


def lobby_breach(state: dict) -> dict:
    loc = LOCATIONS["hotel_lobby"]
    story.scene("ACT II — LOBBY BREACH")
    story.say(f"{loc.name}: {loc.description}")
    story.say("Security freezes. Magazines drop. Pillars become cover.")

    patches: dict = {"agent_memory": [], "character_actions": []}
    dialogue: list[str] = []
    live = dict(state)

    with use_state(live):
        trinity_d, trinity_p = character_act(
            "trinity",
            ["cover", "advance", "extract"],
            (
                f"Reality rewritten={state.get('reality_rewritten')}. "
                "Lobby breach — choose your independent combat action."
            ),
            state=live,
        )
    story.speak_as("Trinity", trinity_d.speech)
    dialogue.append(f"Trinity: {trinity_d.speech}")
    for k, v in trinity_p.items():
        patches[k] = list(patches.get(k) or []) + list(v)
    live = {
        **live,
        "dialogue": list(live.get("dialogue") or []) + dialogue[-1:],
        "agent_memory": list(live.get("agent_memory") or [])
        + list(trinity_p.get("agent_memory") or []),
        "character_actions": list(live.get("character_actions") or [])
        + list(trinity_p.get("character_actions") or []),
    }

    with use_state(live):
        smith_d, smith_p = character_act(
            "smith",
            ["suppress", "flank", "taunt"],
            "Agents arrive mid-breach. Choose your independent response to the anomaly.",
            state=live,
        )
    story.speak_as("Agent Smith", smith_d.speech)
    dialogue.append(f"Agent Smith: {smith_d.speech}")
    for k, v in smith_p.items():
        patches[k] = list(patches.get(k) or []) + list(v)
    live = {
        **live,
        "dialogue": list(live.get("dialogue") or []) + dialogue[-1:],
        "agent_memory": list(live.get("agent_memory") or [])
        + list(smith_p.get("agent_memory") or []),
        "character_actions": list(live.get("character_actions") or [])
        + list(smith_p.get("character_actions") or []),
    }

    with use_state(live):
        neo_d, neo_p = character_act(
            "neo",
            ["dodge", "follow_trinity", "freeze"],
            (
                f"Trinity action={trinity_d.action}. Smith action={smith_d.action}. "
                "Firefight you barely understand — choose independently."
            ),
            state=live,
        )
    story.speak_as("Neo", neo_d.speech)
    dialogue.append(f"Neo: {neo_d.speech}")
    for k, v in neo_p.items():
        patches[k] = list(patches.get(k) or []) + list(v)

    return {
        "location": loc.id,
        "scene": "lobby",
        "dialogue": dialogue,
        "events": [
            f"lobby:breach:{trinity_d.action}:{smith_d.action}:{neo_d.action}"
        ],
        "log": [
            f"[lobby] t={trinity_d.action} s={smith_d.action} n={neo_d.action}"
        ],
        "locations_visited": [loc.id],
        **patches,
    }
