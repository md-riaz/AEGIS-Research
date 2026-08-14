# AEGIS — working notes

## Evaluation policy

**Fix the implementation before freezing a number.** A metric taken while a
known defect or a known coverage gap is outstanding measures the gap, not the
architecture. Publishing it as a finding misattributes an implementation
weakness to the design.

This has bitten repeatedly on this project. Each of these numbers was an
artifact, not a result:

| Number | What it actually measured |
|---|---|
| 0.0% abstention recall (first full run) | `str(Outcome.ANSWER)` serialised as `"Outcome.ANSWER"` |
| 61.8% false abstention | the model's `unmapped_terms` merged without validation |
| 40.0% false abstention | a semantic layer exposing 12 of 126 available tables |
| 23.6% false abstention | current — still has known gaps, so still provisional |

So the working rule is: **when a metric is poor, first ask whether the
implementation or the vocabulary explains it.** Only report it as a property of
the architecture once neither does.

### What this rule is not

It is not licence to withhold an unfavourable measurement, or to report only
the flattering half of a pair. Two things follow from that:

- `abstention_recall` is never reported without `false_abstention_rate`.
  Refusing every request scores 100% on the first alone, and the whole
  contribution collapses if that pairing is broken.
- A limitation that survives a genuine fix attempt gets stated plainly. The
  manuscript's existing 100% claims are precisely what this project is
  correcting; replacing them with a differently-selected set of favourable
  numbers would repeat the error rather than fix it.

Suppressing a real result is also self-defeating in practice: an examiner who
finds the withheld number has found both the weakness *and* the concealment.

### Metrics currently unusable

`translation_precision` and `silent_error_rate` are scored against
`aegis_correct` in `semantic_correctness_annotations.json`, and those labels
describe the **old** pipeline's SQL. `translation_precision` has read 29.9%
across every run because it is the same label count being re-read. Neither may
be quoted until the dataset is re-annotated.

`verify_report_suite.py`'s 20/20 measures coverage of the report shape, not
semantic correctness of the SQL; semantic correctness against the platform is
evidenced separately by `docs/analysis/nopcommerce_sql_parity.md` and pinned by
`tests/test_platform_parity.py`. A differential test of result sets against a
shared database has NOT been run and is the outstanding gap.

### A pass/fail check must test the claim, not a proxy for it

The report-suite verification counted "the compiler emitted SQL" as success.
Five queries passed that check while being silently wrong — an order-level
revenue sum fanned out across item-level joins, missing soft-delete filters, a
customer breakdown grouped by display name, a customer count anchored on the
order date, and an unbindable filter that compiled to `o.Id = '<the unbound
value>'`. Each returned a plausible, chartable number, so nothing downstream
could distinguish them from correct answers. The generalisation for this
project: when a metric can be satisfied by a proxy for the claim, it
eventually will be, and the proxy is what gets reported.

## Measurement setup

`.env` (gitignored) holds live LLM credentials, so the full benchmark runs
locally in ~8 minutes:

```bash
python3 run_benchmark.py --rerun --limit 0
python3 evaluation_dataset/evaluate_abstention.py
```

Do not wait for CI to measure — CI is a gate, not the instrument.

## Architecture invariants

- The LLM extracts intent only. It never produces SQL.
- Coverage analysis runs against the **user's question**, never the model's
  output: vocabulary injection makes the output in-vocabulary by construction,
  so validating it cannot detect an out-of-scope request.
- No silent fallbacks. An absent value must never be replaced by a plausible
  one — that class of defect is the subject of the thesis.
