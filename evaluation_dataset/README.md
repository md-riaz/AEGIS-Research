# AEGIS Evaluation Datasets

This directory contains the static datasets, result artifacts, and verification
scripts backing the claims made in the AEGIS manuscript. The evaluation rests on
two evidence tracks, both derived from nopCommerce:

1. **A 500-question natural-language corpus** — breadth: does the architecture
   accept the range of questions a real user asks, and decline the ones it
   cannot express?
2. **nopCommerce's own twenty standard admin reports** — fidelity: when AEGIS
   answers a question the platform already answers, does it return the same
   data the platform's own report code returns?

The second is the stronger test of the two, because the report list and the
report logic are nopCommerce's, not this project's: there was no opportunity to
pick questions the system was known to handle, nor to write an expected-answer
set that happens to agree with AEGIS's output.

## Datasets

| File | Contents |
|---|---|
| `nopcommerce_500_natural_questions.json` | **500 static natural-language questions**: 425 supported semantic-layer requests and 75 realistic e-commerce boundary requests that should be rejected or clarified. |
| `nopcommerce_report_semantics.json` | The base entity, joins, mandatory filters, aggregation expression, grouping, ordering and limit of each of **nopCommerce's 20 standard admin reports**, extracted by reading nopCommerce 5.00.0 source. Every entry carries a file+method(+line) citation. |
| `nopcommerce_report_oracles.json` | Oracle queries for those 20 reports, for result-set comparison against AEGIS output on the same database. |

## Verification scripts and their result artifacts

| Script | Output | What it measures |
|---|---|---|
| `verify_nopcommerce_500_dataset.py` | `nopcommerce_500_dataset_results.json` | The **deterministic stages only**. It feeds each question's committed intent annotation straight into the mapper — no LLM call — and checks that supported requests resolve, compile, and execute against the configured database. |
| `run_nopcommerce_500_live_benchmark.py` | `nopcommerce_500_live_benchmark_results.json` | The **full pipeline**, with the live LLM parser in the loop: parser success, intent exact match, answer rate, execution validity, boundary rejection accuracy. |
| `verify_report_suite.py` | `report_suite_results.json` | Whether each of the 20 standard admin reports, asked in ordinary business phrasing, reaches an ANSWER outcome with SQL emitted. Needs live LLM credentials; needs no database. |
| `verify_report_differential.py` | `report_differential_results.json` | Whether AEGIS's SQL and nopCommerce's own report logic **return the same data** when executed against the same seeded database. |
| `run_500_baseline_llm.py` | `baseline_500_llm_results.json` | The **direct LLM-to-SQL baseline** over the same 500 questions, same model, same database: translatability, execution validity, unsafe SQL, and how often it answers an out-of-scope question instead of declining. |
| `docker_seed_smoke.py` | — | That the bundled Docker stack comes up with the seed data actually loaded. |

### Latency

Every runner records per-stage timings on each result row and summarises them
(n, mean, median, p95, max) under `latency` in its result artifact. The stages
are `parse_ms` (the only stage that calls the model), `resolve_ms`,
`compile_ms`, `execute_ms`, and `deterministic_ms` — everything after the model
call, summed.

The split is the point. The architecture's claim is that SQL authority lives
entirely in the stages after the parser, so how much of the wall clock each half
accounts for is a property to measure rather than assert. The median and p95 are
reported alongside the mean because the model stage is the one with a long tail,
and a mean alone cannot distinguish a uniformly slow stage from a fast one with
occasional stalls.

Timings are taken over supported questions only. Boundary questions stop at the
resolver by design, so folding them in would describe a pipeline faster than the
one that answers anything.

### The baseline arm

`run_500_baseline_llm.py` asks the **same model through the same endpoint** to
write MySQL directly, with no semantic layer. A baseline served by a weaker
model would flatter AEGIS for a reason that has nothing to do with the
architecture.

Its sharpest number is `boundary_false_answer_rate`: of the 75 questions the
semantic layer cannot express, how many the baseline answered with confident,
executable SQL instead of declining. AEGIS cannot express these at all. No
public text-to-SQL benchmark measures this, because their datasets contain no
unanswerable questions.

SQL that fails the compiler's own forbidden-pattern scan is recorded and never
executed, and the benchmark's database session is opened read-only, so a write
that slipped past the scan would be refused by the server rather than by the
script's judgement. The forbidden patterns are imported from
`SQLCompiler.FORBIDDEN_PATTERNS` rather than restated, so both arms are judged
by one definition that cannot drift.

### The two 500-question runs measure different things

`verify_nopcommerce_500_dataset.py` constructs its intent with
`IntentObject(**item["intent"])`. No model is called. Its figures therefore say
nothing about intent extraction, and must never be presented as end-to-end
results — they are a regression gate on the mapper and compiler.

`run_nopcommerce_500_live_benchmark.py` is the end-to-end measurement. When a
single set of 500-question figures is quoted, it should be this one.

### A pass/fail check must test the claim, not a proxy for it

`verify_report_suite.py` counts a report as reproduced when the outcome is
ANSWER *and* the compiler emitted SQL. That is coverage of the report *shape*,
not correctness of the report: several of the 20 passed that check while being
silently wrong (see `docs/analysis/nopcommerce_sql_parity.md`).
`verify_report_differential.py` is the check that tests the actual claim, by
comparing result sets. Quote the differential, not the suite, when asked whether
AEGIS reproduces the reports.

## Committed figures

Each figure below is the value in the committed result artifact named beside it.
Regenerate the artifact and this table together; a table older than the results
file it summarises is the stale-artifact failure this directory is most prone
to.

**500 questions, deterministic stages** (`nopcommerce_500_dataset_results.json`)
— no LLM in the loop:

| Metric | Value |
|---|---|
| Supported resolution validity | 425/425 (100.0%) |
| Supported compilation validity | 425/425 (100.0%) |
| Supported execution validity | 425/425 (100.0%) |
| Boundary label validity | 75/75 (100.0%) |

**500 questions, live LLM parser** (`nopcommerce_500_live_benchmark_results.json`):

| Metric | Value |
|---|---|
| Parser success | 498/500 (99.6%) |
| Supported intent exact match | 345/425 (81.2%) |
| Supported answer rate | 422/425 (99.3%) |
| Supported execution validity | 422/425 (99.3%) |
| Boundary rejection accuracy | 74/75 (98.7%) |

Intent exact match is the lowest figure here and the most informative one: in
roughly a fifth of supported requests the parser produced an intent that differs
from the committed annotation, while the answer rate stayed at 99.3%. Whether
those divergent intents produced *correct* answers is a separate question that
the answer rate does not settle, and it has not been measured. Do not present
the gap between the two as evidence that the semantic layer absorbs intent
variation until it has been.

**20 standard admin reports:**

| Check | Value | Artifact |
|---|---|---|
| Reproduced (ANSWER + SQL emitted) | 20/20 | `report_suite_results.json` |
| Result set matches nopCommerce's own report logic | 12/20 (60.0%) | `report_differential_results.json` |

**The differential figure must be re-run before it is quoted.**
`report_differential_results.json` was written before the parity fixes in
`aegis/server/compiler.py` and the intent-validation changes that followed.
Several of the eight recorded mismatches have exactly the shape of defects
`docs/analysis/nopcommerce_sql_parity.md` reports as fixed — a customer
breakdown labelled by display name rather than the oracle's email, and
ordering/limit differences on otherwise row-matched results. What the number is
today is unknown, and 60.0% should not be quoted as the current result.

## nopCommerce Report Semantics Reference

`nopcommerce_report_semantics.json` extracts the semantics of nopCommerce's own
twenty admin report implementations directly from its source — base entity,
joins, mandatory filters, aggregation expressions, group-by, and limits — each
with a file, method, and line-number citation into nopSolutions/nopCommerce at
the commit recorded in the file's own `source_commit` field
(`64bdf2ff08c8b39e65717bcf974fb43dc2ef68f2`, nopCommerce 5.00.0).

This is the reference the generated SQL was checked against for the parity
work (see `docs/analysis/nopcommerce_sql_parity.md`). Comparing generated SQL
against the host platform's own source, rather than against an expected-answer
set written by this project, is stronger evidence: this project could not have
shaped the comparison to favor itself, because the comparison target is code
nopCommerce shipped independently of this thesis.

Six of the twenty reports could not be pinned to a single implementing method
in nopCommerce's two order/customer report services, and the file says so in
each entry's own `notes` field rather than guessing a mapping:

- **Low stock** — the underlying logic lives in `IProductService`, a
  different service than the two report services this extraction covers.
- **Latest orders** — the dashboard widget is wired to the general-purpose
  admin `OrderList` action (`IOrderService`/`OrderController`), not a
  report-service method.
- **Shipment count** — no implementing method was found anywhere in the
  searched source at all.
- **Refund totals** — `RefundedAmount` is only ever summed as one component
  inside three other reports' aggregations; no method computes it as a
  standalone report.
- **Tax collected** — the same pattern as Refund totals: `OrderTax` is a
  component summed inside other reports, never a dedicated method of its own.
- **Daily revenue trend** — implemented via `OrderController.LoadOrderStatistics`
  / `IOrderService.SearchOrdersAsync`, a different service, and even there it
  counts orders rather than summing revenue — not a true match either
  organizationally or semantically.

The other fourteen do map to a single, named service method (with line
numbers), though several carry their own caveats worth reading directly in the
file — e.g. "Sales by category" and "Sales by manufacturer" are not separate
methods but the same `SalesSummaryReportAsync` used as report #1, parameterized,
and several reports' filters narrow which orders qualify without narrowing the
summed order-level totals to just the matching line items.

## Reproducing the evaluation

1. **Python environment:**
   ```bash
   python -m venv .venv
   .venv/Scripts/activate   # or: source .venv/bin/activate on Linux/Mac
   pip install -r requirements.txt
   ```

2. **Database:** either bring up the bundled stack —
   ```bash
   docker compose up -d db
   ```
   (seeds MySQL 8.0 from `database/schema.sql` + `database/mock_data.sql` on
   port 3307) — or point at any MySQL 8 instance already loaded with that
   schema/data. Either way, run the date-refresh script so "today"/"this week"
   style queries return non-empty results regardless of when you run the
   evaluation:
   ```bash
   mysql -h127.0.0.1 -P3307 -uroot -proot <database_name> < database/3_refresh_dates.sql
   ```

3. **`.env`** (repository root):
   ```env
   LLM_BASE_URL=https://api.groq.com/openai/v1     # or any OpenAI-compatible endpoint
   LLM_API_KEY=your_key_here
   LLM_MODEL=llama-3.1-8b-instant

   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3307
   MYSQL_USER=root
   MYSQL_PASSWORD=root
   MYSQL_DATABASE=aegis                              # or your database name
   ```

4. **Run the two tracks:**
   ```bash
   # 500 questions — deterministic stages (database only, no LLM)
   python evaluation_dataset/verify_nopcommerce_500_dataset.py

   # 500 questions — end-to-end with the live parser (LLM + database)
   python evaluation_dataset/run_nopcommerce_500_live_benchmark.py

   # 20 standard admin reports — shape coverage (LLM, no database)
   python evaluation_dataset/verify_report_suite.py

   # 20 standard admin reports — result-set differential (database)
   python evaluation_dataset/verify_report_differential.py

   # Direct LLM-to-SQL baseline over the same 500 questions (LLM + database)
   python evaluation_dataset/run_500_baseline_llm.py
   ```

   `verify_report_differential.py` reads `report_suite_results.json`, so run the
   suite before the differential when the compiler has changed.

*(Re-running the live benchmark invokes the LLM API and may produce slightly
different figures across model versions or providers. AEGIS's compiled SQL is
deterministic given an identical intent object; intent extraction itself is
not.)*

## What each figure does and does not prove

- **Execution validity** means the SQL ran without a database error. It says
  nothing about whether the right answer came back.
- **Differential match** is the only figure here that compares actual returned
  data against an independent oracle, and it is the one to quote when asked
  whether AEGIS is correct.
- **Boundary rejection accuracy** is only meaningful alongside the supported
  answer rate. A system that declines everything scores 100% on the first and is
  useless; the pairing is what makes either number mean anything.

The AEGIS architecture prevents SQL injection through untrusted natural-language
input via parameterized SQL templates and restricted vocabulary injection — a
structural guarantee that holds within the defined threat boundary of trusted
semantic-layer definitions.
