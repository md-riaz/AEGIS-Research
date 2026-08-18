# Dataset and Evaluation Corpus

This thesis uses a composite, domain-specific evaluation corpus for the
nopCommerce deployment of AEGIS. The corpus is not a single public benchmark
such as Spider or BIRD; it is a project-specific e-commerce reporting dataset
designed to evaluate the properties claimed by AEGIS: safe report generation,
semantic-layer coverage, platform fidelity, and explicit refusal outside the
declared semantic boundary.

## Dataset Summary

| Dataset component | File | Size | Purpose |
|---|---:|---:|---|
| Expanded natural user question dataset | `evaluation_dataset/nopcommerce_500_natural_questions.json` | 500 questions | Main natural-language coverage dataset: 425 answerable questions over the implemented semantic layer and 75 realistic e-commerce boundary questions. |
| Admin fidelity phrasing dataset | `evaluation_dataset/nopcommerce_admin_fidelity_nl_questions.json` | 80 questions | Five natural-language phrasings for each of the 16 source-derived nopCommerce Admin fidelity oracle tasks. |
| General NL analytics benchmark | `evaluation_dataset/questions.json` | 107 questions | Broad natural-language reporting requests across the AEGIS analytical primitives, including answerable and out-of-scope probes. |
| Pattern classification audit | `evaluation_dataset/pattern_classification.json` | 100 labelled questions | Single-annotator classification of the first 100 general benchmark questions by analytical primitive. |
| Expected-behaviour annotations | `evaluation_dataset/semantic_correctness_annotations.json` | 107 annotations | Labels each general benchmark question as answerable, decline/clarify, write-request, or multi-part. |
| Admin analytics fidelity benchmark | `evaluation_dataset/nopcommerce_admin_analytics_oracles.json` | 16 tasks | First-party nopCommerce Admin report/dashboard oracle tasks extracted from source-code behaviour. |
| Semantic coverage benchmark | `evaluation_dataset/nopcommerce_semantic_coverage_questions.json` | 25 tasks | Natural user questions over the declared nopCommerce semantic layer, including 20 supported analytical compositions and 5 boundary refusals. |

Across the question/task files, the thesis therefore provides **728
question-level evaluation items**: 500 expanded natural user questions, 80
Admin fidelity phrasings, 107 earlier general natural-language analytics
questions, 16 source-derived platform-fidelity oracle tasks, and 25 focused
semantic-coverage tasks.

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

## General NL Analytics Benchmark

File: `evaluation_dataset/questions.json`

This is the broadest natural-language benchmark. It contains 107 reporting
questions. The first 100 are classified into the eleven AEGIS analytical
primitives:

| Pattern | Count |
|---|---:|
| KPI | 28 |
| Ranking | 21 |
| Trend | 10 |
| Comparison | 10 |
| Exception | 18 |
| Summary | 9 |
| Funnel | 1 |
| Cohort | 2 |
| Correlate | 1 |
| Segment | 0 |
| Tabular | 0 |

The remaining 7 questions are explicit boundary probes, including unmodelled
sentiment analysis, forecasting, HR/support-ticket concepts, web telemetry,
compound requests, vague requests, and a disguised write request.

This benchmark is useful for measuring:

- Whether AEGIS compiles safe SQL instead of free-form SQL.
- Whether answerable requests are translated into executable reports.
- Whether out-of-scope requests are declined rather than silently answered.
- How AEGIS compares with unconstrained direct LLM-to-SQL baselines.

It should not be presented as a pure "all questions are answerable" benchmark.
The committed annotations record that it intentionally contains both supported
and unsupported requests.

## Expanded 500-Question Natural User Dataset

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
shipping-method dimensions, and Approved predicates such as low stock.

The 75 boundary questions remain nopCommerce/e-commerce related but require
concepts or analytical templates not currently implemented: web telemetry,
marketing attribution, customer-support tickets, review-text sentiment,
forecasting, churn prediction, supplier performance, product affinity,
delivery SLA analysis, fraud scoring, and similar realistic store-owner asks.

This composition matches the thesis claim: AEGIS has a finite semantic
boundary. It should answer questions inside the deployment's Approved
vocabulary and decline plausible e-commerce questions outside it, rather than
pretending every question is expressible.

## Admin Analytics Fidelity Benchmark

File: `evaluation_dataset/nopcommerce_admin_analytics_oracles.json`

This benchmark contains 16 source-derived nopCommerce Admin analytics tasks:

- 8 Tier A formal report pages.
- 8 Tier B dashboard widgets.

The reference SQL is extracted from nopCommerce Admin source behaviour. AEGIS
is not expected to reproduce the same SQL string; it is evaluated on execution,
result shape, and result values against the same database.

Current result:

| Metric | Result |
|---|---:|
| Execution validity | 16/16 (100.0%) |
| Shape accuracy | 16/16 (100.0%) |
| Result accuracy | 15/16 (93.8%) |

This benchmark is the strongest platform-fidelity evidence because its oracle
comes from nopCommerce itself. Its limitation is scope: it only covers fixed
admin surfaces, not the broader space of natural user questions enabled by the
semantic layer.

## Admin Fidelity Natural-Language Phrasing Dataset

File: `evaluation_dataset/nopcommerce_admin_fidelity_nl_questions.json`

This dataset expands the 16 source-derived Admin fidelity oracle tasks into 80
ordinary natural-language phrasings: five phrasings for each source-derived
surface. It is intended to test whether business users can refer to the same
platform analytics surfaces in varied language, without memorising report
names or semantic-layer identifiers.

It should be reported alongside, not instead of, the 16 oracle tasks. The 16
tasks define the source-derived reference semantics; the 80 phrasings evaluate
natural-language robustness over those same targets.

## Semantic Coverage Benchmark

File: `evaluation_dataset/nopcommerce_semantic_coverage_questions.json`

This benchmark contains 25 author-generated tasks over the declared
nopCommerce semantic layer:

- 20 supported analytical compositions.
- 5 expected boundary refusals.

The supported tasks cover KPI, ranking, trend, segmentation, listings, time
filters, item-grain substitutions, customer/order/product/geography/store
dimensions, refunds, discounts, shipping, profit, low stock, latest orders, and
search terms.

The refusal tasks cover concepts intentionally outside the current semantic
layer or compiler templates: web telemetry, employees/support tickets,
marketing attribution, free-text review sentiment, and forecasting.

Current result:

| Metric | Result |
|---|---:|
| Supported execution validity | 20/20 (100.0%) |
| Supported shape accuracy | 20/20 (100.0%) |
| Supported result accuracy | 20/20 (100.0%) |
| Boundary rejection accuracy | 5/5 (100.0%) |

This benchmark supports the main thesis framing: AEGIS is not merely a clone of
nopCommerce's built-in reports. It can compose broader analytical views from
the Approved semantic layer, while retaining a finite and explicit boundary.

## Why Multiple Dataset Components Are Needed

The three question/task sets measure different things:

| Evaluation question | Best dataset component |
|---|---|
| Does the thesis have enough natural user questions for a dataset page? | Expanded 500-question natural user dataset |
| Can AEGIS handle broad natural-language reporting requests safely? | General 107-question benchmark |
| Does AEGIS match first-party nopCommerce report semantics where an oracle exists? | 16-task Admin analytics fidelity benchmark |
| Can users phrase those Admin-report targets naturally in multiple ways? | 80-question Admin fidelity phrasing dataset |
| Does the nopCommerce semantic layer support useful combinations beyond fixed reports? | 25-task semantic coverage benchmark |
| Does AEGIS refuse requests outside the semantic boundary? | Boundary probes in the 107-question and semantic-coverage datasets |

Collapsing these into one accuracy number would be misleading. AEGIS is a
bounded reporting system, not an infinite text-to-SQL engine. The thesis should
therefore report each dataset component separately and explain what each one
validates.

## Recommended Thesis Wording

> The evaluation corpus contains 728 question-level items over a nopCommerce
> e-commerce database. The main natural-language coverage dataset contains 500
> store-owner questions, of which 425 (85%) are intended to be answerable by
> the implemented semantic layer and 75 (15%) are realistic e-commerce
> boundary questions. The corpus also includes 80 natural-language phrasings of
> source-derived Admin fidelity targets, a 107-question general analytics
> benchmark, a 16-task source-derived nopCommerce Admin oracle benchmark, and a
> 25-task semantic-coverage benchmark. These components evaluate complementary
> properties: broad natural-language reporting behaviour, fidelity to
> first-party platform reports, compositional coverage beyond fixed built-in
> screens, and explicit refusal outside the semantic boundary.
