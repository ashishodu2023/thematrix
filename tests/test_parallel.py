"""Parallel cast helpers."""

from matrix.parallel import act_many, merge_patches, speak_many


def test_speak_many_parallel(monkeypatch):
    monkeypatch.setattr(
        "matrix.parallel.character_speak",
        lambda who, prompt, state=None, stream=False: f"{who}-line",
    )
    out = speak_many([("neo", "hi"), ("smith", "hunt")], state={})
    assert out["neo"] == "neo-line"
    assert out["smith"] == "smith-line"


def test_act_many_parallel(monkeypatch):
    from matrix.awareness import CharacterDecision

    def fake_act(who, allowed, situation, state=None):
        return CharacterDecision(action=allowed[0], speech=f"{who} ok", learned="x"), {
            "character_actions": [f"{who}: {allowed[0]}"],
        }

    monkeypatch.setattr("matrix.parallel.character_act", fake_act)
    out = act_many(
        [
            ("trinity", ["cover", "advance"], "lobby"),
            ("smith", ["suppress", "flank"], "lobby"),
        ],
        state={},
    )
    assert out["trinity"][0].action == "cover"
    assert out["smith"][0].action == "suppress"
    merged = merge_patches([out["trinity"][1], out["smith"][1]])
    assert len(merged["character_actions"]) == 2


def test_graph_has_parallel_field_nodes():
    from matrix.graphs.main import build_graph

    g = build_graph()
    names = set(g.get_graph().nodes)
    for n in ("field_pulse_a", "field_pulse_b", "field_pulse_c", "field_pulse_d", "field_pulse_e"):
        assert n in names
