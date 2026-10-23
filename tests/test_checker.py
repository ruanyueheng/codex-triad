import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codex_triad.checker import diagnose
from codex_triad.installer import InstallationError, install
from codex_triad.templates import Settings


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        install(self.root, Settings())
        self.patcher = patch("codex_triad.checker.shutil.which", return_value=None)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_malformed_manifest_is_reported_not_crashed(self):
        path = self.root / ".codex/triad-state.json"
        original = json.loads(path.read_text())
        for data in ([], 1, {"schema_version": 1}, {**original, "settings": []},
                     {**original, "agent_hashes": []}, {**original, "policy_hash": 1},
                     {**original, "schema_version": True}, {**original, "settings": {"worker_model": None}}):
            with self.subTest(data=data):
                path.write_text(json.dumps(data))
                self.assertTrue(any(c.code == "BAD_MANIFEST" and c.level == "FAIL" for c in diagnose(self.root)))
                with self.assertRaises(InstallationError):
                    install(self.root, Settings())

    def test_invalid_utf8_is_structured_failure(self):
        (self.root / ".codex/config.toml").write_bytes(b"\xff")
        self.assertTrue(any(c.code == "BAD_CONFIG" for c in diagnose(self.root)))

    def test_feature_disabled_and_bad_limits(self):
        config = self.root / ".codex/config.toml"
        config.write_text(config.read_text() + "\n[features]\nmulti_agent = false\n")
        self.assertTrue(any(c.code == "AGENTS_DISABLED" for c in diagnose(self.root)))
        config.write_text(config.read_text().replace("max_concurrent_threads_per_session = 3", "max_concurrent_threads_per_session = true"))
        self.assertTrue(any(c.code == "AGENTS_LIMIT" for c in diagnose(self.root)))

    def test_no_runtime_success_inferred(self):
        checks = {c.code: c for c in diagnose(self.root)}
        for code in ("CODEX_CLI", "CLIENT_CAPABILITIES", "CONFIG_PRECEDENCE", "RUNTIME_UNVERIFIED"):
            self.assertEqual(checks[code].level, "UNKNOWN")

    def test_version_probe_failure_and_timeout_are_unknown(self):
        for outcome in (subprocess.CompletedProcess([], 1, "", "unsupported"), subprocess.TimeoutExpired("codex", 8)):
            with patch("codex_triad.checker.shutil.which", return_value="codex"), patch("codex_triad.checker.subprocess.run") as run:
                if isinstance(outcome, Exception):
                    run.side_effect = outcome
                else:
                    run.return_value = outcome
                self.assertTrue(any(c.code == "CODEX_CLI" and c.level == "UNKNOWN" for c in diagnose(self.root)))

    def test_agent_fields_and_effort_validated(self):
        agent = self.root / ".codex/agents/triad_explorer.toml"
        original = agent.read_text()
        agent.write_text(original.replace('model = "gpt-6-luna"', 'model = 7'))
        self.assertTrue(any(c.code == "AGENT_SCHEMA" for c in diagnose(self.root)))
        agent.write_text(original.replace('model_reasoning_effort = "medium"', 'model_reasoning_effort = "invalid"'))
        self.assertTrue(any(c.code == "EFFORT_SCHEMA" for c in diagnose(self.root)))

    def test_malformed_policy_and_local_agent_edits(self):
        policy = self.root / "AGENTS.md"
        policy.write_text(policy.read_text() + "<!-- CODEX-TRIAD:BEGIN -->")
        agent = self.root / ".codex/agents/triad_triage.toml"
        agent.write_text(agent.read_text() + "# custom\n")
        codes = {c.code for c in diagnose(self.root)}
        self.assertIn("MISSING_POLICY", codes)
        self.assertIn("MODIFIED_AGENT", codes)
