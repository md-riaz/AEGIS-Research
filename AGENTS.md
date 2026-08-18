# AEGIS - working notes

## Document tracks - do not mix

Maintain two independent writing artifacts:

- `docs/AEGIS_Manuscript.md` is the research-paper manuscript track. Compare
  and edit it against journal-style papers in `references/`. The locked target
  is **Journal of Intelligent Information Systems (Springer)** as a regular
  article, using the no-APC subscription route rather than open access. Keep
  the paper framed as an intelligent information systems architecture with
  implementation and evaluation evidence.
- `docs/scripts/thesis_book_generator/` is the Pundra University thesis-book
  source. The submitted DOCX/PDF files are generated from these Python chapter
  scripts, not from `docs/AEGIS_Manuscript.md`.

When the user asks to update the thesis DOCX/book/submission, edit the thesis
book generator files and rebuild/export the DOCX/PDF. When the user asks to
update the manuscript for paper submission, edit `docs/AEGIS_Manuscript.md`.
Do not assume a change in one track updates the other.

For manuscript formatting, follow Springer regular-article expectations:
abstract around 150-250 words, 5-7 keywords, numbered sections, concise inline
figures/tables, and a journal-style reference list. Do not reframe the
manuscript as a conference paper unless the user explicitly changes the target.

## Evaluation policy

**Fix the implementation before freezing a number.** A metric taken while a
known defect or a known coverage gap is outstanding measures the gap, not the
architecture. Publishing it as a finding misattributes an implementation
weakness to the design.

This has bitten repeatedly on this project. Each of these numbers was an
artifact or superseded intermediate state, not the final thesis result:

| Number | What it actually measured |
|---|---|
| 0.0% abstention recall (first full run) | `str(Outcome.ANSWER)` serialized as `"Outcome.ANSWER"` |
| 61.8% false abstention | the model's `unmapped_terms` merged without validation |
| 40.0% false abstention | a semantic layer exposing 12 of 126 available tables |
| 25.5% false abstention | older 107-query benchmark state, now superseded by static nopCommerce datasets |

So the working rule is: **when a metric is poor, first ask whether the
implementation or the vocabulary explains it.** Only report it as a property of
the architecture once neither does.

### What this rule is not

It is not licence to withhold an unfavourable measurement, or to report only
the flattering half of a pair. Two things follow from that:

- `abstention_recall` is never reported without `false_abstention_rate` when
  using the legacy abstention benchmark. Refusing every request scores 100% on
  the first alone, and the whole contribution collapses if that pairing is
  broken.
- A limitation that survives a genuine fix attempt gets stated plainly. The
  manuscript's earlier 100% claims are precisely what this project corrected;
  replacing them with a differently selected set of favourable numbers would
  repeat the error rather than fix it.

Suppressing a real result is also self-defeating in practice: an examiner who
finds the withheld number has found both the weakness and the concealment.

### Metrics currently unusable

`translation_precision` and `silent_error_rate` are scored against
`aegis_correct` in `semantic_correctness_annotations.json`, and those labels
describe the old pipeline's SQL. `translation_precision` has read 29.9% across
every run because it is the same label count being re-read. Neither may be
quoted until the dataset is re-annotated.

`verify_report_suite.py`'s 20/20 measures coverage of the report shape, not
semantic correctness of the SQL. Current thesis evidence should use the static
nopCommerce datasets instead:

- `evaluation_dataset/nopcommerce_500_natural_questions.json`
- `evaluation_dataset/nopcommerce_500_live_benchmark_results.json`
- `evaluation_dataset/nopcommerce_admin_analytics_oracles.json`
- `evaluation_dataset/admin_analytics_benchmark_results.json`
- `evaluation_dataset/nopcommerce_semantic_coverage_questions.json`
- `evaluation_dataset/semantic_coverage_benchmark_results.json`

Current Admin fidelity result is 16/16 execution validity, 16/16 shape accuracy,
and 15/16 result accuracy. The remaining mismatch is an implementation gap
requiring a general multi-period matrix-summary primitive, not a report-specific
preset.

### A pass/fail check must test the claim, not a proxy for it

The old report-suite verification counted "the compiler emitted SQL" as
success. Five queries passed that check while being silently wrong: an
order-level revenue sum fanned out across item-level joins, missing soft-delete
filters, a customer breakdown grouped by display name, a customer count anchored
on the order date, and an unbindable filter that compiled to `o.Id = '<the
unbound value>'`. Each returned a plausible, chartable number, so nothing
downstream could distinguish them from correct answers. The generalization for
this project: when a metric can be satisfied by a proxy for the claim, it
eventually will be, and the proxy is what gets reported.

## Measurement setup

`.env` (gitignored) holds live LLM credentials. The current thesis benchmark
checks are:

```bash
python evaluation_dataset/verify_nopcommerce_500_dataset.py
python evaluation_dataset/run_nopcommerce_500_live_benchmark.py
python evaluation_dataset/verify_admin_analytics_benchmark.py
python evaluation_dataset/verify_semantic_coverage_benchmark.py
```

Do not wait for CI to measure - CI is a gate, not the instrument. Live LLM jobs
were removed from CI because the shared API budget caused unrelated 429
failures.

## Architecture invariants

- The LLM extracts intent only. It never produces SQL.
- Coverage analysis runs against the user's question, never the model's output:
  vocabulary injection makes the output in-vocabulary by construction, so
  validating it cannot detect an out-of-scope request.
- No silent fallbacks. An absent value must never be replaced by a plausible
  one. That class of defect is the subject of the thesis.
- Semantic-layer extensions are allowed per deployment. Report-specific presets
  or hardcoded nopCommerce report shortcuts are not.
- DB dialect limits are prototype/evaluation-scope limits, not architecture
  flaws. The evaluated prototype targets nopCommerce on MySQL.
- Multi-turn conversation is not a thesis limitation; this thesis evaluates
  single-request natural-language analytics.
