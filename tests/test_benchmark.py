import csv
import tempfile
import unittest
from pathlib import Path
from codex_triad.benchmark import BenchmarkError, summarize


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.csv = Path(self.temp.name) / "runs.csv"

    def test_aggregate_and_unknown(self):
        self.csv.write_text("task_id,strategy,success,elapsed_seconds,input_tokens,output_tokens,cost_usd\n"
                            "A,baseline,true,10,100,50,0.25\n"
                            "B,baseline,false,20,120,40,0.30\n"
                            "A,triad,true,11,130,45,\n", encoding="utf-8")
        baseline, triad = summarize(self.csv)
        self.assertEqual(baseline.sample_count, 2)
        self.assertEqual(baseline.median_seconds, 15)
        self.assertEqual(baseline.total_input_tokens, 220)
        self.assertAlmostEqual(baseline.total_cost_usd, 0.55)
        self.assertIsNone(triad.total_cost_usd)

    def test_rejects_invalid(self):
        self.csv.write_text("task_id,strategy,success,elapsed_seconds,input_tokens,output_tokens,cost_usd\n"
                            "x,triad,true,-1,0,0,0\n", encoding="utf-8")
        with self.assertRaises(BenchmarkError):
            summarize(self.csv)

    def test_missing_csv(self):
        with self.assertRaises(BenchmarkError):
            summarize(self.csv)

    def test_extended_metrics_and_metadata(self):
        self.csv.write_text("task_id,strategy,success,elapsed_seconds,input_tokens,output_tokens,cost_usd,main_context_tokens,subagent_count,quality_score,run_id,codex_version,model_ids,task_snapshot,prompt_version,evidence_source\n"
                            "x,triad,true,1,10,20,UNKNOWN,30,2,0.8,r1,v1,verified,sha1,p1,local-export\n")
        result = summarize(self.csv)[0]
        self.assertEqual(result.total_main_context_tokens, 30)
        self.assertEqual(result.total_subagent_count, 2)
        self.assertEqual(result.mean_quality_score, 0.8)
        self.assertEqual(result.metadata_complete_count, 1)
        self.assertIsNone(result.total_cost_usd)

    def test_rejects_bad_shape_unicode_digits_and_nonfinite_values(self):
        header = "task_id,strategy,success,elapsed_seconds,input_tokens,output_tokens,cost_usd\n"
        for row in ("x,triad,true,1,²,0,0", "x,triad,true,1", "x,triad,true,1,0,0,0,extra",
                    "x,triad,true,nan,0,0,0", "x,triad,true,1,0,0,inf"):
            with self.subTest(row=row):
                self.csv.write_text(header + row, encoding="utf-8")
                with self.assertRaises(BenchmarkError):
                    summarize(self.csv)

    def test_rejects_duplicate_columns(self):
        self.csv.write_text("task_id,strategy,success,elapsed_seconds,input_tokens,output_tokens,cost_usd,task_id\n"
                            "x,triad,true,1,0,0,0,x\n")
        with self.assertRaises(BenchmarkError):
            summarize(self.csv)

    def test_large_finite_durations_and_overflowing_totals(self):
        header = "task_id,strategy,success,elapsed_seconds,input_tokens,output_tokens,cost_usd\n"
        self.csv.write_text(header + "a,triad,true,1e308,0,0,\nb,triad,true,1e308,0,0,\n")
        self.assertEqual(summarize(self.csv)[0].median_seconds, 1e308)
        self.csv.write_text(header + "a,triad,true,1,0,0,1e308\nb,triad,true,1,0,0,1e308\n")
        with self.assertRaises(BenchmarkError):
            summarize(self.csv)

    def paired_rows(self):
        common = dict(task_id="task-a", elapsed_seconds="10", input_tokens="100", output_tokens="20",
                      cost_usd="UNKNOWN", codex_version="0.163.0", task_snapshot="frozen-sha",
                      prompt_version="task-v1", evidence_source="private-log", pair_id="1",
                      acceptance_command="python -m unittest", failure_reason="")
        return [{**common, "strategy": "baseline", "success": "false", "run_id": "b1",
                 "model_ids": "main", "failure_reason": "acceptance failed"},
                {**common, "strategy": "triad", "success": "true", "run_id": "t1", "model_ids": "main,worker,advisor"}]

    def write_rows(self, rows):
        with self.csv.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)

    def test_paired_report_keeps_failures_unknown_costs_and_repetitions(self):
        rows = self.paired_rows()
        rows += [{**r, "pair_id": "2", "run_id": r["run_id"] + "-repeat"} for r in rows]
        self.write_rows(rows)
        baseline, triad = summarize(self.csv, paired=True)
        self.assertEqual((baseline.sample_count, triad.sample_count), (2, 2))
        self.assertEqual((baseline.success_count, triad.success_count), (0, 2))
        self.assertIsNone(triad.total_cost_usd)

    def test_paired_report_rejects_mismatched_conditions(self):
        for field in ("codex_version", "task_snapshot", "prompt_version", "acceptance_command"):
            with self.subTest(field=field):
                rows = self.paired_rows()
                rows[1][field] = "different"
                self.write_rows(rows)
                with self.assertRaisesRegex(BenchmarkError, field):
                    summarize(self.csv, paired=True)

    def test_paired_report_rejects_missing_duplicate_or_unexplained_runs(self):
        for case in ("unmatched", "duplicate", "run_id", "missing_metadata", "missing_failure", "different_task"):
            with self.subTest(case=case):
                rows = self.paired_rows()
                if case == "unmatched": rows.pop()
                if case == "duplicate": rows.append({**rows[1], "run_id": "t2"})
                if case == "run_id": rows[1]["run_id"] = rows[0]["run_id"]
                if case == "missing_metadata": rows[1]["model_ids"] = "UNKNOWN"
                if case == "missing_failure": rows[0]["failure_reason"] = ""
                if case == "different_task": rows[1]["task_id"] = "task-b"
                self.write_rows(rows)
                with self.assertRaises(BenchmarkError):
                    summarize(self.csv, paired=True)

if __name__ == '__main__':
    unittest.main()
