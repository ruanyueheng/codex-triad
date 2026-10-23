"""Static preflight; generated files and client version are not runtime evidence."""
from __future__ import annotations

import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .installer import _assert_managed_intact, _hash, _read_state
from .storage import InstallationError, assert_safe_paths, ensure_no_pending, read_text
from .templates import AGENT_NAMES, BEGIN, END, EFFORTS


@dataclass(frozen=True)
class Check:
    level: str  # PASS, WARN, FAIL, UNKNOWN
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"level": self.level, "code": self.code, "message": self.message}


def diagnose(project: Path) -> list[Check]:
    project = project.resolve()
    result = [Check("PASS", "CONFIG_PATH", str(project / ".codex/config.toml"))]
    if not project.is_dir():
        return result + [Check("FAIL", "MISSING_PROJECT", f"Project does not exist: {project}")]
    config = project / ".codex/config.toml"
    policy = project / "AGENTS.md"
    paths = [config, policy, project / ".codex/triad-state.json",
             *(project / f".codex/agents/{name}.toml" for name in AGENT_NAMES)]
    try:
        assert_safe_paths(project, paths)
        ensure_no_pending(project)
    except InstallationError as exc:
        return result + [Check("FAIL", "UNSAFE_PROJECT", str(exc))]
    if not config.exists():
        return result + [Check("FAIL", "MISSING_CONFIG", "Run codex-triad init --project PATH")]
    try:
        parsed = tomllib.loads(read_text(config))
    except (OSError, InstallationError, tomllib.TOMLDecodeError) as exc:
        return result + [Check("FAIL", "BAD_CONFIG", str(exc))]
    try:
        state = _read_state(project)
    except (InstallationError, OSError) as exc:
        state = None
        result.append(Check("FAIL", "BAD_MANIFEST", str(exc)))
    result.append(Check("PASS" if state else "WARN", "MANIFEST" if state else "NO_MANIFEST",
                        "Managed installation recorded" if state else "No valid installation manifest"))
    expected = state["settings"] if state else {}
    for key, wanted in (("model", expected.get("main_model")),
                        ("model_reasoning_effort", expected.get("main_effort"))):
        got = parsed.get(key)
        if not isinstance(got, str) or not got.strip():
            result.append(Check("FAIL", "MAIN_SCHEMA", f"{key} must be a nonempty string"))
        elif wanted and got != wanted:
            result.append(Check("WARN", "MAIN_MISMATCH", f"Project {key} differs from the Triad target"))
        else:
            result.append(Check("PASS", "MAIN_CONFIG", f"Project {key} configured as {got!r}"))
    agents, features = parsed.get("agents", {}), parsed.get("features", {})
    if parsed.get("model_reasoning_effort") not in EFFORTS:
        result.append(Check("FAIL", "EFFORT_SCHEMA", "Unsupported project reasoning effort"))
    if not isinstance(agents, dict) or not isinstance(features, dict):
        result.append(Check("FAIL", "AGENTS_SCHEMA", "agents/features must be tables"))
        agents, features = {}, {}
    for table, key in ((agents, "enabled"), (features, "multi_agent")):
        value = table.get(key, True)
        if type(value) is not bool or not value:
            result.append(Check("FAIL", "AGENTS_DISABLED", f"{key} disables multi-agent or has an invalid type"))
    for key in ("max_concurrent_threads_per_session", "max_threads"):
        if key in agents and (type(agents[key]) is not int or agents[key] < 1):
            result.append(Check("FAIL", "AGENTS_LIMIT", f"agents.{key} must be a positive integer"))
    if "max_threads" in agents and "max_concurrent_threads_per_session" in agents:
        result.append(Check("WARN", "DUPLICATE_LIMIT", "Both concurrency names present; review manually"))
    for key, target in (("default_subagent_model", "worker_model"), ("default_subagent_reasoning_effort", "worker_effort")):
        value = agents.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            result.append(Check("FAIL", "AGENTS_SCHEMA", f"agents.{key} must be a nonempty string"))
        elif expected and value != expected.get(target):
            result.append(Check("WARN", "DEFAULT_MODEL", f"agents.{key} differs from the Triad target"))
    if "default_subagent_reasoning_effort" in agents and agents["default_subagent_reasoning_effort"] not in EFFORTS:
        result.append(Check("FAIL", "EFFORT_SCHEMA", "Unsupported default subagent effort"))
    try:
        text = read_text(policy)
        if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(BEGIN) > text.index(END):
            result.append(Check("FAIL", "MISSING_POLICY", "AGENTS.md lacks exactly one ordered Triad block"))
        elif state and _hash(text[text.index(BEGIN):text.index(END) + len(END)]) != state["policy_hash"]:
            result.append(Check("WARN", "MODIFIED_POLICY", "Managed policy has local edits"))
        else:
            result.append(Check("PASS", "POLICY", "Advisory delegation instructions present"))
        _assert_managed_intact(state, read_text(config), text)
    except (InstallationError, OSError) as exc:
        result.append(Check("FAIL", "MANAGED_CONTENT", str(exc)))
    for name in AGENT_NAMES:
        path = project / f".codex/agents/{name}.toml"
        if not path.exists():
            result.append(Check("FAIL", "MISSING_AGENT", path.name))
            continue
        try:
            text = read_text(path)
            agent = tomllib.loads(text)
        except (OSError, InstallationError, tomllib.TOMLDecodeError) as exc:
            result.append(Check("FAIL", "BAD_AGENT", f"{path.name}: {exc}"))
            continue
        if any(not isinstance(agent.get(k), str) or not agent[k].strip()
               for k in ("name", "description", "developer_instructions", "model", "model_reasoning_effort")) or agent.get("name") != name:
            result.append(Check("FAIL", "AGENT_SCHEMA", f"{path.name}: invalid Triad agent fields/name"))
            continue
        target = expected.get("advisor_model" if name == "triad_architect" else "worker_model")
        if agent["model_reasoning_effort"] not in EFFORTS:
            result.append(Check("FAIL", "EFFORT_SCHEMA", f"{name}: unsupported reasoning effort"))
        if target and agent["model"] != target:
            result.append(Check("WARN", "AGENT_MODEL_MISMATCH", f"{name}: model differs from target"))
        else:
            result.append(Check("PASS", "AGENT_DEFINED", f"{name}: configured model {agent['model']}"))
        if name in agents:
            result.append(Check("WARN", "ROLE_OVERRIDE", f"agents.{name} also declared; inspect manually"))
        if state and _hash(text) != state["agent_hashes"].get(path.name):
            result.append(Check("WARN", "MODIFIED_AGENT", f"{name}: file differs from installation manifest"))
    executable = shutil.which("codex")
    if executable:
        try:
            version = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=8)
            result.append(Check("PASS" if version.returncode == 0 else "UNKNOWN", "CODEX_CLI",
                                (version.stdout or version.stderr).strip()[:160] or "UNKNOWN"))
        except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
            result.append(Check("UNKNOWN", "CODEX_CLI", f"Version unavailable: {type(exc).__name__}"))
    else:
        result.append(Check("UNKNOWN", "CODEX_CLI", "CLI not on PATH; desktop version UNKNOWN"))
    result.extend([
        Check("UNKNOWN", "CLIENT_CAPABILITIES", "Version alone cannot confirm custom-agent schema or hooks support"),
        Check("UNKNOWN", "CONFIG_PRECEDENCE", "CLI > trusted project (nearest wins) > profile > user > cloud defaults > system > built-ins; managed requirements also constrain settings. Other layers were not read."),
        Check("UNKNOWN", "RUNTIME_UNVERIFIED", "Project trust, spawning, effective model, account access and usage NOT_VERIFIED. Run smoke in the actual client."),
    ])
    return result
