"""Optional live Ollama smoke — skipped unless --ollama / MATRIX_OLLAMA_SMOKE=1."""

import os

import pytest

from matrix.llm import OllamaUnavailableError, speak


@pytest.mark.ollama
def test_ollama_speak_smoke():
    if os.getenv("MATRIX_OLLAMA_SMOKE") != "1":
        pytest.skip("Set MATRIX_OLLAMA_SMOKE=1 to run live Ollama smoke")
    try:
        text = speak(
            "You are a terse test assistant.",
            "Reply with exactly the word: ready",
        )
    except OllamaUnavailableError as exc:
        pytest.skip(str(exc))
    assert text
    assert len(text) < 500
