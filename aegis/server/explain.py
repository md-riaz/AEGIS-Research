"""
AEGIS Plan Verbaliser — rendering an interpretation back for confirmation.

Why this exists
---------------
NaLIR (Li et al., 2014) reported the finding that should govern the design of
any natural-language database interface: in their user study, of 32 wrong
answers produced *without* an interactive confirmation step, participants
detected only 7.  Most undetected errors were aggregates — a single number that
looks equally plausible whether or not the system understood the question.
DataTone (Gao et al., 2015) surfaced interpretation choices as "ambiguity
widgets" for the same reason, and found users resolved them readily once they
could see them.

The dominant real-world failure mode is therefore not a crash and not unsafe
SQL.  It is a confident, well-formatted, wrong answer that nobody questions.

AEGIS is unusually well placed to address this cheaply.  Because the LLM
produces a *typed plan* rather than SQL, the system's interpretation exists in
an inspectable form at a point where nothing has executed yet — no query has
run, no result has been rendered, no number has been believed.  Verbalising
that plan costs one template expansion and turns a silent misinterpretation
into a visible, correctable one.

Everything here is deterministic string construction.  No model is consulted:
an explanation produced by a second model call could itself be wrong, and an
explanation that does not faithfully reflect the plan is worse than none.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, List, Optional, Sequence, Union

from .models import AnalysisPlan, Binding
from .semantic_layer import DIMENSIONS, METRICS

logger = logging.getLogger(__name__)

#: Readable renderings for the filter operators the compiler accepts.
_OPERATOR_PHRASES = {
    "=": "is", "==": "is", "!=": "is not", "<>": "is not",
    ">": "is greater than", ">=": "is at least",
    "<": "is less than", "<=": "is at most",
    "contains": "contains", "between": "is between",
    "in": "is one of", "not in": "is not one of",
    "is_null": "is empty", "is_not_null": "is not empty",
}


def _label(object_id: Optional[str]) -> Optional[str]:
    """Human label for a semantic-layer id, falling back to the id itself."""
    if not object_id or object_id == "_none_":
        return None
    for obj in list(METRICS) + list(DIMENSIONS):
        if obj.id == object_id:
            return obj.label
    return object_id.replace("_", " ")


def explain_plan(plan: Optional[AnalysisPlan]) -> str:
    """Render an analysis plan as one plain-English sentence.

    The sentence is what a user is asked to confirm before the result is
    trusted, so it must state every choice that could be wrong: which measure,
    which breakdown, which period, which filters, which ordering and cut-off.

    Args:
        plan: The plan to describe. ``None`` is tolerated because this is also
            called on error paths.

    Returns:
        A sentence such as "Total Revenue, broken down by Product Name, for
        Last 30 days, highest first, top 10." — or a short placeholder when
        there is no plan to describe.
    """
    if plan is None:
        return "No interpretation was produced."

    metric_label = _label(plan.metric)
    # Every measure the query computes has to appear here. A summary returns
    # several columns, and a sentence naming only the first describes something
    # narrower than what the user is about to read — the confirmation step is
    # worthless if it confirms the wrong shape.
    extra_labels = [_label(m) for m in (plan.extra_metrics or [])]
    extra_labels = [label for label in extra_labels if label]
    if metric_label and extra_labels:
        named = [metric_label, *extra_labels]
        metric_label = ", ".join(named[:-1]) + f" and {named[-1]}"
    parts: List[str] = [metric_label] if metric_label else ["A list of records"]

    dimension_label = _label(plan.dimension)
    if dimension_label:
        # "broken down by" reads correctly for segment/trend/ranking alike,
        # whereas "grouped by" invites a SQL reading the user may not have.
        parts.append(f"broken down by {dimension_label}")

    if plan.time_range is not None:
        parts.append(f"for {plan.time_range.label}")
    elif plan.time_rule:
        parts.append(f"for {plan.time_rule}")

    filter_phrases = explain_filters(plan)
    if filter_phrases:
        parts.append("where " + " and ".join(filter_phrases))

    if plan.sort:
        parts.append("highest first" if plan.sort == "desc" else "lowest first")

    if plan.limit:
        parts.append(f"top {plan.limit}")

    sentence = ", ".join(parts) + "."
    # A governed definition the user did not ask for is exactly the kind of
    # decision this verbalisation exists to surface: correct or not, it changes
    # what the number means, and the user cannot check what they are not shown.
    if plan.notes:
        sentence += " " + " ".join(plan.notes)
    return sentence


def explain_filters(plan: Optional[AnalysisPlan]) -> List[str]:
    """Render each filter predicate as a readable phrase.

    Args:
        plan: The plan whose filters should be described.

    Returns:
        One phrase per filter, e.g. ``["Stock Level is less than 10"]``.
        Empty when there are no filters.
    """
    if plan is None or not plan.filters:
        return []

    phrases: List[str] = []
    for f in plan.filters:
        field_label = _label(f.field) or str(f.field).replace("_", " ")
        operator = _OPERATOR_PHRASES.get(str(f.operator), str(f.operator))
        if str(f.operator) in ("is_null", "is_not_null"):
            phrases.append(f"{field_label} {operator}")
        else:
            phrases.append(f"{field_label} {operator} {f.value}")
    return phrases


def explain_bindings(
    source: Union[AnalysisPlan, Sequence[Binding], None]
) -> List[str]:
    """Render how each term in the request was interpreted, with its evidence.

    This is the audit surface.  A user who disagrees with the answer needs to
    see *which word became which approved identifier and on what grounds* —
    that is the level at which a misinterpretation is actually correctable.

    Args:
        source: An :class:`AnalysisPlan` (its ``bindings`` are used) or a bare
            sequence of :class:`Binding` objects.

    Returns:
        One line per bound slot. Slots the request never mentioned are omitted,
        since "the user did not ask for a breakdown" is not an interpretation.
    """
    bindings = _bindings_of(source)
    lines: List[str] = []

    for binding in bindings:
        resolution = _value_of(binding.resolution)
        if resolution == "absent":
            continue

        if resolution == "resolved":
            label = _label(binding.chosen) or binding.chosen
            evidence = binding.candidates[0].evidence if binding.candidates else ""
            line = f"'{binding.term}' → {binding.chosen} ({label})"
            lines.append(f"{line} — {evidence}" if evidence else line)

        elif resolution == "ambiguous":
            options = ", ".join(
                f"{c.id} ({c.label})" for c in binding.candidates
            )
            lines.append(
                f"'{binding.term}' is ambiguous between {options} — "
                f"no {binding.slot} was chosen"
            )

        elif resolution == "unsupported":
            lines.append(
                f"'{binding.term}' matched no approved {binding.slot}"
                + (f" — {binding.reason}" if binding.reason else "")
            )

    return lines


def explain_alternatives(binding: Optional[Binding]) -> List[str]:
    """Render an ambiguous binding's candidates as selectable options.

    NaLIR surfaced its top five candidate mappings and found users could
    reliably pick the correct one from that many; this renders the same list in
    business vocabulary rather than schema identifiers, so the choice is
    meaningful to a non-technical user.

    Args:
        binding: The binding whose candidates should be offered.

    Returns:
        One line per candidate, ordered best-first. Empty if there is nothing
        to choose between.
    """
    if binding is None or not binding.candidates:
        return []
    return [
        f"{candidate.id} — {candidate.label} ({candidate.evidence})"
        for candidate in binding.candidates
    ]


def _bindings_of(
    source: Union[AnalysisPlan, Sequence[Binding], None]
) -> List[Binding]:
    """Accept either a plan or a raw binding sequence."""
    if source is None:
        return []
    if isinstance(source, AnalysisPlan):
        return list(source.bindings)
    return list(source)


def _value_of(enum_or_str: Any) -> str:
    """Normalise an enum-or-string field to its string value.

    ``IntentObject`` and friends are configured with ``use_enum_values``, but a
    ``Binding`` constructed directly in code may still hold an enum member.
    Both shapes must render identically.
    """
    return str(getattr(enum_or_str, "value", enum_or_str))
