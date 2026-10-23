"""Validate supplied App Server records; no network or transcript scraping."""
import json
from pathlib import Path

from .templates import Settings


class EvidenceError(ValueError):
    pass


def verify_runtime(path: Path, settings: Settings = Settings()) -> dict:
    try:
        bundle = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(bundle, dict) or type(bundle.get("schema_version")) is not int or bundle.get("schema_version") != 1:
            raise ValueError("Expected evidence schema_version 1")
        root = bundle["root"]
        root_id = root["thread"]["id"]
        if not isinstance(root_id, str) or not root_id or root.get("model") != settings.main_model:
            raise ValueError("Root ID/model missing or inconsistent")
        children = bundle["children"]["data"]
        notifications = bundle["notifications"]
        if not isinstance(children, list) or not isinstance(notifications, list):
            raise ValueError("children.data and notifications must be arrays")
        roles = {}
        for child in children:
            role = child.get("agentRole")
            if role not in ("triad_explorer", "triad_researcher", "triad_architect"):
                continue
            if role in roles:
                raise ValueError(f"Duplicate role: {role}")
            parent = child.get("parentThreadId") or child.get("source", {}).get("subAgent", {}).get("thread_spawn", {}).get("parent_thread_id")
            target = settings.advisor_model if role == "triad_architect" else settings.worker_model
            if parent != root_id or child.get("model") != target:
                raise ValueError(f"Parent/model mismatch: {role}")
            child_id = child["id"]
            if not isinstance(child_id, str) or not child_id or child_id == root_id:
                raise ValueError(f"Invalid child ID: {role}")
            roles[role] = {"thread_id": child_id, "model": target, "started_ms": None, "completed_ms": None}
        if len(roles) != 3 or len({v["thread_id"] for v in roles.values()}) != 3:
            raise ValueError("Three distinct role threads are required")
        by_id = {v["thread_id"]: v for v in roles.values()}
        endings = [e.get("params", {}).get("turn", {}) for e in notifications
                   if e.get("method") == "turn/completed" and e.get("params", {}).get("threadId") == root_id]
        if len(endings) != 1 or endings[0].get("status") != "completed":
            raise ValueError("Exactly one successful root turn completion is required")
        turn_id = endings[0].get("id")
        if not isinstance(turn_id, str) or not turn_id:
            raise ValueError("Root turn ID is missing")
        for event in notifications:
            params = event.get("params", {})
            if params.get("threadId") != root_id or params.get("turnId") != turn_id:
                continue
            if event.get("method") not in ("item/started", "item/completed"):
                continue
            item = params.get("item", {})
            if item.get("type") != "subAgentActivity" or item.get("agentThreadId") not in by_id:
                continue
            record = by_id[item["agentThreadId"]]
            kind = item.get("kind")
            if kind not in ("started", "completed"):
                continue
            moment = params.get("startedAtMs", params.get("completedAtMs"))
            if type(moment) is not int or moment < 0:
                raise ValueError("Activity timestamps must be nonnegative integers")
            if kind == "started" and item.get("model") != record["model"]:
                raise ValueError("Activity model differs from thread metadata")
            key = kind + "_ms"
            record[key] = moment if record[key] is None else min(record[key], moment)
        for role, record in roles.items():
            if record["started_ms"] is None or record["completed_ms"] is None or record["started_ms"] > record["completed_ms"]:
                raise ValueError(f"Missing or invalid lifecycle: {role}")
        workers = [roles[n] for n in ("triad_explorer", "triad_researcher")]
        if max(v["started_ms"] for v in workers) >= min(v["completed_ms"] for v in workers):
            raise ValueError("Worker execution did not overlap")
        if roles["triad_architect"]["started_ms"] < max(v["completed_ms"] for v in workers):
            raise ValueError("Advisor started before workers completed")
        return {"status": "PASS", "root_thread_id": root_id, "root_model": root["model"],
                "roles": roles, "model_evidence": "CLIENT_RUNTIME", "backend_identity": "UNKNOWN",
                "notice": "Validates supplied protocol records, not their authenticity or account-wide availability."}
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise EvidenceError(f"Runtime evidence rejected: {exc}") from exc
