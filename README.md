# AEGIS

**Analytics Engine with Guaranteed Injection Safety** — a research prototype demonstrating a "Safety by Design" architecture for natural-language analytics interfaces.

> **One-line pitch:** AEGIS doesn't try to make AI-generated SQL safe — it makes the AI generate *intentions* instead, then uses a deterministic compiler to generate SQL from a pre-approved menu. The AI can't inject because it never touches SQL.

---

## The Problem with Every Prior Approach

Every existing NL-to-SQL system shares the same fundamental flaw: **the LLM writes SQL**. Whether it's GPT-4, a fine-tuned model, or a retrieval-augmented system, the LLM generates a string that gets executed against your database. This creates two compounding problems:

1. **Injection**: A malicious user can craft a question that manipulates the LLM into generating `DROP TABLE`, `UNION SELECT passwords`, or data exfiltration queries.
2. **Hallucination**: LLMs invent column names, join conditions, and aggregation logic that *look* correct but produce wrong answers — silently.

Prior work addresses these with *detection*: post-hoc filters, validators, and classifiers that try to catch bad SQL after the LLM generates it. AEGIS's core thesis rejects this approach entirely.

---

## Core Novelty: Structural Safety, Not Detection

AEGIS enforces a hard architectural split between the AI layer and the SQL layer:

```
Natural Language Query
        │
        ▼
 ┌─────────────┐
 │  LLM Layer  │  ← Only job: "which metric? which dimension? which filter?"
 │  (Stage 1)  │    Output: structured IntentObject (JSON, no SQL)
 └─────────────┘
        │
        ▼
 ┌──────────────────────────┐
 │  Deterministic Compiler  │  ← SQL generated here, from allow-listed templates only
 │  (Stages 2–7)            │    LLM output never reaches this layer as raw text
 └──────────────────────────┘
        │
        ▼
   Safe, Valid SQL
```

The LLM **never sees the database schema**. It cannot produce SQL. It can only select from a pre-approved vocabulary defined in the semantic layer. This is not a design choice — it is a mathematical guarantee backed by a formal safety proof in the manuscript.

**Formal claim:** *Given that the SQL compiler only accepts validated `IntentObject` inputs and generates SQL exclusively from pre-defined templates, the set of possible SQL outputs is finite and enumerable. SQL injection requires generating SQL outside this set, which is architecturally impossible.*

---

## Why This Is Novel vs. Prior Work

| Property | End-to-End NL2SQL | AEGIS |
|----------|-------------------|-------|
| SQL injection possible? | Yes — LLM can be prompted into it | **Structurally impossible** |
| Hallucinated column names? | Yes — LLM invents schema | **Impossible** — SQL expressions are pre-compiled constants |
| Schema exposure to LLM | LLM sees full DDL | **LLM never sees schema** |
| Safety mechanism | Detection (post-hoc filters) | **Prevention (structural)** |
| Access control enforcement | Hope LLM respects it | **Permission rewriter appends WHERE clauses deterministically** |
| Auditability | Must inspect every LLM output | **Inspect 15 metrics + 34 dimensions** — complete, finite |
| New schema support | Re-train or re-prompt | **Build semantic layer (~14 person-hours for WooCommerce)** |

---

## The Semantic Layer: The Closed Vocabulary

The semantic layer (`aegis/server/semantic_layer.py`) is the heart of the system. It defines the **complete, enumerable set of things AEGIS can answer**. Every query is validated against this vocabulary before any SQL is generated.

### 15 Metrics — Named SQL Aggregate Expressions

Each metric is a SQL fragment the LLM can *reference by ID* but never modify. Examples:

| ID | SQL Expression |
|----|----------------|
| `revenue` | `SUM(COALESCE(o.OrderTotal, 0) - COALESCE(o.RefundedAmount, 0))` |
| `order_count` | `COUNT(DISTINCT o.Id)` |
| `avg_order_value` | `AVG(COALESCE(o.OrderTotal, 0))` |
| `customer_ltv` | `SUM(o.OrderTotal) / COUNT(DISTINCT o.CustomerId)` |
| `refund_rate` | `100.0 * SUM(o.RefundedAmount) / NULLIF(SUM(o.OrderTotal), 0)` |
| `cart_abandonment_rate` | Ratio of incomplete-to-total shopping cart records |
| `inventory_turnover` | COGS / average inventory value |

The LLM outputs `"metric": "revenue"`. The compiler substitutes the literal SQL. **No LLM output ever touches aggregate logic.**

### 34 Dimensions — Grouping and Filtering Axes

Dimensions define what you can slice by. They range from simple column references to complex CASE expressions and cross-table lookups:

```python
# Simple column reference
Dimension(id="order_month",  sql_expr="DATE_FORMAT(o.CreatedOnUtc, '%Y-%m')")

# Pre-approved CASE expression — complex logic, but a fixed constant
Dimension(id="order_status", sql_expr="""
    CASE o.OrderStatusId
        WHEN 10 THEN 'Pending'   WHEN 20 THEN 'Processing'
        WHEN 30 THEN 'Complete'  WHEN 40 THEN 'Cancelled'
        ELSE 'Unknown' END""")

# Cross-table dimension — requires compiler to resolve joins via BFS
Dimension(id="category_name", sql_expr="c.Name", binding_table="Category",
          required_joins=["Product_Category_Mapping", "Category"])
```

The 34 dimensions span: order timing (day/week/month/quarter/year), order status, geography (city/state/country), product attributes, customer segments, shipment status, store identity, and price ranges.

### 11 JOIN_GRAPH Paths — BFS-Resolved Joins

The compiler uses an undirected graph of 11 pre-approved JOIN clauses. When a query needs a metric from one table and a dimension from another, the compiler runs **Breadth-First Search** to find the minimal join path:

```
Order ──── Customer ──── Address ──── Country
  │
  └──── OrderItem ──── Product ──── Category
                          │
                     Manufacturer
```

Example: `revenue` (bound to `Order`) broken down by `category_name` (bound to `Category`) → BFS resolves: `Order → OrderItem → Product → Product_Category_Mapping → Category`. The FROM/JOIN clauses are assembled automatically from pre-approved `ON` clauses. **No join logic is ever LLM-generated.**

### Vocabulary Injection — How the LLM Knows Business Terms

```python
SYNONYMS = {}  # intentionally empty
```

If a user asks "show me sales by product line", how does AEGIS know `sales = revenue` and `product line = category_name`?

The LLM learns this **at inference time** through the system prompt. All 15 metric labels and 34 dimension labels are injected into the LLM's system prompt (~1,100 tokens). The LLM maps natural language to the closest approved ID. No hard-coded synonym dictionary is needed. The LLM handles fuzzy matching; the compiler handles execution. This also eliminates a maintenance burden — adding a new business term requires no code change.

### Business Logic Mappings

```python
BUSINESS_LOGIC_MAPPINGS = {"abandoned": {"OrderStatusId": 40}}
```

Abstract business terms that map to specific database values. "Show me abandoned orders" → the mapper rewrites to a filter on `OrderStatusId = 40` before SQL compilation.

---

## The 7-Stage Pipeline

| # | Stage | Module | Description |
|---|-------|--------|-------------|
| 1 | Intent Extraction | `aegis/server/intent_parser.py` | LLM maps natural language → structured `IntentObject` |
| 2 | Coverage Validation | `run_demo_server.py` | Rejects queries outside the semantic layer vocabulary |
| 3 | Semantic Mapping | `aegis/server/mapper.py` | Resolves terms to canonical IDs, expands business logic |
| 4 | Permission Rewriting | `aegis/server/permission_rewriter.py` | Appends row-level security predicates (WHERE clauses) |
| 5 | SQL Compilation | `aegis/server/compiler.py` | Deterministic template-based SQL generation with BFS join resolution |
| 6 | Visualization Selection | `aegis/server/visualization.py` | Rule-based chart type selection (11 analytics primitives) |
| 7 | Widget Persistence | `aegis/server/widget_engine.py` | SHA-256 deduplication, storage, scheduled refresh |

### Two-Layer SQL Safety

The compiler enforces safety at two levels:

1. **Parameterized templates**: All SQL is assembled from pre-defined template fragments. User-controlled values are always bound as parameters, never interpolated.
2. **Post-compilation safety scanner**: 16 forbidden patterns (DROP, DELETE, INSERT, UNION, comment sequences, etc.) are checked after compilation as a defense-in-depth measure.

---

## Benchmark Results (100 Queries)

| System | Unsafe SQL | Execution Validity | Coverage |
|--------|-----------|-------------------|----------|
| B1: Direct GPT-4 | 5.0% | 99.0% | 99.0% |
| B2: Schema-Aware Prompt | 3.0% | 97.0% | 97.0% |
| B3: Few-Shot NL2SQL | 1.0% | 66.0% | 55.0% |
| B4: RAG-Enhanced | 0.0% | 88.7% | 91.0% |
| **AEGIS** | **0.0%** | **100.0%** | **100.0%** |

The 0% unsafe SQL rate is not a statistical result — it follows from the architecture. The benchmark confirms it empirically; the formal proof guarantees it structurally.

### Generalizability

To validate that AEGIS is not tightly coupled to the nopCommerce schema, the system was ported to a **WooCommerce** database schema:

- 98% intent accuracy on the WooCommerce benchmark
- 14 person-hours to build the new semantic layer
- Zero changes to the pipeline, compiler, or LLM configuration

---

## Quick Start

```bash
# 1. Copy and fill in your Groq API key
cp .env.example .env

# 2. Start with Docker (recommended)
docker-compose up --build
# Dashboard available at http://localhost:8765

# 3. Or run locally
pip install -r requirements.txt
python run_demo_server.py
```

---

## Project Structure

```
AEGIS-Research/
├── aegis/
│   └── server/
│       ├── semantic_layer.py     # Closed vocabulary: 15 metrics, 34 dimensions, 11 join paths
│       ├── intent_parser.py      # Stage 1: LLM intent extraction -> IntentObject
│       ├── mapper.py             # Stage 3: semantic mapping + business logic expansion
│       ├── permission_rewriter.py# Stage 4: row-level security WHERE clause injection
│       ├── compiler.py           # Stage 5: BFS join resolution + template SQL generation
│       ├── visualization.py      # Stage 6: rule-based chart type selection
│       ├── widget_engine.py      # Stage 7: SHA-256 dedup + widget persistence
│       ├── models.py             # Pydantic contracts between pipeline stages
│       ├── database_client.py    # MySQL connector wrapper
│       └── ai_config.py          # LLM provider config and rate limiting
├── database/
│   ├── schema.sql                # nopCommerce table DDL (16 tables)
│   ├── mock_data.sql             # Pre-generated test data
│   ├── generate_data.py          # Synthetic data generator
│   └── generate_mock.py          # Alternative mock data script
├── evaluation_dataset/
│   ├── questions.json            # 100-query benchmark dataset
│   ├── generate_dataset.py       # Dataset generation script
│   └── evaluate_metrics.py       # Metric computation script
├── docs/
│   ├── AEGIS_Manuscript.md       # Research paper (Markdown)
│   ├── AEGIS_Manuscript.tex      # Research paper (LaTeX)
│   ├── scripts/
│   │   └── generate_figures.py   # Reproducible figure generation (matplotlib)
│   └── analysis/                 # Supporting analysis documents
├── static/
│   └── index.html                # Single-page dashboard frontend
├── tests/
│   ├── test_mapper.py            # Unit tests for SemanticMapper
│   ├── test_compiler.py          # Integration smoke-tests for compiler
│   └── test_query.py             # End-to-end tests (requires running server)
├── run_demo_server.py            # FastAPI server entry point
├── run_demo_cli.py               # CLI pipeline demo
└── run_benchmark.py              # Benchmark runner (AEGIS vs. baseline)
```

---

## Running Tests

```bash
# Unit tests: semantic mapper, SQL compiler, coverage validation
python -m unittest discover -s tests

# Integration smoke-test: prints generated SQL without a database connection
python tests/test_compiler.py
```

---

## Running the Benchmark

```bash
python run_benchmark.py           # resume from last checkpoint
python run_benchmark.py --rerun   # force full re-evaluation
```

Results are written to `evaluation_dataset/benchmark_results.json`. The benchmark compares AEGIS against four baselines across 100 natural-language analytics queries.

---

## Research Paper

The full manuscript is at [`docs/AEGIS_Manuscript.md`](docs/AEGIS_Manuscript.md) (LaTeX source: [`docs/AEGIS_Manuscript.tex`](docs/AEGIS_Manuscript.tex)).

It covers:
- Formal safety proof (Section 5)
- Semantic layer design and vocabulary injection mechanism (Section 4)
- SQL compilation with BFS join resolution (Section 4.5)
- Benchmark evaluation against 4 baselines (Section 6)
- Ablation study: contribution of each pipeline stage (Section 6.6)
- Generalizability evaluation on WooCommerce schema (Section 6.7)
- End-to-end latency breakdown (Section 6.8)
