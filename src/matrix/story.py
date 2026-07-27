"""Story-mode cinematic narration — Matrix green on black + Operator Console."""

from __future__ import annotations

from matrix import rain as matrix_rain
from matrix import theme
from matrix.awareness import current_state

# Last known graph snapshot (survives when ContextVar briefly unbound)
_LAST_STATE: dict = {}


def note_state(state: dict | None) -> None:
    """Remember the latest Matrix state for console live updates."""
    global _LAST_STATE
    if state:
        _LAST_STATE = dict(state)


def _push(extra: dict | None = None) -> None:
    try:
        from matrix import dashboard

        payload = dict(extra or {})
        state = current_state() or _LAST_STATE
        feed = list(payload.get("feed_append") or [])
        event = str(payload.get("status") or "")
        if state:
            if event and not state.get("scene"):
                # keep scene from event titles when node hasn't set it yet
                pass
            dashboard.publish_state(
                state,
                event=event,
                feed_lines=feed,
            )
        else:
            dashboard.publish(payload)
    except Exception:  # noqa: BLE001
        pass


def scene(title: str) -> None:
    theme.out()
    matrix_rain.decode_title(title)
    _push(
        {
            "feed_append": [f"══ {title} ══"],
            "status": title.lower().replace(" ", "_"),
        }
    )


def say(line: str) -> None:
    theme.out_styled(f"  {line}")
    _push({"feed_append": [line]})


def beat(line: str) -> None:
    theme.out_styled(f"  → {line}", dim=True)
    _push({"feed_append": [f"→ {line}"]})


def speak_as(who: str, line: str) -> None:
    theme.out_styled(f"{who}:")
    theme.out_styled(f'"{line}"')
    _push({"feed_append": [f'{who}: "{line}"']})


_RESUME_HINTS = {
    "bug": "uv run matrix-resume extract   # or refuse",
    "trust": "uv run matrix-resume trust   # or walk",
    "oracle_question": 'uv run matrix-resume "Am I the One?"',
    "pill": "uv run matrix-resume red   # or blue",
    "steak": "uv run matrix-resume refuse   # or steak",
    "jump": "uv run matrix-resume jump   # or hesitate",
    "fight_or_flee": "uv run matrix-resume fight   # or flee",
    "radio": "uv run matrix-resume call   # or silent",
    "code": "uv run matrix-resume accept   # or deny",
}


def pause_for_interrupt(thread_id: str, kind: str, hint: str, values: dict) -> None:
    note_state(values)
    try:
        from matrix.hitl_bridge import publish_pending
        from matrix import dashboard

        hitl = publish_pending(
            thread_id=thread_id, kind=str(kind), message=str(hint or "")
        )
        dashboard.publish({"status": "hitl", "hitl": hitl, "thread_id": thread_id})
    except Exception:  # noqa: BLE001
        pass
    matrix_rain.rain(0.35)
    scene("THE MATRIX PAUSES")
    say(f"Pending decision: {kind}")
    say(hint)
    if values.get("oracle_prophecy"):
        say(f'Last prophecy: "{values["oracle_prophecy"]}"')
    if values.get("location"):
        say(f"Location: {values['location']}")
    if values.get("trace_level") is not None:
        say(f"Trace level: {values.get('trace_level')}")
    if values.get("meta_policy"):
        say(f"Meta policy: {values.get('meta_policy')}")
    theme.out()
    say("You are the Operator (outside the simulation).")
    if values.get("co_human_id"):
        say(f"Co-pilot seat: {values['co_human_id']}")
    beat(f"Resume with:  {_RESUME_HINTS.get(kind, 'uv run matrix-resume <answer>')}")
    beat(f"Thread saved:  {thread_id}")


def ending(result: dict) -> None:
    note_state(result)
    scene("OUTCOME")
    say(result.get("outcome") or "(no outcome)")
    say(f"Cycle: {result.get('cycle')}")
    say(f"Awakened: {result.get('awakened')}")
    say(f"Meta policy: {result.get('meta_policy') or 'n/a'}")
    say(f"Trace: {result.get('trace_level', 0)}")
    say(f"Bug: {result.get('bug_choice') or 'n/a'}")
    say(f"Trust: {result.get('trust_choice') or 'n/a'}")
    say(f"Steak: {result.get('steak_choice') or 'n/a'}")
    say(f"Jump: {result.get('jump_choice') or 'n/a'}")
    say(f"Fight: {result.get('fight_choice') or 'n/a'}")
    say(f"Radio: {result.get('radio_choice') or 'n/a'}")
    say(f"Code: {result.get('code_choice') or 'n/a'}")
    say(f"Showdown: {result.get('showdown_status') or 'n/a'}")
    say(f"Training score: {result.get('training_score', 0)}")
    say(f"Physics now: {', '.join(result.get('physics_rules') or [])}")
    say(f"Sticky: {result.get('sticky_flags') or {}}")
    say(f"Lives recorded outside the Matrix: {result.get('previous_lives')}")
    visited = list(dict.fromkeys(result.get("locations_visited") or []))
    if visited:
        say(f"Path: {' → '.join(visited)}")
    theme.out()


def already_finished(thread_id: str, values: dict, requested: str) -> None:
    scene("ALREADY FINISHED")
    say(f"Thread {thread_id} already completed — no pending interrupt.")
    say(f"Last outcome: {values.get('outcome')}")
    say(f"Last pill: {values.get('pill_choice')} (you asked for: {requested})")
    theme.out()
    beat("Start a new jack-in first:")
    beat("  uv run matrix-jack-in")
    theme.out()
