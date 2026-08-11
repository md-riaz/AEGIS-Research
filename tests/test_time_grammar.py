"""
Unit tests for aegis.server.time_grammar.

The module under test is a *total* normaliser: every input maps to exactly one
of RESOLVED, UNSUPPORTED, or NONE.  The property these tests exist to protect
is that a temporal constraint can never be silently discarded — the previous
matcher returned ``None`` for unrecognised phrases and every caller treated
that as "no filter needed", so "this morning", "this quarter" and
"last 90 days" produced queries that ran over all of history and returned a
confident wrong number.
"""

import unittest

from aegis.server import time_grammar
from aegis.server.time_grammar import TimeStatus, normalise, supported_expressions


class TestRegressionPhrases(unittest.TestCase):
    """The three phrases that used to vanish from the WHERE clause entirely."""

    def test_previously_dropped_phrases_now_resolve(self):
        for phrase in ("this morning", "this quarter", "last 90 days"):
            with self.subTest(phrase=phrase):
                result = normalise(phrase)
                self.assertIs(result.status, TimeStatus.RESOLVED)
                self.assertIsNotNone(result.range)
                self.assertTrue(result.range.start_sql)


class TestNamedWindows(unittest.TestCase):
    def test_named_day_windows(self):
        for phrase in ("today", "yesterday"):
            with self.subTest(phrase=phrase):
                self.assertIs(normalise(phrase).status, TimeStatus.RESOLVED)

    def test_named_period_windows(self):
        phrases = [
            "this week", "last week", "this month", "last month",
            "this quarter", "last quarter", "this year", "last year",
        ]
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                result = normalise(phrase)
                self.assertIs(result.status, TimeStatus.RESOLVED)
                # A bounded named period must be two-sided, otherwise "last
                # month" would silently include the current month too.
                self.assertIsNotNone(result.range.end_sql)

    def test_to_date_windows_are_open_ended(self):
        for phrase in ("week to date", "month to date", "year to date"):
            with self.subTest(phrase=phrase):
                result = normalise(phrase)
                self.assertIs(result.status, TimeStatus.RESOLVED)
                self.assertIsNone(result.range.end_sql)


class TestRelativeWindows(unittest.TestCase):
    def test_last_n_units(self):
        for phrase, canonical in (
            ("last 7 days", "last_7_days"),
            ("past 24 hours", "last_24_hours"),
            ("trailing 12 months", "last_12_months"),
        ):
            with self.subTest(phrase=phrase):
                result = normalise(phrase)
                self.assertIs(result.status, TimeStatus.RESOLVED)
                self.assertEqual(result.range.canonical, canonical)

    def test_n_units_ago_is_a_single_period_not_a_rolling_window(self):
        result = normalise("3 days ago")
        self.assertIs(result.status, TimeStatus.RESOLVED)
        self.assertIsNotNone(result.range.end_sql)

    def test_zero_length_window_is_rejected(self):
        self.assertIs(normalise("last 0 days").status, TimeStatus.UNSUPPORTED)


class TestAbsoluteWindows(unittest.TestCase):
    def test_year(self):
        result = normalise("2023")
        self.assertIs(result.status, TimeStatus.RESOLVED)
        self.assertEqual(result.range.canonical, "year_2023")

    def test_quarter_of_year(self):
        result = normalise("Q2 2023")
        self.assertIs(result.status, TimeStatus.RESOLVED)
        self.assertEqual(result.range.canonical, "q2_2023")

    def test_month_of_year(self):
        result = normalise("March 2024")
        self.assertIs(result.status, TimeStatus.RESOLVED)
        self.assertEqual(result.range.canonical, "2024_03")


class TestNormalisation(unittest.TestCase):
    def test_surface_variants_share_one_canonical_form(self):
        """Widget de-duplication depends on equivalent phrasings colliding."""
        variants = ["last month", "Last Month", "last_month", "last-month",
                    "  LAST   MONTH  ", "previous month"]
        canonicals = {normalise(v).range.canonical for v in variants}
        self.assertEqual(canonicals, {"last_month"})

    def test_absence_of_a_period_is_not_a_failure(self):
        for phrase in (None, "", "all time", "overall"):
            with self.subTest(phrase=phrase):
                self.assertIs(normalise(phrase).status, TimeStatus.NONE)


class TestUnsupported(unittest.TestCase):
    def test_unmodellable_phrases_report_a_reason(self):
        for phrase in ("peak traffic hours", "since the site redesign",
                       "whenever sales spiked"):
            with self.subTest(phrase=phrase):
                result = normalise(phrase)
                self.assertIs(result.status, TimeStatus.UNSUPPORTED)
                self.assertTrue(result.reason)
                self.assertIsNone(result.range)


class TestFiscalCalendar(unittest.TestCase):
    """Fiscal phrases must abstain until a fiscal calendar is configured.

    Reinterpreting "previous fiscal year" as a calendar year shifts every
    boundary in the result, so guessing is materially worse than declining.
    """

    def setUp(self):
        self._original = time_grammar.FISCAL_YEAR_START_MONTH

    def tearDown(self):
        time_grammar.FISCAL_YEAR_START_MONTH = self._original

    def test_unconfigured_fiscal_year_abstains(self):
        time_grammar.FISCAL_YEAR_START_MONTH = None
        result = normalise("previous fiscal year")
        self.assertIs(result.status, TimeStatus.UNSUPPORTED)
        self.assertIn("fiscal calendar", result.reason.lower())

    def test_configured_fiscal_year_resolves(self):
        time_grammar.FISCAL_YEAR_START_MONTH = 4
        result = normalise("previous fiscal year")
        self.assertIs(result.status, TimeStatus.RESOLVED)
        self.assertIsNotNone(result.range)


class TestPredicateRendering(unittest.TestCase):
    def test_bounded_window_renders_two_sided_predicate(self):
        predicate = normalise("last month").range.to_predicate("o.CreatedOnUtc")
        self.assertIn("o.CreatedOnUtc", predicate)
        self.assertIn(">=", predicate)
        self.assertIn("<", predicate)

    def test_open_window_renders_lower_bound_only(self):
        predicate = normalise("last 30 days").range.to_predicate("o.CreatedOnUtc")
        self.assertIn(">=", predicate)
        self.assertNotIn("<", predicate)


class TestDocumentedVocabulary(unittest.TestCase):
    def test_every_documented_concrete_phrase_resolves(self):
        """The advertised vocabulary must not contain phrases we then reject."""
        for phrase in supported_expressions():
            if "N " in phrase or "<" in phrase or ".." in phrase:
                continue  # templated description, not a concrete phrase
            with self.subTest(phrase=phrase):
                self.assertIsNot(
                    normalise(phrase).status, TimeStatus.UNSUPPORTED,
                    f"documented phrase {phrase!r} was rejected",
                )


if __name__ == "__main__":
    unittest.main()
