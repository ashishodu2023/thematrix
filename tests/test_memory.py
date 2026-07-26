from matrix.models import MatrixSession, PreviousLife
from matrix.services.memory import SessionMemory


def test_session_roundtrip(monkeypatch):
    store: dict[str, str] = {}

    monkeypatch.setattr(
        "matrix.services.memory.redis_client.get",
        lambda key: store.get(key),
    )
    monkeypatch.setattr(
        "matrix.services.memory.redis_client.set",
        lambda key, value: store.__setitem__(key, value),
    )

    empty = SessionMemory.load("trinity")
    assert empty.human_id == "trinity"
    assert empty.lives == []

    life = PreviousLife(
        cycle=1,
        city="Mega City",
        pill_choice="red",
        outcome="unplugged",
        reality_rewritten=True,
        training_score=4,
        fight_choice="fight",
        locations_visited=["cafe", "construct"],
    )
    session = SessionMemory.record_life("trinity", life)
    assert session.awakened_count == 1
    assert len(session.lives) == 1

    loaded = SessionMemory.load("trinity")
    assert isinstance(loaded, MatrixSession)
    assert loaded.lives[0].training_score == 4
    assert loaded.lives[0].fight_choice == "fight"
