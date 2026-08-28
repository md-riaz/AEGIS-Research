# AEGIS — working notes

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
  replacing them with a differently-selected set of favourable numbers would
  repeat the error rather than fix it.

Suppressing a real result is also self-defeating in practice: an examiner who
finds the withheld number has found both the weakness *and* the concealment.

### The two evidence tracks

Everything quotable comes from one of two places, and they answer different
questions:

- **500 natural-language questions** — breadth. Two runs exist over the same
  corpus: `verify_nopcommerce_500_dataset.py` feeds committed intent
  annotations straight into the mapper with **no LLM call**, and
  `run_nopcommerce_500_live_benchmark.py` runs the full pipeline with the live
  parser. Only the second is an end-to-end result. The first is a regression
  gate on the mapper and compiler, and its figures must never be presented as
  though the model were in the loop.
- **nopCommerce's own 20 standard admin reports** — fidelity.
  `verify_report_suite.py` checks that a report request compiles to SQL;
  `verify_report_differential.py` checks that the SQL returns the same data as
  nopCommerce's own report logic on the same database. The differential is the
  one that tests the claim.

`report_differential_results.json` was written before the parity fixes in
`aegis/server/compiler.py` and the intent-validation changes that followed, so
its 12/20 must be re-run before it is quoted.

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

`.env` (gitignored) holds live LLM credentials and the MySQL connection, so the
evaluation runs locally:

```bash
# breadth — end-to-end, live parser
python3 evaluation_dataset/run_nopcommerce_500_live_benchmark.py

# fidelity — compile, then compare result sets against nopCommerce's own reports
python3 evaluation_dataset/verify_report_suite.py
python3 evaluation_dataset/verify_report_differential.py
```

`verify_report_differential.py` reads `report_suite_results.json`, so run the
suite first whenever the compiler has changed.

Do not wait for CI to measure — CI is a gate, not the instrument.

## Architecture invariants

- The LLM extracts intent only. It never produces SQL.
- The LLM extracts structured intent from vague user language. AEGIS validates
  that structured intent against the semantic layer; the original request text
  is retained only for narrow non-executable safety/scope cues such as writes,
  direct credential/secret requests, and explicit prediction/causal-analysis
  requests outside the SQL-only prototype scope.
- No silent fallbacks. An absent value must never be replaced by a plausible
  one — that class of defect is the subject of the thesis.
