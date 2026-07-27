"""Deeper Reloaded set pieces — Club Hel, Burly Brawl."""

from __future__ import annotations

from matrix import story
from matrix.awareness import aware_node, use_state
from matrix.llm import character_act
from matrix.minds import MindStore
from matrix.objectives import scoreboard_delta
from matrix.parallel import speak_many
from matrix.physics import apply_event
from matrix.season import phase_event_tag, prompt_flavor
from matrix.surveillance import bump_trace
from matrix.timeline import record
from matrix.world import LOCATIONS


@aware_node
def club_hel_fight(state: dict) -> dict:
    loc = LOCATIONS.get("club_vip") or LOCATIONS["club"]
    story.scene("ACT II — CLUB HEL")
    story.say(f"{loc.name}: twin ghosts, silver blades, Merovingian's court.")
    flavor = prompt_flavor()
    with use_state(state):
        neo_d, neo_p = character_act(
            "neo",
            ["fight", "kiss", "bargain", "flee"],
            (
                f"{flavor} Club Hel — Twins draw blades. Persephone offers a kiss of memory. "
                "Merovingian watches. Choose fight, kiss, bargain, or flee."
            ),
            state=state,
            tools="agent",
        )
        twin_d, twin_p = character_act(
            "merovingian",
            ["observe", "unleash_twins", "detain"],
            (
                f"Neo chose {neo_d.action} in Club Hel. "
                "Choose observe, unleash_twins, or detain."
            ),
            state=state,
        )
    lines = speak_many(
        [
            (
                "persephone",
                "Grant Neo a kiss of memory before the twins strike — one intimate sentence.",
            ),
            (
                "trinity",
                "Fight through Club Hel — one terse combat sentence.",
            ),
        ],
        state=state,
    )
    story.speak_as("Persephone", lines["persephone"])
    story.speak_as("Trinity", lines["trinity"])
    story.speak_as("Neo", neo_d.speech)
    story.speak_as("Merovingian", twin_d.speech)

    sticky = dict(state.get("sticky_flags") or {})
    sticky["club_hel"] = True
    action = neo_d.action
    if action == "kiss":
        sticky["persephone_kiss"] = True
        MindStore.remember("persephone", "kissed Neo in Club Hel", neo_location=loc.id)
        branch = "kiss"
    elif action == "bargain":
        sticky["club_bargain"] = True
        MindStore.remember("merovingian", "Neo bargained in Club Hel", neo_location=loc.id)
        branch = "bargain"
    elif action == "flee":
        sticky["club_fled"] = True
        branch = "flee"
    else:
        sticky["persephone_kiss"] = True
        sticky["club_fought"] = True
        branch = "fight"

    if twin_d.action == "unleash_twins":
        sticky["twins_unleashed"] = True
    elif twin_d.action == "detain":
        sticky["club_detained"] = True

    record(
        kind="club_hel_tree",
        choice=action,
        why=f"merovingian={twin_d.action}",
        scene="club_hel",
        meta={"branch": branch},
    )
    MindStore.remember("persephone", f"Club Hel branch={branch}", neo_location=loc.id)
    board = scoreboard_delta(
        [
            ("neo", "dodge" if action == "flee" else "fight"),
            ("trinity", "cover"),
            ("merovingian", twin_d.action if twin_d.action in {"observe", "detain"} else "observe"),
        ]
    )
    heat = 6.0 if action != "flee" else 9.0
    if twin_d.action == "unleash_twins":
        heat += 4.0
    trace = bump_trace(state, heat, "club_hel")
    season_ev = phase_event_tag()
    events = ["act2:club_hel", f"act2:club_hel:{branch}"]
    if season_ev:
        events.append(season_ev)
    story.beat(f"BRANCH club_hel → {branch} / host={twin_d.action}")
    return {
        "location": loc.id,
        "scene": "club_hel",
        "sticky_flags": sticky,
        "dialogue": [
            f"Persephone: {lines['persephone']}",
            f"Trinity: {lines['trinity']}",
            f"Neo: {neo_d.speech}",
            f"Merovingian: {twin_d.speech}",
        ],
        "events": events,
        "log": [f"[club_hel] {branch}/{twin_d.action}"],
        "locations_visited": [loc.id],
        "active_tracks": ["neo:club_hel"],
        "faction_scoreboard": board,
        "trace_level": trace.get("trace_level", state.get("trace_level")),
        "character_actions": list(neo_p.get("character_actions") or [])
        + list(twin_p.get("character_actions") or []),
        "agent_memory": list(neo_p.get("agent_memory") or [])
        + list(twin_p.get("agent_memory") or []),
        "agent_positions": {
            **(state.get("agent_positions") or {}),
            "neo": loc.id,
            "trinity": loc.id,
            "persephone": loc.id,
            "merovingian": loc.id,
        },
    }


@aware_node
def burly_brawl(state: dict) -> dict:
    loc = LOCATIONS.get("hotel_lobby") or list(LOCATIONS.values())[0]
    story.scene("ACT II — BURLY BRAWL")
    story.say("A hundred Agent Smiths. Rain. Concrete. The anomaly multiplies.")
    flavor = prompt_flavor()
    with use_state(state):
        neo_d, neo_p = character_act(
            "neo",
            ["fight", "flee", "believe", "fly"],
            (
                f"{flavor} Burly Brawl — Smith copies swarm. "
                f"score={state.get('training_score')}. "
                "Choose fight, flee, believe (see the code), or fly (superjump)."
            ),
            state=state,
            tools="agent",
        )
        smith_d, smith_p = character_act(
            "smith",
            ["swarm", "taunt", "assimilate"],
            (
                f"Neo chose {neo_d.action} in the Burly Brawl. "
                "As the swarm, choose swarm, taunt, or assimilate."
            ),
            state=state,
            tools="agent",
        )
    lines = speak_many(
        [
            (
                "oracle",
                "Remote whisper about choice during the brawl — one cryptic sentence.",
            ),
        ],
        state=state,
    )
    story.speak_as("Agent Smith (×100)", smith_d.speech)
    story.speak_as("Neo", neo_d.speech)
    story.speak_as("Oracle", lines["oracle"])

    sticky = dict(state.get("sticky_flags") or {})
    sticky["burly_brawl"] = True
    rules = list(state.get("physics_rules") or [])
    if neo_d.action == "believe":
        rules = apply_event(rules, "code_sight")
        sticky["saw_code"] = True
    elif neo_d.action == "fly":
        rules = apply_event(rules, "code_sight")
        sticky["saw_code"] = True
        sticky["burly_flew"] = True
    if smith_d.action == "assimilate":
        sticky["smith_assimilate_push"] = True

    record(
        kind="burly_tree",
        choice=neo_d.action,
        why=f"smith={smith_d.action}",
        scene="burly_brawl",
    )
    MindStore.remember(
        "smith",
        f"burly brawl — Neo={neo_d.action} Smith={smith_d.action}",
        neo_location=loc.id,
    )
    board = scoreboard_delta(
        [
            (
                "neo",
                neo_d.action
                if neo_d.action in {"fight", "flee", "believe", "fly"}
                else "dodge",
            ),
            ("smith", "close_in"),
        ]
    )
    heat = 12.0
    if neo_d.action == "fight":
        heat = 14.0
    elif neo_d.action == "flee":
        heat = 10.0
    elif neo_d.action == "fly":
        heat = 8.0
    if smith_d.action == "assimilate":
        heat += 3.0
    trace = bump_trace(state, heat, "burly_brawl")
    season_ev = phase_event_tag()
    events = [f"act2:burly_brawl:{neo_d.action}", f"act2:burly_smith:{smith_d.action}"]
    if season_ev:
        events.append(season_ev)
    story.beat(f"BRANCH burly_brawl → {neo_d.action} vs {smith_d.action}")
    return {
        "location": loc.id,
        "scene": "burly_brawl",
        "sticky_flags": sticky,
        "physics_rules": rules,
        "fight_choice": neo_d.action
        if neo_d.action in {"fight", "flee"}
        else state.get("fight_choice"),
        "dialogue": [
            f"Agent Smith: {smith_d.speech}",
            f"Neo: {neo_d.speech}",
            f"Oracle: {lines['oracle']}",
        ],
        "events": events,
        "log": [f"[burly_brawl] {neo_d.action}/{smith_d.action}"],
        "locations_visited": [loc.id],
        "active_tracks": ["neo:burly_brawl", "agents:swarm"],
        "faction_scoreboard": board,
        "trace_level": trace.get("trace_level", state.get("trace_level")),
        "character_actions": list(neo_p.get("character_actions") or [])
        + list(smith_p.get("character_actions") or []),
        "agent_memory": list(neo_p.get("agent_memory") or [])
        + list(smith_p.get("agent_memory") or []),
        "agent_positions": {
            **(state.get("agent_positions") or {}),
            "neo": loc.id,
            "smith": loc.id,
            "jones": loc.id,
            "brown": loc.id,
        },
    }
