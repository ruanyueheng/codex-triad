# Contributing

Thanks for improving Codex Triad. Before opening a PR:

1. Open an issue for breaking model-routing, config-format, or installation behavior changes.
2. Keep the CLI Python-standard-library-only unless a compelling need is documented.
3. Add unit tests for parsing, idempotency, collision safety, uninstall behavior, and Windows support.
4. Do not add screenshots or benchmark numbers without provenance, client/build, task details and protocol.
5. Never commit private `.codex/config.toml` files containing provider endpoints/tokens; sanitize all logs.
6. Explain whether behavior is a deterministic capability, an AGENTS.md instruction, or a user-observed result.

Run `python -m unittest discover -s tests -v` before your PR. See [evaluation guidelines](docs/EVALUATION.md) for performance claims.


中文开发检查：保持五个 CLI 命令与旧参数兼容；安全边界变更需回归测试。`python -m compileall -q src tests tools` 做轻量语法检查；运行 `python tools/build_release.py` 和 `python tools/check_wheel.py` 验证离线包。未引入 lint/type-check 依赖；语法检查不等于类型检查。恢复日志、私有配置、真实试验数据不要提交。
