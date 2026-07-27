"""RAG over Redis agent knowledge / minds — Ollama embeddings with hash fallback."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import urllib.request
from collections import Counter
from functools import lru_cache
from typing import Iterable

from matrix.minds import MindStore
from matrix.services.memory import SessionMemory

_TOKEN = re.compile(r"[a-z0-9_]{3,}")
_DIM = int(os.getenv("MATRIX_RAG_DIM", "128"))
_USE_EMBED = os.getenv("MATRIX_RAG_EMBED", "1").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}
_USE_OLLAMA = os.getenv("MATRIX_RAG_OLLAMA", "1").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}
_OLLAMA_EMBED_MODEL = os.getenv("MATRIX_RAG_MODEL", "nomic-embed-text")


def _ollama_base() -> str:
    try:
        from matrix.config import config

        return (config.ollama_base_url or "http://127.0.0.1:11434").rstrip("/")
    except Exception:  # noqa: BLE001
        return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def _ollama_embed(text: str) -> list[float] | None:
    """Call Ollama embeddings API; return None on any failure."""
    if not _USE_OLLAMA:
        return None
    payload = {
        "model": _OLLAMA_EMBED_MODEL,
        "prompt": (text or "")[:4000],
    }
    try:
        req = urllib.request.Request(
            f"{_ollama_base()}/api/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        vec = body.get("embedding")
        if isinstance(vec, list) and vec:
            norm = math.sqrt(sum(float(v) * float(v) for v in vec)) or 1.0
            return [float(v) / norm for v in vec]
    except Exception:  # noqa: BLE001
        return None
    return None


def _tokenize(text: str) -> Counter[str]:
    return Counter(_TOKEN.findall((text or "").lower()))


def _ngrams(text: str, n: int = 3) -> list[str]:
    t = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()
    toks = t.split()
    grams: list[str] = list(toks)
    for i in range(len(toks) - 1):
        grams.append(toks[i] + "_" + toks[i + 1])
    compact = t.replace(" ", "")[:240]
    for i in range(max(0, len(compact) - n + 1)):
        grams.append(compact[i : i + n])
    return grams


def hash_embed(text: str, dim: int = _DIM) -> list[float]:
    """Feature-hashing embedding — stable, dependency-free."""
    vec = [0.0] * dim
    for g in _ngrams(text):
        h = hashlib.blake2b(g.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(h[:4], "little") % dim
        sign = 1.0 if (h[4] & 1) == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


@lru_cache(maxsize=512)
def _cached_hash(text: str) -> tuple[float, ...]:
    return tuple(hash_embed(text))


def embed(text: str, dim: int = _DIM) -> list[float]:
    """Prefer Ollama embeddings; fall back to hashed features."""
    ollama_vec = _ollama_embed(text)
    if ollama_vec:
        return ollama_vec
    if dim == _DIM:
        return list(_cached_hash(text))
    return hash_embed(text, dim=dim)


def _cosine_vec(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n <= 0:
        return 0.0
    return sum(a[i] * b[i] for i in range(n))


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    shared = set(a) & set(b)
    if not shared:
        return 0.0
    num = sum(a[t] * b[t] for t in shared)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    if da <= 0 or db <= 0:
        return 0.0
    return num / (da * db)


def corpus_for(human_id: str = "neo", characters: Iterable[str] | None = None) -> list[str]:
    docs: list[str] = []
    session = SessionMemory.load(human_id)
    docs.extend(session.agent_knowledge[-80:])
    for life in session.lives[-5:]:
        if getattr(life, "outcome", None):
            docs.append(f"past_life: {life.outcome}")
    names = list(characters or [])
    if not names:
        names = [
            "smith",
            "trinity",
            "neo",
            "oracle",
            "architect",
            "cypher",
            "niobe",
            "merovingian",
            "keymaker",
        ]
    for name in names:
        mind = MindStore.load(name)
        docs.append(MindStore.dossier(name))
        docs.extend(mind.facts[-8:])
    seen: set[str] = set()
    out: list[str] = []
    for d in docs:
        t = (d or "").strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def retrieve(
    query: str,
    *,
    human_id: str = "neo",
    characters: Iterable[str] | None = None,
    k: int = 5,
) -> list[tuple[float, str]]:
    scored: list[tuple[float, str]] = []
    if _USE_EMBED:
        qv = embed(query)
        for doc in corpus_for(human_id, characters):
            score = _cosine_vec(qv, embed(doc))
            if score > 0.08:
                scored.append((score, doc))
    else:
        q = _tokenize(query)
        for doc in corpus_for(human_id, characters):
            score = _cosine(q, _tokenize(doc))
            if score > 0.05:
                scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:k]


def retrieve_block(
    query: str,
    *,
    human_id: str = "neo",
    character: str = "",
    k: int = 4,
) -> str:
    chars = [character] if character else None
    hits = retrieve(query, human_id=human_id, characters=chars, k=k)
    if not hits:
        hits = retrieve(query, human_id=human_id, k=k)
    if not hits:
        return ""
    lines = [f"- ({score:.2f}) {doc}" for score, doc in hits]
    return "Retrieved memory:\n" + "\n".join(lines)


def embedding_backend() -> str:
    """Diagnostic: which embedding path is active."""
    if not _USE_EMBED:
        return "token_cosine"
    probe = _ollama_embed("matrix probe")
    if probe:
        return f"ollama:{_OLLAMA_EMBED_MODEL}"
    return "hash"
