import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from codex_triad.cli import main
from codex_triad.models import ModelSelectionError, choose_settings, discover_models, latest_model, visible_models
from codex_triad.templates import Settings


CATALOG = [
    {"model": "provider/reasoner", "supportedReasoningEfforts": [{"reasoningEffort": "high"}], "defaultReasoningEffort": "high", "isDefault": True},
    {"model": "fast-model", "supportedReasoningEfforts": [{"reasoningEffort": "none"}, {"reasoningEffort": "low"}], "defaultReasoningEffort": "none"},
]


def family_catalog(*models, efforts=("medium", "high")):
    return visible_models([{"model": model, "supportedReasoningEfforts": [{"reasoningEffort": effort} for effort in efforts],
                            "defaultReasoningEffort": efforts[0]} for model in models])


class ModelTests(unittest.TestCase):
    def test_models_command_lists_capabilities_without_installing_or_starting_turns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            catalog = visible_models(CATALOG)
            args = ["models", "--project", str(root), "--codex-home", str(root), "--system-proxy"]
            with patch("codex_triad.cli.discover_models", return_value=catalog) as discover, patch("codex_triad.cli.install", side_effect=AssertionError("listing must not install")):
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(main([*args, "--json"]), 0)
                self.assertEqual(json.loads(out.getvalue()), catalog)
                discover.assert_called_once_with(root, codex_home=root, system_proxy=True)
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(main(args), 0)
                self.assertIn("fast-model", out.getvalue())
                self.assertIn("none, low", out.getvalue())
                self.assertIn("has not been tested", out.getvalue())
            self.assertEqual(list(root.iterdir()), [])

    def test_models_command_reports_discovery_errors_without_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch("codex_triad.cli.discover_models", side_effect=ModelSelectionError("catalog unavailable")), contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(main(["models", "--project", str(root)]), 2)
            self.assertIn("catalog unavailable", err.getvalue())
            self.assertEqual(list(root.iterdir()), [])

    def test_legacy_default_assignments_skip_discovery_and_remain_pinned(self):
        from codex_triad.installer import install
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            install(root, Settings())
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            with patch("codex_triad.cli.discover_models") as discover:
                self.assertEqual(main(["init", "--project", str(root)]), 0)
                discover.assert_not_called()
            self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_programmatic_complete_assignment_pins_previously_automatic_roles(self):
        from codex_triad.installer import install
        catalog = family_catalog("gpt-6.1-sol", "gpt-6-luna", "gpt-6-astra")
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            args = ["init", "--project", str(root)]
            with patch("codex_triad.cli.discover_models", return_value=catalog):
                self.assertEqual(main(args), 0)
            state = json.loads((root / ".codex/triad-state.json").read_text())
            install(root, Settings(**state["settings"]))
            with patch("codex_triad.cli.discover_models") as discover:
                self.assertEqual(main(args), 0)
                discover.assert_not_called()
            self.assertNotIn("auto_model_roles", json.loads((root / ".codex/triad-state.json").read_text()))

    def test_latest_stable_family_uses_numeric_versions_and_rolling_aliases(self):
        catalog = family_catalog("gpt-6.9-sol", "gpt-6.10-sol-2026-10-23", "gpt-6.10-sol",
                                 "gpt-7-sol-preview", "gpt-7-sol-mini", "gpt-7-astra",
                                 "gpt-6.10-sol-latest", "gpt-6-luna")
        self.assertEqual(latest_model(catalog, "sol")["model"], "gpt-6.10-sol-latest")
        self.assertEqual(latest_model(list(reversed(catalog)), "sol")["model"], "gpt-6.10-sol-latest")
        self.assertEqual(latest_model(catalog, "astra")["model"], "gpt-7-astra")
        self.assertIsNone(latest_model(family_catalog("gpt-7-luna-preview"), "luna"))
        dated = family_catalog("provider/gpt-6-luna-2026-10-22", "provider/gpt-6-luna-2026-10-23")
        self.assertEqual(latest_model(dated, "luna")["model"], "provider/gpt-6-luna-2026-10-23")

    def test_automatic_init_refreshes_only_automatic_roles_and_keeps_manual_choices(self):
        first = family_catalog("gpt-6-sol", "gpt-6.1-sol", "gpt-6-luna", "gpt-6-astra")
        newer = family_catalog("gpt-6.2-sol", "gpt-6.1-luna", "gpt-6.1-astra")
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            args = ["init", "--project", str(root)]
            with patch("codex_triad.cli.discover_models", return_value=first) as discover:
                self.assertEqual(main([*args, "--dry-run"]), 0)
                self.assertEqual(list(root.iterdir()), [])
                self.assertEqual(main(args), 0)
                self.assertEqual(discover.call_count, 2)
            manifest = root / ".codex/triad-state.json"
            state = json.loads(manifest.read_text())
            self.assertEqual(state["settings"]["main_model"], "gpt-6.1-sol")
            self.assertEqual(set(state["auto_model_roles"]), {"main", "worker", "advisor"})
            with patch("codex_triad.cli.discover_models", return_value=newer):
                self.assertEqual(main([*args, "--worker-model", "user/pinned-worker", "--worker-effort", "low"]), 0)
                self.assertEqual(main(args), 0)
            state = json.loads(manifest.read_text())
            self.assertEqual(state["settings"]["main_model"], "gpt-6.2-sol")
            self.assertEqual(state["settings"]["advisor_model"], "gpt-6.1-astra")
            self.assertEqual(state["settings"]["worker_model"], "user/pinned-worker")
            self.assertEqual(state["settings"]["worker_effort"], "low")
            self.assertNotIn("worker", state["auto_model_roles"])

    def test_missing_family_and_unsupported_explicit_effort_never_write(self):
        cases = [(family_catalog("gpt-6.1-sol", "gpt-6-astra"), [], "luna"),
                 (family_catalog("gpt-6.1-sol", "gpt-6-astra", "gpt-6-luna", efforts=("medium",)), ["--main-effort", "high"], "does not support")]
        for catalog, extra, message in cases:
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                with patch("codex_triad.cli.discover_models", return_value=catalog), contextlib.redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(main(["init", "--project", str(root), *extra]), 2)
                self.assertIn(message, err.getvalue())
                self.assertEqual(list(root.iterdir()), [])

    def test_explicit_models_skip_discovery_and_unset_effort_uses_supported_default(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            args = ["init", "--project", str(root)]
            with patch("codex_triad.cli.discover_models") as discover:
                self.assertEqual(main([*args, "--main-model", "custom/main", "--worker-model", "custom/worker", "--advisor-model", "custom/advisor"]), 0)
                discover.assert_not_called()
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            catalog = family_catalog("gpt-6.1-sol", "gpt-6-astra", "gpt-6-luna", efforts=("low",))
            with patch("codex_triad.cli.discover_models", return_value=catalog):
                self.assertEqual(main(["init", "--project", str(root)]), 0)
            saved = json.loads((root / ".codex/triad-state.json").read_text())["settings"]
            self.assertEqual((saved["main_effort"], saved["worker_effort"], saved["advisor_effort"]), ("low", "low", "low"))

    def test_invalid_auto_role_metadata_is_rejected_before_discovery(self):
        from codex_triad.installer import install
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            install(root, Settings())
            path = root / ".codex/triad-state.json"
            initial = json.loads(path.read_text())
            for roles in (None, "main", ["main", "main"], ["unexpected"], [{}]):
                with self.subTest(roles=roles):
                    path.write_text(json.dumps({**initial, "auto_model_roles": roles}))
                    with patch("codex_triad.cli.discover_models") as discover, contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(main(["init", "--project", str(root)]), 2)
                    discover.assert_not_called()

    def test_auto_refresh_rejects_unsupported_saved_effort_without_changes(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            args = ["init", "--project", str(root)]
            with patch("codex_triad.cli.discover_models", return_value=family_catalog("gpt-6.1-sol", "gpt-6-luna", "gpt-6-astra")):
                self.assertEqual(main([*args, "--main-effort", "high"]), 0)
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            newer = family_catalog("gpt-6.2-sol", "gpt-6.1-luna", "gpt-6.1-astra", efforts=("low",))
            with patch("codex_triad.cli.discover_models", return_value=newer), contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(main(args), 2)
            self.assertIn("does not support", err.getvalue())
            self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_automatic_efforts_adapt_when_new_models_change_capabilities(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            args = ["init", "--project", str(root)]
            first = family_catalog("gpt-6.1-sol", "gpt-6-luna", "gpt-6-astra", efforts=("low",))
            newer = family_catalog("gpt-6.2-sol", "gpt-6.1-luna", "gpt-6.1-astra", efforts=("medium",))
            with patch("codex_triad.cli.discover_models", return_value=first):
                self.assertEqual(main(args), 0)
            with patch("codex_triad.cli.discover_models", return_value=newer):
                self.assertEqual(main(args), 0)
            saved = json.loads((root / ".codex/triad-state.json").read_text())
            self.assertEqual(set(saved["auto_effort_roles"]), {"main", "worker", "advisor"})
            self.assertEqual({saved["settings"][role + "_effort"] for role in saved["auto_effort_roles"]}, {"medium"})

    def test_interactive_picker_can_repair_an_unsupported_pinned_effort(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            args = ["init", "--project", str(root)]
            first = family_catalog("gpt-6.1-sol", "gpt-6-luna", "gpt-6-astra")
            newer = family_catalog("gpt-6.2-sol", "gpt-6.1-luna", "gpt-6.1-astra", efforts=("medium",))
            with patch("codex_triad.cli.discover_models", return_value=first):
                self.assertEqual(main([*args, "--main-effort", "high"]), 0)
            with patch("codex_triad.cli.discover_models", return_value=newer), patch("builtins.input", side_effect=[""] * 6):
                self.assertEqual(main([*args, "--interactive"]), 0)
            saved = json.loads((root / ".codex/triad-state.json").read_text())
            self.assertEqual(saved["settings"]["main_effort"], "medium")
            self.assertNotIn("auto_model_roles", saved)
            self.assertNotIn("auto_effort_roles", saved)

    def test_pinning_current_auto_model_has_visible_dry_run_and_install(self):
        catalog = family_catalog("gpt-6.1-sol", "gpt-6-luna", "gpt-6-astra")
        with tempfile.TemporaryDirectory() as temp, patch("codex_triad.cli.discover_models", return_value=catalog):
            root = Path(temp)
            args = ["init", "--project", str(root)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            pin = [*args, "--main-model", "gpt-6.1-sol"]
            with contextlib.redirect_stdout(io.StringIO()) as preview:
                self.assertEqual(main([*pin, "--dry-run"]), 0)
            self.assertIn("triad-state.json", preview.getvalue())
            self.assertIn("auto_model_roles", preview.getvalue())
            self.assertEqual(before, {p: p.read_bytes() for p in before})
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(pin), 0)
            self.assertIn("INSTALL", output.getvalue())
            self.assertIn("triad-state.json", output.getvalue())
            saved = json.loads((root / ".codex/triad-state.json").read_text())
            self.assertNotIn("main", saved["auto_model_roles"])
            self.assertNotIn("main", saved["auto_effort_roles"])

    def test_concurrent_manual_selection_is_not_overwritten_by_stale_discovery(self):
        from codex_triad.installer import install
        from dataclasses import replace
        first = family_catalog("gpt-6.1-sol", "gpt-6-luna", "gpt-6-astra")
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            args = ["init", "--project", str(root)]
            with patch("codex_triad.cli.discover_models", return_value=first):
                self.assertEqual(main(args), 0)
            concurrent = {}
            def discover(*_, **__):
                install(root, replace(Settings(), main_model="user/pinned-main"))
                concurrent.update({p: p.read_bytes() for p in root.rglob("*") if p.is_file()})
                return first
            with patch("codex_triad.cli.discover_models", side_effect=discover), contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(main(args), 2)
            self.assertIn("changed during selection", err.getvalue())
            self.assertEqual(concurrent, {p: p.read_bytes() for p in concurrent})
            saved = json.loads((root / ".codex/triad-state.json").read_text())
            self.assertEqual(saved["settings"]["main_model"], "user/pinned-main")

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
