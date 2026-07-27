from matrix.city_graph import shortest_path, step_toward
from matrix.objectives import resolve_conflict
from matrix.physics import apply_event, chase_modifiers, showdown_win_threshold
from matrix.minds import MindStore
from matrix.surveillance import bump_trace, hardline_available


def test_city_pathfinding():
    path = shortest_path("apartment", "subway")
    assert path[0] == "apartment"
    assert path[-1] == "subway"
    assert step_toward("hotel_lobby", "rooftop") == "rooftop"


def test_physics_bend_and_chase():
    rules = apply_event(
        ["gravity", "solidity", "causality", "spoon_exists"], "bend_spoon"
    )
    assert "spoon_exists" not in rules
    assert "belief_over_rules" in rules
    mods = chase_modifiers(
        {
            "physics_rules": rules,
            "reality_rewritten": True,
            "bug_implanted": False,
            "sticky_flags": {},
            "trace_level": 0,
        }
    )
    assert mods["escape"] > 0


def test_showdown_threshold_code_sight():
    assert showdown_win_threshold({"physics_rules": ["code_sight"]}) < 6


def test_mind_store_memory():
    MindStore.remember("smith", "Neo escaped subway", neo_location="subway")
    d = MindStore.dossier("smith")
    assert "Neo escaped" in d or "subway" in d


def test_conflict_resolution():
    result = resolve_conflict(
        [("trinity", "extract"), ("neo", "follow_trinity")],
        [("smith", "hold")],
    )
    assert result.winner in {"zion", "agents", "draw"}
    assert "zion" in result.scoreboard


def test_trace_bump():
    patch = bump_trace({"trace_level": 10}, 5, "test")
    assert patch["trace_level"] == 15
    assert hardline_available({"hardline_cooldown": 0})
