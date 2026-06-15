"""
AEGIS typed data contracts between pipeline stages.

Each Pydantic model represents the output of one pipeline stage and the
expected input of the next.  The flow is:

  IntentObject  (Stage 1 output — intent_parser.py)
      ↓
  AnalysisPlan  (Stage 2 output — mapper.py)
      ↓
  SQL + params  (Stage 3 output — compiler.py)
      ↓
  VisualizationSpec (Stage 4 output — visualization.py, defined there)
      ↓
  Widget        (Stage 5 output — widget_engine.py, defined there)
"""

from enum import Enum
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class IntentClass(str, Enum):
    """
    Ten reusable analytics primitives that cover the majority of
    institutional reporting needs.  Mapping to visual diagram labels:
        Aggregate → KPI, Filter → Exception, Group → Summary,
        Compare → Comparison, Rank → Ranking, Trend → Trend,
        Segment → Segment, Funnel → Funnel, Cohort → Cohort,
        Correlate → Correlate, Tabular → Tabular.
    """
    KPI = "kpi"                   # Aggregate – single scalar fact
    RANKING = "ranking"           # Rank – Top/Bottom N lists
    TREND = "trend"               # Trend – time-series analysis
    COMPARISON = "comparison"     # Compare – side-by-side groups
    EXCEPTION = "exception"       # Filter – threshold / anomaly
    SUMMARY = "summary"           # Group – multi-metric overview
    SEGMENT = "segment"           # Segment – breakdown by category
    FUNNEL = "funnel"             # Funnel – conversion stages
    COHORT = "cohort"             # Cohort – defines a "who" group
    CORRELATE = "correlate"       # Correlate – defines a "what" relation
    TABULAR = "tabular"           # Tabular – Direct record retrieval

class FilterOperator(str, Enum):
    """Allowed comparison operators for WHERE-clause filter predicates."""
    EQ = "="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    NEQ = "!="
    NOT_EQ = "<>"
    CONTAINS = "contains"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"

class Filter(BaseModel):
    """A single WHERE-clause predicate: field, operator, and value."""
    model_config = ConfigDict(use_enum_values=True)

    field: str
    operator: Union[FilterOperator, str]
    value: Any # Be flexible here for raw LLM values before mapping

class IntentObject(BaseModel):
    """Structured intent extracted by the LLM from a natural-language query."""
    model_config = ConfigDict(use_enum_values=True)

    intent_class: IntentClass
    metric_term: Optional[str] = "order_count"
    dimension_term: Optional[str] = None
    time_term: Optional[str] = None
    filters: List[Filter] = Field(default_factory=list)
    sort: Optional[str] = None
    limit: Optional[int] = None
    confidence: str = "high"
    needs_clarification: bool = False
    clarification_reason: Optional[str] = None

class AnalysisPlan(BaseModel):
    """Grounded analysis plan produced by SemanticMapper; consumed by SQLCompiler."""
    model_config = ConfigDict(use_enum_values=True)

    pattern: str
    metric: str
    dimension: Optional[str] = None
    time_rule: Optional[str] = None
    join_path: List[str]
    filters: List[Filter] = Field(default_factory=list) # Standardized to Filter objects
    sort: Optional[str] = None
    limit: Optional[int] = None
    visual: str
