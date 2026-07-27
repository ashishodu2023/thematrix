"""Live Operator Console — visual Matrix control room (browser UI)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATUS_FILE = _PROJECT_ROOT / ".matrix_status.json"
_DEFAULT_PORT = int(os.getenv("MATRIX_DASHBOARD_PORT", "8765"))

_lock = threading.Lock()
_server: ThreadingHTTPServer | None = None
_thread: threading.Thread | None = None
_seq = 0

# Slightly spread map so labels don't collide
_MAP_XY: dict[str, tuple[float, float]] = {
    "jack_point": (14, 78),
    "apartment": (30, 52),
    "club": (46, 70),
    "club_vip": (52, 58),
    "keymaker_hall": (70, 62),
    "oracle_apartment": (34, 24),
    "cafe": (58, 40),
    "hotel_lobby": (62, 74),
    "subway": (74, 54),
    "rooftop": (82, 22),
    "highway": (90, 66),
    "construct": (16, 16),
    "nebuchadnezzar": (8, 36),
    "zion_dock": (4, 48),
    "real_world": (8, 8),
}

_EDGES = [
    ("jack_point", "apartment"),
    ("jack_point", "subway"),
    ("jack_point", "hotel_lobby"),
    ("apartment", "club"),
    ("apartment", "oracle_apartment"),
    ("club", "cafe"),
    ("club", "hotel_lobby"),
    ("club", "club_vip"),
    ("club_vip", "keymaker_hall"),
    ("keymaker_hall", "hotel_lobby"),
    ("oracle_apartment", "cafe"),
    ("cafe", "subway"),
    ("hotel_lobby", "rooftop"),
    ("hotel_lobby", "subway"),
    ("subway", "highway"),
    ("rooftop", "highway"),
    ("construct", "nebuchadnezzar"),
    ("nebuchadnezzar", "real_world"),
    ("nebuchadnezzar", "zion_dock"),
]

_sse_lock = threading.Lock()
_sse_subs: list = []


def publish(status: dict[str, Any]) -> None:
    """Merge into latest status and write for the console to poll."""
    global _seq
    with _lock:
        current: dict[str, Any] = {}
        if STATUS_FILE.exists():
            try:
                current = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                current = {}
        # Append dialogue lines into a rolling feed (dedupe consecutive repeats)
        feed = list(current.get("feed") or [])
        for line in status.get("feed_append") or []:
            if not feed or feed[-1] != line:
                feed.append(line)
        feed = feed[-60:]
        merged = {**current, **status}
        if feed:
            merged["feed"] = feed
        merged.pop("feed_append", None)
        if "cast_style" not in merged:
            from matrix.cast import CAST_STYLE

            merged["cast_style"] = CAST_STYLE
        if merged.get("agent_positions"):
            from matrix.cast import ensure_cast

            merged["agent_positions"] = ensure_cast(
                {
                    "location": merged.get("location"),
                    "co_human_id": merged.get("co_human") or merged.get("co_human_id"),
                    "scene": merged.get("scene"),
                    "agent_positions": merged.get("agent_positions"),
                }
            )
        merged["map"] = {
            "nodes": [
                {"id": k, "x": xy[0], "y": xy[1]} for k, xy in _MAP_XY.items()
            ],
            "edges": [{"a": a, "b": b} for a, b in _EDGES],
        }
        _seq += 1
        merged["seq"] = _seq
        merged["updated_at"] = time.time()
        # Hunt path Neo → nearest Agent (for map overlay)
        try:
            from matrix.city_graph import shortest_path
            from matrix.hitl_bridge import read_pending

            loc = str(merged.get("location") or "")
            positions = merged.get("agent_positions") or {}
            best: list[str] = []
            for agent in ("smith", "jones", "brown"):
                where = positions.get(agent)
                if not where or not loc:
                    continue
                path = shortest_path(loc, where)
                if path and (not best or len(path) < len(best)):
                    best = path
            merged["hunt_path"] = best
            pending = read_pending()
            if pending and "hitl" not in status:
                merged["hitl"] = pending
            from matrix.config import config as cfg

            merged["tts"] = cfg.tts
            merged["difficulty"] = cfg.difficulty
            merged["seats"] = {
                "neo": {"label": "Neo", "url": f"/?seat=neo"},
                "trinity": {"label": "Trinity", "url": "/?seat=trinity"},
                "operator": {"label": "Operator", "url": "/?seat=operator"},
            }
        except Exception:  # noqa: BLE001
            pass
        STATUS_FILE.write_text(
            json.dumps(merged, indent=2, default=str), encoding="utf-8"
        )
        _broadcast(merged)


def publish_state(
    state: dict[str, Any],
    *,
    event: str = "",
    feed_lines: list[str] | None = None,
) -> None:
    """Push a graph state snapshot to the Operator Console."""
    from matrix.cast import CAST_STYLE, ensure_cast

    positions = ensure_cast(state)
    publish(
        {
            "status": event or state.get("scene") or "live",
            "scene": state.get("scene") or event or "live",
            "location": state.get("location"),
            "cycle": state.get("cycle"),
            "threat": state.get("threat_level"),
            "trace": state.get("trace_level"),
            "meta": state.get("meta_policy"),
            "outcome": state.get("outcome"),
            "awakened": state.get("awakened"),
            "pill": state.get("pill_choice"),
            "training_score": state.get("training_score"),
            "pursuit_status": state.get("pursuit_status"),
            "showdown_status": state.get("showdown_status"),
            "world_tick": state.get("world_tick"),
            "agent_positions": positions,
            "cast_style": CAST_STYLE,
            "faction_scoreboard": state.get("faction_scoreboard") or {},
            "sticky": state.get("sticky_flags") or {},
            "physics": state.get("physics_rules") or [],
            "sector_heat": state.get("sector_heat") or {},
            "phone_taps": list(state.get("phone_taps") or [])[-8:],
            "hardline_cooldown": state.get("hardline_cooldown") or 0,
            "co_human": state.get("co_human_id") or "",
            "human_id": state.get("human_id") or "neo",
            "feed_append": list(feed_lines or []),
            "hint": "",
            "tracks": list(state.get("active_tracks") or [])[-8:],
        }
    )


def read_status() -> dict[str, Any]:
    if not STATUS_FILE.exists():
        return {
            "status": "idle",
            "hint": "Run: uv run matrix-daemon start — then watch this console",
            "map": {
                "nodes": [
                    {"id": k, "x": xy[0], "y": xy[1]} for k, xy in _MAP_XY.items()
                ],
                "edges": [{"a": a, "b": b} for a, b in _EDGES],
            },
        }
    try:
        data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        if "map" not in data:
            data["map"] = {
                "nodes": [
                    {"id": k, "x": xy[0], "y": xy[1]} for k, xy in _MAP_XY.items()
                ],
                "edges": [{"a": a, "b": b} for a, b in _EDGES],
            }
        return data
    except Exception:  # noqa: BLE001
        return {"status": "error"}


_CONSOLE_HTML = Path(__file__).resolve().parent / "static" / "console.html"


def _broadcast(data: dict[str, Any]) -> None:
    import queue as queue_mod

    dead: list = []
    with _sse_lock:
        subs = list(_sse_subs)
    for q in subs:
        try:
            q.put_nowait(data)
        except Exception:  # noqa: BLE001
            dead.append(q)
    if dead:
        with _sse_lock:
            for q in dead:
                if q in _sse_subs:
                    _sse_subs.remove(q)


def _page_html(port: int) -> bytes:
    html = _CONSOLE_HTML.read_text(encoding="utf-8")
    return html.replace("%PORT%", str(port)).encode("utf-8")


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or 0)
    raw = handler.rfile.read(length) if length else b"{}"
    try:
        return json.loads(raw.decode("utf-8") or "{}")
    except Exception:  # noqa: BLE001
        return {}


class _Handler(BaseHTTPRequestHandler):
    port: int = _DEFAULT_PORT

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _json(self, payload: dict[str, Any], code: int = 200) -> None:
        body = json.dumps(payload, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        data = _read_json_body(self)
        if path == "/api/choice":
            try:
                from matrix.operator_api import resume_choice

                out = resume_choice(
                    str(data.get("choice") or ""),
                    seat=str(data.get("seat") or "operator"),
                )
                self._json(out)
            except Exception as exc:  # noqa: BLE001
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        if path == "/api/preset":
            try:
                from matrix import config as matrix_config
                from matrix.presets import apply_preset

                name = apply_preset(str(data.get("name") or "balanced"))
                matrix_config.config = matrix_config.Config.from_env()
                publish({"difficulty": name, "feed_append": [f"Difficulty → {name}"]})
                self._json({"ok": True, "difficulty": name})
            except Exception as exc:  # noqa: BLE001
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        if path == "/api/speak":
            try:
                from matrix.voice import browser_hints, speak, stop

                if data.get("stop"):
                    stop()
                    self._json({"ok": True, "stopped": True})
                    return
                who = str(data.get("who") or "Operator")
                text = str(data.get("text") or "")
                out = speak(who, text, interrupt=bool(data.get("interrupt", False)))
                out["hints"] = browser_hints(who)
                self._json(out)
            except Exception as exc:  # noqa: BLE001
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        if path == "/api/command":
            try:
                from matrix.operator_commands import apply_command

                # Merge last published state as base
                base = read_status()
                state = {
                    "location": base.get("location"),
                    "agent_positions": base.get("agent_positions") or {},
                    "trace_level": base.get("trace"),
                    "hardline_cooldown": base.get("hardline_cooldown") or 0,
                    "sector_heat": base.get("sector_heat") or {},
                    "phone_taps": base.get("phone_taps") or [],
                    "training_skills": base.get("training_skills") or [],
                    "training_score": base.get("training_score") or 0,
                    "sentinel_alert": base.get("sentinel_alert"),
                    "faction_scoreboard": base.get("faction_scoreboard") or {},
                }
                out = apply_command(
                    state,
                    command=str(data.get("command") or ""),
                    target=str(data.get("target") or ""),
                    seat=str(data.get("seat") or "operator"),
                )
                if out.get("ok"):
                    feed = []
                    if out.get("feed_line"):
                        feed.append(out["feed_line"])
                    publish(
                        {
                            "location": out.get("location", state.get("location")),
                            "agent_positions": out.get(
                                "agent_positions", state.get("agent_positions")
                            ),
                            "trace": out.get("trace_level", state.get("trace_level")),
                            "hardline_cooldown": out.get(
                                "hardline_cooldown", state.get("hardline_cooldown")
                            ),
                            "sector_heat": out.get("sector_heat", state.get("sector_heat")),
                            "phone_taps": list(state.get("phone_taps") or [])
                            + list(out.get("phone_taps") or []),
                            "training_score": out.get(
                                "training_score", state.get("training_score")
                            ),
                            "faction_scoreboard": out.get("faction_scoreboard")
                            or state.get("faction_scoreboard"),
                            "feed_append": feed,
                            "status": "operator_command",
                        }
                    )
                self._json(out)
            except Exception as exc:  # noqa: BLE001
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        self._json({"ok": False, "error": "not found"}, 404)

    def do_GET(self) -> None:  # noqa: N802
        import queue as queue_mod
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path.startswith("/api/status"):
            self._json(read_status())
            return

        if path.startswith("/api/metrics"):
            from matrix.metrics import collect_metrics

            hid = (qs.get("human") or ["neo"])[0]
            self._json(collect_metrics(hid))
            return

        if path.startswith("/api/replays"):
            from matrix.replay import list_replays, load_replay

            rid = (qs.get("id") or [None])[0]
            if rid:
                data = load_replay(str(rid))
                if not data:
                    self._json({"ok": False, "error": "missing"}, 404)
                    return
                self._json(data)
                return
            self._json({"replays": list_replays()})
            return

        if path.startswith("/api/events"):
            q: queue_mod.Queue = queue_mod.Queue(maxsize=16)
            with _sse_lock:
                _sse_subs.append(q)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                # initial snapshot
                snap = json.dumps(read_status(), default=str)
                self.wfile.write(f"data: {snap}\n\n".encode())
                self.wfile.flush()
                while True:
                    try:
                        item = q.get(timeout=20)
                        self.wfile.write(
                            f"data: {json.dumps(item, default=str)}\n\n".encode()
                        )
                        self.wfile.flush()
                    except queue_mod.Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except Exception:  # noqa: BLE001
                pass
            finally:
                with _sse_lock:
                    if q in _sse_subs:
                        _sse_subs.remove(q)
            return

        body = _page_html(self.port)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def console_url(port: int | None = None) -> str:
    return f"http://127.0.0.1:{port or _DEFAULT_PORT}"


def start(port: int | None = None) -> None:
    global _server, _thread
    if _thread and _thread.is_alive():
        return
    p = port or _DEFAULT_PORT
    _Handler.port = p

    def _run() -> None:
        global _server
        # Threading: SSE /api/events holds a connection open; a single-thread
        # HTTPServer would block /api/status polls → console "link down".
        _server = ThreadingHTTPServer(("127.0.0.1", p), _Handler)
        _server.allow_reuse_address = True
        _server.daemon_threads = True
        _server.serve_forever()

    _thread = threading.Thread(target=_run, name="matrix-dashboard", daemon=True)
    _thread.start()


def wait_ready(port: int | None = None, timeout: float = 5.0) -> bool:
    """Poll until the console HTTP server answers."""
    url = console_url(port) + "/api/status"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.4) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.1)
    return False


def open_firefox(port: int | None = None, *, path: str = "/") -> bool:
    """Open the Operator Console in Firefox (falls back to default browser)."""
    url = console_url(port) + (path if path.startswith("/") else "/" + path)
    wait_ready(port)

    # macOS — prefer Firefox.app
    if shutil.which("open"):
        try:
            r = subprocess.run(
                ["open", "-a", "Firefox", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if r.returncode == 0:
                return True
        except OSError:
            pass
        try:
            r = subprocess.run(
                ["open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if r.returncode == 0:
                return True
        except OSError:
            pass

    # Linux / generic Firefox binary
    for bin_name in ("firefox", "firefox-bin", "firefox-esr"):
        if shutil.which(bin_name):
            try:
                subprocess.Popen(
                    [bin_name, "--new-tab", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except OSError:
                continue

    try:
        import webbrowser

        webbrowser.open(url)
        return True
    except Exception:  # noqa: BLE001
        return False


def start_console(*, port: int | None = None, open_browser: bool = True) -> str:
    """Start dashboard HTTP server and optionally open Firefox (multi-seat)."""
    start(port)
    url = console_url(port)
    publish(
        {
            "status": "idle",
            "hint": "Backend starting — console will fill with live signal.",
            "feed_append": ["Operator console online.", "Waiting for jack-in…"],
        }
    )
    if open_browser and os.getenv("MATRIX_OPEN_BROWSER", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }:
        # One window by default (switch seats in-toolbar). Set MATRIX_OPEN_SEATS=operator,trinity for both.
        seats = [
            s.strip()
            for s in os.getenv("MATRIX_OPEN_SEATS", "operator").split(",")
            if s.strip()
        ] or ["operator"]
        for seat in seats:
            open_firefox(port, path=f"/?seat={seat}")
    return url


def stop() -> None:
    global _server
    if _server:
        _server.shutdown()
        _server = None


def main() -> None:
    from matrix.theme import banner, out

    banner()
    url = start_console(open_browser=True)
    out(f"Operator Console → {url}", bold=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        stop()


if __name__ == "__main__":
    main()
