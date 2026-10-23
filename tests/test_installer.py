import json
import tempfile
import tomllib
import unittest
from pathlib import Path
from codex_triad.installer import InstallationError, install, uninstall
from codex_triad.templates import AGENT_NAMES, Settings
from codex_triad.checker import diagnose


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def config(self):
        return tomllib.loads((self.root / ".codex" / "config.toml").read_text(encoding="utf-8"))

    def test_clean_install(self):
        install(self.root, Settings())
        conf = self.config()
        self.assertEqual(conf["model"], "gpt-6.1-sol")
        self.assertEqual(conf["agents"]["max_concurrent_threads_per_session"], 3)
        for name in AGENT_NAMES:
            agent = tomllib.loads((self.root / ".codex" / "agents" / f"{name}.toml").read_text())
            self.assertEqual(agent["name"], name)
            self.assertTrue(agent["developer_instructions"])
        self.assertFalse(any(x.level == "FAIL" for x in diagnose(self.root)))

    def test_idempotent(self):
        install(self.root, Settings())
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        install(self.root, Settings())
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_non_destructive_merge_existing(self):
        (self.root / ".codex").mkdir()
        old = "# Personal config\nmodel = \"existing-model\"\n[agents]\nmax_threads = 2\n[features]\ncustom_feature = true\n"
        (self.root / ".codex" / "config.toml").write_text(old)
        (self.root / "AGENTS.md").write_text("# My team rules\n")
        logs = install(self.root, Settings())
        self.assertTrue(any("WARNING" in line for line in logs))
        self.assertEqual(self.config()["model"], "existing-model")
        self.assertEqual(self.config()["agents"]["max_threads"], 2)
        self.assertTrue(self.config()["features"]["custom_feature"])
        self.assertIn("# My team rules", (self.root / "AGENTS.md").read_text())
        self.assertIn("CODEX-TRIAD:BEGIN", (self.root / "AGENTS.md").read_text())
        self.assertTrue(any(c.code == "MAIN_MISMATCH" for c in diagnose(self.root)))

    def test_agent_collision_is_refused(self):
        agent_folder = self.root / ".codex" / "agents"
        agent_folder.mkdir(parents=True)
        (agent_folder / "triad_explorer.toml").write_text("name = 'personal'\n")
        with self.assertRaises(InstallationError):
            install(self.root, Settings())
        self.assertFalse((self.root / "AGENTS.md").exists())

    def test_user_modified_managed_agent_is_protected(self):
        install(self.root, Settings())
        agent = self.root / ".codex" / "agents" / "triad_explorer.toml"
        agent.write_text(agent.read_text() + "# local edit\n")
        with self.assertRaises(InstallationError):
            install(self.root, Settings(worker_model="gpt-6.1-sol"))
        install(self.root, Settings(worker_model="gpt-6.1-sol"), force=True)
        self.assertNotIn("# local edit", agent.read_text())

    def test_uninstall_preserves_other_rules(self):
        (self.root / "AGENTS.md").write_text("# Keep this policy\n")
        (self.root / ".codex").mkdir()
        (self.root / ".codex" / "config.toml").write_text("# Keep me\napproval_policy = 'on-request'\n")
        install(self.root, Settings())
        uninstall(self.root)
        self.assertIn("# Keep this policy", (self.root / "AGENTS.md").read_text())
        self.assertNotIn("CODEX-TRIAD:BEGIN", (self.root / "AGENTS.md").read_text())
        cfg = self.config()
        self.assertEqual(cfg["approval_policy"], "on-request")
        self.assertNotIn("model", cfg)
        self.assertFalse((self.root / ".codex" / "triad-state.json").exists())

    def test_uninstall_pristine(self):
        install(self.root, Settings())
        uninstall(self.root)
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / ".codex" / "triad-state.json").exists())
        self.assertFalse(any((self.root / ".codex" / "agents").glob("*.toml")))

    def test_dry_run_no_mutations(self):
        messages = install(self.root, Settings(), dry_run=True)
        self.assertTrue(messages)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_config_with_nested_agent_role(self):
        (self.root / ".codex").mkdir()
        (self.root / ".codex" / "config.toml").write_text("[agents.something]\ndescription='local role'\nconfig_file='elsewhere.toml'\n")
        install(self.root, Settings())
        self.assertEqual(self.config()["agents"]["something"]["description"], "local role")
        self.assertEqual(self.config()["agents"]["default_subagent_model"], "gpt-6-luna")

    def test_uninstall_does_not_erase_edited_policy(self):
        install(self.root, Settings())
        policy = self.root / "AGENTS.md"
        policy.write_text(policy.read_text().replace("**Main session responsibility:**", "CUSTOM RULE\n**Main session responsibility:**"))
        result = uninstall(self.root)
        self.assertIn("CUSTOM RULE", policy.read_text())
        self.assertTrue(any("PARTIAL_UNINSTALL" in line for line in result))
        self.assertTrue((self.root / ".codex" / "triad-state.json").exists())

    def test_modified_marked_config_refused(self):
        install(self.root, Settings())
        cfg = self.root / ".codex" / "config.toml"
        cfg.write_text(cfg.read_text().replace('model = "gpt-6.1-sol"', 'model = "my-custom-model"'))
        with self.assertRaises(InstallationError):
            install(self.root, Settings())
        with self.assertRaises(InstallationError):
            uninstall(self.root)
        self.assertIn("my-custom-model", cfg.read_text())

    def test_do_not_claim_stray_markers(self):
        (self.root / "AGENTS.md").write_text("<!-- CODEX-TRIAD:BEGIN -->\nMy custom policy\n<!-- CODEX-TRIAD:END -->")
        with self.assertRaises(InstallationError):
            install(self.root, Settings())

    def test_config_symlink_refused(self):
        other = self.root / "outside.toml"
        other.write_text("model='secret'\n")
        (self.root / ".codex").mkdir()
        try:
            (self.root / ".codex" / "config.toml").symlink_to(other)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(InstallationError):
            install(self.root, Settings())
        self.assertEqual(other.read_text(), "model='secret'\n")

    def test_upgrade_models_updates_owned_settings_only(self):
        install(self.root, Settings())
        updated = Settings(main_model="custom-main", advisor_model="custom-advisor", worker_model="custom-worker")
        install(self.root, updated)
        self.assertEqual(self.config()["model"], "custom-main")
        self.assertEqual(self.config()["agents"]["default_subagent_model"], "custom-worker")
        self.assertEqual(tomllib.loads((self.root / ".codex/agents/triad_architect.toml").read_text())["model"], "custom-advisor")
        self.assertFalse(any(x.level == "FAIL" for x in diagnose(self.root)))

    def test_invalid_model_and_subagent_cap(self):
        with self.assertRaises(InstallationError):
            install(self.root, Settings(worker_model="invalid model"))
        with self.assertRaises(InstallationError):
            install(self.root, Settings(max_subagents=100))

    def test_uninstall_with_following_table(self):
        (self.root / ".codex").mkdir()
        (self.root / ".codex" / "config.toml").write_text("[features]\napps = true\n")
        install(self.root, Settings())
        uninstall(self.root)
        contents = (self.root / ".codex" / "config.toml").read_text()
        self.assertNotIn("codex-triad:section", contents)
        self.assertIn("apps = true", contents)
        tomllib.loads(contents)

    def test_missing_config_doctor_fails(self):
        self.assertTrue(any(x.level == "FAIL" for x in diagnose(self.root)))

    def test_dry_run_uninstall(self):
        install(self.root, Settings())
        uninstall(self.root, dry_run=True)
        self.assertTrue((self.root / ".codex" / "triad-state.json").exists())


    def test_preserve_manually_modified_managed_line(self):
        install(self.root, Settings())
        path = self.root / ".codex" / "config.toml"
        contents = path.read_text(encoding="utf-8")
        path.write_text(contents.replace('model = "gpt-6.1-sol"  # codex-triad:managed',
                                         'model = "my-own-model"  # codex-triad:managed'), encoding="utf-8")
        with self.assertRaises(InstallationError):
            install(self.root, Settings())
        with self.assertRaises(InstallationError):
            uninstall(self.root)
        self.assertEqual(self.config()["model"], "my-own-model")

    def test_preserve_manually_modified_policy(self):
        install(self.root, Settings())
        path = self.root / "AGENTS.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "## Codex Triad orchestration", "## Codex Triad orchestration (custom)"), encoding="utf-8")
        with self.assertRaises(InstallationError):
            install(self.root, Settings())
        messages = uninstall(self.root)
        self.assertTrue(any("SKIPPED modified AGENTS" in x for x in messages))
        self.assertIn("(custom)", path.read_text(encoding="utf-8"))

    def test_refuse_untracked_agent_even_identical(self):
        install(self.root, Settings())
        state = self.root / ".codex" / "triad-state.json"
        state.unlink()
        with self.assertRaises(InstallationError):
            install(self.root, Settings())

    def test_no_symlink_traversal(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        actual_project = self.root / "work"
        actual_project.mkdir()
        try:
            (actual_project / ".codex").symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(InstallationError):
            install(actual_project, Settings())
        self.assertEqual(list(outside.iterdir()), [])

    def test_invalid_install_manifest(self):
        state = self.root / ".codex" / "triad-state.json"
        state.parent.mkdir()
        state.write_text("[]", encoding="utf-8")
        with self.assertRaises(InstallationError):
            install(self.root, Settings())

    def test_force_never_claims_unknown_agent(self):
        folder = self.root / ".codex/agents"
        folder.mkdir(parents=True)
        agent = folder / "triad_explorer.toml"
        agent.write_bytes(b"user-owned")
        with self.assertRaises(InstallationError):
            install(self.root, Settings(), force=True)
        self.assertEqual(agent.read_bytes(), b"user-owned")

    def test_roundtrip_preserves_user_bytes(self):
        for original in (b"", b"  \r\n", b"# user", b"# user\r\n\r\n", b"# user\n   "):
            with self.subTest(original=original), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / ".codex").mkdir()
                config = root / ".codex/config.toml"
                policy = root / "AGENTS.md"
                config.write_bytes(original)
                policy.write_bytes(original)
                install(root, Settings())
                install(root, Settings())
                uninstall(root)
                self.assertEqual(config.read_bytes(), original)
                self.assertEqual(policy.read_bytes(), original)

    def test_multiline_fake_table_is_preserved_or_refused(self):
        config = self.root / ".codex/config.toml"
        config.parent.mkdir()
        original = 'notes = """\n[agents]\nhello\n"""\n'
        config.write_text(original)
        with self.assertRaises(InstallationError):
            install(self.root, Settings())
        self.assertEqual(config.read_text(), original)

    def test_managed_looking_line_inside_literal_is_not_removed(self):
        install(self.root, Settings())
        config = self.root / ".codex/config.toml"
        original = config.read_text() + '\n[notes]\ntext = \'\'\'\nmodel = "gpt-6.1-sol"  # codex-triad:managed\n\'\'\'\n'
        config.write_text(original)
        with self.assertRaises(InstallationError):
            uninstall(self.root)
        self.assertEqual(config.read_text(), original)

    def test_invalid_toml_untouched(self):
        config = self.root / ".codex/config.toml"
        config.parent.mkdir()
        config.write_bytes(b"model = [")
        with self.assertRaises(InstallationError):
            install(self.root, Settings())
        self.assertEqual(config.read_bytes(), b"model = [")
        self.assertFalse((self.root / "AGENTS.md").exists())

    def test_public_api_validates_setting_types(self):
        for settings in (Settings(max_subagents=True), Settings(max_subagents="3"), Settings(worker_model=3), Settings(worker_effort="bad")):
            with self.subTest(settings=settings), self.assertRaises(InstallationError):
                install(self.root, settings)

    def test_uninstall_retains_malformed_policy(self):
        install(self.root, Settings())
        policy = self.root / "AGENTS.md"
        policy.write_text(policy.read_text().replace("<!-- CODEX-TRIAD:END -->", ""))
        messages = uninstall(self.root)
        self.assertTrue(any("PARTIAL_UNINSTALL" in x for x in messages))
        self.assertTrue((self.root / ".codex/triad-state.json").exists())

    def test_preview_includes_diff(self):
        messages = install(self.root, Settings(), dry_run=True)
        self.assertTrue(any(x.startswith("+++ after/.codex/config.toml") for x in messages))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_legacy_schema_one_upgrade(self):
        install(self.root, Settings())
        state = self.root / ".codex/triad-state.json"
        data = json.loads(state.read_text())
        for key in ("config_original_hash", "config_created", "policy_created", "policy_joiner"):
            del data[key]
        state.write_text(json.dumps(data))
        install(self.root, Settings(worker_model="updated-worker"))
        self.assertEqual(self.config()["agents"]["default_subagent_model"], "updated-worker")
        uninstall(self.root)
        self.assertFalse(state.exists())

    def test_long_unicode_project_path(self):
        root = self.root / ("a" * 100) / ("b" * 100) / "项目 with spaces"
        try:
            root.mkdir(parents=True)
        except OSError:
            self.skipTest("long paths unavailable on host")
        install(root, Settings())
        install(root, Settings(worker_model="long-path-worker"))
        uninstall(root)
        self.assertFalse((root / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
