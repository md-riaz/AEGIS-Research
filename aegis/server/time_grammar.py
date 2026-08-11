"""
AEGIS Time Grammar — a *total* normaliser for temporal expressions.

Rationale
---------
The original pipeline translated time phrases with a best-effort matcher that
returned ``None`` for anything it did not recognise.  Every caller then did::

    time_part = self._get_smart_time_sql(field, plan.time_rule)
    if time_part:
        parts.append(time_part)

which means an unrecognised phrase ("this morning", "this quarter",
"last 90 days") did not raise and did not filter — the temporal constraint was
silently discarded and the query ran over all of history.  The user received a
confident, well-formed, wrong number.

This module removes that failure class structurally.  ``normalise()`` is a
total function over strings: every input maps to exactly one of

  * ``TimeStatus.RESOLVED``    — a canonical :class:`TimeRange` with explicit
                                 lower/upper bounds,
  * ``TimeStatus.UNSUPPORTED`` — a machine-readable reason,
  * ``TimeStatus.NONE``        — the request genuinely carries no time filter.

There is no fourth outcome, and no code path where a temporal constraint can
be dropped without a recorded decision.

Design notes
------------
* Bounds are half-open ``[start, end)``.  This makes month/quarter/year
  arithmetic exact and avoids the ``BETWEEN`` end-of-day truncation bug that
  affects naive ``CAST(x AS DATE)`` comparisons.
* All expressions are anchored on ``UTC_TIMESTAMP()`` to match the rest of the
  compiler.
* Fiscal-calendar phrases resolve only when the deployment configures
  :data:`FISCAL_YEAR_START_MONTH`.  When it is unset, the phrase is reported
  ``UNSUPPORTED`` rather than being silently reinterpreted as a calendar year —
  a wrong fiscal boundary is a materially wrong answer, not a rounding error.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional, Tuple

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Deployment configuration
# ---------------------------------------------------------------------------

#: Month (1–12) on which the organisation's fiscal year begins.  ``None`` means
#: "no fiscal calendar has been configured for this deployment", which makes
#: every fiscal phrase resolve to UNSUPPORTED instead of guessing.
FISCAL_YEAR_START_MONTH: Optional[int] = None


class TimeStatus(str, Enum):
    """Outcome of normalising a temporal expression."""

    RESOLVED = "resolved"
    UNSUPPORTED = "unsupported"
    NONE = "none"


class TimeGrain(str, Enum):
    """Granularity implied by a temporal expression."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class TimeRange(BaseModel):
    """A canonical, half-open ``[start, end)`` temporal window.

    Attributes:
        canonical: Stable identifier for the window (e.g. ``last_30_days``).
            Two phrasings that mean the same window share a canonical form,
            which is what makes widget de-duplication meaningful.
        label: Human-readable rendering used in clarification prompts and
            widget titles.
        grain: Natural granularity, used by the visualisation layer to pick a
            temporal binning.
        start_sql: MySQL expression for the inclusive lower bound.
        end_sql: MySQL expression for the exclusive upper bound, or ``None``
            for "up to now".
    """

    canonical: str
    label: str
    grain: TimeGrain
    start_sql: str
    end_sql: Optional[str] = None

    def to_predicate(self, field_expr: str) -> str:
        """Render the range as a SQL predicate over ``field_expr``."""
        lower = f"{field_expr} >= {self.start_sql}"
        if self.end_sql is None:
            return lower
        return f"({lower} AND {field_expr} < {self.end_sql})"


class TimeResolution(BaseModel):
    """Result of :func:`normalise` — always one of three explicit outcomes."""

    status: TimeStatus
    range: Optional[TimeRange] = None
    reason: Optional[str] = None
    raw: Optional[str] = None

    @property
    def is_resolved(self) -> bool:
        return self.status is TimeStatus.RESOLVED


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

_NOW = "UTC_TIMESTAMP()"
_TODAY = f"CAST({_NOW} AS DATE)"

#: Start of the ISO week (Monday) containing today.
_WEEK_START = f"DATE_SUB({_TODAY}, INTERVAL WEEKDAY({_NOW}) DAY)"
#: First day of the current calendar month.
_MONTH_START = f"DATE_FORMAT({_NOW}, '%Y-%m-01')"
#: First day of the current calendar quarter.
_QUARTER_START = (
    f"MAKEDATE(YEAR({_NOW}), 1) "
    f"+ INTERVAL (QUARTER({_NOW}) - 1) QUARTER"
)
#: First day of the current calendar year.
_YEAR_START = f"MAKEDATE(YEAR({_NOW}), 1)"

_UNIT_ALIASES = {
    "hour": "HOUR", "hours": "HOUR", "hr": "HOUR", "hrs": "HOUR",
    "day": "DAY", "days": "DAY",
    "week": "WEEK", "weeks": "WEEK",
    "month": "MONTH", "months": "MONTH",
    "quarter": "QUARTER", "quarters": "QUARTER",
    "year": "YEAR", "years": "YEAR",
}

_UNIT_GRAIN = {
    "HOUR": TimeGrain.HOUR,
    "DAY": TimeGrain.DAY,
    "WEEK": TimeGrain.WEEK,
    "MONTH": TimeGrain.MONTH,
    "QUARTER": TimeGrain.QUARTER,
    "YEAR": TimeGrain.YEAR,
}

_MONTH_NAMES = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

#: Phrases that explicitly mean "no temporal restriction".
_ALL_TIME = {
    "", "all", "all time", "alltime", "any", "any time", "anytime",
    "ever", "lifetime", "overall", "to date", "none", "null",
}


def _fixed_window(
    canonical: str,
    label: str,
    grain: TimeGrain,
    start_sql: str,
    end_sql: Optional[str] = None,
) -> TimeResolution:
    return TimeResolution(
        status=TimeStatus.RESOLVED,
        range=TimeRange(
            canonical=canonical,
            label=label,
            grain=grain,
            start_sql=start_sql,
            end_sql=end_sql,
        ),
    )


def _unsupported(raw: str, reason: str) -> TimeResolution:
    return TimeResolution(status=TimeStatus.UNSUPPORTED, reason=reason, raw=raw)


# ---------------------------------------------------------------------------
# Named windows — exact-phrase table
# ---------------------------------------------------------------------------

def _named_windows() -> dict:
    """Build the exact-phrase lookup table.

    Kept as a function so the SQL fragments stay readable and so a deployment
    can extend the table without editing tuple literals inline.
    """
    return {
        # --- day-level -----------------------------------------------------
        "today": _fixed_window(
            "today", "Today", TimeGrain.DAY,
            _TODAY, f"{_TODAY} + INTERVAL 1 DAY",
        ),
        "yesterday": _fixed_window(
            "yesterday", "Yesterday", TimeGrain.DAY,
            f"{_TODAY} - INTERVAL 1 DAY", _TODAY,
        ),
        "day before yesterday": _fixed_window(
            "day_before_yesterday", "The day before yesterday", TimeGrain.DAY,
            f"{_TODAY} - INTERVAL 2 DAY", f"{_TODAY} - INTERVAL 1 DAY",
        ),

        # --- intra-day -----------------------------------------------------
        # These were the phrases that previously vanished from the WHERE clause.
        "this morning": _fixed_window(
            "this_morning", "This morning (00:00–12:00)", TimeGrain.HOUR,
            _TODAY, f"{_TODAY} + INTERVAL 12 HOUR",
        ),
        "this afternoon": _fixed_window(
            "this_afternoon", "This afternoon (12:00–17:00)", TimeGrain.HOUR,
            f"{_TODAY} + INTERVAL 12 HOUR", f"{_TODAY} + INTERVAL 17 HOUR",
        ),
        "this evening": _fixed_window(
            "this_evening", "This evening (17:00–24:00)", TimeGrain.HOUR,
            f"{_TODAY} + INTERVAL 17 HOUR", f"{_TODAY} + INTERVAL 1 DAY",
        ),
        "tonight": _fixed_window(
            "this_evening", "This evening (17:00–24:00)", TimeGrain.HOUR,
            f"{_TODAY} + INTERVAL 17 HOUR", f"{_TODAY} + INTERVAL 1 DAY",
        ),
        "last night": _fixed_window(
            "last_night", "Last night (17:00–24:00 yesterday)", TimeGrain.HOUR,
            f"{_TODAY} - INTERVAL 7 HOUR", _TODAY,
        ),

        # --- week ----------------------------------------------------------
        "this week": _fixed_window(
            "this_week", "This week (from Monday)", TimeGrain.WEEK,
            _WEEK_START, f"{_WEEK_START} + INTERVAL 1 WEEK",
        ),
        "last week": _fixed_window(
            "last_week", "Last week", TimeGrain.WEEK,
            f"{_WEEK_START} - INTERVAL 1 WEEK", _WEEK_START,
        ),
        "week to date": _fixed_window(
            "week_to_date", "Week to date", TimeGrain.DAY,
            _WEEK_START, None,
        ),

        # --- month ---------------------------------------------------------
        "this month": _fixed_window(
            "this_month", "This month", TimeGrain.MONTH,
            _MONTH_START, f"{_MONTH_START} + INTERVAL 1 MONTH",
        ),
        "last month": _fixed_window(
            "last_month", "Last month", TimeGrain.MONTH,
            f"{_MONTH_START} - INTERVAL 1 MONTH", _MONTH_START,
        ),
        "month to date": _fixed_window(
            "month_to_date", "Month to date", TimeGrain.DAY,
            _MONTH_START, None,
        ),

        # --- quarter -------------------------------------------------------
        "this quarter": _fixed_window(
            "this_quarter", "This quarter", TimeGrain.QUARTER,
            _QUARTER_START, f"{_QUARTER_START} + INTERVAL 1 QUARTER",
        ),
        "last quarter": _fixed_window(
            "last_quarter", "Last quarter", TimeGrain.QUARTER,
            f"{_QUARTER_START} - INTERVAL 1 QUARTER", _QUARTER_START,
        ),
        "quarter to date": _fixed_window(
            "quarter_to_date", "Quarter to date", TimeGrain.DAY,
            _QUARTER_START, None,
        ),

        # --- year ----------------------------------------------------------
        "this year": _fixed_window(
            "this_year", "This year", TimeGrain.YEAR,
            _YEAR_START, f"{_YEAR_START} + INTERVAL 1 YEAR",
        ),
        "last year": _fixed_window(
            "last_year", "Last year", TimeGrain.YEAR,
            f"{_YEAR_START} - INTERVAL 1 YEAR", _YEAR_START,
        ),
        "year to date": _fixed_window(
            "year_to_date", "Year to date", TimeGrain.MONTH,
            _YEAR_START, None,
        ),
    }


_NAMED = _named_windows()

#: Phrasings that mean the same thing as a canonical key above.
_PHRASE_ALIASES = {
    "current day": "today", "now": "today", "current": "today",
    "so far today": "today", "past 1 day": "today",
    "previous day": "yesterday",
    "current week": "this week", "past week": "this week",
    "previous week": "last week",
    "current month": "this month", "past month": "this month",
    "previous month": "last month",
    "current quarter": "this quarter", "past quarter": "this quarter",
    "previous quarter": "last quarter",
    "current year": "this year", "past year": "this year",
    "previous year": "last year",
    "wtd": "week to date", "mtd": "month to date",
    "qtd": "quarter to date", "ytd": "year to date",
}


# ---------------------------------------------------------------------------
# Pattern handlers
# ---------------------------------------------------------------------------

_RE_RELATIVE = re.compile(
    r"^(?:the\s+)?(?:last|past|previous|trailing|latest|prior)\s+"
    r"(\d+)\s+"
    r"(hour|hours|hr|hrs|day|days|week|weeks|month|months|quarter|quarters|year|years)$"
)

_RE_AGO = re.compile(
    r"^(\d+)\s+"
    r"(hour|hours|hr|hrs|day|days|week|weeks|month|months|quarter|quarters|year|years)"
    r"\s+ago$"
)

_RE_YEAR = re.compile(r"^(?:in\s+|for\s+|year\s+|fy\s*)?((?:19|20)\d{2})$")

_RE_QUARTER_YEAR = re.compile(r"^q([1-4])\s*(?:of\s+)?((?:19|20)\d{2})$")

_RE_MONTH_YEAR = re.compile(r"^([a-z]+)\s+((?:19|20)\d{2})$")

_RE_FISCAL = re.compile(r"\bfiscal\b|\bfy\b")


def _handle_relative(match: re.Match) -> TimeResolution:
    """Handle "last N <unit>" / "past N <unit>" / "trailing N <unit>"."""
    n = int(match.group(1))
    unit = _UNIT_ALIASES[match.group(2)]
    if n <= 0:
        return _unsupported(match.string, "time window must be a positive number of periods")
    grain = _UNIT_GRAIN[unit]
    # A rolling window ending now — the reading business users expect from
    # "last 90 days" (not "the 90 days before the current calendar period").
    return _fixed_window(
        canonical=f"last_{n}_{unit.lower()}s",
        label=f"Last {n} {unit.lower()}{'s' if n != 1 else ''}",
        grain=grain,
        start_sql=f"DATE_SUB({_NOW}, INTERVAL {n} {unit})",
        end_sql=None,
    )


def _handle_ago(match: re.Match) -> TimeResolution:
    """Handle "N <unit> ago" — a single period, not a rolling window."""
    n = int(match.group(1))
    unit = _UNIT_ALIASES[match.group(2)]
    if n <= 0:
        return _unsupported(match.string, "time offset must be a positive number of periods")
    grain = _UNIT_GRAIN[unit]
    return _fixed_window(
        canonical=f"{n}_{unit.lower()}s_ago",
        label=f"{n} {unit.lower()}{'s' if n != 1 else ''} ago",
        grain=grain,
        start_sql=f"DATE_SUB({_NOW}, INTERVAL {n} {unit})",
        end_sql=f"DATE_SUB({_NOW}, INTERVAL {n - 1} {unit})" if n > 1 else _NOW,
    )


def _handle_year(match: re.Match) -> TimeResolution:
    year = int(match.group(1))
    return _fixed_window(
        canonical=f"year_{year}",
        label=str(year),
        grain=TimeGrain.YEAR,
        start_sql=f"MAKEDATE({year}, 1)",
        end_sql=f"MAKEDATE({year + 1}, 1)",
    )


def _handle_quarter_year(match: re.Match) -> TimeResolution:
    q = int(match.group(1))
    year = int(match.group(2))
    start_month = (q - 1) * 3 + 1
    return _fixed_window(
        canonical=f"q{q}_{year}",
        label=f"Q{q} {year}",
        grain=TimeGrain.QUARTER,
        start_sql=f"MAKEDATE({year}, 1) + INTERVAL {start_month - 1} MONTH",
        end_sql=f"MAKEDATE({year}, 1) + INTERVAL {start_month + 2} MONTH",
    )


def _handle_month_year(match: re.Match) -> Optional[TimeResolution]:
    name = match.group(1)
    if name not in _MONTH_NAMES:
        return None
    month = _MONTH_NAMES[name]
    year = int(match.group(2))
    return _fixed_window(
        canonical=f"{year}_{month:02d}",
        label=f"{name.capitalize()} {year}",
        grain=TimeGrain.MONTH,
        start_sql=f"MAKEDATE({year}, 1) + INTERVAL {month - 1} MONTH",
        end_sql=f"MAKEDATE({year}, 1) + INTERVAL {month} MONTH",
    )


def _handle_fiscal(phrase: str) -> TimeResolution:
    """Fiscal phrases resolve only when a fiscal calendar is configured.

    Reinterpreting "previous fiscal year" as a calendar year silently shifts
    every boundary in the result.  Abstaining is the correct behaviour when the
    deployment has not told us where its fiscal year starts.
    """
    if FISCAL_YEAR_START_MONTH is None:
        return _unsupported(
            phrase,
            "fiscal calendar is not configured for this deployment "
            "(set FISCAL_YEAR_START_MONTH in the semantic layer)",
        )
    start_month = FISCAL_YEAR_START_MONTH
    offset = 0 if ("this" in phrase or "current" in phrase) else -1
    anchor = (
        f"MAKEDATE(YEAR({_NOW}) - IF(MONTH({_NOW}) < {start_month}, 1, 0), 1) "
        f"+ INTERVAL {start_month - 1} MONTH"
    )
    return _fixed_window(
        canonical=f"fiscal_year_{'current' if offset == 0 else 'previous'}",
        label=f"{'Current' if offset == 0 else 'Previous'} fiscal year",
        grain=TimeGrain.YEAR,
        start_sql=f"{anchor} + INTERVAL {offset} YEAR",
        end_sql=f"{anchor} + INTERVAL {offset + 1} YEAR",
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def _clean(phrase: str) -> str:
    """Lower-case, collapse whitespace, strip separators and filler words."""
    text = phrase.lower().replace("_", " ").replace("-", " ")
    text = text.replace("‑", " ").replace("–", " ").replace("—", " ")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for filler in ("during ", "within ", "over ", "in the ", "for the ", "the "):
        if text.startswith(filler):
            text = text[len(filler):]
    return text.strip()


def normalise(phrase: Optional[str]) -> TimeResolution:
    """Normalise a temporal expression into an explicit outcome.

    This function is total: every input produces RESOLVED, UNSUPPORTED, or
    NONE.  It never returns a value that a caller can mistake for "no filter
    needed" when the user did in fact ask for one.

    Args:
        phrase: Raw temporal expression from the intent object, or ``None``.

    Returns:
        A :class:`TimeResolution` carrying the canonical range or the reason
        the phrase could not be honoured.
    """
    if phrase is None:
        return TimeResolution(status=TimeStatus.NONE)

    text = _clean(str(phrase))
    if text in _ALL_TIME:
        return TimeResolution(status=TimeStatus.NONE, raw=str(phrase))

    if _RE_FISCAL.search(text):
        return _handle_fiscal(text)

    resolved = _PHRASE_ALIASES.get(text, text)
    if resolved in _NAMED:
        return _NAMED[resolved]

    for pattern, handler in (
        (_RE_RELATIVE, _handle_relative),
        (_RE_AGO, _handle_ago),
        (_RE_QUARTER_YEAR, _handle_quarter_year),
        (_RE_MONTH_YEAR, _handle_month_year),
        (_RE_YEAR, _handle_year),
    ):
        match = pattern.match(text)
        if match:
            result = handler(match)
            if result is not None:
                return result

    # "last 24 hours" phrased without a unit gap, e.g. "past24hours", and any
    # other shape we do not model, must abstain rather than silently pass.
    return _unsupported(
        str(phrase),
        f"unrecognised time expression '{phrase}'. Supported forms include: "
        "today, yesterday, this/last week|month|quarter|year, "
        "last N days|weeks|months|quarters|years, N days ago, "
        "week/month/quarter/year to date, Q1 2024, March 2024, 2023",
    )


def supported_expressions() -> list:
    """Return the documented vocabulary, for clarification messages and docs."""
    return sorted(set(_NAMED.keys()) | set(_PHRASE_ALIASES.keys())) + [
        "last N hours|days|weeks|months|quarters|years",
        "N days|weeks|months ago",
        "Q1..Q4 <year>",
        "<month name> <year>",
        "<year>",
    ]
