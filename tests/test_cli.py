import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codex_triad.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "项目 with spaces"
        self.root.mkdir()

    def run_cli(self, *args):
        result = subprocess.run([sys.executable, "-m", "codex_triad", *args],
                                capture_output=True, encoding="utf-8", timeout=15,
                                env={**os.environ, "PYTHONUTF8": "1"})
        self.assertNotIn("Traceback", result.stderr)
        return result

    def test_end_to_end_all_five_commands(self):
        project = ["--project", str(self.root)]
        preview = self.run_cli("init", *project, "--dry-run")
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn("+++ after/", preview.stdout)
        self.assertEqual(list(self.root.iterdir()), [])
        installed = self.run_cli("init", *project)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        doctor = self.run_cli("doctor", *project, "--json")
        self.assertEqual(doctor.returncode, 0, doctor.stdout)
        self.assertTrue(any(c["code"] == "RUNTIME_UNVERIFIED" for c in json.loads(doctor.stdout)))
        self.assertIn("MODEL_NOT_VERIFIED", self.run_cli("smoke", "--phase", "workers").stdout)
        self.assertIn("MODEL_NOT_VERIFIED", self.run_cli("smoke", "--phase", "advisor").stdout)
        csv = self.root / "runs.csv"
        csv.write_text("task_id,strategy,success,elapsed_seconds,input_tokens,output_tokens,cost_usd\nx,triad,true,1,UNKNOWN,,\n")
        report = self.run_cli("report", "--csv", str(csv), "--json")
        self.assertEqual(report.returncode, 0, report.stderr)
        self.assertIsNone(json.loads(report.stdout)[0]["total_input_tokens"])
        preview = self.run_cli("uninstall", *project, "--dry-run")
        self.assertEqual(preview.returncode, 0)
        self.assertIn("triad-state.json", preview.stdout)
        self.assertTrue((self.root / "AGENTS.md").exists())
        self.assertEqual(self.run_cli("uninstall", *project).returncode, 0)
        self.assertEqual(csv.read_text().splitlines()[1], "x,triad,true,1,UNKNOWN,,")
        self.assertFalse((self.root / "AGENTS.md").exists())

    def test_doctor_missing_project_json_and_exit_status(self):
        result = self.run_cli("doctor", "--project", str(self.root / "missing"), "--json")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(c["level"] == "FAIL" for c in json.loads(result.stdout)))

    def test_install_errors_have_no_traceback(self):
        result = self.run_cli("init", "--project", str(self.root), "--max-subagents", "0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ERROR", result.stderr)

    def test_smoke_does_not_execute_anything(self):
        with patch("subprocess.run", side_effect=AssertionError("must not spawn")), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["smoke"]), 0)
        self.assertIn("consume model quota", out.getvalue())

    def test_recover_is_separate_from_install(self):
        result = self.run_cli("init", "--project", str(self.root), "--recover")
        self.assertEqual(result.returncode, 0)
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertEqual(self.run_cli("init", "--project", str(self.root), "--recover", "--dry-run").returncode, 2)

    def test_runtime_evidence_error_has_no_traceback(self):
        path = self.root / "bad-evidence.json"
        path.write_text("[]")
        result = self.run_cli("report", "--runtime-evidence", str(path), "--json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("rejected", result.stderr)
