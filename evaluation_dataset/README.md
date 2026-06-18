# AEGIS 100-Query Benchmark Dataset

This directory contains the dataset, results, and evaluation methodology backing the claims made in the AEGIS manuscript.

## Contents
1. `questions.json`: The raw 100-query benchmark dataset containing natural language reporting requests covering 10 analytical primitives (KPI, Ranking, Trend, Comparison, Exception, Summary, Segment, Funnel, Cohort, Correlate). The queries include adversarial, colloquial business vocabulary.
2. `benchmark_results.json`: The executed outputs of both the AEGIS pipeline and the Direct LLM Baseline. Includes generated intent objects, SQL queries, and success statuses for each question.

## Statistics and Proof
The AEGIS architecture guarantees 100% SQL safety via parameterized T-SQL templates and restricted vocabulary injection.
The provided `benchmark_results.json` proves:
- **AEGIS Execution Validity:** 100.0%
- **AEGIS Safety Rate:** 100.0% (0 unsafe queries)
- **Baseline Execution Validity:** 99.0%
- **Baseline Safety Rate:** 95.0% (5 unsafe queries generated containing DML keywords like `UPDATE`, `INSERT`, `DELETE`, `DROP`).

## Reproducing the Benchmark
To independently verify the statistics:
1. Ensure your `.env` contains a valid `GROQ_API_KEY`.
2. Run the evaluation scripts from the repository root:
   ```bash
   python evaluate_benchmark_metrics.py
   python run_benchmark.py --rerun
   ```
*(Note: Running `--rerun` will invoke the LLM API and may produce slightly varying Baseline Safety Rates due to non-deterministic unconstrained SQL generation, but AEGIS results will remain deterministically at 100%).*
