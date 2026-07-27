"""Tests for RAG, tools, routing, multiplayer."""

from __future__ import annotations

from matrix.multiplayer import clear_votes, record_vote
from matrix.rag import retrieve
from matrix.routing import route_after_keymaker, route_after_wander
from matrix.tool_runtime import parse_tool_calls, run_tools, tool_scan


def test_rag_retrieve_smoke():
    hits = retrieve("Agent Smith hunting Neo", human_id="neo", k=3)
    assert isinstance(hits, list)


def test_parse_and_run_tools():
    raw = "ACTION: hunt\nSAY: Found him.\nLEARN: Neo flees.\nTOOL: scan(highway)\n"
    assert parse_tool_calls(raw) == [("scan", "highway")]
    state = {"location": "highway", "city": "Mega City", "current_agent": "smith", "trace_level": 1}
    patch = run_tools(state, raw)
    assert any("scan" in str(x) for x in patch.get("tool_results") or [])
    assert patch.get("sectors_scanned") == ["highway"]
    alone = tool_scan(state, "subway")
    assert "subway" in alone["sectors_scanned"][0] or alone["sectors_scanned"] == ["subway"]


def test_open_world_routing():
    assert route_after_keymaker({"key_choice": "take_key", "sticky_flags": {}}) == "highway_chase"
    assert route_after_keymaker({"key_choice": "refuse_key", "sticky_flags": {}}) == "city_wander"
    assert route_after_keymaker({"location": "hotel_lobby"}) == "prepare_swarm"
    assert route_after_wander({"location": "highway"}) == "highway_chase"
    # Open-city: low-trace cafe can loop wander before swarm
    assert route_after_wander({"location": "cafe", "wander_hops": 0, "trace_level": 10}) == "city_wander"
    assert route_after_wander({"location": "cafe", "wander_hops": 2, "trace_level": 10}) == "prepare_swarm"


def test_branch_snapshot_live():
    from matrix.routing import branch_snapshot

    snap = branch_snapshot(
        {
            "scene": "keymaker",
            "key_choice": "take_key",
            "sticky_flags": {"took_key": True},
            "location": "keymaker_hall",
            "events": ["act2:keymaker:take_key"],
        }
    )
    assert snap["current"] == "keymaker_doors"
    assert snap["predicted"] == "highway_chase"
    assert snap["fork_active"] is True
    assert any(n["id"] == "highway_chase" for n in snap["nodes"])


def test_multi_seat_votes():
    clear_votes("fight_or_flee")
    mid = record_vote("fight_or_flee", "neo", "fight")
    assert mid.get("ready") is False or mid.get("mode") == "operator_fallback"
    # With only one vote and dual required + seats not both online, may need operator
    clear_votes("fight_or_flee")
    op = record_vote("fight_or_flee", "operator", "flee")
    assert op.get("ready") is True
    assert op.get("choice") == "flee"
