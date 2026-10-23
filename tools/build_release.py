"""Build locally with installed tooling; package reviewed source directories only."""
import hashlib
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = ("pyproject.toml", "MANIFEST.in", ".gitignore", "LICENSE", "SKILL.md", "README.md", "README.zh-CN.md",
              "SECURITY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md", "RELEASE_NOTES.md",
              "WORK_HANDOFF.md", "WORK_START_HERE.md", "WORK_PROMPT.txt", "task_plan.md", "findings.md", "progress.md")
SOURCE_DIRS = {"src/codex_triad": {".py"}, "tests": {".py"}, "tools": {".py"},
               "docs": {".md"}, ".github": {".md", ".yml"}, "evaluation": {".csv", ".json"}, "scripts": {".py"}}
SKILL_REFERENCES = {"SKILL.md", "LICENSE", "docs/CLI_NATIVE_VERIFICATION.md", "docs/MODEL_ASSIGNMENT.md",
                    "docs/ADR-001-SAFE-INSTALL.md", "evaluation/cli-runtime-20261023.json"}


def source_files():
    files = [ROOT / name for name in ROOT_FILES]
    files.extend(p for folder, extensions in SOURCE_DIRS.items() for p in (ROOT / folder).rglob("*")
                 if p.is_file() and p.suffix in extensions and "__pycache__" not in p.parts)
    for path in files:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"Unsafe/missing release source: {path.name}")
    return sorted(files)


def main():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    subprocess.run([sys.executable, "-m", "pip", "wheel", ".", "--no-index", "--no-deps", "--no-build-isolation", "-w", "dist"],
                   cwd=ROOT, check=True)
    wheel = output / f"codex_triad-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert "codex_triad/storage.py" in names
        assert not any("__pycache__" in n or n.endswith(".pyc") for n in names)
    source = output / f"codex-triad-{version}-source.zip"
    with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in source_files():
            info = zipfile.ZipInfo(f"codex-triad-{version}/{path.relative_to(ROOT).as_posix()}", (2026, 10, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        assert any(n.endswith("/tests/test_storage.py") for n in names)
        assert not any(part in {".codex", ".git", "__pycache__", "dist", ".venv", ".env"} for n in names for part in n.split("/"))
    skill = output / f"codex-triad-{version}-skill.zip"
    with zipfile.ZipFile(skill, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in source_files():
            relative = path.relative_to(ROOT)
            if relative.parts[0] in {"src", "scripts"} or relative.as_posix() in SKILL_REFERENCES:
                archive.write(path, f"codex-triad/{relative.as_posix()}")
    with zipfile.ZipFile(skill) as archive:
        assert "codex-triad/SKILL.md" in archive.namelist()
        assert "codex-triad/scripts/triad.py" in archive.namelist()
        assert "codex-triad/src/codex_triad/evidence.py" in archive.namelist()
        assert not any(n.startswith(("codex-triad/tests/", "codex-triad/tools/", "codex-triad/docs/work/"))
                       for n in archive.namelist())
    hashes = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}" for p in (wheel, source, skill)]
    (output / "SHA256SUMS.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print("\n".join(hashes))


if __name__ == "__main__":
    main()
