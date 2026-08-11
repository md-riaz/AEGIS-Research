"""
Unit tests for aegis.server.visualization.

The selector must reject encodings that are structurally valid but
semantically indefensible — a pie chart of an average, a pie chart of fifty
slices, a scatter plot with one quantitative field — and it must say why.  The
pruning trail is part of the contract, not a debugging aid: a governed
analytics system should be able to show why it drew what it drew.
"""

import unittest

from aegis.server.mapper import SemanticResolver
from aegis.server.models import IntentObject
from aegis.server.visualization import (
    MAX_CATEGORIES_FOR_CHART,
    MAX_PIE_SLICES,
    VisualizationSelector,
)


def plan_for(**intent_kwargs):
    """Resolve an intent into a plan, failing loudly if it is not answerable."""
    result = SemanticResolver().resolve(IntentObject(**intent_kwargs), "")
    if result.plan is None:
        raise AssertionError(f"fixture did not resolve: {result.message}")
    return result.plan


class TestChartValidityRules(unittest.TestCase):
    def setUp(self):
        self.selector = VisualizationSelector()

    def test_average_is_never_a_pie_chart(self):
        """Parts of an average do not sum to a whole, so slices would lie."""
        plan = plan_for(intent_class="segment", metric_term="avg_order_value",
                        dimension_term="category_name")
        spec = self.selector.select(plan, row_count=5)
        self.assertNotEqual(spec.chart_type, "pie_chart")
        self.assertTrue(any(r["chart_type"] == "pie_chart" for r in spec.rejected))

    def test_additive_metric_may_be_a_pie_chart_at_low_cardinality(self):
        plan = plan_for(intent_class="segment", metric_term="revenue",
                        dimension_term="category_name")
        spec = self.selector.select(plan, row_count=5)
        self.assertEqual(spec.chart_type, "pie_chart")
        self.assertEqual(spec.rejected, [])

    def test_high_cardinality_falls_back_to_a_table(self):
        plan = plan_for(intent_class="segment", metric_term="revenue",
                        dimension_term="product_name")
        spec = self.selector.select(plan, row_count=MAX_CATEGORIES_FOR_CHART + 25)
        self.assertEqual(spec.chart_type, "table")
        pruned = {r["chart_type"] for r in spec.rejected}
        self.assertIn("pie_chart", pruned)
        self.assertIn("bar_chart", pruned)

    def test_too_many_pie_slices_becomes_a_bar_chart(self):
        plan = plan_for(intent_class="segment", metric_term="revenue",
                        dimension_term="category_name")
        spec = self.selector.select(plan, row_count=MAX_PIE_SLICES + 1)
        self.assertEqual(spec.chart_type, "bar_chart")

    def test_single_value_becomes_a_kpi_card(self):
        plan = plan_for(intent_class="segment", metric_term="revenue",
                        dimension_term="category_name")
        spec = self.selector.select(plan, row_count=1)
        self.assertEqual(spec.chart_type, "kpi_card")

    def test_scatter_requires_a_quantitative_dimension(self):
        plan = plan_for(intent_class="correlate", metric_term="revenue",
                        dimension_term="category_name")
        spec = self.selector.select(plan, row_count=12)
        self.assertNotEqual(spec.chart_type, "scatter_plot")
        self.assertTrue(any(r["chart_type"] == "scatter_plot" for r in spec.rejected))

    def test_every_rejection_carries_a_reason(self):
        plan = plan_for(intent_class="segment", metric_term="avg_order_value",
                        dimension_term="product_name")
        spec = self.selector.select(plan, row_count=50)
        self.assertTrue(spec.rejected)
        for rejection in spec.rejected:
            self.assertTrue(rejection["reason"])


class TestVegaLiteEmission(unittest.TestCase):
    def setUp(self):
        self.selector = VisualizationSelector()

    def test_temporal_dimension_is_typed_and_binned_by_grain(self):
        plan = plan_for(intent_class="trend", metric_term="revenue",
                        dimension_term="order_date", time_term="last 12 months")
        spec = self.selector.select(plan)
        encoding = spec.vega_lite["encoding"]
        self.assertEqual(encoding["x"]["type"], "temporal")
        self.assertEqual(encoding["x"]["timeUnit"], "yearmonth")
        self.assertEqual(encoding["y"]["type"], "quantitative")

    def test_nominal_dimension_is_typed_nominal(self):
        plan = plan_for(intent_class="ranking", metric_term="revenue",
                        dimension_term="product_name", limit=10, sort="desc")
        spec = self.selector.select(plan, row_count=10)
        self.assertEqual(spec.vega_lite["encoding"]["x"]["type"], "nominal")

    def test_spec_declares_a_schema_and_a_mark(self):
        plan = plan_for(intent_class="ranking", metric_term="revenue",
                        dimension_term="product_name", limit=10)
        spec = self.selector.select(plan, row_count=10)
        self.assertIn("vega-lite", spec.vega_lite["$schema"])
        self.assertTrue(spec.vega_lite["mark"])

    def test_pie_chart_uses_theta_and_colour(self):
        plan = plan_for(intent_class="segment", metric_term="revenue",
                        dimension_term="category_name")
        spec = self.selector.select(plan, row_count=5)
        self.assertIn("theta", spec.vega_lite["encoding"])
        self.assertIn("color", spec.vega_lite["encoding"])


class TestPresentation(unittest.TestCase):
    def setUp(self):
        self.selector = VisualizationSelector()

    def test_title_uses_semantic_labels_and_the_period(self):
        plan = plan_for(intent_class="kpi", metric_term="avg_order_value",
                        time_term="last month")
        spec = self.selector.select(plan, row_count=1)
        self.assertIn("Average Order Value", spec.title)
        self.assertIn("Last month", spec.title)

    def test_to_dict_preserves_the_legacy_keys(self):
        plan = plan_for(intent_class="ranking", metric_term="revenue",
                        dimension_term="product_name", limit=5)
        payload = self.selector.select(plan, row_count=5).to_dict()
        for key in ("chart_type", "title", "x_axis", "y_axis", "series_key",
                    "color_scheme", "options"):
            self.assertIn(key, payload)
        for key in ("vega_lite", "encoding_rationale", "rejected"):
            self.assertIn(key, payload)

    def test_rationale_is_always_populated(self):
        plan = plan_for(intent_class="kpi", metric_term="revenue")
        spec = self.selector.select(plan, row_count=1)
        self.assertTrue(spec.encoding_rationale)


if __name__ == "__main__":
    unittest.main()
