import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codex_triad.checker import diagnose
from codex_triad.cli import main
from codex_triad.installer import InstallationError, install
from codex_triad.models import ModelSelectionError
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

    def catalog(self):
        return [{"model": model, "efforts": ["medium", "high"], "default_effort": "medium", "is_default": False}
                for model in (Settings().main_model, Settings().worker_model, Settings().advisor_model)]

    def test_default_doctor_does_not_query_models(self):
        with patch("codex_triad.checker.discover_models") as discover:
            diagnose(self.root)
        discover.assert_not_called()

    def test_catalog_match_preserves_files_and_runtime_unknowns(self):
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with patch("codex_triad.checker.discover_models", return_value=self.catalog()) as discover:
            checks = diagnose(self.root, check_models=True)
        discover.assert_called_once_with(self.root.resolve(), codex_home=None, system_proxy=False)
        self.assertEqual(sum(c.code == "MODEL_LISTED" for c in checks), 6)
        self.assertFalse(any(c.level == "FAIL" for c in checks))
        self.assertTrue(any(c.code == "RUNTIME_UNVERIFIED" and c.level == "UNKNOWN" for c in checks))
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_catalog_checks_preserved_user_config_instead_of_manifest_target(self):
        project = self.root / "existing"
        (project / ".codex").mkdir(parents=True)
        config = project / ".codex/config.toml"
        config.write_text('model = "custom-main"\nmodel_reasoning_effort = "high"\n[agents]\n'
                          'default_subagent_model = "custom-default"\ndefault_subagent_reasoning_effort = "medium"\n')
        install(project, Settings())
        agent = project / ".codex/agents/triad_explorer.toml"
        agent.write_text(agent.read_text().replace(Settings().worker_model, "custom-explorer"))
        with patch("codex_triad.checker.discover_models", return_value=self.catalog()):
            checks = diagnose(project, check_models=True)
        warnings = [c for c in checks if c.code == "MODEL_NOT_LISTED"]
        self.assertEqual(len(warnings), 3)
        for role, model in (("main", "custom-main"), ("default worker", "custom-default"), ("triad_explorer", "custom-explorer")):
            self.assertTrue(any(role in c.message and model in c.message and c.level == "WARN" for c in warnings))

    def test_catalog_uses_edited_agent_instead_of_manifest_target(self):
        agent = self.root / ".codex/agents/triad_explorer.toml"
        agent.write_text(agent.read_text().replace(Settings().worker_model, "custom-explorer"))
        with patch("codex_triad.checker.discover_models", return_value=self.catalog()):
            checks = diagnose(self.root, check_models=True)
        warnings = [c for c in checks if c.code == "MODEL_NOT_LISTED"]
        self.assertEqual(len(warnings), 1)
        self.assertIn("custom-explorer", warnings[0].message)

    def test_unsupported_effort_is_catalog_warning_not_access_denial(self):
        catalog = self.catalog()
        catalog[0]["efforts"] = ["medium"]
        with patch("codex_triad.checker.discover_models", return_value=catalog):
            checks = diagnose(self.root, check_models=True)
        warning = next(c for c in checks if c.code == "MODEL_EFFORT_NOT_LISTED")
        self.assertEqual(warning.level, "WARN")
        self.assertIn("main:", warning.message)
        self.assertIn("reported options: medium", warning.message)

    def test_static_failures_skip_catalog_query(self):
        (self.root / ".codex/agents/triad_explorer.toml").unlink()
        with patch("codex_triad.checker.discover_models") as discover:
            checks = diagnose(self.root, check_models=True)
        discover.assert_not_called()
        self.assertTrue(any(c.code == "MISSING_AGENT" and c.level == "FAIL" for c in checks))
        self.assertTrue(any(c.code == "MODEL_CATALOG" and c.level == "UNKNOWN" for c in checks))

    def test_cli_catalog_failure_stays_structured_and_forwards_discovery_options(self):
        for error in (ModelSelectionError("catalog unavailable"), FileNotFoundError("missing home")):
            with self.subTest(error=error), patch("codex_triad.checker.discover_models", side_effect=error) as discover, \
                 contextlib.redirect_stdout(io.StringIO()) as out:
                status = main(["doctor", "--project", str(self.root), "--check-models", "--json",
                               "--codex-home", str(self.root / "home"), "--system-proxy"])
            self.assertEqual(status, 0)
            checks = json.loads(out.getvalue())
            self.assertTrue(any(c["code"] == "MODEL_CATALOG" and c["level"] == "UNKNOWN" for c in checks))
            discover.assert_called_once_with(self.root.resolve(), codex_home=self.root / "home", system_proxy=True)

    def test_cli_discovery_options_require_explicit_check(self):
        for flag in (["--codex-home", str(self.root)], ["--system-proxy"]):
            with patch("codex_triad.checker.discover_models") as discover, contextlib.redirect_stderr(io.StringIO()) as err:
                status = main(["doctor", "--project", str(self.root), *flag])
            self.assertEqual(status, 2)
            self.assertIn("require --check-models", err.getvalue())
            discover.assert_not_called()
