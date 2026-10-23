# Changelog

## Unreleased — 2026-10-24

- Protect default, environment-selected and explicitly supplied Codex homes before installation writes; apply the same shared guard to uninstall/recovery and previews while allowing managed worktrees.
- Preserve installed model, effort and concurrency choices during non-interactive partial updates and repeated init.
- Build wheel/source/skill artifacts from the explicit public-file list in MANIFEST.in; exclude unlisted local code, notes and evaluation data regardless of Git ignore rules.
- Distinguish App Server requests from responses, reject malformed responses, and consume buffered completion events for the exact active turn. Add offline transport regressions and replay the sanitized CLI 0.163.0 fixture through the collector.
- Add opt-in `report --csv PATH --paired` validation for matched task repetitions, frozen conditions, unique run IDs and recorded failures; retain the existing report JSON shape and unknown-cost handling.
- Display the requested AgentShield badge in both READMEs with its provenance and unverified certification scope in SECURITY.md.

## 0.2.0a4 — 2026-10-23 · Public preview preparation

- Lead the bilingual README with `npx skills add`, verify npm-installed helpers and add a pinned skills CLI compatibility check in CI.
- Rebuild bilingual onboarding, repository-scoped skill instructions and current validation documentation.
- Separate the standalone skill archive from development history; verify it without site-packages alongside the clean wheel.
- Add public project metadata, issue/security routes and downloadable CI preview artifacts.
- Document the unresolved desktop setting observation and dedicated-CODEX_HOME isolation requirement without attributing an unproven cause.

## 0.2.0a3 — User-selected role models

- Add opt-in interactive role/model/effort picker using paginated App Server model/list. No generation turns are started.
- Permit model reuse, provider-style model IDs and none/minimal efforts; preserve legacy flags/defaults and protected user config.
- Remove model branding from generated advisor checkpoints and skill role responsibilities.
- Share App Server transport with runtime collection; verify custom assignments with report --runtime-evidence --project.


## 0.2.0a2 — 2026-10-23 · Native runtime evidence and skill

- Verify actual App Server role/parent/child/model/lifecycle records; do not rely on empty exec wait items or assistant self-report.
- Add opt-in `scripts/collect_runtime.py`, offline `report --runtime-evidence`, negative regression cases and a real sanitized fixture.
- Add self-contained root SKILL.md, bundled CLI launcher and skill ZIP; no global skill installation.
- Native CLI 0.163.0 smoke passed on the tested Windows account. Backend identity remains UNKNOWN. No public publication performed.


## 0.2.0a1 — 2026-10-23 · Local preview

- Fix project writes with shared path guards, process lock, byte snapshots, atomic replacement, rollback journal and explicit --recover.
- Refuse junctions, hardlinks, invalid manifests and unknown agent ownership even with --force; validate full TOML semantics around managed edits.
- Preserve UTF-8/CRLF, user whitespace and pre-existing empty files; retain partial-uninstall state.
- Add structured UNKNOWN diagnostics, effort/type checks, quota-aware smoke/evidence instructions and optional offline evaluation/provenance fields.
- Restore build compatibility with declared setuptools minimum, add CLI/fault-injection tests, broaden CI and provide offline ZIP/wheel verification tools.
- Keep all five commands/old flags. Existing schema-1 state remains readable. Intentional security tightening: --force no longer claims unknown files.
- Live three-model identity, enforced advisor gates, cost savings and remote publication remain NOT_VERIFIED/unimplemented.

## 0.1.0 — Initial pre-release

- Four native Codex custom subagent profiles: Astra advisor and three Luna specialists.
- Non-destructive project-local installer with idempotent config merge, dry-run, collision detection, state, and uninstall.
- Static doctor, smoke prompts, bilingual documentation, tests and CI.
- Documented clear limitations: checkpoint instructions are not enforced hooks; no runtime model guarantee or cost-reduction claim.
