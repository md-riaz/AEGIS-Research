# nopCommerce SQL Parity: AEGIS Against the Platform's Own Report Implementations

## Method

Two artifacts drive this comparison, both committed under `evaluation_dataset/`:

- `nopcommerce_report_semantics.json` — the base entity, joins, mandatory
  filters, aggregation expression, grouping, ordering and limit of each of
  nopCommerce's 20 standard admin reports, extracted by reading nopCommerce
  5.00.0 source at commit `64bdf2ff08c8b39e65717bcf974fb43dc2ef68f2`. Every
  entry carries a file+method(+line) citation.
- `report_suite_results.json` — the SQL AEGIS actually compiles for the same
  20 report questions, produced by `evaluation_dataset/verify_report_suite.py`
  running the real parse → resolve → compile pipeline (no database required,
  since compilation is offline; the script's own docstring is explicit that
  this checks compilability, not result-set correctness). All 20 questions
  reached `outcome: answer` with SQL emitted (`"total": 20, "reproduced": 20`).

Comparing against the platform's own service-layer source is stronger
evidence than comparing against a self-authored specification of what the
reports "should" do: nopCommerce's source is not a hypothesis AEGIS's authors
could have shaped to fit AEGIS's output, and it exposes exactly the kind of
implementation detail — order-level totals reused across item-level
breakdowns, a hardcoded status set, a role filter — that a self-written
expectation would tend to silently agree with the implementation on, because
both were written by people reasoning the same "obvious" way.

Every claim below was re-checked in this pass against (a) the two JSON
artifacts, (b) `git diff` against the working tree's pre-fix state, and (c)
the nopCommerce source itself at the recorded commit, read from the read-only
clone at `/workspace/nopsolutions/nopcommerce`. Where a detail in the original
finding list did not hold up, it is corrected below rather than repeated.

All seven defects below are now fixed in the working tree
(`aegis/server/compiler.py`, `aegis/server/mapper.py`,
`aegis/server/semantic_layer.py`, `aegis/server/models.py`,
`aegis/server/explain.py`) and covered by regression tests
(`tests/test_resolution.py::TestGrainGuard`,
`tests/test_platform_parity.py`). They are recorded here as defects that
existed and were corrected, not as though AEGIS had always behaved this way.

---

## Findings, fixed

### 1. Order-level revenue fanned out across item-level joins

AEGIS compiled "revenue by category / manufacturer / product" as
`SUM(o.OrderTotal - o.RefundedAmount)` while joining
`Order → OrderItem → Product → …`. An order with N matching line items
contributed its whole order total N times.

nopCommerce's own bestsellers report groups **order items**, not orders, and
aggregates `g.Sum(x => x.PriceExclTax)` per product
(`Nop.Services/Orders/OrderReportService.cs`, `BestSellersReportAsync`,
group/select at lines 703–711 — confirmed by reading the method directly).
nopCommerce's *Sales Summary* method, filtered by category or manufacturer, is
not a counterexample: its own extraction notes flag that this filter only
decides which orders qualify and still sums the **whole** order total,
including revenue from lines outside the filtered category — a caveat about
nopCommerce's own report, not evidence that summing whole orders per category
is correct behavior to copy.

**Fix**: `Metric.item_grain_equivalent` in the semantic layer declares
`revenue`'s item-grain counterpart (`line_item_revenue`,
`SUM(oi.PriceExclTax)`). `SemanticResolver._resolve_grain` substitutes it
whenever an order-grain metric's join path crosses a fan-out table
(`OrderItem`, `Product`, `Product_Category_Mapping`, `Category`,
`Product_Manufacturer_Mapping`, `Manufacturer`). The substitution is written
into `AnalysisPlan.notes` and read out by `explain_plan`, so a user asking for
"revenue by category" is told the number is product revenue, not silently
handed a differently-defined one. Compiled output confirms this:
`report_suite_results.json`'s "Sales by category" SQL aggregates
`SUM(oi.PriceExclTax)` and its `interpretation` field states the substitution
in the same words the plan note carries.

### 2. No soft-delete filters

`Order`, `Product` and `Customer` all implement `ISoftDeletedEntity`
(confirmed directly in
`Nop.Core/Domain/{Orders/Order.cs, Catalog/Product.cs, Customers/Customer.cs}`),
and every nopCommerce report reachable from the two service files applies
`!Deleted` before aggregating — e.g. `SalesSummaryReportAsync` line 482,
`BestSellersReportAsync`'s `SearchOrderItems` line 129, `GetCountryReportAsync`
line 193, `GetBestCustomersReportAsync` lines 80–81. AEGIS applied none of
these.

**Fix**: `MANDATORY_PREDICATES` (`Order → o.Deleted = 0`,
`Product → p.Deleted = 0`, `Customer → cu.Deleted = 0`) is appended by the
compiler against the **resolved** join path — the tables the compiler
actually decided to join — rather than the plan's declared one. This
distinction is real: a category breakdown reaches `Product` only as a
bridging table on the way to `Category`, a binding that names neither
`Product` nor its predicate directly, so reading the declared path would have
missed it. Confirmed in the compiled SQL: "Sales by category" carries both
`o.Deleted = 0` and `p.Deleted = 0`.

**This fix is not complete, and the gap is visible in the artifacts
themselves** (see "Additional gaps observed" below): a metric whose binding
table is `OrderItem` alone never pulls `Order` into the resolved join path,
so `o.Deleted = 0` is never added even though nopCommerce's equivalent query
does apply it.

### 3. Customer breakdowns grouped by display name

AEGIS grouped `GROUP BY CONCAT(FirstName, ' ', LastName)`, merging two
different customers who share a name into a single row and summing their
revenue together. nopCommerce's `GetBestCustomersReportAsync` groups
`group co by co.c.Id` (`Nop.Services/Customers/CustomerReportService.cs`,
confirmed at line ~83) — customer identity, not the rendered name.

**Fix**: `Dimension.group_expr` lets a dimension declare a GROUP BY
expression distinct from its display `sql_expr`; `customer_name`'s
`group_expr` is set to `cu.Id`. Confirmed in compiled SQL: "Best customers by
order total" selects `CONCAT(cu.FirstName, ' ', cu.LastName) AS label` but
groups `GROUP BY cu.Id`.

### 4. "Registered customers" counted only customers who had ordered

The compiler hardcoded `o.CreatedOnUtc` as the time anchor for every metric,
including `customer_count`. That both applied the wrong date column (customer
registration date, not order date) and dragged the `Order` table into the
join — so "customers registered this month" silently meant "customers who
ordered this month," excluding every registrant who had not yet bought
anything.

**Fix**: `Metric.time_anchor` lets a metric declare which column its time
window binds to (`customer_count` → `cu.CreatedOnUtc`); the compiler reads
`metric.time_anchor` instead of a hardcoded column. Confirmed in compiled
SQL: "Registered customers" filters on `cu.CreatedOnUtc` with no `Order` join
at all.

### 5. Unbindable filter fields silently became `o.Id`

A filter field the semantic layer could not resolve fell through to
`ALIAS_TO_TABLE.get(field_name, "o.Id")`, compiling to e.g.
`o.Id = 'incomplete_order'`. This runs, returns zero rows (or an arbitrary
row, if `'incomplete_order'` happened to coerce to a real id), and reports
itself as a successful answer with no signal that the condition was
discarded.

**Fix**: `UnknownFilterFieldError` is now raised instead of falling through.
An unbindable filter is an unanswerable request and must say so.

### 6. Two report-shaped concepts missing from the vocabulary

nopCommerce names both of these as first-class admin reports; neither
existed as an expressible AEGIS concept.

- **Low stock**: nopCommerce compares each product's own stock against its
  own minimum (`p.StockQuantity <= p.MinStockQuantity`,
  `Nop.Services/Catalog/ProductService.cs`, `GetLowStockProductsAsync`, lines
  1233–1244 — read directly to confirm since the report-semantics extraction
  itself could not follow this predicate from the two report-service files
  and correctly reported it as `null` rather than guess). There is no
  user-supplied threshold to bind a filter to.
- **Incomplete orders**: `OrderStatusId = 10` (`OrderStatus.Pending`,
  confirmed in `Nop.Core/Domain/Orders/OrderStatus.cs`), per
  `OrderModelFactory.PrepareOrderIncompleteReportListModelAsync` line 1846.

**Fix**: `GOVERNED_PREDICATES` — whole WHERE fragments authored in the
semantic layer, referenced only by key (`PREDICATE_FIELD`), rendered by
lookup and never by interpolation. An unrecognized key raises rather than
silently dropping the predicate. No user text reaches SQL through this path,
so this does not reopen the injection surface the parameterized-filter design
otherwise closes.

**This fix, too, is narrower than the platform's own report** — see
"Additional gaps observed" below: the low-stock predicate reproduces only the
single-warehouse, non-attribute-combination branch of nopCommerce's own
report.

### 7. A mislabel found in passing

The pre-existing `BUSINESS_LOGIC_MAPPINGS["abandoned"]` mapped to
`OrderStatusId = 40`. Confirmed against
`Nop.Core/Domain/Orders/OrderStatus.cs`: 40 is **Cancelled**, not abandoned.
An abandoned cart, in nopCommerce's own domain model, is a `ShoppingCartItem`
row that was never converted into an order at all — a different table,
with no `OrderStatusId` to filter on. This is ordinary nopCommerce domain
knowledge, not something drawn from either JSON artifact, so it carries no
file+line citation here beyond the `OrderStatus` enum confirming that 40
means Cancelled.

The mapping was kept (a plan built before the fix must keep resolving) and
relabeled: `"cancelled"` was added as its honestly-named twin, and the
docstring states plainly that `"abandoned"` here means Cancelled, not
cart abandonment. AEGIS still has no way to answer a genuine
"abandoned cart" question; it now no longer pretends `"abandoned"` answers
one under the order-status vocabulary.

---

## Residual divergences (declared, not defects)

These are differences between what AEGIS computes and what nopCommerce's
admin screens show, that are not being "fixed" because they are legitimate
definitional choices — but they mean the two systems will not print the same
number, and that should be stated rather than discovered by a reader later.

1. **Revenue's refund treatment.** AEGIS's `revenue` metric is
   `SUM(OrderTotal - RefundedAmount)`. nopCommerce's own Sales Summary
   (`SalesSummaryReportAsync`) computes `OrderTotalSum = Sum(o.OrderTotal)`
   and reports `OrderRefundedAmountSum` as a **separate** column; only the
   derived `Profit` figure subtracts refunds, and even then alongside
   shipping, tax, and cost, not as a net-revenue figure. A declared
   definitional choice, not a defect — but confirmed via the artifact that
   the two systems' "revenue" will not agree numerically wherever any
   refunds exist.

2. **"Registered customers" role scope.** nopCommerce's
   `GetRegisteredCustomersReportAsync` counts only customers holding the
   built-in Registered role (`customerRoleIds: [registeredCustomerRole.Id]`,
   confirmed directly in `CustomerReportService.cs` lines 119–126). AEGIS's
   compiled SQL (`COUNT(DISTINCT cu.Id) ... WHERE cu.Deleted = 0` plus the
   date window) has no role filter at all — it counts every non-deleted
   customer, guests included.

3. **"Average order value" doesn't average, in nopCommerce.** The extraction
   notes for this report are unambiguous: nopCommerce's admin screen name is
   misleading — `OrderAverageReportAsync` / `GetOrderAverageReportLineAsync`
   never divide `SumOrders` by `CountOrders` anywhere in the traced code; the
   screen shows a raw `SUM(o.OrderTotal)` per (status, period) cell despite
   its name. AEGIS's compiled SQL for this report is
   `AVG(COALESCE(o.OrderTotal, 0))` — a true average. Here AEGIS is arguably
   **more correct** than the platform it was checked against, which is worth
   saying plainly rather than treating every divergence as an AEGIS defect.
   Separately, and in AEGIS's favor in a different way: nopCommerce's version
   is not one number but 20 independent cells (4 hardcoded statuses × 5
   fixed periods, each its own database round trip), so the two are not
   simply the same computation done two ways — AEGIS's single overall
   average and nopCommerce's per-status-per-period grid answer different
   questions, and "AEGIS's number is nopCommerce's number, just averaged"
   is not a claim this comparison supports.

4. **Store, vendor and published scoping are unmodeled.** Most nopCommerce
   report methods accept `storeId`, `vendorId`, and/or `showHidden` /
   `loadPublishedOnly` parameters (e.g. Sales Summary, Bestsellers, Low
   Stock, Never Sold all take at least one of these; Country Sales and Best
   Customers take none, per their own extraction notes). AEGIS's semantic
   layer has no equivalent concept for any of the three — every AEGIS query
   is implicitly store-wide, vendor-wide and includes unpublished products.

5. **Six of the twenty reports could not be tied to one dedicated service
   method** by the extraction — this needs one correction to the number:
   read literally against the artifact, it is **seven reports**, grouped
   under six explanatory entries because two of them (Refund totals, Tax
   collected) share one underlying cause. The seven, with what the artifact
   says about each:
   - **Low stock** — the implementation lives in `IProductService`, outside
     the two report-service files the extraction was scoped to; reported as
     `null` rather than guessed.
   - **Order status breakdown** — no query in either service file returns
     order counts grouped across all statuses in one call; this "report"
     fully overlaps report #16 (Average order value)'s per-status cells, and
     the extraction cross-references it there instead of inventing a
     separate mapping.
   - **Latest orders** — dashboard widget only, backed by the general-purpose
     `OrderController.OrderList` action (`IOrderService`), not either report
     service.
   - **Shipment count** — no implementing method found anywhere in the
     provided source; the extraction's own note says a repo-wide search for
     shipment-count report code returned nothing tied to a reports feature.
   - **Refund totals** and **Tax collected** — both exist only as
     intermediate subtracted terms inside the Sales Summary "Profit" formula
     and as raw columns on `OrderAverageReportLine`; there is no admin
     screen whose sole purpose is either one.
   - **Daily revenue trend** — the closest artifact
     (`OrderController.LoadOrderStatistics`) is a **count of orders**, not a
     sum of revenue, and lives in a different service (`IOrderService`)
     entirely; the extraction flags this as not a true match either
     semantically or organizationally.

   ("Sales summary today" carries a similar caveat — no dedicated "today"
   entry point exists either — but unlike the seven above, its semantics
   were fully derived from a concrete, cited code path
   (`OrderAverageReportAsync`'s "today" branch) rather than left `null`, so
   it is not counted among the unmapped seven here.)

---

## Additional gaps observed during this verification

These were not in the original finding list. They surfaced from directly
comparing the compiled SQL in `report_suite_results.json` against the
mandatory filters recorded for the same report in
`nopcommerce_report_semantics.json`, and are reported because the evaluation
policy this repository runs under treats a withheld real result as a second
failure on top of the first.

- **The soft-delete fix (Finding 2) does not reach every report it should.**
  `MANDATORY_PREDICATES` is only applied for tables the compiler's resolved
  join path actually visits. The `item_quantity` metric
  (`SUM(oi.Quantity)`, "Quantity Sold") binds to `OrderItem` alone and never
  requires `Order`, so "Bestsellers by quantity" compiles to
  `FROM OrderItem oi LEFT JOIN Product p ... WHERE p.Deleted = 0` — no
  `Order` join, and no `o.Deleted = 0`. nopCommerce's own bestsellers query
  (`SearchOrderItems`, `!o.Deleted && !p.Deleted`, line 129) always joins
  `Order` for this same check, quantity-only or not. Concretely: quantities
  sold via a soft-deleted order still count toward AEGIS's "units sold"
  total. This is a real, currently-open gap in Finding 2's fix, not a
  theoretical one — it is visible directly in the committed
  `report_suite_results.json`.

- **"Products never purchased" omits the platform's product-type
  restriction and its soft-delete-on-orders check.** nopCommerce's
  `ProductsNeverSoldAsync` mandatorily restricts to
  `p.ProductTypeId == (int)ProductType.SimpleProduct` — grouped/bundled
  products are excluded from the report's very definition, sold or not — and
  its "has this ever been ordered" subquery filters `!o.Deleted`. AEGIS's
  compiled SQL (`FROM Product p LEFT JOIN OrderItem oi ... WHERE
  COALESCE(oi.Quantity, 0) = 0 AND p.Deleted = 0`) has neither: it has no
  `ProductTypeId` filter, so grouped/bundled products can appear in AEGIS's
  list when nopCommerce's report design excludes them unconditionally; and
  it never joins `Order`, so items sold only through a soft-deleted order
  would still make a product ineligible for "never purchased" in AEGIS,
  where nopCommerce's subquery would not count that sale at all.

- **The `low_stock` governed predicate covers only part of nopCommerce's own
  report.** `GetLowStockProductsAsync`'s multi-warehouse branch sums
  `ProductWarehouseInventory` rows (`StockQuantity - ReservedQuantity`) when
  `UseMultipleWarehouses` is set, rather than reading `p.StockQuantity`
  directly; AEGIS's predicate always reads `p.StockQuantity`. Separately,
  nopCommerce's Low Stock screen merges this query's results with a second,
  independent one over `ProductAttributeCombination` rows
  (`GetLowStockProductCombinationsAsync`) for attribute-level variants; the
  `low_stock` governed predicate implements only the first of the two.

None of these three are corrected in this pass — flagging them is the extent
of this document's job. Fixing them would mean widening
`MANDATORY_PREDICATES` to reach single-table metrics (or deciding that some
metrics are legitimately order-agnostic and living with the gap), adding a
product-type-aware variant for "never purchased," and either accepting the
`low_stock` predicate's declared scope-of-coverage as a stated limitation or
building the multi-warehouse and combination branches out. Each is a real
follow-up, not a rhetorical one.

---

## Limits of the comparison method

This was a **textual** comparison: nopCommerce's C#/LINQ source, read and
transcribed by hand (with method+line citations so each transcription can be
checked), against AEGIS's compiled SQL text, read and compared by hand
against those transcriptions. No result-set equivalence testing was run — no
database was available in this environment to load nopCommerce sample data,
run both nopCommerce's query and AEGIS's compiled SQL against the same rows,
and diff the output. Every claim in this document is therefore a claim about
matching or diverging *query semantics as written*, not about matching
numbers on real data.

This matters in at least one concrete way already visible in the artifacts:
`nopcommerce_report_semantics.json`'s own notes on `SalesSummaryReportAsync`
observe that a category/manufacturer filter changes *which orders qualify*
without changing *what gets summed* — a subtlety that a same-database
differential test would surface immediately (AEGIS's line-item sum and
nopCommerce's whole-order sum would visibly disagree on the same data) but
that a purely textual reading could describe accurately while still leaving
a reader to do the arithmetic themselves to see the size of the disagreement.

The obvious next step is exactly that same-database differential test: seed
a nopCommerce install (or a schema-faithful fixture) with data exercising
soft-deletes, shared customer names, multi-category orders and refunds, run
both nopCommerce's admin report and AEGIS's compiled SQL against it, and diff
row-for-row. That test does not exist yet. Nothing in this document should be
read as claiming it does.

## References

- `evaluation_dataset/nopcommerce_report_semantics.json` — nopCommerce
  5.00.0, commit `64bdf2ff08c8b39e65717bcf974fb43dc2ef68f2`.
- `evaluation_dataset/report_suite_results.json` — produced by
  `evaluation_dataset/verify_report_suite.py`; `"total": 20, "reproduced": 20`.
- Fix locations: `aegis/server/semantic_layer.py` (`Metric.item_grain_equivalent`,
  `Metric.time_anchor`, `MANDATORY_PREDICATES`, `GOVERNED_PREDICATES`,
  `PREDICATE_FIELD`), `aegis/server/compiler.py` (`UnknownFilterFieldError`,
  `_mandatory_predicates`, governed-predicate lookup in
  `_build_single_filter`), `aegis/server/mapper.py`
  (`SemanticResolver._resolve_grain`, `_as_filter`), `aegis/server/models.py`
  (`AnalysisPlan.notes`), `aegis/server/explain.py` (`explain_plan` reading
  `plan.notes`).
- Regression coverage: `tests/test_resolution.py::TestGrainGuard`,
  `tests/test_platform_parity.py`.
