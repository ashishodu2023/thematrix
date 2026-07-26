"""Runtime configuration for The Matrix simulation."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    threat_skip_oracle: int = 7
    pursuit_max_rounds: int = 7
    showdown_max_rounds: int = 3
    default_agents: tuple[str, ...] = ("Smith", "Jones", "Brown")

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            threat_skip_oracle=int(os.getenv("MATRIX_THREAT_SKIP_ORACLE", "7")),
            pursuit_max_rounds=int(os.getenv("MATRIX_PURSUIT_MAX_ROUNDS", "7")),
            showdown_max_rounds=int(os.getenv("MATRIX_SHOWDOWN_MAX_ROUNDS", "3")),
        )


config = Config.from_env()
