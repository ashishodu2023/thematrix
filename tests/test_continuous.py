from matrix.continuous import CONTINUOUS_LEARNERS, learning_pulse


def test_learning_pulse_persists(monkeypatch):
    saved: list[str] = []

    monkeypatch.setattr(
        "matrix.continuous.character_act",
        lambda name, allowed, situation, state=None: (
            type("D", (), {"action": "adapt", "speech": f"{name} adapts", "learned": f"peer of {name}"})(),
            {
                "character_actions": [f"{name}: adapt"],
                "agent_memory": [f"{name}: learned — peer of {name}"],
            },
        ),
    )
    monkeypatch.setattr(
        "matrix.continuous.SessionMemory.remember_agents",
        lambda human_id, observations: saved.extend(observations) or None,
    )

    facts = learning_pulse(
        {
            "human_id": "neo",
            "outcome": "blue pill",
            "awakened": False,
            "agent_memory": [],
            "character_actions": [],
            "dialogue": ["Trinity: Cover me."],
            "agent_reports": [],
        }
    )
    assert len(facts) >= len(CONTINUOUS_LEARNERS)
    assert saved
    assert any("adapt" in f for f in facts)
