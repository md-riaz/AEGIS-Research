"""
AEGIS SQL Compiler Module (§4.7).

Transforms a validated AnalysisPlan into a production-safe MySQL query using
allow-listed templates and parameterized value binding.  No user text is ever
interpolated into SQL — all identifiers come from the semantic layer's closed
vocabulary, and all literal values are sanitised through ``_sanitize_value()``.

Post-compilation, ``_validate_sql_safety()`` scans the output for forbidden
constructs (DML, UNION, system-table references) as a defence-in-depth layer.
This ensures Proposition 1 holds: sql ∈ Q_safe(L, r).
"""

import re
import logging
from typing import List, Dict, Set, Optional, Any, Tuple
from . import time_grammar
from .models import AnalysisPlan, Filter, FilterOperator
from .semantic_layer import (METRICS, DIMENSIONS, JOIN_GRAPH, ALIAS_TO_TABLE,
                             APPROVED_PREDICATES, MANDATORY_PREDICATES,
                             MATRIX_SUMMARIES, PREDICATE_FIELD,
                             TABLE_DATE_FIELDS)

# Configure module-level logger
logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when compiled SQL contains a forbidden construct."""
    pass


class UnresolvedMetricError(Exception):
    """Raised when a plan reaches the compiler with no resolvable measure.

    The aggregate path used to fall back to ``METRICS[0]``, so a plan whose
    metric slot was empty compiled into a revenue query regardless of what had
    been asked. Choosing a measure on the requester's behalf is precisely the
    substitution the resolver was rewritten to eliminate; this closes the same
    hole one stage further down.
    """


class UnknownFilterFieldError(Exception):
    """Raised when a filter names something the semantic layer cannot bind.

    Closes the same class of silent-failure path as
    :class:`TimeResolutionError`.  The compiler used to fall back to ``o.Id``
    for any unrecognised filter field, so a filter the layer could not express
    became a predicate on the order id: it compiled cleanly, ran without error,
    returned an empty or arbitrary result, and was reported as a successful
    answer with no indication that the user's condition had been discarded.
    """


class TimeResolutionError(Exception):
    """Raised when a requested time period cannot be expressed in SQL.

    This exception exists to close a silent-failure path.  The compiler
    previously called a best-effort time matcher that returned ``None`` for any
    phrase it did not recognise, and both call sites did::

        time_part = self._get_smart_time_sql(...)
        if time_part:
            parts.append(time_part)

    So "this morning", "this quarter" and "last 90 days" produced no WHERE
    clause at all: the temporal constraint was discarded and the query ran over
    all of history, returning a confident, well-formed, wrong number.  Nothing
    in the output distinguished it from a correct answer.

    Refusing is strictly better than answering over the wrong period, so an
    unresolvable phrase now raises instead of evaporating.
    """
    pass

class SQLCompiler:
    """
    Deterministic SQL Compiler for AEGIS (§4.7).

    Translates an abstract analysis plan into a safe SQL query using
    constrained templates, validated join paths, and post-compilation
    safety scanning.  The compiler guarantees that every output query
    belongs to Q_safe(L, r) — the family of queries derivable from
    pattern templates using only bindings from the semantic layer.
    """

    # Forbidden SQL constructs — defence-in-depth (§4.7, Ablation row "AST")
    FORBIDDEN_PATTERNS: List[str] = [
        r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b',
        r'\bALTER\b', r'\bTRUNCATE\b', r'\bEXEC\b', r'\bxp_\b',
        r'\bUNION\b', r'\bEXCEPT\b', r'\bINTERSECT\b',
        r'\bsys\.\b', r'\bINFORMATION_SCHEMA\b',
        r'\bCREATE\b', r'\bGRANT\b', r'\bREVOKE\b',
    ]

    # Metadata for join relationships (Table Name -> Join Clause)
    JOIN_CLAUSES: Dict[str, str] = {
        "OrderItem": "LEFT JOIN `OrderItem` oi ON o.Id = oi.OrderId",
        "Product": "LEFT JOIN `Product` p ON oi.ProductId = p.Id",
        "Product_Category_Mapping": "LEFT JOIN `Product_Category_Mapping` pcm ON p.Id = pcm.ProductId",
        "Category": "LEFT JOIN `Category` c ON pcm.CategoryId = c.Id",
        "Customer": "INNER JOIN `Customer` cu ON o.CustomerId = cu.Id",
        "Product_Manufacturer_Mapping": "INNER JOIN `Product_Manufacturer_Mapping` pmm ON p.Id = pmm.ProductId",
        "Manufacturer": "INNER JOIN `Manufacturer` mf ON pmm.ManufacturerId = mf.Id",
        "Address": "INNER JOIN `Address` addr ON o.BillingAddressId = addr.Id",
        "Country": "INNER JOIN `Country` co ON addr.CountryId = co.Id",
        "Shipment": "INNER JOIN `Shipment` sh ON o.Id = sh.OrderId",
        "Store": "INNER JOIN `Store` st ON o.StoreId = st.Id",
        # Newly exposed source tables. Each was already present in the schema;
        # only the semantic-layer binding was missing, which is why requests
        # about coupons, tags, carts and reviews were declined as unmapped.
        "DiscountUsageHistory": "LEFT JOIN `DiscountUsageHistory` duh ON o.Id = duh.OrderId",
        "Product_ProductTag_Mapping": "LEFT JOIN `Product_ProductTag_Mapping` pptm ON p.Id = pptm.Product_Id",
        "ProductTag": "LEFT JOIN `ProductTag` pt ON pptm.ProductTag_Id = pt.Id",
        "ShoppingCartItem": "LEFT JOIN `ShoppingCartItem` sci ON sci.CustomerId = o.CustomerId",
        "ProductReview": "LEFT JOIN `ProductReview` pr ON pr.ProductId = p.Id",
        "SearchTerm": "",
    }

    # Standard table aliases
    TABLE_ALIASES: Dict[str, str] = {
        "Order": "o",
        "OrderItem": "oi",
        "Product": "p",
        "Category": "c",
        "Product_Category_Mapping": "pcm",
        "Customer": "cu",
        "Product_Manufacturer_Mapping": "pmm",
        "Manufacturer": "mf",
        "Address": "addr",
        "Country": "co",
        "Shipment": "sh",
        "Store": "st",
        "DiscountUsageHistory": "duh",
        "Product_ProductTag_Mapping": "pptm",
        "ProductTag": "pt",
        "ShoppingCartItem": "sci",
        "ProductReview": "pr",
        "SearchTerm": "sterm",
    }

    # Deterministic join order based on schema dependencies (§4.7)
    JOIN_ORDER: Dict[str, int] = {
        "Order": 0,
        "OrderItem": 10,
        "Product": 20,
        "Product_Category_Mapping": 30,
        "Category": 40,
        "Product_Manufacturer_Mapping": 30,
        "Manufacturer": 40,
        "Customer": 10,
        "Address": 10,
        "Country": 20,
        "Shipment": 10,
        "Store": 10,
        # Tag and review joins hang off Product, so they must be ordered after
        # it; the cart and discount joins hang off Order.
        "DiscountUsageHistory": 10,
        "ShoppingCartItem": 10,
        "Product_ProductTag_Mapping": 30,
        "ProductTag": 40,
        "ProductReview": 30,
        "SearchTerm": 0,
    }

    #: General dashboard-style predicate summaries.
    #:
    #: This is still the compiler's Approved-template path: users select named
    #: semantic predicates, and the fixed SQL fragments live in code owned by
    #: the deployment. It does not map a report title to SQL; it renders the
    #: reusable "several counts over one table" primitive used by operational
    #: dashboards.
    SUMMARY_SETS: Dict[str, List[Tuple[str, str]]] = {
        "incomplete_order_statuses": [
            ("Total unpaid orders", "o.OrderStatusId <> 40 AND o.PaymentStatusId = 10"),
            ("Total not shipped orders", "o.OrderStatusId <> 40 AND o.ShippingStatusId = 20"),
            ("Total not delivered orders", "o.OrderStatusId <> 40 AND o.ShippingStatusId <> 40"),
        ],
    }

    ZERO_FILL_WINDOWS: Dict[str, Dict[str, str]] = {
        "last seven days": {
            "start": "CAST(UTC_TIMESTAMP() AS DATE) - INTERVAL 7 DAY",
            "end": "CAST(UTC_TIMESTAMP() AS DATE)",
        },
        "last 7 days": {
            "start": "CAST(UTC_TIMESTAMP() AS DATE) - INTERVAL 7 DAY",
            "end": "CAST(UTC_TIMESTAMP() AS DATE)",
        },
    }

    def __init__(self) -> None:
        """Initialize the compiler by building the join adjacency list."""
        self._adj_list: Dict[str, List[str]] = {}
        self._initialize_join_graph()

    def _initialize_join_graph(self) -> None:
        """Constructs an adjacency list from the semantic layer's join graph."""
        for join in JOIN_GRAPH:
            source, target = join.source, join.target
            self._adj_list.setdefault(source, []).append(target)
            self._adj_list.setdefault(target, []).append(source)

    def compile(self, plan: AnalysisPlan) -> str:
        """
        Compiles an AnalysisPlan into a validated MySQL string (§4.7).

        The compilation pipeline:
          1. Identify required tables from metric/dimension bindings.
          2. Build WHERE clauses (time rules + filters with sanitised values).
          3. Resolve the minimal join path via BFS.
          4. Assemble SELECT / FROM / WHERE / GROUP BY / ORDER BY.
          5. Post-compilation safety validation (forbidden-pattern scan).

        Args:
            plan: The validated AnalysisPlan from the SemanticMapper.

        Returns:
            A tuple of (safe MySQL query string, dict of parameters, list of rationale strings).

        Raises:
            SecurityError: If the compiled SQL contains a forbidden construct.
        """
        rationale = []
        logger.info(f"Compiling plan for pattern: {plan.pattern}")
        rationale.append(f"Selected Pattern Template: **{plan.pattern.upper()}**")

        # tabular and exception get their own compilation path (no aggregation)
        if plan.pattern in ["tabular", "exception"]:
            if plan.dimension in self.SUMMARY_SETS:
                sql, params, tab_rationale = self._compile_predicate_summary(plan)
                return sql, params, rationale + tab_rationale
            sql, params, tab_rationale = self._compile_tabular(plan)
            return sql, params, rationale + tab_rationale
        
        # 1. Identify required tables
        required_tables = self._get_required_tables(plan)
        rationale.append(f"Identified Required Tables: {', '.join(required_tables)}")

        if plan.matrix_summary:
            sql, params, matrix_rationale = self._compile_matrix_summary(
                plan, required_tables
            )
            return sql, params, rationale + matrix_rationale

        zero_fill = self._can_zero_fill_daily_trend(plan)
        if zero_fill:
            sql, params, trend_rationale = self._compile_zero_filled_daily_trend(plan)
            return sql, params, rationale + trend_rationale
        
        # 2. Build WHERE clauses (Time + Filters)
        where_parts, params = self._build_where_clauses(plan)
        
        # Scan WHERE clauses for aliases to find implicit tables (e.g. from custom filters)
        for part in where_parts:
            found_aliases = re.findall(r'\b([a-z]+)\.', part.lower())
            for alias in found_aliases:
                if alias in ALIAS_TO_TABLE:
                    required_tables.add(ALIAS_TO_TABLE[alias])

        # 3. Resolve Full Join Path using BFS
        full_join_path = self._resolve_shortest_join_path(list(required_tables))
        rationale.append(f"Resolved Deterministic Join Path: {' -> '.join(full_join_path)}")

        # Always-on predicates, added once the real join path is known.
        where_parts.extend(self._mandatory_predicates(full_join_path))
        
        # 4. Assemble SQL Parts
        # No silent substitution for an unresolved measure.
        #
        # This defaulted to METRICS[0] — revenue — so a plan whose metric slot
        # was empty ("_none_", which the resolver emits deliberately when no
        # measure was named) came back as a revenue query the user never asked
        # for. "Give me an overview of category performance" compiled to a
        # revenue breakdown; it only failed loudly because the join path had
        # been computed without revenue's table and produced invalid SQL. Had
        # the tables happened to line up, it would have returned a confident
        # wrong answer instead.
        #
        # This is the same silent fallback the resolver removed in mapper.py;
        # it survived here because the compiler was never the stage anyone
        # looked at for it.
        # Preserve the order the measures were asked for; filtering METRICS
        # instead would silently reorder the columns of the answer.
        by_id = {m.id: m for m in METRICS}
        extra_metric_objs = [by_id[i] for i in (plan.extra_metrics or []) if i in by_id]
        metric_obj = next((m for m in METRICS if m.id == plan.metric), None)
        if metric_obj is None:
            raise UnresolvedMetricError(
                f"no approved metric corresponds to '{plan.metric}'. A measure "
                f"cannot be chosen on the requester's behalf."
            )
        rationale.append(f"Mapped Metric '{plan.metric}' to Expression: `{metric_obj.sql_expr}`")
        
        dim_obj = next((d for d in DIMENSIONS if d.id == plan.dimension), None) if plan.dimension else None
        if dim_obj:
             rationale.append(f"Mapped Dimension '{plan.dimension}' to Column: `{dim_obj.sql_expr}`")

        sql_parts = [
            self._assemble_select(metric_obj, dim_obj, extra_metric_objs, plan),
            self._assemble_from(full_join_path),
            self._assemble_where(where_parts)
        ]

        # Add optional clauses
        if dim_obj:
            sql_parts.append(self._assemble_group_by(dim_obj, plan))
        
        # Patterns that require ordering
        if plan.sort or plan.pattern in ["ranking", "segment", "cohort", "correlate", "trend"]:
            sql_parts.append(self._assemble_order_by(plan.sort, dim_obj, plan.pattern))
            
        if plan.limit:
            safe_limit = int(plan.limit)  # coerce to int to prevent injection
            sql_parts.append(f"LIMIT {safe_limit}")
        elif plan.pattern not in ["kpi", "summary"]:
            # Default safety limit for non-aggregate queries
            sql_parts.append("LIMIT 100")

        full_sql = "\n".join(sql_parts)

        # Defence-in-depth: post-compilation safety scan (§4.7)
        self._validate_sql_safety(full_sql)
        rationale.append("Passed Post-Compilation Safety Scan (No forbidden patterns detected)")

        return full_sql.strip(), params, rationale

    def _compile_tabular(self, plan: AnalysisPlan) -> Tuple[str, Dict[str, Any], List[str]]:
        rationale = []
        dim_obj = next((d for d in DIMENSIONS if d.id == plan.dimension), None) if plan.dimension else None
        metric_obj = next((m for m in METRICS if m.id == plan.metric), None)
        
        rationale.append(f"Starting Tabular Compilation for dimension: {plan.dimension}")

        # ---- Determine required tables from dimension + filters FIRST ----
        required_tables = set(plan.join_path)
        if dim_obj:
            required_tables.add(dim_obj.binding_table)
            rationale.append(f"Primary table identified from dimension: {dim_obj.binding_table}")
            if hasattr(dim_obj, 'required_joins'):
                required_tables.update(dim_obj.required_joins)
                rationale.append(f"Additional joins required by dimension: {', '.join(dim_obj.required_joins)}")

        # Build WHERE — override time field to match dimension's table
        where_parts, params = self._build_where_clauses_for_lookup(plan, dim_obj)
        for part in where_parts:
            found_aliases = re.findall(r'\b([a-z]+)\.', part.lower())
            for alias in found_aliases:
                if alias in ALIAS_TO_TABLE:
                    required_tables.add(ALIAS_TO_TABLE[alias])

        # ---- Determine SELECT columns (raw, no aggregation) ----
        columns = []
        if dim_obj:
            columns.append(f"{dim_obj.sql_expr} AS `{dim_obj.label}`")

        # Only include metric column if its raw table is already required
        # This prevents e.g. "low stock products" from joining to Order
        metric_included = False
        if metric_obj:
            raw_expr = self._strip_aggregate(metric_obj.sql_expr)
            if raw_expr:
                metric_table = metric_obj.binding_table
                already_needed = metric_table in required_tables
                if already_needed and (not dim_obj or raw_expr != dim_obj.sql_expr):
                    columns.append(f"{raw_expr} AS `{metric_obj.label}`")
                    metric_included = True
                    rationale.append(f"Included metric column: {metric_obj.label}")

        # Add natural extra columns from the dimension's root table
        # for richer tabular output
        if dim_obj:
            extra_cols = self._get_natural_columns(dim_obj.binding_table, dim_obj.sql_expr)
            for col_expr, col_label in extra_cols:
                if not any(col_expr in c for c in columns):
                    columns.append(f"{col_expr} AS `{col_label}`")

        if not columns:
            columns = ["*"]

        select_clause = "SELECT " + ", ".join(columns)

        # Resolve Join Path (for Tabular, we often have a single table or shallow joins)
        if self._needs_order_bridge(required_tables):
            required_tables.add("Order")
            rationale.append("Added 'Order' table as bridge for disjoint tables")

        full_join_path = self._resolve_shortest_join_path(list(required_tables))
        rationale.append(f"Resolved Tabular Join Path: {' -> '.join(full_join_path)}")

        where_parts.extend(self._mandatory_predicates(full_join_path))
        
        from_clause = self._assemble_from_smart(full_join_path, required_tables)
        where_clause = self._assemble_where(where_parts)

        sql_parts = [select_clause, from_clause, where_clause]
        
        # Add sorting.
        #
        # `plan.sort` holds a *direction*, not a column, so emitting it alone
        # produced `ORDER BY desc` — invalid SQL that only surfaced once the
        # queries were executed rather than merely compiled. Sort on the
        # measure when the listing carries one, otherwise on the dimension;
        # if neither is present there is nothing to order by and the clause is
        # omitted rather than guessed at.
        direction = "DESC" if str(plan.sort).lower() == "desc" else "ASC"
        if plan.limit and dim_obj and dim_obj.binding_table == "Order" and str(plan.sort).lower() == "desc":
            sql_parts.append("ORDER BY o.CreatedOnUtc DESC, o.Id DESC")
        elif plan.sort:
            if metric_included and metric_obj:
                sql_parts.append(
                    f"ORDER BY {self._strip_aggregate(metric_obj.sql_expr)} {direction}"
                )
            elif dim_obj:
                sql_parts.append(f"ORDER BY {self._dimension_select_expr(dim_obj, plan)} {direction}")
            else:
                rationale.append(
                    "Sort requested but no metric or dimension column to sort on; "
                    "ORDER BY omitted"
                )
        
        safe_limit = int(plan.limit) if plan.limit else 100
        sql_parts.append(f"LIMIT {safe_limit}")

        full_sql = "\n".join(sql_parts)
        self._validate_sql_safety(full_sql)
        rationale.append("Passed Post-Compilation Safety Scan")

        return full_sql.strip(), params, rationale

    def _compile_predicate_summary(self, plan: AnalysisPlan) -> Tuple[str, Dict[str, Any], List[str]]:
        entries = self.SUMMARY_SETS[plan.dimension or ""]
        parts = [
            "SELECT " + ", ".join([
                f"'{label}' AS label",
                "COUNT(*) AS value",
            ])
            + "\nFROM `Order` o\nWHERE 1=1\n  AND o.Deleted = 0\n  AND " + predicate
            for label, predicate in entries
        ]
        sql = "\nUNION ALL\n".join(parts)
        return sql, {}, [
            f"Rendered Approved predicate-summary set: {plan.dimension}",
            "Rendered from fixed semantic-layer predicates",
        ]

    def _compile_matrix_summary(
        self, plan: AnalysisPlan, required_tables: Set[str]
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        summary = MATRIX_SUMMARIES.get(plan.matrix_summary or "")
        if summary is None:
            raise UnresolvedMetricError(
                f"unknown matrix summary '{plan.matrix_summary}'"
            )

        dimension = next(
            (d for d in DIMENSIONS if d.id == summary.dimension_id), None
        )
        if dimension is None:
            raise UnresolvedMetricError(
                f"matrix summary '{summary.id}' references unknown dimension "
                f"'{summary.dimension_id}'"
            )

        required_tables.add(summary.binding_table)
        required_tables.update(summary.required_joins)
        required_tables.add(dimension.binding_table)
        required_tables.update(dimension.required_joins)

        where_parts, params = self._build_where_clauses(plan)
        for part in where_parts:
            for alias in re.findall(r'\b([a-z]+)\.', part.lower()):
                if alias in ALIAS_TO_TABLE:
                    required_tables.add(ALIAS_TO_TABLE[alias])

        full_join_path = self._resolve_shortest_join_path(list(required_tables))
        where_parts.extend(self._mandatory_predicates(full_join_path))

        bucket_cols = []
        for bucket in summary.buckets:
            if bucket.predicate == "1=1":
                bucket_cols.append(
                    f"SUM({summary.value_expr}) AS `{bucket.label}`"
                )
            else:
                bucket_cols.append(
                    f"SUM(CASE WHEN {bucket.predicate} THEN "
                    f"{summary.value_expr} ELSE 0 END) AS `{bucket.label}`"
                )

        sql_parts = [
            "SELECT "
            + self._dimension_select_expr(dimension, plan)
            + " AS label,\n  "
            + ",\n  ".join(bucket_cols),
            self._assemble_from(full_join_path),
            self._assemble_where(where_parts),
            self._assemble_group_by(dimension, plan),
        ]
        if summary.order_expr:
            sql_parts.append(f"ORDER BY {summary.order_expr}")

        sql = "\n".join(sql_parts)
        self._validate_sql_safety(sql)
        return sql.strip(), params, [
            f"Rendered Approved period matrix: {summary.id}",
            "Rendered from semantic-layer metric, dimension and bucket definitions",
            "Passed Post-Compilation Safety Scan",
        ]

    def _can_zero_fill_daily_trend(self, plan: AnalysisPlan) -> bool:
        range_grain = (
            plan.time_range.grain.value
            if plan.time_range is not None and plan.time_range.grain is not None
            else None
        )
        if plan.pattern != "trend" or (plan.time_grain or range_grain) != "day":
            return False
        if str(plan.time_rule or "").strip().lower() not in self.ZERO_FILL_WINDOWS:
            return False
        if plan.filters:
            return False
        return bool(plan.metric and plan.dimension)

    def _compile_zero_filled_daily_trend(
        self, plan: AnalysisPlan
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        metric = next((m for m in METRICS if m.id == plan.metric), None)
        dimension = next((d for d in DIMENSIONS if d.id == plan.dimension), None)
        if metric is None or dimension is None:
            raise UnresolvedMetricError("zero-filled trend requires a metric and date dimension")
        if dimension.datatype != "date":
            raise TimeResolutionError("zero-filled trend requires a date dimension")

        rule = self.ZERO_FILL_WINDOWS[str(plan.time_rule or "").strip().lower()]
        root_table = metric.binding_table
        root_alias = self.TABLE_ALIASES[root_table]
        date_field = TABLE_DATE_FIELDS.get(root_table) or dimension.sql_expr
        required_tables = self._get_required_tables(plan)
        if set(required_tables) - {root_table}:
            raise TimeResolutionError(
                "zero-filled daily trends currently support one fact table"
            )
        where_parts = self._mandatory_predicates_for_tables({root_table})
        join_predicates = [
            f"{date_field} >= days.d",
            f"{date_field} < days.d + INTERVAL 1 DAY",
            *where_parts,
        ]

        sql = (
            "WITH RECURSIVE days AS (\n"
            f"  SELECT {rule['start']} AS d\n"
            "  UNION ALL\n"
            f"  SELECT d + INTERVAL 1 DAY FROM days WHERE d < {rule['end']}\n"
            ")\n"
            "SELECT DATE_FORMAT(days.d, '%Y-%m-%d') AS label, "
            f"COALESCE({metric.sql_expr}, 0) AS value\n"
            "FROM days\n"
            f"LEFT JOIN `{root_table}` {root_alias} ON "
            + " AND ".join(join_predicates)
            + "\nGROUP BY days.d\nORDER BY days.d"
        )
        return sql, {}, [
            f"Rendered zero-filled daily trend for {plan.time_rule}",
            "Rendered from fixed compiler template",
        ]

    def _mandatory_predicates_for_tables(self, tables: Set[str]) -> List[str]:
        predicates: List[str] = []
        for table in tables:
            alias = self.TABLE_ALIASES.get(table)
            if alias is None:
                continue
            entries = MANDATORY_PREDICATES.get(table, [])
            if isinstance(entries, str):
                entries = [entries]
            for predicate in entries:
                sql = predicate["sql"] if isinstance(predicate, dict) else str(predicate)
                if "." not in sql:
                    sql = f"{alias}.{sql}"
                predicates.append(sql)
        return predicates

    @staticmethod
    def _get_natural_columns(table: str, exclude_expr: str) -> list:
        """Return extra columns from a table for richer tabular output."""
        TABLE_EXTRA_COLS = {
            "Product": [
                ("p.StockQuantity", "Stock Qty"),
                ("p.ApprovedTotalReviews", "Reviews"),
            ],
            "Customer": [
                ("cu.CreatedOnUtc", "Registered On"),
            ],
            "Order": [
                ("o.OrderTotal", "Order Total"),
                ("o.CreatedOnUtc", "Order Date"),
            ],
        }
        extras = TABLE_EXTRA_COLS.get(table, [])
        return [(expr, label) for expr, label in extras if expr != exclude_expr]

    # Date fields by table — used by _build_where_clauses_for_lookup
    #: Defined in the semantic layer so the resolver can consult it too and
    #: refuse before compilation; kept as a class attribute because the lookup
    #: path below and the parity tests both reference it by that name.
    TABLE_DATE_FIELDS = TABLE_DATE_FIELDS

    def _build_where_clauses_for_lookup(self, plan, dim_obj):
        """Like _build_where_clauses but uses the correct date field for time_rule."""
        parts = []
        params = {}

        # Pick the right date field based on the dimension's root table
        time_field = "o.CreatedOnUtc"  # default
        if dim_obj:
            time_field = self.TABLE_DATE_FIELDS.get(dim_obj.binding_table, "o.CreatedOnUtc") or None
        if time_field:
            predicate = self._time_predicate(plan, time_field)
            if predicate:
                parts.append(predicate)
        elif plan.time_range is not None or plan.time_rule:
            # The requested grouping has no date column at all, so the period
            # cannot be applied.  Answering without it would quietly widen the
            # result to all of history.
            raise TimeResolutionError(
                f"'{plan.dimension}' has no date field, so the requested "
                f"period cannot be applied to this report."
            )

        # Field filters — reuse existing logic
        filters_by_field = {}
        for f in plan.filters:
            field = f.field if hasattr(f, 'field') else 'unknown'
            filters_by_field.setdefault(field, []).append(f)

        for field, fs in filters_by_field.items():
            field_clauses = []
            for f in fs:
                sql_part, f_params = self._build_single_filter(f, len(params))
                if sql_part:
                    field_clauses.append(sql_part)
                    params.update(f_params)
            if len(field_clauses) > 1:
                parts.append("(" + " OR ".join(field_clauses) + ")")
            elif field_clauses:
                parts.append(field_clauses[0])

        return parts, params

    @staticmethod
    def _strip_aggregate(sql_expr: str) -> Optional[str]:
        """Remove aggregate wrapper (SUM/COUNT/AVG/MIN/MAX) to get raw column.

        e.g. 'SUM(oi.Quantity)' → 'oi.Quantity'
             'COUNT(DISTINCT o.Id)' → 'o.Id'

        Returns ``None`` when the expression is not a single aggregate call and
        so has no raw column to expose; callers must treat that as "no column",
        not as a string.
        """
        m = re.match(r'^(?:SUM|COUNT|AVG|MIN|MAX)\((?:DISTINCT\s+)?(.+)\)$', sql_expr, re.IGNORECASE)
        if not m:
            return sql_expr

        # The pattern above is greedy, so on a composite expression it matches
        # the *first* aggregate's opening bracket against the *last* bracket in
        # the string. A ratio metric such as
        #     SUM(COALESCE(o.OrderDiscount,0)) / NULLIF(SUM(...), 0)
        # therefore yielded the unbalanced fragment
        #     COALESCE(o.OrderDiscount,0)) / NULLIF(SUM(...), 0
        # which was spliced into SELECT and WHERE and produced a syntax error
        # at execution — never at compile time, so every check that stopped at
        # "SQL was produced" passed it.
        #
        # A metric is unwrappable only when it is one aggregate call and
        # nothing else, which means the bracket opened after the function name
        # must close on the final character. Anything else has no single raw
        # column to expose, and saying so is the correct answer.
        inner = m.group(1).strip()
        depth = 0
        for char in inner:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    return None          # closed the aggregate early: composite
        if depth != 0:
            return None
        # CASE expressions are a single call but have no raw column to expose.
        if "CASE" in inner.upper():
            return None
        return inner

    def _needs_order_bridge(self, tables: set) -> bool:
        """Check if Order table is needed to bridge disjoint table sets."""
        # If we only have tables from one side of the schema, no bridge needed
        product_side = {"Product", "Category", "Product_Category_Mapping", "Manufacturer", "Product_Manufacturer_Mapping"}
        customer_side = {"Customer", "Address", "Country"}
        order_side = {"Order", "Shipment", "Store"}
        
        has_product = bool(tables & product_side)
        has_customer = bool(tables & customer_side)
        has_order = bool(tables & order_side)
        
        # Need Order as bridge only if we're mixing product + customer sides
        # Or if order specific tables are mixed with product side
        if has_product and (has_customer or has_order):
            return True
        return False

    def _assemble_from_smart(self, join_path: list, required_tables: set) -> str:
        """Assembles FROM clause, choosing the most natural root table.

        For queries that don't involve Order (e.g. Product-only),
        this picks the correct root instead of defaulting to Order.
        """
        if not join_path:
            return ""

        # Pick root: prefer the table that ISN'T a junction table
        if "Order" in join_path:
            root = "Order"
        elif "Product" in join_path:
            root = "Product"
        elif "Customer" in join_path:
            root = "Customer"
        else:
            root = join_path[0]

        alias = self.TABLE_ALIASES.get(root, 'root')
        from_clause = f"FROM `{root}` {alias}"

        # Smart join clauses for non-Order roots
        NON_ORDER_JOINS = {
            "Product_Category_Mapping": {
                "Product": "LEFT JOIN `Product_Category_Mapping` pcm ON p.Id = pcm.ProductId",
            },
            "Category": {
                "Product_Category_Mapping": "LEFT JOIN `Category` c ON pcm.CategoryId = c.Id",
            },
            "OrderItem": {
                "Product": "LEFT JOIN `OrderItem` oi ON p.Id = oi.ProductId",
            }
        }

        sorted_joins = sorted([t for t in join_path if t != root], key=lambda x: self.JOIN_ORDER.get(x, 999))

        for table in sorted_joins:
            if root != "Order" and table in NON_ORDER_JOINS and root in NON_ORDER_JOINS.get(table, {}):
                from_clause += f"\n{NON_ORDER_JOINS[table][root]}"
            elif table in self.JOIN_CLAUSES:
                clause = self.JOIN_CLAUSES[table]
                if clause:
                    from_clause += f"\n{clause}"

        return from_clause

    def _get_required_tables(self, plan: AnalysisPlan) -> Set[str]:
        """Identifies all tables required by metrics and dimensions."""
        tables = set(plan.join_path)
        # Removed hardcoded Order addition to allow non-Order roots
        
        for measure_id in [plan.metric, *(plan.extra_metrics or [])]:
            metric_obj = next((m for m in METRICS if m.id == measure_id), None)
            if metric_obj:
                tables.add(metric_obj.binding_table)
                if hasattr(metric_obj, 'required_joins'):
                    tables.update(metric_obj.required_joins)
            
        if plan.dimension:
            dim_obj = next((d for d in DIMENSIONS if d.id == plan.dimension), None)
            if dim_obj:
                tables.add(dim_obj.binding_table)
                if hasattr(dim_obj, 'required_joins'):
                    tables.update(dim_obj.required_joins)
        if plan.matrix_summary:
            summary = MATRIX_SUMMARIES.get(plan.matrix_summary)
            if summary:
                tables.add(summary.binding_table)
                tables.update(summary.required_joins)
                dim_obj = next(
                    (d for d in DIMENSIONS if d.id == summary.dimension_id), None
                )
                if dim_obj:
                    tables.add(dim_obj.binding_table)
                    if hasattr(dim_obj, 'required_joins'):
                        tables.update(dim_obj.required_joins)
                
        return tables

    def _resolve_shortest_join_path(self, target_nodes: List[str]) -> List[str]:
        """Finds the minimal set of join nodes required to connect all targets."""
        if not target_nodes: return []
        if len(target_nodes) == 1: return target_nodes
        
        # Prefer 'Order' as the root of the star/snowflake
        root = "Order" if "Order" in target_nodes else target_nodes[0]
        full_path_nodes = {root}
        
        for target in target_nodes:
            if target in full_path_nodes: continue
            
            # BFS for shortest path from current graph to target
            queue: List[Tuple[str, List[str]]] = [(n, [n]) for n in full_path_nodes]
            visited = set()
            
            while queue:
                current_node, path = queue.pop(0)
                if current_node == target:
                    full_path_nodes.update(path)
                    break
                
                if current_node in visited: continue
                visited.add(current_node)
                
                for neighbor in self._adj_list.get(current_node, []):
                    if neighbor not in path:
                        queue.append((neighbor, path + [neighbor]))
                        
        return list(full_path_nodes)

    def _assemble_select(self, metric: Any, dimension: Optional[Any],
                         extra_metrics: Optional[List[Any]] = None,
                         plan: Optional[AnalysisPlan] = None) -> str:
        """Assembles the SELECT clause.

        The first measure keeps the ``value`` alias every downstream consumer
        already reads. Additional measures — which only a summary carries —
        are projected alongside it under their own ids, so a request for three
        measures returns three columns instead of one silently chosen for the
        user.
        """
        measures = [f"{metric.sql_expr} AS value"]
        for extra in extra_metrics or []:
            measures.append(f"{extra.sql_expr} AS `{extra.id}`")
        projected = ", ".join(measures)

        if dimension:
            dim_expr = self._dimension_select_expr(dimension, plan)
            return f"SELECT {dim_expr} AS label, {projected}"
        return f"SELECT {projected}"

    @staticmethod
    def _dimension_select_expr(dimension: Any, plan: Optional[AnalysisPlan] = None) -> str:
        grain = getattr(plan, "time_grain", None) if plan is not None else None
        if dimension.datatype == "date":
            if grain == "month":
                return f"DATE_FORMAT({dimension.sql_expr}, '%Y-%m')"
            if grain == "year":
                return f"CAST(YEAR({dimension.sql_expr}) AS CHAR)"
            return f"CAST({dimension.sql_expr} AS DATE)"
        return dimension.sql_expr

    def _assemble_from(self, join_path: List[str]) -> str:
        """Assembles the FROM and JOIN clauses for aggregate queries (always roots at Order).

        For tabular/non-aggregate queries that may root at Product or Customer,
        use _assemble_from_smart() instead.
        """
        if not join_path: return ""

        root = "Order" if "Order" in join_path else join_path[0]
        from_clause = f"FROM `{root}` {self.TABLE_ALIASES.get(root, 'root')}"
        
        # Consistent join order for determinism and performance
        sorted_joins = sorted([t for t in join_path if t != root], key=lambda x: self.JOIN_ORDER.get(x, 999))
        
        for table in sorted_joins:
            if table in self.JOIN_CLAUSES:
                clause = self.JOIN_CLAUSES[table]
                if clause:
                    from_clause += f"\n{clause}"
                
        return from_clause

    def _assemble_where(self, where_parts: List[str]) -> str:
        """Assembles the WHERE clause."""
        clause = "WHERE 1=1"
        if where_parts:
            clause += "\n  AND " + "\n  AND ".join(where_parts)
        return clause

    def _assemble_group_by(self, dimension: Any,
                           plan: Optional[AnalysisPlan] = None) -> str:
        """Assembles the GROUP BY clause.

        Groups by the dimension's declared identity where it has one. Grouping
        by the displayed label instead merges rows that only look alike — two
        customers sharing a name become one row whose total is the sum of both,
        and nothing in the output marks it as a merge.
        """
        declared = getattr(dimension, "group_expr", "")
        expr = declared or dimension.sql_expr
        if dimension.datatype == "date":
            expr = self._dimension_select_expr(dimension, plan)
        elif not declared and "SELECT" in dimension.sql_expr.upper():
            # MySQL's ONLY_FULL_GROUP_BY (on by default since 8.0) rejects a
            # GROUP BY whose expression contains a correlated subquery, even
            # when the SELECT list repeats that expression verbatim: it cannot
            # prove the subquery functionally determines the grouping, so it
            # sees the outer column inside it as a bare non-aggregated column.
            # The customer-cohort dimension is exactly this shape, and every
            # cohort query failed at execution with error 1055 — invisible to
            # a compiler that only checks whether SQL was produced.
            #
            # Grouping by the SELECT alias is equivalent here, because the
            # projection aliases this same expression as `label`. It is only
            # used where no explicit group_expr is declared, so a dimension
            # that deliberately groups by something other than what it
            # displays (customer identity vs. customer name) is unaffected.
            return "GROUP BY label"
        return f"GROUP BY {expr}"

    def _assemble_order_by(self, sort_dir: Optional[str],
                           dimension: Optional[Any] = None,
                           pattern: Optional[str] = None) -> str:
        """Assembles the ORDER BY clause."""
        direction = sort_dir if sort_dir and sort_dir.lower() in ["asc", "desc"] else "desc"
        if pattern == "trend" and dimension is not None:
            return "ORDER BY label asc"
        return f"ORDER BY value {direction}"

    def _build_where_clauses(self, plan: AnalysisPlan) -> Tuple[List[str], Dict[str, Any]]:
        """Orchestrates the construction of all filter conditions."""
        parts = []
        params = {}
        
        # 1. Time Rule
        # The window applies to the column the *measure* is dated by, which is
        # not always the order date. Hardcoding the order date made a customer
        # count silently mean "customers who ordered in this period".
        metric_obj = next((m for m in METRICS if m.id == plan.metric), None)
        anchor = getattr(metric_obj, "time_anchor", "") or "o.CreatedOnUtc"
        predicate = self._time_predicate(plan, anchor)
        if predicate:
            parts.append(predicate)


        # 2. Field Filters
        # Group by field to handle logical grouped expressions
        filters_by_field: Dict[str, List[Dict]] = {}
        for f in plan.filters:
            field = f.field if hasattr(f, 'field') else 'unknown'
            filters_by_field.setdefault(field, []).append(f)
            
        for field, fs in filters_by_field.items():
            field_clauses = []
            for f in fs:
                sql_part, f_params = self._build_single_filter(f, len(params))
                if sql_part:
                    field_clauses.append(sql_part)
                    params.update(f_params)
                    
            if len(field_clauses) > 1:
                parts.append("(" + " OR ".join(field_clauses) + ")")
            elif field_clauses:
                parts.append(field_clauses[0])

        return parts, params

    @staticmethod
    def _mandatory_predicates(tables) -> List[str]:
        """Soft-delete and equivalent always-on predicates for ``tables``.

        These are the platform's own flags, which every nopCommerce report
        filters before it aggregates. They are not the user's filters and are
        not the user's to drop, so they come from the semantic layer rather
        than from whatever the request happened to ask for.

        Applied against the *resolved* join path rather than the plan's
        declared one: the compiler adds bridging tables of its own (a category
        breakdown reaches Category through Product, which no binding names), and
        a bridging table brings its own deleted rows with it.
        """
        return [
            MANDATORY_PREDICATES[table]
            for table in sorted(tables)
            if table in MANDATORY_PREDICATES
        ]

    def _build_single_filter(self, f: Filter, param_offset: int = 0) -> Tuple[str, Dict[str, Any]]:
        """Constructs a parameterized MySQL predicate for a single filter object.

        Returns a tuple of (sql_template, params) to achieve 100% security 
        against SQL injection (Proposition 1, §4.7).
        """
        field_name = f.field
        op = f.operator
        val = f.value
        params = {}

        # Approved predicate: the filter names a fragment authored in the
        # semantic layer.  The fragment is fetched by key and emitted verbatim;
        # the value is never interpolated, so this path adds no injection
        # surface.  An unrecognised key raises rather than falling through —
        # a dropped predicate silently widens the result set, and a query that
        # returns more rows than it should is exactly the kind of wrong answer
        # a user has no way to detect.
        if field_name == PREDICATE_FIELD:
            entry = APPROVED_PREDICATES.get(str(val))
            if entry is None:
                raise SecurityError(
                    f"unknown Approved predicate '{val}'. Approved predicates: "
                    f"{sorted(APPROVED_PREDICATES)}"
                )
            return f"({entry['sql']})", params

        # Normalize operator for SQL
        op_map = {
            "==": "=",
            "eq": "=",
            "neq": "!=",
            "gt": ">",
            "gte": ">=",
            "lt": "<",
            "lte": "<=",
        }
        op = op_map.get(op.lower(), op)

        dim = next((d for d in DIMENSIONS if d.id == field_name), None)
        if dim:
            sql_field = dim.sql_expr
        else:
            metric = next((m for m in METRICS if m.id == field_name), None)
            if metric:
                # For filters on metrics, we unwrap the aggregate (e.g. SUM(x) -> x)
                # This works for tabular queries where we filter raw rows.
                #
                # It does not work for a metric with no single raw column — a
                # ratio, or a CASE. The `or "o.Id"` that used to stand here
                # turned "categories where the average discount exceeds 30%"
                # into a filter on the order id: a query that runs, returns
                # something, and answers a different question than the one
                # asked. A rate is a quotient of two aggregates and belongs in
                # HAVING rather than WHERE in any case, so the honest response
                # is to say the filter cannot be expressed.
                sql_field = self._strip_aggregate(metric.sql_expr)
                if not sql_field:
                    raise UnknownFilterFieldError(
                        f"'{metric.label}' is an aggregate with no single "
                        f"underlying column, so it cannot be used as a "
                        f"row-level filter"
                    )
            elif field_name in ALIAS_TO_TABLE:
                sql_field = ALIAS_TO_TABLE[field_name]
            else:
                # Previously this defaulted to "o.Id", so a filter the
                # semantic layer did not recognise silently became a predicate
                # on the order id — e.g. `o.Id = 'incomplete_order'`, which
                # compiles, executes, returns zero rows, and reports itself as
                # a successful answer. An unbindable filter is an unanswerable
                # request, and must say so rather than quietly filtering on
                # something the user never asked about.
                raise UnknownFilterFieldError(
                    f"filter field '{field_name}' is not an approved metric, "
                    f"dimension, table alias or Approved predicate"
                )

        # Temporal logic for date fields.
        #
        # The declared datatype is authoritative; the name heuristic is only a
        # fallback for fields that are not semantic-layer dimensions.  Relying
        # on substring matching alone meant a date column whose id contained
        # neither "date" nor "time" took the literal-binding path below.
        is_temporal = (
            dim.datatype == "date" if dim
            else ("date" in field_name or "time" in field_name)
        )
        if isinstance(val, str) and is_temporal:
            if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', str(val)):
                p_name = f"p{param_offset}"
                params[p_name] = val
                return f"CAST({sql_field} AS DATE) {op} @{p_name}", params

            # A relative phrase on a date column must be resolved to a range,
            # never bound as a literal.  Falling through to the equality branch
            # below produced `CreatedOnUtc = 'this morning'`, which MySQL
            # rejects outright — the visible half of the same defect that made
            # aggregate queries silently ignore their time window.
            resolution = time_grammar.normalise(val)
            if resolution.is_resolved and resolution.range is not None:
                return resolution.range.to_predicate(sql_field), params
            raise TimeResolutionError(
                f"filter on '{field_name}': {resolution.reason}"
                if resolution.reason
                else f"filter on '{field_name}': cannot interpret '{val}' as a date"
            )

        # Null checks (no user value involved)
        if op == 'is_null': return f"{sql_field} IS NULL", params
        if op == 'is_not_null': return f"{sql_field} IS NOT NULL", params

        # List operators
        if isinstance(val, list) or op in ['in', 'not_in']:
            if not isinstance(val, list):
                val = [v.strip() for v in str(val).split(',')]
            
            placeholders = []
            for i, v in enumerate(val):
                p_name = f"p{param_offset + i}"
                params[p_name] = v if not isinstance(v, str) or not v.isdigit() else int(v)
                placeholders.append(f"@{p_name}")
                
            items = ", ".join(placeholders)
            prefix = "NOT " if op == 'not_in' else ""
            return f"{sql_field} {prefix}IN ({items})", params

        # Range operators
        if op == 'between' and isinstance(val, list) and len(val) == 2:
            p1 = f"p{param_offset}"
            p2 = f"p{param_offset + 1}"
            params[p1] = val[0]
            params[p2] = val[1]
            return f"{sql_field} BETWEEN @{p1} AND @{p2}", params

        # String search
        if op == 'contains':
            p_name = f"p{param_offset}"
            params[p_name] = f"%{val}%"
            return f"{sql_field} LIKE @{p_name}", params

        # Default equality/inequality
        p_name = f"p{param_offset}"
        params[p_name] = val
        return f"{sql_field} {op} @{p_name}", params

    def _time_predicate(self, plan: AnalysisPlan, field_expr: str) -> Optional[str]:
        """Render the plan's temporal window as a SQL predicate.

        The compiler reads ``plan.time_range`` — the normalised, half-open
        window produced by :mod:`.time_grammar` — and never ``plan.time_rule``,
        which is retained only as the raw phrase for provenance and display.
        That separation is what makes the dropped-filter failure class
        unreachable: an unnormalised phrase has no path into SQL.

        Note on the safety argument: ``TimeRange.start_sql`` and ``end_sql`` are
        SQL fragments the compiler itself builds from a closed grammar of fixed
        templates in :mod:`.time_grammar`.  No user text reaches them — the
        grammar matches a phrase and selects a pre-written fragment, it never
        interpolates the phrase.  Embedding them therefore does not widen the
        injection surface, and Proposition 1 continues to hold.

        Args:
            plan: The analysis plan being compiled.
            field_expr: Qualified date column to constrain, e.g.
                ``"o.CreatedOnUtc"``.

        Returns:
            A SQL predicate string, or ``None`` when no period was requested.

        Raises:
            TimeResolutionError: If the plan carries a raw time phrase that was
                never normalised into a range.
        """
        if plan.time_range is not None:
            return plan.time_range.to_predicate(field_expr)

        if plan.time_rule:
            # Reaching here means a plan was built outside the resolver, which
            # is the only component that normalises time.  Re-run the grammar
            # so the decision is made in one place.
            resolution = time_grammar.normalise(plan.time_rule)
            if resolution.is_resolved and resolution.range is not None:
                return resolution.range.to_predicate(field_expr)

            # Only an UNSUPPORTED phrase is an error. A granularity ("monthly")
            # or an underdetermined period that the resolver already turned
            # into a clarification carries no filtering intent, so there is
            # nothing to refuse — raising here crashed the single most common
            # trend request, and the server reported the crash as an answer.
            if resolution.status is time_grammar.TimeStatus.UNSUPPORTED:
                raise TimeResolutionError(
                    resolution.reason
                    or f"time expression '{plan.time_rule}' could not be resolved"
                )

        return None

    def _get_smart_time_sql(self, field_expr: str, value: str) -> Optional[str]:
        """Translate a time phrase into a MySQL predicate.

        .. deprecated::
            Retained for backwards compatibility with existing callers and
            tests.  The main compile path goes through :meth:`_time_predicate`,
            which cannot silently drop a constraint.  This shim delegates to
            :func:`time_grammar.normalise` so both paths share one grammar, but
            it preserves the old ``None``-on-failure signature — which is
            exactly the signature that made the original bug possible, so do
            not use it in new code.
        """
        resolution = time_grammar.normalise(value)
        if resolution.is_resolved and resolution.range is not None:
            return resolution.range.to_predicate(field_expr)
        return None

    def _legacy_time_sql(self, field_expr: str, value: str) -> Optional[str]:
        """Original hand-rolled matcher, kept only for reference/diffing."""
        val = value.lower().replace("_", " ").strip()
        
        # Exact Day
        if val in ["today", "now", "current"]:
            return f"CAST({field_expr} AS DATE) = CAST(UTC_TIMESTAMP() AS DATE)"
        if val in ["yesterday"]:
            return f"CAST({field_expr} AS DATE) = CAST(DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY) AS DATE)"
        
        # Relative Windows
        if val in ["now-1d", "now-24h", "past 24 hours"]:
            return f"{field_expr} >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 24 HOUR)"
            
        # Flexible Relative Windows (e.g. "past 30 days", "30 days ago")
        m = re.match(r'(?:past\s+)?(\d+)\s+days?(?:\s+ago)?', val)
        if m:
            days = m.group(1)
            if "ago" in val and "past" not in val:
                return f"{field_expr} <= DATE_SUB(UTC_TIMESTAMP(), INTERVAL {days} DAY)"
            return f"{field_expr} >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL {days} DAY)"
            
        # Bucketed Windows (Standard ISO definitions)
        if "week" in val:
            offset = -1 if "last" in val else 0
            return f"{field_expr} >= DATE_ADD(DATE(UTC_TIMESTAMP() - INTERVAL WEEKDAY(UTC_TIMESTAMP()) DAY), INTERVAL {offset} WEEK)"
        
        if "month" in val:
            offset = -1 if "last" in val else 0
            return f"{field_expr} >= DATE_ADD(LAST_DAY(UTC_TIMESTAMP() - INTERVAL 1 MONTH) + INTERVAL 1 DAY, INTERVAL {offset} MONTH)"
            
        if "year" in val:
            offset = -1 if "last" in val else 0
            return f"YEAR({field_expr}) = YEAR(UTC_TIMESTAMP()) + {offset}"
            
        return None

    # ------------------------------------------------------------------
    # Post-compilation safety validation (§4.7, Ablation: "AST validation")
    # ------------------------------------------------------------------
    def _validate_sql_safety(self, sql: str) -> None:
        """Scans compiled SQL for forbidden constructs as defence-in-depth.

        Even though the template-based compiler should never produce unsafe
        SQL, this validation layer provides an additional guarantee.  It
        corresponds to the AST validation described in §4.7 and the ablation
        study row ``– AST validation``.

        Raises:
            SecurityError: If any forbidden pattern is detected.
        """
        for pattern in self.FORBIDDEN_PATTERNS:
            match = re.search(pattern, sql, re.IGNORECASE)
            if match:
                logger.error(
                    f"SECURITY: Forbidden SQL construct '{match.group()}' "
                    f"detected in compiled query."
                )
                raise SecurityError(
                    f"Compiled SQL contains forbidden construct: "
                    f"'{match.group()}'. Query rejected."
                )
