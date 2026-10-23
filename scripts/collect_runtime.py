"""Opt-in, bounded App Server smoke test using the installed Codex CLI."""
import argparse
import json
import os
from pathlib import Path
import queue
import shutil
import sys
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from codex_triad.evidence import verify_runtime
from codex_triad.appserver import Client
from codex_triad.installer import _previous_settings, _read_state
from codex_triad.storage import assert_safe_paths, _restrict_windows_temp



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New private output directory; never upload raw diagnostics")
    parser.add_argument("--codex-home", type=Path, help="Optional independently configured/logged-in Codex home, applied only to the child")
    parser.add_argument("--system-proxy", action="store_true", help="Inherit system proxy in the child only")
    parser.add_argument("--run", action="store_true", help="Explicitly run model calls; may consume quota")
    args = parser.parse_args()
    if not args.run: parser.error("--run is required because this test calls models and consumes quota")
    project = args.project.resolve(strict=True)
    assert_safe_paths(project, [project / ".codex/triad-state.json"])
    settings = _previous_settings(_read_state(project))
    if settings is None: parser.error("Install Triad into the target project first")
    executable = shutil.which("codex")
    if not executable: parser.error("Codex CLI is not on PATH")
    output = args.output.resolve()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    if os.name == "nt": _restrict_windows_temp(output)
    environment = os.environ.copy()
    if args.codex_home:
        home = args.codex_home.resolve(strict=True)
        environment["CODEX_HOME"] = str(home)
    environment["CODEX_SQLITE_HOME"] = str(output / "state")
    if args.system_proxy:
        for scheme, value in urllib.request.getproxies().items():
            if scheme in ("http", "https"): environment[scheme.upper() + "_PROXY"] = value
    client = None
    active = None
    try:
        with (output / "server.stderr.txt").open("w", encoding="utf-8") as stderr:
            client = Client(executable, project, environment, stderr)
            client.call("initialize", {"clientInfo": {"name": "codex-triad-verifier", "version": "0.2.0a2"}, "capabilities": {"experimentalApi": True}})
            client.send({"method": "initialized", "params": {}})
            started = client.call("thread/start", {"cwd": str(project), "model": settings.main_model, "ephemeral": False,
                "sandbox": "read-only", "approvalPolicy": "never", "multiAgentMode": "explicitRequestOnly",
                "config": {"features.hooks": False, "features.apps": False, "features.plugins": False, "skills.include_instructions": False}})
            root_id = started["thread"]["id"]
            prompt = ("Perform real delegation now: spawn custom roles triad_explorer and triad_researcher concurrently, "
                "wait for BOTH, then spawn triad_architect to review their actual findings and wait. Use role-configured models/efforts; "
                "do not manually override models or substitute built-ins. Each report <=50 words. Supplied fixture: "
                "app.py defines add(a,b)=a+b; __main__ prints add(2,3). README requires Python>=3.11, stdlib only. "
                "Explorer identifies entry point; researcher identifies runtime/dependencies; architect reviews correctness. "
                "Do not inspect other files, edit, use shell/network tools, commit or push. Report original spawn errors. "
                "A mere acknowledgement is failure. Conclude with a short summary of returned findings.")
            turn = client.call("turn/start", {"threadId": root_id, "input": [{"type": "text", "text": prompt}],
                "model": settings.main_model, "effort": settings.main_effort, "multiAgentMode": "explicitRequestOnly"})
            active = (root_id, turn["turn"]["id"])
            deadline = time.monotonic() + 240
            events = list(client.events)
            while time.monotonic() < deadline:
                try: message = client.receive()
                except queue.Empty: continue
                events.append(message)
                if message.get("method") == "turn/completed" and message.get("params", {}).get("threadId") == root_id:
                    active = None
                    break
            if active: raise TimeoutError("Runtime test exceeded 240 seconds")
            children = client.call("thread/list", {"parentThreadId": root_id, "limit": 100})
            safe_events = [e for e in events if e.get("method") == "turn/completed" or
                           e.get("params", {}).get("item", {}).get("type") == "subAgentActivity"]
            # Keep only protocol metadata needed by the offline verifier; exclude prompts, config and credentials.
            for event in safe_events:
                if event.get("method") == "turn/completed":
                    turn_data = event["params"]["turn"]
                    event["params"]["turn"] = {k: turn_data.get(k) for k in ("id", "status")}
            bundle = {"schema_version": 1, "root": {"model": started["model"], "thread": {"id": root_id}},
                "children": {"data": [{k: t.get(k) for k in ("id", "agentRole", "model", "parentThreadId")} for t in children.get("data", [])]},
                "notifications": safe_events}
            evidence = output / "evidence.json"
            evidence.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
            result = verify_runtime(evidence, settings)
            (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(json.dumps(result, indent=2))
    finally:
        if client:
            if active:
                try: client.call("turn/interrupt", {"threadId": active[0], "turnId": active[1]})
                except (RuntimeError, TimeoutError, OSError): pass
            client.close()


if __name__ == "__main__":
    try: main()
    except (OSError, ValueError, RuntimeError, TimeoutError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
