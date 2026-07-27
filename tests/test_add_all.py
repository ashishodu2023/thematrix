"""Tests for lobby, agency, season beats, EMP→ship, episode export."""

from __future__ import annotations

from pathlib import Path

from matrix import agency, emp_game, lobby, season
from matrix.episode import export_episode, list_episodes
from matrix.rag import embedding_backend, hash_embed, retrieve
from matrix.replay import save_life


def test_lobby_create_join_leave(tmp_path, monkeypatch):
    monkeypatch.setattr(lobby, "_FILE", tmp_path / "lobby.json")
    monkeypatch.setattr(agency, "_AGENCY_FILE", tmp_path / "agency.json")
    st = lobby.create(host="operator")
    assert st["code"]
    code = st["code"]
    joined = lobby.join(code, "neo", name="Ash")
    assert joined["ok"] is True
    assert "neo" in joined["seats"]
    bad = lobby.join("XXXXXX", "trinity", name="T")
    assert bad["ok"] is False
    lobby.leave("neo")
    assert "neo" not in lobby.status()["seats"]


def test_agency_queue_and_merge(tmp_path, monkeypatch):
    monkeypatch.setattr(agency, "_AGENCY_FILE", tmp_path / "agency.json")
    monkeypatch.setenv("MATRIX_TRUE_MP", "1")
    q = agency.queue_intent("neo", "linger")
    assert q["ok"] is True
    state = {
        "location": "hotel_lobby",
        "agent_positions": {"neo": "hotel_lobby"},
        "trace_level": 10,
        "sticky_flags": {},
        "events": [],
        "log": [],
    }
    agency.merge_agency_into(state)
    assert state.get("sticky_flags", {}).get("agency_neo") == "linger"
    assert any("agency:neo" in str(e) for e in state.get("events") or [])


def test_season_phase_beats(tmp_path, monkeypatch):
    monkeypatch.setattr(season, "_FILE", tmp_path / "season.json")
    out = season.set_arc("smith_infection")
    assert out["arc"] == "smith_infection"
    assert out["beat"]
    flavor = season.prompt_flavor()
    assert "smith_infection" in flavor
    assert "Current beat" in flavor
    advanced = season.advance_from_life(
        {"outcome": "Agent Smith wins", "sticky_flags": {"bug_implanted": True}}
    )
    assert advanced["progress"] >= 1
    assert advanced["phase"] >= 0


def test_emp_ship_coupling(tmp_path, monkeypatch):
    monkeypatch.setattr(emp_game, "_FILE", tmp_path / "emp.json")
    emp_game.reset()
    # Force destroy
    data = emp_game.status()
    data["heat"] = 100
    data["alive"] = False
    emp_game._save(data)  # noqa: SLF001
    patch = emp_game.apply_to_ship_state({"sentinel_alert": True, "sticky_flags": {}})
    assert patch.get("ship_destroyed") is True
    assert patch.get("sticky_flags", {}).get("ship_destroyed") is True

    emp_game.reset()
    pulsed = emp_game.pulse()
    assert pulsed.get("ok") is True
    cool = emp_game.apply_to_ship_state({"sentinel_alert": True, "sticky_flags": {}})
    assert cool.get("ship_destroyed") is not True


def test_episode_export(tmp_path, monkeypatch):
    from matrix import episode, replay

    monkeypatch.setattr(replay, "_REPLAY_DIR", tmp_path / "replays")
    monkeypatch.setattr(episode, "_EP_DIR", tmp_path / "episodes")
    path = save_life(
        {
            "cycle": 99,
            "outcome": "awakened",
            "awakened": True,
            "pill_choice": "red",
            "dialogue": ["Neo: I know kung fu.", "Morpheus: Show me."],
            "events": ["══ ACT I ══", "pill:red"],
            "locations_visited": ["jack_point", "construct"],
        },
        feed=["══ ACT I ══", "Neo: I know kung fu.", "Morpheus: Show me."],
    )
    out = export_episode(path.name)
    assert out["ok"] is True
    assert Path(out["html_path"]).exists()
    assert Path(out["script_path"]).exists()
    assert list_episodes()


def test_rag_hash_and_backend():
    v = hash_embed("Agent Smith hunts Neo in the lobby")
    assert len(v) == 128
    assert abs(sum(x * x for x in v) - 1.0) < 1e-5
    backend = embedding_backend()
    assert backend in {"hash", "token_cosine"} or backend.startswith("ollama:")
    hits = retrieve("Agent Smith", human_id="neo", k=2)
    assert isinstance(hits, list)
