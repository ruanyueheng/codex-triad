# Codex Triad

[![CI](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml/badge.svg)](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Give coordination, exploration and review their own models in Codex.**

[中文](README.zh-CN.md) · [Getting started](docs/GETTING_STARTED.md) · [Validation](docs/VALIDATION.md) · [Troubleshooting](docs/TROUBLESHOOTING.md)

Codex Triad is a project-local CLI and Agent Skill for native Codex subagents. Choose a model and reasoning effort for each responsibility, preview the changes, and keep your existing configuration. Use one model for all three responsibilities or a different model for each.

**Alpha preview · Community project, not affiliated with OpenAI.** Review checkpoints are instructions, not enforced hooks. Model access depends on your client and account.

## How it works

| Responsibility | Work | Native roles |
|---|---|---|
| Coordinator | Own the implementation, tests and final result | Main session |
| Workers | Investigate bounded, independent questions | `triad_explorer`, `triad_researcher`, `triad_triage` |
| Advisor | Review consequential decisions, repeated failures and nontrivial commits | `triad_architect` |

```text
Task → coordinator → scoped workers → implementation + tests
                   → advisor at relevant checkpoints → result + evidence
```

The legacy Sol/Luna/Astra preset is optional. Every assignment can be changed; there is no model gateway or automatic fallback.

## Quick start

Requires Python 3.11+. Interactive selection also needs an installed, authenticated Codex CLI with App Server `model/list` support. The tested client is CLI 0.163.0 on Windows; see [compatibility and evidence](docs/VALIDATION.md).

Clone this repository, then run the bundled CLI without installing Python packages:

```bash
git clone https://github.com/ruanyueheng/codex-triad.git
cd codex-triad
python scripts/triad.py --help
```

From this directory, create a disposable target and choose its models:

```bash
mkdir ../triad-demo
python scripts/triad.py init --project ../triad-demo --interactive --dry-run
python scripts/triad.py init --project ../triad-demo --interactive
python scripts/triad.py doctor --project ../triad-demo --json
```

On Windows, `py -3` can replace `python`; on macOS/Linux, use `python3` if needed. A preview does not save your selection: the second command asks again. Model catalog lookup may contact the configured service; it does not start a generation turn. A listed model is not proof of account access.

Next, inspect the generated files, open the **target project** in Codex, trust it only after review, and start a new session. Ask the coordinator to use Triad for a task that benefits from scoped investigations and review. Verify actual child activity rather than assuming that installation started agents.

No CLI or network access yet? Try the [offline walkthrough](docs/GETTING_STARTED.md#offline-walkthrough) first. The five commands also work as `python -m codex_triad` after a [virtual-environment installation](docs/GETTING_STARTED.md#optional-python-package-installation). This project is not published to PyPI.

## Use as a skill

The repository root contains `SKILL.md` and its supporting runtime. A clone alone does not register a skill with Codex.

Extract the built `codex-triad-<version>-skill.zip` into your target repository's `.agents/skills/`. It must contain `.agents/skills/codex-triad/SKILL.md`, `scripts/`, `src/`, `docs/` and `evaluation/`. Then invoke:

```text
$codex-triad
Inspect this project's model assignments, then fix the failing tests.
Use scoped workers where useful, keep one implementation owner,
and ask the configured advisor to review the actual diff and test results.
```

Alternatively, explicitly ask Codex to read the cloned repository's `SKILL.md` by its absolute path. See [skill setup, examples and removal](docs/GETTING_STARTED.md#use-the-skill). Local skill discovery follows [official Codex guidance](https://learn.chatgpt.com/docs/build-skills).

## What changes in your project

Triad manages a marked section of `AGENTS.md`, marked additions to `.codex/config.toml`, four role TOMLs and an ownership manifest. It preserves existing settings and refuses unknown file collisions. Inspect conflicts with `doctor`; `--force` does not override unrelated configuration.

```bash
python scripts/triad.py uninstall --project ../triad-demo --dry-run
python scripts/triad.py uninstall --project ../triad-demo
```

Uninstall keeps user-edited files and reports partial removal. It may leave empty directories and a lock file. Interrupted writes can be recovered explicitly; see [safe storage](docs/ADR-001-SAFE-INSTALL.md).

## Verification, without inflated claims

- Unit and integration tests cover configuration merging, preservation, rollback, concurrency, model selection and negative runtime-evidence cases.
- CI runs on Windows and Linux with Python 3.11–3.14, builds the archives, installs a clean wheel and checks the standalone skill.
- An observed CLI App Server run supplies role, parent/child, model activity and ordering evidence. A separate repair exercise passed 20 project tests and 7 independent checks.
- These results do not prove backend model identity, universal account access, enforced review or lower cost. The [validation report](docs/VALIDATION.md) includes an unresolved desktop configuration-persistence observation.

Offline verification of the supplied, sanitized runtime fixture:

```bash
python scripts/triad.py report --runtime-evidence evaluation/cli-runtime-20261023.json --json
```

`doctor` checks local configuration; `smoke` prints prompts. Neither proves successful model calls. Live collection is opt-in, consumes quota, and should use a separately configured `CODEX_HOME` when isolation is required. See [native runtime verification](docs/CLI_NATIVE_VERIFICATION.md).

## Documentation and development

[Model assignments](docs/MODEL_ASSIGNMENT.md) · [Architecture](docs/ARCHITECTURE.md) · [Evaluation](docs/EVALUATION.md) · [Roadmap](docs/ROADMAP.md) · [Changelog](CHANGELOG.md)

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/build_release.py
python tools/check_wheel.py
```

The runtime uses only the Python standard library; builds need setuptools and wheel. Commands and artifact checks are detailed in [CONTRIBUTING.md](CONTRIBUTING.md). Build output is in `dist/`; successful CI runs also retain preview artifacts.

Report bugs through [Issues](https://github.com/ruanyueheng/codex-triad/issues/new/choose). For sensitive reports, use the [security policy](SECURITY.md), not public logs. Contributions that improve reproducibility and compatibility are welcome.

[MIT license](LICENSE). README organization was informed by [uv](https://github.com/astral-sh/uv), [ripgrep](https://github.com/BurntSushi/ripgrep) and [Anthropic Skills](https://github.com/anthropics/skills); no affiliation or endorsement is implied.
