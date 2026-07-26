"""
Continuous Matrix daemon — background cycles with Operator LLM choosing HITLs.

Commands:
  matrix-daemon start [--cycles N] [--interval SEC] [--foreground]
  matrix-daemon stop
  matrix-daemon status
  matrix-daemon run     # foreground worker (used by start)
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from langgraph.types import Command

from matrix.characters import all_brain_models
from matrix.graph import get_graph, reset_graph_cache
from matrix.llm import operator_choose
from matrix.start_driver import INITIAL_STATE
from matrix.thread_store import new_thread_id

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
PID_FILE = _PROJECT_ROOT / ".matrix_daemon.pid"
LOG_FILE = _PROJECT_ROOT / ".matrix_daemon.log"

_HITL_OPTIONS: dict[str, list[str]] = {
    "bug": ["extract", "refuse"],
    "trust": ["trust", "walk"],
    "pill": ["red", "blue"],
    "steak": ["steak", "refuse"],
    "jump": ["jump", "hesitate"],
    "fight_or_flee": ["fight", "flee"],
    "radio": ["call", "silent"],
    "code": ["accept", "deny"],
}


def _log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} | {msg}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _interrupt_payload(result: dict) -> dict | None:
    interrupts = result.get("__interrupt__") if isinstance(result, dict) else None
    if not interrupts:
        return None
    first = interrupts[0]
    value = getattr(first, "value", first)
    return value if isinstance(value, dict) else {"message": str(value), "kind": "unknown"}


def _context_summary(values: dict) -> str:
    keys = [
        "location",
        "scene",
        "anomaly",
        "threat_level",
        "oracle_prophecy",
        "pursuit_status",
        "training_score",
        "pill_choice",
        "trust_choice",
    ]
    parts = [f"{k}={values.get(k)}" for k in keys if values.get(k) not in (None, "", [])]
    return "; ".join(parts)


def run_one_cycle(human_id: str = "neo") -> dict:
    """Run one full auto jack-in using Operator brain for every HITL."""
    reset_graph_cache()
    graph = get_graph()
    thread_id = new_thread_id(human_id)
    config = {"configurable": {"thread_id": thread_id}}
    state = {**INITIAL_STATE, "human_id": human_id}

    _log(f"CYCLE START thread={thread_id}")
    result = graph.invoke(state, config=config)

    safety = 0
    while True:
        safety += 1
        if safety > 40:
            _log("CYCLE ABORT — too many HITL steps")
            break

        payload = _interrupt_payload(result)
        if not payload:
            break

        kind = str(payload.get("kind") or "unknown")
        if kind == "oracle_question":
            choice = operator_choose(
                kind,
                ["Am I the One?", "What is the Matrix?", "Why am I here?"],
                _context_summary(result),
            )
        else:
            options = _HITL_OPTIONS.get(kind, ["red"])
            choice = operator_choose(kind, options, _context_summary(result))

        _log(f"OPERATOR brain chose kind={kind} → {choice}")
        result = graph.invoke(Command(resume=choice), config=config)

    _log(
        f"CYCLE END outcome={result.get('outcome')} "
        f"score={result.get('training_score')} "
        f"awakened={result.get('awakened')}"
    )
    return result


def run_daemon(cycles: int, interval: float) -> None:
    _log("DAEMON START")
    _log(f"Character brains: {all_brain_models()}")
    completed = 0
    while True:
        try:
            run_one_cycle("neo")
            completed += 1
        except Exception as exc:  # noqa: BLE001
            _log(f"CYCLE ERROR: {exc}")
        if cycles > 0 and completed >= cycles:
            _log(f"DAEMON STOP after {completed} cycle(s)")
            break
        _log(f"Sleeping {interval}s before next cycle…")
        time.sleep(interval)


def cmd_start(cycles: int, interval: float, foreground: bool) -> None:
    if PID_FILE.exists():
        pid = PID_FILE.read_text(encoding="utf-8").strip()
        print(f"Daemon already running? pid={pid} (matrix-daemon stop first)")
        sys.exit(1)

    if foreground:
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
        try:
            run_daemon(cycles, interval)
        finally:
            if PID_FILE.exists():
                PID_FILE.unlink()
        return

    cmd = [
        sys.executable,
        "-m",
        "matrix.daemon",
        "run",
        "--cycles",
        str(cycles),
        "--interval",
        str(interval),
    ]
    log_fh = LOG_FILE.open("a", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        cwd=str(_PROJECT_ROOT),
        stdout=log_fh,
        stderr=log_fh,
        start_new_session=True,
        env=os.environ.copy(),
    )
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    print(f"Daemon started pid={proc.pid}")
    print(f"Log: {LOG_FILE}")
    print("Stop with: uv run matrix-daemon stop")


def cmd_stop() -> None:
    if not PID_FILE.exists():
        print("No daemon PID file.")
        return
    pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to pid={pid}")
    except ProcessLookupError:
        print(f"Process {pid} not found.")
    finally:
        PID_FILE.unlink(missing_ok=True)


def cmd_status() -> None:
    if not PID_FILE.exists():
        print("Daemon: stopped")
        return
    pid = PID_FILE.read_text(encoding="utf-8").strip()
    running = Path(f"/proc/{pid}").exists() if sys.platform.startswith("linux") else True
    try:
        os.kill(int(pid), 0)
        running = True
    except OSError:
        running = False
    print(f"Daemon: {'running' if running else 'stale'} pid={pid}")
    print(f"Log: {LOG_FILE}")
    if LOG_FILE.exists():
        print("--- last 15 log lines ---")
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
        for line in lines[-15:]:
            print(line)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="matrix-daemon")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start", help="Start background daemon")
    p_start.add_argument("--cycles", type=int, default=0, help="0 = infinite")
    p_start.add_argument("--interval", type=float, default=30.0)
    p_start.add_argument("--foreground", action="store_true")

    p_run = sub.add_parser("run", help="Foreground worker loop")
    p_run.add_argument("--cycles", type=int, default=0)
    p_run.add_argument("--interval", type=float, default=30.0)

    sub.add_parser("stop", help="Stop background daemon")
    sub.add_parser("status", help="Show daemon status / recent logs")

    args = parser.parse_args(argv)
    if args.cmd == "start":
        cmd_start(args.cycles, args.interval, args.foreground)
    elif args.cmd == "run":
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
        try:
            run_daemon(args.cycles, args.interval)
        finally:
            PID_FILE.unlink(missing_ok=True)
    elif args.cmd == "stop":
        cmd_stop()
    elif args.cmd == "status":
        cmd_status()


if __name__ == "__main__":
    main()
