"""Difficulty presets — cinematic / balanced / fast / tiny."""

from __future__ import annotations

import os
from typing import Any

PRESETS: dict[str, dict[str, Any]] = {
    "cinematic": {
        "MATRIX_FAST": "0",
        "MATRIX_STREAM": "1",
        "MATRIX_PACE": "0.12",
        "MATRIX_NO_RAIN": "0",
        "MATRIX_VERTICAL": "1",
        "MATRIX_MAX_TOKENS": "140",
        "MATRIX_HITL_WAIT": "0",
        "MATRIX_PARALLEL": "1",
    },
    "balanced": {
        "MATRIX_FAST": "1",
        "MATRIX_STREAM": "0",
        "MATRIX_PACE": "0",
        "MATRIX_NO_RAIN": "1",
        "MATRIX_VERTICAL": "0",
        "MATRIX_MAX_TOKENS": "96",
        "MATRIX_HITL_WAIT": "30",
        "MATRIX_PARALLEL": "1",
    },
    "fast": {
        "MATRIX_FAST": "1",
        "MATRIX_STREAM": "0",
        "MATRIX_PACE": "0",
        "MATRIX_NO_RAIN": "1",
        "MATRIX_VERTICAL": "0",
        "MATRIX_MAX_TOKENS": "64",
        "MATRIX_HITL_WAIT": "12",
        "MATRIX_PARALLEL": "1",
        "MATRIX_BRAIN_ARCHITECT": "qwen2.5:3b",
        "MATRIX_BRAIN_ORACLE": "qwen2.5:3b",
        "MATRIX_BRAIN_SMITH": "qwen2.5:3b",
    },
    "tiny": {
        "MATRIX_FAST": "1",
        "MATRIX_STREAM": "0",
        "MATRIX_PACE": "0",
        "MATRIX_NO_RAIN": "1",
        "MATRIX_VERTICAL": "0",
        "MATRIX_MAX_TOKENS": "48",
        "MATRIX_HITL_WAIT": "8",
        "MATRIX_PARALLEL": "1",
        "OLLAMA_MODEL": "tinyllama",
        "MATRIX_BRAIN_NEO": "tinyllama",
        "MATRIX_BRAIN_TRINITY": "tinyllama",
        "MATRIX_BRAIN_MORPHEUS": "tinyllama",
        "MATRIX_BRAIN_SMITH": "tinyllama",
        "MATRIX_BRAIN_ORACLE": "tinyllama",
        "MATRIX_BRAIN_ARCHITECT": "tinyllama",
        "MATRIX_BRAIN_OPERATOR": "tinyllama",
    },
}


def apply_preset(name: str) -> str:
    """Apply env overrides for a preset (call before Config.from_env reload)."""
    key = (name or "balanced").strip().lower()
    preset = PRESETS.get(key) or PRESETS["balanced"]
    for env_k, env_v in preset.items():
        os.environ[env_k] = str(env_v)
    os.environ["MATRIX_DIFFICULTY"] = key
    return key


def current_preset() -> str:
    return os.getenv("MATRIX_DIFFICULTY", "balanced").strip().lower() or "balanced"
