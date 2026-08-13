"""
Unit tests for aegis.server.grounding.

The engine returns ranked candidates plus one of RESOLVED / AMBIGUOUS /
UNSUPPORTED / ABSENT.  It must never silently substitute a binding, because a
substituted binding is indistinguishable from a correct one at every later
stage of the pipeline.
"""

import unittest

from aegis.server.grounding import ACCEPT_FLOOR, GroundingEngine
from aegis.server.models import MatchKind, Resolution
from aegis.server.semantic_layer import DIMENSIONS, METRICS


class TestExactMatches(unittest.TestCase):
    def setUp(self):
        self.engine = GroundingEngine()

    def test_canonical_id_resolves(self):
        binding = self.engine.ground("revenue", "metric")
        self.assertIs(binding.resolution, Resolution.RESOLVED)
        self.assertEqual(binding.chosen, "revenue")

    def test_human_label_resolves(self):
        binding = self.engine.ground("Total Revenue", "metric")
        self.assertIs(binding.resolution, Resolution.RESOLVED)
        self.assertEqual(binding.chosen, "revenue")

    def test_declared_alias_resolves(self):
        """Aliases live on the object's own description, not a side registry."""
        binding = self.engine.ground("sales", "metric")
        self.assertIs(binding.resolution, Resolution.RESOLVED)
        self.assertEqual(binding.chosen, "revenue")
        self.assertIs(binding.candidates[0].match_kind, MatchKind.ALIAS)


class TestContainment(unittest.TestCase):
    def setUp(self):
        self.engine = GroundingEngine()

    def test_term_contained_in_compound_id_resolves(self):
        for term, slot, expected in (
            ("country", "dimension", "country_name"),
            ("quantity", "metric", "item_quantity"),
        ):
            with self.subTest(term=term):
                binding = self.engine.ground(term, slot)
                self.assertIs(binding.resolution, Resolution.RESOLVED)
                self.assertEqual(binding.chosen, expected)


class TestAmbiguity(unittest.TestCase):
    """Genuine ambiguity must be reported, never guessed."""

    def setUp(self):
        self.engine = GroundingEngine()

    def test_refund_is_ambiguous_between_count_and_amount(self):
        binding = self.engine.ground("refund", "metric")
        self.assertIs(binding.resolution, Resolution.AMBIGUOUS)
        self.assertIsNone(binding.chosen)
        self.assertGreater(len(binding.candidates), 1)
        # Assert the pair is present rather than pinning the exact set: the
        # vocabulary is meant to grow, and a test that breaks whenever a metric
        # is added tests the semantic layer's size rather than the behaviour.
        self.assertLessEqual(
            {"refund_count", "refund_amount"},
            {c.id for c in binding.candidates},
        )

    def test_bare_name_is_ambiguous_across_name_dimensions(self):
        binding = self.engine.ground("name", "dimension")
        self.assertIs(binding.resolution, Resolution.AMBIGUOUS)
        self.assertIsNone(binding.chosen)
        self.assertGreater(len(binding.candidates), 1)


class TestUnsupported(unittest.TestCase):
    def setUp(self):
        self.engine = GroundingEngine()

    def test_out_of_vocabulary_terms_do_not_resolve(self):
        for term in ("bounce rate", "sentiment", "page load time"):
            with self.subTest(term=term):
                binding = self.engine.ground(term, "metric")
                self.assertIs(binding.resolution, Resolution.UNSUPPORTED)
                self.assertIsNone(binding.chosen)
                self.assertTrue(binding.reason)

    def test_missing_term_is_absent_not_unsupported(self):
        """"Not asked for" and "cannot be expressed" are different outcomes."""
        for term in (None, "", "   "):
            with self.subTest(term=term):
                binding = self.engine.ground(term, "metric")
                self.assertIs(binding.resolution, Resolution.ABSENT)


class TestOrderIndependence(unittest.TestCase):
    """Regression test for the original first-match-wins resolver.

    The previous implementation returned the first object whose id or
    description contained the term, so reordering the semantic layer silently
    changed which metric a query measured.  Resolution must depend only on the
    evidence, never on declaration order.
    """

    def test_reversing_the_vocabulary_does_not_change_resolution(self):
        default = GroundingEngine()
        reversed_engine = GroundingEngine(
            metrics=list(reversed(METRICS)),
            dimensions=list(reversed(DIMENSIONS)),
        )
        for term, slot in (
            ("revenue", "metric"), ("sales", "metric"), ("country", "dimension"),
            ("product_name", "dimension"), ("quantity", "metric"),
        ):
            with self.subTest(term=term):
                self.assertEqual(
                    default.ground(term, slot).chosen,
                    reversed_engine.ground(term, slot).chosen,
                )

    def test_ambiguity_verdict_is_also_order_independent(self):
        default = GroundingEngine()
        reversed_engine = GroundingEngine(
            metrics=list(reversed(METRICS)),
            dimensions=list(reversed(DIMENSIONS)),
        )
        self.assertIs(default.ground("refund", "metric").resolution,
                      reversed_engine.ground("refund", "metric").resolution)


class TestScoringInvariants(unittest.TestCase):
    def setUp(self):
        self.engine = GroundingEngine()

    def test_description_overlap_can_never_win_outright(self):
        """Weak evidence may suggest an alternative but must not decide."""
        for slot in ("metric", "dimension"):
            objects = METRICS if slot == "metric" else DIMENSIONS
            for obj in objects:
                for candidate in self.engine.candidates(obj.description[:12], slot):
                    if candidate.match_kind is MatchKind.DESCRIPTION_OVERLAP:
                        self.assertLess(candidate.score, ACCEPT_FLOOR)

    def test_candidates_carry_evidence_and_bounded_scores(self):
        for term, slot in (("revenue", "metric"), ("refund", "metric"),
                           ("country", "dimension")):
            for candidate in self.engine.candidates(term, slot):
                with self.subTest(term=term, candidate=candidate.id):
                    self.assertTrue(candidate.evidence)
                    self.assertGreaterEqual(candidate.score, 0.0)
                    self.assertLessEqual(candidate.score, 1.0)

    def test_candidates_are_ranked_best_first(self):
        candidates = self.engine.candidates("revenue", "metric")
        scores = [c.score for c in candidates]
        self.assertEqual(scores, sorted(scores, reverse=True))


class TestVocabularyIntrospection(unittest.TestCase):
    def test_vocabulary_lists_approved_ids(self):
        engine = GroundingEngine()
        self.assertIn("revenue", engine.vocabulary("metric"))
        self.assertIn("product_name", engine.vocabulary("dimension"))

    def test_unknown_slot_is_rejected(self):
        with self.assertRaises(ValueError):
            GroundingEngine().ground("revenue", "not_a_slot")


if __name__ == "__main__":
    unittest.main()
