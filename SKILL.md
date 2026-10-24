---
name: codex-triad
description: Set up or use a project-local Codex workflow with user-selected coordinator, worker and advisor models, bounded research, implementation and review. Use when the user requests Codex Triad, three-tier model collaboration, or its installation and runtime verification; skip trivial changes that do not benefit from delegation.
---

# Codex Triad

Read the project's existing model assignment and preserve manual choices. By default, `init` queries the current client's visible catalog and selects the latest stable Sol for coordinator/implementation, Luna for worker/exploration, and Astra for advisor/review. Re-running `init` refreshes automatic assignments; explicit model flags or interactive choices pin those roles. Historical manifests retain their saved assignments. Users may assign any model to any responsibility and reuse models. Offer `init --interactive` when they want to choose. Catalog visibility is not proof of account access or subagent compatibility; report a missing family or failed call without silently substituting models. For offline setup, specify all three model IDs explicitly.

Use `models --project PATH` to inspect the current client's model IDs and supported/default reasoning efforts before setup; add `--json` for structured output. It queries the catalog without installing roles or starting generation turns. Interactive setup lets the user choose a model and supported effort separately for each responsibility, including model reuse.

## Choose the operation

- **Use the workflow:** inspect the task and acceptance criteria. Delegate independent bounded questions to the configured workers when useful, wait for evidence, let the configured coordinator own source changes and tests, and send the actual design/diff/test evidence to the configured advisor at relevant checkpoints. If no agent interface exists, report that limitation and perform an explicitly disclosed single-agent fallback.
- **Install or remove project roles:** run the bundled CLI through `python <skill-folder>/scripts/triad.py`. This loads only the bundled standard-library package; it does not install Python packages globally. Preview `init --project PATH --dry-run` before installation. Use `uninstall --dry-run` before removal. Keep unknown files and existing model/provider/permission settings protected. Never install into the Codex home or modify global config to make a test pass.
- **Verify native roles:** follow [native verification](docs/CLI_NATIVE_VERIFICATION.md). Static doctor and successful independent model requests are separate from actual delegation. Require protocol role/parent/child/model/lifecycle evidence; do not accept assistant self-report as proof.

Do not copy credentials into this skill, a repository, reports, prompts or archives. Reuse the client's normal authentication. Runtime tests can consume quota: perform them only when the user's task authorizes actual calls. Installation, static doctor and offline report do not call models. Publishing to GitHub/PyPI or changing repository visibility requires the user's explicit destination and authorization; this skill is not publication consent.

When the user requires configuration isolation, run model tests through a child CLI/App Server with a separately configured `CODEX_HOME`, as described in [native verification](docs/CLI_NATIVE_VERIFICATION.md). A project directory alone does not isolate client preferences. Do not use desktop agent model/effort overrides to establish that guarantee when their persistence scope is unknown. Compare global config hashes before and after without recording its contents; a mismatch must be disclosed and investigated, never reported as unchanged. Stop further overrides after a mismatch and do not overwrite concurrent user changes.

## Delegation contract

Each child receives one goal, allowed paths, relevant evidence, constraints and expected output. Reports separate observed evidence from inference and unknowns. Explorer: EVIDENCE/ANSWER/UNRESOLVED. Researcher: FINDING/SOURCE/LIMITS/RECOMMENDATION. Triage: FAILURE_SIGNATURE/EVIDENCE/HYPOTHESES/NEXT_TEST/UNCERTAINTY. Keep worker reports near 300 words or less.

For regressions, record the original failing tests before edits and preserve supplied acceptance tests unless the user asks to revise them. Complete worker baseline investigations before source edits, or give workers an immutable snapshot; label later findings as observations of modified code. For parsing or serialization changes, check an end-to-end or round-trip case across the changed boundary. Use byte comparisons when encoding or embedded newline preservation matters.

Only the coordinator edits unless the user explicitly assigns other writers. Worker/advisor read-only instructions are behavioral constraints; their actual sandbox and permissions follow the parent.

Request the configured advisor before consequential architecture/security/migration decisions, after two fixes with the same failure signature without progress, or before delivering or committing a nontrivial repair. Supply actual related code, diff, constraints and observed tests. Resolve concrete blockers and rerun affected checks before delivery; avoid repeated review of unchanged evidence. Ask for VERDICT, BLOCKERS, RISKS, NEXT_ACTIONS and UNCERTAINTIES, at most about 450 words. These checkpoints are advisory; do not call them enforced hooks.

## Finish with evidence

Report what changed, observed tests, real agent activity, unresolved issues and the practical scope of verification. Keep configured model IDs, client runtime model metadata and independent provider-side identity distinct. Never guess tokens/costs or claim savings without measured comparable data.

For recovery or local-file conflicts use the existing CLI's ownership checks; see [safe storage](docs/ADR-001-SAFE-INSTALL.md) only when needed. For protocol observations, flags and proof requirements use [native verification](docs/CLI_NATIVE_VERIFICATION.md).

For user-selected role models and reasoning options, read [model assignment](docs/MODEL_ASSIGNMENT.md) when configuring or changing the mapping.
