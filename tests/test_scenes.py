"""Unit tests with mocked Ollama (no server required)."""

import matrix.nodes.architect as architect_mod
import matrix.nodes.cafe as cafe_mod
import matrix.nodes.construct as construct_mod
import matrix.nodes.pursuit as pursuit_mod
from matrix.nodes.architect import architect
from matrix.nodes.cafe import cafe_scene
from matrix.nodes.construct import load_skills
from matrix.nodes.kernel import simulation_kernel
from matrix.nodes.pill import resolve_choice
from matrix.nodes.pursuit import pursuit_loop


def _base(**overrides):
    state = {
        "human_id": "neo",
        "city": "Mega City",
        "cycle": 1,
        "location": "",
        "scene": "",
        "physics_rules": ["gravity", "solidity", "causality", "spoon_exists"],
        "anomaly": "spoon",
        "threat_level": 4,
        "architect_plan": "",
        "oracle_question": "Am I the One?",
        "oracle_prophecy": "",
        "agent_names": ["Smith"],
        "current_agent": "Smith",
        "agent_reports": [],
        "sectors_scanned": [],
        "spoon_exists": True,
        "reality_rewritten": True,
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


def _silence(monkeypatch):
    """Nodes import `from matrix import story` — patch the shared module."""
    monkeypatch.setattr("matrix.story.scene", lambda *_a, **_k: None)
    monkeypatch.setattr("matrix.story.say", lambda *_a, **_k: None)
    monkeypatch.setattr("matrix.story.beat", lambda *_a, **_k: None)
    monkeypatch.setattr("matrix.story.speak_as", lambda *_a, **_k: None)


def test_kernel_boot(monkeypatch):
    class FakeSession:
        lives = []
        agent_knowledge = []
        sticky_flags = {}
        co_human_id = ""

    monkeypatch.setattr(
        "matrix.nodes.kernel.SessionMemory.load",
        lambda human_id: FakeSession(),
    )
    _silence(monkeypatch)
    result = simulation_kernel(_base())
    assert result["city"] == "Mega City"
    assert result["previous_lives"] == 0
    assert result["location"] == "jack_point"


def test_architect_routes_to_oracle(monkeypatch):
    _silence(monkeypatch)

    def fake_act(character, allowed, situation, state=None):
        from matrix.awareness import CharacterDecision

        return CharacterDecision("consult_oracle", "Consult the Oracle.", "Neo recurs"), {
            "character_actions": ["architect: consult_oracle"],
            "agent_memory": ["architect: learned — Neo recurs"],
        }

    monkeypatch.setattr(architect_mod, "character_act", fake_act)
    cmd = architect(_base(threat_level=4))
    assert cmd.goto == "oracle_question"


def test_architect_skips_oracle_on_high_threat(monkeypatch):
    _silence(monkeypatch)

    def fake_act(character, allowed, situation, state=None):
        from matrix.awareness import CharacterDecision

        assert allowed == ["deploy_cafe", "quarantine_anomaly", "archive_anomaly"]
        return CharacterDecision("deploy_cafe", "Deploy immediately.", ""), {
            "character_actions": ["architect: deploy_cafe"],
        }

    monkeypatch.setattr(architect_mod, "character_act", fake_act)
    cmd = architect(_base(threat_level=9))
    assert cmd.goto == "cafe_scene"


def test_cafe_scene_uses_llm(monkeypatch):
    _silence(monkeypatch)

    def fake_act(character, allowed, situation, state=None):
        from matrix.awareness import CharacterDecision

        if character == "spoon_boy":
            return CharacterDecision("teach", "There is no spoon.", "Neo doubts"), {
                "character_actions": ["spoon_boy: teach"],
                "agent_memory": ["spoon_boy: learned — Neo doubts"],
            }
        return CharacterDecision("believe", "I… believe.", "Boy knows"), {
            "character_actions": ["neo: believe"],
            "agent_memory": ["neo: learned — Boy knows"],
        }

    monkeypatch.setattr(cafe_mod, "character_act", fake_act)
    result = cafe_scene(_base())
    assert result["location"] == "cafe"
    assert "Spoon Boy" in result["dialogue"][0]


def test_pursuit_escape(monkeypatch):
    _silence(monkeypatch)

    def fake_act(character, allowed, situation, state=None):
        from matrix.awareness import CharacterDecision

        return CharacterDecision("close_in", "Mr. Anderson...", "Neo fears"), {
            "character_actions": ["smith: close_in"],
            "agent_memory": ["smith: learned — Neo fears"],
        }

    monkeypatch.setattr(pursuit_mod, "character_act", fake_act)
    monkeypatch.setattr(
        pursuit_mod,
        "pursue_step",
        lambda *_a, **_k: ("escaped", "Neo escapes"),
    )
    cmd = pursuit_loop(_base())
    assert cmd.goto == "morpheus_offer"
    assert cmd.update["pursuit_status"] == "escaped"


def test_construct_scoring(monkeypatch):
    _silence(monkeypatch)
    monkeypatch.setattr(
        "matrix.nodes.construct.character_speak",
        lambda *_a, **_k: "Program loaded.",
    )
    loaded = load_skills(_base(reality_rewritten=True))
    assert len(loaded["training_skills"]) == 3
    from matrix.nodes.construct import spar_morpheus

    scored = spar_morpheus({**_base(reality_rewritten=True), **loaded})
    assert scored["training_score"] >= 2


def test_resolve_red_fight(monkeypatch):
    _silence(monkeypatch)
    result = resolve_choice(
        _base(
            pill_choice="red",
            fight_choice="fight",
            training_score=10,
            trust_choice="trust",
            jump_choice="jump",
            radio_choice="call",
            code_choice="accept",
            bug_choice="extract",
            steak_choice="refuse",
            showdown_status="won",
        )
    )
    assert result["awakened"] is True
    assert "The One begins" in result["outcome"]
