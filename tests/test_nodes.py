from matrix.nodes.reality import bend_reality, enforce_reality
from matrix.nodes.swarm import route_reality
from matrix.tools.agent_tools import detect_anomaly, scan_sector


def _base(**overrides):
    state = {
        "human_id": "neo",
        "city": "Mega City",
        "cycle": 1,
        "location": "cafe",
        "scene": "cafe",
        "physics_rules": ["gravity", "solidity", "causality", "spoon_exists"],
        "anomaly": "spoon",
        "threat_level": 4,
        "architect_plan": "",
        "oracle_question": "",
        "oracle_prophecy": "",
        "agent_names": ["Smith", "Jones", "Brown"],
        "current_agent": "Smith",
        "agent_reports": [],
        "sectors_scanned": [],
        "spoon_exists": True,
        "reality_rewritten": False,
        "pursuit_round": 0,
        "pursuit_status": "idle",
        "pursuit_log": [],
        "pending_decision": "",
        "pill_choice": "",
        "fight_choice": "",
        "awakened": False,
        "training_skills": [],
        "training_score": 0,
        "dialogue": [],
        "events": [],
        "log": [],
        "outcome": "",
        "previous_lives": 0,
        "locations_visited": [],
    }
    state.update(overrides)
    return state


def test_detect_spoon():
    assert "spoon" in detect_anomaly("Smith", "spoon").lower()


def test_scan_sector():
    assert "Mega City" in scan_sector("Jones", "Mega City", "sector-j1")


def test_route_reality_bend():
    assert route_reality(_base(anomaly="spoon")) == "bend_reality"


def test_route_reality_enforce():
    assert (
        route_reality(_base(anomaly="none", agent_reports=["clear"]))
        == "enforce_reality"
    )


def test_bend_reality(monkeypatch):
    monkeypatch.setattr("matrix.story.scene", lambda *_a, **_k: None)
    monkeypatch.setattr("matrix.story.say", lambda *_a, **_k: None)
    result = bend_reality(_base())
    assert result["spoon_exists"] is False
    assert "belief_over_form" in result["physics_rules"]


def test_enforce_reality(monkeypatch):
    monkeypatch.setattr("matrix.story.scene", lambda *_a, **_k: None)
    monkeypatch.setattr("matrix.story.say", lambda *_a, **_k: None)
    result = enforce_reality(_base())
    assert result["reality_rewritten"] is False
