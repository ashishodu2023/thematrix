"""Human-like TTS for the Operator Console.

On macOS, prefers the system ``say`` command with curated character voices.
Lines are **queued** and spoken to completion (no mid-sentence cuts) unless
explicitly stopped.
"""

from __future__ import annotations

import platform
import queue
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass
from typing import Any

_lock = threading.Lock()
_proc: subprocess.Popen[bytes] | None = None
_say_available: bool | None = None
# name -> list of language tags from ``say -v ?`` (e.g. en_US)
_installed_voices: dict[str, list[str]] | None = None

_MAX_QUEUE = 8  # drop oldest pending if feed outruns speech
_speech_q: queue.Queue[tuple[str, str] | None] = queue.Queue()
_worker_started = False
_worker_lock = threading.Lock()


@dataclass(frozen=True)
class VoiceProfile:
    """Character speaking style for macOS ``say`` and browser hints."""

    voices: tuple[str, ...]  # preferred macOS voice names, first match wins
    rate: int  # words per minute for ``say -r``
    browser_rate: float
    browser_pitch: float
    gender: str  # hint for browser voice picker


# Prefer Samantha / Daniel / Karen / Moira / Reed — widely installed & natural.
CHAR_VOICES: dict[str, VoiceProfile] = {
    "neo": VoiceProfile(("Reed", "Daniel", "Alex", "Tom"), 175, 0.95, 0.98, "male"),
    "trinity": VoiceProfile(("Samantha", "Allison", "Ava", "Susan", "Karen"), 185, 1.0, 1.08, "female"),
    "morpheus": VoiceProfile(("Daniel", "Reed", "Alex", "Oliver"), 155, 0.88, 0.82, "male"),
    "agent smith": VoiceProfile(("Daniel", "Reed", "Alex", "Tom"), 155, 0.9, 0.72, "male"),
    "smith": VoiceProfile(("Daniel", "Reed", "Alex", "Tom"), 155, 0.9, 0.72, "male"),
    "oracle": VoiceProfile(("Karen", "Moira", "Fiona", "Samantha"), 165, 0.9, 1.12, "female"),
    "architect": VoiceProfile(("Daniel", "Reed", "Oliver", "Alex"), 145, 0.85, 0.68, "male"),
    "cypher": VoiceProfile(("Reed", "Daniel", "Alex"), 172, 0.98, 0.9, "male"),
    "spoon boy": VoiceProfile(("Samantha", "Karen", "Junior"), 195, 1.08, 1.25, "child"),
    "merovingian": VoiceProfile(("Thomas", "Daniel", "Reed"), 170, 0.95, 0.88, "male"),
    "keymaker": VoiceProfile(("Daniel", "Reed", "Alex"), 150, 0.87, 0.85, "male"),
    "niobe": VoiceProfile(("Samantha", "Karen", "Moira"), 180, 0.98, 1.05, "female"),
    "persephone": VoiceProfile(("Moira", "Samantha", "Karen"), 170, 0.95, 1.1, "female"),
    "seraph": VoiceProfile(("Daniel", "Reed", "Alex"), 165, 0.92, 0.95, "male"),
    "tank": VoiceProfile(("Reed", "Daniel", "Alex"), 185, 1.02, 0.95, "male"),
    "operator": VoiceProfile(("Samantha", "Daniel", "Karen"), 180, 0.98, 1.0, "neutral"),
    "sentinel": VoiceProfile(("Zarvox", "Reed"), 200, 1.15, 0.5, "robot"),
}


def _normalize_who(who: str) -> str:
    w = who.strip().lower()
    w = re.sub(r"^agent\s+", "", w)
    w = re.sub(r"\s*\(.*\)$", "", w).strip()
    return w


def profile_for(who: str) -> VoiceProfile:
    key = _normalize_who(who)
    if key in CHAR_VOICES:
        return CHAR_VOICES[key]
    for name, prof in CHAR_VOICES.items():
        if name in key or key in name:
            return prof
    return CHAR_VOICES["operator"]


def say_available() -> bool:
    global _say_available
    if _say_available is None:
        _say_available = platform.system() == "Darwin" and shutil.which("say") is not None
    return bool(_say_available)


def _list_say_voices() -> dict[str, list[str]]:
    global _installed_voices
    if _installed_voices is not None:
        return _installed_voices
    voices: dict[str, list[str]] = {}
    if not say_available():
        _installed_voices = voices
        return voices
    try:
        out = subprocess.check_output(["say", "-v", "?"], text=True, stderr=subprocess.DEVNULL, timeout=5)
        for line in out.splitlines():
            if "#" in line:
                left = line.split("#", 1)[0].strip()
            else:
                left = line.strip()
            if not left:
                continue
            parts = left.split()
            if len(parts) < 2:
                continue
            lang = parts[-1]
            name = " ".join(parts[:-1])
            if not name:
                continue
            voices.setdefault(name, []).append(lang)
    except Exception:  # noqa: BLE001
        pass
    _installed_voices = voices
    return voices


def _english_ok(langs: list[str]) -> bool:
    return any(lg.lower().startswith("en") for lg in langs)


def pick_say_voice(who: str) -> str:
    prof = profile_for(who)
    installed = _list_say_voices()
    for v in prof.voices:
        langs = installed.get(v) or []
        if langs and _english_ok(langs):
            return v
        if langs and v == "Thomas":
            return v
    for preferred in ("Samantha", "Daniel", "Karen", "Moira", "Reed", "Alex", "Allison", "Ava"):
        langs = installed.get(preferred) or []
        if langs and _english_ok(langs):
            return preferred
    return prof.voices[0]


def humanize_text(text: str) -> str:
    """Light punctuation so speech breathes more naturally."""
    t = " ".join(str(text or "").split()).strip()
    if not t:
        return ""
    t = re.sub(r"\bMr\.\s*", "Mister ", t)
    t = re.sub(r"\bMs\.\s*", "Miss ", t)
    t = re.sub(r"\bDr\.\s*", "Doctor ", t)
    t = re.sub(r"\s*[—–]\s*", ", ", t)
    t = re.sub(r"\s*;\s*", ", ", t)
    if len(t) > 320:
        t = t[:317].rsplit(" ", 1)[0] + "…"
    return t


def _kill_proc() -> None:
    global _proc
    with _lock:
        if _proc and _proc.poll() is None:
            try:
                _proc.terminate()
            except Exception:  # noqa: BLE001
                pass
            try:
                _proc.wait(timeout=0.4)
            except Exception:  # noqa: BLE001
                try:
                    _proc.kill()
                except Exception:  # noqa: BLE001
                    pass
        _proc = None


def _drain_queue() -> None:
    while True:
        try:
            _speech_q.get_nowait()
            _speech_q.task_done()
        except queue.Empty:
            break


def _speak_blocking(who: str, text: str) -> None:
    """Run ``say`` and wait until the line finishes."""
    global _proc
    voice = pick_say_voice(who)
    rate = profile_for(who).rate
    cmd = ["say", "-v", voice, "-r", str(rate), text]
    with _lock:
        _proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc = _proc
    try:
        proc.wait()
    finally:
        with _lock:
            if _proc is proc:
                _proc = None


def _worker() -> None:
    while True:
        item = _speech_q.get()
        try:
            if item is None:
                continue
            who, text = item
            if not text:
                continue
            _speak_blocking(who, text)
        except Exception:  # noqa: BLE001
            pass
        finally:
            _speech_q.task_done()


def _ensure_worker() -> None:
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        t = threading.Thread(target=_worker, name="matrix-tts", daemon=True)
        t.start()
        _worker_started = True


def stop() -> None:
    """Cancel current speech and clear the queue."""
    _drain_queue()
    _kill_proc()


def speak(who: str, text: str, *, interrupt: bool = False) -> dict[str, Any]:
    """Enqueue a line for macOS ``say``. Completes before the next line plays.

    Set ``interrupt=True`` only to cut the current line (e.g. TTS toggle off).
    """
    cleaned = humanize_text(text)
    if not cleaned:
        return {"ok": False, "error": "empty"}
    if not say_available():
        return {"ok": False, "fallback": "browser", "error": "say unavailable"}

    _ensure_worker()
    if interrupt:
        stop()

    # Cap backlog so fast mode doesn't pile up minutes of dialogue
    while _speech_q.qsize() >= _MAX_QUEUE:
        try:
            _speech_q.get_nowait()
            _speech_q.task_done()
        except queue.Empty:
            break

    voice = pick_say_voice(who)
    rate = profile_for(who).rate
    _speech_q.put((who, cleaned))
    return {
        "ok": True,
        "engine": "say",
        "queued": True,
        "queue_size": _speech_q.qsize(),
        "voice": voice,
        "rate": rate,
        "who": who,
        "text": cleaned,
    }


def browser_hints(who: str) -> dict[str, Any]:
    """Hints the console uses when falling back to SpeechSynthesis."""
    prof = profile_for(who)
    return {
        "preferred_voices": list(prof.voices),
        "rate": prof.browser_rate,
        "pitch": prof.browser_pitch,
        "gender": prof.gender,
        "lang": "en-US",
    }
