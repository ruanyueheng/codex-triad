> Source: [ruanyueheng/codex-triad](https://github.com/ruanyueheng/codex-triad) (currently private). Clone the whole repository for the self-contained skill; copying only SKILL.md is insufficient.

> 0.2.0a3: assign any client-visible model to coordinator, worker or advisor with `python scripts/triad.py init --project PATH --interactive --dry-run`. Reasoning options follow the selected model; reuse is allowed. Omit --dry-run to install project settings.

> 0.2.0a3: native CLI App Server role/thread/model activity has been observed. A self-contained skill and offline evidence verifier are included. See [native verification](docs/CLI_NATIVE_VERIFICATION.md). Independent backend identity and other accounts/versions remain unverified.

# Codex Triad

[中文说明](README.zh-CN.md) · [Architecture](docs/ARCHITECTURE.md) · [Validation](docs/work/VALIDATION_REPORT.md) · [Security](SECURITY.md)

**0.2.0a3 local preview. Not an official OpenAI project.** Triad installs native Codex custom-agent configuration. It is not a model gateway or an enforced scheduler.

These are legacy defaults only; users can replace every assignment:

- `gpt-6.1-sol`: coordinator and source implementation.
- `gpt-6-luna`: bounded Explorer, Researcher and Triage investigations.
- `gpt-6-astra`: consequential design/security, repeated-failure and pre-commit advice.

These are configured targets. Account access, actual child threads and effective model identities are **NOT_VERIFIED**. Read-only instructions do not create a separate sandbox.

## Quick start

Python 3.11+. Extract the source ZIP and enter the directory containing `pyproject.toml`. No remote repository is needed.

```powershell
py -3 -m pip install -e .
py -3 -m codex_triad --help
codex-triad init --project "C:\Projects\MyApp" --dry-run
codex-triad init --project "C:\Projects\MyApp"
codex-triad doctor --project "C:\Projects\MyApp" --json
codex-triad smoke --phase workers
codex-triad smoke --phase advisor
```

Use `py -3 -m codex_triad` if the console entry point is not on PATH. On macOS/Linux use `python3` and a local project path. For offline installation with existing build tools add `--no-index --no-deps --no-build-isolation`; ordinary pip installation may download build tooling. Triad commands themselves make no network requests.

Smoke only prints prompts. Executing them in Codex may consume quota. Start a new session in a trusted disposable project, inspect real root/child model and thread evidence, and retain `MODEL_NOT_VERIFIED` where identity is unavailable. Follow the [runtime checklist](docs/RUNTIME_VERIFICATION.md).

## Configuration and removal

```bash
codex-triad init --project ./my-app --main-model gpt-6.1-sol --advisor-model gpt-6-astra --worker-model gpt-6-luna --main-effort high --advisor-effort high --worker-effort medium --max-subagents 3
codex-triad uninstall --project ./my-app --dry-run
codex-triad uninstall --project ./my-app
```

The installer manages marked additions in `AGENTS.md` and `.codex/config.toml`, four `.codex/agents/triad_*.toml` files and a local ownership manifest. Existing configuration is preserved with conflict warnings. `--force` replaces only manifest-owned agent files or policy blocks; it never claims unknown files or overrides edited config entries. Existing schema-1 manifests remain supported.

Actual operations use an OS lock, per-file atomic replacement and a local recovery journal. Existing Windows DACLs are preserved; new/staging files are owner-only, so other runtime identities require explicit access. Caught failures attempt rollback. After process interruption, inspect local backups and run `codex-triad init --project ./my-app --recover` (also accepted by uninstall). Recovery is a separate operation and refuses to overwrite later edits. The temporary journal may contain sensitive original configuration in base64, not encryption; never upload it. Successful completion removes it. Empty directories and `.triad.lock` remain. See [ADR-001](docs/ADR-001-SAFE-INSTALL.md).

Install previews show diffs without writing. Uninstall previews list removal/reversion/retention actions. Previews can include local edits; sanitize before sharing. Invalid files, symlinks, junctions, hardlinks and unsafe-to-merge TOML layouts fail conservatively.

## Diagnosis and delegation

`doctor --json` returns an array of `level/code/message` checks. PASS concerns a static project fact. FAIL indicates an error; WARN requires review; UNKNOWN includes runtime capabilities, trust, effective model and account access. Exit codes: 0 when no FAIL exists (UNKNOWN can remain), 1 for a failed diagnosis, 2 for operation/argument errors.

The coordinator owns edits. Every delegated input contains goal, scope, evidence, constraints and expected output. Roles return bounded evidence and uncertainty; see the [contracts](docs/ARCHITECTURE.md). Advisor checkpoints remain **advisory/prompt-based**. No hooks, global model/proxy/permission changes, credential reads, log uploads or model calls are installed by default. [Official compatibility and P2 assessment](docs/OFFICIAL_COMPATIBILITY.md).

## Evaluation and development

```bash
python -m unittest discover -s tests -v
codex-triad report --csv path/to/measured-runs.csv --json
python -m compileall -q src tests tools
python tools/build_release.py
python tools/check_wheel.py
```

The offline report retains legacy CSV compatibility and adds optional context, subagent count, quality and provenance metrics. Missing values remain JSON null / text UNKNOWN, never inferred costs. Five task categories and a runtime evidence template are provided; no benchmark improvement is claimed. See [evaluation](docs/EVALUATION.md).

[Validation and remaining work](docs/work/VALIDATION_REPORT.md) · [Audit](docs/work/AUDIT_FINDINGS.md) · [Changes](docs/work/CHANGE_SUMMARY.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md) · [Publishing](docs/PUBLISHING.md) · [Roadmap](docs/ROADMAP.md)

MIT licensed. Repository/name/trademark availability, maintainer contact and remote CI still require release review. The source is now authorized for upload to the private repository; public publication remains a separate decision.
