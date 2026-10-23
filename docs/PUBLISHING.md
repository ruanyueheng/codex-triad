# GitHub publication checklist / 发布清单

Repository: [ruanyueheng/codex-triad](https://github.com/ruanyueheng/codex-triad). Visibility changes and releases require explicit maintainer authorization. Making source public is separate from publishing a GitHub Release or a PyPI package.

1. Inspect the Git diff and **all reachable history**, not only current/ignored files, for secrets and private data. A pattern scan is not a complete security audit.
2. Keep logs, authentication, Codex homes and recovery journals outside the repository; confirm archives contain only reviewed paths.
3. Run unit tests, compile checks, artifact build, clean wheel and extracted skill checks. Exercise the documented offline lifecycle in a fresh directory.
4. Verify Windows/Linux × Python 3.11–3.14 CI for the exact commit. Separate static checks, runtime metadata and unverified backend claims.
5. If authorized live checks are needed, use a separate child CODEX_HOME, a disposable trusted project and private output. Compare local global-config hashes before/after.
6. Review MIT attribution, README links, package version, changelog and issue/security routes. Do not imply OpenAI endorsement, trademark clearance or measured savings.
7. Push the reviewed commit and change visibility only after verification. Enable private vulnerability reporting when supported, then verify anonymous repository access.

## For a later release

Update the version in `pyproject.toml` and `src/codex_triad/__init__.py`, release notes and versioned examples. Build with installed setuptools/wheel:

```bash
python tools/build_release.py
python tools/check_wheel.py
```

Review the wheel, source ZIP, lean skill ZIP and SHA256SUMS. Tag/upload only after explicit release authorization; do not create a PyPI listing as a side effect. Keep alpha releases marked prerelease until compatibility justifies a stable label.

## Documentation references

README organization draws from [uv](https://github.com/astral-sh/uv) (scope and quick start), [ripgrep](https://github.com/BurntSushi/ripgrep) (navigation, reproducible evidence and limitations) and [Anthropic Skills](https://github.com/anthropics/skills) (self-contained skills and concrete examples). These are organizational references, not copied implementation or endorsements.
