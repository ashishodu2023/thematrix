"""
Operator outside the Matrix — resume a paused jack-in.

Usage examples:
    matrix-resume "Am I the One?"     # oracle_question interrupt
    matrix-resume red                 # pill interrupt
    matrix-resume blue
    matrix-resume fight               # fight_or_flee interrupt
    matrix-resume flee
"""

from __future__ import annotations

import sys

from langgraph.types import Command

from matrix import story
from matrix.graph import get_graph
from matrix.thread_store import load_active_thread


def _interrupt_kind(snapshot) -> str | None:
    interrupts = getattr(snapshot, "interrupts", None) or ()
    for item in interrupts:
        value = getattr(item, "value", item)
        if isinstance(value, dict) and value.get("kind"):
            return str(value["kind"])
    pending = (snapshot.values or {}).get("pending_decision")
    return str(pending) if pending else None


def _parse_resume(kind: str | None, args: list[str]) -> str:
    joined = " ".join(args).strip()
    if not joined:
        if kind == "oracle_question":
            return "Am I the One?"
        if kind == "pill":
            return "red"
        if kind == "fight_or_flee":
            return "flee"
        return "red"

    lowered = joined.lower()
    if kind == "pill":
        if lowered not in {"red", "blue"}:
            print("Pill interrupt expects: red | blue")
            sys.exit(1)
        return lowered
    if kind == "fight_or_flee":
        if lowered not in {"fight", "flee"}:
            print("Fight/flee interrupt expects: fight | flee")
            sys.exit(1)
        return lowered
    # oracle_question — free text
    return joined


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]

    try:
        thread_id = load_active_thread()
    except FileNotFoundError as exc:
        print(str(exc))
        sys.exit(1)

    config = {"configurable": {"thread_id": thread_id}}
    graph = get_graph()
    snapshot = graph.get_state(config)

    if not snapshot.values:
        story.scene("NO CHECKPOINT")
        story.say(f"No saved state for thread {thread_id}.")
        story.beat("Run:  uv run matrix-jack-in")
        sys.exit(1)

    interrupts = getattr(snapshot, "interrupts", None) or ()
    if not interrupts and not snapshot.next:
        requested = " ".join(args) if args else "(none)"
        story.already_finished(thread_id, snapshot.values, requested)
        sys.exit(1)

    if not interrupts:
        story.scene("NOT WAITING")
        story.say("Thread has next nodes but no interrupt payload.")
        story.say(f"next={snapshot.next}")
        sys.exit(1)

    kind = _interrupt_kind(snapshot)
    resume_value = _parse_resume(kind, args)

    story.scene("OPERATOR RESUME")
    story.say(f"Thread: {thread_id}")
    story.say(f"Interrupt kind: {kind}")
    story.say(f"Injecting: {resume_value}")

    try:
        result = graph.invoke(Command(resume=resume_value), config=config)
    except Exception as exc:  # noqa: BLE001
        from matrix.llm import OllamaUnavailableError

        if isinstance(exc, OllamaUnavailableError) or "Ollama" in str(exc):
            print()
            print(str(exc))
            raise SystemExit(1) from exc
        raise

    # May pause again on the next HITL
    interrupts_out = result.get("__interrupt__") if isinstance(result, dict) else None
    if interrupts_out:
        first = interrupts_out[0]
        payload = getattr(first, "value", first)
        if not isinstance(payload, dict):
            payload = {"message": str(payload)}
        next_kind = payload.get("kind") or "unknown"
        hint = payload.get("message") or ""
        story.pause_for_interrupt(thread_id, next_kind, hint, result)
    else:
        story.ending(result)


if __name__ == "__main__":
    main()
