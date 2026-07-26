"""Ollama LLM factory for character dialogue."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from matrix.config import config


class OllamaUnavailableError(RuntimeError):
    """Raised when Ollama cannot be reached or generation fails."""


def get_llm() -> BaseChatModel:
    """Build a ChatOllama client from env/config."""
    return ChatOllama(
        model=config.ollama_model,
        base_url=config.ollama_base_url,
        temperature=0.7,
    )


def speak(system: str, user: str, *, llm: BaseChatModel | None = None) -> str:
    """
    Generate a short in-character line via Ollama.

    Raises OllamaUnavailableError with setup hints on connection failure.
    """
    client = llm or get_llm()
    try:
        response = client.invoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=user),
            ]
        )
    except Exception as exc:  # noqa: BLE001 — surface any transport/model error
        raise OllamaUnavailableError(
            "Ollama is unavailable. Start it and pull the model:\n"
            "  ollama serve\n"
            f"  ollama pull {config.ollama_model}\n"
            f"  OLLAMA_BASE_URL={config.ollama_base_url}\n"
            f"Original error: {exc}"
        ) from exc

    content = response.content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                parts.append(str(block))
        text = " ".join(parts)
    else:
        text = str(content)
    return text.strip().strip('"')
