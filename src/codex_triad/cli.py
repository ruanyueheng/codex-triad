"""Cross-platform, stdlib-only CLI for installing Codex Triad into existing projects."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .checker import diagnose
from .benchmark import BenchmarkError, summarize
from .installer import InstallationError, install, uninstall
from .templates import EFFORTS, Settings
from .storage import recover
from .evidence import EvidenceError, verify_runtime
from .models import ModelSelectionError, choose_settings, discover_models
from .installer import _previous_settings, _read_state
from .storage import assert_safe_paths

SMOKE = {
    "workers": """Running this prompt in Codex may consume model quota. This command only prints instructions.
Read-only smoke test. Please spawn two *real* named Codex subagents concurrently:
triad_explorer: locate the program entry points with file/symbol references;
triad_researcher: identify dependency declarations and runtime versions with file references.
Wait for both. Do not modify files, run migrations, commit, or push.
Report the observed spawn statuses and each agent's output. If UI/runtime does not expose
actual model identity, say MODEL_NOT_VERIFIED (do not infer it from TOML or agent self-report).
If any spawn fails, include the exact error and do not simulate subagents inside the main thread.""",
    "advisor": """Running this prompt in Codex may consume model quota. This command only prints instructions.
Read-only smoke test. Spawn the real triad_architect subagent to review the current
project's architecture, with scope limited to major entry points and documented interfaces.
Do not edit, commit, push, or deploy. Report the actual spawn result and explicit agent model
if the runtime exposes it; otherwise say MODEL_NOT_VERIFIED, not success-by-assumption.""",
}
EVIDENCE_REQUEST = """
Record client/version/date, requested agent name, observed thread ID/status, effective model
and effort (or UNKNOWN/MODEL_NOT_VERIFIED), outcome and original error. Keep raw evidence
locally and redact secrets. Use evaluation/runtime-evidence.template.json where available."""


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-triad", description="Configure and validate tiered Codex subagents safely")
    subs = parser.add_subparsers(dest="command", required=True)
    init = subs.add_parser("init", help="Install/upgrade project-scoped agents with non-destructive config merging")
    init.add_argument("--project", type=Path, default=Path.cwd())
    init.add_argument("--main-model")
    init.add_argument("--advisor-model")
    init.add_argument("--worker-model")
    init.add_argument("--main-effort", choices=EFFORTS)
    init.add_argument("--advisor-effort", choices=EFFORTS)
    init.add_argument("--worker-effort", choices=EFFORTS)
    init.add_argument("--interactive", action="store_true", help="Query client-visible models and assign models/efforts to all three responsibilities")
    init.add_argument("--codex-home", type=Path, help="Optional configured Codex home for model discovery, child process only")
    init.add_argument("--system-proxy", action="store_true", help="Inherit system proxy for model discovery in the child only")
    init.add_argument("--max-subagents", type=int)
    init.add_argument("--dry-run", action="store_true")
    init.add_argument("--recover", action="store_true", help="Restore an interrupted transaction only; do not install")
    init.add_argument("--force", action="store_true", help="Replace locally edited Triad agent files or marked policy (never unrelated config)")
    doctor = subs.add_parser("doctor", help="Static checks (never claims live model availability)")
    doctor.add_argument("--project", type=Path, default=Path.cwd())
    doctor.add_argument("--json", action="store_true", help="Print machine-readable report")
    smoke = subs.add_parser("smoke", help="Print a real subagent test prompt for use in Codex")
    smoke.add_argument("--phase", choices=tuple(SMOKE), default="workers")
    remove = subs.add_parser("uninstall", help="Remove managed Triad additions; keep unrelated files")
    remove.add_argument("--project", type=Path, default=Path.cwd())
    remove.add_argument("--dry-run", action="store_true")
    remove.add_argument("--recover", action="store_true", help="Restore an interrupted transaction only; do not uninstall")
    report = subs.add_parser("report", help="Summarize user-recorded offline evaluation CSV; no model calls")
    source = report.add_mutually_exclusive_group(required=True)
    source.add_argument("--csv", type=Path, help="Measured experiment rows")
    source.add_argument("--runtime-evidence", type=Path, help="Validate supplied App Server role/thread/model records offline")
    report.add_argument("--json", action="store_true", help="Print machine-readable summary")
    report.add_argument("--paired", action="store_true", help="Require matched baseline/triad CSV runs with frozen provenance and acceptance commands")
    report.add_argument("--project", type=Path, help="Read this project's model assignment for runtime evidence verification")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command in ("init", "uninstall") and args.recover:
            if args.dry_run:
                raise InstallationError("--recover cannot be combined with --dry-run")
            project = args.project.resolve()
            assert_safe_paths(project, [project / ".codex/.triad.lock"], codex_home=getattr(args, "codex_home", None))
            for item in recover(args.project):
                print(item)
            return 0
        if args.command == "init":
            project = args.project.resolve()
            if not project.is_dir():
                raise InstallationError("Project directory not found")
            assert_safe_paths(project, [project / ".codex/triad-state.json"], codex_home=args.codex_home)
            defaults = _previous_settings(_read_state(project)) or Settings()
            settings = Settings(**{key: getattr(args, key) if getattr(args, key) is not None else getattr(defaults, key) for key in
                ("main_model", "advisor_model", "worker_model", "main_effort", "advisor_effort", "worker_effort")},
                max_subagents=args.max_subagents if args.max_subagents is not None else defaults.max_subagents)
            if args.interactive:
                catalog = discover_models(project, codex_home=args.codex_home, system_proxy=args.system_proxy)
                settings = choose_settings(catalog, settings, ask=input, show=print)
            for item in install(args.project, settings, dry_run=args.dry_run, force=args.force):
                print(item)
            if not args.dry_run:
                print("Next: trust/open the project in local Codex; run `codex-triad doctor`, then `codex-triad smoke`. No runtime model calls have been made.")
            return 0
        if args.command == "doctor":
            results = diagnose(args.project)
            if args.json:
                print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))
            else:
                for r in results:
                    print(f"[{r.level}] {r.code}: {r.message}")
            return 1 if any(r.level == "FAIL" for r in results) else 0
        if args.command == "smoke":
            print(SMOKE[args.phase] + EVIDENCE_REQUEST)
            return 0
        if args.command == "report":
            if args.paired and not args.csv:
                raise BenchmarkError("--paired requires --csv")
            if args.runtime_evidence:
                settings = Settings()
                if args.project:
                    project = args.project.resolve()
                    assert_safe_paths(project, [project / ".codex/triad-state.json"])
                    settings = _previous_settings(_read_state(project))
                    if settings is None:
                        raise EvidenceError("No model assignment found in the target project")
                result = verify_runtime(args.runtime_evidence, settings)
                print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else
                      "PASS: three role threads and runtime models, overlapping workers, advisor after workers. Backend identity UNKNOWN.")
                return 0
            results = summarize(args.csv, paired=args.paired)
            if args.json:
                print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))
            else:
                if args.paired:
                    print(f"Validated {results[0].sample_count} baseline/triad task pairs; failed runs included.")
                for r in results:
                    print(f"[{r.strategy.upper()}] {r.sample_count} runs, {r.success_count} passed "
                          f"({r.success_count / r.sample_count:.1%}); median {r.median_seconds:.2f}s; "
                          f"tokens in/out {r.total_input_tokens if r.total_input_tokens is not None else 'UNKNOWN'}/"
                          f"{r.total_output_tokens if r.total_output_tokens is not None else 'UNKNOWN'}; "
                          f"reported cost USD {r.total_cost_usd if r.total_cost_usd is not None else 'UNKNOWN'}")
                print("Descriptive summary only; no live telemetry, causal claims, or token price inference.")
            return 0
        if args.command == "uninstall":
            for item in uninstall(args.project, dry_run=args.dry_run):
                print(item)
            return 0
    except (InstallationError, BenchmarkError, EvidenceError, ModelSelectionError, OSError, UnicodeError, EOFError, KeyboardInterrupt) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
