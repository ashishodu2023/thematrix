"""Expansion suite — director, season, timeline, open-city, RAG embed, EMP."""

from __future__ import annotations

from matrix import director, emp_game, season, timeline
from matrix.lc_tools import langchain_tools, tool_calls_to_raw
from matrix.metrics import collect_metrics
from matrix.rag import embed, retrieve
from matrix.routing import (
    BRANCH_GRAPH,
    open_city_enabled,
    route_after_cafe,
    route_after_keymaker,
    route_after_lobby,
    route_after_merovingian,
    route_after_wander,
)


def test_director_pause_force_inject(tmp_path, monkeypatch):
    monkeypatch.setattr(director, "_DIR_FILE", tmp_path / "dir.json")
    assert director.set_paused(True)["paused"] is True
    assert director.peek_force_branch() == ""
    director.force_branch("city_wander")
    assert director.peek_force_branch() == "city_wander"
    assert director.consume_force_branch() == "city_wander"
    assert director.peek_force_branch() == ""
    director.inject("glitch", "test")
    items = director.pop_injects()
    assert len(items) == 1
    assert items[0]["event"] == "glitch"


def test_season_arcs(tmp_path, monkeypatch):
    monkeypatch.setattr(season, "_FILE", tmp_path / "season.json")
    season.set_arc("smith_infection")
    out = season.advance_from_life({"outcome": "Smith catches Neo", "sticky_flags": {}})
    assert out["arc"] == "smith_infection"
    assert out["progress"] >= 1
    assert "infection" in season.prompt_flavor().lower() or "smith" in season.prompt_flavor().lower()


def test_timeline_record(tmp_path, monkeypatch):
    monkeypatch.setattr(timeline, "_FILE", tmp_path / "tl.json")
    timeline.clear()
    timeline.record(kind="pill", choice="red", why="console")
    rows = timeline.list_timeline()
    assert rows[-1]["choice"] == "red"


def test_open_city_branch_graph():
    assert open_city_enabled()
    assert "club_hel_fight" in BRANCH_GRAPH
    assert "burly_brawl" in BRANCH_GRAPH
    assert route_after_cafe({"previous_lives": 1, "wander_hops": 0}, commit=False) in {
        "merovingian_vip",
        "city_wander",
        "club_hel_fight",
    }
    assert route_after_merovingian({"sticky_flags": {"persephone_kiss": True}}, commit=False) == "club_hel_fight"
    assert route_after_keymaker({"key_choice": "refuse_key"}, commit=False) == "city_wander"
    assert route_after_lobby({"sticky_flags": {"burly_brawl": True}}, commit=False) == "pursuit_loop"


def test_director_force_commit(tmp_path, monkeypatch):
    monkeypatch.setattr(director, "_DIR_FILE", tmp_path / "dir2.json")
    director.force_branch("highway_chase")
    assert route_after_keymaker({}, commit=False) == "highway_chase"
    assert director.peek_force_branch() == "highway_chase"
    assert route_after_keymaker({}, commit=True) == "highway_chase"
    assert director.peek_force_branch() == ""


def test_embedding_rag_smoke():
    a = embed("Agent Smith hunts Neo on the highway")
    b = embed("Smith highway pursuit of Neo")
    c = embed("cookies and prophecy in the kitchen")
    assert len(a) == len(b) == 128
    # similar docs should score higher than unrelated
    from matrix.rag import _cosine_vec

    assert _cosine_vec(a, b) > _cosine_vec(a, c)


def test_lc_tools_catalog():
    tools = langchain_tools("agent")
    assert {t.name for t in tools} >= {"scan", "detect", "tap"}
    raw = tool_calls_to_raw([{"name": "scan", "args": {"sector": "highway"}}])
    assert "TOOL: scan(highway)" in raw


def test_emp_game(tmp_path, monkeypatch):
    monkeypatch.setattr(emp_game, "_FILE", tmp_path / "emp.json")
    emp_game.reset()
    before = emp_game.status()["heat"]
    out = emp_game.pulse()
    assert out["ok"] is True
    assert out["heat"] < before
    assert out["charges"] == 2


def test_metrics_analytics_shape():
    m = collect_metrics("neo")
    assert "analytics" in m
    assert "ending_buckets" in m["analytics"]
    assert "branch_frequencies" in m["analytics"]


def test_wander_route_can_loop():
    nxt = route_after_wander(
        {"location": "cafe", "wander_hops": 0, "trace_level": 10},
        commit=False,
    )
    assert nxt == "city_wander"
