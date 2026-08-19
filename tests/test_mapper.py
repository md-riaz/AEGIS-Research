"""
Unit tests for aegis.server.mapper.SemanticMapper.

Covers the four-tier resolution strategy (exact ID, synonym, substring, label),
business logic filter expansion, full intent-to-plan mapping, and the
can_resolve() validation gate used by the server's validation endpoint.
"""

import unittest
from aegis.server.mapper import SemanticMapper
from aegis.server.models import IntentObject, Filter


class TestSemanticMapper(unittest.TestCase):
    def setUp(self):
        self.mapper = SemanticMapper()

    def test_resolve_id_exact_match(self):
        # Should resolve exactly
        self.assertEqual(self.mapper._resolve_id("revenue", "metric"), "revenue")
        self.assertEqual(self.mapper._resolve_id("category_name", "dimension"), "category_name")

    def test_resolve_id_label_match(self):
        # "Total Revenue" -> "revenue"
        self.assertEqual(self.mapper._resolve_id("total revenue", "metric"), "revenue")

    def test_resolve_id_fuzzy_match(self):
        # Substring match: "gross revenue" contains "revenue" or vice versa
        self.assertEqual(self.mapper._resolve_id("gross revenue", "metric"), "revenue")

    def test_resolve_id_unknown(self):
        self.assertEqual(self.mapper._resolve_id("unknown_metric_xyz", "metric"), "unknown")

    def test_apply_business_logic_filters(self):
        # "cancelled" is a predefined business logic term.
        # It was "abandoned" until that mapping was removed: it pointed at
        # OrderStatusId = 40, which is nopCommerce's *Cancelled*, so the
        # term returned a count of a different thing entirely.
        filters = [Filter(field="status", operator="=", value="cancelled")]
        mapped = self.mapper._apply_business_logic_filters(filters)
        
        self.assertEqual(len(mapped), 1)
        self.assertEqual(mapped[0].field, "OrderStatusId")
        self.assertEqual(mapped[0].operator, "=")
        self.assertEqual(mapped[0].value, 40)  # predefined in semantic layer

    def test_map_intent_to_plan(self):
        intent = IntentObject(
            intent_class="trend",
            metric_term="Total Revenue",
            dimension_term="Order Date",
            time_term="past 24 hours",
            filters=[Filter(field="status", operator="=", value="cancelled")],
            sort="desc",
            limit=10,
            confidence="high"
        )
        plan = self.mapper.map(intent)
        
        self.assertEqual(plan.pattern, "trend")
        self.assertEqual(plan.metric, "revenue")
        self.assertEqual(plan.dimension, "order_date")
        self.assertEqual(plan.time_rule, "past 24 hours")
        self.assertEqual(plan.sort, "desc")
        self.assertEqual(plan.limit, 10)
        # A trend defaults to a line chart.  The resolver previously said
        # "area_chart" here while visualization.INTENT_VISUAL_POLICY said
        # "line_chart" for the same pattern, so the chart a user saw depended
        # on which module answered first.  Line is the correct default: area
        # implies a part-to-whole reading that a single series does not carry.
        self.assertEqual(plan.visual, "line_chart")

        # The normalised window is what the compiler consumes; the raw phrase
        # is retained only for provenance.
        self.assertIsNotNone(plan.time_range)
        self.assertEqual(plan.time_range.canonical, "last_24_hours")

        # Verify business logic application in the mapped plan
        self.assertEqual(plan.filters[0].field, "OrderStatusId")
        self.assertEqual(plan.filters[0].value, 40)

    def test_can_resolve(self):
        self.assertTrue(SemanticMapper.can_resolve("revenue", "metric"))
        self.assertFalse(SemanticMapper.can_resolve("unresolvable_metric_123", "metric"))

if __name__ == '__main__':
    unittest.main()
