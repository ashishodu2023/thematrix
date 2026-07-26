"""Ollama LLM factory — rank-scaled brains + awareness-aware dialogue/acts."""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from matrix.awareness import (
    CharacterDecision,
    current_state,
    dossier_of_others,
    parse_decision,
    record_action,
    remember,
)
from matrix.characters import PERSONAS, agent_persona, brain_model, character_rank
from matrix.config import config


class OllamaUnavailableError(RuntimeError):
    """Raised when Ollama cannot be reached or generation fails."""


@lru_cache(maxsize=32)
def get_llm(model: str | None = None) -> BaseChatModel:
    """Build / cache a ChatOllama client for a specific model tag."""
    tag = model or config.ollama_model
    return ChatOllama(
        model=tag,
        base_url=config.ollama_base_url,
        temperature=0.7,
    )


def get_character_llm(character: str) -> BaseChatModel:
    """Return the Ollama brain assigned to this character (rank-scaled)."""
    return get_llm(brain_model(character, fallback=config.ollama_model))


def _extract_text(content: object) -> str:
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


def speak(
    system: str,
    user: str,
    *,
    llm: BaseChatModel | None = None,
    model: str | None = None,
) -> str:
    """Generate a short line via Ollama."""
    client = llm or get_llm(model)
    try:
        response = client.invoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=user),
            ]
        )
    except Exception as exc:  # noqa: BLE001
        tag = model or config.ollama_model
        raise OllamaUnavailableError(
            "Ollama is unavailable or model missing. Try:\n"
            "  ollama serve\n"
            f"  ollama pull {tag}\n"
            "  uv run matrix-pull-brains\n"
            f"  OLLAMA_BASE_URL={config.ollama_base_url}\n"
            f"Original error: {exc}"
        ) from exc
    return _extract_text(response.content)


def _system_for(character: str) -> str:
    key = character.strip().lower()
    base = PERSONAS.get(key) or agent_persona(key)
    rank = character_rank(key)
    return (
        f"{base}\n"
        f"Your Matrix rank is {rank}/12 (higher = more authority/power). "
        "You share the simulation with other independent agents. "
        "Use what you know about them. Act on your own judgment."
    )


def character_speak(
    character: str,
    user: str,
    state: dict | None = None,
) -> str:
    """
    Speak in-character using that character's rank-scaled Ollama brain.

    Injects shared awareness of other agents (from `state` or bound context).
    """
    key = character.strip().lower()
    ctx = state if state is not None else current_state()
    awareness = dossier_of_others(key, ctx)
    system = _system_for(key)
    prompt = (
        f"Shared awareness of other Matrix agents:\n{awareness}\n\n"
        f"Your situation / instruction:\n{user}"
    )
    model = brain_model(key, fallback=config.ollama_model)
    try:
        return speak(system, prompt, model=model)
    except OllamaUnavailableError:
        if model != config.ollama_model:
            return speak(system, prompt, model=config.ollama_model)
        raise


def character_act(
    character: str,
    allowed_actions: list[str],
    situation: str,
    state: dict | None = None,
) -> tuple[CharacterDecision, dict]:
    """
    Independent action: character learns about others, chooses an action, speaks.

    Returns (decision, state_patches) where patches include agent_memory
    and character_actions reducers.
    """
    if not allowed_actions:
        raise ValueError("allowed_actions must be non-empty")

    key = character.strip().lower()
    ctx = state if state is not None else current_state()
    opts = ", ".join(allowed_actions)
    user = (
        f"{situation}\n\n"
        f"You act independently. Choose exactly one ACTION from: {opts}.\n"
        "Reply in this exact format:\n"
        "ACTION: <one allowed action>\n"
        "SAY: <one short in-character sentence>\n"
        "LEARN: <one short fact you inferred about another agent or the anomaly>"
    )
    raw = character_speak(key, user, state=ctx)
    action, speech, learned = parse_decision(raw, allowed_actions)
    decision = CharacterDecision(action=action, speech=speech, learned=learned)
    patches: dict = {}
    patches.update(record_action(key, action, speech[:80]))
    if learned:
        patches.update(remember(key, learned))
    return decision, patches


def operator_choose(kind: str, options: list[str], context: str) -> str:
    """Daemon HITL brain — Operator model picks exactly one allowed option."""
    opts = ", ".join(options)
    user = (
        f"Pending Matrix decision kind={kind}.\n"
        f"Allowed options (pick exactly one): {opts}\n"
        f"Context:\n{context[:1200]}\n"
        "Reply with ONLY the chosen option word."
    )
    raw = character_speak("operator", user).strip().lower()
    tokens = raw.replace(".", " ").replace(",", " ").split()
    for token in tokens:
        if token in options:
            return token
    for opt in options:
        if opt in raw:
            return opt
    return options[0]
