import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from scripts import collect_runtime
from codex_triad.installer import install
from codex_triad.templates import Settings


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        install(self.project, Settings())
        fixture = Path(__file__).resolve().parents[1] / "evaluation/cli-runtime-20261023.json"
        self.bundle = json.loads(fixture.read_text(encoding="utf-8"))
        self.completion = next(e for e in self.bundle["notifications"] if e["method"] == "turn/completed"
                               and e["params"]["threadId"] == self.bundle["root"]["thread"]["id"])

    def collect(self, buffered, received):
        client = Mock(events=buffered)
        client.receive.side_effect = received
        def call(method, params):
            return {"initialize": {}, "thread/start": self.bundle["root"],
                    "turn/start": {"turn": {"id": self.completion["params"]["turn"]["id"]}},
                    "thread/list": self.bundle["children"], "turn/interrupt": {}}[method]
        client.call.side_effect = call
        output = self.root / "output"
        args = ["collect_runtime.py", "--project", str(self.project), "--output", str(output), "--run"]
        with patch.object(collect_runtime, "Client", return_value=client), \
             patch.object(collect_runtime.shutil, "which", return_value="fake-codex"), \
             patch.object(collect_runtime.sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
            collect_runtime.main()
        self.assertEqual(json.loads((output / "result.json").read_text())["status"], "PASS")
        client.close.assert_called_once()
        return client

    def test_completion_buffered_before_turn_start_reply(self):
        client = self.collect(self.bundle["notifications"], AssertionError("must use buffered completion"))
        client.receive.assert_not_called()

    def test_other_turn_completion_does_not_end_current_turn(self):
        stale = copy.deepcopy(self.completion)
        stale["params"]["turn"]["id"] = "previous-turn"
        client = self.collect([], [stale, *self.bundle["notifications"]])
        self.assertEqual(client.receive.call_count, 1 + len(self.bundle["notifications"]))
