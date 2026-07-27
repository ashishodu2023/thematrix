from matrix.awareness import CharacterDecision
from matrix.continuous import CONTINUOUS_LEARNERS, FAST_LEARNERS, learning_pulse


def test_learning_pulse_persists(monkeypatch):
    saved: list[str] = []

    def fake_act_many(jobs, state=None):
        out = {}
        for name, allowed, _situation in jobs:
            out[name] = (
                CharacterDecision(
                    action="adapt",
                    speech=f"{name} adapts",
                    learned=f"peer of {name}",
                ),
                {
                    "character_actions": [f"{name}: adapt"],
                    "agent_memory": [f"{name}: learned — peer of {name}"],
                },
            )
        return out

    monkeypatch.setattr("matrix.continuous.act_many", fake_act_many)
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
    assert len(facts) >= len(FAST_LEARNERS)
    assert len(FAST_LEARNERS) < len(CONTINUOUS_LEARNERS)
    assert saved
    assert any("adapt" in f for f in facts)
