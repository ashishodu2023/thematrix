"""Backward-compatible import path: `from matrix.graph import get_graph`."""

from matrix.graphs.main import build_graph, get_graph, reset_graph_cache

__all__ = ["build_graph", "get_graph", "reset_graph_cache"]
