"""Export a finished life as a TV-episode style artifact (HTML + script)."""

from __future__ import annotations

import html
import json
import time
from pathlib import Path
from typing import Any

from matrix.replay import list_replays, load_replay

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_EP_DIR = _PROJECT_ROOT / ".matrix_episodes"


def _dir() -> Path:
    _EP_DIR.mkdir(parents=True, exist_ok=True)
    return _EP_DIR


def _acts_from_feed(feed: list[str]) -> list[dict[str, Any]]:
    acts: list[dict[str, Any]] = []
    current = {"title": "PROLOGUE", "lines": []}
    for raw in feed:
        s = str(raw or "").strip()
        if not s:
            continue
        if s.startswith("══") or "ACT " in s.upper():
            if current["lines"]:
                acts.append(current)
            title = s.replace("═", "").strip() or "BEAT"
            current = {"title": title[:80], "lines": []}
            continue
        current["lines"].append(s)
    if current["lines"]:
        acts.append(current)
    return acts or [{"title": "THE MATRIX", "lines": feed[-40:]}]


def export_episode(replay_id: str | None = None) -> dict[str, Any]:
    """Build an HTML episode page + dialogue script from a replay."""
    rid = replay_id
    if not rid:
        items = list_replays(limit=1)
        if not items:
            return {"ok": False, "error": "no replays saved yet"}
        rid = str(items[0]["id"])
    data = load_replay(str(rid))
    if not data:
        return {"ok": False, "error": f"replay {rid} missing"}

    feed = list(data.get("feed") or data.get("dialogue") or [])
    acts = _acts_from_feed(feed)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    cycle = data.get("cycle") or 0
    outcome = str(data.get("outcome") or "unknown")[:120]
    base = f"episode-c{cycle}-{stamp}"
    html_path = _dir() / f"{base}.html"
    script_path = _dir() / f"{base}.script.txt"
    meta_path = _dir() / f"{base}.json"

    script_lines = [
        f"THE MATRIX — Episode (cycle {cycle})",
        f"Outcome: {outcome}",
        f"Pill: {data.get('pill')} · Awakened: {data.get('awakened')}",
        "",
    ]
    for act in acts:
        script_lines.append(f"## {act['title']}")
        script_lines.extend(act["lines"])
        script_lines.append("")

    script_path.write_text("\n".join(script_lines), encoding="utf-8")

    body_acts = []
    for act in acts:
        lis = "".join(
            f"<p class='line'>{html.escape(str(x))}</p>" for x in act["lines"][-30:]
        )
        body_acts.append(
            f"<section class='act'><h2>{html.escape(act['title'])}</h2>{lis}</section>"
        )

    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>THE MATRIX — Episode c{html.escape(str(cycle))}</title>
<style>
  body {{ margin:0; background:#010302; color:#39FF14;
    font-family: ui-monospace, Menlo, monospace; padding:2rem; }}
  h1 {{ letter-spacing:0.25em; }}
  h2 {{ color:#7CFF7C; border-bottom:1px solid #13401c; padding-bottom:0.35rem; }}
  .meta {{ color:#9ad9a3; margin-bottom:1.5rem; }}
  .act {{ margin:1.5rem 0; }}
  .line {{ line-height:1.45; color:#7CFF7C; }}
  .controls {{ position:sticky; top:0; background:#010302ee; padding:0.5rem 0; }}
  button {{ background:#041008; color:#39FF14; border:1px solid #13401c;
    font-family:inherit; padding:0.4rem 0.8rem; cursor:pointer; }}
</style></head><body>
<h1>THE MATRIX</h1>
<div class="meta">Cycle {html.escape(str(cycle))} · {html.escape(outcome)}</div>
<div class="controls">
  <button type="button" id="play">Play as audio drama</button>
  <button type="button" id="stop">Stop</button>
</div>
{"".join(body_acts)}
<script>
const lines = {json.dumps([x for a in acts for x in a["lines"][-30:]])};
let i = 0; let speaking = false;
document.getElementById('play').onclick = () => {{
  if (!window.speechSynthesis) return alert('No speechSynthesis');
  speaking = true; i = 0;
  const next = () => {{
    if (!speaking || i >= lines.length) return;
    const u = new SpeechSynthesisUtterance(String(lines[i++]));
    u.rate = 0.95; u.onend = next; speechSynthesis.speak(u);
  }};
  next();
}};
document.getElementById('stop').onclick = () => {{
  speaking = false; speechSynthesis.cancel();
}};
</script>
</body></html>
"""
    html_path.write_text(page, encoding="utf-8")
    meta = {
        "id": base,
        "replay_id": rid,
        "cycle": cycle,
        "outcome": outcome,
        "html": str(html_path.name),
        "script": str(script_path.name),
        "acts": len(acts),
        "lines": sum(len(a["lines"]) for a in acts),
        "saved_at": time.time(),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {
        "ok": True,
        **meta,
        "html_path": str(html_path),
        "script_path": str(script_path),
        "url": f"/episodes/{html_path.name}",
    }


def list_episodes(limit: int = 20) -> list[dict[str, Any]]:
    rows = []
    for p in sorted(_dir().glob("episode-*.json"), reverse=True)[:limit]:
        try:
            rows.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            continue
    return rows
