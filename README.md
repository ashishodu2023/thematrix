# The Matrix

Multi-act cinematic LangGraph simulation with **rank-scaled Ollama brains**,
**shared multi-agent awareness**, and an optional **background daemon**.

## Rank → brain (bigger LLM = higher Matrix rank)

| Rank | Character | Default Ollama model | ~Size |
|---:|---|---|---|
| 1 | Spoon Boy | `tinyllama` | 1.1B |
| 2 | Jones | `gemma2:2b` | 2B |
| 3 | Brown | `gemma2:2b` | 2B |
| 4 | Tank | `phi3:mini` | 3.8B |
| 5 | Cypher | `qwen2.5:3b` | 3B |
| 6 | Operator | `llama3.2` | 3B |
| 7 | Trinity | `mistral` | 7B |
| 8 | Morpheus | `llama3.1` | 8B |
| 9 | Neo | `qwen2.5:7b` | 7B |
| 10 | Smith | `gemma2:9b` | 9B |
| 11 | Oracle | `qwen2.5:14b` | 14B |
| 12 | Architect | `qwen2.5:32b` | 32B |

Override any brain: `MATRIX_BRAIN_NEO=…`, `MATRIX_BRAIN_ARCHITECT=…`, etc.

## Multi-agent learning & independent action

Every character receives a shared **awareness dossier** (other Agents’ dialogue,
reports, prior actions, Oracle/Architect echoes, Redis cross-cycle memory).

Key scenes call `character_act`: each brain **chooses its own action**, speaks,
and records a **LEARN** fact about peers. Swarm Agents, Smith’s pursuit, the
Architect’s routing, cafe, and lobby all decide independently. Learning persists
via `SessionMemory.agent_knowledge` for the next jack-in.

```bash
ollama serve
uv run matrix-pull-brains    # pulls every rank-scaled model (large!)
```

Tip: if 14B/32B are too heavy, override down, e.g.
`MATRIX_BRAIN_ARCHITECT=qwen2.5:7b MATRIX_BRAIN_ORACLE=qwen2.5:7b`.

## Interactive run

```bash
uv run matrix-jack-in
uv run matrix-resume extract
# … continue through HITLs …
```

## Daemon (continuous background)

Auto-plays full cycles; Operator LLM chooses each HITL.

```bash
uv run matrix-daemon start
uv run matrix-daemon start --cycles 3 --interval 60
uv run matrix-daemon start --foreground --cycles 1
uv run matrix-daemon status
uv run matrix-daemon stop
```

Logs: `.matrix_daemon.log` · PID: `.matrix_daemon.pid`

## Tests

```bash
uv run pytest -q
```
