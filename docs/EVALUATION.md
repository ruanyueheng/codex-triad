# Evaluation protocol / 评测规范

**Status: methodology only; no experimental results are claimed.** Triad cannot capture the token consumption, speed, or effective model of Codex sessions automatically. All rows must come from an actual measured run, and a blank field means unknown (not zero).

## Practical design

1. Select at least 10 representative, independently verifiable coding tasks. Freeze the repo SHA, test commands, task descriptions, and Codex version. Use both easy and hard tasks.
2. For each task, run **baseline (Sol alone)** and **triad (Sol + Luna workers + optional Astra)** from identical clean worktrees. Alternate trial order to reduce time-of-day effects, repeat runs if affordable, and isolate caches as much as possible.
3. Record start/end wall time and test results; only record token counts or costs if observed via an actual authoritative usage/billing surface. Report cache and rate-limit conditions; do not estimate Codex subscription billing as API spend.
4. Keep the evaluator blind to strategy where feasible. Grade correctness using tests and manual assessment of reproducibility, regressions and security. Track advisor trigger rate, spawned agent success, number of retries, model confirmation, and unexpected file modifications separately in raw notes.
5. Compare task-matched pass rate, median latency, input/output token totals, observed expense (if available) and regression count. Report uncertainty; different models and concurrent runs can change variance. An improvement on one toy repository is not evidence of general savings.

## Local CSV analysis

Copy `evaluation/runs.template.csv` to an untracked or private CSV, fill observed rows, then run:

```bash
codex-triad report --csv path/to/my-runs.csv
codex-triad report --csv path/to/my-runs.csv --json
```

Columns:

| Column | Format | Definition |
| --- | --- | --- |
| `task_id` | nonempty string | Same ID across baseline and triad for paired comparison |
| `strategy` | `baseline` or `triad` | Which configuration actually ran |
| `success` | `true` / `false` | Meets frozen acceptance criteria |
| `elapsed_seconds` | nonnegative float | End-to-end wall time measured externally |
| `input_tokens` | integer or blank | Actual observed input usage; blank means unknown |
| `output_tokens` | integer or blank | Actual observed output usage; blank means unknown |
| `cost_usd` | nonnegative float or blank | Observed monetary charge, **not** assumed token pricing |

`report` summarizes each strategy separately. If any metric value is missing within a strategy, its total is reported as **unknown**, not a false partial total. It does **not** claim causal improvement or enforce pairing; researchers must inspect the underlying raw task-matched records.

## 0.2 扩展 / Optional extensions

旧的七列 CSV 仍有效。指标空白或 `UNKNOWN` 都记未知；JSON 使用 null，文本使用 UNKNOWN。`elapsed_seconds` 是必填的实际测量值，必须非负且有限。额外列如下：

| Column | Format | Meaning |
|---|---|---|
| main_context_tokens | nonnegative integer / blank / UNKNOWN | 仅有可信来源时填写主线程上下文占用，不能用输入 token 总和替代 |
| subagent_count | nonnegative integer / blank / UNKNOWN | 实际观察到的子线程数量 |
| quality_score | 0..1 / blank / UNKNOWN | 使用实验前冻结的独立评分规则 |
| run_id, codex_version, model_ids | string / UNKNOWN | 每次实验标识、客户端版本、可信来源的实际模型 ID |
| task_snapshot, prompt_version, evidence_source | string / UNKNOWN | 仓库/任务快照、提示词版本、私有证据位置 |
| failure_reason | string | 原始失败原因的脱敏摘要；保留失败实验 |

输出附加 context/subagent 总量、平均质量及 `metadata_complete_count`。元数据完整只表示字段已填，不代表来源真实、模型已核验或样本已匹配。工具不对评分做语义判断。每项汇总如有缺失就保持未知。

`evaluation/tasks.json` 提供入口追踪、版本兼容、重复故障、跨模块修复、提交前审查五类任务；仅为协议，不包含虚构运行结果。每类任务用相同快照、相同验收跑 baseline/triad，建议至少 10 个具体样本并重复；记录样本量与配对关系。`runtime-evidence.template.json` 单独记录每次角色/模型/线程核验。

English: legacy CSV remains valid. Optional metrics and provenance fields support broader experiments, but no automatic collection, pairing enforcement, semantic quality grading or source verification is performed. Missing data stays unknown. Templates and task definitions are protocol-only, not experimental evidence.

## Suggested claims policy

- Say **"configured"** when the TOML references a model, **"spawn observed"** when a thread actually started, and **"model confirmed"** only when trusted runtime instrumentation exposes the effective ID.
- Report sample size and task mix alongside every statistic.
- Never claim "save X% tokens" without complete observed measurements and a comparable baseline.
- Preserve failed experiments in the dataset to avoid cherry-picking.
