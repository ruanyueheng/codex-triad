"""Conservative, reversible project-local installer without TOML round-tripping."""
from __future__ import annotations

import hashlib
import json
import re
import tomllib
import copy
import difflib
from dataclasses import asdict
from pathlib import Path
from typing import Any
from contextlib import nullcontext

from .templates import (AGENT_NAMES, BEGIN, END, EFFORTS, MANAGED_LINE, Settings,
                        agent_toml, instructions_block, required_config)
from .storage import (InstallationError, apply_changes, assert_safe_paths as _assert_safe_paths,
                      ensure_no_pending, project_lock, read_bytes, read_text)

STATE_NAME = "triad-state.json"
AGENTS_HEADER_RE = re.compile(r"^\s*\[agents\](?:\s*#.*)?\s*$")


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _val(v: str | int | bool) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    return json.dumps(v, ensure_ascii=False)


def _load_toml(content: str, where: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(content) if content.strip() else {}
    except tomllib.TOMLDecodeError as exc:
        raise InstallationError(f"Invalid TOML at {where}: {exc}") from exc


def _managed_lines(settings: Settings) -> set[str]:
    """Recognize only *exact* Triad-generated key/value lines for a given install.

    A user editing a managed line must not have their change silently erased.
    """
    root, agents = required_config(settings)
    return {f"{key} = {_val(value)}  {MANAGED_LINE}" for key, value in {**root, **agents}.items()}


def _assert_managed_intact(state: dict[str, Any] | None, config: str, policy: str) -> None:
    """Refuse to overwrite untracked/locally modified Triad-managed config entries."""
    marked = [line.rstrip("\r\n") for line in config.splitlines() if MANAGED_LINE in line]
    if state is None:
        if marked or BEGIN in policy or END in policy:
            raise InstallationError("Triad markers found without manifest; refusing to claim existing content")
        return
    previous = _previous_settings(state)
    expected = _managed_lines(previous)
    for line in marked:
        if line not in expected:
            raise InstallationError("A managed config line was edited; resolve it manually before upgrading or uninstalling")


def _strip_our_config_lines(content: str, previous: Settings | None) -> str:
    # Keep table headers to avoid reparenting user-owned entries to other tables.
    # Never match on comment substring alone; only exact previously written lines.
    if previous is None:
        return content
    root, agents = required_config(previous)
    owned = {f"{key} = {_val(value)}  {MANAGED_LINE}": (scope, key, value)
             for scope, values in ((None, root), ("agents", agents)) for key, value in values.items()}
    lines = content.splitlines(keepends=True)
    parsed = _load_toml(content, Path("config.toml"))
    for index, line in enumerate(lines):
        entry = owned.get(line.rstrip("\r\n"))
        if entry is None:
            continue
        scope, key, value = entry
        expected = copy.deepcopy(parsed)
        table = expected if scope is None else expected.get(scope, {})
        if type(table.get(key)) is not type(value) or table.get(key) != value:
            raise InstallationError("Managed config line is outside its expected TOML scope")
        del table[key]
        candidate = "".join(lines[:index] + lines[index + 1:])
        actual = _load_toml(candidate, Path("config.toml"))
        if actual != expected:
            raise InstallationError("Unsafe config edit (multiline string or unexpected TOML scope); merge manually")
        lines[index] = ""
        parsed = actual
    return "".join(lines)


def _previous_settings(state: dict[str, Any] | None) -> Settings | None:
    if state is None:
        return None
    try:
        values = state["settings"]
        if not isinstance(values, dict):
            raise TypeError("settings must be an object")
        settings = Settings(**values)
        _validate_settings(settings)
        return settings
    except (TypeError, KeyError) as exc:
        raise InstallationError(f"Invalid existing Triad installation manifest: {exc}") from exc


def merge_config(original: str, settings: Settings, where: Path, previous: Settings | None = None) -> tuple[str, list[str]]:
    """Add only missing settings; never rewrite or change existing user values."""
    cleaned = _strip_our_config_lines(original, previous)
    parsed = _load_toml(cleaned, where)
    roots, agent_values = required_config(settings)
    expected = copy.deepcopy(parsed)
    warns: list[str] = []
    root_add = []
    for key, value in roots.items():
        if key not in parsed:
            root_add.append(f"{key} = {_val(value)}  {MANAGED_LINE}\n")
            expected[key] = value
        elif parsed[key] != value:
            warns.append(f"existing {key}={parsed[key]!r} preserved; expected {value!r}")

    if root_add:
        # Top-level keys MUST occur before the first TOML table.
        cleaned = "".join(root_add) + cleaned

    agents_parsed = parsed.get("agents", {})
    if not isinstance(agents_parsed, dict):
        raise InstallationError(f"Expected [agents] to be a table in {where}")
    values_add = []
    for key, value in agent_values.items():
        if key == "max_concurrent_threads_per_session" and "max_threads" in agents_parsed:
            actual = agents_parsed["max_threads"]
            if actual != value:
                warns.append(f"legacy agents.max_threads={actual!r} preserved; expected {value!r}")
            continue
        if key not in agents_parsed:
            values_add.append(f"{key} = {_val(value)}  {MANAGED_LINE}\n")
            expected.setdefault("agents", {})[key] = value
        elif agents_parsed[key] != value:
            warns.append(f"existing agents.{key}={agents_parsed[key]!r} preserved; expected {value!r}")

    if values_add:
        lines = cleaned.splitlines(keepends=True)
        first_agents_table = next((i for i, line in enumerate(lines) if AGENTS_HEADER_RE.fullmatch(line.rstrip("\r\n"))), None)
        if first_agents_table is not None:
            if not lines[first_agents_table].endswith("\n"):
                lines[first_agents_table] += "\n"
            lines[first_agents_table + 1:first_agents_table + 1] = values_add
        else:
            # If [agents.some_role] was already present, write the parent before it.
            child_idx = next((i for i, line in enumerate(lines) if line.strip().startswith("[agents.")), None)
            section = ["[agents]  # codex-triad:section\n", *values_add]
            if child_idx is not None:
                lines[child_idx:child_idx] = section
            else:
                if lines and not lines[-1].endswith("\n"):
                    lines[-1] += "\n"
                lines.extend(section)
        cleaned = "".join(lines)

    if _load_toml(cleaned, where) != expected:
        raise InstallationError("Cannot safely merge this TOML layout; unrelated values would change")
    return cleaned, warns


def merge_agents_md(existing: str, block: str) -> str:
    if (BEGIN in existing) != (END in existing):
        raise InstallationError("AGENTS.md has a partial CODEX-TRIAD marker; repair it manually")
    if BEGIN in existing:
        if existing.count(BEGIN) != 1 or existing.count(END) != 1 or existing.index(BEGIN) > existing.index(END):
            raise InstallationError("AGENTS.md has invalid/duplicated CODEX-TRIAD markers")
        a = existing.index(BEGIN)
        b = existing.index(END) + len(END)
        return existing[:a] + block + existing[b:]
    return existing + ("\n\n" if existing else "") + block + "\n"


def _state_path(project: Path) -> Path:
    return project / ".codex" / STATE_NAME


def _read_state(project: Path) -> dict[str, Any] | None:
    file = _state_path(project)
    if not file.exists():
        return None
    try:
        data = json.loads(read_text(file))
    except (ValueError, OSError) as exc:
        raise InstallationError(f"Could not read {file}: {exc}") from exc
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data.get("schema_version") != 1 or data.get("generator") != "codex-triad":
        raise InstallationError("Unsupported triad-state.json format; manual upgrade required")
    _previous_settings(data)
    _validate_auto_model_roles(data.get("auto_model_roles", []))
    _validate_auto_model_roles(data.get("auto_effort_roles", []))
    if not set(data.get("auto_effort_roles", [])) <= set(data.get("auto_model_roles", [])):
        raise InstallationError("Automatic efforts require automatic model roles")
    hashes = data.get("agent_hashes")
    if not isinstance(hashes, dict) or not set(hashes) <= {f"{n}.toml" for n in AGENT_NAMES}:
        raise InstallationError("Invalid agent hashes in installation manifest")
    for value in [*hashes.values(), data.get("policy_hash")]:
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise InstallationError("Invalid content hash in installation manifest")
    for key in ("config_original_hash", "policy_joiner"):
        if key in data and not isinstance(data[key], str):
            raise InstallationError(f"Invalid {key} in installation manifest")
    for key in ("config_created", "policy_created"):
        if key in data and type(data[key]) is not bool:
            raise InstallationError(f"Invalid {key} in installation manifest")
    if data.get("policy_joiner", "") not in ("", "\n\n"):
        raise InstallationError("Invalid policy joiner in installation manifest")
    return data


def _validate_settings(settings: Settings) -> None:
    if type(settings.max_subagents) is not int or not 1 <= settings.max_subagents <= 16:
        raise InstallationError("max-subagents must be between 1 and 16")
    for attribute in ("main_effort", "advisor_effort", "worker_effort"):
        if getattr(settings, attribute) not in EFFORTS:
            raise InstallationError(f"Invalid reasoning effort for {attribute}")
    for attribute in ("main_model", "advisor_model", "worker_model"):
        model = getattr(settings, attribute)
        if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/@+-]*", model):
            raise InstallationError(f"Invalid model ID for {attribute}")


def _validate_auto_model_roles(roles) -> None:
    if not isinstance(roles, (list, tuple)) or any(role not in ("main", "worker", "advisor") for role in roles) or len(set(roles)) != len(roles):
        raise InstallationError("Invalid automatic role metadata in installation manifest")


_STATE_UNCHECKED = object()


def install(project: Path, settings: Settings, *, dry_run: bool = False, force: bool = False,
            auto_model_roles: tuple[str, ...] = (), auto_effort_roles: tuple[str, ...] = (),
            expected_state: Any = _STATE_UNCHECKED) -> list[str]:
    """Apply a complete assignment; explicit Settings pin roles unless provenance is supplied."""
    project = project.resolve()
    _validate_settings(settings)
    _validate_auto_model_roles(auto_model_roles)
    _validate_auto_model_roles(auto_effort_roles)
    if not set(auto_effort_roles) <= set(auto_model_roles):
        raise InstallationError("Automatic efforts require automatic model roles")
    with nullcontext() if dry_run else project_lock(project):
        return _install(project, settings, dry_run=dry_run, force=force, auto_model_roles=auto_model_roles,
                        auto_effort_roles=auto_effort_roles, expected_state=expected_state)


def _install(project: Path, settings: Settings, *, dry_run: bool, force: bool, auto_model_roles: tuple[str, ...],
             auto_effort_roles: tuple[str, ...], expected_state: Any) -> list[str]:
    project = project.resolve()
    if not project.is_dir():
        raise InstallationError(f"Project directory not found: {project}")
    ensure_no_pending(project)
    config = project / ".codex" / "config.toml"
    agents_md = project / "AGENTS.md"
    agent_paths = [project / ".codex" / "agents" / f"{name}.toml" for name in AGENT_NAMES]
    _assert_safe_paths(project, [config, agents_md, _state_path(project), *agent_paths])
    before = {p: read_bytes(p) for p in [config, agents_md, _state_path(project), *agent_paths]}
    state = _read_state(project)
    if expected_state is not _STATE_UNCHECKED and state != expected_state:
        raise InstallationError("Project model assignment changed during selection; rerun init. Installation was not applied.")
    previous = _previous_settings(state)
    existing_config = read_text(config)
    existing_agents = read_text(agents_md)
    _assert_managed_intact(state, existing_config, existing_agents)
    updated_config, warnings = merge_config(existing_config, settings, config, previous)
    if state is not None and BEGIN in existing_agents and END in existing_agents:
        existing_block = existing_agents[existing_agents.index(BEGIN):existing_agents.index(END) + len(END)]
        previous_hash = state.get("policy_hash") or _hash(instructions_block(previous))
        if _hash(existing_block) != previous_hash and not force:
            raise InstallationError("Triad policy block in AGENTS.md was modified. Merge manually or use --force.")
    updated_agents_md = merge_agents_md(existing_agents, instructions_block(settings))

    desired_agents: dict[Path, str] = {}
    for name in AGENT_NAMES:
        path = project / ".codex" / "agents" / f"{name}.toml"
        rendered = agent_toml(name, settings)
        _load_toml(rendered, path)
        if path.exists():
            current = read_text(path)
            before_hash = (state or {}).get("agent_hashes", {}).get(path.name)
            if before_hash is None:
                raise InstallationError(f"Untracked agent: {path}. Move or rename it manually; --force cannot claim ownership.")
            if not force and before_hash != _hash(current):
                raise InstallationError(f"Locally edited agent: {path}. Merge manually or use --force deliberately.")
        desired_agents[path] = rendered

    changes: dict[Path, str] = {config: updated_config, agents_md: updated_agents_md, **desired_agents}
    # Include selection provenance in the transaction and its dry-run preview.
    manifest = {
        "schema_version": 1,
        "generator": "codex-triad",
        "settings": asdict(settings),
        "agent_hashes": {path.name: _hash(content) for path, content in desired_agents.items()},
        "policy_hash": _hash(instructions_block(settings)),
        "config_created": state.get("config_created", False) if state else not config.exists(),
        "config_original_hash": state.get("config_original_hash", "") if state else _hash(existing_config),
        "policy_created": state.get("policy_created", False) if state else not agents_md.exists(),
        "policy_joiner": state.get("policy_joiner", "") if state and BEGIN in existing_agents else ("\n\n" if existing_agents else ""),
    }
    if auto_model_roles:
        manifest["auto_model_roles"] = list(auto_model_roles)
    if auto_effort_roles:
        manifest["auto_effort_roles"] = list(auto_effort_roles)
    changes[_state_path(project)] = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    messages = [f"{'WOULD INSTALL' if dry_run else 'INSTALL'} {path.relative_to(project)}" for path, new in changes.items()
                if not path.exists() or read_text(path) != new]
    messages.extend(f"WARNING {warning}" for warning in warnings)
    if dry_run:
        for path, new in changes.items():
            old = read_text(path)
            messages.extend(line.rstrip("\n") for line in difflib.unified_diff(
                old.splitlines(keepends=True), new.splitlines(keepends=True),
                fromfile=f"before/{path.relative_to(project).as_posix()}",
                tofile=f"after/{path.relative_to(project).as_posix()}", n=3 if path == _state_path(project) else 0))
        return messages or ["No changes needed"]
    apply_changes(project, {p: text.encode("utf-8") for p, text in changes.items()}, before)
    return messages or ["Already up-to-date"]


def uninstall(project: Path, *, dry_run: bool = False) -> list[str]:
    project = project.resolve()
    with nullcontext() if dry_run else project_lock(project):
        return _uninstall(project, dry_run=dry_run)


def _uninstall(project: Path, *, dry_run: bool) -> list[str]:
    project = project.resolve()
    ensure_no_pending(project)
    _assert_safe_paths(project, [project / ".codex" / "config.toml", project / "AGENTS.md",
                                 _state_path(project), *(project / ".codex" / "agents" / f"{name}.toml" for name in AGENT_NAMES)])
    state = _read_state(project)
    if state is None:
        raise InstallationError("No .codex/triad-state.json found. Refusing to touch untracked files.")
    previous_settings = _previous_settings(state)
    before = {p: read_bytes(p) for p in [project / ".codex/config.toml", project / "AGENTS.md", _state_path(project),
                                         *(project / f".codex/agents/{name}.toml" for name in AGENT_NAMES)]}
    changes: dict[Path, str | None] = {}
    output: list[str] = []
    config = project / ".codex" / "config.toml"
    policy_file = project / "AGENTS.md"
    _assert_managed_intact(
        state,
        read_text(config), read_text(policy_file),
    )
    if config.exists():
        previous = read_text(config)
        new = _strip_our_config_lines(previous, previous_settings)
        if new == previous and MANAGED_LINE in previous:
            output.append("SKIPPED changed or untracked managed config lines; review .codex/config.toml manually")
        # Remove only our empty header; preserve any later user whitespace.
        new = re.sub(r"(?m)^\[agents\][ \t]*# codex-triad:section[^\n]*\n(?=(?:[ \t]*\n)*(?:\[|\Z))", "", new)
        new_parsed = _load_toml(new, config)
        expected = _load_toml(_strip_our_config_lines(previous, previous_settings), config)
        if expected.get("agents") == {} and "agents" not in new_parsed:
            del expected["agents"]
        if new_parsed != expected:
            raise InstallationError("Unsafe managed table removal; merge config manually")
        for candidate in (new, new.removesuffix("\n"), new.removesuffix("\r\n")):
            if _hash(candidate) == state.get("config_original_hash"):
                new = candidate
                break
        if new != previous:
            changes[config] = None if not new and state.get("config_created", True) else new
    agents_md = project / "AGENTS.md"
    if agents_md.exists():
        previous = read_text(agents_md)
        valid = previous.count(BEGIN) == previous.count(END) == 1 and previous.index(BEGIN) < previous.index(END)
        if valid:
            existing_block = previous[previous.index(BEGIN):previous.index(END) + len(END)]
            expected_hash = state.get("policy_hash") or _hash(instructions_block(previous_settings))
            if _hash(existing_block) == expected_hash:
                prefix, suffix = previous.split(existing_block)
                joiner = state.get("policy_joiner", "")
                prefix = prefix.removesuffix(joiner) if joiner else prefix
                new = prefix + suffix.removeprefix("\n")
                changes[agents_md] = None if not new and state.get("policy_created", True) else new
            else:
                output.append("SKIPPED modified AGENTS.md policy block; review manually")
        elif BEGIN in previous or END in previous:
            output.append("SKIPPED malformed AGENTS.md policy markers; review manually")
    for name in AGENT_NAMES:
        path = project / ".codex" / "agents" / f"{name}.toml"
        if path.exists():
            actual = _hash(read_text(path))
            if actual == state.get("agent_hashes", {}).get(path.name):
                changes[path] = None
            else:
                output.append(f"SKIPPED modified agent: {path.relative_to(project)}")
    for path, new in changes.items():
        output.append(f"{'WOULD REMOVE/REVERT' if dry_run else 'REMOVE/REVERT'} {path.relative_to(project)}")
    skipped = any(line.startswith("SKIPPED") for line in output)
    if skipped:
        output.append("PARTIAL_UNINSTALL: manifest retained so edited files can be reconciled safely")
    else:
        changes[_state_path(project)] = None
        output.append(f"{'WOULD REMOVE' if dry_run else 'REMOVE'} .codex/triad-state.json")
    if not dry_run:
        apply_changes(project, {p: value.encode("utf-8") if value is not None else None for p, value in changes.items()}, before)
    return output or ["No managed files to remove"]
