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
from aegis.server.compiler import SQLCompiler
from aegis.server.explain import explain_plan
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
        # Revenue per *product* is measured on the line item: an order total
        # cannot be attributed to one of the order's lines without counting the
        # order once per line. See TestGrainGuard below.
        self.assertEqual(result.plan.metric, "line_item_revenue")
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


class TestNoFalseAbstention(unittest.TestCase):
    """Answerable requests must not be declined over incidental wording.

    Abstention is only useful if it is precise.  A system that refuses
    supported requests because of a negation adverb or a rank noun trades one
    failure mode for another, so each of these phrasings is pinned.
    """

    def setUp(self):
        self.resolver = SemanticResolver()

    def test_negation_does_not_trigger_a_coverage_gap(self):
        result = self.resolver.resolve(
            IntentObject(intent_class="tabular", metric_term="item_quantity",
                         dimension_term="product_name",
                         filters=[Filter(field="item_quantity", operator="=", value=0)]),
            "List products never sold",
        )
        self.assertFalse(result.coverage.unmapped_concepts)

    def test_rank_nouns_do_not_trigger_a_coverage_gap(self):
        result = self.resolver.resolve(
            IntentObject(intent_class="ranking", metric_term="item_quantity",
                         dimension_term="product_name", limit=5, sort="desc"),
            "Top 5 bestsellers by quantity",
        )
        self.assertFalse(result.coverage.unmapped_concepts)
        self.assertIs(result.outcome, Outcome.ANSWER)

    def test_transactional_verbs_do_not_trigger_a_coverage_gap(self):
        for question in (
            "Which 5 categories made the most sales last month?",
            "How many orders were placed yesterday?",
            "What was the total revenue generated today?",
        ):
            with self.subTest(question=question):
                result = self.resolver.resolve(
                    IntentObject(intent_class="kpi", metric_term="revenue",
                                 time_term="today"),
                    question,
                )
                self.assertFalse(result.coverage.unmapped_concepts)


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
        self.assertEqual(plan.metric, "line_item_revenue")

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




class TestTemporalIntentClassification(unittest.TestCase):
    """A granularity must not be treated as an unrecognised filter.

    Caught by the integration suite the first time it genuinely ran: "Monthly
    revenue trend" came back REJECT with "unrecognised time expression
    'monthly'". The phrase specifies bucketing, not filtering.
    """

    def setUp(self):
        self.resolver = SemanticResolver()

    def test_granularity_answers_and_carries_a_grain(self):
        result = self.resolver.resolve(
            IntentObject(intent_class="trend", metric_term="revenue",
                         dimension_term="order_date", time_term="monthly"),
            "Monthly revenue trend",
        )
        self.assertIs(result.outcome, Outcome.ANSWER)
        self.assertEqual(result.plan.time_grain, "month")
        self.assertIsNone(result.plan.time_range)

    def test_vague_period_clarifies_rather_than_rejecting(self):
        result = self.resolver.resolve(
            IntentObject(intent_class="tabular", dimension_term="tracking_number",
                         time_term="recent"),
            "List recent shipments with tracking details",
        )
        self.assertIs(result.outcome, Outcome.CLARIFY)
        self.assertTrue(result.question)

    def test_a_real_window_still_filters(self):
        result = self.resolver.resolve(
            IntentObject(intent_class="trend", metric_term="revenue",
                         dimension_term="order_date", time_term="last month"),
            "revenue trend last month",
        )
        self.assertIs(result.outcome, Outcome.ANSWER)
        self.assertIsNotNone(result.plan.time_range)


class TestFalseAbstentionFixes(unittest.TestCase):
    """Regressions for requests the system wrongly refused.

    Each was found by running the live pipeline over the benchmark and
    inspecting what it declined. Abstention is only useful if it is precise;
    these pin the cases where refusing was the wrong answer.
    """

    def setUp(self):
        self.resolver = SemanticResolver()

    def test_model_reported_unmapped_terms_are_filtered(self):
        """The extractor's report is evidence, not a verdict.

        Asked for unmapped terms, the model over-reports: "daily", "average",
        "past 60 days" and "generated" are all named, because none is a metric
        or dimension. Taking that at face value was the largest single source
        of wrongly refused requests.
        """
        result = self.resolver.resolve(
            IntentObject(
                intent_class="trend", metric_term="revenue",
                dimension_term="order_date", time_term="last 30 days",
                unmapped_terms=["daily", "generated", "past 60 days", "average"],
            ),
            "Show the daily revenue generated over the past 60 days",
        )
        self.assertIs(result.outcome, Outcome.ANSWER)
        self.assertFalse(result.coverage.unmapped_concepts)

    def test_a_genuine_gap_reported_by_the_model_still_counts(self):
        result = self.resolver.resolve(
            IntentObject(intent_class="kpi", metric_term="order_count",
                         unmapped_terms=["support tickets"]),
            "how many support tickets were raised",
        )
        self.assertIs(result.outcome, Outcome.REJECT)

    def test_qualifiers_do_not_block_the_answer(self):
        """"net revenue" is expressible; only its definition differs."""
        result = self.resolver.resolve(
            IntentObject(intent_class="kpi", metric_term="revenue",
                         time_term="today"),
            "What is the net revenue after discounts for today?",
        )
        self.assertIs(result.outcome, Outcome.ANSWER)

    def test_summary_does_not_require_a_single_metric(self):
        """A summary is a multi-metric overview by definition."""
        result = self.resolver.resolve(
            IntentObject(intent_class="summary", dimension_term="category_name"),
            "Summarize total sales, average order value and order count by category",
        )
        self.assertIs(result.outcome, Outcome.ANSWER)

    def test_a_dimension_in_the_metric_slot_is_refiled(self):
        """The term is approved; only its slot was wrong.

        The request is still declined afterwards, but for an honest reason:
        ranking by a raw numeric attribute is not an aggregation, and the
        pattern needs a metric. What must not happen is refusing because
        "no approved metric corresponds to 'product_rating'" — the term *is*
        approved, and reporting it as unknown misdescribes the limitation.
        """
        result = self.resolver.resolve(
            IntentObject(intent_class="ranking", metric_term="product_rating",
                         limit=10, sort="desc"),
            "products with the highest rating",
        )
        self.assertNotIn("no approved metric", result.message or "")

        metric = next(b for b in result.bindings if b.slot == "metric")
        dimension = next(b for b in result.bindings if b.slot == "dimension")
        self.assertEqual(dimension.chosen, "product_rating")
        self.assertIsNone(metric.chosen)


class TestGrainGuard(unittest.TestCase):
    """An order-level aggregate must not be fanned out by an item-level join.

    `SUM(o.OrderTotal)` grouped by category — joined Order → OrderItem →
    Product → Category — adds each order's whole total once per matching line.
    An order with three items in one category contributes three times.  The
    result is ordered, chartable and plausibly sized, with nothing in it that
    could tell a reader it is wrong, which is what makes this worth a guard
    rather than a note in the documentation.

    Verified against the host platform's own implementation: nopCommerce's
    bestsellers report aggregates `g.Sum(x => x.PriceExclTax)` over order
    items, not order totals (OrderReportService.BestSellersReportAsync).
    """

    def setUp(self):
        self.resolver = SemanticMapper()

    def _plan(self, dimension):
        return self.resolver.resolve(
            IntentObject(intent_class="segment", metric_term="revenue",
                         dimension_term=dimension),
            f"revenue by {dimension}",
        ).plan

    def test_item_level_breakdowns_use_the_item_level_measure(self):
        for dimension in ("product_name", "category_name", "manufacturer_name"):
            with self.subTest(dimension=dimension):
                self.assertEqual(self._plan(dimension).metric, "line_item_revenue")

    def test_order_level_breakdowns_keep_the_order_level_measure(self):
        """The guard must not fire where there is no fan-out to prevent."""
        for dimension in ("country_name", "order_status"):
            with self.subTest(dimension=dimension):
                self.assertEqual(self._plan(dimension).metric, "revenue")

    def test_substitution_is_stated_in_the_plan(self):
        """A governed definition the user cannot see is indistinguishable from
        a guess, which is the thing this pipeline exists to rule out."""
        plan = self._plan("category_name")
        self.assertTrue(plan.notes)
        self.assertIn("line", explain_plan(plan).lower())

    def test_compiled_sql_aggregates_the_item_column(self):
        sql, _, _ = SQLCompiler().compile(self._plan("category_name"))
        self.assertIn("oi.PriceExclTax", sql)
        self.assertNotIn("o.OrderTotal", sql)


if __name__ == "__main__":
    unittest.main()
