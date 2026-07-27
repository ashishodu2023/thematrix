"""Main Matrix control plane — expanded multi-act cinematic graph."""

from langgraph.graph import END, START, StateGraph

from matrix.graphs.construct import construct_graph
from matrix.nodes.act0 import (
    bug_choice,
    bug_prompt,
    bug_refuse,
    interrogation,
    office_cube,
    white_rabbit,
)
from matrix.nodes.architect import architect
from matrix.nodes.awaken import (
    combat_beat,
    epilogue,
    jump_choice,
    jump_offer,
    post_jump_training,
    radio_choice,
    radio_prompt,
    ship_awaken,
)
from matrix.nodes.cafe import cafe_scene
from matrix.nodes.dream import dream_glitch, meet_trinity
from matrix.nodes.finale import (
    code_choice,
    code_prompt,
    phone_booth,
    subway_showdown,
    zion_arrival,
)
from matrix.nodes.kernel import simulation_kernel
from matrix.nodes.lobby import lobby_breach
from matrix.nodes.operator import operator_persist
from matrix.nodes.oracle import oracle_question, oracle_speak
from matrix.meta_game import meta_negotiate
from matrix.awareness import live_node
from matrix.nodes.expanded import (
    highway_chase,
    keymaker_doors,
    merovingian_vip,
    sentinel_hunt,
    zion_dock,
)
from matrix.nodes.wander import city_wander
from matrix.nodes.reloaded import burly_brawl, club_hel_fight
from matrix.routing import (
    route_after_cafe,
    route_after_keymaker,
    route_after_lobby,
    route_after_merovingian,
    route_after_wander,
)
from matrix.nodes.field import (
    field_pulse_a,
    field_pulse_b,
    field_pulse_c,
    field_pulse_d,
    field_pulse_e,
)
from matrix.nodes.pill import (
    blue_ending,
    fight_or_flee,
    morpheus_offer,
    pill_choice,
    resolve_choice,
    trinity_warn,
)
from matrix.nodes.pursuit import pursuit_loop
from matrix.nodes.reality import bend_reality, enforce_reality
from matrix.nodes.ship_life import (
    battery_farm,
    crew_dinner,
    sentinel_scan,
    steak_choice,
    steak_prompt,
    steak_regret,
)
from matrix.nodes.swarm import (
    agent_worker,
    dispatch_agents,
    prepare_swarm,
    reconcile,
    route_reality,
)
from matrix.nodes.trust import (
    early_doubt,
    morpheus_briefing,
    trust_choice,
    trust_prompt,
)
from matrix.services.memory import build_checkpointer
from matrix.state import MatrixState


def build_graph():
    """
    Act 0: rabbit → office → interrogation → bug HITL
    Act I: dream → trinity → trust HITL → briefing
    Act II: architect → oracle → cafe → swarm → lobby → pursuit → pills
    Act III: ship → farm → dinner → steak HITL → sentinel → construct → jump
    Act IV: fight → combat → radio → showdown loop → hardline
    Act V: code HITL → zion → resolve → epilogue → persist
    """
    builder = StateGraph(MatrixState)
    _raw_add = builder.add_node

    def add_node(name, action, **kwargs):  # noqa: ANN001
        """Every node pushes live Operator Console updates."""
        return _raw_add(name, live_node(action), **kwargs)

    builder.add_node = add_node  # type: ignore[method-assign]

    # Act 0
    builder.add_node("simulation_kernel", simulation_kernel)
    builder.add_node("meta_layer", meta_negotiate)
    builder.add_node("white_rabbit", white_rabbit)
    builder.add_node("office_cube", office_cube)
    builder.add_node("interrogation", interrogation)
    builder.add_node("bug_prompt", bug_prompt)
    builder.add_node("bug_choice", bug_choice)
    builder.add_node("bug_refuse", bug_refuse)

    # Act I
    builder.add_node("dream_glitch", dream_glitch)
    builder.add_node("meet_trinity", meet_trinity)
    builder.add_node("trust_prompt", trust_prompt)
    builder.add_node("trust_choice", trust_choice)
    builder.add_node("morpheus_briefing", morpheus_briefing)
    builder.add_node("early_doubt", early_doubt)
    builder.add_node("architect", architect)

    # Act II
    builder.add_node("oracle_question", oracle_question)
    builder.add_node("oracle_speak", oracle_speak)
    builder.add_node("cafe_scene", cafe_scene)
    builder.add_node("prepare_swarm", prepare_swarm)
    builder.add_node("agent_worker", agent_worker)
    builder.add_node("reconcile", reconcile)
    builder.add_node("bend_reality", bend_reality)
    builder.add_node("enforce_reality", enforce_reality)
    builder.add_node("lobby_breach", lobby_breach)
    builder.add_node("pursuit_loop", pursuit_loop)
    builder.add_node("morpheus_offer", morpheus_offer)
    builder.add_node("pill_choice", pill_choice)
    builder.add_node("blue_ending", blue_ending)

    # Act III
    builder.add_node("ship_awaken", ship_awaken)
    builder.add_node("battery_farm", battery_farm)
    builder.add_node("crew_dinner", crew_dinner)
    builder.add_node("steak_prompt", steak_prompt)
    builder.add_node("steak_choice", steak_choice)
    builder.add_node("steak_regret", steak_regret)
    builder.add_node("sentinel_scan", sentinel_scan)
    builder.add_node("construct_training", construct_graph)
    builder.add_node("jump_offer", jump_offer)
    builder.add_node("jump_choice", jump_choice)
    builder.add_node("post_jump_training", post_jump_training)

    # Act IV / V
    builder.add_node("trinity_warn", trinity_warn)
    builder.add_node("fight_or_flee", fight_or_flee)
    builder.add_node("combat_beat", combat_beat)
    builder.add_node("radio_prompt", radio_prompt)
    builder.add_node("radio_choice", radio_choice)
    builder.add_node("subway_showdown", subway_showdown)
    builder.add_node("phone_booth", phone_booth)
    builder.add_node("code_prompt", code_prompt)
    builder.add_node("code_choice", code_choice)
    builder.add_node("zion_arrival", zion_arrival)
    builder.add_node("resolve_choice", resolve_choice)
    builder.add_node("epilogue", epilogue)
    builder.add_node("operator_persist", operator_persist)

    # Parallel Agent field tracks (fan-out beside Neo's story)
    builder.add_node("field_pulse_a", field_pulse_a)
    builder.add_node("field_pulse_b", field_pulse_b)
    builder.add_node("field_pulse_c", field_pulse_c)
    builder.add_node("field_pulse_d", field_pulse_d)
    builder.add_node("field_pulse_e", field_pulse_e)
    builder.add_node("merovingian_vip", merovingian_vip)
    builder.add_node("keymaker_doors", keymaker_doors)
    builder.add_node("city_wander", city_wander)
    builder.add_node("highway_chase", highway_chase)
    builder.add_node("club_hel_fight", club_hel_fight)
    builder.add_node("burly_brawl", burly_brawl)
    builder.add_node("sentinel_hunt", sentinel_hunt)
    builder.add_node("zion_dock", zion_dock)

    # --- Edges ---
    builder.add_edge(START, "simulation_kernel")
    builder.add_edge("simulation_kernel", "meta_layer")

    # Act 0: Neo rabbit ∥ Agent field → join at office (wait for BOTH)
    builder.add_edge("meta_layer", "white_rabbit")
    builder.add_edge("meta_layer", "field_pulse_a")
    builder.add_edge(["white_rabbit", "field_pulse_a"], "office_cube")

    # Act 0: interrogation ∥ Agents → join at bug_prompt
    builder.add_edge("office_cube", "interrogation")
    builder.add_edge("office_cube", "field_pulse_b")
    builder.add_edge(["interrogation", "field_pulse_b"], "bug_prompt")

    builder.add_edge("bug_prompt", "bug_choice")
    # bug_choice Command → dream_glitch | bug_refuse
    builder.add_edge("bug_refuse", "dream_glitch")

    # Act I: meet_trinity ∥ Agents → join at trust_prompt
    builder.add_edge("dream_glitch", "meet_trinity")
    builder.add_edge("dream_glitch", "field_pulse_c")
    builder.add_edge(["meet_trinity", "field_pulse_c"], "trust_prompt")

    builder.add_edge("trust_prompt", "trust_choice")
    builder.add_edge("morpheus_briefing", "architect")
    builder.add_edge("early_doubt", "architect")

    builder.add_edge("oracle_question", "oracle_speak")
    builder.add_edge("oracle_speak", "cafe_scene")

    # Expanded Act II — open-city forks (Cafe → Merovingian/Wander/Club Hel → Keymaker…)
    builder.add_conditional_edges(
        "cafe_scene",
        route_after_cafe,
        {
            "merovingian_vip": "merovingian_vip",
            "city_wander": "city_wander",
            "club_hel_fight": "club_hel_fight",
        },
    )
    builder.add_conditional_edges(
        "merovingian_vip",
        route_after_merovingian,
        {
            "club_hel_fight": "club_hel_fight",
            "keymaker_doors": "keymaker_doors",
        },
    )
    builder.add_edge("club_hel_fight", "keymaker_doors")
    builder.add_conditional_edges(
        "keymaker_doors",
        route_after_keymaker,
        {
            "highway_chase": "highway_chase",
            "city_wander": "city_wander",
            "prepare_swarm": "prepare_swarm",
        },
    )
    builder.add_conditional_edges(
        "city_wander",
        route_after_wander,
        {
            "highway_chase": "highway_chase",
            "prepare_swarm": "prepare_swarm",
            "merovingian_vip": "merovingian_vip",
            "city_wander": "city_wander",
            "club_hel_fight": "club_hel_fight",
        },
    )
    # Highway ∥ field pulse → single prepare_swarm (was double-invoking → CYCLE ERROR)
    builder.add_edge("highway_chase", "field_pulse_d")
    builder.add_edge(["highway_chase", "field_pulse_d"], "prepare_swarm")

    builder.add_conditional_edges(
        "prepare_swarm",
        dispatch_agents,
        ["agent_worker"],
    )
    builder.add_edge("agent_worker", "reconcile")
    builder.add_conditional_edges(
        "reconcile",
        route_reality,
        {
            "bend_reality": "bend_reality",
            "enforce_reality": "enforce_reality",
        },
    )
    builder.add_edge("bend_reality", "lobby_breach")
    builder.add_edge("enforce_reality", "lobby_breach")
    builder.add_conditional_edges(
        "lobby_breach",
        route_after_lobby,
        {
            "burly_brawl": "burly_brawl",
            "pursuit_loop": "pursuit_loop",
        },
    )
    builder.add_edge("burly_brawl", "pursuit_loop")
    builder.add_edge("morpheus_offer", "pill_choice")

    builder.add_edge("blue_ending", "epilogue")

    # Red path — ship life
    builder.add_edge("ship_awaken", "battery_farm")
    builder.add_edge("battery_farm", "crew_dinner")
    builder.add_edge("crew_dinner", "steak_prompt")
    builder.add_edge("steak_prompt", "steak_choice")
    builder.add_edge("steak_regret", "sentinel_scan")
    builder.add_edge("sentinel_scan", "sentinel_hunt")
    builder.add_edge("sentinel_hunt", "construct_training")
    builder.add_edge("construct_training", "jump_offer")
    builder.add_edge("jump_offer", "jump_choice")
    builder.add_edge("jump_choice", "post_jump_training")
    builder.add_edge("post_jump_training", "trinity_warn")
    builder.add_edge("trinity_warn", "fight_or_flee")

    # Act IV: fight ∥ Agents → join combat once
    builder.add_edge("fight_or_flee", "field_pulse_e")
    builder.add_edge(["fight_or_flee", "field_pulse_e"], "combat_beat")

    builder.add_edge("combat_beat", "radio_prompt")
    builder.add_edge("radio_prompt", "radio_choice")
    builder.add_edge("radio_choice", "subway_showdown")
    # subway_showdown Command loop → phone_booth
    builder.add_edge("phone_booth", "code_prompt")
    builder.add_edge("code_prompt", "code_choice")
    builder.add_edge("code_choice", "zion_arrival")
    builder.add_edge("zion_arrival", "zion_dock")
    builder.add_edge("zion_dock", "resolve_choice")
    builder.add_edge("resolve_choice", "epilogue")
    builder.add_edge("epilogue", "operator_persist")
    builder.add_edge("operator_persist", END)

    return builder.compile(checkpointer=build_checkpointer())


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def reset_graph_cache() -> None:
    global _graph
    _graph = None
