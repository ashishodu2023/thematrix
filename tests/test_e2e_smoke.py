"""End-to-end smoke — mocked LLMs, full graph compile + HITL bridge + replay."""

from __future__ import annotations

from matrix.awareness import CharacterDecision
from matrix.hitl_bridge import clear_pending, publish_pending, submit_choice, wait_for_choice
from matrix.presets import PRESETS, apply_preset
from matrix.replay import list_replays, save_life
from matrix.metrics import collect_metrics


def test_graph_compiles_with_expanded_nodes():
    from matrix.graphs.main import build_graph, reset_graph_cache

    reset_graph_cache()
    g = build_graph()
    nodes = set(g.get_graph().nodes)
    for n in (
        "merovingian_vip",
        "keymaker_doors",
        "sentinel_hunt",
        "zion_dock",
        "field_pulse_a",
    ):
        assert n in nodes


def test_hitl_bridge_roundtrip(tmp_path, monkeypatch):
    import matrix.hitl_bridge as hb

    monkeypatch.setattr(hb, "_HITL_PENDING", tmp_path / "p.json")
    monkeypatch.setattr(hb, "_HITL_CHOICE", tmp_path / "c.json")
    publish_pending(thread_id="t1", kind="pill", message="choose")
    submit_choice("red", thread_id="t1", seat="neo")
    assert wait_for_choice("t1", timeout=0.5) == "red"
    clear_pending()


def test_replay_and_metrics(monkeypatch):
    from pathlib import Path
    import matrix.replay as rp

    monkeypatch.setattr(rp, "_REPLAY_DIR", Path("/tmp/matrix-replays-test"))
    path = save_life(
        {
            "cycle": 9,
            "outcome": "red pill win",
            "awakened": True,
            "pill_choice": "red",
            "location": "zion_dock",
            "dialogue": ["Neo: I know kung fu."],
            "faction_scoreboard": {"zion": 3, "agents": 1},
            "agent_positions": {"neo": "zion_dock"},
        },
        feed=["══ TEST ══", 'Neo: "I know kung fu."'],
    )
    assert path.exists()
    assert list_replays(limit=5)
    m = collect_metrics("neo")
    assert "lives_recorded" in m
    assert m["replays_saved"] >= 1


def test_presets_apply(monkeypatch):
    name = apply_preset("tiny")
    assert name == "tiny"
    assert "tiny" in PRESETS
    apply_preset("balanced")


def test_expanded_scene_units(monkeypatch):
    monkeypatch.setattr(
        "matrix.nodes.expanded.speak_many",
        lambda jobs, state=None: {who: f"{who}-line" for who, _ in jobs},
    )
    from matrix.nodes.expanded import keymaker_doors, merovingian_vip, zion_dock

    state = {"agent_positions": {}, "previous_lives": 0}
    assert merovingian_vip(state)["location"] == "club_vip"
    assert keymaker_doors(state)["location"] == "keymaker_hall"
    assert zion_dock(state)["location"] == "zion_dock"
