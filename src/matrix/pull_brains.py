"""Pull all character brain models into local Ollama (rank order)."""

from __future__ import annotations

import subprocess
import sys

from matrix.characters import brains_by_rank


def main() -> None:
    ranked = brains_by_rank()
    print("Pulling Matrix brains (ascending rank → larger models):")
    for rank, name, model in ranked:
        print(f"  rank {rank:2d}  {name:12} → {model}")
    print()
    models = list(dict.fromkeys(model for _, _, model in ranked))
    for model in models:
        print(f"==> ollama pull {model}")
        result = subprocess.run(["ollama", "pull", model], check=False)
        if result.returncode != 0:
            print(f"FAILED: {model}", file=sys.stderr)
            sys.exit(result.returncode)
    print("All brains ready.")


if __name__ == "__main__":
    main()
