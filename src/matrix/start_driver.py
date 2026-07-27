"""
Jack into the Matrix.

Default: CONTINUOUS backend + Operator Console + Firefox in one command.
Use --interactive to pause for human choices.
Use --no-browser to skip opening Firefox.
"""

from __future__ import annotations

import argparse

from matrix import story
from matrix import theme
from matrix.graph import get_graph, reset_graph_cache
from matrix.thread_store import new_thread_id

INITIAL_STATE = {
    "human_id": "neo",
    "co_human_id": "",
    "city": "Mega City",
    "cycle": 1,
    "location": "",
    "scene": "",
    "physics_rules": ["gravity", "solidity", "causality", "spoon_exists"],
    "anomaly": "spoon",
    "threat_level": 4,
    "architect_plan": "",
    "oracle_question": "",
    "oracle_prophecy": "",
    "agent_names": ["Smith", "Jones", "Brown"],
    "current_agent": "",
    "agent_reports": [],
    "sectors_scanned": [],
    "spoon_exists": True,
    "reality_rewritten": False,
    "pursuit_round": 0,
    "pursuit_status": "idle",
    "pursuit_log": [],
    "pending_decision": "",
    "pill_choice": "",
    "trust_choice": "",
    "bug_choice": "",
    "steak_choice": "",
    "jump_choice": "",
    "fight_choice": "",
    "radio_choice": "",
    "code_choice": "",
    "key_choice": "",
    "awakened": False,
    "bug_implanted": False,
    "sentinel_alert": False,
    "training_skills": [],
    "training_score": 0,
    "showdown_round": 0,
    "showdown_status": "",
    "dream_note": "",
    "briefing": "",
    "dialogue": [],
    "events": [],
    "log": [],
    "outcome": "",
    "previous_lives": 0,
    "locations_visited": [],
    "agent_memory": [],
    "character_actions": [],
    "world_tick": 0,
    "trace_level": 0.0,
    "hardline_cooldown": 0,
    "phone_taps": [],
    "sector_heat": {},
    "agent_positions": {},
    "sticky_flags": {},
    "meta_policy": "",
    "faction_scoreboard": {},
    "active_tracks": [],
}


def _interrupt_payload(result: dict) -> dict:
    interrupts = result.get("__interrupt__") if isinstance(result, dict) else None
    if not interrupts:
        return {}
    first = interrupts[0]
    value = getattr(first, "value", first)
    return value if isinstance(value, dict) else {"message": str(value)}


def _boot_console(open_browser: bool) -> None:
    from matrix import dashboard
    from matrix.config import config as matrix_config

    if not matrix_config.dashboard:
        return
    url = dashboard.start_console(open_browser=open_browser)
    theme.out(f"Operator Console → {url}", bold=True)
    if open_browser:
        theme.out("Opening Firefox…")


def _run_interactive(args: argparse.Namespace) -> None:
    reset_graph_cache()
    state = {
        **INITIAL_STATE,
        "human_id": args.human,
        "co_human_id": args.co_human,
    }
    thread_id = new_thread_id(state["human_id"])
    config = {"configurable": {"thread_id": thread_id}}
    graph = get_graph()

    theme.banner()
    theme.out("Interactive mode — will pause at HITLs", bold=True)
    theme.out(f"Fresh thread: {thread_id}")
    if args.co_human:
        theme.out(f"Co-pilot: {args.co_human}")
    _boot_console(open_browser=not args.no_browser)
    theme.out()

    try:
        result = graph.invoke(state, config=config)
    except Exception as exc:  # noqa: BLE001
        from matrix.llm import OllamaUnavailableError

        if isinstance(exc, OllamaUnavailableError) or "Ollama" in str(exc):
            print()
            print(str(exc))
            raise SystemExit(1) from exc
        raise

    payload = _interrupt_payload(result)
    if payload:
        kind = payload.get("kind") or result.get("pending_decision") or "unknown"
        hint = payload.get("message") or payload.get("hint") or ""
        story.pause_for_interrupt(thread_id, kind, hint, result)
    else:
        story.ending(result)


def _run_continuous(args: argparse.Namespace) -> None:
    from matrix.daemon import run_daemon

    theme.banner()
    theme.out("ONE COMMAND — backend + Operator Console", bold=True)
    theme.out("CONTINUOUS mode — Operator auto-picks every choice")
    from matrix.config import config as matrix_config

    if matrix_config.fast:
        theme.out("FAST mode on (≤7B brains, no rain/stream) — MATRIX_FAST=0 for cinematic")
    theme.out("Never stops until Ctrl+C  (or: uv run matrix-daemon stop)")
    if args.co_human:
        theme.out(f"Co-pilot: {args.co_human}")
    _boot_console(open_browser=not args.no_browser)
    theme.out()

    run_daemon(
        cycles=args.cycles,
        interval=args.interval,
        co_human_id=args.co_human or "trinity",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="matrix-jack-in",
        description=(
            "Jack into the Matrix: starts the simulation backend + Operator "
            "Console and opens Firefox (continuous by default)."
        ),
    )
    parser.add_argument(
        "--co-human",
        default="trinity",
        help="Second jack-in seat (default: trinity)",
    )
    parser.add_argument("--human", default="neo", help="Primary human_id")
    parser.add_argument(
        "--console",
        action="store_true",
        help="(Deprecated) Console always starts; kept for compatibility",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open Firefox (console still starts)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Pause at HITLs for human choices (disables continuous)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=0,
        help="Continuous mode: 0 = infinite (default), N = stop after N lives",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.0,
        help="Seconds between continuous lives (default 0)",
    )
    parser.add_argument(
        "--difficulty",
        default="",
        choices=["", "cinematic", "balanced", "fast", "tiny"],
        help="Difficulty preset (sets pace/models/HITL wait)",
    )
    args = parser.parse_args(argv)

    if args.difficulty:
        from matrix import config as matrix_config
        from matrix.presets import apply_preset

        apply_preset(args.difficulty)
        matrix_config.config = matrix_config.Config.from_env()

    if args.interactive:
        _run_interactive(args)
    else:
        _run_continuous(args)


if __name__ == "__main__":
    main()
