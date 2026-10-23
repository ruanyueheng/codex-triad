"""Run the bundled Triad CLI without installing into the user's Python environment."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from codex_triad.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
