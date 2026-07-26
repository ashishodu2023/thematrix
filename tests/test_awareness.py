from matrix.awareness import dossier_of_others, parse_decision, remember, record_action
from matrix.llm import character_act


def test_dossier_excludes_self_dialogue():
    state = {
        "city": "Mega City",
        "scene": "lobby",
        "anomaly": "spoon",
        "threat_level": 5,
        "agent_names": ["Smith", "Jones"],
        "dialogue": [
            "Trinity: Cover me.",
            "Agent Smith: Mr. Anderson.",
            "Neo: What is happening?",
        ],
        "agent_reports": ["Jones: sector clear"],
        "agent_memory": ["trinity: learned — Smith hunts Neo"],
        "character_actions": ["trinity: cover — Cover me."],
    }
    brief = dossier_of_others("smith", state)
    assert "Trinity: Cover me." in brief
    assert "Neo: What is happening?" in brief
    assert "Agent Smith: Mr. Anderson." not in brief
    assert "Jones: sector clear" in brief


def test_remember_and_record_patches():
    mem = remember("neo", "Trinity covers under fire")
    assert mem["agent_memory"][0].startswith("neo: learned")
    act = record_action("trinity", "cover", "left flank")
    assert "trinity: cover" in act["character_actions"][0]


def test_character_act_independent(monkeypatch):
    monkeypatch.setattr(
        "matrix.llm.character_speak",
        lambda *_a, **_k: (
            "ACTION: hunt\nSAY: Pursuing anomaly.\nLEARN: Brown holds the west."
        ),
    )
    decision, patches = character_act(
        "smith",
        ["scan", "hunt", "hold"],
        "Field choice",
        state={"dialogue": [], "agent_memory": [], "character_actions": []},
    )
    assert decision.action == "hunt"
    assert "Pursuing" in decision.speech
    assert "Brown" in decision.learned
    assert patches["character_actions"]
    assert patches["agent_memory"]
