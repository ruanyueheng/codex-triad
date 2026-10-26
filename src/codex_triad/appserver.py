"""Shared stdio transport for the installed Codex App Server."""
import json
import os
import queue
import subprocess
import threading
import time
from contextlib import suppress

class Client:
    def __init__(self, executable, project, environment, stderr):
        self.process = subprocess.Popen([executable, "app-server", "--listen", "stdio://", "-c", "features.hooks=false",
            "-c", "features.apps=false", "-c", "features.plugins=false"],
            cwd=project, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
            text=True, encoding="utf-8", bufsize=1)
        self.queue = queue.Queue()
        self.events = []
        self.counter = 0
        self.failure = None
        self.closed = False
        def read():
            try:
                for line in self.process.stdout:
                    self.queue.put(json.loads(line))
            except (ValueError, OSError) as exc:
                self.queue.put(RuntimeError(f"Invalid App Server stream ({type(exc).__name__}); check client output/encoding"))
            finally:
                self.queue.put(None)
                with suppress(OSError):
                    self.process.stdout.close()
        threading.Thread(target=read, daemon=True).start()

    def send(self, value):
        if self.failure is not None:
            raise self.failure
        self.process.stdin.write(json.dumps(value) + "\n")
        self.process.stdin.flush()

    def receive(self, timeout=1):
        if self.failure is not None:
            raise self.failure
        message = self.queue.get(timeout=timeout)
        if message is None:
            self.failure = RuntimeError("Codex App Server closed; check client startup/configuration")
        elif isinstance(message, Exception):
            self.failure = message
        elif not isinstance(message, dict):
            self.failure = RuntimeError("Invalid App Server message: expected a JSON object")
        if self.failure is not None:
            raise self.failure
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
        if self.closed:
            return
        self.failure = self.failure or RuntimeError("Codex App Server client is closed")
        # EOF lets CLI launchers wait for their children to release files before exiting.
        with suppress(OSError):
            self.process.stdin.close()
        try: self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                self.process.wait(timeout=10)
            else:
                self.process.terminate()
                try: self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=10)
        self.closed = True

