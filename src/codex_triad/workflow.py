"""Start a real Codex task with a task-appropriate collaboration style."""
from pathlib import Path
import shutil
import tomllib

from .storage import assert_safe_paths, read_text


MODES = {
    "auto": "Inspect the task and choose the smallest useful team. Handle focused changes directly; use workers for independent unknowns and an advisor for consequential decisions. Do not ask the user to select a mode.",
    "quick": "The coordinator handles the task directly. Do not spawn subagents for this task unless the user later asks for collaboration. Keep investigation and checks proportional to the change.",
    "team": "Use workers for independent investigation where the task permits parallel work. The coordinator implements and integrates. Ask an advisor to review the resulting substantive change once; do not manufacture parallel tasks for a trivial change.",
    "review": "Perform a read-only review of the requested target. Report concrete findings with locations, impact and suggested fixes. Do not edit files or implement fixes in this mode.",
}


class WorkflowError(ValueError):
    pass


def task_prompt(task: str, mode: str = "auto", *, project: Path | None = None) -> str:
    if not isinstance(task, str) or not task.strip():
        raise WorkflowError("Describe the task to start.")
    if mode not in MODES:
        raise WorkflowError(f"Unknown task mode: {mode}")
    target = ""
    if project is not None:
        project = project.resolve()
        if not project.is_dir():
            raise WorkflowError("Project directory not found")
        target = f"\nTarget project: {project}\nWork in this directory; do not silently substitute the current chat's project.\n"
    return f"""Carry out this task using Codex Triad. Read the project's instructions first.
{target}

Collaboration mode: {mode}
{MODES[mode]}

Use the current session and existing project model/permission choices. If native
triad_explorer, triad_researcher, triad_triage or triad_architect roles are available,
use the appropriate configured roles. Otherwise use available agent tools, or work
directly when delegation is unavailable, and briefly state the actual arrangement.
Do not turn a task into a configuration wizard or change model/provider settings
just to start. Never claim that unavailable roles or unobserved models were used.

For implementation requests, proceed from investigation through the working change;
a plan alone is not the deliverable. Ask only for missing information that materially
changes the result, while continuing independent work. Give workers bounded questions
and keep source edits with the coordinator unless the user assigns other writers.
Respect existing authorization for commits, publishing and destructive actions.

Keep updates about user-visible progress and decisions. Validate the changed behavior
and required project checks; expand testing only for a concrete unresolved concern.
Finish with what now works, how to use or inspect it, and material limitations.

User task:
{task}
"""


def codex_command() -> list[str]:
    executable = shutil.which("codex")
    if not executable:
        raise WorkflowError("Codex CLI not found. Copy the task into your current Codex chat, or install the CLI.")
    path = Path(executable)
    if path.suffix.lower() in (".cmd", ".bat", ".ps1"):
        # Bypass npm's Windows shell shim so task text cannot become shell syntax.
        entry = path.parent / "node_modules/@openai/codex/bin/codex.js"
        local_node = path.parent / "node.exe"
        node = str(local_node) if local_node.is_file() else shutil.which("node")
        if not entry.is_file() or not node or Path(node).suffix.lower() != ".exe":
            raise WorkflowError("Cannot safely launch this Codex script wrapper. Use the native CLI or the npm Codex installation, or copy the task into your current chat.")
        return [node, str(entry)]
    return [executable]


def task_command(project: Path, task: str, mode: str = "auto") -> list[str]:
    project = project.resolve()
    if not project.is_dir():
        raise WorkflowError("Project directory not found")
    prompt = task_prompt(task, mode, project=project)
    command = [*codex_command(), "--cd", str(project)]
    if mode == "review":
        command.extend(["--sandbox", "read-only"])
    return [*command, prompt]


def project_models(project: Path) -> dict[str, str]:
    """Read the actual project choices without querying or rewriting the client."""
    project = project.resolve()
    paths = [project / ".codex/config.toml", project / ".codex/agents/triad_explorer.toml",
             project / ".codex/agents/triad_architect.toml"]
    assert_safe_paths(project, paths)
    config, worker, advisor = [tomllib.loads(read_text(path)) for path in paths]
    agents = config.get("agents", {})
    return {"main": str(config.get("model") or "沿用 Codex 当前模型"),
            "worker": str(worker.get("model") or (agents.get("default_subagent_model") if isinstance(agents, dict) else None) or "由当前会话安排"),
            "advisor": str(advisor.get("model") or "由当前会话安排")}
