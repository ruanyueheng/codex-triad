# Architecture and delegation contract

## Scope

Triad 0.2.0a2 is a **generator/installer for native Codex custom agents**. It does not run the model server, intercept calls, measure actual tokens, or force event-driven delegation. Instructions in `AGENTS.md` are a *behavioral request*, not a deterministic scheduler.

中文入口：[安全写入 ADR](ADR-001-SAFE-INSTALL.md)、[官方配置与 P2 调查](OFFICIAL_COMPATIBILITY.md)、[运行验收](RUNTIME_VERIFICATION.md)。

## Implementation boundaries / 实现边界

- `cli.py`: five stable commands, exit codes and output. Explicit `--recover` performs recovery only.
- `templates.py`: settings, official agent fields and bounded role instructions.
- `installer.py`: ownership, configuration merge, change planning and uninstall reports.
- `storage.py`: shared path guards, OS lock, snapshot comparison, atomic replacement, local journal and rollback/recovery.
- `checker.py`: static diagnostics using the same ownership/path checks; runtime facts remain UNKNOWN.
- `benchmark.py`: user-supplied offline measurements; missing totals remain unknown, no telemetry collection.

实际文件操作是运行时代码；Agent 路由、角色只读和 Astra 检查点是提示词约定。多文件事务可恢复，不提供同时可见性或抵御本地恶意写入的安全边界。

## Bounded role contracts / 有界角色契约

All inputs: one goal, exact scope/paths, relevant source/log/diff evidence, constraints and expected output. Missing evidence must be reported explicitly. Coordinator owns source edits; workers/advisor are read-only by instruction.

| Role | Required input | Output | Limit |
|---|---|---|---|
| Explorer | Repository question and permitted paths | EVIDENCE, ANSWER, UNRESOLVED; paths/symbols | 300 words |
| Researcher | Dependency/version and narrow behavior question | FINDING, SOURCE, LIMITS, RECOMMENDATION | 300 words |
| Triage | Original error, signature, previous attempts, permitted tests | FAILURE_SIGNATURE, EVIDENCE, HYPOTHESES, NEXT_TEST, UNCERTAINTY | 300 words |
| Architect | Actual diff/design, related source/tests, constraints | VERDICT, BLOCKERS, RISKS, NEXT_ACTIONS, UNCERTAINTIES | 450 words |

Each report separates direct evidence, inference and unknowns. A failed spawn is reported with its original error; a single-agent fallback is disclosed. Neither agent self-report nor these contracts verify actual model identity.

## Roles and data flow

1. The main coordinator uses the user-selected main model (Sol is a legacy preset). It owns state, edits, test execution, and the final response.
2. The user-configured explorer/researcher/triage workers receive bounded questions. They return short evidence and uncertainty. No broad transcript streaming back to the main context.
3. The user-configured advisor reviews at defined checkpoints. It is not a general implementation agent.
4. The user sees the review and actual test results, and decides whether to commit.

## Escalation policy

| Event | Coordinator response | Advisor |
| --- | --- | --- |
| Small, reversible change | Implement, focused test | Skip |
| Important API, migration or security boundary | Gather scoped evidence; assess change before committing design | Call |
| First failing test | Triage signature and isolate reproduction | Skip by default |
| Same signature fails twice after attempted fixes | Stop repeating approach; send evidence, attempts and failure signature | Call |
| Nontrivial pre-commit review | Provide diff, relevant tests, constraints | Call |
| No agent tool or model authorization | Explicitly disclose limitation and use an honest single-agent fallback | Unavailable |

Astra outputs one of `APPROVE`, `APPROVE_WITH_CONDITIONS`, `BLOCK`, `INSUFFICIENT_EVIDENCE`. It provides evidence-backed findings, **not a machine-enforced approval**. If risks are blocking, the coordinator should not conceal them.

## Isolation and concurrency

- Concurrency limit defaults to **three spawned agents**, excluding the root thread (subject to Codex backend behavior).
- Read-heavy tasks parallelize well. Concurrent changes to the same files do not; do not delegate overlapping writes.
- Instructions forbid editing for reviewer roles, **but subagents inherit the parent sandbox**. Use a read-only parent permission mode when hard read-only behavior is needed.
- Scoping and summaries avoid flooding main context. This does not guarantee net lower tokens.

## Configuration precedence

Project `.codex/config.toml` can be bypassed when the project isn't trusted. CLI/model-picker overrides and running session state can supersede the intended values. Different installed clients or workspaces may have different model access. The project's `doctor` checks syntax and intent, while runtime smoke prompts check *actual spawning*. See [Codex docs](https://developers.openai.com/codex/subagents).

## Road to deterministic scheduling

True enforced gatekeeping needs a supervising process with observable events (test outcomes, diff creation, commit request), reliable agent invocation and refusal/abort semantics. That is deliberately **out of scope** for this release. If added, it must not silently block user work or intercept Git changes without opt-in and careful tests.

## Native runtime evidence

The opt-in collector uses the installed CLI App Server protocol. Offline evidence.py joins roles, parent/child threads and activity within one successful turn, requires worker overlap and advisor order, and keeps backend identity UNKNOWN. See [native verification](CLI_NATIVE_VERIFICATION.md).
