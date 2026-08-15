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
import re
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
from .semantic_layer import (ALIAS_TO_TABLE, BUSINESS_LOGIC_MAPPINGS,
                             DIMENSIONS, FAN_OUT_TABLES, GOVERNED_PREDICATES,
                             LISTING_PATTERNS, METRICS, ORDER_GRAIN_TABLES,
                             PREDICATE_FIELD, TABLE_DATE_FIELDS)

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

        # Every additional measure a summary named is grounded here, and each
        # one that fails to bind is reported rather than dropped. Silently
        # keeping the measures that happened to resolve would answer a narrower
        # question than the one asked, without saying so.
        extra_bindings = [
            self.engine.ground(term, "metric")
            for term in (intent.metric_terms or [])
            if term and term != intent.metric_term
        ]
        bindings.extend(extra_bindings)

        coverage = self.analyser.analyse(question, intent, bindings) if question \
            else self._coverage_from_bindings(intent, bindings)

        time_result = time_grammar.normalise(intent.time_term)

        # --- REJECT: the vocabulary cannot express the request -------------
        rejection = self._rejection_reason(
            pattern, metric_binding, dimension_binding, time_result, coverage,
            intent.filters, intent.time_term,
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
            time_result, bindings, coverage, extra_bindings,
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
        time_term: Optional[str] = None,
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
        # A summary is multi-metric by definition, so it is absent from
        # REQUIRES_METRIC — but it still needs at least one measure. Naming
        # none leaves nothing to compute, and the empty slot used to be filled
        # silently with whichever metric came first.
        if metric.resolution == Resolution.ABSENT and pattern == "summary":
            return (
                "A summary needs at least one measure, and the request did not "
                "name one. Approved metrics: "
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
        # A filter naming something the layer cannot bind used to reach the
        # compiler and raise, which the caller saw as a crash rather than as
        # the explanation it is. Grounding happens first, so anything still
        # unbound here is genuinely outside the vocabulary.
        # Ground once and reuse. `_unfilterable_metric_terms` used to receive
        # the raw intent filters while `_unbindable_filter_fields` grounded
        # them internally, so the two checks disagreed about what a field was
        # called: a model-supplied "discount rate" matched no METRICS entry,
        # the aggregate-filter refusal was skipped, and the compiler raised one
        # stage later — the crash-instead-of-explanation path this change set
        # removes everywhere else.
        grounded_filters = self._apply_business_logic_filters(list(filters or []))

        unbindable = self._unbindable_filter_fields(grounded_filters, grounded=True)
        if unbindable:
            names = ", ".join(f"'{n}'" for n in unbindable)
            return (
                f"The condition on {names} cannot be expressed: it does not "
                f"name an approved metric or dimension. Approved dimensions: "
                f"{', '.join(self.engine.vocabulary('dimension'))}."
            )

        unfilterable = self._unfilterable_metric_terms(grounded_filters)
        if unfilterable:
            names = ", ".join(f"'{n}'" for n in unfilterable)
            return (
                f"{names} is an average or rate, which is computed across a "
                f"group rather than stored per row, so it cannot be used as a "
                f"filter here. Asking for the same breakdown without the "
                f"threshold will work, and the values can be read off directly."
            )

        # An order-level measure broken down by an item-level attribute counts
        # each order once per matching line. Where the semantic layer declares
        # an item-grain counterpart the plan builder substitutes it; where it
        # does not — an average or a rate over order totals — there is nothing
        # correct to compute, and the honest answer is to say so rather than
        # return an inflated number that looks ordinary.
        if (metric.resolution == Resolution.RESOLVED and metric.chosen
                and dimension.resolution == Resolution.RESOLVED):
            metric_obj = next((m for m in METRICS if m.id == metric.chosen), None)
            tables = self._prospective_join_tables(metric, dimension)
            if metric_obj is not None and not self._survives_fan_out(metric_obj, tables):
                substitute = getattr(metric_obj, "item_grain_equivalent", "")
                if not substitute:
                    dim_obj = next(
                        (d for d in DIMENSIONS if d.id == dimension.chosen), None)
                    return self._fan_out_message(
                        metric_obj, dim_obj.label if dim_obj else "that attribute")

        # A listing anchored on a table that records no date cannot carry a
        # period. The compiler already refused this, correctly — filtering on
        # nothing would quietly widen the report to all of history — but it
        # refused by raising, one stage after the request had been accepted as
        # answerable. The benchmark therefore recorded id 41 ("items not sold
        # in the past 60 days with inventory below 5") as a pipeline crash
        # rather than the reasoned decline it actually was, and a crash is
        # counted as a fault against the system rather than the abstention
        # working. Same judgement, moved to the stage that can express it.
        if (pattern in LISTING_PATTERNS
                and (time_result.range is not None or time_term)
                and dimension.resolution == Resolution.RESOLVED
                and dimension.chosen):
            dim_obj = next((d for d in DIMENSIONS if d.id == dimension.chosen), None)
            if (dim_obj is not None
                    and dim_obj.binding_table in TABLE_DATE_FIELDS
                    and TABLE_DATE_FIELDS[dim_obj.binding_table] is None):
                return (
                    f"{dim_obj.label} records no date, so a listing of it "
                    f"cannot be limited to a period — there is no column to "
                    f"filter on. Applying no filter instead would silently "
                    f"widen the report to all of history, which is why this is "
                    f"declined rather than answered. The same question can be "
                    f"asked without the period, or asked about orders, which "
                    f"are dated."
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
        extra_bindings: Optional[Sequence[Binding]] = None,
    ) -> AnalysisPlan:
        metric_id = metric.chosen or "_none_"
        dimension_id = dimension.chosen

        metric_obj = next((m for m in METRICS if m.id == metric_id), None)
        dim_obj = (next((d for d in DIMENSIONS if d.id == dimension_id), None)
                   if dimension_id else None)

        join_tables: Set[str] = set()
        for obj in (metric_obj, dim_obj):
            if obj is not None:
                join_tables.add(obj.binding_table)
                join_tables.update(obj.required_joins)

        metric_id, metric_obj, grain_note = self._resolve_grain(
            metric_obj, join_tables
        )
        if metric_obj:
            join_tables.add(metric_obj.binding_table)
            join_tables.update(metric_obj.required_joins)

        # Additional summary measures: keep declaration order, drop duplicates.
        #
        # A secondary measure may widen the join path, and widening it can
        # invalidate a measure already admitted — "average order value and
        # units sold, by status" reaches OrderItem only through the second
        # measure, and the average is then taken over order rows duplicated per
        # line. The old code accumulated the join set as it went, so the
        # primary had already been cleared against a narrower path and nothing
        # rechecked it: the compiler emitted a line-count-weighted average with
        # neither a note nor a refusal. Each candidate is now tested against the
        # path it would create, and admitted only if every measure already in
        # the plan still survives it.
        admitted: List[Any] = []
        extra_metric_ids: List[str] = []
        if metric_obj is not None:
            admitted.append(metric_obj)
        for binding in extra_bindings or []:
            if binding.resolution is not Resolution.RESOLVED or not binding.chosen:
                # Dropping this silently would answer a narrower question than
                # the one asked and say nothing about it — the exact failure
                # this pipeline exists to rule out, and what the comment above
                # already promised not to do.
                named = binding.term or "one of the measures requested"
                grain_note = (grain_note + " " if grain_note else "") + (
                    f"'{named}' could not be matched to an approved measure, "
                    f"so it is not included."
                )
                continue
            candidate = next(
                (m for m in METRICS if m.id == binding.chosen), None)
            if candidate is None:
                continue
            widened = set(join_tables)
            widened.add(candidate.binding_table)
            widened.update(candidate.required_joins)

            resolved_id, extra_obj, extra_note = self._resolve_grain(
                candidate, widened)
            if extra_obj is None:
                continue
            widened.add(extra_obj.binding_table)
            widened.update(extra_obj.required_joins)

            # Same fan-out rule as the primary measure, applied to the whole
            # plan: the candidate must survive the path it creates, and so must
            # everything already in. Otherwise the guard would protect the first
            # measure of a summary and quietly leave the rest multiplied by the
            # item-level join — an average over order totals repeated once per
            # line item, sitting in the same row as a correctly-grained one.
            casualty = next(
                (m for m in admitted + [extra_obj]
                 if not self._survives_fan_out(m, widened)), None)
            if casualty is not None:
                grain_note = (grain_note + " " if grain_note else "") + (
                    f"{extra_obj.label} is measured per line item, and "
                    f"including it would split each order across its lines, "
                    f"so {casualty.label} would no longer be correct. "
                    f"{extra_obj.label} is not included."
                    if casualty is not extra_obj else
                    f"{extra_obj.label} is measured per order and cannot be "
                    f"attributed to this breakdown, so it is not included."
                )
                continue
            if resolved_id == metric_id or resolved_id in extra_metric_ids:
                continue
            extra_metric_ids.append(resolved_id)
            admitted.append(extra_obj)
            join_tables = widened
            if extra_note:
                grain_note = (grain_note + " " if grain_note else "") + extra_note

        return AnalysisPlan(
            pattern=pattern,
            metric=metric_id,
            extra_metrics=extra_metric_ids,
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
    def _prospective_join_tables(metric_binding, dimension_binding) -> Set[str]:
        """Tables the primary measure and the breakdown alone would need.

        Computed before the plan is built so the fan-out check can run in the
        rejection path, where an unanswerable request becomes a reasoned
        refusal rather than a raised exception.

        Additional summary measures are deliberately *not* counted here. A
        request is only unanswerable if the breakdown itself defeats the
        measure that was asked for; where a secondary measure is what drags in
        the item-level join, the plan builder drops that measure and reports
        it, which answers the question that was asked instead of refusing it.
        """
        tables: Set[str] = set()
        for binding, catalogue in ((metric_binding, METRICS),
                                   (dimension_binding, DIMENSIONS)):
            if binding.resolution is not Resolution.RESOLVED or not binding.chosen:
                continue
            obj = next((o for o in catalogue if o.id == binding.chosen), None)
            if obj:
                tables.add(obj.binding_table)
                tables.update(obj.required_joins)
        return tables

    @staticmethod
    def _fan_out_message(metric_obj, dimension_label: str) -> str:
        return (
            f"{metric_obj.label} is measured per order, and grouping by "
            f"{dimension_label} splits each order across its line items. "
            f"Reporting it that way would count one order once per matching "
            f"line and inflate the figure, so it is declined rather than "
            f"answered. Measures defined at line-item level can be broken down "
            f"this way, and {metric_obj.label} can be reported without the "
            f"breakdown or grouped by an order-level attribute such as status "
            f"or country."
        )

    @staticmethod
    def _survives_fan_out(metric_obj, join_tables: Set[str]) -> bool:
        """Whether this measure is still correct across a fan-out join.

        An order-grain aggregate over a join that multiplies order rows counts
        each order once per matching line — unless the aggregate collapses the
        duplicates itself. `COUNT(DISTINCT o.Id)` does; `AVG(o.OrderTotal)`
        does not, and there is no item-level counterpart to substitute for it,
        because an order total genuinely does not belong to any one of the
        order's lines.
        """
        if metric_obj.binding_table not in ORDER_GRAIN_TABLES:
            return True
        if not (join_tables & FAN_OUT_TABLES):
            return True
        return bool(re.match(r"^\s*COUNT\s*\(\s*DISTINCT\b",
                             metric_obj.sql_expr, re.IGNORECASE))

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
            final_filters.append(self._ground_filter_field(f))
        return final_filters

    def _ground_filter_field(self, f: Filter) -> Filter:
        """Rewrite a filter's field to the approved id it names.

        Filter fields were matched against exact semantic-layer ids while
        metric and dimension *terms* went through the grounding engine, so the
        two halves of the same vocabulary disagreed about what counted as
        approved. The model would return `field="quantity"` — which grounds
        cleanly to `item_quantity` in any other slot — and the compiler raised
        `UnknownFilterFieldError`, surfacing to the user as a crash on a
        request the layer can express perfectly well.

        Grounding here means a filter field is resolved by the same evidence as
        every other term. A field that genuinely cannot be bound is left alone
        and reported by `_unbindable_filter_fields`, which turns it into a
        reasoned refusal rather than an exception from three stages down.
        """
        name = str(f.field)
        if (name == PREDICATE_FIELD
                or any(m.id == name for m in METRICS)
                or any(d.id == name for d in DIMENSIONS)
                or name in ALIAS_TO_TABLE):
            return f
        for slot in ("dimension", "metric"):
            binding = self.engine.ground(name, slot)
            if binding.resolution is Resolution.RESOLVED and binding.chosen:
                logger.info("Grounded filter field %r to %s", name, binding.chosen)
                return f.model_copy(update={"field": binding.chosen})
        return f

    def _unbindable_filter_fields(self, filters, grounded: bool = False) -> List[str]:
        """Filter fields that name nothing the semantic layer can express."""
        unbindable: List[str] = []
        candidates = (list(filters or []) if grounded
                      else self._apply_business_logic_filters(list(filters or [])))
        for f in candidates:
            name = str(f.field)
            if (name == PREDICATE_FIELD
                    or any(m.id == name for m in METRICS)
                    or any(d.id == name for d in DIMENSIONS)
                    or name in ALIAS_TO_TABLE):
                continue
            unbindable.append(name)
        return unbindable

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
