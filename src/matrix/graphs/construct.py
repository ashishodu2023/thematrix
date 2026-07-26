"""Construct training — nested StateGraph used as a node in the main graph."""

from langgraph.graph import END, START, StateGraph

from matrix.nodes.construct import (
    load_skills,
    score_training,
    spar_agent_sim,
    spar_morpheus,
)
from matrix.state import MatrixState


def build_construct_graph():
    builder = StateGraph(MatrixState)
    builder.add_node("load_skills", load_skills)
    builder.add_node("spar_morpheus", spar_morpheus)
    builder.add_node("spar_agent_sim", spar_agent_sim)
    builder.add_node("score_training", score_training)

    builder.add_edge(START, "load_skills")
    builder.add_edge("load_skills", "spar_morpheus")
    builder.add_edge("spar_morpheus", "spar_agent_sim")
    builder.add_edge("spar_agent_sim", "score_training")
    builder.add_edge("score_training", END)
    return builder.compile()


construct_graph = build_construct_graph()
