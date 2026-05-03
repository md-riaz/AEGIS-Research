"""
SafeDash Visualization Selector Module.

Policy-driven visualization selection based on intent class, result shape,
and data characteristics. Charts are chosen by rule, not by the model.
"""

import logging
from typing import Optional, Dict, Any, List
from .models import AnalysisPlan

logger = logging.getLogger(__name__)


class VisualizationSpec:
    """
    A concrete visualization specification that can be rendered by any
    charting library (Chart.js, ECharts, Plotly, etc.).
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
    ):
        self.chart_type = chart_type
        self.title = title
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.series_key = series_key
        self.color_scheme = color_scheme
        self.options = options or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_type": self.chart_type,
            "title": self.title,
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "series_key": self.series_key,
            "color_scheme": self.color_scheme,
            "options": self.options,
        }


# ---------------------------------------------------------------------------
# Policy tables — these are the "rules" that replace model-driven chart choice
# ---------------------------------------------------------------------------

# Primary mapping: intent class → default chart type
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
    "point_lookup": "table",
}

# Override rules based on result shape (cardinality thresholds)
CARDINALITY_OVERRIDES: Dict[str, Dict[str, str]] = {
    "bar_chart": {
        "high_cardinality": "table",       # > 20 categories → table
        "single_value": "kpi_card",         # 1 value → KPI card
    },
    "pie_chart": {
        "high_cardinality": "bar_chart",    # > 8 slices → bar chart
    },
    "grouped_bar": {
        "high_cardinality": "table",        # > 4 groups × 20 categories → table
    },
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


class VisualizationSelector:
    """
    Rule-based visualization selector.

    Selects the appropriate chart type based on:
    1. The analysis plan's intent class (primary rule)
    2. Result cardinality (override rules)
    3. Data type of the dimension (categorical vs. temporal)

    This is a deterministic component — the LLM has no influence on chart
    selection. This ensures visual consistency: the same plan always produces
    the same visualization type.
    """

    def select(
        self,
        plan: AnalysisPlan,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None,
    ) -> VisualizationSpec:
        """
        Select a visualization specification for the given analysis plan.

        Args:
            plan: The grounded analysis plan from the semantic mapper.
            row_count: Optional actual row count from query execution.
            column_count: Optional actual column count.

        Returns:
            A VisualizationSpec ready for frontend rendering.
        """
        # 1. Start with the intent-class default
        chart_type = INTENT_VISUAL_POLICY.get(plan.pattern, "table")

        # 2. Apply the plan's visual field if it was explicitly set
        if plan.visual and plan.visual != chart_type:
            logger.debug(
                f"Plan visual '{plan.visual}' differs from policy '{chart_type}'; "
                f"using plan visual."
            )
            chart_type = plan.visual

        # 3. Apply cardinality overrides if we have result shape info
        if row_count is not None:
            chart_type = self._apply_cardinality_rules(
                chart_type, row_count, column_count
            )

        # 4. Build the visualization specification
        title = self._generate_title(plan)
        x_axis, y_axis = self._infer_axes(plan, chart_type)
        color_scheme = self._select_color_scheme(plan)

        spec = VisualizationSpec(
            chart_type=chart_type,
            title=title,
            x_axis=x_axis,
            y_axis=y_axis,
            series_key=plan.dimension,
            color_scheme=color_scheme,
            options=self._build_chart_options(chart_type, plan),
        )

        logger.info(
            f"Selected visualization: {chart_type} for pattern '{plan.pattern}'"
        )
        return spec

    def _apply_cardinality_rules(
        self, chart_type: str, row_count: int, column_count: Optional[int]
    ) -> str:
        """Apply cardinality-based overrides to the chart type."""
        overrides = CARDINALITY_OVERRIDES.get(chart_type, {})

        if row_count == 1 and "single_value" in overrides:
            logger.debug(f"Cardinality override: single value → {overrides['single_value']}")
            return overrides["single_value"]

        if row_count > 20 and "high_cardinality" in overrides:
            logger.debug(
                f"Cardinality override: {row_count} rows → {overrides['high_cardinality']}"
            )
            return overrides["high_cardinality"]

        if chart_type == "pie_chart" and row_count > 8:
            logger.debug("Cardinality override: too many pie slices → bar_chart")
            return "bar_chart"

        return chart_type

    def _generate_title(self, plan: AnalysisPlan) -> str:
        """Generate a human-readable title from the analysis plan."""
        metric_label = plan.metric.replace("_", " ").title()

        if plan.pattern == "kpi":
            return f"Total {metric_label}"
        elif plan.pattern == "ranking":
            limit = plan.limit or 10
            dim_label = (plan.dimension or "items").replace("_", " ").title()
            return f"Top {limit} {dim_label} by {metric_label}"
        elif plan.pattern == "trend":
            return f"{metric_label} Over Time"
        elif plan.pattern == "comparison":
            dim_label = (plan.dimension or "groups").replace("_", " ").title()
            return f"{metric_label} by {dim_label}"
        elif plan.pattern == "exception":
            return f"{metric_label} — Exception Report"
        elif plan.pattern == "summary":
            return f"{metric_label} Summary"
        elif plan.pattern == "segment":
            dim_label = (plan.dimension or "segment").replace("_", " ").title()
            return f"{metric_label} by {dim_label}"
        else:
            return f"{metric_label} Analysis"

    def _infer_axes(self, plan: AnalysisPlan, chart_type: str):
        """Infer x and y axis labels based on the chart type and plan."""
        metric_label = plan.metric.replace("_", " ").title()
        dim_label = (plan.dimension or "").replace("_", " ").title() if plan.dimension else None

        if chart_type in ("bar_chart", "grouped_bar"):
            return dim_label, metric_label
        elif chart_type == "line_chart":
            return "Date", metric_label
        elif chart_type == "scatter_plot":
            return dim_label or "X", metric_label
        else:
            return None, None

    def _select_color_scheme(self, plan: AnalysisPlan) -> str:
        """Select a color scheme based on the plan context."""
        if plan.pattern in ("exception",):
            return "warm"
        elif plan.pattern in ("trend", "kpi"):
            return "cool"
        return "default"

    def _build_chart_options(
        self, chart_type: str, plan: AnalysisPlan
    ) -> Dict[str, Any]:
        """Build chart-specific rendering options."""
        options: Dict[str, Any] = {}

        if chart_type == "bar_chart":
            options["orientation"] = "horizontal"
            options["sort_by_value"] = True
        elif chart_type == "line_chart":
            options["show_points"] = True
            options["fill_area"] = False
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

        return options
