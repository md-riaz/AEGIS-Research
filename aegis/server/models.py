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

from .time_grammar import TimeRange

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

class Confidence(str, Enum):
    """Self-reported confidence of the intent extraction stage."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IntentObject(BaseModel):
    """Structured intent extracted by the LLM from a natural-language query.

    Two fields carry the abstention channel added in the revised architecture:

    ``unmapped_terms``
        Content words the model could not account for with any approved metric,
        dimension, or filter.  A non-empty list means the model was *forced* to
        pick something from the closed vocabulary, which is the signature of an
        out-of-scope request.

    ``confidence``
        Defaults to ``LOW``.  The original implementation defaulted to ``high``
        and injected that default whenever the field was absent, which made the
        downstream confidence gate unreachable.  Absence of evidence is now
        treated as absence of confidence.
    """
    # ``validate_default`` matters here: Pydantic skips validation of field
    # defaults unless asked, so ``use_enum_values`` would not apply to them.
    # The default confidence would then surface as the ``Confidence.LOW`` enum
    # member while an explicitly supplied value surfaced as the string
    # ``"low"``.  Downstream code compares against strings, so a request that
    # said nothing about its confidence must not take a different shape from
    # one that reported low confidence outright.
    model_config = ConfigDict(use_enum_values=True, validate_default=True)

    intent_class: IntentClass
    metric_term: Optional[str] = None
    dimension_term: Optional[str] = None
    time_term: Optional[str] = None
    filters: List[Filter] = Field(default_factory=list)
    sort: Optional[str] = None
    limit: Optional[int] = None
    confidence: Confidence = Confidence.LOW
    needs_clarification: bool = False
    clarification_reason: Optional[str] = None
    unmapped_terms: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Grounding contracts (Stage 2)
# ---------------------------------------------------------------------------

class MatchKind(str, Enum):
    """How a candidate binding was found, ordered by decreasing reliability."""
    EXACT_ID = "exact_id"
    EXACT_LABEL = "exact_label"
    ALIAS = "alias"
    TOKEN_OVERLAP = "token_overlap"
    DESCRIPTION_OVERLAP = "description_overlap"


class Resolution(str, Enum):
    """Outcome of grounding one term against the semantic layer."""
    RESOLVED = "resolved"       # exactly one defensible binding
    AMBIGUOUS = "ambiguous"     # several bindings score comparably
    UNSUPPORTED = "unsupported" # nothing in the vocabulary accounts for it
    ABSENT = "absent"           # the request did not specify this slot


class GroundingCandidate(BaseModel):
    """One possible binding of a natural-language term to a semantic object."""
    id: str
    label: str
    score: float
    match_kind: MatchKind
    evidence: str


class Binding(BaseModel):
    """The full grounding record for a single slot (metric or dimension).

    Retaining the ranked alternatives — rather than collapsing to one string —
    is what makes clarification, explanation, and auditing possible.  The
    original resolver returned only the winner, so a wrong binding was
    indistinguishable from a right one at every later stage.
    """
    term: Optional[str] = None
    slot: str
    resolution: Resolution
    chosen: Optional[str] = None
    candidates: List[GroundingCandidate] = Field(default_factory=list)
    reason: Optional[str] = None


class CoverageReport(BaseModel):
    """What the semantic layer could and could not account for in a request.

    Gaps are graded, because they call for different responses:

    ``unmapped_concepts`` (hard gap)
        A domain concept with no binding at all — "bounce rate", "sentiment",
        "carrier". No combination of approved bindings expresses it, so the
        request is rejected.

    ``qualified_concepts`` (soft gap)
        A modifier on a concept that *is* bound — "net revenue", "new
        customers", "profit margin". The request is expressible; what differs
        is the definition the user assumed versus the one the semantic layer
        governs. The right response is to state the governed definition and
        let the user confirm, not to refuse.
    """
    unmapped_concepts: List[str] = Field(default_factory=list)
    qualified_concepts: List[str] = Field(default_factory=list)
    ambiguous_slots: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    #: True when the request asks for two distinct reports. A widget holds one
    #: result shape, so answering only the first half is a silent partial
    #: answer; the resolver offers to build both instead.
    compound_request: bool = False
    #: True when the request asks to change data. AEGIS structurally cannot
    #: express a write, so such a request is already safe — this flag exists so
    #: it is declined for the stated reason rather than incidentally, because
    #: some noun in the sentence failed to bind.
    write_request: bool = False

    @property
    def is_covered(self) -> bool:
        return not self.unmapped_concepts and not self.ambiguous_slots


class Outcome(str, Enum):
    """Terminal decision of the resolution stage."""
    ANSWER = "answer"     # bindings are complete and unambiguous
    CLARIFY = "clarify"   # a specific, answerable question for the user
    REJECT = "reject"     # nothing in the vocabulary can express this request


class AnalysisPlan(BaseModel):
    """Grounded analysis plan produced by SemanticResolver; consumed by SQLCompiler.

    ``time_range`` carries the normalised, half-open window.  ``time_rule``
    remains as the raw phrase for provenance and display only — the compiler
    reads ``time_range``, so an unnormalised phrase can no longer reach SQL.
    """
    model_config = ConfigDict(use_enum_values=True)

    pattern: str
    metric: str
    dimension: Optional[str] = None
    time_rule: Optional[str] = None
    time_range: Optional[TimeRange] = None
    join_path: List[str]
    filters: List[Filter] = Field(default_factory=list) # Standardized to Filter objects
    sort: Optional[str] = None
    limit: Optional[int] = None
    visual: str
    bindings: List[Binding] = Field(default_factory=list)
    coverage: CoverageReport = Field(default_factory=CoverageReport)


class ResolutionResult(BaseModel):
    """What the resolver returns: either a plan, or a reasoned non-answer.

    Making the non-answer a first-class return value — rather than an exception
    or a silently substituted default — is the structural change that lets the
    pipeline decline a request it cannot express.
    """
    outcome: Outcome
    plan: Optional[AnalysisPlan] = None
    bindings: List[Binding] = Field(default_factory=list)
    coverage: CoverageReport = Field(default_factory=CoverageReport)
    message: Optional[str] = None
    question: Optional[str] = None
    options: List[str] = Field(default_factory=list)
