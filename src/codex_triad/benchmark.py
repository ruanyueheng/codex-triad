"""Offline, user-supplied experiment summary. Never invent token usage or live costs."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


class BenchmarkError(ValueError):
    pass


COLUMNS = ("task_id", "strategy", "success", "elapsed_seconds", "input_tokens", "output_tokens", "cost_usd")
STRATEGIES = ("baseline", "triad")
METADATA = ("run_id", "codex_version", "model_ids", "task_snapshot", "prompt_version", "evidence_source")


@dataclass(frozen=True)
class Result:
    strategy: str
    sample_count: int
    success_count: int
    median_seconds: float
    total_input_tokens: int | None
    total_output_tokens: int | None
    total_cost_usd: float | None
    total_main_context_tokens: int | None = None
    total_subagent_count: int | None = None
    mean_quality_score: float | None = None
    metadata_complete_count: int = 0

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "sample_count": self.sample_count,
            "success_count": self.success_count,
            "success_rate": round(self.success_count / self.sample_count, 4),
            "median_seconds": round(self.median_seconds, 3),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6) if self.total_cost_usd is not None else None,
            "total_main_context_tokens": self.total_main_context_tokens,
            "total_subagent_count": self.total_subagent_count,
            "mean_quality_score": self.mean_quality_score,
            "metadata_complete_count": self.metadata_complete_count,
        }


def summarize(path: Path) -> list[Result]:
    if not path.is_file():
        raise BenchmarkError(f"Benchmark CSV not found: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or not set(COLUMNS).issubset(reader.fieldnames):
                raise BenchmarkError(f"CSV must contain columns: {', '.join(COLUMNS)}")
            rows = list(reader)
    except (UnicodeError, OSError, csv.Error) as exc:
        raise BenchmarkError(f"Could not load CSV: {exc}") from exc
    if not rows:
        raise BenchmarkError("CSV contains no experiment rows")
    by_strategy: dict[str, list[dict]] = defaultdict(list)
    for line, row in enumerate(rows, start=2):
        if None in row or any(row.get(key) is None for key in COLUMNS):
            raise BenchmarkError(f"line {line}: row length does not match CSV header")
        strategy = (row.get("strategy") or "").strip().lower()
        if strategy not in STRATEGIES:
            raise BenchmarkError(f"line {line}: strategy must be baseline or triad")
        if not (row.get("task_id") or "").strip():
            raise BenchmarkError(f"line {line}: task_id is required")
        success = (row.get("success") or "").strip().lower()
        if success not in ("true", "false"):
            raise BenchmarkError(f"line {line}: success must be true or false")
        parsed = {"success": success == "true"}
        try:
            seconds = float(row["elapsed_seconds"])
            if seconds < 0 or seconds == float("inf") or seconds != seconds:
                raise ValueError()
            parsed["seconds"] = seconds
            for key in ("input_tokens", "output_tokens", "main_context_tokens", "subagent_count"):
                value = (row.get(key) or "").strip()
                if value and value.upper() != "UNKNOWN":
                    if not value.isascii() or not value.isdecimal():
                        raise ValueError(f"invalid {key}")
                    parsed[key] = int(value)
                else:
                    parsed[key] = None
            cost = (row.get("cost_usd") or "").strip()
            if cost and cost.upper() != "UNKNOWN":
                numeric_cost = float(cost)
                if numeric_cost < 0 or numeric_cost == float("inf") or numeric_cost != numeric_cost:
                    raise ValueError("invalid cost")
                parsed["cost_usd"] = numeric_cost
            else:
                parsed["cost_usd"] = None
            quality = (row.get("quality_score") or "").strip()
            parsed["quality_score"] = None if not quality or quality.upper() == "UNKNOWN" else float(quality)
            if parsed["quality_score"] is not None and not 0 <= parsed["quality_score"] <= 1:
                raise ValueError("quality_score must be between 0 and 1")
            parsed["metadata_complete"] = all((row.get(k) or "").strip().upper() not in ("", "UNKNOWN", "MODEL_NOT_VERIFIED") for k in METADATA)
        except (ValueError, TypeError) as exc:
            raise BenchmarkError(f"line {line}: invalid metric ({exc})") from exc
        by_strategy[strategy].append(parsed)

    results = []
    for strategy in STRATEGIES:
        group = by_strategy.get(strategy, [])
        if not group:
            continue
        def total_or_unknown(column: str):
            if any(item[column] is None for item in group):
                return None
            total = sum(item[column] for item in group)
            if isinstance(total, float) and not math.isfinite(total):
                raise BenchmarkError(f"Non-finite aggregate for {column}")
            return total
        durations = sorted(item["seconds"] for item in group)
        middle = len(durations) // 2
        median = durations[middle] if len(durations) % 2 else durations[middle - 1] + (durations[middle] - durations[middle - 1]) / 2
        quality_total = total_or_unknown("quality_score")
        results.append(Result(
            strategy=strategy,
            sample_count=len(group),
            success_count=sum(item["success"] for item in group),
            median_seconds=median,
            total_input_tokens=total_or_unknown("input_tokens"),
            total_output_tokens=total_or_unknown("output_tokens"),
            total_cost_usd=total_or_unknown("cost_usd"),
            total_main_context_tokens=total_or_unknown("main_context_tokens"),
            total_subagent_count=total_or_unknown("subagent_count"),
            mean_quality_score=quality_total / len(group) if quality_total is not None else None,
            metadata_complete_count=sum(item["metadata_complete"] for item in group),
        ))
    return results
