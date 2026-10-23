import copy
import json
from pathlib import Path
import tempfile
import unittest

from codex_triad.evidence import EvidenceError, verify_runtime
from codex_triad.templates import Settings


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "evidence.json"
        self.bundle = {"schema_version": 1, "root": {"model": "gpt-6.1-sol", "thread": {"id": "root"}},
                       "children": {"data": []}, "notifications": []}
        for role, model, start, end in (("triad_explorer", "gpt-6-luna", 1, 5),
                                       ("triad_researcher", "gpt-6-luna", 2, 6),
                                       ("triad_architect", "gpt-6-astra", 7, 10)):
            self.bundle["children"]["data"].append({"id": role, "agentRole": role, "model": model, "parentThreadId": "root"})
            for kind, moment in (("started", start), ("completed", end)):
                self.bundle["notifications"].append({"method": "item/started", "params": {"threadId": "root", "turnId": "turn", "startedAtMs": moment,
                    "item": {"type": "subAgentActivity", "kind": kind, "model": model if kind == "started" else None, "agentThreadId": role}}})
        self.bundle["notifications"].append({"method": "turn/completed", "params": {"threadId": "root", "turn": {"status": "completed", "id": "turn"}}})

    def verify(self, bundle):
        self.path.write_text(json.dumps(bundle), encoding="utf-8")
        return verify_runtime(self.path)

    def test_join_start_model_with_null_completion_model(self):
        result = self.verify(self.bundle)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["roles"]["triad_architect"]["model"], "gpt-6-astra")
        self.assertEqual(result["backend_identity"], "UNKNOWN")

    def test_custom_model_assignment_can_use_one_model_for_every_role(self):
        b = copy.deepcopy(self.bundle)
        b["root"]["model"] = "user/model"
        for c in b["children"]["data"]: c["model"] = "user/model"
        for e in b["notifications"]:
            item = e.get("params", {}).get("item", {})
            if item.get("kind") == "started": item["model"] = "user/model"
        self.path.write_text(json.dumps(b), encoding="utf-8")
        result = verify_runtime(self.path, Settings(main_model="user/model", worker_model="user/model", advisor_model="user/model"))
        self.assertEqual(result["status"], "PASS")

    def test_rejects_missing_lifecycle_wrong_model_parent_or_roles(self):
        for change in ("no_lifecycle", "wrong_model", "wrong_parent", "duplicate_role", "root_failed", "advisor_early", "workers_serial", "bad_timestamp", "mixed_turns"):
            with self.subTest(change=change):
                b = copy.deepcopy(self.bundle)
                if change == "no_lifecycle": b["notifications"] = b["notifications"][-1:]
                if change == "wrong_model": b["children"]["data"][0]["model"] = "gpt-6-astra"
                if change == "wrong_parent": b["children"]["data"][0]["parentThreadId"] = "other"
                if change == "duplicate_role": b["children"]["data"].append(b["children"]["data"][0])
                if change == "root_failed": b["notifications"][-1]["params"]["turn"]["status"] = "failed"
                if change == "advisor_early": b["notifications"][4]["params"]["startedAtMs"] = 3
                if change == "workers_serial": b["notifications"][2]["params"]["startedAtMs"] = 5
                if change == "bad_timestamp": b["notifications"][0]["params"]["startedAtMs"] = True
                if change == "mixed_turns": b["notifications"][0]["params"]["turnId"] = "other"
                with self.assertRaises(EvidenceError): self.verify(b)

    def test_self_report_and_empty_wait_are_not_spawn_evidence(self):
        b = copy.deepcopy(self.bundle)
        b["notifications"] = [{"method": "item/completed", "params": {"threadId": "root", "item": {"type": "agentMessage", "text": "All agents completed"}}}, b["notifications"][-1]]
        with self.assertRaises(EvidenceError): self.verify(b)

    def test_malformed_input_is_rejected(self):
        for b in ([], None, {"schema_version": 1}, {**self.bundle, "children": []}):
            with self.subTest(b=b), self.assertRaises(EvidenceError): self.verify(b)
