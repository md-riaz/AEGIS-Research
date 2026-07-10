# AEGIS: A Safety-by-Design Architecture for LLM-Driven Self-Service Analytics

**AEGIS** *(Analytics Engine with Guaranteed Injection Safety)* — a research prototype that turns plain-English reporting requests into dynamic, refreshable dashboard widgets using a strictly controlled pipeline where the LLM never generates SQL.

> **Core thesis:** AEGIS doesn't try to make AI-generated SQL safe — it makes the AI generate *intentions* instead, then uses a deterministic compiler to generate SQL from a pre-approved menu. The AI can't inject because it never touches SQL.

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
 │  (Stages 2–7)            │    metric/dimension names are compile-time constants; values are parameterized
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
| `item_quantity` | `SUM(COALESCE(oi.Quantity, 0))` |
| `shipping_cost` | `SUM(o.OrderShippingExclTax)` |
| `customer_count` | `COUNT(DISTINCT cu.Id)` |
| `profit` | `SUM(COALESCE(o.OrderTotal, 0) - COALESCE(o.OrderSubtotalExclTax, 0))` |

The LLM outputs `"metric": "revenue"`. The compiler substitutes the literal SQL. **No LLM output ever touches aggregate logic.**

### 34 Dimensions — Grouping and Filtering Axes

Dimensions define what you can slice by. They range from simple column references to complex CASE expressions and cross-table lookups:

```python
# Simple column reference
Dimension(id="order_month", label="Order Month",
          description="Month when the order was placed",
          sql_expr="DATE_FORMAT(o.CreatedOnUtc, '%Y-%m')",
          binding_table="Order", datatype="string")

# Pre-approved CASE expression — complex logic, but a fixed constant
Dimension(id="order_status", label="Order Status",
          description="Human-readable order status label",
          sql_expr="""CASE o.OrderStatusId
              WHEN 10 THEN 'Pending'   WHEN 20 THEN 'Processing'
              WHEN 30 THEN 'Complete'  WHEN 40 THEN 'Cancelled'
              ELSE 'Unknown' END""",
          binding_table="Order", datatype="string")

# Cross-table dimension — requires compiler to resolve joins via BFS
Dimension(id="category_name", label="Category",
          description="Product category name",
          sql_expr="c.Name", binding_table="Category", datatype="string",
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
BUSINESS_LOGIC_MAPPINGS = {
    "abandoned": {"field": "OrderStatusId", "operator": "=", "value": 40}
}
```

Abstract business terms that map to concrete SQL predicates. "Show me abandoned orders" → the mapper rewrites to a filter `OrderStatusId = 40` before SQL compilation.

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
2. **Post-compilation safety scanner**: 16 forbidden patterns (DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE, UNION, EXCEPT, INTERSECT, EXEC, CREATE, GRANT, REVOKE, xp_, sys., INFORMATION_SCHEMA) are checked after compilation as a defense-in-depth measure.

---

## Benchmark Results (100 Queries)

| System | Unsafe SQL | Execution Validity | Coverage |
|--------|-----------|-------------------|----------|
| B1: Direct LLM-to-SQL | 5.0% | 99.0% | 99.0% |
| B2: Decomposed LLM | 3.0% | 97.0% | 97.0% |
| B3: Template-only (no LLM) | 1.0% | 66.0% | 55.0% |
| B4: AEGIS ablated (no semantic layer) | 0.0% | 88.7% | 91.0% |
| **AEGIS (full)** | **0.0%** | **100.0%** | **100.0%** |

The 0% unsafe SQL rate is not a statistical result — it follows from the architecture. The benchmark confirms it empirically; the formal proof guarantees it structurally.

### Generalizability

To validate that AEGIS is not tightly coupled to the nopCommerce schema, the system was ported to a **WooCommerce** database schema:

- 98% intent accuracy on the WooCommerce benchmark
- 14 person-hours to build the new semantic layer
- Zero changes to the pipeline, compiler, or LLM configuration

---

## Deploying AEGIS on a New Schema (e.g., WooCommerce)

> **Key principle:** Only the semantic layer changes. The LLM, compiler, safety scanner, visualization engine, and widget system are schema-agnostic and require zero modification.

A WooCommerce store owner (or any operator with a different database schema) can onboard AEGIS by following these steps. The WooCommerce evaluation in this thesis took **14 person-hours** end-to-end.

### Step 1 — Prerequisites (~30 min)

- Python 3.10+, pip, Git
- MySQL read access to the WooCommerce database
- An API key for any OpenAI-compatible LLM endpoint ([Groq free tier](https://console.groq.com) works out of the box)

```bash
git clone https://github.com/md-riaz/AEGIS-Research.git
cd AEGIS-Research
pip install -r requirements.txt
cp .env.example .env          # fill in DB credentials and LLM_BASE_URL + LLM_API_KEY
```

### Step 2 — Analyse the Schema (~2–3 hours)

Inspect the target database and answer these questions — they map directly to the semantic layer:

| Question | Semantic layer element |
|----------|-----------------------|
| What KPIs does the business track? (revenue, orders, refunds…) | → `METRICS` |
| What do they slice reports by? (month, category, country…) | → `DIMENSIONS` |
| How are the tables joined? (orders → items → products…) | → `JOIN_GRAPH` |
| What business shorthand is used? ("abandoned", "returning", "VIP"…) | → `BUSINESS_LOGIC_MAPPINGS` |

For WooCommerce the key tables are: `wc_orders`, `wc_order_items`, `wc_order_addresses`, `wp_posts` (products), `wp_terms` (categories), `wp_users` (customers), and related meta tables.

### Step 3 — Build the Semantic Layer (~8–10 hours)

Create a new `aegis/server/semantic_layer.py` (or copy and edit the existing one). The WooCommerce layer built in this thesis had:

- **12 metrics** — revenue, order count, average order value, item quantity, refund amount, customer count, shipping cost, coupon discount, product revenue, tax, fulfilment rate, review score
- **28 dimensions** — order date (day/week/month/quarter/year), order status, payment method, product name, category, customer city/country, shipping zone, coupon code, store currency
- **9 join paths** — wc_orders → wc_order_items → products → categories; wc_orders → wc_order_addresses; wc_orders → wp_users; etc.

**Example metric (WooCommerce):**
```python
Metric(
    id="revenue",
    label="Total Revenue",
    description="Net revenue after refunds",
    sql_expr="SUM(COALESCE(o.total_amount, 0) - COALESCE(o.refund_amount, 0))",
    binding_table="wc_orders",
    default_visual="kpi_card"
)
```

**Example dimension (WooCommerce):**
```python
Dimension(
    id="order_month",
    label="Order Month",
    description="Month when the order was placed",
    sql_expr="DATE_FORMAT(o.date_created_gmt, '%Y-%m')",
    binding_table="wc_orders",
    datatype="string"
)
```

**Example join path (WooCommerce):**
```python
JoinPath(
    source="wc_orders",
    target="wc_order_items",
    on_clause="o.id = oi.order_id"
)
```

### Step 4 — Configure the Database Client (~30 min)

In `.env`, set the WooCommerce database credentials:

```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_woocommerce_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Any OpenAI-compatible endpoint:
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=your_api_key
LLM_MODEL=llama-3.1-8b-instant
```

No changes to `database_client.py` are needed — it reads these at runtime.

### Step 5 — Test (~1–2 hours)

```bash
# Run the unit tests (mapper, compiler, coverage validator)
python -m unittest discover -s tests

# Interactive CLI: try a few natural-language questions
python run_demo_cli.py
# > "Show me total revenue by product category this month"
# > "Which customers placed the most orders last quarter?"
# > "What is the average order value for orders over $100?"
```

Verify that the generated SQL references the correct WooCommerce table and column names. If a query fails coverage validation, a metric or dimension is missing from the semantic layer — add it and re-test.

### Step 6 — Deploy (~30 min)

```bash
# Docker (recommended for production)
docker-compose up --build
# Dashboard at http://localhost:8765

# Or run directly
python run_demo_server.py
```

### What You Do NOT Need to Change

| Component | Why it is schema-agnostic |
|-----------|--------------------------|
| `intent_parser.py` | LLM prompt injects your new vocabulary automatically |
| `mapper.py` | Maps whatever IDs your semantic layer defines |
| `compiler.py` | Templates work with any SQL aliases and table names |
| `permission_rewriter.py` | Predicate injection is vocabulary-independent |
| `visualization.py` | Chart selection depends on pattern type, not schema |
| `widget_engine.py` | Widget lifecycle is schema-agnostic |

### Effort Estimate

Based on the WooCommerce evaluation in this thesis:

| Task | Estimated time |
|------|----------------|
| Schema analysis and table mapping | 2–3 hours |
| Writing metrics (SQL aggregate expressions) | 2–3 hours |
| Writing dimensions (column expressions + join requirements) | 3–4 hours |
| Defining join paths | 1 hour |
| Testing and iteration | 2 hours |
| **Total** | **~14 person-hours** |

---

## Quick Start

```bash
# 1. Copy the env template
cp .env.example .env

# 2. Configure your LLM provider (see "LLM Provider Setup" below)
# 3. Start with Docker (recommended)
docker-compose up --build
# Dashboard available at http://localhost:8765

# Or run locally
pip install -r requirements.txt
python run_demo_server.py
```

---

## LLM Provider Setup

AEGIS supports **any OpenAI-compatible API** — Groq, OpenRouter, OmniRoute, a local Ollama instance, or any other provider that speaks the `/v1/chat/completions` protocol.

### Option A — Generic OpenAI-compatible provider (recommended)

Set three variables in `.env` and AEGIS will route all LLM calls through that endpoint, regardless of model name:

```env
LLM_BASE_URL=https://api.groq.com/openai/v1   # your provider's base URL
LLM_API_KEY=your_api_key_here
LLM_MODEL=llama-3.1-8b-instant                # any model the endpoint accepts
```

Examples for common providers:

| Provider | `LLM_BASE_URL` | Notes |
|----------|----------------|-------|
| [Groq](https://console.groq.com) | `https://api.groq.com/openai/v1` | Free tier available |
| [OpenRouter](https://openrouter.ai) | `https://openrouter.ai/api/v1` | Routes to GPT-4, Claude, Llama, etc. |
| OmniRoute / custom | `http://localhost:20128/v1` | Self-hosted gateway |
| [Ollama](https://ollama.com) (local) | `http://localhost:11434/v1` | Fully offline |

Optional rate-limit overrides (defaults are conservative):

```env
LLM_RPM=30    # requests per minute
LLM_RPD=14400 # requests per day
```

### Option B — Groq only (legacy / backward-compatible)

If `LLM_BASE_URL` is **not** set, AEGIS falls back to the original Groq-specific path:

```env
GROQ_API_KEY=your_groq_api_key_here
```

The model defaults to `llama-3.1-8b-instant`. To use `llama-3.3-70b-versatile` instead, change `GROQ_MODELS[0]` in `aegis/server/ai_config.py` or set `LLM_MODEL` alongside `LLM_BASE_URL`.

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
│   ├── schema.sql                # nopCommerce table DDL (126 tables, 107 FK constraints)
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
├── run_benchmark.py              # Benchmark runner (AEGIS vs. baseline)
└── requirements.txt              # Python dependencies
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
