"""
Regression tests for temporal handling in aegis.server.compiler.

Caught by the live-query suite: "Monthly revenue trend" resolved cleanly, then
crashed the compiler with TimeResolutionError. `time_rule` was the truthy
string "monthly" while `time_range` was None, and the compiler treated any
unresolvable phrase as an error — including a granularity, which carries no
filtering intent at all.

The server reported that crash with the default outcome "answer", so the suite
recorded it as a passing query. Both halves are pinned here and in
tests/test_query.py.
"""

import unittest

from aegis.server.compiler import SQLCompiler, TimeResolutionError
from aegis.server.mapper import SemanticResolver
from aegis.server.models import IntentObject


class TestGrainDoesNotCrashTheCompiler(unittest.TestCase):
    def setUp(self):
        self.resolver = SemanticResolver()
        self.compiler = SQLCompiler()

    def _plan(self, time_term):
        result = self.resolver.resolve(
            IntentObject(intent_class="trend", metric_term="revenue",
                         dimension_term="order_date", time_term=time_term),
            "revenue trend",
        )
        self.assertIsNotNone(result.plan, f"{time_term!r} did not resolve")
        return result.plan

    def test_granularity_compiles_without_a_time_predicate(self):
        for phrase in ("monthly", "daily", "weekly", "quarterly"):
            with self.subTest(phrase=phrase):
                sql, _, _ = self.compiler.compile(self._plan(phrase))
                self.assertNotIn("CreatedOnUtc >=", sql)

    def test_a_real_window_still_emits_a_predicate(self):
        sql, _, _ = self.compiler.compile(self._plan("last month"))
        self.assertIn("CreatedOnUtc >=", sql)

    def test_no_period_emits_no_predicate(self):
        sql, _, _ = self.compiler.compile(self._plan(None))
        self.assertNotIn("CreatedOnUtc >=", sql)

    def test_an_unsupported_phrase_still_refuses(self):
        """Only UNSUPPORTED is an error — the dropped-filter guard must hold."""
        plan = self._plan("last month")
        plan.time_range = None
        plan.time_rule = "whenever sales spiked"
        with self.assertRaises(TimeResolutionError):
            self.compiler.compile(plan)


if __name__ == "__main__":
    unittest.main()
