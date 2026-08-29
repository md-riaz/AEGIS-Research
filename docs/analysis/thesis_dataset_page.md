# Dataset and Evaluation Corpus

This thesis uses a domain-specific evaluation corpus for the nopCommerce
deployment of AEGIS. The corpus is not a single public benchmark such as Spider
or BIRD; it is a project-specific e-commerce reporting dataset designed to
evaluate the properties claimed by AEGIS: safe report generation, semantic-layer
coverage, platform fidelity, and explicit refusal outside the declared semantic
boundary.

## Dataset Summary

| Dataset component | File | Size | Purpose |
|---|---:|---:|---|
| Natural user question dataset | `evaluation_dataset/nopcommerce_500_natural_questions.json` | 500 questions | Breadth: 425 answerable questions over the implemented semantic layer and 75 realistic e-commerce boundary questions. |
| nopCommerce standard admin reports | `evaluation_dataset/nopcommerce_report_semantics.json`, `nopcommerce_report_oracles.json` | 20 reports | Fidelity: the platform's own report list, with its own implementing logic as the oracle. |

Across the two components the thesis provides **520 question-level evaluation
items**: 500 natural user questions and 20 source-derived platform report
tasks.

The two components are deliberately different in kind. The 500 questions are
written for this project, so they measure how the architecture behaves across
the range of language a store owner uses. The 20 reports are not written for
this project at all — the list is nopCommerce's own admin menu and the
comparison target is nopCommerce's own service-layer code — so they measure
fidelity in a way this project could not have shaped to favour itself.

## Database Substrate

All executable benchmarks target the nopCommerce schema loaded into MySQL. The
schema is the same application domain throughout the evaluation, so differences
between benchmark components come from the question/task design rather than
from changing databases.

Current seeded database snapshot used for local verification:

| Table | Rows |
|---|---:|
| `Customer` | 1,200 |
| `Order` | 2,500 |
| `OrderItem` | 6,320 |
| `Product` | 17 |
| `Category` | 8 |
| `Manufacturer` | 8 |
| `Shipment` | 1,492 |
| `Store` | 1 |

The database is refreshed with `database/3_refresh_dates.sql` before running
date-sensitive benchmarks so relative phrases such as "today", "this week",
and "this month" remain meaningful independent of the calendar date on which
the evaluation is rerun.

## 500-Question Natural User Dataset

File: `evaluation_dataset/nopcommerce_500_natural_questions.json`

This is the main dataset page evidence for breadth. It contains 500 natural
e-commerce questions written for the nopCommerce semantic-layer implementation.
The composition is deliberately not 100% answerable:

| Subset | Count | Share |
|---|---:|---:|
| Supported by the implemented semantic layer | 425 | 85.0% |
| Realistic e-commerce boundary questions | 75 | 15.0% |

The supported 425 questions cover KPI, ranking, trend, segmentation, listing,
time-filtered questions, item-grain substitutions, product/category/customer/
country/store/order-status/payment-status/shipping-status/payment-method/
shipping-method dimensions, and approved predicates such as low stock.

The 75 boundary questions remain nopCommerce/e-commerce related but require
concepts or analytical templates not currently implemented: web telemetry,
marketing attribution, customer-support tickets, review-text sentiment,
forecasting, churn prediction, supplier performance, product affinity,
delivery SLA analysis, fraud scoring, and similar realistic store-owner asks.

This composition matches the thesis claim: AEGIS has a finite semantic
boundary. It should answer questions inside the deployment's approved
vocabulary and decline plausible e-commerce questions outside it, rather than
pretending every question is expressible.

### Two runs over the same corpus

The corpus is executed two ways, and they answer different questions. Reporting
either one as though it were the other is the single easiest way to overstate
this evaluation.

**Deterministic stages only** (`verify_nopcommerce_500_dataset.py` →
`nopcommerce_500_dataset_results.json`). Each question's committed intent
annotation is passed straight to the semantic mapper — no model is called. This
isolates resolution, compilation, and execution as a regression gate.

| Metric | Result |
|---|---:|
| Supported resolution validity | 425/425 (100.0%) |
| Supported compilation validity | 425/425 (100.0%) |
| Supported execution validity | 425/425 (100.0%) |
| Boundary label validity | 75/75 (100.0%) |

These figures say nothing about intent extraction, because the LLM is not in the
loop. They must not be quoted as end-to-end results.

**Full pipeline with the live parser**
(`run_nopcommerce_500_live_benchmark.py` →
`nopcommerce_500_live_benchmark_results.json`). This is the end-to-end
measurement, and the one to quote when a single set of 500-question figures is
reported.

| Metric | Result |
|---|---:|
| Parser success | 498/500 (99.6%) |
| Supported intent exact match | 345/425 (81.2%) |
| Supported answer rate | 422/425 (99.3%) |
| Supported execution validity | 422/425 (99.3%) |
| Boundary rejection accuracy | 74/75 (98.7%) |

Intent exact match is the lowest figure and the most informative one: in roughly
a fifth of supported requests the parser produced an intent differing from the
committed annotation, while the answer rate stayed at 99.3%. Whether those
divergent intents produced *correct* answers is a separate question the answer
rate does not settle, and it has not been measured. The gap between the two
must not be presented as evidence that the semantic layer absorbs intent
variation until it has been.

Boundary rejection accuracy is reported alongside the supported answer rate and
only alongside it. A system that declines every request scores 100% on the
first and is useless; the pairing is what makes either number mean anything.

## nopCommerce Standard Admin Reports

Files: `evaluation_dataset/nopcommerce_report_semantics.json`,
`evaluation_dataset/nopcommerce_report_oracles.json`

`nopcommerce_report_semantics.json` records the base entity, joins, mandatory
filters, aggregation expression, grouping, ordering and limit of each of
nopCommerce's twenty standard admin reports, extracted by reading nopCommerce
5.00.0 source at commit `64bdf2ff08c8b39e65717bcf974fb43dc2ef68f2`. Every entry
carries a file, method, and line-number citation.

AEGIS is not expected to reproduce the same SQL string. It is evaluated on
whether the report can be requested in ordinary business phrasing, and whether
the resulting query returns the same data as the platform's own report logic
against the same database.

| Check | Script | Result | Artifact |
|---|---|---:|---|
| Reproduced (ANSWER outcome + SQL emitted) | `verify_report_suite.py` | 20/20 | `report_suite_results.json` |
| Result set matches nopCommerce's own report logic | `verify_report_differential.py` | 12/20 (60.0%) | `report_differential_results.json` |

The first check is a proxy and must be labelled as one: it measures coverage of
the report *shape*, not correctness. Several of the twenty passed it while being
silently wrong — an order-level revenue sum fanned out across item-level joins,
a missing soft-delete filter, a customer breakdown grouped by display name — and
each returned a plausible, chartable number. Those defects are documented in
`docs/analysis/nopcommerce_sql_parity.md`.

The differential is the check that tests the claim. **Its recorded 12/20 must
be re-run before it is quoted.** `report_differential_results.json` was written
before the parity fixes in `aegis/server/compiler.py` and the intent-validation
changes that followed, and several of the eight recorded mismatches have exactly
the shape of defects that parity work reports as fixed. What the figure is today
is unknown.

Six of the twenty reports could not be pinned to a single implementing method in
nopCommerce's order/customer report services; each such entry says so in its own
`notes` field rather than guessing a mapping. See
`evaluation_dataset/README.md` for the list and the reason in each case.

## Why Two Components Are Needed

| Evaluation question | Dataset component |
|---|---|
| Can AEGIS handle the range of natural-language reporting requests a store owner asks? | 500-question natural user dataset |
| Does AEGIS refuse requests outside the semantic boundary? | The 75 boundary questions in that dataset |
| Does AEGIS match first-party nopCommerce report semantics where the platform provides its own oracle? | 20 standard admin reports, differential check |

Collapsing these into one accuracy number would be misleading. AEGIS is a
bounded reporting system, not an unbounded text-to-SQL engine. The thesis
therefore reports each component separately and states what each one validates.

## Recommended Thesis Wording

> The evaluation corpus contains 520 question-level items over a nopCommerce
> e-commerce database. The natural-language coverage dataset contains 500
> store-owner questions, of which 425 (85%) are intended to be answerable by the
> implemented semantic layer and 75 (15%) are realistic e-commerce boundary
> questions. Platform fidelity is evaluated against nopCommerce's own twenty
> standard admin reports, using the platform's own report implementations as the
> oracle and comparing result sets on a shared seeded database. The two
> components evaluate complementary properties: breadth of natural-language
> reporting behaviour with explicit refusal outside the semantic boundary, and
> fidelity to first-party platform reports where an independent oracle exists.
