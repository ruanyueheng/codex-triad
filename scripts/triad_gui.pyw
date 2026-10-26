"""Double-click entry point for the bundled graphical launcher."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from codex_triad.gui import main

main()
