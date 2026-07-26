"""Story-mode cinematic narration."""

from __future__ import annotations


def scene(title: str) -> None:
    print()
    print(f"══ {title} ══")


def say(line: str) -> None:
    print(f"  {line}")


def beat(line: str) -> None:
    print(f"  → {line}")


def speak_as(who: str, line: str) -> None:
    print(f'  {who}: "{line}"')


def pause_for_interrupt(thread_id: str, kind: str, hint: str, values: dict) -> None:
    scene("THE MATRIX PAUSES")
    say(f"Pending decision: {kind}")
    say(hint)
    if values.get("oracle_prophecy"):
        say(f'Last prophecy: "{values["oracle_prophecy"]}"')
    if values.get("location"):
        say(f"Location: {values['location']}")
    print()
    say("You are the Operator (outside the simulation).")
    if kind == "oracle_question":
        beat('Resume with:  uv run matrix-resume "Am I the One?"')
    elif kind == "pill":
        beat("Resume with:  uv run matrix-resume red   # or blue")
    elif kind == "fight_or_flee":
        beat("Resume with:  uv run matrix-resume fight   # or flee")
    else:
        beat(f"Resume with:  uv run matrix-resume <answer>")
    beat(f"Thread saved:  {thread_id}")


def ending(result: dict) -> None:
    scene("OUTCOME")
    say(result.get("outcome") or "(no outcome)")
    say(f"Awakened: {result.get('awakened')}")
    say(f"Fight choice: {result.get('fight_choice') or 'n/a'}")
    say(f"Training score: {result.get('training_score', 0)}")
    say(f"Physics now: {', '.join(result.get('physics_rules') or [])}")
    say(f"Lives recorded outside the Matrix: {result.get('previous_lives')}")
    visited = result.get("locations_visited") or []
    if visited:
        say(f"Path: {' → '.join(visited)}")
    print()


def already_finished(thread_id: str, values: dict, requested: str) -> None:
    scene("ALREADY FINISHED")
    say(f"Thread {thread_id} already completed — no pending interrupt.")
    say(f"Last outcome: {values.get('outcome')}")
    say(f"Last pill: {values.get('pill_choice')} (you asked for: {requested})")
    print()
    beat("Start a new jack-in first:")
    beat("  uv run matrix-jack-in")
    print()
