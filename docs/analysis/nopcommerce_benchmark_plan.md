# nopCommerce Benchmark Plan

AEGIS is implemented for nopCommerce, but it is not intended to clone the
nopCommerce Admin reporting UI one screen at a time. The target is an approved
nopCommerce semantic layer: once a metric, dimension, filter, join path, and
result shape are declared, users can ask natural analytical questions over
those concepts in many combinations. Built-in reports are therefore validation
anchors, not the complete system boundary.

For the thesis dataset page, use `docs/analysis/thesis_dataset_page.md`. It
summarises the evaluation corpus: the 500-question natural user dataset and
nopCommerce's own twenty standard admin reports.

## Benchmark 1: Natural User Question Breadth

File: `evaluation_dataset/nopcommerce_500_natural_questions.json`

Purpose: evaluate how the architecture behaves across the range of language a
store owner actually uses — both inside and outside the declared semantic
boundary.

Scope:

- 425 questions answerable by the implemented semantic layer: KPI queries,
  rankings, trends, segmentation, listings, time filters, item-grain
  substitutions, and approved predicates such as low stock.
- 75 realistic e-commerce boundary questions requiring unmodelled concepts:
  web telemetry, marketing attribution, support tickets, review-text sentiment,
  forecasting, churn prediction, supplier performance, product affinity,
  delivery SLA analysis, and fraud scoring.

Runs:

- `verify_nopcommerce_500_dataset.py` — deterministic stages only. Committed
  intent annotations are passed straight to the mapper with no model call. This
  is a regression gate on resolution, compilation, and execution; its figures
  are not end-to-end results.
- `run_nopcommerce_500_live_benchmark.py` — the full pipeline with the live
  parser. This is the end-to-end measurement.

Metrics (live run):

- Parser success.
- Supported intent exact match.
- Supported answer rate.
- Supported execution validity.
- Boundary rejection accuracy.

Current result (live run):

- Parser success: 498/500 (99.6%).
- Supported intent exact match: 345/425 (81.2%).
- Supported answer rate: 422/425 (99.3%).
- Supported execution validity: 422/425 (99.3%).
- Boundary rejection accuracy: 74/75 (98.7%).

Interpretation:

Boundary rejection accuracy is only meaningful alongside the supported answer
rate; a system that declines everything scores 100% on the first. Intent exact
match is the lowest figure and the one worth explaining: a fifth of supported
requests produced an intent differing from the committed annotation while the
answer rate held at 99.3%. Whether those divergent intents produced correct
answers has not been measured, and the gap must not be presented as evidence
that the semantic layer absorbs intent variation until it has been.

## Benchmark 2: Platform Report Fidelity

Files: `evaluation_dataset/nopcommerce_report_semantics.json`,
`evaluation_dataset/nopcommerce_report_oracles.json`

Purpose: compare AEGIS against nopCommerce's own twenty standard admin reports,
where the platform's own service-layer code provides the oracle.

Scope:

- The full standard admin report list, taken from nopCommerce's own admin menu
  rather than selected by this project.
- Report semantics extracted from nopCommerce 5.00.0 source at commit
  `64bdf2ff08c8b39e65717bcf974fb43dc2ef68f2`, each entry carrying a file,
  method, and line-number citation.

Metrics:

- Shape coverage: does an ordinary business phrasing of the report reach an
  ANSWER outcome with SQL emitted (`verify_report_suite.py`)?
- Differential match: does that SQL return the same data as nopCommerce's own
  report logic on the same seeded database (`verify_report_differential.py`)?

Current result:

- Reproduced (ANSWER + SQL emitted): 20/20.
- Result set matches platform report logic: 12/20 (60.0%).

Interpretation:

Shape coverage is a proxy and must be labelled as one. Several of the twenty
passed it while being silently wrong — an order-level revenue sum fanned out
across item-level joins, a missing soft-delete filter, a customer breakdown
grouped by display name — each returning a plausible, chartable number. Those
defects are documented in `docs/analysis/nopcommerce_sql_parity.md`.

The differential is the check that tests the claim, and its recorded 12/20 must
be re-run before it is quoted: the artifact was written before the parity fixes
in `aegis/server/compiler.py` and the intent-validation changes that followed,
and several of the eight recorded mismatches have exactly the shape of defects
that parity work reports as fixed.

## Thesis Framing

The claim should be:

> AEGIS safely answers analytical questions over the metrics, dimensions,
> predicates, joins, time rules, and result shapes declared in the deployment's
> semantic layer. Built-in platform reports validate semantic fidelity where a
> first-party oracle exists, while the 500-question corpus shows that the same
> approved layer supports broader natural user questions without opening the
> system to arbitrary SQL generation.

The claim should not be:

> AEGIS reproduces every possible nopCommerce report, dashboard, grid, or future
> analytical question.

This distinction keeps the implementation general enough for the architecture
while still being honest that a real deployment has a finite semantic boundary.
