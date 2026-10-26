import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codex_triad.workflow import WorkflowError, codex_command, project_models, task_command, task_prompt


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "项目 with spaces"
        self.project.mkdir()

    def test_user_text_is_one_literal_argument_and_review_is_read_only(self):
        task = '--help & echo "测试" | %PATH% `literal`\n不要修改文件'
        with patch("codex_triad.workflow.codex_command", return_value=["codex.exe"]):
            command = task_command(self.project, task, "review")
        self.assertEqual(command[:-1], ["codex.exe", "--cd", str(self.project.resolve()), "--sandbox", "read-only"])
        self.assertTrue(command[-1].endswith(task + "\n"))
        self.assertEqual(list(self.project.iterdir()), [])

    def test_other_modes_preserve_client_permission_and_model_choices(self):
        for mode in ("auto", "quick", "team"):
            with self.subTest(mode=mode), patch("codex_triad.workflow.codex_command", return_value=["codex.exe"]):
                command = task_command(self.project, "完成任务", mode)
            self.assertEqual(command[:-1], ["codex.exe", "--cd", str(self.project.resolve())])

    def test_invalid_task_mode_or_project_never_launches(self):
        with patch("codex_triad.workflow.codex_command") as command:
            for task, mode in (("  ", "auto"), ("task", "unknown")):
                with self.assertRaises(WorkflowError):
                    task_command(self.project, task, mode)
            with self.assertRaises(WorkflowError):
                task_command(self.project / "missing", "task")
            command.assert_not_called()

    def test_npm_windows_launcher_bypasses_shell(self):
        shim = self.project / "codex.cmd"
        shim.write_text("this shell script must never execute")
        entry = self.project / "node_modules/@openai/codex/bin/codex.js"
        entry.parent.mkdir(parents=True)
        entry.write_text("// test fixture")
        node = self.project / "node.exe"
        node.touch()
        with patch("codex_triad.workflow.shutil.which", return_value=str(shim)):
            self.assertEqual(codex_command(), [str(node), str(entry)])
        entry.unlink()
        with patch("codex_triad.workflow.shutil.which", return_value=str(shim)), self.assertRaises(WorkflowError):
            codex_command()

    def test_prompt_copy_works_without_cli_or_installation(self):
        with patch("codex_triad.workflow.shutil.which", return_value=None):
            prompt = task_prompt("审查代码", "review", project=self.project)
            self.assertTrue(prompt.endswith("审查代码\n"))
            self.assertIn(str(self.project.resolve()), prompt)
            with self.assertRaises(WorkflowError):
                codex_command()

    def test_model_summary_reads_actual_choices_without_writes(self):
        self.assertEqual(project_models(self.project)["main"], "沿用 Codex 当前模型")
        agents = self.project / ".codex/agents"
        agents.mkdir(parents=True)
        (agents.parent / "config.toml").write_text('model = "my/main"\n[agents]\ndefault_subagent_model = "my/default"\n')
        (agents / "triad_explorer.toml").write_text('model = "my/worker"\n')
        (agents / "triad_architect.toml").write_text('model = "my/advisor"\n')
        before = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        self.assertEqual(project_models(self.project), {"main": "my/main", "worker": "my/worker", "advisor": "my/advisor"})
        self.assertEqual(before, {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()})
