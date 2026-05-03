"""
SafeDash Widget Persistence Engine.

Manages the lifecycle of dashboard widgets as first-class queryable artifacts.
Each widget stores its canonical analysis plan, compiled SQL template hash,
visualization specification, access control scope, and refresh metadata.

Supports similarity-based retrieval to surface existing widgets for recurring
queries — directly addressing the formative study finding that 61% of
institutional reporting requests are recurrences.
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from .models import AnalysisPlan
from .visualization import VisualizationSpec

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Widget data model
# ---------------------------------------------------------------------------

class Widget:
    """
    A first-class stored analytics artifact.

    Attributes:
        widget_id:      Unique identifier (SHA-256 of canonical plan).
        original_query: The natural-language request that created this widget.
        plan:           The canonical AnalysisPlan (JSON-serializable).
        sql_hash:       SHA-256 hash of the compiled SQL template.
        compiled_sql:   The actual compiled SQL string.
        visualization:  The VisualizationSpec for rendering.
        created_at:     ISO-8601 creation timestamp.
        updated_at:     ISO-8601 last-update timestamp.
        access_scope:   Role or user scope for permission enforcement.
        run_history:    List of execution timestamps (for refresh tracking).
        tags:           User- or system-assigned tags for retrieval.
    """

    def __init__(
        self,
        original_query: str,
        plan: AnalysisPlan,
        compiled_sql: str,
        visualization: VisualizationSpec,
        access_scope: str = "public",
        tags: Optional[List[str]] = None,
        sql_params: Optional[Dict[str, Any]] = None,
    ):
        self.plan = plan
        self.original_query = original_query
        self.compiled_sql = compiled_sql
        self.sql_params = sql_params or {}
        self.visualization = visualization
        self.access_scope = access_scope
        self.tags = tags or []

        # Derived fields
        self.widget_id = self._compute_id(plan)
        self.sql_hash = hashlib.sha256(compiled_sql.encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat()
        self.created_at = now
        self.updated_at = now
        self.run_history: List[str] = [now]

    @staticmethod
    def _compute_id(plan: AnalysisPlan) -> str:
        """Compute a deterministic widget ID from the canonical plan."""
        canonical = json.dumps(plan.model_dump(), sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def record_execution(self) -> None:
        """Record a new execution in the run history."""
        now = datetime.now(timezone.utc).isoformat()
        self.run_history.append(now)
        self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the widget to a dictionary for storage."""
        return {
            "widget_id": self.widget_id,
            "original_query": self.original_query,
            "plan": self.plan.model_dump(),
            "sql_hash": self.sql_hash,
            "compiled_sql": self.compiled_sql,
            "sql_params": self.sql_params,
            "visualization": self.visualization.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_scope": self.access_scope,
            "run_history": self.run_history,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Widget":
        """Deserialize a widget from a stored dictionary."""
        plan = AnalysisPlan(**data["plan"])
        vis = VisualizationSpec(**data["visualization"])
        widget = cls(
            original_query=data["original_query"],
            plan=plan,
            compiled_sql=data["compiled_sql"],
            visualization=vis,
            access_scope=data.get("access_scope", "public"),
            tags=data.get("tags", []),
            sql_params=data.get("sql_params", {}),
        )
        widget.widget_id = data["widget_id"]
        widget.sql_hash = data["sql_hash"]
        widget.created_at = data["created_at"]
        widget.updated_at = data["updated_at"]
        widget.run_history = data.get("run_history", [])
        return widget


# ---------------------------------------------------------------------------
# Widget Registry — in-memory + file-based persistence
# ---------------------------------------------------------------------------

class WidgetRegistry:
    """
    Manages widget storage, retrieval, and similarity-based deduplication.

    Storage: JSON file on disk (production would use JSONB columns in
    PostgreSQL or a document store). The file path is configurable.

    Similarity: Two plans are considered similar if they share the same
    pattern, metric, and dimension — differing only in time rules, filters,
    or limits. This directly addresses the formative study finding that
    61% of institutional reporting requests are recurrences.
    """

    def __init__(self, storage_path: str = "widgets.json"):
        self._storage_path = storage_path
        self._widgets: Dict[str, Widget] = {}
        self._load()

    # --- Public API ---

    def register(self, widget: Widget) -> Widget:
        """
        Register a new widget or return an existing similar one.

        If a structurally similar widget already exists (same pattern,
        metric, dimension), the existing widget is returned and its
        run history is updated. Otherwise, the new widget is stored.
        """
        # Check for structural similarity first
        similar = self.find_similar(widget.plan)
        if similar:
            logger.info(
                f"Found similar widget '{similar.widget_id}' for query "
                f"'{widget.original_query[:50]}...'. Reusing."
            )
            similar.record_execution()
            self._save()
            return similar

        # Store the new widget
        self._widgets[widget.widget_id] = widget
        self._save()
        logger.info(
            f"Registered new widget '{widget.widget_id}' for query "
            f"'{widget.original_query[:50]}...'"
        )
        return widget

    def get(self, widget_id: str) -> Optional[Widget]:
        """Retrieve a widget by its ID."""
        return self._widgets.get(widget_id)

    def find_similar(self, plan: AnalysisPlan) -> Optional[Widget]:
        """
        Find a structurally similar widget in the registry.

        Similarity criteria: same pattern + same metric + same dimension.
        Time rules, filters, and limits may differ.
        """
        for widget in self._widgets.values():
            if self._is_structurally_similar(widget.plan, plan):
                return widget
        return None

    def list_all(self, access_scope: Optional[str] = None) -> List[Widget]:
        """List all widgets, optionally filtered by access scope."""
        widgets = list(self._widgets.values())
        if access_scope:
            widgets = [w for w in widgets if w.access_scope == access_scope]
        return sorted(widgets, key=lambda w: w.updated_at, reverse=True)

    def delete(self, widget_id: str) -> bool:
        """Delete a widget by ID."""
        if widget_id in self._widgets:
            del self._widgets[widget_id]
            self._save()
            logger.info(f"Deleted widget '{widget_id}'")
            return True
        return False

    def search_by_query(self, query: str) -> List[Widget]:
        """
        Search widgets by original query text (substring match).
        In production, this would use full-text search or embeddings.
        """
        query_lower = query.lower()
        return [
            w for w in self._widgets.values()
            if query_lower in w.original_query.lower()
        ]

    @property
    def count(self) -> int:
        """Return the total number of stored widgets."""
        return len(self._widgets)

    # --- Similarity Logic ---

    @staticmethod
    def _is_structurally_similar(
        plan_a: AnalysisPlan, plan_b: AnalysisPlan
    ) -> bool:
        """
        Two plans are structurally similar if they share the same
        pattern, metric, and dimension.
        """
        return (
            plan_a.pattern == plan_b.pattern
            and plan_a.metric == plan_b.metric
            and plan_a.dimension == plan_b.dimension
        )

    # --- Persistence ---

    def _save(self) -> None:
        """Persist the widget registry to disk."""
        data = {
            wid: widget.to_dict()
            for wid, widget in self._widgets.items()
        }
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Failed to save widget registry: {e}")

    def _load(self) -> None:
        """Load the widget registry from disk."""
        if not os.path.exists(self._storage_path):
            logger.info(f"No widget registry found at '{self._storage_path}'. Starting fresh.")
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for wid, widget_data in data.items():
                self._widgets[wid] = Widget.from_dict(widget_data)
            logger.info(f"Loaded {len(self._widgets)} widgets from registry.")
        except (IOError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load widget registry: {e}. Starting fresh.")
            self._widgets = {}


# ---------------------------------------------------------------------------
# Dashboard Composer — assembles widgets into a dashboard layout
# ---------------------------------------------------------------------------

class DashboardComposer:
    """
    Composes registered widgets into a dashboard layout specification.

    The layout is a JSON-serializable structure that frontend frameworks
    (React, Vue, etc.) can render into a grid-based dashboard.
    """

    # Default grid settings
    GRID_COLUMNS = 12
    WIDGET_SIZES = {
        "kpi_card":     {"cols": 3, "rows": 1},
        "kpi_grid":     {"cols": 12, "rows": 2},
        "bar_chart":    {"cols": 6, "rows": 3},
        "line_chart":   {"cols": 6, "rows": 3},
        "grouped_bar":  {"cols": 6, "rows": 3},
        "pie_chart":    {"cols": 4, "rows": 3},
        "table":        {"cols": 12, "rows": 4},
        "scatter_plot": {"cols": 6, "rows": 3},
        "funnel_chart": {"cols": 6, "rows": 3},
    }

    def compose(
        self,
        widgets: List[Widget],
        title: str = "SafeDash Dashboard",
    ) -> Dict[str, Any]:
        """
        Compose a list of widgets into a dashboard layout.

        Returns a JSON-serializable dashboard specification.
        """
        layout_items = []
        current_row = 0
        current_col = 0

        for widget in widgets:
            chart_type = widget.visualization.chart_type
            size = self.WIDGET_SIZES.get(chart_type, {"cols": 6, "rows": 3})

            # Wrap to next row if needed
            if current_col + size["cols"] > self.GRID_COLUMNS:
                current_row += 1
                current_col = 0

            layout_items.append({
                "widget_id": widget.widget_id,
                "title": widget.visualization.title,
                "chart_type": chart_type,
                "grid_position": {
                    "col": current_col,
                    "row": current_row,
                    "cols": size["cols"],
                    "rows": size["rows"],
                },
                "visualization": widget.visualization.to_dict(),
                "sql_hash": widget.sql_hash,
                "last_updated": widget.updated_at,
            })

            current_col += size["cols"]

        return {
            "title": title,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "grid_columns": self.GRID_COLUMNS,
            "widgets": layout_items,
            "total_widgets": len(layout_items),
        }
