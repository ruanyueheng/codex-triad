"""Check the clean wheel and standalone skill outside the source tree, without model calls."""
import os
import subprocess
import sys
import tempfile
import tomllib
import venv
import zipfile
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
        environment["CODEX_HOME"] = str(folder / "codex-home")
        (folder / "codex-home").mkdir()

        def run(*args):
            return subprocess.run([str(python), *args], cwd=folder, env=environment,
                                  check=True, capture_output=True, encoding="utf-8", timeout=60)

        run("-m", "pip", "install", "--no-index", "--no-deps", str(wheel))
        assert run("-c", "import codex_triad; print(codex_triad.__version__)").stdout.strip() == version
        project = folder / "project"
        project.mkdir()
        models = ("--main-model", "gpt-6.1-sol", "--worker-model", "gpt-6-luna", "--advisor-model", "gpt-6-astra")
        run("-m", "codex_triad", "--help")
        run("-m", "codex_triad", "models", "--help")
        assert "--check-models" in run("-m", "codex_triad", "doctor", "--help").stdout
        console = python.parent / ("codex-triad.exe" if os.name == "nt" else "codex-triad")
        subprocess.run([str(console), "--help"], cwd=folder, env=environment,
                       check=True, capture_output=True, timeout=15)
        run("-m", "codex_triad", "init", "--project", str(project), *models)
        run("-m", "codex_triad", "doctor", "--project", str(project), "--json")
        run("-m", "codex_triad", "uninstall", "--project", str(project))
        assert not (project / "AGENTS.md").exists()

        destination = folder / "host" / ".agents" / "skills"
        with zipfile.ZipFile(root / "dist" / f"codex-triad-{version}-skill.zip") as archive:
            archive.extractall(destination)
        bundle = destination / "codex-triad"
        script = bundle / "scripts" / "triad.py"

        def skill(*args):
            # No site-packages: the skill must work without the installed wheel or checkout.
            return subprocess.run([sys.executable, "-I", "-S", "-X", "utf8", str(script), *args], cwd=folder,
                                  env=environment, check=True, capture_output=True, encoding="utf-8", timeout=60)

        target = folder / "host"
        (target / ".codex").mkdir()
        original_config = b'# keep my settings\r\nmodel_provider = "my-provider"\r\n'
        original_rules = b"Keep existing team rules.\r\n"
        config = target / ".codex" / "config.toml"
        rules = target / "AGENTS.md"
        config.write_bytes(original_config)
        rules.write_bytes(original_rules)
        skill("--help")
        skill("models", "--help")
        assert "--check-models" in skill("doctor", "--help").stdout
        skill("init", "--project", str(target), *models, "--dry-run")
        assert config.read_bytes() == original_config and rules.read_bytes() == original_rules
        assert not (target / ".codex" / "triad-state.json").exists()
        skill("init", "--project", str(target), *models)
        skill("doctor", "--project", str(target), "--json")
        skill("smoke", "--phase", "workers")
        skill("smoke", "--phase", "advisor")
        skill("report", "--runtime-evidence", str(bundle / "evaluation" / "cli-runtime-20261023.json"), "--json")
        skill("uninstall", "--project", str(target), "--dry-run")
        assert (target / ".codex" / "triad-state.json").exists()
        skill("uninstall", "--project", str(target))
        assert config.read_bytes() == original_config and rules.read_bytes() == original_rules
    print(f"Clean wheel and standalone skill lifecycles passed: {version}")


if __name__ == "__main__":
    main()
