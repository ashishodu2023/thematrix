"""Lobby breach — competing Zion vs Agent objectives + world tick."""

from matrix import story
from matrix import sound as matrix_sound
from matrix.config import config
from matrix.objectives import accumulate_board, resolve_conflict
from matrix.parallel import act_many, merge_patches
from matrix.surveillance import tap_phone
from matrix.tick import world_tick
from matrix.world import LOCATIONS


def lobby_breach(state: dict) -> dict:
    loc = LOCATIONS["hotel_lobby"]
    story.scene("ACT II — LOBBY BREACH")
    story.say(f"{loc.name}: {loc.description}")
    story.say("Security freezes. Magazines drop. Pillars become cover.")
    matrix_sound.play("agent")

    live = {**state, "location": loc.id}
    tick_patches: dict = {}
    for _ in range(max(1, config.world_ticks_per_scene)):
        tp = world_tick(live, neo_target=loc.id)
        tick_patches.update(tp)
        live = {**live, **tp}

    # Trinity + Smith decide at the same time (parallel brains)
    first = act_many(
        [
            (
                "trinity",
                ["cover", "advance", "extract"],
                (
                    f"Reality rewritten={state.get('reality_rewritten')} "
                    f"trace={live.get('trace_level')}. "
                    "Lobby breach — choose your independent combat action."
                ),
            ),
            (
                "smith",
                ["suppress", "flank", "taunt"],
                "Agents arrive mid-breach. Choose your independent response to the anomaly.",
            ),
        ],
        state=live,
    )
    trinity_d, trinity_p = first["trinity"]
    smith_d, smith_p = first["smith"]
    story.speak_as("Trinity", trinity_d.speech)
    story.speak_as("Agent Smith", smith_d.speech)

    dialogue = [
        f"Trinity: {trinity_d.speech}",
        f"Agent Smith: {smith_d.speech}",
    ]
    live = {
        **live,
        "dialogue": list(live.get("dialogue") or []) + dialogue,
        "agent_memory": list(live.get("agent_memory") or [])
        + list(trinity_p.get("agent_memory") or [])
        + list(smith_p.get("agent_memory") or []),
        "character_actions": list(live.get("character_actions") or [])
        + list(trinity_p.get("character_actions") or [])
        + list(smith_p.get("character_actions") or []),
    }

    neo_actions = ["dodge", "follow_trinity", "freeze"]
    if (state.get("co_human_id") or "").lower() in {"trinity", "tank", "morpheus"}:
        neo_actions = ["follow_trinity", "dodge", "freeze"]

    neo_batch = act_many(
        [
            (
                "neo",
                neo_actions,
                (
                    f"Trinity action={trinity_d.action}. Smith action={smith_d.action}. "
                    f"Co-pilot={state.get('co_human_id') or 'none'}. "
                    "Firefight — choose independently."
                ),
            )
        ],
        state=live,
    )
    neo_d, neo_p = neo_batch["neo"]
    story.speak_as("Neo", neo_d.speech)
    dialogue.append(f"Neo: {neo_d.speech}")

    patches = merge_patches([trinity_p, smith_p, neo_p])
    conflict = resolve_conflict(
        [("trinity", trinity_d.action), ("neo", neo_d.action)],
        [("smith", smith_d.action)],
    )
    story.beat(conflict.narration)

    return {
        "location": loc.id,
        "scene": "lobby",
        "dialogue": dialogue,
        "events": [
            f"lobby:breach:{trinity_d.action}:{smith_d.action}:{neo_d.action}",
            f"lobby:conflict:{conflict.winner}",
        ],
        "log": [
            f"[lobby] t={trinity_d.action} s={smith_d.action} n={neo_d.action} "
            f"winner={conflict.winner}"
        ],
        "locations_visited": [loc.id],
        "faction_scoreboard": accumulate_board(
            state.get("faction_scoreboard"), conflict.scoreboard
        ),
        "active_tracks": ["neo:lobby", "agents:lobby"],
        "phone_taps": (tap_phone(f"lobby radio @ {loc.id}").get("phone_taps") or []),
        **tick_patches,
        **patches,
    }
