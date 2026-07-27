"""Operator API helpers — resume graph from console choices."""

from __future__ import annotations

import threading
from typing import Any

from langgraph.types import Command

from matrix import story
from matrix.graph import get_graph
from matrix.hitl_bridge import clear_pending, options_for, read_pending, submit_choice
from matrix.thread_store import load_active_thread


def resume_choice(choice: str, *, seat: str = "operator") -> dict[str, Any]:
    """Submit HITL choice for daemon waiters and/or resume an interactive thread."""
    pending = read_pending() or {}
    recorded = submit_choice(choice, seat=seat)

    # If a jack-in is paused in Redis checkpoint, resume it in a worker thread.
    def _run() -> None:
        try:
            thread_id = load_active_thread()
        except FileNotFoundError:
            return
        config = {"configurable": {"thread_id": thread_id}}
        graph = get_graph()
        snapshot = graph.get_state(config)
        interrupts = getattr(snapshot, "interrupts", None) or ()
        if not interrupts:
            return
        kind = ""
        for item in interrupts:
            value = getattr(item, "value", item)
            if isinstance(value, dict) and value.get("kind"):
                kind = str(value["kind"])
                break
        text = recorded["choice"]
        allowed = options_for(kind)
        if kind and kind != "oracle_question" and allowed:
            if text.lower() not in {a.lower() for a in allowed}:
                return
        try:
            result = graph.invoke(Command(resume=text), config=config)
        except Exception:  # noqa: BLE001
            return
        clear_pending()
        interrupts_out = result.get("__interrupt__") if isinstance(result, dict) else None
        if interrupts_out:
            first = interrupts_out[0]
            payload = getattr(first, "value", first)
            if not isinstance(payload, dict):
                payload = {"message": str(payload)}
            next_kind = payload.get("kind") or "unknown"
            hint = payload.get("message") or ""
            from matrix.hitl_bridge import publish_pending
            from matrix import dashboard

            hitl = publish_pending(
                thread_id=thread_id,
                kind=str(next_kind),
                message=str(hint),
                seat=seat,
            )
            dashboard.publish(
                {
                    "status": "hitl",
                    "hitl": hitl,
                    "thread_id": thread_id,
                    "location": result.get("location"),
                    "scene": result.get("scene"),
                }
            )
            story.pause_for_interrupt(thread_id, next_kind, hint, result)
        else:
            from matrix import dashboard
            from matrix.replay import save_life

            dashboard.publish({"status": "cycle_end", "hitl": None, "outcome": result.get("outcome")})
            save_life(result, feed=list(result.get("dialogue") or []))
            story.ending(result)

    threading.Thread(target=_run, name="matrix-resume-ui", daemon=True).start()
    return {"ok": True, "queued": recorded, "pending_was": pending}
