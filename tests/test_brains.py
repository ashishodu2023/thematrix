from matrix.characters import (
    RANK,
    all_brain_models,
    brain_model,
    brains_by_rank,
    character_rank,
)
from matrix.llm import operator_choose
from matrix.awareness import parse_decision


def test_brains_scale_with_matrix_rank(monkeypatch):
    """Higher Matrix rank must get a model at least as 'large' in the ladder."""
    monkeypatch.setenv("MATRIX_FAST", "0")
    from matrix import config as matrix_config
    from matrix import characters as chars

    matrix_config.config = matrix_config.Config.from_env()
    try:
        by_rank = chars.brains_by_rank()
        assert by_rank[0][0] == 1
        assert by_rank[0][1] in {"spoon_boy", "sentinel"}
        assert by_rank[-1][1] == "architect"
        assert chars.brain_model("spoon_boy") == "tinyllama"
        assert chars.brain_model("sentinel") == "tinyllama"
        assert chars.brain_model("architect") == "qwen2.5:32b"
        assert chars.brain_model("oracle") == "qwen2.5:14b"
        assert chars.brain_model("smith") == "gemma2:9b"
        assert chars.brain_model("neo") == "qwen2.5:7b"
        assert chars.character_rank("architect") > chars.character_rank(
            "neo"
        ) > chars.character_rank("trinity")
    finally:
        monkeypatch.setenv("MATRIX_FAST", "1")
        matrix_config.config = matrix_config.Config.from_env()


def test_fast_brains_cap_at_7b(monkeypatch):
    monkeypatch.setenv("MATRIX_FAST", "1")
    from matrix import config as matrix_config
    from matrix.characters import brain_model

    matrix_config.config = matrix_config.Config.from_env()
    assert brain_model("architect") == "qwen2.5:7b"
    assert brain_model("oracle") == "qwen2.5:7b"
    assert brain_model("spoon_boy") == "tinyllama"


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


def test_parse_decision_jammed_oneline():
    action, speech, learned = parse_decision(
        "ACTION:PURGEThe spoon hides a razor.SAY:I will eliminate it.LEARN:Smith re-inspects.",
        ["control", "balance", "purge"],
    )
    assert action == "purge"
    assert "ACTION" not in speech.upper()
    assert "eliminate" in speech.lower() or speech.startswith("(")
    assert "Smith" in learned or learned == ""
