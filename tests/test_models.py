import copy
import contextlib
import io
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from codex_triad.cli import main
from codex_triad.models import ModelSelectionError, choose_settings, discover_models, visible_models
from codex_triad.templates import Settings


CATALOG = [
    {"model": "provider/reasoner", "supportedReasoningEfforts": [{"reasoningEffort": "high"}], "defaultReasoningEffort": "high", "isDefault": True},
    {"model": "fast-model", "supportedReasoningEfforts": [{"reasoningEffort": "none"}, {"reasoningEffort": "low"}], "defaultReasoningEffort": "none"},
]


class ModelTests(unittest.TestCase):
    def test_any_visible_model_can_take_any_role_and_be_reused(self):
        answers = iter(["2", "none", "2", "low", "1", "high"])
        settings = choose_settings(visible_models(CATALOG), Settings(), ask=lambda _: next(answers), show=lambda _: None)
        self.assertEqual(settings.main_model, "fast-model")
        self.assertEqual(settings.worker_model, "fast-model")
        self.assertEqual(settings.advisor_model, "provider/reasoner")
        self.assertEqual(settings.main_effort, "none")

    def test_invalid_selection_and_unsupported_effort_are_reprompted(self):
        answers = iter(["bad", "2", "ultra", "low", "1", "", "1", ""])
        settings = choose_settings(visible_models(CATALOG), Settings(), ask=lambda _: next(answers), show=lambda _: None)
        self.assertEqual(settings.main_model, "fast-model")
        self.assertEqual(settings.main_effort, "low")

    def test_catalog_rejects_unknown_efforts_missing_fields_and_duplicates(self):
        for entries in ([], [{}], [CATALOG[0], CATALOG[0]], [{**CATALOG[0], "defaultReasoningEffort": "low"}],
                        [{**CATALOG[0], "supportedReasoningEfforts": []}]):
            with self.subTest(entries=entries), self.assertRaises(ModelSelectionError):
                visible_models(entries)
        entries = copy.deepcopy(CATALOG)
        entries[0]["hidden"] = True
        self.assertEqual([m["model"] for m in visible_models(entries)], ["fast-model"])

    @patch("codex_triad.models.shutil.which", return_value="codex")
    @patch("codex_triad.models.Client")
    def test_discovery_paginates_without_starting_threads(self, mock_client, _):
        client = mock_client.return_value
        client.call.side_effect = [{}, {"data": CATALOG[:1], "nextCursor": "next"}, {"data": CATALOG[1:], "nextCursor": None}]
        models = discover_models(Path.cwd())
        self.assertEqual(len(models), 2)
        self.assertEqual([call.args[0] for call in client.call.call_args_list], ["initialize", "model/list", "model/list"])
        self.assertEqual(client.call.call_args_list[-1].args[1]["cursor"], "next")
        client.close.assert_called_once()

    @patch("codex_triad.models.shutil.which", return_value="codex")
    @patch("codex_triad.models.Client")
    def test_repeated_cursor_fails_and_closes_client(self, mock_client, _):
        client = mock_client.return_value
        client.call.side_effect = [{}, {"data": CATALOG[:1], "nextCursor": "same"}, {"data": [], "nextCursor": "same"}]
        with self.assertRaises(ModelSelectionError): discover_models(Path.cwd())
        client.close.assert_called_once()

    def test_interactive_install_and_dry_run_with_custom_assignment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = ["init", "--project", str(root), "--interactive"]
            def select(extra):
                with patch("codex_triad.cli.discover_models", return_value=visible_models(CATALOG)), patch("builtins.input", side_effect=["2", "none", "2", "low", "1", "high"]), contextlib.redirect_stdout(io.StringIO()):
                    return main(args + extra)
            self.assertEqual(select(["--dry-run"]), 0)
            self.assertEqual(list(root.iterdir()), [])
            self.assertEqual(select([]), 0)
            config = tomllib.loads((root / ".codex/config.toml").read_text(encoding="utf-8"))
            self.assertEqual(config["model"], "fast-model")
            advisor = tomllib.loads((root / ".codex/agents/triad_architect.toml").read_text(encoding="utf-8"))
            self.assertEqual(advisor["model"], "provider/reasoner")
            self.assertNotIn("Astra advisory", (root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_discovery_failure_and_cancel_never_install(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch("codex_triad.cli.discover_models", side_effect=ModelSelectionError("unavailable")), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["init", "--project", str(root), "--interactive"]), 2)
            self.assertEqual(list(root.iterdir()), [])
            with patch("codex_triad.cli.discover_models", return_value=visible_models(CATALOG)), patch("builtins.input", side_effect=EOFError), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["init", "--project", str(root), "--interactive"]), 2)
            self.assertEqual(list(root.iterdir()), [])
