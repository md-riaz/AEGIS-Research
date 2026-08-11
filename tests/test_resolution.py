"""
End-to-end tests for aegis.server.mapper.SemanticResolver.

These run entirely offline — no LLM, no database — because the behaviour under
test is deterministic by design.

The central case is the one the architecture exists for.  Dynamic vocabulary
injection means the intent object is *always* in-vocabulary: asked about page
load times, the model must still return some approved metric id, and that id
validates.  Checking the model's output therefore cannot detect an out-of-scope
request.  The resolver checks the original question instead, which is the only
place the evidence survives.
"""

import unittest

from aegis.server.mapper import (
    SemanticMapper,
    SemanticResolver,
    UnresolvedRequestError,
)
from aegis.server.models import Filter, IntentObject, Outcome


class TestAnswerablePath(unittest.TestCase):
    def setUp(self):
        self.resolver = SemanticResolver()

    def test_fully_bound_request_produces_a_plan(self):
        result = self.resolver.resolve(
            IntentObject(
                intent_class="ranking", metric_term="revenue",
                dimension_term="product_name", limit=10, sort="desc",
                time_term="last 30 days",
            ),
            "top 10 products by revenue in the last 30 days",
        )
        self.assertIs(result.outcome, Outcome.ANSWER)
        self.assertIsNotNone(result.plan)
        self.assertEqual(result.plan.metric, "revenue")
        self.assertEqual(result.plan.dimension, "product_name")
        self.assertTrue(result.plan.join_path)
        self.assertIsNotNone(result.plan.time_range)

    def test_plan_retains_binding_evidence(self):
        """Provenance must survive into the plan, or nothing can audit it."""
        result = self.resolver.resolve(
            IntentObject(intent_class="kpi", metric_term="sales", time_term="today"),
            "what were total sales today",
        )
        self.assertIs(result.outcome, Outcome.ANSWER)
        self.assertTrue(result.plan.bindings)
        metric_binding = next(b for b in result.plan.bindings if b.slot == "metric")
        self.assertEqual(metric_binding.chosen, "revenue")
        self.assertTrue(metric_binding.candidates[0].evidence)


class TestRejectionPath(unittest.TestCase):
    """Out-of-vocabulary requests must be declined, not answered."""

    def setUp(self):
        self.resolver = SemanticResolver()

    def test_out_of_scope_question_with_valid_intent_is_rejected(self):
        # The intent object is deliberately well-formed and in-vocabulary —
        # that is exactly what vocabulary injection produces for a question the
        # system cannot answer.
        result = self.resolver.resolve(
            IntentObject(intent_class="kpi", metric_term="order_count"),
            "What is our average page load time for the checkout page?",
        )
        self.assertIs(result.outcome, Outcome.REJECT)
        self.assertTrue(result.coverage.unmapped_concepts)

    def test_out_of_domain_entity_is_rejected(self):
        result = self.resolver.resolve(
            IntentObject(intent_class="ranking", metric_term="order_count",
                         dimension_term="customer_name"),
            "Which employee handled the most support tickets this week?",
        )
        self.assertIs(result.outcome, Outcome.REJECT)
        self.assertTrue(result.message)

    def test_unsupported_time_phrase_is_rejected_not_ignored(self):
        """A dropped period silently widens the answer to all of history."""
        result = self.resolver.resolve(
            IntentObject(intent_class="kpi", metric_term="revenue",
                         time_term="during peak traffic hours"),
            "what was revenue during peak traffic hours",
        )
        self.assertIs(result.outcome, Outcome.REJECT)

    def test_write_request_is_declined_as_read_only(self):
        """The refusal must name the real reason, not an incidental one.

        AEGIS structurally cannot express a write, so this request was always
        safe.  Without an explicit check it was declined merely because some
        noun in the sentence failed to bind, which tells the user the
        vocabulary is incomplete rather than that the system is read-only.
        """
        result = self.resolver.resolve(
            IntentObject(intent_class="kpi", metric_term="order_count"),
            "Cancel all orders stuck in Pending for more than 30 days",
        )
        self.assertIs(result.outcome, Outcome.REJECT)
        self.assertTrue(result.coverage.write_request)
        self.assertIn("read-only", result.message)

    def test_a_status_named_cancelled_is_not_a_write_request(self):
        """"Cancel" as a data value must not trip the write detector."""
        result = self.resolver.resolve(
            IntentObject(intent_class="tabular", dimension_term="order_status",
                         time_term="this month"),
            "Show orders with a cancelled status this month",
        )
        self.assertFalse(result.coverage.write_request)
        self.assertIs(result.outcome, Outcome.ANSWER)

    def test_pattern_requiring_a_dimension_is_rejected_without_one(self):
        result = self.resolver.resolve(
            IntentObject(intent_class="ranking", metric_term="revenue"),
            "rank them by revenue",
        )
        self.assertIs(result.outcome, Outcome.REJECT)


class TestClarificationPath(unittest.TestCase):
    def setUp(self):
        self.resolver = SemanticResolver()

    def test_ambiguous_term_asks_a_concrete_question(self):
        result = self.resolver.resolve(
            IntentObject(intent_class="kpi", metric_term="refund", time_term="today"),
            "how many refunds today",
        )
        self.assertIs(result.outcome, Outcome.CLARIFY)
        self.assertTrue(result.question)
        self.assertGreater(len(result.options), 1)

    def test_compound_request_offers_to_split(self):
        """A widget holds one result shape, so two reports need two widgets."""
        result = self.resolver.resolve(
            IntentObject(intent_class="trend", metric_term="revenue",
                         dimension_term="order_month"),
            "Show revenue trend by month and also rank the top 5 customers by spending.",
        )
        self.assertIs(result.outcome, Outcome.CLARIFY)
        self.assertTrue(result.question)


class TestRemovedSilentFallbacks(unittest.TestCase):
    """Regression tests for each substitution the resolver used to make."""

    def setUp(self):
        self.resolver = SemanticResolver()

    def test_unresolvable_metric_does_not_become_revenue(self):
        """Old behaviour: `if metric_id == "unknown": metric_id = "revenue"`."""
        result = self.resolver.resolve(
            IntentObject(intent_class="kpi", metric_term="bounce rate"),
            "what is our bounce rate",
        )
        self.assertIsNot(result.outcome, Outcome.ANSWER)
        if result.plan is not None:
            self.assertNotEqual(result.plan.metric, "revenue")

    def test_unresolvable_dimension_is_not_silently_dropped(self):
        """Old behaviour: an unknown dimension became None, changing the question."""
        result = self.resolver.resolve(
            IntentObject(intent_class="segment", metric_term="revenue",
                         dimension_term="marketing_channel"),
            "revenue by marketing channel",
        )
        self.assertIsNot(result.outcome, Outcome.ANSWER)

    def test_absent_metric_does_not_default_to_order_count(self):
        """Old behaviour: IntentObject.metric_term defaulted to "order_count"."""
        intent = IntentObject(intent_class="kpi")
        self.assertIsNone(intent.metric_term)
        result = self.resolver.resolve(intent, "how is the business doing overall?")
        self.assertIsNot(result.outcome, Outcome.ANSWER)


class TestLegacySurface(unittest.TestCase):
    def setUp(self):
        self.resolver = SemanticResolver()

    def test_map_raises_rather_than_inventing_a_plan(self):
        with self.assertRaises(UnresolvedRequestError) as ctx:
            self.resolver.map(
                IntentObject(intent_class="kpi", metric_term="order_count"),
                "What is our average page load time for the checkout page?",
            )
        self.assertIsNot(ctx.exception.result.outcome, Outcome.ANSWER)

    def test_map_still_returns_a_plan_for_answerable_requests(self):
        plan = self.resolver.map(
            IntentObject(intent_class="segment", metric_term="revenue",
                         dimension_term="category_name"),
            "revenue by category",
        )
        self.assertEqual(plan.metric, "revenue")

    def test_can_resolve_rejects_ambiguous_and_unknown_terms(self):
        self.assertTrue(SemanticMapper.can_resolve("revenue", "metric"))
        self.assertFalse(SemanticMapper.can_resolve("refund", "metric"))
        self.assertFalse(SemanticMapper.can_resolve("bounce rate", "metric"))

    def test_business_logic_filters_still_expand(self):
        plan = self.resolver.map(
            IntentObject(
                intent_class="segment", metric_term="order_count",
                dimension_term="order_status",
                filters=[Filter(field="status", operator="=", value="abandoned")],
            ),
            "abandoned orders by status",
        )
        self.assertEqual(plan.filters[0].field, "OrderStatusId")
        self.assertEqual(plan.filters[0].value, 40)


if __name__ == "__main__":
    unittest.main()
