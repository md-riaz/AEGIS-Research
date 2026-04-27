"""
SafeDash SQL Compiler Module.

This module provides the SQLCompiler class, which transforms a validated 
AnalysisPlan into a production-safe T-SQL query for the nopCommerce schema.
It enforces architectural governance by using allow-listed templates and 
preventing raw LLM text from entering the SQL string.
"""

import re
import logging
from typing import List, Dict, Set, Optional, Any, Tuple
from .models import AnalysisPlan, Filter, FilterOperator
from .semantic_layer import METRICS, DIMENSIONS, JOIN_GRAPH, ALIAS_TO_TABLE

# Configure module-level logger
logger = logging.getLogger(__name__)

class SQLCompiler:
    """
    Deterministic SQL Compiler for SafeDash.
    
    Translates an abstract analysis plan into a safe SQL query using 
    constrained templates and validated join paths.
    """

    # Metadata for join relationships (Table Name -> Join Clause)
    JOIN_CLAUSES: Dict[str, str] = {
        "OrderItem": "INNER JOIN [OrderItem] oi ON o.Id = oi.OrderId",
        "Product": "INNER JOIN [Product] p ON oi.ProductId = p.Id",
        "Product_Category_Mapping": "INNER JOIN [Product_Category_Mapping] pcm ON p.Id = pcm.ProductId",
        "Category": "INNER JOIN [Category] c ON pcm.CategoryId = c.Id",
        "Customer": "INNER JOIN [Customer] cu ON o.CustomerId = cu.Id",
        "Manufacturer": "INNER JOIN [Manufacturer] m ON p.ManufacturerId = m.Id"
    }

    # Standard table aliases
    TABLE_ALIASES: Dict[str, str] = {
        "Order": "o",
        "OrderItem": "oi",
        "Product": "p",
        "Category": "c",
        "Product_Category_Mapping": "pcm",
        "Customer": "cu",
        "Manufacturer": "m"
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
        Compiles an AnalysisPlan into a T-SQL string.

        Args:
            plan (AnalysisPlan): The validated plan to compile.

        Returns:
            str: The generated T-SQL query.
        """
        logger.info(f"Compiling plan for pattern: {plan.pattern}")
        
        # 1. Identify required tables
        required_tables = self._get_required_tables(plan)
        
        # 2. Build WHERE clauses (Time + Filters)
        where_parts = self._build_where_clauses(plan)
        
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
            sql_parts.append(f"OFFSET 0 ROWS FETCH NEXT {plan.limit} ROWS ONLY")

        full_sql = "\n".join(sql_parts)
        return full_sql.strip()

    def _get_required_tables(self, plan: AnalysisPlan) -> Set[str]:
        """Identifies all tables required by metrics and dimensions."""
        tables = set(plan.join_path)
        
        metric_obj = next((m for m in METRICS if m.id == plan.metric), None)
        if metric_obj:
            tables.add(metric_obj.binding_table)
            
        if plan.dimension:
            dim_obj = next((d for d in DIMENSIONS if d.id == plan.dimension), None)
            if dim_obj:
                tables.add(dim_obj.binding_table)
                
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
        from_clause = f"FROM [{root}] {self.TABLE_ALIASES.get(root, 'root')}"
        
        # Consistent join order for determinism and performance
        order_key = {t: i for i, t in enumerate(["OrderItem", "Product", "Product_Category_Mapping", "Category", "Customer", "Manufacturer"])}
        sorted_joins = sorted([t for t in join_path if t != root], key=lambda x: order_key.get(x, 99))
        
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

    def _build_where_clauses(self, plan: AnalysisPlan) -> List[str]:
        """Orchestrates the construction of all filter conditions."""
        parts = []
        
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
            field_clauses = [self._build_single_filter(f) for f in fs]
            field_clauses = [c for c in field_clauses if c]
            if len(field_clauses) > 1:
                parts.append("(" + " OR ".join(field_clauses) + ")")
            elif field_clauses:
                parts.append(field_clauses[0])
                
        return parts

    def _build_single_filter(self, f: Filter) -> str:
        """Constructs a T-SQL predicate for a single filter object."""
        field_name = f.field
        val = f.value
        op = f.operator
        
        # Resolve field SQL expression
        dim = next((d for d in DIMENSIONS if d.id == field_name), None)
        sql_field = dim.sql_expr if dim else ALIAS_TO_TABLE.get(field_name, "o.Id")

        # Temporal logic for date fields
        if isinstance(val, str) and ("date" in field_name or "time" in field_name):
            if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}', val):
                return f"CAST({sql_field} AS DATE) {op} '{val}'"
            
            smart_sql = self._get_smart_time_sql(sql_field, val)
            if smart_sql: return smart_sql

        # Null checks
        if op == 'is_null': return f"{sql_field} IS NULL"
        if op == 'is_not_null': return f"{sql_field} IS NOT NULL"

        # List operators
        if isinstance(val, list) or op in ['in', 'not_in']:
            if not isinstance(val, list):
                val = [v.strip() for v in str(val).split(',')]
            items = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in val])
            prefix = "NOT " if op == 'not_in' else ""
            return f"{sql_field} {prefix}IN ({items})"

        # Range operators
        if op == 'between' and isinstance(val, list) and len(val) == 2:
            v1 = f"'{val[0]}'" if isinstance(val[0], str) else val[0]
            v2 = f"'{val[1]}'" if isinstance(val[1], str) else val[1]
            return f"{sql_field} BETWEEN {v1} AND {v2}"

        # String search
        if op == 'contains': return f"{sql_field} LIKE '%{val}%'"

        # Default equality/inequality
        formatted_val = f"'{val}'" if isinstance(val, str) else str(val)
        return f"{sql_field} {op} {formatted_val}"

    def _get_smart_time_sql(self, field_expr: str, value: str) -> Optional[str]:
        """Translates semantic time references into T-SQL expressions."""
        val = value.lower().replace("_", " ").strip()
        
        # Exact Day
        if val in ["today", "now", "current"]:
            return f"CAST({field_expr} AS DATE) = CAST(GETUTCDATE() AS DATE)"
        if val in ["yesterday"]:
            return f"CAST({field_expr} AS DATE) = CAST(DATEADD(day, -1, GETUTCDATE()) AS DATE)"
        
        # Relative Windows
        if val in ["now-1d", "now-24h", "past 24 hours"]:
            return f"{field_expr} >= DATEADD(hour, -24, GETUTCDATE())"
            
        # Bucketed Windows (Standard ISO definitions)
        if "week" in val:
            offset = -1 if "last" in val else 0
            return f"{field_expr} >= DATEADD(week, DATEDIFF(week, 0, GETUTCDATE()) + {offset}, 0)"
        
        if "month" in val:
            offset = -1 if "last" in val else 0
            return f"{field_expr} >= DATEADD(month, DATEDIFF(month, 0, GETUTCDATE()) + {offset}, 0)"
            
        if "year" in val:
            offset = -1 if "last" in val else 0
            return f"YEAR({field_expr}) = YEAR(GETUTCDATE()) + {offset}"
            
        return None
