from matrix.characters import (
    RANK,
    all_brain_models,
    brain_model,
    brains_by_rank,
    character_rank,
)
from matrix.llm import operator_choose
from matrix.awareness import parse_decision


def test_brains_scale_with_matrix_rank():
    """Higher Matrix rank must get a model at least as 'large' in the ladder."""
    by_rank = brains_by_rank()
    assert by_rank[0][1] == "spoon_boy"
    assert by_rank[-1][1] == "architect"
    assert brain_model("spoon_boy") == "tinyllama"
    assert brain_model("architect") == "qwen2.5:32b"
    assert brain_model("oracle") == "qwen2.5:14b"
    assert brain_model("smith") == "gemma2:9b"
    assert brain_model("neo") == "qwen2.5:7b"
    assert character_rank("architect") > character_rank("neo") > character_rank(
        "trinity"
    )


def test_all_brains_cover_cast():
    brains = all_brain_models()
    assert set(brains) == set(RANK)
    # Architect brain distinct from spoon boy
    assert brains["architect"] != brains["spoon_boy"]


def test_brain_env_override(monkeypatch):
    monkeypatch.setenv("MATRIX_BRAIN_NEO", "custom-neo")
    assert brain_model("neo") == "custom-neo"


def test_operator_choose_parses_option(monkeypatch):
    monkeypatch.setattr(
        "matrix.llm.character_speak",
        lambda *_a, **_k: "I choose red because truth.",
    )
    assert operator_choose("pill", ["red", "blue"], "context") == "red"


def test_parse_decision_format():
    action, speech, learned = parse_decision(
        "ACTION: hunt\nSAY: Sector compromised.\nLEARN: Jones already scanned north.",
        ["scan", "hunt", "contain"],
    )
    assert action == "hunt"
    assert "Sector" in speech
    assert "Jones" in learned
