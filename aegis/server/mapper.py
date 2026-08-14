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
from typing import Any, Dict, List, Optional, Sequence, Set

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
from .semantic_layer import (BUSINESS_LOGIC_MAPPINGS, DIMENSIONS,
                             FAN_OUT_TABLES, GOVERNED_PREDICATES, METRICS,
                             ORDER_GRAIN_TABLES, PREDICATE_FIELD)

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
    #
    #: "summary" is deliberately absent: a summary is a multi-metric overview
    #: by definition ("total sales, average order value and order count by
    #: category"), so the extractor legitimately returns no single metric for
    #: one. Demanding one refused exactly the requests the pattern exists to
    #: serve.
    REQUIRES_METRIC = {"kpi", "ranking", "trend", "comparison", "segment", "correlate"}

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
        metric_binding, dimension_binding = self._recover_swapped_slots(
            metric_binding, dimension_binding
        )
        bindings = [metric_binding, dimension_binding]

        coverage = self.analyser.analyse(question, intent, bindings) if question \
            else self._coverage_from_bindings(intent, bindings)

        time_result = time_grammar.normalise(intent.time_term)

        # --- REJECT: the vocabulary cannot express the request -------------
        rejection = self._rejection_reason(
            pattern, metric_binding, dimension_binding, time_result, coverage,
            intent.filters,
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
            metric_binding, dimension_binding, intent, coverage, time_result
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

    def _recover_swapped_slots(self, metric: Binding, dimension: Binding):
        """Re-file a term the extractor put in the wrong slot.

        The model sometimes returns a dimension id as ``metric_term`` — asked
        for "the average rating of products returned more than twice", it
        offers ``product_rating``, which is a dimension. Refusing because "no
        approved metric corresponds to 'product_rating'" is pedantry: the term
        *is* approved, and its correct slot is unambiguous because it grounds
        cleanly in the other vocabulary and not at all in this one.

        Only a term that fails in its own slot and resolves in the other is
        moved, and only into a slot that is otherwise empty, so this cannot
        override something the model got right.

        Returns:
            The possibly-corrected ``(metric, dimension)`` pair.
        """
        if (
            metric.resolution == Resolution.UNSUPPORTED
            and dimension.resolution == Resolution.ABSENT
            and metric.term
        ):
            as_dimension = self.engine.ground(metric.term, "dimension")
            if as_dimension.resolution == Resolution.RESOLVED:
                logger.info(
                    "Re-filed %r from metric to dimension: it names an "
                    "approved dimension.", metric.term,
                )
                return (
                    Binding(term=None, slot="metric", resolution=Resolution.ABSENT),
                    as_dimension,
                )

        if (
            dimension.resolution == Resolution.UNSUPPORTED
            and metric.resolution == Resolution.ABSENT
            and dimension.term
        ):
            as_metric = self.engine.ground(dimension.term, "metric")
            if as_metric.resolution == Resolution.RESOLVED:
                logger.info(
                    "Re-filed %r from dimension to metric: it names an "
                    "approved metric.", dimension.term,
                )
                return (
                    as_metric,
                    Binding(term=None, slot="dimension", resolution=Resolution.ABSENT),
                )

        return metric, dimension

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
        filters: Optional[Sequence[Filter]] = None,
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

        # A summary is multi-metric by definition, which is why `summary` is
        # absent from REQUIRES_METRIC — but the compiler builds one aggregate
        # expression per query and has no multi-metric form. Left unchecked the
        # plan reached the compiler with an empty metric slot, where it used to
        # be silently filled with revenue and now raises. Both are worse than
        # saying so here: an unsupported request should be a reasoned refusal,
        # not a crash reported as a hard failure.
        if metric.resolution == Resolution.ABSENT and pattern == "summary":
            return (
                "A summary over several measures at once is not something this "
                "system can build yet — it produces one measure per report. "
                "Asking for them individually will work: "
                f"{', '.join(self.engine.vocabulary('metric'))}."
            )

        if pattern in self.REQUIRES_DIMENSION and dimension.resolution == Resolution.ABSENT:
            return (
                f"A '{pattern}' report needs something to group by, and the "
                f"request did not name an approved dimension. Approved "
                f"dimensions: {', '.join(self.engine.vocabulary('dimension'))}."
            )

        # A rate is a quotient of two aggregates, so there is no per-row value
        # to compare against a threshold — "categories where the average
        # discount exceeds 30%" is a HAVING clause, which the compiler's
        # templates do not cover. The compiler refuses correctly but does it by
        # raising, which surfaces to the user as a crash rather than as the
        # explanation they can act on.
        unfilterable = self._unfilterable_metric_terms(filters)
        if unfilterable:
            names = ", ".join(f"'{n}'" for n in unfilterable)
            return (
                f"{names} is an average or rate, which is computed across a "
                f"group rather than stored per row, so it cannot be used as a "
                f"filter here. Asking for the same breakdown without the "
                f"threshold will work, and the values can be read off directly."
            )

        if time_result.status == time_grammar.TimeStatus.UNSUPPORTED:
            return (
                f"{time_result.reason}. The time filter was not applied because "
                f"answering over the wrong period would be worse than not "
                f"answering."
            )

        # GRAIN_ONLY and VAGUE are deliberately not rejections. A granularity
        # ("monthly") imposes no filter at all, and an underdetermined period
        # ("recent") is a question worth asking rather than grounds to refuse.
        return None

    @staticmethod
    def _unfilterable_metric_terms(filters) -> List[str]:
        """Metric names used as row filters that have no per-row value.

        A ratio or average is computed across a group, so there is nothing on
        an individual row to compare a threshold against. Detecting it here
        keeps the refusal a reasoned one; the compiler also refuses, but only
        by raising.
        """
        from .compiler import SQLCompiler

        names: List[str] = []
        for f in filters or []:
            metric = next((m for m in METRICS if m.id == str(f.field)), None)
            if metric and not SQLCompiler._strip_aggregate(metric.sql_expr):
                names.append(metric.label)
        return names

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
        time_result=None,
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

        if time_result is not None and time_result.status == time_grammar.TimeStatus.VAGUE:
            return (time_result.reason, [])

        if coverage.compound_request:
            return (
                "This asks for two different reports in one request, and a "
                "widget shows one result shape. Which should this widget "
                "show? I can build the other as a second widget.",
                [],
            )

        # Qualifiers deliberately do NOT block. "net revenue", "new customers"
        # and "profit margin" are all expressible; what differs is the
        # definition the user assumed versus the one the semantic layer owns.
        # Refusing to answer teaches the user the system is broken, when the
        # useful response is the governed number plus a note saying how it is
        # defined. The note travels on the plan's coverage warnings and is
        # surfaced by the interpretation line.
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

        metric_id, metric_obj, grain_note = self._resolve_grain(
            metric_obj, join_tables
        )
        if metric_obj:
            join_tables.add(metric_obj.binding_table)
            join_tables.update(metric_obj.required_joins)

        return AnalysisPlan(
            pattern=pattern,
            metric=metric_id,
            dimension=dimension_id,
            time_rule=intent.time_term,
            time_range=time_result.range,
            time_grain=(
                time_result.grain.value if time_result.grain is not None else None
            ),
            join_path=sorted(join_tables),
            filters=self._apply_business_logic_filters(intent.filters),
            sort=intent.sort,
            limit=intent.limit,
            visual=self.VISUAL_DEFAULTS.get(pattern, "kpi_card"),
            bindings=bindings,
            coverage=coverage,
            notes=[grain_note] if grain_note else [],
        )

    @staticmethod
    def _resolve_grain(metric_obj, join_tables: Set[str]):
        """Keep an order-level aggregate off an item-level breakdown.

        `SUM(o.OrderTotal)` grouped by category — joined Order → OrderItem →
        Product → Category — adds each order's whole total once per matching
        line, so an order with three items in a category contributes three
        times. Nothing about the result reveals this: it is ordered, chartable,
        and plausibly sized. The host platform does not compute per-category
        revenue this way either; it filters orders by category and still
        reports whole-order totals, which is imprecise but at least not
        multiplicative.

        Where the semantic layer declares an item-grain counterpart, that
        counterpart is used and the substitution is recorded so the plan
        verbalisation states it: this is a governed definition ("revenue by
        category means line-item revenue"), authored by an administrator, not a
        silent repair. Where none is declared, the metric is left alone and the
        caller decides — a wrong number must never be manufactured here.

        Returns:
            ``(metric_id, metric_obj, note_or_None)``.
        """
        if metric_obj is None:
            return "_none_", None, None
        if metric_obj.binding_table not in ORDER_GRAIN_TABLES:
            return metric_obj.id, metric_obj, None
        if not (join_tables & FAN_OUT_TABLES):
            return metric_obj.id, metric_obj, None

        replacement_id = getattr(metric_obj, "item_grain_equivalent", "")
        if not replacement_id:
            return metric_obj.id, metric_obj, None
        replacement = next((m for m in METRICS if m.id == replacement_id), None)
        if replacement is None:
            return metric_obj.id, metric_obj, None

        note = (
            f"{metric_obj.label} is measured per order, so it cannot be "
            f"attributed to an item-level breakdown without counting each "
            f"order once per matching line. Using {replacement.label} instead, "
            f"as the semantic layer defines for this grain."
        )
        logger.info("Grain guard: %s -> %s (%s)",
                    metric_obj.id, replacement.id, sorted(join_tables & FAN_OUT_TABLES))
        return replacement.id, replacement, note

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

            mapping = (BUSINESS_LOGIC_MAPPINGS.get(field)
                       or BUSINESS_LOGIC_MAPPINGS.get(val))
            if mapping is not None:
                final_filters.append(self._as_filter(mapping))
                continue
            final_filters.append(f)
        return final_filters

    @staticmethod
    def _as_filter(mapping: Dict[str, Any]) -> Filter:
        """Builds the Filter a business-logic mapping stands for.

        A mapping is either a field/operator/value triple or a reference to a
        governed predicate.  The reference carries only the *key* — the SQL
        lives in the semantic layer and is looked up by the compiler — so no
        user-influenced text is ever placed on the path to a query.
        """
        if "predicate" in mapping:
            key = mapping["predicate"]
            if key not in GOVERNED_PREDICATES:
                # A dangling reference must fail loudly. Dropping the filter
                # would widen the result set silently, which is the exact
                # class of defect this pipeline exists to rule out.
                raise KeyError(
                    f"business logic mapping references unknown governed "
                    f"predicate '{key}'"
                )
            return Filter(field=PREDICATE_FIELD, operator="=", value=key)
        return Filter(**mapping)

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
