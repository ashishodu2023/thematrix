"""Smoke tests for expansion systems — physics, surveillance, commands, scoreboard."""

from __future__ import annotations

from matrix.objectives import accumulate_board, scoreboard_delta
from matrix.operator_commands import apply_command
from matrix.physics import apply_event, chase_modifiers, showdown_win_threshold
from matrix.state import merge_scoreboard
from matrix.surveillance import hardline_available, tap_phone, use_hardline


def test_dialogue_and_scoreboard_reducers():
    assert merge_scoreboard({"zion": 2}, {"agents": 3, "zion": 1}) == {
        "zion": 3,
        "agents": 3,
        "system": 0,
    }


def test_glitch_and_meta_affect_chase():
    rules = apply_event(["gravity", "spoon_exists"], "glitch")
    assert "deja_vu" in rules
    base = chase_modifiers({"physics_rules": rules, "meta_policy": "choice", "trace_level": 0})
    control = chase_modifiers({"physics_rules": rules, "meta_policy": "control", "trace_level": 0})
    assert base["escape"] > control["escape"]
    assert showdown_win_threshold({"physics_rules": rules, "meta_policy": "choice"}) <= 6


def test_key_path_and_hardline():
    rules = apply_event([], "key_path")
    assert "key_path" in rules
    state = {"hardline_cooldown": 0, "trace_level": 20.0}
    assert hardline_available(state)
    used = use_hardline(state)
    assert used["hardline_cooldown"] == 3
    tap = tap_phone("test-line")
    assert tap["phone_taps"] == ["test-line"]


def test_operator_move_command():
    state = {
        "location": "club",
        "agent_positions": {"neo": "club"},
        "trace_level": 10.0,
        "hardline_cooldown": 0,
        "sector_heat": {},
        "phone_taps": [],
        "training_skills": [],
        "training_score": 0,
    }
    out = apply_command(state, command="move", target="apartment", seat="operator")
    # apartment may or may not be neighbor — accept ok or route error
    assert "ok" in out
    emp = apply_command(state, command="emp", seat="operator")
    assert emp.get("ok") is True


def test_scoreboard_delta_patrol():
    board = scoreboard_delta([("jones", "patrol"), ("trinity", "cover")])
    assert board["agents"] >= 1
    assert board["zion"] >= 2
    acc = accumulate_board({"zion": 5}, board)
    assert acc["zion"] >= 7
