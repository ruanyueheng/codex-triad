# Codex Triad

[![CI](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml/badge.svg)](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![AgentShield Security](https://merx.help/badge/A+.svg)](https://merx.help/shield)

AgentShield is a third-party scan badge; see its [scope and verification status](SECURITY.md#agentshield-badge).

**Three responsibilities. Your choice of models. One Codex workflow.**

[中文](README.zh-CN.md) · [Install](#install) · [Usage](#usage) · [Guide](docs/GETTING_STARTED.md)

Codex Triad gives implementation, exploration and review their own roles. Choose the models you want, let workers investigate in parallel, and bring in an advisor for decisions and code review.

## Install

Run this in your project:

```bash
npx skills add ruanyueheng/codex-triad --agent codex
```

This uses the [skills CLI](https://github.com/vercel-labs/skills) to install into `.agents/skills/codex-triad/`. Requires Node.js 22.20+; the bundled configuration helper uses Python 3.11+ and your Codex CLI.

## Usage

Open Codex in your project and start with:

```text
$codex-triad
Set up Triad for this project. Let me choose the coordinator,
worker and advisor models from my client's model list.
```

You choose a model and reasoning effort for each responsibility. The same model can serve multiple roles.

Then give it a task:

```text
$codex-triad
Fix the CSV import bug. Have workers investigate the importer and tests,
implement the fix, run the tests, and ask the advisor to review the diff.
```

## Roles

| Responsibility | What it does | Codex roles |
|---|---|---|
| Coordinator | Plans, implements, tests and integrates | Main session |
| Workers | Explore code, research dependencies and diagnose failures | `triad_explorer`, `triad_researcher`, `triad_triage` |
| Advisor | Reviews designs, repeated failures and important changes | `triad_architect` |

Unspecified roles automatically use the latest visible stable Sol (coordinator), Luna (workers) and Astra (advisor). Re-running `init` refreshes automatic choices and preserves manual ones. All three assignments remain configurable.

## CLI

Use the installed helper directly when you want to configure or inspect roles:

```bash
python .agents/skills/codex-triad/scripts/triad.py models --project .
python .agents/skills/codex-triad/scripts/triad.py init --project . --interactive
python .agents/skills/codex-triad/scripts/triad.py doctor --project . --json
```

For suspected model or reasoning-effort drift, add `doctor --check-models` to compare configuration with the current client catalog without generation calls. Missing entries produce warnings. See [model diagnostics](docs/MODEL_ASSIGNMENT.md).

The six commands are `models`, `init`, `doctor`, `smoke`, `uninstall` and `report`. `models --json` exports visible models and reasoning options; `init --interactive` lets you assign each role and effort. Add `--dry-run` to preview installation or removal. See the [guide](docs/GETTING_STARTED.md) for source installation, offline use and examples.

## Tests

Unit/integration tests, Windows/Linux CI on Python 3.11–3.14, clean wheel/skill installation checks, and an observed three-model CLI workflow. Details and reproducible commands are in [validation](docs/VALIDATION.md).

## Documentation

[Model selection](docs/MODEL_ASSIGNMENT.md) · [Architecture](docs/ARCHITECTURE.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Changelog](CHANGELOG.md)

[Contribute](CONTRIBUTING.md) · [Report a bug](https://github.com/ruanyueheng/codex-triad/issues/new/choose) · [Security](SECURITY.md)

MIT · Alpha preview · Community project for Codex.
