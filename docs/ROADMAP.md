# Roadmap

Status markers: `[x]` implemented, `[ ]` proposed (not promised).

## Immediate priorities — 2026-10-26

The user-facing task workbench is now implemented: project selection, task templates, four collaboration modes, prompt preview/copy and interactive Codex launch. Runtime execution remains in the native Codex client.

1. [x] Diagnose installed model/effort drift with opt-in `doctor --check-models`; keep catalog matching distinct from generation access.
2. [x] Surface transport failures promptly and close CLI launchers gracefully; cover EOF, malformed streams, inherited pipes and bounded shutdown.
3. [ ] Expand the client compatibility fixtures to additional pinned releases and macOS, retaining actual failure records.
4. [ ] Collect repeated paired task measurements, including failed and timed-out runs, before claiming collaboration quality, speed or cost gains.

The next evidence gap is repeatable client compatibility and measured task outcomes. A new scheduler remains research until supported event contracts and concrete user needs justify its maintenance cost.

## v0.1 — Reproducible, safe foundation

- [x] Generate official-format Codex custom agents.
- [x] Non-destructive project installation, dry-run and uninstall.
- [x] Config/role doctor with machine-readable JSON.
- [x] Bounded delegated result contracts.
- [x] Smoke prompts for real subagent validation.
- [x] Windows/Linux CI and unit tests.
- [x] Native CLI model/role/thread confirmation on the tested Windows CLI 0.163.0 account; not a universal compatibility claim.

## v0.2.0a1 — Safe writes and reproducible local delivery

- [x] OS lock, atomic file replacement, transaction rollback and explicit interruption recovery.
- [x] Junction/hardlink guards, strict manifests, safe TOML semantic comparisons.
- [x] CLI integration tests, UNKNOWN diagnostics and optional evaluation/provenance fields.
- [x] Local source ZIP, wheel and clean-environment wheel verification tools.
- [x] Official hooks/SDK/API feasibility assessment, without installing a gate.

## Next — Opt-in observability and evaluation

- [x] Opt-in, privacy-aware runtime evidence collector for agent/model/thread IDs (only where supported by Codex).
- [ ] Reproducible A/B harness for tasks and real token/cost comparison.
- [x] Offline paired CSV validation for frozen task conditions, repeated trials and retained failures; real measurements remain pending.
- [ ] Version compatibility matrix with pinned client builds and accepted model IDs.
- [x] Offline App Server transport regressions and collector replay of the sanitized CLI 0.163.0 fixture.
- [x] Better config migration/rollback reports and conflict inspection.
- [x] User-selected models and reasoning efforts, including model reuse across responsibilities.
- [x] Standalone skill archive with isolated, site-packages-free lifecycle verification.
- [ ] Identify the source of the desktop global-setting change documented in [validation](VALIDATION.md).
- [ ] Additional account/client-version reports and macOS native integration.

## v0.3 — Reliable policy engine (research)

- [ ] Investigate supported event hooks or Agents API for deterministic checkpoints.
- [ ] Two-failure signature detector and review-before-commit gate (explicit user opt-in).
- [ ] Safe fallback when advisor model is unavailable; no silent privilege escalation.
- [ ] Limits on wall-time, budget and delegation to prevent runaway agent spawning.

## v1.0 — Production quality target

- [ ] End-to-end Windows/macOS/Linux integration tests against pinned Codex versions.
- [ ] Threat model, compatibility policy, contributor-driven benchmarks.
- [ ] Real performance claims backed by reproducible measurements.
