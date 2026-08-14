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

from aegis.server.compiler import SQLCompiler, UnknownFilterFieldError
from aegis.server.mapper import SemanticMapper
from aegis.server.models import Filter, IntentObject
from aegis.server.semantic_layer import GOVERNED_PREDICATES, PREDICATE_FIELD


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


class TestGovernedPredicates(unittest.TestCase):
    """Concepts the platform names as first-class reports but which cannot be
    written as `field operator value`, because the comparison is between two
    columns rather than against a user-supplied threshold."""

    def test_low_stock_compares_each_product_to_its_own_minimum(self):
        sql = SQLCompiler()._build_single_filter(
            Filter(field=PREDICATE_FIELD, operator="=", value="low_stock")
        )[0]
        self.assertIn("p.StockQuantity <= p.MinStockQuantity", sql)
        self.assertIn("p.ManageInventoryMethodId = 1", sql)
        self.assertIn("p.ProductTypeId <> 10", sql)

    def test_predicate_value_is_a_key_never_sql(self):
        """The filter carries an id; the SQL lives in the semantic layer. A
        request can select a fragment but cannot author or extend one."""
        for entry in GOVERNED_PREDICATES.values():
            self.assertNotIn(";", entry["sql"])

    def test_unknown_predicate_key_is_refused(self):
        with self.assertRaises(Exception):
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


if __name__ == "__main__":
    unittest.main()
