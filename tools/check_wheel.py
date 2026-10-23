"""Install the built wheel offline, then check the CLI from outside the source tree."""
import os
import subprocess
import sys
import tempfile
import tomllib
import venv
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    wheel = root / "dist" / f"codex_triad-{version}-py3-none-any.whl"
    with tempfile.TemporaryDirectory(prefix="triad-wheel-") as tmp:
        folder = Path(tmp)
        venv.create(folder / "env", with_pip=True)
        python = folder / "env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        environment = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        environment["PYTHONUTF8"] = "1"

        def run(*args):
            return subprocess.run([str(python), *args], cwd=folder, env=environment,
                                  check=True, capture_output=True, encoding="utf-8", timeout=60)

        run("-m", "pip", "install", "--no-index", "--no-deps", str(wheel))
        assert run("-c", "import codex_triad; print(codex_triad.__version__)").stdout.strip() == version
        project = folder / "project"
        project.mkdir()
        run("-m", "codex_triad", "--help")
        console = python.parent / ("codex-triad.exe" if os.name == "nt" else "codex-triad")
        subprocess.run([str(console), "--help"], cwd=folder, env=environment,
                       check=True, capture_output=True, timeout=15)
        run("-m", "codex_triad", "init", "--project", str(project))
        run("-m", "codex_triad", "doctor", "--project", str(project), "--json")
        run("-m", "codex_triad", "uninstall", "--project", str(project))
        assert not (project / "AGENTS.md").exists()
    print(f"Clean wheel installation and CLI lifecycle passed: {version}")


if __name__ == "__main__":
    main()
