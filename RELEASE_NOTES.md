# Codex Triad 0.2.0a4 — Public preview

Project-local coordination, exploration and advisory review with user-selected Codex models. This is an alpha preview, not an official OpenAI project or a production policy engine.

## Included

- Five compatible commands: `init`, `doctor`, `smoke`, `uninstall`, `report`.
- Interactive model/effort assignment and reuse, preserving existing settings.
- Ownership-aware installation/removal, conflict checks, atomic replacement and explicit recovery.
- A self-contained skill ZIP with runtime and necessary references, separate from development history.
- Offline runtime evidence verification and opt-in live collection.
- Windows/Linux CI across Python 3.11–3.14, clean wheel and standalone skill checks.

## Changes in this preview

- Reorganize bilingual onboarding around installation, concrete workflow and observed evidence.
- Add repository-scoped skill setup, offline walkthrough, current compatibility and contribution/security routes.
- Test the extracted skill with site-packages disabled; omit development files from its archive.
- Disclose the unresolved desktop global-setting observation and require a dedicated child CODEX_HOME for isolated tests.

## Limits

Native runtime metadata was observed on the tested Windows client/account. It does not prove independent backend identity or universal access. Advisory checks and read-only instructions are not enforced hooks or independent sandboxes. Speed/cost advantage and macOS native integration remain untested. See [validation](docs/VALIDATION.md).

Build `dist/` locally or use preview artifacts from [CI](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml). No PyPI package has been published; public source does not imply a stable release.
