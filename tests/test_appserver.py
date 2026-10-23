import io
import json
import unittest
from unittest.mock import Mock, patch

from codex_triad.appserver import Client


class AppServerTests(unittest.TestCase):
    def client(self, messages):
        process = Mock(stdin=io.StringIO(), stdout=io.StringIO(
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
        process.terminate.assert_called_once()
