"""Runtime configuration for The Matrix simulation."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _f(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _truthy(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() not in {"0", "false", "no", "off"}


@dataclass(frozen=True)
class Config:
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    threat_skip_oracle: int = 7
    pursuit_max_rounds: int = 7
    showdown_max_rounds: int = 3
    default_agents: tuple[str, ...] = ("Smith", "Jones", "Brown")
    pace_seconds: float = 0.0
    stream_tokens: bool = False
    dashboard: bool = True
    world_ticks_per_scene: int = 1
    fast: bool = True
    max_tokens: int = 96
    no_rain: bool = True
    hitl_wait: float = 45.0
    difficulty: str = "balanced"
    tts: bool = True

    @classmethod
    def from_env(cls) -> Config:
        # Apply difficulty preset env if MATRIX_DIFFICULTY set before first import
        difficulty = os.getenv("MATRIX_DIFFICULTY", "balanced").strip().lower() or "balanced"
        fast = _truthy("MATRIX_FAST", "1")
        stream_default = "0" if fast else "1"
        pace_default = 0.0 if fast else 0.15
        rain_default = "1" if fast else "0"
        tokens_default = 80 if fast else 120
        hitl_default = 45.0 if difficulty in {"balanced", "cinematic"} else 12.0
        return cls(
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            threat_skip_oracle=int(os.getenv("MATRIX_THREAT_SKIP_ORACLE", "7")),
            pursuit_max_rounds=int(os.getenv("MATRIX_PURSUIT_MAX_ROUNDS", "7")),
            showdown_max_rounds=int(os.getenv("MATRIX_SHOWDOWN_MAX_ROUNDS", "3")),
            pace_seconds=_f("MATRIX_PACE", pace_default),
            stream_tokens=_truthy("MATRIX_STREAM", stream_default),
            dashboard=_truthy("MATRIX_DASHBOARD", "1"),
            world_ticks_per_scene=int(os.getenv("MATRIX_TICKS_PER_SCENE", "1")),
            fast=fast,
            max_tokens=int(os.getenv("MATRIX_MAX_TOKENS", str(tokens_default))),
            no_rain=_truthy("MATRIX_NO_RAIN", rain_default),
            hitl_wait=_f("MATRIX_HITL_WAIT", hitl_default),
            difficulty=difficulty,
            tts=_truthy("MATRIX_TTS", "1"),
        )


config = Config.from_env()

# Per-character voice temperatures (clinical → warm)
CHARACTER_TEMPERATURE: dict[str, float] = {
    "smith": 0.25,
    "jones": 0.2,
    "brown": 0.2,
    "architect": 0.3,
    "operator": 0.2,
    "tank": 0.55,
    "trinity": 0.45,
    "morpheus": 0.65,
    "neo": 0.7,
    "cypher": 0.75,
    "spoon_boy": 0.8,
    "oracle": 0.9,
    "merovingian": 0.55,
    "keymaker": 0.35,
    "sentinel": 0.15,
}
