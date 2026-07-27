"""Ollama LLM factory — streaming, per-character temperature, awareness."""

from __future__ import annotations

import sys
import time
import os
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
from matrix.config import CHARACTER_TEMPERATURE, config
from matrix.minds import MindStore
from matrix.objectives import apply_action_score
from matrix.theme import enabled, paint


class OllamaUnavailableError(RuntimeError):
    """Raised when Ollama cannot be reached or generation fails."""


@lru_cache(maxsize=64)
def get_llm(model: str | None = None, temperature: float = 0.7) -> BaseChatModel:
    tag = model or config.ollama_model
    return ChatOllama(
        model=tag,
        base_url=config.ollama_base_url,
        temperature=temperature,
        num_predict=config.max_tokens,
    )


def get_character_llm(character: str) -> BaseChatModel:
    key = character.strip().lower()
    temp = CHARACTER_TEMPERATURE.get(key, 0.7)
    return get_llm(brain_model(key, fallback=config.ollama_model), temperature=temp)


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


def _drip(text: str) -> None:
    """Stream green glyphs to the terminal."""
    if not config.stream_tokens or not enabled():
        return
    delay = 0.0 if config.fast else 0.008
    for ch in text:
        sys.stdout.write(paint(ch))
        sys.stdout.flush()
        if delay:
            time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def speak(
    system: str,
    user: str,
    *,
    llm: BaseChatModel | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    stream: bool | None = None,
) -> str:
    client = llm or get_llm(model, temperature=temperature)
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    do_stream = config.stream_tokens if stream is None else stream
    try:
        if do_stream and hasattr(client, "stream"):
            chunks: list[str] = []
            if enabled():
                sys.stdout.write(paint("  ░ "))
                sys.stdout.flush()
            for piece in client.stream(messages):
                part = _extract_text(getattr(piece, "content", piece) or "")
                if not part:
                    continue
                chunks.append(part)
                if enabled():
                    sys.stdout.write(paint(part))
                    sys.stdout.flush()
            if enabled():
                sys.stdout.write("\n")
                sys.stdout.flush()
            text = _extract_text("".join(chunks))
            if config.pace_seconds > 0:
                time.sleep(config.pace_seconds)
            return text
        response = client.invoke(messages)
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
    text = _extract_text(response.content)
    _drip(text)
    if config.pace_seconds > 0:
        time.sleep(config.pace_seconds)
    return text


def _system_for(character: str) -> str:
    key = character.strip().lower()
    base = PERSONAS.get(key) or agent_persona(key)
    rank = character_rank(key)
    mind = MindStore.dossier(key)
    return (
        f"{base}\n"
        f"Your Matrix rank is {rank}/12. Persistent mind: {mind}. "
        "Compete for your faction's objectives. Act independently."
    )


def character_speak(
    character: str,
    user: str,
    state: dict | None = None,
    *,
    stream: bool | None = None,
) -> str:
    key = character.strip().lower()
    ctx = state if state is not None else current_state()
    awareness = dossier_of_others(key, ctx)
    system = _system_for(key)
    prompt = (
        f"Shared awareness of other Matrix agents:\n{awareness}\n\n"
        f"Your situation / instruction:\n{user}"
    )
    model = brain_model(key, fallback=config.ollama_model)
    temp = CHARACTER_TEMPERATURE.get(key, 0.7)
    try:
        return speak(
            system, prompt, model=model, temperature=temp, stream=stream
        )
    except OllamaUnavailableError:
        if model != config.ollama_model:
            return speak(
                system,
                prompt,
                model=config.ollama_model,
                temperature=temp,
                stream=stream,
            )
        raise


def character_act(
    character: str,
    allowed_actions: list[str],
    situation: str,
    state: dict | None = None,
    *,
    tools: str | None = None,
) -> tuple[CharacterDecision, dict]:
    if not allowed_actions:
        raise ValueError("allowed_actions must be non-empty")

    key = character.strip().lower()
    ctx = state if state is not None else current_state()
    opts = ", ".join(allowed_actions)

    rag_block = ""
    try:
        from matrix.rag import retrieve_block

        rag_block = retrieve_block(
            situation,
            human_id=str((ctx or {}).get("human_id") or "neo"),
            character=key,
            k=3,
        )
    except Exception:  # noqa: BLE001
        rag_block = ""

    tool_hint = ""
    tool_allowed = None
    if tools:
        from matrix.tool_runtime import AGENT_TOOLS, OPERATOR_TOOLS, tool_catalog as list_tools

        tool_allowed = OPERATOR_TOOLS if tools == "operator" else AGENT_TOOLS
        tool_hint = (
            f"\nOptional tools (zero or one line): TOOL: <{list_tools(tools)}> (arg)\n"
            "Example: TOOL: scan(highway)"
        )

    user = (
        f"{situation}\n\n"
        + (f"{rag_block}\n\n" if rag_block else "")
        + f"You act independently for your faction. "
        f"Choose exactly one ACTION from: {opts}.\n"
        "Reply in this exact format (three lines, spaces after colons):\n"
        "ACTION: <one allowed action>\n"
        "SAY: <one short in-character sentence>\n"
        "LEARN: <one short fact you inferred about another agent or the anomaly>\n"
        "Do not glue words together. Always put a space after each colon."
        + tool_hint
    )
    # Non-streaming so ACTION/SAY/LEARN parse cleanly
    raw = character_speak(key, user, state=ctx, stream=False)
    action, speech, learned = parse_decision(raw, allowed_actions)
    decision = CharacterDecision(action=action, speech=speech, learned=learned)
    apply_action_score(key, action)
    neo_loc = str((ctx or {}).get("location") or "")
    if learned:
        MindStore.remember(key, learned, neo_location=neo_loc)
    patches: dict = {}
    patches.update(record_action(key, action, speech[:80]))
    if learned:
        patches.update(remember(key, learned))
    if tool_allowed and ctx is not None:
        from matrix.tool_runtime import run_tools

        tool_patch = run_tools({**ctx, "current_agent": key}, raw, allowed=tool_allowed)
        for k, v in tool_patch.items():
            if k in {
                "events",
                "log",
                "agent_reports",
                "sectors_scanned",
                "phone_taps",
                "tool_results",
            }:
                patches[k] = list(patches.get(k) or []) + list(
                    v if isinstance(v, list) else [v]
                )
            elif k not in {"ok"}:
                patches[k] = v
        # Native bind_tools pass (default ON; set MATRIX_BIND_TOOLS=0 to disable)
        _bind = os.getenv("MATRIX_BIND_TOOLS", "1").strip().lower()
        if _bind not in {"0", "false", "no", "off"}:
            try:
                from langchain_core.messages import HumanMessage, SystemMessage

                from matrix.lc_tools import try_bound_invoke

                bound = try_bound_invoke(
                    get_character_llm(key),
                    [
                        SystemMessage(content=_system_for(key) + "\nPrefer structured tools."),
                        HumanMessage(content=situation[:800]),
                    ],
                    kind=tools,
                    state={**ctx, "current_agent": key},
                )
                if bound:
                    _, bound_patches = bound
                    for k, v in bound_patches.items():
                        if k in {
                            "events",
                            "log",
                            "agent_reports",
                            "sectors_scanned",
                            "phone_taps",
                            "tool_results",
                        }:
                            patches[k] = list(patches.get(k) or []) + list(
                                v if isinstance(v, list) else [v]
                            )
                        elif k not in {"ok"} and k not in patches:
                            patches[k] = v
            except Exception:  # noqa: BLE001
                pass
    return decision, patches


def operator_choose(kind: str, options: list[str], context: str) -> str:
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
