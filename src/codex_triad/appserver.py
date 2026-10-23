"""Shared stdio transport for the installed Codex App Server."""
import json
import queue
import subprocess
import threading
import time

class Client:
    def __init__(self, executable, project, environment, stderr):
        self.process = subprocess.Popen([executable, "app-server", "--listen", "stdio://", "-c", "features.hooks=false"],
            cwd=project, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
            text=True, encoding="utf-8", bufsize=1)
        self.queue = queue.Queue()
        self.events = []
        self.counter = 0
        def read():
            for line in self.process.stdout:
                try: self.queue.put(json.loads(line))
                except ValueError: continue
            self.queue.put(None)
        threading.Thread(target=read, daemon=True).start()

    def send(self, value):
        self.process.stdin.write(json.dumps(value) + "\n")
        self.process.stdin.flush()

    def receive(self, timeout=1):
        message = self.queue.get(timeout=timeout)
        if message is None:
            raise RuntimeError("Codex App Server closed; inspect private server.stderr.txt")
        if not isinstance(message, dict):
            raise RuntimeError("Invalid App Server message: expected a JSON object")
        if "method" in message and "id" in message:
            self.send({"id": message["id"], "error": {"code": -32601, "message": "Interactive approvals are unavailable in this read-only smoke test"}})
        return message

    def call(self, method, params):
        self.counter += 1
        request_id = self.counter
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            try: message = self.receive()
            except queue.Empty: continue
            if "method" not in message and message.get("id") == request_id:
                if ("result" in message) == ("error" in message):
                    raise RuntimeError("Invalid App Server response: expected exactly one of result/error")
                if "error" in message: raise RuntimeError(json.dumps(message["error"]))
                return message.get("result")
            self.events.append(message)
        raise TimeoutError(method)

    def close(self):
        self.process.terminate()
        try: self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

