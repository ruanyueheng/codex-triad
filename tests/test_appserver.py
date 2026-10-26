import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from codex_triad.appserver import Client


class AppServerTests(unittest.TestCase):
    def client(self, messages, *, stdout=None):
        process = Mock(stdin=io.StringIO(), stdout=stdout if stdout is not None else io.StringIO(
            "".join(json.dumps(m) + "\n" for m in messages)))
        with patch("codex_triad.appserver.subprocess.Popen", return_value=process):
            client = Client("codex", ".", {}, None)
        self.addCleanup(client.close)
        return client, process

    def test_server_request_with_matching_id_does_not_consume_response(self):
        request = {"id": 1, "method": "item/commandExecution/requestApproval", "params": {}}
        event = {"method": "thread/started", "params": {"thread": {"id": "root"}}}
        client, process = self.client([request, event, {"id": 1, "result": {"ok": True}}])
        self.assertEqual(client.call("thread/start", {}), {"ok": True})
        self.assertIn(event, client.events)
        replies = [json.loads(line) for line in process.stdin.getvalue().splitlines()]
        self.assertEqual(replies[-1]["error"]["code"], -32601)

    def test_extensions_are_disabled_before_the_server_starts(self):
        process = Mock(stdin=io.StringIO(), stdout=io.StringIO())
        with patch("codex_triad.appserver.subprocess.Popen", return_value=process) as popen:
            client = Client("codex", ".", {}, None)
        self.addCleanup(client.close)
        command = popen.call_args.args[0]
        overrides = [command[i + 1] for i, arg in enumerate(command[:-1]) if arg == "-c"]
        for feature in ("hooks", "apps", "plugins"):
            self.assertIn(f"features.{feature}=false", overrides)

    def test_rpc_errors_and_disconnect_are_not_success(self):
        for messages, expected in (([{"id": 1, "error": {"code": -1, "message": "denied"}}], "denied"),
                                   ([], "closed")):
            with self.subTest(messages=messages):
                client, _ = self.client(messages)
                with self.assertRaisesRegex(RuntimeError, expected):
                    client.call("model/list", {})

    def test_malformed_protocol_messages_are_rejected(self):
        for message in ([], 7, None, {"id": 1}, {"id": 1, "result": {}, "error": {}}):
            with self.subTest(message=message):
                client, _ = self.client([message])
                with self.assertRaises(RuntimeError):
                    client.call("model/list", {})

    def test_timeout_and_child_cleanup(self):
        client, process = self.client([])
        with patch("codex_triad.appserver.time.monotonic", side_effect=[0, 46]):
            with self.assertRaises(TimeoutError):
                client.call("model/list", {})
        client.close()
        client.close()
        self.assertTrue(process.stdin.closed)
        process.wait.assert_called_once_with(timeout=10)
        process.terminate.assert_not_called()

    def test_invalid_stream_fails_promptly_and_does_not_expose_content(self):
        for raw in (b'private-payload-not-json\n', b'\xff\n'):
            with self.subTest(raw=raw):
                stdout = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8")
                self.addCleanup(stdout.close)
                client, _ = self.client([], stdout=stdout)
                with self.assertRaisesRegex(RuntimeError, "Invalid App Server stream") as error:
                    client.receive(timeout=0.2)
                self.assertNotIn("private-payload", str(error.exception))
                with self.assertRaisesRegex(RuntimeError, "Invalid App Server stream"):
                    client.receive(timeout=0.2)

    def test_read_failure_reaches_caller(self):
        stdout = Mock()
        stdout.__iter__ = Mock(side_effect=OSError("private pipe detail"))
        client, _ = self.client([], stdout=stdout)
        with self.assertRaisesRegex(RuntimeError, "Invalid App Server stream"):
            client.receive(timeout=0.2)

    def test_disconnect_remains_observable_without_another_write(self):
        client, process = self.client([])
        with self.assertRaisesRegex(RuntimeError, "closed"):
            client.receive(timeout=0.2)
        with patch("codex_triad.appserver.time.monotonic", side_effect=[0, 46]), self.assertRaisesRegex(RuntimeError, "closed"):
            client.call("model/list", {})
        self.assertEqual(process.stdin.getvalue(), "")

    def test_close_allows_launcher_child_to_finish(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "child-finished"
            child = ("import sys; from pathlib import Path; "
                     "print('{\"ready\":true}', flush=True); sys.stdin.read(); "
                     "Path(sys.argv[1]).write_text('closed')")
            launcher = "import subprocess, sys; subprocess.run([sys.executable, '-c', sys.argv[1], sys.argv[2]], check=True)"
            popen = subprocess.Popen
            with patch("codex_triad.appserver.subprocess.Popen", side_effect=lambda *a, **kw:
                       popen([sys.executable, "-c", launcher, child, str(marker)], **kw)):
                client = Client("unused", temp, None, subprocess.DEVNULL)
            try:
                self.assertEqual(client.receive(timeout=5), {"ready": True})
            finally:
                client.close()
            self.assertEqual(client.process.returncode, 0)
            self.assertEqual(marker.read_text(), "closed")

    def test_shutdown_escalates_only_after_eof_timeout(self):
        for platform in ("nt", "posix"):
            with self.subTest(platform=platform):
                client, process = self.client([])
                expired = subprocess.TimeoutExpired("codex", 10)
                process.wait.side_effect = [expired, 0] if platform == "nt" else [expired, expired, 0]
                with patch("codex_triad.appserver.os.name", platform), patch("codex_triad.appserver.subprocess.run") as run:
                    client.close()
                self.assertTrue(process.stdin.closed)
                if platform == "nt":
                    self.assertEqual(run.call_args.args[0], ["taskkill", "/PID", str(process.pid), "/T", "/F"])
                else:
                    run.assert_not_called()
                    process.terminate.assert_called_once()
                    process.kill.assert_called_once()
