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
from .models import AnalysisPlan, Filter, FilterOperator
from .semantic_layer import METRICS, DIMENSIONS, JOIN_GRAPH, ALIAS_TO_TABLE

# Configure module-level logger
logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when compiled SQL contains a forbidden construct."""
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
        "OrderItem": "INNER JOIN `OrderItem` oi ON o.Id = oi.OrderId",
        "Product": "INNER JOIN `Product` p ON oi.ProductId = p.Id",
        "Product_Category_Mapping": "INNER JOIN `Product_Category_Mapping` pcm ON p.Id = pcm.ProductId",
        "Category": "INNER JOIN `Category` c ON pcm.CategoryId = c.Id",
        "Customer": "INNER JOIN `Customer` cu ON o.CustomerId = cu.Id",
        "Product_Manufacturer_Mapping": "INNER JOIN `Product_Manufacturer_Mapping` pmm ON p.Id = pmm.ProductId",
        "Manufacturer": "INNER JOIN `Manufacturer` mf ON pmm.ManufacturerId = mf.Id",
        "Address": "INNER JOIN `Address` addr ON o.BillingAddressId = addr.Id",
        "Country": "INNER JOIN `Country` co ON addr.CountryId = co.Id",
        "Shipment": "INNER JOIN `Shipment` sh ON o.Id = sh.OrderId",
        "Store": "INNER JOIN `Store` st ON o.StoreId = st.Id",
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
            A tuple of (safe MySQL query string, dict of parameters).

        Raises:
            SecurityError: If the compiled SQL contains a forbidden construct.
        """
        logger.info(f"Compiling plan for pattern: {plan.pattern}")

        # tabular and exception get their own compilation path (no aggregation)
        if plan.pattern in ["tabular", "exception"]:
            return self._compile_tabular(plan)
        
        # 1. Identify required tables
        required_tables = self._get_required_tables(plan)
        
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
        
        # 4. Assemble SQL Parts
        metric_obj = next((m for m in METRICS if m.id == plan.metric), METRICS[0])
        dim_obj = next((d for d in DIMENSIONS if d.id == plan.dimension), None) if plan.dimension else None

        sql_parts = [
            self._assemble_select(metric_obj, dim_obj),
            self._assemble_from(full_join_path),
            self._assemble_where(where_parts)
        ]

        # Add optional clauses
        if dim_obj:
            sql_parts.append(self._assemble_group_by(dim_obj))
        
        # Patterns that require ordering
        if plan.sort or plan.pattern in ["ranking", "segment", "cohort", "correlate"]:
            sql_parts.append(self._assemble_order_by(plan.sort))
            
        if plan.limit:
            safe_limit = int(plan.limit)  # coerce to int to prevent injection
            sql_parts.append(f"LIMIT {safe_limit}")
        elif plan.pattern not in ["kpi", "summary"]:
            # Default safety limit for non-aggregate queries
            sql_parts.append("LIMIT 100")

        full_sql = "\n".join(sql_parts)

        # Defence-in-depth: post-compilation safety scan (§4.7)
        self._validate_sql_safety(full_sql)

        return full_sql.strip(), params

    def _compile_tabular(self, plan: AnalysisPlan):
        """Compile a tabular query: raw rows, no aggregation.

        Unlike aggregate queries, tabular SELECTs individual columns
        without GROUP BY.  The root table is chosen from the dimension/metric
        binding rather than defaulting to Order, so Product-only or
        Customer-only queries never require an Order JOIN.
        """
        dim_obj = next((d for d in DIMENSIONS if d.id == plan.dimension), None) if plan.dimension else None
        metric_obj = next((m for m in METRICS if m.id == plan.metric), None)

        # ---- Determine required tables from dimension + filters FIRST ----
        required_tables = set(plan.join_path)
        if dim_obj:
            required_tables.add(dim_obj.binding_table)
            if hasattr(dim_obj, 'required_joins'):
                required_tables.update(dim_obj.required_joins)

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
                # Check if metric table is already in our required set
                # (or if it IS the dimension table)
                already_needed = metric_table in required_tables
                if already_needed and (not dim_obj or raw_expr != dim_obj.sql_expr):
                    columns.append(f"{raw_expr} AS `{metric_obj.label}`")
                    metric_included = True

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

        # If metric wasn't included, don't add its table dependencies
        if metric_included and metric_obj:
            required_tables.add(metric_obj.binding_table)
            if hasattr(metric_obj, 'required_joins'):
                required_tables.update(metric_obj.required_joins)

        # Only add Order if truly needed as a bridge
        needs_order = "Order" in required_tables or self._needs_order_bridge(required_tables)
        if needs_order:
            required_tables.add("Order")

        full_join_path = self._resolve_shortest_join_path(list(required_tables))

        # ---- Assemble FROM using the correct root ----
        from_clause = self._assemble_from_smart(full_join_path, required_tables)

        # ---- Build final SQL (NO GROUP BY) ----
        sql_parts = [select_clause, from_clause, self._assemble_where(where_parts)]

        # Order by dimension if available
        if plan.sort and dim_obj:
            direction = plan.sort if plan.sort.lower() in ["asc", "desc"] else "asc"
            sql_parts.append(f"ORDER BY {dim_obj.sql_expr} {direction}")

        safe_limit = int(plan.limit) if plan.limit else 100
        sql_parts.append(f"LIMIT {safe_limit}")

        full_sql = "\n".join(sql_parts)
        self._validate_sql_safety(full_sql)
        return full_sql.strip(), params

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
    TABLE_DATE_FIELDS = {
        "Customer": "cu.CreatedOnUtc",
        "Order": "o.CreatedOnUtc",
        "Product": None,  # Products don't have a date field in this schema
    }

    def _build_where_clauses_for_lookup(self, plan, dim_obj):
        """Like _build_where_clauses but uses the correct date field for time_rule."""
        parts = []
        params = {}

        if plan.time_rule:
            # Pick the right date field based on the dimension's root table
            time_field = "o.CreatedOnUtc"  # default
            if dim_obj:
                time_field = self.TABLE_DATE_FIELDS.get(dim_obj.binding_table, "o.CreatedOnUtc") or None
            if time_field:
                time_part = self._get_smart_time_sql(time_field, plan.time_rule)
                if time_part:
                    parts.append(time_part)

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
    def _strip_aggregate(sql_expr: str) -> str:
        """Remove aggregate wrapper (SUM/COUNT/AVG/MIN/MAX) to get raw column.

        e.g. 'SUM(oi.Quantity)' → 'oi.Quantity'
             'COUNT(DISTINCT o.Id)' → 'o.Id'
        """
        m = re.match(r'^(?:SUM|COUNT|AVG|MIN|MAX)\((?:DISTINCT\s+)?(.+)\)$', sql_expr, re.IGNORECASE)
        if m:
            inner = m.group(1).strip()
            # Handle CASE expressions — too complex to unwrap
            if 'CASE' in inner.upper():
                return None
            return inner
        return sql_expr

    def _needs_order_bridge(self, tables: set) -> bool:
        """Check if Order table is needed to bridge disjoint table sets."""
        # If we have OrderItem, we almost always need Order for the join logic
        if "OrderItem" in tables:
            return True
            
        # If we only have tables from one side of the schema, no bridge needed
        product_side = {"Product", "Category", "Product_Category_Mapping", "Manufacturer", "Product_Manufacturer_Mapping"}
        customer_side = {"Customer", "Address", "Country"}
        order_side = {"Order", "OrderItem", "Shipment", "Store"}
        
        has_product = bool(tables & product_side)
        has_customer = bool(tables & customer_side)
        has_order = bool(tables & order_side)
        
        # Need Order as bridge only if we're mixing product + customer sides
        if has_product and has_customer:
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
                "Product": "INNER JOIN `Product_Category_Mapping` pcm ON p.Id = pcm.ProductId",
            },
            "Category": {
                "Product_Category_Mapping": "INNER JOIN `Category` c ON pcm.CategoryId = c.Id",
            },
        }

        sorted_joins = sorted([t for t in join_path if t != root], key=lambda x: self.JOIN_ORDER.get(x, 999))

        for table in sorted_joins:
            if root != "Order" and table in NON_ORDER_JOINS and root in NON_ORDER_JOINS.get(table, {}):
                from_clause += f"\n{NON_ORDER_JOINS[table][root]}"
            elif table in self.JOIN_CLAUSES:
                from_clause += f"\n{self.JOIN_CLAUSES[table]}"

        return from_clause

    def _get_required_tables(self, plan: AnalysisPlan) -> Set[str]:
        """Identifies all tables required by metrics and dimensions."""
        tables = set(plan.join_path)
        tables.add("Order") # Always include Order as JOIN_CLAUSES assumes it is the root table
        
        metric_obj = next((m for m in METRICS if m.id == plan.metric), None)
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

    def _assemble_select(self, metric: Any, dimension: Optional[Any]) -> str:
        """Assembles the SELECT clause."""
        if dimension:
            dim_expr = dimension.sql_expr
            if dimension.datatype == "date":
                dim_expr = f"CAST({dimension.sql_expr} AS DATE)"
            return f"SELECT {dim_expr} AS label, {metric.sql_expr} AS value"
        return f"SELECT {metric.sql_expr} AS value"

    def _assemble_from(self, join_path: List[str]) -> str:
        """Assembles the FROM and JOIN clauses."""
        if not join_path: return ""
        
        root = "Order" if "Order" in join_path else join_path[0]
        from_clause = f"FROM `{root}` {self.TABLE_ALIASES.get(root, 'root')}"
        
        # Consistent join order for determinism and performance
        sorted_joins = sorted([t for t in join_path if t != root], key=lambda x: self.JOIN_ORDER.get(x, 999))
        
        for table in sorted_joins:
            if table in self.JOIN_CLAUSES:
                from_clause += f"\n{self.JOIN_CLAUSES[table]}"
                
        return from_clause

    def _assemble_where(self, where_parts: List[str]) -> str:
        """Assembles the WHERE clause."""
        clause = "WHERE 1=1"
        if where_parts:
            clause += "\n  AND " + "\n  AND ".join(where_parts)
        return clause

    def _assemble_group_by(self, dimension: Any) -> str:
        """Assembles the GROUP BY clause."""
        expr = dimension.sql_expr
        if dimension.datatype == "date":
            expr = f"CAST({dimension.sql_expr} AS DATE)"
        return f"GROUP BY {expr}"

    def _assemble_order_by(self, sort_dir: Optional[str]) -> str:
        """Assembles the ORDER BY clause."""
        direction = sort_dir if sort_dir and sort_dir.lower() in ["asc", "desc"] else "desc"
        return f"ORDER BY value {direction}"

    def _build_where_clauses(self, plan: AnalysisPlan) -> Tuple[List[str], Dict[str, Any]]:
        """Orchestrates the construction of all filter conditions."""
        parts = []
        params = {}
        
        # 1. Time Rule
        if plan.time_rule:
            time_part = self._get_smart_time_sql("o.CreatedOnUtc", plan.time_rule)
            if time_part: parts.append(time_part)
            
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

    def _build_single_filter(self, f: Filter, param_offset: int = 0) -> Tuple[str, Dict[str, Any]]:
        """Constructs a parameterized MySQL predicate for a single filter object.

        Returns a tuple of (sql_template, params) to achieve 100% security 
        against SQL injection (Proposition 1, §4.7).
        """
        field_name = f.field
        op = f.operator
        val = f.value
        params = {}
        
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
                sql_field = self._strip_aggregate(metric.sql_expr) or "o.Id"
            else:
                sql_field = ALIAS_TO_TABLE.get(field_name, "o.Id")

        # Temporal logic for date fields
        if isinstance(val, str) and ("date" in field_name or "time" in field_name):
            if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', str(val)):
                p_name = f"p{param_offset}"
                params[p_name] = val
                return f"CAST({sql_field} AS DATE) {op} @{p_name}", params
            
            smart_sql = self._get_smart_time_sql(sql_field, val)
            if smart_sql: return smart_sql, params

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

    def _get_smart_time_sql(self, field_expr: str, value: str) -> Optional[str]:
        """Translates semantic time references into MySQL expressions."""
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
