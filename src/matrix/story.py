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
    scene("THE MATRIX PAUSES")
    say(f"Pending decision: {kind}")
    say(hint)
    if values.get("oracle_prophecy"):
        say(f'Last prophecy: "{values["oracle_prophecy"]}"')
    if values.get("location"):
        say(f"Location: {values['location']}")
    print()
    say("You are the Operator (outside the simulation).")
    beat(f"Resume with:  {_RESUME_HINTS.get(kind, 'uv run matrix-resume <answer>')}")
    beat(f"Thread saved:  {thread_id}")


def ending(result: dict) -> None:
    scene("OUTCOME")
    say(result.get("outcome") or "(no outcome)")
    say(f"Cycle: {result.get('cycle')}")
    say(f"Awakened: {result.get('awakened')}")
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
    say(f"Lives recorded outside the Matrix: {result.get('previous_lives')}")
    visited = list(dict.fromkeys(result.get("locations_visited") or []))
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
