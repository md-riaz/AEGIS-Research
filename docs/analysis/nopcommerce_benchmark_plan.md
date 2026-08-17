# nopCommerce Benchmark Plan

AEGIS is implemented for nopCommerce, but it is not intended to clone the
nopCommerce Admin reporting UI one screen at a time. The target is a governed
nopCommerce semantic layer: once a metric, dimension, filter, join path, and
result shape are declared, users can ask natural analytical questions over
those concepts in many combinations. Built-in reports are therefore validation
anchors, not the complete system boundary.

For the thesis dataset page, use
`docs/analysis/thesis_dataset_page.md`. It summarizes the complete evaluation
corpus: the 500-question natural user dataset, 80 Admin fidelity phrasings, the
107-question general benchmark, the 16-task Admin fidelity benchmark, and the
25-task semantic coverage benchmark.

## Benchmark 1: Admin Analytics Fidelity

File: `evaluation_dataset/nopcommerce_admin_analytics_oracles.json`

Purpose: compare AEGIS against first-party nopCommerce Admin analytics surfaces
where the source system provides a clear oracle.

Scope:

- Tier A formal admin report pages.
- Tier B dashboard widgets.

Metrics:

- Execution validity.
- Shape accuracy.
- Result accuracy.
- Failure cause.

Current result:

- Execution validity: 16/16 (100.0%).
- Shape accuracy: 16/16 (100.0%).
- Result accuracy: 15/16 (93.8%).

Interpretation:

The remaining failure is an expressiveness limit of the current implementation,
not unsafe SQL generation. The dashboard order average matrix requires a
general multi-period matrix-summary primitive that AEGIS does not yet
implement.

## Benchmark 2: Semantic Coverage

File: `evaluation_dataset/nopcommerce_semantic_coverage_questions.json`

Purpose: evaluate broader user-facing analytical coverage over the declared
nopCommerce semantic layer, beyond fixed built-in reports.

Scope:

- KPI queries.
- Rankings.
- Trends.
- Segmentation.
- Listings.
- Time filters.
- Item-grain substitutions.
- Boundary rejections for unmodelled concepts.

Metrics:

- Supported execution validity.
- Supported shape accuracy.
- Supported result accuracy.
- Boundary rejection accuracy.

Current result:

- Supported execution validity: 20/20 (100.0%).
- Supported shape accuracy: 20/20 (100.0%).
- Supported result accuracy: 20/20 (100.0%).
- Boundary rejection accuracy: 5/5 (100.0%).

Interpretation:

This benchmark demonstrates the thesis value more directly than built-in report
matching alone: a nopCommerce-aware AEGIS deployment can compose many valid
analytical views from the governed semantic layer, while still refusing
questions about concepts outside that layer such as web telemetry, employees,
support tickets, marketing attribution, free-text review sentiment, and
forecasting.

## Thesis Framing

The claim should be:

> AEGIS safely answers analytical questions over the metrics, dimensions,
> predicates, joins, time rules, and result shapes declared in the deployment's
> semantic layer. Built-in platform reports validate semantic fidelity where a
> first-party oracle exists, while semantic-coverage evaluation shows that the
> same governed layer supports broader natural user questions without opening
> the system to arbitrary SQL generation.

The claim should not be:

> AEGIS reproduces every possible nopCommerce report, dashboard, grid, or future
> analytical question.

This distinction keeps the implementation general enough for the architecture
while still being honest that a real deployment has a finite semantic boundary.
