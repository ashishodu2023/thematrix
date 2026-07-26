"""Main Matrix control plane."""

from langgraph.graph import END, START, StateGraph

from matrix.graphs.construct import construct_graph
from matrix.nodes.architect import architect
from matrix.nodes.cafe import cafe_scene
from matrix.nodes.operator import operator_persist
from matrix.nodes.oracle import oracle_question, oracle_speak
from matrix.nodes.pill import (
    blue_ending,
    fight_or_flee,
    pill_choice,
    resolve_choice,
)
from matrix.nodes.pursuit import pursuit_loop
from matrix.nodes.reality import bend_reality, enforce_reality
from matrix.nodes.kernel import simulation_kernel
from matrix.nodes.swarm import (
    agent_worker,
    dispatch_agents,
    prepare_swarm,
    reconcile,
    route_reality,
)
from matrix.services.memory import build_checkpointer
from matrix.state import MatrixState


def build_graph():
    """
    START → kernel → architect ──Command──┐
                                           │
                    oracle_question ───────┤
                    oracle_speak           │
                                           ▼
                                      cafe_scene
                                           │
                                    prepare_swarm ─Send×N→ agent_worker
                                           │
                                       reconcile
                                           │
                               bend_reality / enforce_reality
                                           │
                                      pursuit_loop ─Command loop─┐
                                           │                     │
                                      pill_choice ←──────────────┘
                                         │    │
                                   blue_ending construct_training
                                         │    │
                                         │  fight_or_flee
                                         │    │
                                         │  resolve_choice
                                         ▼    ▼
                                   operator_persist → END
    """
    builder = StateGraph(MatrixState)

    builder.add_node("simulation_kernel", simulation_kernel)
    builder.add_node("architect", architect)
    builder.add_node("oracle_question", oracle_question)
    builder.add_node("oracle_speak", oracle_speak)
    builder.add_node("cafe_scene", cafe_scene)
    builder.add_node("prepare_swarm", prepare_swarm)
    builder.add_node("agent_worker", agent_worker)
    builder.add_node("reconcile", reconcile)
    builder.add_node("bend_reality", bend_reality)
    builder.add_node("enforce_reality", enforce_reality)
    builder.add_node("pursuit_loop", pursuit_loop)
    builder.add_node("pill_choice", pill_choice)
    builder.add_node("blue_ending", blue_ending)
    builder.add_node("construct_training", construct_graph)
    builder.add_node("fight_or_flee", fight_or_flee)
    builder.add_node("resolve_choice", resolve_choice)
    builder.add_node("operator_persist", operator_persist)

    builder.add_edge(START, "simulation_kernel")
    builder.add_edge("simulation_kernel", "architect")
    builder.add_edge("oracle_question", "oracle_speak")
    builder.add_edge("oracle_speak", "cafe_scene")
    builder.add_edge("cafe_scene", "prepare_swarm")
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
    builder.add_edge("bend_reality", "pursuit_loop")
    builder.add_edge("enforce_reality", "pursuit_loop")
    builder.add_edge("blue_ending", "operator_persist")
    builder.add_edge("construct_training", "fight_or_flee")
    builder.add_edge("fight_or_flee", "resolve_choice")
    builder.add_edge("resolve_choice", "operator_persist")
    builder.add_edge("operator_persist", END)

    return builder.compile(checkpointer=build_checkpointer())


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
