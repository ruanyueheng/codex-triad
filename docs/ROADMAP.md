# Roadmap

Status markers: `[x]` implemented, `[ ]` proposed (not promised).

## v0.1 — Reproducible, safe foundation

- [x] Generate official-format Codex custom agents.
- [x] Non-destructive project installation, dry-run and uninstall.
- [x] Config/role doctor with machine-readable JSON.
- [x] Bounded delegated result contracts.
- [x] Smoke prompts for real subagent validation.
- [x] Windows/Linux CI and unit tests.
- [ ] User-reported end-to-end model-selection confirmation on supported Codex desktop/CLI builds.

## v0.2.0a1 — Safe writes and reproducible local delivery

- [x] OS lock, atomic file replacement, transaction rollback and explicit interruption recovery.
- [x] Junction/hardlink guards, strict manifests, safe TOML semantic comparisons.
- [x] CLI integration tests, UNKNOWN diagnostics and optional evaluation/provenance fields.
- [x] Local source ZIP, wheel and clean-environment wheel verification tools.
- [x] Official hooks/SDK/API feasibility assessment, without installing a gate.

## Next — Opt-in observability and evaluation

- [ ] Opt-in, privacy-aware runtime evidence collector for agent/model/thread IDs (only where supported by Codex).
- [ ] Reproducible A/B harness for tasks and real token/cost comparison.
- [ ] Version compatibility matrix with pinned client builds and accepted model IDs.
- [x] Better config migration/rollback reports and conflict inspection.

## v0.3 — Reliable policy engine (research)

- [ ] Investigate supported event hooks or Agents API for deterministic checkpoints.
- [ ] Two-failure signature detector and review-before-commit gate (explicit user opt-in).
- [ ] Safe fallback when advisor model is unavailable; no silent privilege escalation.
- [ ] Limits on wall-time, budget and delegation to prevent runaway agent spawning.

## v1.0 — Production quality target

- [ ] End-to-end Windows/macOS/Linux integration tests against pinned Codex versions.
- [ ] Threat model, compatibility policy, contributor-driven benchmarks.
- [ ] Real performance claims backed by reproducible measurements.
