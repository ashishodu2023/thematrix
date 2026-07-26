"""Pull all character brain models into local Ollama (rank order)."""

from __future__ import annotations

import subprocess
import sys

from matrix.characters import brains_by_rank
from matrix.theme import banner, out, paint


def main() -> None:
    banner()
    out("Pulling Matrix brains (ascending rank → larger models):", bold=True)
    ranked = brains_by_rank()
    for rank, name, model in ranked:
        out(f"  rank {rank:2d}  {name:12} → {model}")
    out()
    models = list(dict.fromkeys(model for _, _, model in ranked))
    for model in models:
        out(f"==> ollama pull {model}", bold=True)
        result = subprocess.run(["ollama", "pull", model], check=False)
        if result.returncode != 0:
            print(paint(f"FAILED: {model}"), file=sys.stderr)
            sys.exit(result.returncode)
    out("All brains ready.", bold=True)


if __name__ == "__main__":
    main()
