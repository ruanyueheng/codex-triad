# Codex Triad 0.2.0a5 — Automatic selection and model discovery

Configure project-local coordinator, worker and advisor models automatically, or choose each model and reasoning effort yourself. This is an alpha preview of a community project.

## Changes / 本版更新

- **Automatic defaults:** fresh `init` resolves the latest visible stable Sol for main, Luna for workers and Astra for advisor. Subsequent init refreshes automatic choices and preserves explicit, interactive and legacy assignments.
- **Model discovery:** new `models` command lists the current client's model IDs and supported/default reasoning efforts; add `--json` for structured output.
- **Manual assignment:** `init --interactive` selects a model and supported effort separately for each responsibility, including model reuse.
- **Safe updates:** automatic efforts adapt to model capabilities; unsupported pinned efforts can be repaired interactively. Stale selections cannot overwrite concurrent choices, and previews show automatic-to-fixed transitions.
- **Workflow guidance:** record regression baselines before edits, check parsing/serialization boundaries end to end, and request advisor review before delivering a nontrivial repair.
- Includes the configuration, packaging, transport and paired-evaluation hardening recorded in [CHANGELOG.md](CHANGELOG.md).

## Quick start / 使用

After installing the skill in your project:

```bash
python .agents/skills/codex-triad/scripts/triad.py models --project .
python .agents/skills/codex-triad/scripts/triad.py init --project . --interactive --dry-run
python .agents/skills/codex-triad/scripts/triad.py init --project . --interactive
```

Without model flags, `init` selects the automatic defaults. If a family is absent, it fails without installing rather than substituting another family. Fully specifying all three model IDs skips discovery and supports offline configuration.

首次默认安装会查询目录；离线安装请明确指定三个模型。已有手动或历史分配保持固定，交互选择也会固定三种职责。

## Validation and limits / 验证与边界

107 local Windows tests passed, including automatic selection, model listing, effort handling, concurrent-choice protection and manifest previews. Real catalog queries and scripted interactive installation completed without generation calls or global configuration changes. Clean wheel and standalone skill installation checks passed. CI checks Windows/Linux with Python 3.11–3.14 for the release commit.

The tested current catalog reports Sol and Astra but no Luna. The CSV repair passed 13 unchanged acceptance tests and 7 independent checks; a revised full workflow timed out before advisor completion. These observations do not establish a complete three-model workflow or a speed, cost or quality advantage. Catalog visibility and client model metadata are not independent backend identity or account-wide access proofs. See [validation](docs/VALIDATION.md).

## Downloads

- `codex-triad-0.2.0a5-skill.zip`: 19-file standalone skill; extract into your project's `.agents/skills/`.
- `codex-triad-0.2.0a5-source.zip`: reviewed source snapshot.
- `codex_triad-0.2.0a5-py3-none-any.whl`: optional Python package installation.
- `SHA256SUMS.txt`: SHA-256 checksums for all three packages.

No PyPI package is published by this release. Keep raw logs, authentication and local Codex homes private.
