"""
AEGIS Semantic Resolver (Stage 2) — grounding with an explicit non-answer.

What changed and why
--------------------
The previous mapper resolved every slot to *something*::

    metric_id = self._resolve_id(intent.metric_term or "order_count", "metric")
    if metric_id == "unknown":
        metric_id = "revenue"          # silent substitution
    ...
    if dimension_id == "unknown":
        dimension_id = None            # silent removal of the grouping

Combined with an intent object whose ``metric_term`` defaulted to
``order_count``, this meant a request the system did not understand still
produced a syntactically valid, safely compiled, confidently presented — and
wrong — widget.  The safety guarantee held; the answer was fiction.

The resolver below removes every silent fallback.  Each slot is grounded
through :mod:`.grounding`, which returns ranked candidates and one of
RESOLVED / AMBIGUOUS / UNSUPPORTED / ABSENT.  Those outcomes, together with the
:mod:`.coverage` report over the original question and the total time grammar,
decide the terminal :class:`~.models.Outcome`:

  * **ANSWER**  — every required slot is bound and the vocabulary explains the
    whole request.
  * **CLARIFY** — the request is expressible, but a specific choice is
    genuinely underdetermined.  The user is asked one concrete question with
    the candidate answers attached.
  * **REJECT**  — no combination of approved bindings expresses the request.

``SemanticMapper`` is retained as an alias so existing callers and tests keep
working; new code should use :class:`SemanticResolver`.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence, Set

from . import time_grammar
from .coverage import CoverageAnalyser
from .grounding import GroundingEngine
from .models import (
    AnalysisPlan,
    Binding,
    CoverageReport,
    Filter,
    IntentObject,
    Outcome,
    Resolution,
    ResolutionResult,
)
from .semantic_layer import BUSINESS_LOGIC_MAPPINGS, DIMENSIONS, METRICS

logger = logging.getLogger(__name__)


class UnresolvedRequestError(Exception):
    """Raised by the legacy ``map()`` path when a request is not answerable."""

    def __init__(self, result: ResolutionResult):
        super().__init__(result.message or "request could not be resolved")
        self.result = result


class SemanticResolver:
    """Grounds an intent into an analysis plan, or explains why it cannot."""

    #: Default chart per pattern.  The visualisation layer refines this from
    #: the actual result shape; this is only the starting point.
    VISUAL_DEFAULTS: Dict[str, str] = {
        "ranking": "bar_chart",
        "trend": "line_chart",
        "comparison": "grouped_bar",
        "tabular": "table",
        "kpi": "kpi_card",
        "exception": "table",
        "summary": "kpi_grid",
        "segment": "pie_chart",
        "funnel": "funnel_chart",
        "cohort": "grouped_bar",
        "correlate": "scatter_plot",
    }

    #: Patterns that are meaningless without a grouping dimension.  Previously
    #: a dropped dimension turned these into a single scalar without comment.
    REQUIRES_DIMENSION = {"ranking", "trend", "comparison", "segment", "cohort", "correlate"}

    #: Patterns that are meaningless without a metric.
    REQUIRES_METRIC = {"kpi", "ranking", "trend", "comparison", "segment", "summary", "correlate"}

    def __init__(
        self,
        engine: Optional[GroundingEngine] = None,
        analyser: Optional[CoverageAnalyser] = None,
    ):
        self.engine = engine or GroundingEngine()
        self.analyser = analyser or CoverageAnalyser(self.engine)

    # ------------------------------------------------------------------
    # Primary entry point
    # ------------------------------------------------------------------

    def resolve(self, intent: IntentObject, question: str = "") -> ResolutionResult:
        """Ground ``intent`` into a plan or a reasoned non-answer.

        Args:
            intent: Typed output of the intent extraction stage.
            question: The original request text.  Supplying it enables the
                coverage analysis that detects out-of-vocabulary concepts; the
                resolver still works without it, but loses that protection.

        Returns:
            A :class:`ResolutionResult` whose ``outcome`` is ANSWER, CLARIFY,
            or REJECT.
        """
        pattern = str(intent.intent_class)

        metric_binding = self.engine.ground(intent.metric_term, "metric")
        dimension_binding = self.engine.ground(intent.dimension_term, "dimension")
        bindings = [metric_binding, dimension_binding]

        coverage = self.analyser.analyse(question, intent, bindings) if question \
            else self._coverage_from_bindings(intent, bindings)

        time_result = time_grammar.normalise(intent.time_term)

        # --- REJECT: the vocabulary cannot express the request -------------
        rejection = self._rejection_reason(
            pattern, metric_binding, dimension_binding, time_result, coverage
        )
        if rejection is not None:
            return ResolutionResult(
                outcome=Outcome.REJECT,
                bindings=bindings,
                coverage=coverage,
                message=rejection,
            )

        # --- CLARIFY: expressible, but a choice is underdetermined ---------
        clarification = self._clarification(
            metric_binding, dimension_binding, intent, coverage
        )
        if clarification is not None:
            question_text, options = clarification
            return ResolutionResult(
                outcome=Outcome.CLARIFY,
                bindings=bindings,
                coverage=coverage,
                question=question_text,
                options=options,
                message="The request is supported but underdetermined.",
            )

        # --- ANSWER --------------------------------------------------------
        plan = self._build_plan(
            intent, pattern, metric_binding, dimension_binding,
            time_result, bindings, coverage,
        )
        return ResolutionResult(
            outcome=Outcome.ANSWER, plan=plan, bindings=bindings, coverage=coverage
        )

    # ------------------------------------------------------------------
    # Decision rules
    # ------------------------------------------------------------------

    def _rejection_reason(
        self,
        pattern: str,
        metric: Binding,
        dimension: Binding,
        time_result,
        coverage: CoverageReport,
    ) -> Optional[str]:
        """Return a rejection message, or ``None`` if the request is expressible."""
        # Checked before coverage: a write request is a category error, not a
        # vocabulary gap, and saying so is far more useful than reporting
        # whichever noun in the sentence happened not to bind.
        if coverage.write_request:
            return (
                "This asks to change data, and AEGIS is read-only — it can "
                "only produce reports. There is no way to express a write in "
                "this system. If it would help, ask for the same records as a "
                "report instead."
            )

        if coverage.unmapped_concepts:
            concepts = ", ".join(f"'{c}'" for c in coverage.unmapped_concepts)
            return (
                f"This request refers to {concepts}, which the semantic layer "
                f"does not define. Approved metrics: "
                f"{', '.join(self.engine.vocabulary('metric'))}. "
                f"Approved dimensions: "
                f"{', '.join(self.engine.vocabulary('dimension'))}."
            )

        if metric.resolution == Resolution.UNSUPPORTED:
            return (
                f"{metric.reason} Approved metrics: "
                f"{', '.join(self.engine.vocabulary('metric'))}."
            )

        if dimension.resolution == Resolution.UNSUPPORTED:
            return (
                f"{dimension.reason} Approved dimensions: "
                f"{', '.join(self.engine.vocabulary('dimension'))}."
            )

        if pattern in self.REQUIRES_METRIC and metric.resolution == Resolution.ABSENT:
            return (
                f"A '{pattern}' report needs a metric, and the request did not "
                f"name one. Approved metrics: "
                f"{', '.join(self.engine.vocabulary('metric'))}."
            )

        if pattern in self.REQUIRES_DIMENSION and dimension.resolution == Resolution.ABSENT:
            return (
                f"A '{pattern}' report needs something to group by, and the "
                f"request did not name an approved dimension. Approved "
                f"dimensions: {', '.join(self.engine.vocabulary('dimension'))}."
            )

        if time_result.status == time_grammar.TimeStatus.UNSUPPORTED:
            return (
                f"{time_result.reason}. The time filter was not applied because "
                f"answering over the wrong period would be worse than not "
                f"answering."
            )

        return None

    @staticmethod
    def _definition(object_id: str) -> str:
        """Human-readable definition of an approved metric or dimension."""
        for obj in list(METRICS) + list(DIMENSIONS):
            if obj.id == object_id:
                return obj.description
        return "not defined"

    def _clarification(
        self,
        metric: Binding,
        dimension: Binding,
        intent: IntentObject,
        coverage: CoverageReport,
    ) -> Optional[tuple]:
        """Return ``(question, options)`` when one choice is underdetermined.

        Only the first ambiguity is surfaced.  DataTone showed that stacking
        ambiguity widgets multiplies the decisions a user must make; resolving
        one at a time keeps each turn answerable.
        """
        for binding, noun in ((metric, "measure"), (dimension, "breakdown")):
            if binding.resolution == Resolution.AMBIGUOUS:
                options = [c.id for c in binding.candidates]
                return (
                    f"'{binding.term}' could mean {len(options)} different "
                    f"{noun}s. Which did you mean?",
                    options,
                )

        if coverage.compound_request:
            return (
                "This asks for two different reports in one request, and a "
                "widget shows one result shape. Which should this widget "
                "show? I can build the other as a second widget.",
                [],
            )

        if coverage.qualified_concepts:
            qualifiers = ", ".join(f"'{q}'" for q in coverage.qualified_concepts)
            definitions = "; ".join(
                f"{b.chosen} = {self._definition(b.chosen)}"
                for b in (metric, dimension)
                if b.chosen and b.chosen != "_none_"
            )
            return (
                f"The request qualifies the measurement with {qualifiers}, "
                f"which the semantic layer does not model separately. The "
                f"governed definition is: {definitions}. Use that?",
                [],
            )

        if intent.needs_clarification:
            return (
                intent.clarification_reason
                or "The request is ambiguous. Could you rephrase it more specifically?",
                [],
            )
        return None

    def _coverage_from_bindings(
        self, intent: IntentObject, bindings: Sequence[Binding]
    ) -> CoverageReport:
        """Fallback coverage report when the original question is unavailable."""
        return CoverageReport(
            unmapped_concepts=list(intent.unmapped_terms),
            ambiguous_slots=[
                b.slot for b in bindings if b.resolution == Resolution.AMBIGUOUS
            ],
        )

    # ------------------------------------------------------------------
    # Plan construction
    # ------------------------------------------------------------------

    def _build_plan(
        self,
        intent: IntentObject,
        pattern: str,
        metric: Binding,
        dimension: Binding,
        time_result,
        bindings: List[Binding],
        coverage: CoverageReport,
    ) -> AnalysisPlan:
        metric_id = metric.chosen or "_none_"
        dimension_id = dimension.chosen

        join_tables: Set[str] = set()
        metric_obj = next((m for m in METRICS if m.id == metric_id), None)
        if metric_obj:
            join_tables.add(metric_obj.binding_table)
            join_tables.update(metric_obj.required_joins)

        if dimension_id:
            dim_obj = next((d for d in DIMENSIONS if d.id == dimension_id), None)
            if dim_obj:
                join_tables.add(dim_obj.binding_table)
                join_tables.update(dim_obj.required_joins)

        return AnalysisPlan(
            pattern=pattern,
            metric=metric_id,
            dimension=dimension_id,
            time_rule=intent.time_term,
            time_range=time_result.range,
            join_path=sorted(join_tables),
            filters=self._apply_business_logic_filters(intent.filters),
            sort=intent.sort,
            limit=intent.limit,
            visual=self.VISUAL_DEFAULTS.get(pattern, "kpi_card"),
            bindings=bindings,
            coverage=coverage,
        )

    def _apply_business_logic_filters(self, filters: List[Filter]) -> List[Filter]:
        """Expand abstract business terms into concrete filter predicates.

        Example:
            ``Filter(field='status', value='abandoned')``
            → ``Filter(field='OrderStatusId', operator='=', value=40)``
        """
        final_filters: List[Filter] = []
        for f in filters:
            field = f.field.lower()
            val = str(f.value).lower() if f.value is not None else ""

            if field in BUSINESS_LOGIC_MAPPINGS:
                final_filters.append(Filter(**BUSINESS_LOGIC_MAPPINGS[field]))
                continue
            if val in BUSINESS_LOGIC_MAPPINGS:
                final_filters.append(Filter(**BUSINESS_LOGIC_MAPPINGS[val]))
                continue
            final_filters.append(f)
        return final_filters

    # ------------------------------------------------------------------
    # Backwards-compatible surface
    # ------------------------------------------------------------------

    def map(self, intent: IntentObject, question: str = "") -> AnalysisPlan:
        """Legacy entry point returning a plan directly.

        Raises:
            UnresolvedRequestError: If the request is not answerable.  The old
                behaviour — substituting ``revenue`` and continuing — is what
                this architecture exists to prevent, so the failure is now
                explicit rather than silent.
        """
        result = self.resolve(intent, question)
        if result.outcome != Outcome.ANSWER or result.plan is None:
            raise UnresolvedRequestError(result)
        return result.plan

    def _resolve_id(self, term: str, type: str) -> str:
        """Resolve a term to a canonical id, or the sentinel ``"unknown"``.

        Retained for the coverage gate and existing tests.  Ambiguous terms
        report ``"unknown"`` rather than silently picking a winner, which is
        the behavioural difference from the original four-tier scan.
        """
        if not term:
            return ""
        binding = self.engine.ground(term, type)
        if binding.resolution == Resolution.RESOLVED:
            return binding.chosen
        return "unknown"

    @classmethod
    def can_resolve(cls, term: str, obj_type: str) -> bool:
        """Whether ``term`` grounds to exactly one approved object."""
        return cls()._resolve_id(term, obj_type) not in ("unknown", "")


#: Backwards-compatible alias — the class was named ``SemanticMapper`` when it
#: only mapped.  It now resolves, decides, and can decline.
SemanticMapper = SemanticResolver
