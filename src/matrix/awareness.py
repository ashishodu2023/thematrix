"""Shared awareness — characters learn about others and act independently."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from typing import Iterator

_STATE: ContextVar[dict | None] = ContextVar("matrix_awareness_state", default=None)


@contextmanager
def use_state(state: dict) -> Iterator[dict]:
    """Bind graph state so character_speak / character_act see other agents."""
    token = _STATE.set(state)
    try:
        from matrix import story

        story.note_state(state)
        yield state
    finally:
        _STATE.reset(token)


def _publish_snap(state: dict, out: object) -> None:
    try:
        from matrix import dashboard
        from matrix import story

        snap = dict(state)
        if isinstance(out, dict):
            for k, v in out.items():
                if str(k).startswith("__"):
                    continue
                snap[k] = v
            story.note_state(snap)
        dashboard.publish_state(snap)
    except Exception:  # noqa: BLE001
        pass


def aware_node(fn):
    """Decorator: bind Matrix state + push Operator Console live updates."""

    @wraps(fn)
    def wrapper(state, *args, **kwargs):
        with use_state(state):
            out = fn(state, *args, **kwargs)
        _publish_snap(state, out)
        return out

    wrapper._matrix_live = True  # type: ignore[attr-defined]
    return wrapper


def live_node(fn):
    """Wrap a node for live console updates; leave compiled subgraphs alone."""
    if fn is None:
        return fn
    # Compiled LangGraph graphs / runnables expose invoke + get_graph
    if hasattr(fn, "get_graph") and hasattr(fn, "invoke"):
        return fn
    if getattr(fn, "_matrix_live", False):
        return fn
    return aware_node(fn)


def current_state() -> dict | None:
    return _STATE.get()


def dossier_of_others(character: str, state: dict | None, *, limit: int = 12) -> str:
    """
    Build a short multi-agent awareness brief for `character`.

    Pulls dialogue, reports, actions, persistent minds, and surveillance.
    """
    if not state:
        return "No shared Matrix awareness yet."

    key = character.strip().lower()
    lines: list[str] = []

    city = state.get("city") or "?"
    threat = state.get("threat_level")
    anomaly = state.get("anomaly")
    scene = state.get("scene") or "?"
    trace = state.get("trace_level")
    meta = state.get("meta_policy") or "-"
    lines.append(
        f"World: city={city} scene={scene} anomaly={anomaly} "
        f"threat={threat} trace={trace} meta={meta}"
    )
    sticky = state.get("sticky_flags") or {}
    if sticky:
        lines.append(f"Sticky branches: {sticky}")

    try:
        from matrix.minds import MindStore

        peer_names = [
            "neo",
            "trinity",
            "morpheus",
            "smith",
            "oracle",
            "architect",
            "tank",
            "cypher",
            "jones",
            "brown",
        ]
        mind_bits = []
        for n in peer_names:
            if n == key:
                continue
            mind_bits.append(f"{n}[{MindStore.dossier(n)}]")
        if mind_bits:
            lines.append("Persistent minds: " + " || ".join(mind_bits[:6]))
    except Exception:  # noqa: BLE001
        pass

    agents = state.get("agent_names") or []
    if agents:
        others = [a for a in agents if a.strip().lower() != key]
        if others:
            lines.append(f"Known Agents in field: {', '.join(others)}")
    positions = state.get("agent_positions") or {}
    if positions:
        lines.append(f"Agent positions: {positions}")

    memory = list(state.get("agent_memory") or [])
    if memory:
        lines.append("Learned about others:")
        for item in memory[-limit:]:
            if key and str(item).lower().startswith(f"{key}:"):
                continue
            lines.append(f"  - {item}")

    actions = list(state.get("character_actions") or [])
    peer_actions = [
        a for a in actions if not str(a).lower().startswith(f"{key}:")
    ]
    if peer_actions:
        lines.append("Recent independent actions by others:")
        for item in peer_actions[-limit:]:
            lines.append(f"  - {item}")

    reports = list(state.get("agent_reports") or [])
    if reports:
        lines.append("Agent field reports:")
        for item in reports[-limit:]:
            lines.append(f"  - {item}")

    dialogue = list(state.get("dialogue") or [])
    others_lines = []
    for line in dialogue:
        speaker = str(line).split(":", 1)[0].strip().lower()
        speaker_key = speaker.replace("agent ", "").replace(" ", "_")
        if speaker_key == key or speaker == key:
            continue
        others_lines.append(line)
    if others_lines:
        lines.append("What others said:")
        for item in others_lines[-limit:]:
            lines.append(f"  - {item}")

    prophecy = state.get("oracle_prophecy") or ""
    if prophecy and key != "oracle":
        lines.append(f"Oracle prophecy echo: {prophecy}")

    plan = state.get("architect_plan") or ""
    if plan and key != "architect":
        lines.append(f"Architect plan known: {plan}")

    return "\n".join(lines)


def remember(character: str, observation: str) -> dict:
    """State patch: character learned a fact about the Matrix / others."""
    text = observation.strip()
    if not text:
        return {}
    return {
        "agent_memory": [f"{character}: learned — {text}"],
    }


def record_action(character: str, action: str, detail: str = "") -> dict:
    """State patch: character took an independent action."""
    bit = f"{character}: {action}"
    if detail:
        bit = f"{bit} — {detail}"
    return {
        "character_actions": [bit],
        "agent_memory": [f"{character}: observed action {action}"],
    }


@dataclass
class CharacterDecision:
    action: str
    speech: str
    learned: str = ""


def parse_decision(raw: str, allowed: list[str]) -> tuple[str, str, str]:
    """
    Parse LLM output of the form:
      ACTION: <option>
      SAY: <line>
      LEARN: <fact about another agent>

    Also handles jammed one-liners like:
      ACTION:purgeThe spoon...SAY:HelloLEARN:fact
    """
    import re

    text = (raw or "").strip()
    # Insert breaks before labels even when the model jams them together
    text = re.sub(r"(?i)\b(ACTION|SAY|LEARN)\s*:", r"\n\1: ", text)
    text = text.strip()

    action = allowed[0]
    speech = ""
    learned = ""

    m_act = re.search(r"(?i)ACTION\s*:\s*([a-z0-9_\-]+)", text)
    if m_act:
        cand = m_act.group(1).lower().strip(".,")
        if cand in allowed:
            action = cand
        else:
            # model may glue action to next word: purgeThe → purge
            for opt in sorted(allowed, key=len, reverse=True):
                if cand.startswith(opt):
                    action = opt
                    break

    m_say = re.search(
        r"(?i)SAY\s*:\s*(.+?)(?=\n\s*LEARN\s*:|\Z)", text, flags=re.S
    )
    if m_say:
        speech = m_say.group(1).strip().strip('"')

    m_learn = re.search(r"(?i)LEARN\s*:\s*(.+)$", text, flags=re.S)
    if m_learn:
        learned = m_learn.group(1).strip().strip('"')

    if not speech:
        # Strip label debris and use remaining prose
        cleaned = re.sub(r"(?i)\b(ACTION|SAY|LEARN)\s*:\s*", " ", text)
        for opt in allowed:
            cleaned = re.sub(rf"(?i)\b{re.escape(opt)}\b", " ", cleaned, count=1)
        speech = " ".join(cleaned.split()).strip().strip('"')

    # Never return the raw structured blob as dialogue
    if re.search(r"(?i)\bACTION\s*:", speech) or len(speech) > 280:
        # Prefer a short sentence after the action token
        after = text
        if m_act:
            after = text[m_act.end() :]
        after = re.sub(r"(?i)\b(SAY|LEARN)\s*:", " ", after)
        speech = " ".join(after.split())[:180].strip()

    if not speech:
        speech = f"({action})"

    # Fallback: first matching option token anywhere
    tokens = re.findall(r"[a-z0-9_\-]+", text.lower())
    for t in tokens:
        if t in allowed:
            action = t
            break

    return action, speech, learned
