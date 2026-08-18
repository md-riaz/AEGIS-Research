"""
AEGIS Visualization Selector — encoding chosen from data, with a pruning trail.

Why this stage was rebuilt
--------------------------
The original selector mapped ``intent_class`` to a chart-type string through an
eleven-entry dictionary, with three cardinality overrides bolted on.  It never
consulted the dimension's declared datatype, the metric's aggregation
semantics, or the shape of the result.  Consequently a pie chart of fifty
categories, a line chart over a nominal axis, and an *average* rendered as pie
slices were all "successfully generated" — structurally valid, semantically
indefensible.

That gap matters for the thesis specifically.  AEGIS positions itself in the
NL2VIS line (nvBench/ncNet, NL4DV, DataTone, DeepEye) but inherited none of its
mechanics:

* those systems emit an explicit **visualization specification** (Vega-Lite) as
  the target artifact, not a chart-type string — which is what makes an output
  comparable, portable, and checkable by anyone else;
* they select encodings from **data characteristics**, not from task type alone;
* nvBench prunes bad charts with a learned model (DeepEye) before a human ever
  sees them, treating "this chart is unreadable" as a first-class outcome.

This module supplies all three deterministically.  It emits a Vega-Lite v5
spec, derives encodings from the semantic layer's declared datatypes plus the
observed result shape, and records **every candidate it rejected and why** in
``VisualizationSpec.rejected``.  The pruning trail is deliberately part of the
output rather than a log line: a Approved analytics system should be able to
show why it drew what it drew.

Chart selection remains fully deterministic.  The LLM has no influence here —
the same plan and the same result shape always produce the same encoding.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from .models import AnalysisPlan
from .semantic_layer import DIMENSIONS, MATRIX_SUMMARIES, METRICS

logger = logging.getLogger(__name__)


class VisualizationSpec:
    """A concrete visualization specification.

    Carries both the renderer-agnostic fields the AEGIS frontend consumes
    (``chart_type``, axes, options) and a standard Vega-Lite specification, so
    the same widget can be rendered by Chart.js, ECharts, or any Vega-Lite
    runtime — and so the output is directly comparable with the NL2VIS
    literature, which uses Vega-Lite as its interchange format.
    """

    def __init__(
        self,
        chart_type: str,
        title: str,
        x_axis: Optional[str] = None,
        y_axis: Optional[str] = None,
        series_key: Optional[str] = None,
        color_scheme: str = "default",
        options: Optional[Dict[str, Any]] = None,
        vega_lite: Optional[Dict[str, Any]] = None,
        encoding_rationale: Optional[List[str]] = None,
        rejected: Optional[List[Dict[str, str]]] = None,
    ):
        self.chart_type = chart_type
        self.title = title
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.series_key = series_key
        self.color_scheme = color_scheme
        self.options = options or {}
        self.vega_lite = vega_lite or {}
        self.encoding_rationale = encoding_rationale or []
        self.rejected = rejected or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_type": self.chart_type,
            "title": self.title,
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "series_key": self.series_key,
            "color_scheme": self.color_scheme,
            "options": self.options,
            "vega_lite": self.vega_lite,
            "encoding_rationale": self.encoding_rationale,
            "rejected": self.rejected,
        }


# ---------------------------------------------------------------------------
# Policy tables
# ---------------------------------------------------------------------------

#: Starting point only — the validity rules below may override any of these
#: once the dimension's datatype and the result shape are known.
INTENT_VISUAL_POLICY: Dict[str, str] = {
    "kpi":        "kpi_card",
    "ranking":    "bar_chart",
    "trend":      "line_chart",
    "comparison": "grouped_bar",
    "exception":  "table",
    "summary":    "kpi_grid",
    "segment":    "pie_chart",
    "funnel":     "funnel_chart",
    "cohort":     "grouped_bar",
    "correlate":  "scatter_plot",
    "tabular":    "table",
}

#: Above this many categories a categorical chart stops being readable and the
#: data is better served as a sortable table.  nvBench applies the same idea
#: through DeepEye's learned filter; the threshold here is explicit so it can
#: be argued with and tuned per deployment.
MAX_CATEGORIES_FOR_CHART = 20

#: Pie and donut charts encode part-to-whole. Beyond a handful of slices the
#: angular comparison becomes guesswork.
MAX_PIE_SLICES = 8
MIN_PIE_SLICES = 2

#: Semantic-layer datatype → Vega-Lite encoding type.
VEGA_TYPE_BY_DATATYPE: Dict[str, str] = {
    "string": "nominal",
    "number": "quantitative",
    "date": "temporal",
}

#: Time grain → Vega-Lite ``timeUnit``, so a monthly trend bins by month rather
#: than plotting every raw timestamp.
VEGA_TIME_UNIT_BY_GRAIN: Dict[str, str] = {
    "hour": "yearmonthdatehours",
    "day": "yearmonthdate",
    "week": "yearweek",
    "month": "yearmonth",
    "quarter": "yearquarter",
    "year": "year",
}

#: Chart type → Vega-Lite mark.
VEGA_MARK_BY_CHART: Dict[str, Any] = {
    "bar_chart": "bar",
    "grouped_bar": "bar",
    "line_chart": {"type": "line", "point": True},
    "area_chart": "area",
    "pie_chart": {"type": "arc", "innerRadius": 0},
    "scatter_plot": "point",
    "funnel_chart": "bar",
    "table": "text",
    "kpi_card": "text",
    "kpi_grid": "text",
}

# Chart.js-compatible color palettes
COLOR_SCHEMES: Dict[str, List[str]] = {
    "default": [
        "#4F46E5", "#7C3AED", "#EC4899", "#F59E0B",
        "#10B981", "#3B82F6", "#EF4444", "#8B5CF6",
    ],
    "warm": [
        "#F59E0B", "#EF4444", "#EC4899", "#F97316",
        "#DC2626", "#DB2777", "#EA580C", "#E11D48",
    ],
    "cool": [
        "#3B82F6", "#10B981", "#06B6D4", "#4F46E5",
        "#059669", "#0891B2", "#4338CA", "#047857",
    ],
    "monochrome": [
        "#1E293B", "#334155", "#475569", "#64748B",
        "#94A3B8", "#CBD5E1", "#E2E8F0", "#F1F5F9",
    ],
}

#: Retained for backwards compatibility; the validity rules supersede it.
CARDINALITY_OVERRIDES: Dict[str, Dict[str, str]] = {
    "bar_chart": {"high_cardinality": "table", "single_value": "kpi_card"},
    "pie_chart": {"high_cardinality": "bar_chart"},
    "grouped_bar": {"high_cardinality": "table"},
}


class VisualizationSelector:
    """Rule-based selector that validates an encoding before emitting it.

    Selection proceeds in two passes.  The first proposes a chart from the
    analysis pattern.  The second tests that proposal against the data it would
    actually be drawn from and downgrades it when a rule fails, recording the
    rejection.  A downgrade is always to a strictly safer encoding — bar before
    pie, table before bar — so the pass terminates.
    """

    def select(
        self,
        plan: AnalysisPlan,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None,
    ) -> VisualizationSpec:
        """Select and validate a visualization for ``plan``.

        Args:
            plan: The grounded analysis plan from the semantic resolver.
            row_count: Observed row count from execution, when available.  With
                it the selector can apply cardinality rules; without it, it
                reasons from the plan alone and says so in the rationale.
            column_count: Observed column count, when available.

        Returns:
            A :class:`VisualizationSpec` including a Vega-Lite specification,
            the rules that fired, and every encoding that was pruned.
        """
        rationale: List[str] = []
        rejected: List[Dict[str, str]] = []

        dimension = self._dimension(plan)
        metric = self._metric(plan)
        dim_type = self._vega_type(dimension)

        proposed = plan.visual or INTENT_VISUAL_POLICY.get(plan.pattern, "table")
        rationale.append(
            f"Pattern '{plan.pattern}' proposes {proposed}."
        )
        if row_count is None:
            rationale.append(
                "No observed result shape available; cardinality rules were "
                "evaluated from the plan only."
            )

        chart_type = self._validate(
            proposed, plan, dimension, metric, dim_type,
            row_count, rationale, rejected,
        )

        if plan.matrix_summary and plan.matrix_summary in MATRIX_SUMMARIES:
            title = MATRIX_SUMMARIES[plan.matrix_summary].label
        else:
            title = self._generate_title(plan, metric, dimension)
        x_axis, y_axis = self._infer_axes(plan, chart_type, metric, dimension)

        spec = VisualizationSpec(
            chart_type=chart_type,
            title=title,
            x_axis=x_axis,
            y_axis=y_axis,
            series_key=plan.dimension,
            color_scheme=self._select_color_scheme(plan),
            options=self._build_chart_options(chart_type, plan),
            vega_lite=self._build_vega_lite(
                chart_type, plan, metric, dimension, dim_type, title
            ),
            encoding_rationale=rationale,
            rejected=rejected,
        )
        if plan.matrix_summary:
            spec.options.update({
                "layout": "matrix_summary",
                "number_format": "currency",
                "compact": False,
                "explain_label": (
                    "Approved semantic-layer matrix; values are period order "
                    "totals grouped by status."
                ),
            })

        logger.info(
            "Selected %s for pattern '%s' (%d encoding(s) pruned)",
            chart_type, plan.pattern, len(rejected),
        )
        return spec

    # ------------------------------------------------------------------
    # Validity rules
    # ------------------------------------------------------------------

    def _validate(
        self,
        chart_type: str,
        plan: AnalysisPlan,
        dimension,
        metric,
        dim_type: Optional[str],
        row_count: Optional[int],
        rationale: List[str],
        rejected: List[Dict[str, str]],
    ) -> str:
        """Downgrade ``chart_type`` until every validity rule passes."""

        def reject(current: str, replacement: str, reason: str) -> str:
            rejected.append({"chart_type": current, "reason": reason})
            rationale.append(f"{current} → {replacement}: {reason}")
            return replacement

        # R1 — A single scalar is a number, not a chart.
        if row_count == 1 and chart_type not in ("kpi_card", "table", "kpi_grid"):
            chart_type = reject(
                chart_type, "kpi_card",
                "the result is a single value, which no categorical or "
                "temporal encoding can convey",
            )

        # R2 — A grouping chart needs something to group by.
        if chart_type in ("bar_chart", "pie_chart", "grouped_bar", "line_chart",
                          "area_chart", "scatter_plot") and plan.dimension is None:
            chart_type = reject(
                chart_type, "kpi_card",
                "no dimension is bound, so there is no axis to encode",
            )

        # R3 — Temporal data belongs on a line; pie cannot express order.
        if dim_type == "temporal" and chart_type in ("pie_chart",):
            chart_type = reject(
                chart_type, "line_chart",
                "the dimension is temporal and a pie chart discards ordering",
            )

        # R4 — Pie charts need a part-to-whole reading.  An average or a rate
        #      does not sum to a meaningful total, so slices would be a lie
        #      even when the slice count is reasonable.
        if chart_type == "pie_chart" and not self._is_additive(metric):
            label = metric.label if metric else plan.metric
            chart_type = reject(
                chart_type, "bar_chart",
                f"'{label}' is not additively decomposable, so its parts do "
                f"not sum to a whole",
            )

        # R5 — Pie slice count.
        if chart_type == "pie_chart" and row_count is not None:
            if row_count > MAX_PIE_SLICES:
                chart_type = reject(
                    chart_type, "bar_chart",
                    f"{row_count} slices exceeds the {MAX_PIE_SLICES}-slice "
                    f"limit for readable angular comparison",
                )
            elif row_count < MIN_PIE_SLICES:
                chart_type = reject(
                    chart_type, "kpi_card",
                    "a part-to-whole chart needs at least two parts",
                )

        # R6 — Scatter plots need two quantitative fields.
        if chart_type == "scatter_plot" and dim_type != "quantitative":
            chart_type = reject(
                chart_type, "bar_chart",
                "a scatter plot needs two quantitative fields and the "
                "dimension is not quantitative",
            )

        # R7 — Grouped bars need a series to group.
        if chart_type == "grouped_bar" and plan.dimension is None:
            chart_type = reject(
                chart_type, "bar_chart",
                "no series key is available to group by",
            )

        # R8 — Categorical cardinality ceiling.
        if (
            row_count is not None
            and row_count > MAX_CATEGORIES_FOR_CHART
            and chart_type in ("bar_chart", "grouped_bar", "pie_chart")
        ):
            chart_type = reject(
                chart_type, "table",
                f"{row_count} categories exceeds the "
                f"{MAX_CATEGORIES_FOR_CHART}-category ceiling for a readable "
                f"categorical chart",
            )

        if not rejected:
            rationale.append(f"{chart_type} passed all validity rules.")
        return chart_type

    @staticmethod
    def _is_additive(metric) -> bool:
        """Whether a metric's parts sum to its whole.

        Sums and counts decompose additively; averages and ratios do not.  This
        is read from the metric's own SQL aggregate rather than from a hardcoded
        list, so a new metric inherits the correct behaviour automatically.
        """
        if metric is None:
            return False
        expr = metric.sql_expr.upper()
        if "AVG(" in expr:
            return False
        return "SUM(" in expr or "COUNT(" in expr

    # ------------------------------------------------------------------
    # Vega-Lite emission
    # ------------------------------------------------------------------

    def _build_vega_lite(
        self,
        chart_type: str,
        plan: AnalysisPlan,
        metric,
        dimension,
        dim_type: Optional[str],
        title: str,
    ) -> Dict[str, Any]:
        """Build a self-contained Vega-Lite v5 specification.

        The ``data`` block is left as a named source so the widget engine can
        bind the executed result set at render time without the spec having to
        embed the rows.
        """
        spec: Dict[str, Any] = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": title,
            "data": {"name": "widget_result"},
            "mark": VEGA_MARK_BY_CHART.get(chart_type, "bar"),
        }

        metric_field = metric.label if metric else "value"
        metric_encoding = {"field": metric_field, "type": "quantitative"}

        if chart_type in ("kpi_card", "kpi_grid"):
            spec["encoding"] = {"text": metric_encoding}
            return spec

        if chart_type == "table" or dimension is None:
            spec["encoding"] = {"text": metric_encoding}
            return spec

        dim_encoding: Dict[str, Any] = {
            "field": dimension.label,
            "type": dim_type or "nominal",
        }

        # Bin a temporal axis at the grain the user actually asked for, so a
        # "monthly revenue" request is not plotted per raw timestamp.
        #
        # An explicit granularity ("monthly") wins over the grain implied by a
        # window: "monthly revenue for last quarter" should bucket by month,
        # not by quarter. Only when no granularity was stated does the window's
        # own grain supply a sensible default.
        if dim_type == "temporal":
            grain = plan.time_grain
            if grain is None and plan.time_range is not None:
                grain = getattr(plan.time_range.grain, "value", plan.time_range.grain)
            time_unit = VEGA_TIME_UNIT_BY_GRAIN.get(str(grain)) if grain else None
            if time_unit:
                dim_encoding["timeUnit"] = time_unit

        if chart_type == "pie_chart":
            spec["encoding"] = {
                "theta": metric_encoding,
                "color": dim_encoding,
            }
            return spec

        if chart_type == "scatter_plot":
            spec["encoding"] = {"x": dim_encoding, "y": metric_encoding}
            return spec

        # Bar/line/area share the same x/y arrangement.
        if plan.sort and chart_type in ("bar_chart", "grouped_bar"):
            dim_encoding["sort"] = "-y" if plan.sort == "desc" else "y"

        spec["encoding"] = {"x": dim_encoding, "y": metric_encoding}
        if chart_type == "grouped_bar":
            spec["encoding"]["color"] = dict(dim_encoding)
            spec["encoding"]["xOffset"] = {"field": dimension.label}
        return spec

    # ------------------------------------------------------------------
    # Semantic layer lookups and labelling
    # ------------------------------------------------------------------

    @staticmethod
    def _metric(plan: AnalysisPlan):
        """The Metric object behind ``plan.metric``, or None for listings."""
        if not plan.metric or plan.metric == "_none_":
            return None
        return next((m for m in METRICS if m.id == plan.metric), None)

    @staticmethod
    def _dimension(plan: AnalysisPlan):
        """The Dimension object behind ``plan.dimension``, if any."""
        if not plan.dimension:
            return None
        return next((d for d in DIMENSIONS if d.id == plan.dimension), None)

    @staticmethod
    def _vega_type(dimension) -> Optional[str]:
        """Vega-Lite encoding type for a dimension's declared datatype."""
        if dimension is None:
            return None
        return VEGA_TYPE_BY_DATATYPE.get(dimension.datatype, "nominal")

    def _generate_title(self, plan: AnalysisPlan, metric, dimension) -> str:
        """Build a readable title from semantic-layer labels and the period.

        Labels come from the semantic layer rather than from title-casing the
        identifier, so a widget reads "Average Order Value", not
        "Avg Order Value".
        """
        metric_label = metric.label if metric else "Records"
        dim_label = dimension.label if dimension else None
        period = plan.time_range.label if plan.time_range else None

        if plan.pattern == "kpi":
            base = metric_label
        elif plan.pattern == "ranking":
            base = f"Top {plan.limit or 10} {dim_label or 'Items'} by {metric_label}"
        elif plan.pattern == "trend":
            base = f"{metric_label} Over Time"
        elif plan.pattern in ("comparison", "segment", "cohort"):
            base = f"{metric_label} by {dim_label}" if dim_label else metric_label
        elif plan.pattern == "exception":
            base = f"{metric_label} — Exception Report"
        elif plan.pattern == "summary":
            base = f"{metric_label} Summary"
        elif plan.pattern == "tabular":
            base = f"{dim_label or 'Records'} Listing"
        else:
            base = f"{metric_label} Analysis"

        return f"{base} — {period}" if period else base

    def _infer_axes(
        self, plan: AnalysisPlan, chart_type: str, metric, dimension
    ) -> Tuple[Optional[str], Optional[str]]:
        """Axis labels for renderers that do not consume the Vega-Lite spec."""
        metric_label = metric.label if metric else None
        dim_label = dimension.label if dimension else None

        if chart_type in ("bar_chart", "grouped_bar", "line_chart",
                          "area_chart", "scatter_plot"):
            return dim_label, metric_label
        return None, None

    def _select_color_scheme(self, plan: AnalysisPlan) -> str:
        """Select a palette from the plan's analytical context."""
        if plan.pattern == "exception":
            return "warm"
        if plan.pattern in ("trend", "kpi"):
            return "cool"
        return "default"

    def _build_chart_options(
        self, chart_type: str, plan: AnalysisPlan
    ) -> Dict[str, Any]:
        """Build renderer-specific options for the selected chart type."""
        options: Dict[str, Any] = {}

        if chart_type == "bar_chart":
            options["orientation"] = "horizontal"
            options["sort_by_value"] = True
        elif chart_type in ("line_chart", "area_chart"):
            options["show_points"] = True
            options["fill_area"] = chart_type == "area_chart"
            options["smooth"] = True
        elif chart_type == "pie_chart":
            options["show_legend"] = True
            options["show_percentages"] = True
        elif chart_type == "kpi_card":
            options["show_trend_arrow"] = True
            options["decimal_places"] = 2
        elif chart_type == "table":
            options["sortable"] = True
            options["pagination"] = True
            options["page_size"] = 25
        elif chart_type == "kpi_grid":
            options["columns"] = 3
            options["show_sparklines"] = True

        if plan.sort:
            options["default_sort"] = plan.sort
        if plan.time_range is not None:
            options["period_label"] = plan.time_range.label

        return options

    def _apply_cardinality_rules(
        self, chart_type: str, row_count: int, column_count: Optional[int] = None
    ) -> str:
        """Legacy cardinality override hook.

        .. deprecated::
            Superseded by the validity rules in :meth:`_validate`, which record
            why an encoding was pruned instead of silently swapping it.
            Retained so existing callers keep working.
        """
        overrides = CARDINALITY_OVERRIDES.get(chart_type, {})
        if row_count == 1 and "single_value" in overrides:
            return overrides["single_value"]
        if row_count > MAX_CATEGORIES_FOR_CHART and "high_cardinality" in overrides:
            return overrides["high_cardinality"]
        if chart_type == "pie_chart" and row_count > MAX_PIE_SLICES:
            return "bar_chart"
        return chart_type
