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

## Possible outcomes

Every finished cycle writes a terminal `outcome` string (and `awakened` flag)
via `blue_ending` or `resolve_choice`. Path forks and HITLs below shape which
ending you get.

### Terminal endings (`outcome`)

| Ending | When | `awakened` | Summary |
|---|---|---:|---|
| **Blue pill** | `pill_choice=blue` | no | Wakes in bed; believes what they want to believe. (Also set early in `blue_ending` before epilogue.) |
| **The One begins** | red + `fight` + `training_score≥8` + `code=accept` | yes | Full path — bug/trust/steak/jump/showdown/radio + sees the code. |
| **Beginning of belief** | red + `fight` + `training_score≥6` (but not the full “One” bar) | yes | Trains, fights Smith, radio/code recorded — belief starts. |
| **Rescued by Trinity** | red + `fight` + `training_score<6` | yes | Undertrained; Smith nearly wins; rescued (radio/code noted). |
| **Lives to fight another cycle** | red + `flee` | yes | Trains, flees to a hardline; survives for another cycle. |
| **Desert of the real** | red + no fight/flee recorded | yes | Unplugged fallback — welcome to the desert of the real. |

Blue-pill runs skip Acts III–V and go straight to epilogue/persist after `blue_ending`.

### HITL choices (Operator / daemon)

| Kind | Options | Effect |
|---|---|---|
| `bug` | `extract` \| `refuse` | Extract → dream path; refuse → `bug_refuse` then dream (bug implanted). |
| `trust` | `trust` \| `walk` | Trust → Morpheus briefing; walk → `early_doubt` then Architect. |
| `oracle_question` | free text | Stored as `oracle_question`; Oracle answers before cafe. |
| `pill` | `red` \| `blue` | **Branch point** — red → ship/awakening; blue → blue ending. |
| `steak` | `steak` \| `refuse` | Steak → Cypher regret beat; refuse → skip to sentinel. |
| `jump` | `jump` \| `hesitate` | Affects training narrative / score path into combat. |
| `fight_or_flee` | `fight` \| `flee` | **Major** input to terminal ending (see table above). |
| `radio` | `call` \| `silent` | Embedded in red-path outcome text. |
| `code` | `accept` \| `deny` | Accept +3 training score + `code_sight`; required with high score for “The One begins”. |

Invalid / empty HITL answers fall back: pill→`blue`, fight→`flee`, code→`accept`, etc.

### Non-HITL path statuses (folded into endings)

| Field | Possible values | How it arises |
|---|---|---|
| `pursuit_status` | `idle` → `chasing` → `escaped` \| `caught` | Smith pursuit loop (LLM action biases odds); max rounds ⇒ `escaped`. |
| `showdown_status` | `won` \| `escaped` | Subway showdown: `won` if `training_score≥6` when done; else `escaped`. |
| `reality_rewritten` | `true` \| `false` | `bend_reality` vs `enforce_reality` after Agent swarm reconcile. |
| Architect route | consult Oracle \| skip to cafe | Architect `character_act`; threat ≥ `MATRIX_THREAT_SKIP_ORACLE` (default 7) forces cafe. |
| Independent scene acts | e.g. swarm `scan/hunt/contain/observe`, lobby `cover/advance/…` | Logged in `character_actions` / `agent_memory`; color narrative, not the terminal ending key. |

### Example red-path “The One” recipe

```
bug=extract → trust=trust → pill=red → steak=refuse → jump=jump
→ fight=fight → radio=call → code=accept
(+ construct training_score ≥ 8, showdown won)
```

→ outcome contains *“sees the code — The One begins.”* · `awakened=true`

## Tests

```bash
uv run pytest -q
```
