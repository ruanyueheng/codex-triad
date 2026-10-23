# Contributing

Small, reproducible fixes are welcome. Start with [Issues](https://github.com/ruanyueheng/codex-triad/issues); discuss breaking configuration, routing or permission changes first.

## Development setup

Python 3.11+; runtime dependencies are standard-library-only. Use a virtual environment, install the checkout with `python -m pip install -e .`, then run:

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests tools scripts
python tools/build_release.py
python tools/check_wheel.py
```

Builds need setuptools>=68 and wheel; normal pip may fetch tooling. CI runs these checks on Windows/Linux with Python 3.11–3.14. Artifact checks install a clean wheel and exercise the extracted skill without site-packages.

## Pull requests

1. Open an issue for breaking model-routing, config-format, or installation behavior changes.
2. Keep the CLI Python-standard-library-only unless a compelling need is documented.
3. Add unit tests for parsing, idempotency, collision safety, uninstall behavior, and Windows support.
4. Do not add screenshots or benchmark numbers without provenance, client/build, task details and protocol.
5. Never commit private `.codex/config.toml` files containing provider endpoints/tokens; sanitize all logs.
6. Explain whether behavior is a deterministic capability, an AGENTS.md instruction, or a user-observed result.
7. Add new public source, tests, fixtures and docs to the explicit `MANIFEST.in` file list; release builds exclude unlisted files. Do not add wildcard includes or private evaluation data.

Describe the concrete failure, resulting behavior and observed tests. Preserve the five CLI commands and existing manifests, or explain migration. See [evaluation guidelines](docs/EVALUATION.md) for performance claims.

## Privacy and isolated tests

Use disposable projects. Do not commit authentication, private configuration, recovery journals, personal paths or raw transcripts. Sanitized doctor output and a minimal fixture are usually enough. Paid calls need authorization and are not required for ordinary unit tests.

For isolated runtime tests use a separate CODEX_HOME and child CLI/App Server. Desktop model overrides have not established isolation. Read [security boundaries](SECURITY.md) and [observed limitations](docs/VALIDATION.md).

## Documentation

Keep [English](README.md) and [Chinese](README.zh-CN.md) behavior aligned. README is the first-use path; detailed setup and current verification belong in docs/GETTING_STARTED.md and docs/VALIDATION.md. Keep historical reports as history.


中文开发检查：保持五个 CLI 命令与旧参数兼容；安全边界变更需回归测试。`python -m compileall -q src tests tools` 做轻量语法检查；运行 `python tools/build_release.py` 和 `python tools/check_wheel.py` 验证离线包。未引入 lint/type-check 依赖；语法检查不等于类型检查。恢复日志、私有配置、真实试验数据不要提交。
