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

So the working rule is: **when a metric is poor, first ask whether the
implementation or the vocabulary explains it.** Only report it as a property of
the architecture once neither does.

### What this rule is not

It is not licence to withhold an unfavourable measurement, or to report only
the flattering half of a pair. Two things follow from that:

- A rejection metric is never reported without the answer metric that bounds
  it. Declining every request scores 100% on boundary rejection alone, and the
  whole contribution collapses if that pairing is broken.
- A limitation that survives a genuine fix attempt gets stated plainly.
  Unqualified 100% claims are precisely what this project is correcting;
  replacing them with a differently selected set of favourable numbers would
  repeat the error rather than fix it.

Suppressing a real result is also self-defeating in practice: an examiner who
finds the withheld number has found both the weakness and the concealment.

### The two evidence tracks

Everything quotable comes from one of two places, and they answer different
questions:

- **500 natural-language questions** - breadth.
  `evaluation_dataset/nopcommerce_500_natural_questions.json`. Two runs exist
  over the same corpus: `verify_nopcommerce_500_dataset.py` feeds committed
  intent annotations straight into the mapper with **no LLM call**, and
  `run_nopcommerce_500_live_benchmark.py` runs the full pipeline with the live
  parser. Only the second is an end-to-end result. The first is a regression
  gate on the mapper and compiler, and its figures must never be presented as
  though the model were in the loop.
- **nopCommerce's own 20 standard admin reports** - fidelity.
  `evaluation_dataset/nopcommerce_report_semantics.json` and
  `nopcommerce_report_oracles.json`. `verify_report_suite.py` checks that a
  report request compiles to SQL; `verify_report_differential.py` checks that
  the SQL returns the same data as nopCommerce's own report logic on the same
  database. The differential is the one that tests the claim.

`report_differential_results.json` was written before the parity fixes in
`aegis/server/compiler.py` and the intent-validation changes that followed, so
its 12/20 must be re-run before it is quoted.

### A pass/fail check must test the claim, not a proxy for it

The report-suite verification counted "the compiler emitted SQL" as success.
Five queries passed that check while being silently wrong: an order-level
revenue sum fanned out across item-level joins, missing soft-delete filters, a
customer breakdown grouped by display name, a customer count anchored on the
order date, and an unbindable filter that compiled to `o.Id = '<the unbound
value>'`. Each returned a plausible, chartable number, so nothing downstream
could distinguish them from correct answers. The generalization for this
project: when a metric can be satisfied by a proxy for the claim, it eventually
will be, and the proxy is what gets reported.

## Measurement setup

`.env` (gitignored) holds live LLM credentials and the MySQL connection. The
evaluation checks are:

```bash
# breadth
python evaluation_dataset/verify_nopcommerce_500_dataset.py
python evaluation_dataset/run_nopcommerce_500_live_benchmark.py

# fidelity
python evaluation_dataset/verify_report_suite.py
python evaluation_dataset/verify_report_differential.py
```

`verify_report_differential.py` reads `report_suite_results.json`, so run the
suite first whenever the compiler has changed.

Do not wait for CI to measure - CI is a gate, not the instrument. Live LLM jobs
were removed from CI because the shared API budget caused unrelated 429
failures.

## Architecture invariants

- The LLM extracts intent only. It never produces SQL.
- The LLM extracts structured intent from vague user language. AEGIS validates
  that structured intent against the semantic layer; the original request text
  is retained only for narrow non-executable safety/scope cues such as writes,
  direct credential/secret requests, and explicit prediction/causal-analysis
  requests outside the SQL-only prototype scope.
- No silent fallbacks. An absent value must never be replaced by a plausible
  one. That class of defect is the subject of the thesis.
- Semantic-layer extensions are allowed per deployment. Report-specific presets
  or hardcoded nopCommerce report shortcuts are not.
- DB dialect limits are prototype/evaluation-scope limits, not architecture
  flaws. The evaluated prototype targets nopCommerce on MySQL.
- Multi-turn conversation is not a thesis limitation; this thesis evaluates
  single-request natural-language analytics.
