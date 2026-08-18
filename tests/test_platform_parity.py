"""
Regression tests for divergences found by comparing compiled SQL against
nopCommerce's own report implementations.

Each test here corresponds to a specific query in
``nopSolutions/nopCommerce`` whose semantics AEGIS did not reproduce.  The
divergences share one property that makes them worth pinning: every one of them
produced a query that compiled, executed, returned a plausible number, and was
wrong, with nothing in the output that could reveal it.  That is the failure
mode this project exists to eliminate, so a test that merely checked "SQL was
produced" would have passed against all of them — as the report-suite check
initially did.

Extracted semantics are recorded in
``evaluation_dataset/nopcommerce_report_semantics.json`` with file and method
citations, so each expectation below can be checked against the platform source
rather than taken on trust.
"""

import unittest

from aegis.server.compiler import (SQLCompiler, SecurityError,
                                   UnknownFilterFieldError)
from aegis.server.mapper import SemanticMapper
from aegis.server.models import Filter, IntentObject
from aegis.server.semantic_layer import APPROVED_PREDICATES, PREDICATE_FIELD


def _sql(intent, question):
    resolution = SemanticMapper().resolve(intent, question)
    return SQLCompiler().compile(resolution.plan)[0]


class TestSoftDeleteFilters(unittest.TestCase):
    """nopCommerce filters `!Deleted` on Order, Product and Customer in every
    report before aggregating; AEGIS filtered none of them, so every total
    silently included soft-deleted rows."""

    def test_order_totals_exclude_deleted_orders(self):
        sql = _sql(IntentObject(intent_class="kpi", metric_term="revenue"),
                   "total revenue")
        self.assertIn("o.Deleted = 0", sql)

    def test_customer_breakdown_excludes_deleted_customers_and_orders(self):
        sql = _sql(
            IntentObject(intent_class="ranking", metric_term="revenue",
                         dimension_term="customer_name", sort="desc"),
            "top customers by amount spent",
        )
        self.assertIn("cu.Deleted = 0", sql)
        self.assertIn("o.Deleted = 0", sql)

    def test_bridging_tables_are_filtered_too(self):
        """A category breakdown reaches Category through Product, which no
        binding names — so reading the plan's declared join path rather than
        the compiler's resolved one missed the Product flag entirely."""
        sql = _sql(
            IntentObject(intent_class="segment", metric_term="revenue",
                         dimension_term="category_name"),
            "revenue by category",
        )
        self.assertIn("p.Deleted = 0", sql)


class TestGroupingIdentity(unittest.TestCase):
    def test_customers_group_by_id_not_display_name(self):
        """GetBestCustomersReportAsync groups by Customer.Id. Grouping by the
        rendered name merges two different people who share one, producing a
        single row whose total is the sum of both."""
        sql = _sql(
            IntentObject(intent_class="ranking", metric_term="revenue",
                         dimension_term="customer_name", sort="desc"),
            "top customers by amount spent",
        )
        self.assertIn("GROUP BY cu.Id", sql)
        # The label must still be the readable name, not the id.
        self.assertIn("CONCAT(cu.FirstName", sql)


class TestApprovedPredicates(unittest.TestCase):
    """Concepts the platform names as first-class reports but which cannot be
    written as `field operator value`, because the comparison is between two
    columns rather than against a user-supplied threshold."""

    def test_low_stock_compares_each_product_to_its_own_minimum(self):
        sql = SQLCompiler()._build_single_filter(
            Filter(field=PREDICATE_FIELD, operator="=", value="low_stock")
        )[0]
        self.assertIn("<= p.MinStockQuantity", sql)
        self.assertIn("p.ManageInventoryMethodId = 1", sql)
        self.assertIn("p.ProductTypeId <> 10", sql)
        # Both of the platform's branches: a multi-warehouse product's real
        # level is the sum over its warehouse rows, not Product.StockQuantity,
        # so comparing the Product column for every product returns the wrong
        # set of products for any catalogue that uses warehouses.
        self.assertIn("p.UseMultipleWarehouses = 1", sql)
        self.assertIn("pwi.StockQuantity - pwi.ReservedQuantity", sql)
        self.assertIn("ELSE p.StockQuantity END", sql)

    def test_item_level_measures_join_order_for_its_delete_flag(self):
        """OrderItem-bound metrics had no Order join, so `o.Deleted = 0` could
        never apply — bestsellers counted lines from soft-deleted orders.
        nopCommerce's SearchOrderItems joins Order for exactly this."""
        sql = _sql(
            IntentObject(intent_class="ranking", metric_term="item_quantity",
                         dimension_term="product_name", sort="desc"),
            "which products sold the most units",
        )
        self.assertIn("o.Deleted = 0", sql)
        self.assertIn("p.Deleted = 0", sql)

    def test_predicate_value_is_a_key_never_sql(self):
        """The filter carries an id; the SQL lives in the semantic layer. A
        request can select a fragment but cannot author or extend one."""
        for entry in APPROVED_PREDICATES.values():
            self.assertNotIn(";", entry["sql"])

    def test_unknown_predicate_key_is_refused(self):
        # The exact type matters: `Exception` would also pass on a TypeError
        # from a renamed argument, so the test could keep reporting a working
        # refusal long after the refusal had stopped happening.
        with self.assertRaises(SecurityError):
            SQLCompiler()._build_single_filter(
                Filter(field=PREDICATE_FIELD, operator="=", value="not_a_predicate")
            )


class TestUnknownFilterField(unittest.TestCase):
    def test_unbindable_filter_field_raises_instead_of_targeting_order_id(self):
        """Old behaviour: an unrecognised field fell back to ``o.Id``, so a
        condition the layer could not express became ``o.Id = 'incomplete'`` —
        a query that runs, returns nothing, and reports success."""
        with self.assertRaises(UnknownFilterFieldError):
            SQLCompiler()._build_single_filter(
                Filter(field="not_a_real_field", operator="=", value="x")
            )




class TestExecutableSQL(unittest.TestCase):
    """Defects that only running the queries could expose.

    Each of these compiled without complaint and passed every check that asks
    whether SQL was produced. They were found by installing MySQL and executing
    all 40 answered benchmark queries against a seeded database — the
    differential step `docs/analysis/nopcommerce_sql_parity.md` named as its own
    limitation.
    """

    def test_sorted_listing_orders_by_a_column_not_a_direction(self):
        """`plan.sort` holds a direction; emitting it alone gave `ORDER BY desc`."""
        sql = _sql(
            IntentObject(intent_class="tabular", dimension_term="category_name",
                         metric_term="item_quantity", sort="desc", limit=7),
            "list the top 7 most frequently purchased categories",
        )
        self.assertNotIn("ORDER BY desc", sql)
        self.assertNotIn("ORDER BY asc", sql)
        if "ORDER BY" in sql:
            after = sql.split("ORDER BY", 1)[1].strip()
            self.assertRegex(after.split()[0], r"[A-Za-z_(]")

    def test_subquery_dimension_groups_by_alias_for_only_full_group_by(self):
        """MySQL 8 rejects a GROUP BY containing a correlated subquery (1055),
        so every cohort query failed at execution."""
        sql = _sql(
            IntentObject(intent_class="cohort", metric_term="avg_order_value",
                         dimension_term="customer_cohort"),
            "average order value for first-time versus returning customers",
        )
        self.assertIn("GROUP BY label", sql)

    def test_ratio_metric_is_not_unwrapped_into_unbalanced_sql(self):
        """The greedy aggregate-stripper matched the first `SUM(` against the
        last `)`, splicing an unbalanced fragment into SELECT and WHERE."""
        from aegis.server.semantic_layer import METRICS
        ratio = next(m for m in METRICS if m.id == "discount_rate")
        self.assertIsNone(SQLCompiler._strip_aggregate(ratio.sql_expr))
        # A genuinely simple aggregate must still unwrap.
        simple = next(m for m in METRICS if m.id == "item_quantity")
        self.assertEqual(SQLCompiler._strip_aggregate(simple.sql_expr),
                         "COALESCE(oi.Quantity, 0)")

    def test_aggregate_only_metric_cannot_be_a_row_filter(self):
        """A rate is a quotient of two aggregates and belongs in HAVING. The
        old `or "o.Id"` fallback turned it into a filter on the order id."""
        with self.assertRaises(UnknownFilterFieldError):
            SQLCompiler()._build_single_filter(
                Filter(field="discount_rate", operator=">", value=30)
            )

    def test_missing_metric_does_not_become_revenue(self):
        """The compiler defaulted to METRICS[0], so a plan with no measure
        compiled into a revenue query the requester never asked for — the same
        silent substitution the resolver had already removed."""
        from aegis.server.compiler import UnresolvedMetricError
        from aegis.server.models import AnalysisPlan

        # The resolver now declines this class of request before it reaches the
        # compiler, so the guard is exercised directly: it is the backstop for
        # any future path that lets an unresolved measure through.
        plan = AnalysisPlan(
            pattern="segment", metric="_none_", dimension="category_name",
            join_path=["Category"], visual="pie_chart",
        )
        with self.assertRaises(UnresolvedMetricError):
            SQLCompiler().compile(plan)

    def test_summary_projects_every_measure_as_its_own_column(self):
        """The compiler emits one column per measure, so a three-measure
        request returns three numbers rather than one chosen for the user."""
        resolution = SemanticMapper().resolve(
            IntentObject(intent_class="summary", metric_term="revenue",
                         metric_terms=["revenue", "avg_order_value", "order_count"],
                         dimension_term="order_status"),
            "summarize total sales, average order value and order count by status",
        )
        sql = SQLCompiler().compile(resolution.plan)[0]
        self.assertIn("AS value", sql)
        self.assertIn("`avg_order_value`", sql)
        self.assertIn("`order_count`", sql)
        # Column order follows the request, not the semantic layer's
        # declaration order — reordering the answer's columns silently is its
        # own small dishonesty.
        self.assertLess(sql.index("`avg_order_value`"), sql.index("`order_count`"))

    def test_summary_naming_no_measure_is_declined_before_compiling(self):
        resolution = SemanticMapper().resolve(
            IntentObject(intent_class="summary", dimension_term="category_name"),
            "give me an overview of product category performance",
        )
        self.assertIsNone(resolution.plan)
        self.assertIn("at least one measure", resolution.message)




class TestFilterFieldGrounding(unittest.TestCase):
    """Filter fields go through the same grounding as every other term.

    They used to be matched against exact semantic-layer ids while metric and
    dimension *terms* were grounded, so the two halves of one vocabulary
    disagreed about what counted as approved. A model returning
    `field="quantity"` — which grounds cleanly in any other slot — reached the
    compiler and raised, and the caller saw a crash on a request the layer can
    express. Observed in CI, not in theory.
    """

    def test_a_groundable_filter_field_is_resolved_not_refused(self):
        resolution = SemanticMapper().resolve(
            IntentObject(intent_class="tabular", dimension_term="product_name",
                         filters=[Filter(field="quantity", operator="<", value=10)]),
            "products with quantity less than 10",
        )
        self.assertIsNotNone(resolution.plan)
        self.assertEqual(resolution.plan.filters[0].field, "item_quantity")

    def test_an_unbindable_filter_field_is_declined_with_a_reason(self):
        resolution = SemanticMapper().resolve(
            IntentObject(intent_class="tabular", dimension_term="product_name",
                         filters=[Filter(field="sentiment_score", operator=">", value=3)]),
            "products with sentiment score above 3",
        )
        self.assertIsNone(resolution.plan)
        self.assertIn("sentiment_score", resolution.message)

    def test_APPROVED_PREDICATES_survive_grounding_untouched(self):
        """The reserved predicate field is not a vocabulary term to resolve."""
        resolution = SemanticMapper().resolve(
            IntentObject(intent_class="tabular", dimension_term="product_name",
                         filters=[Filter(field="low stock", operator="=", value=True)]),
            "which products are low on stock",
        )
        self.assertIsNotNone(resolution.plan)
        self.assertEqual(resolution.plan.filters[0].field, PREDICATE_FIELD)




class TestItemGrainCounterparts(unittest.TestCase):
    """Money measures defined on the order, asked for per product.

    An order's profit *is* attributable to its lines — both the price and the
    cost are recorded per line — so declining "profit margin by product" was a
    configuration gap, not a limit of the design. The fan-out guard was correct
    to refuse the order-level expression; it simply had nothing correct to
    offer instead.
    """

    def _plan(self, metric, dimension):
        return SemanticMapper().resolve(
            IntentObject(intent_class="ranking", metric_term=metric,
                         dimension_term=dimension, sort="desc"),
            f"top products by {metric}",
        )

    def test_profit_and_margin_resolve_to_their_line_level_form(self):
        for metric, expected in (("profit", "line_item_profit"),
                                 ("profit_margin", "line_item_profit_margin"),
                                 ("discount_rate", "line_item_discount_rate")):
            with self.subTest(metric=metric):
                plan = self._plan(metric, "product_name").plan
                self.assertIsNotNone(plan, f"{metric} was declined")
                self.assertEqual(plan.metric, expected)

    def test_the_substituted_expression_aggregates_line_columns(self):
        sql = SQLCompiler().compile(self._plan("profit_margin", "category_name").plan)[0]
        self.assertIn("oi.PriceExclTax", sql)
        self.assertIn("oi.OriginalProductCost", sql)
        self.assertNotIn("o.OrderSubtotalExclTax", sql)

    def test_refunds_stay_declined_because_nothing_ties_them_to_a_line(self):
        """RefundedAmount is recorded on the order alone. A refund rate per
        category would have to invent the attribution, so declining is the
        correct answer — and the reason given must be the grain conflict, not
        a false claim that the vocabulary lacks the word."""
        result = self._plan("refund_rate", "category_name")
        self.assertIsNone(result.plan)
        self.assertIn("per order", result.message)


class TestPluralStemming(unittest.TestCase):
    def test_both_singular_readings_are_offered(self):
        """`_singular` returns the first matching rule, so "-es" always beat
        "-s": "rates" stemmed to "rat" and never to "rate", which is in the
        analytic vocabulary. The word was then reported as an unmapped domain
        concept and the request declined for a term the layer knows."""
        from aegis.server.coverage import _stems
        self.assertIn("rate", _stems("rates"))
        self.assertIn("sale", _stems("sales"))
        self.assertIn("price", _stems("prices"))
        # The other reading has to survive too — "boxes" really is "box".
        self.assertIn("box", _stems("boxes"))


if __name__ == "__main__":
    unittest.main()
