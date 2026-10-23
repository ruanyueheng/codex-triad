from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import build_release


class ReleaseTests(unittest.TestCase):
    def test_unlisted_files_never_enter_source_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for path in build_release.source_files():
                target = root / path.relative_to(build_release.ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
            canaries = ["evaluation/private-runs.csv", "evaluation/private-evidence.json",
                        "docs/private-notes.md", "src/codex_triad/private_settings.py"]
            for name in canaries:
                (root / name).write_text("PRIVATE_SYNTHETIC_CANARY", encoding="utf-8")
            (root / ".gitignore").write_text("\n".join(canaries), encoding="utf-8")
            with patch.object(build_release, "ROOT", root):
                included = {p.relative_to(root).as_posix() for p in build_release.source_files()}
            self.assertFalse(included.intersection(canaries))
            self.assertIn("src/codex_triad/storage.py", included)

    def test_release_manifest_rejects_wildcards_and_missing_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for entry in ("include *.py", "recursive-include evaluation *.csv", "include missing.py",
                          "include ../outside.py"):
                with self.subTest(entry=entry), patch.object(build_release, "ROOT", root):
                    (root / "MANIFEST.in").write_text(entry, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        build_release.source_files()
