# AEGIS

**Analytics Engine with Guaranteed Injection Safety** — a research prototype demonstrating a "Safety by Design" architecture for natural-language analytics interfaces. Unlike end-to-end LLM text-to-SQL approaches (which are prone to hallucinations and injection attacks), AEGIS uses the LLM *only* for intent extraction. A deterministic compiler then generates all SQL from allow-listed templates, mathematically guaranteeing that every executed query is safe, valid, and aligned with organizational access policies.

---

## System Overview

The pipeline has 7 stages, each a separate module:

| # | Stage | Module | Description |
|---|-------|--------|-------------|
| 1 | Intent Extraction | `aegis/server/intent_parser.py` | LLM maps natural language → structured `IntentObject` |
| 2 | Coverage Validation | `run_demo_server.py` | Rejects queries outside the semantic layer vocabulary |
| 3 | Semantic Mapping | `aegis/server/mapper.py` | Resolves terms to canonical IDs, expands business logic |
| 4 | Permission Rewriting | `aegis/server/permission_rewriter.py` | Appends row-level security predicates |
| 5 | SQL Compilation | `aegis/server/compiler.py` | Deterministic template-based SQL generation |
| 6 | Visualization Selection | `aegis/server/visualization.py` | Rule-based chart type selection |
| 7 | Widget Persistence | `aegis/server/widget_engine.py` | Stores widgets as JSON artifacts |

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
safedash-research/
├── aegis/
│   └── server/
│       ├── intent_parser.py      # Stage 1: LLM intent extraction
│       ├── mapper.py             # Stage 3: semantic mapping
│       ├── permission_rewriter.py# Stage 4: row-level security
│       ├── compiler.py           # Stage 5: SQL compilation
│       ├── visualization.py      # Stage 6: chart selection
│       ├── widget_engine.py      # Stage 7: widget persistence
│       ├── semantic_layer.py     # Closed vocabulary (metrics, dimensions, joins)
│       ├── models.py             # Pydantic contracts between stages
│       ├── database_client.py    # MySQL connector wrapper
│       └── ai_config.py          # LLM provider config and rate limiting
├── database/
│   ├── schema.sql                # nopCommerce table DDL
│   ├── mock_data.sql             # Pre-generated test data
│   ├── generate_data.py          # Synthetic data generator
│   ├── generate_mock.py          # Alternative mock data script
│   └── fix_sql.py                # SQL utility/repair script
├── evaluation_dataset/
│   ├── questions.json            # 100-query benchmark dataset
│   ├── generate_dataset.py       # Dataset generation script
│   └── evaluate_metrics.py       # Metric computation script
├── static/
│   └── index.html                # Single-page dashboard frontend
├── demo/
│   └── demo_dashboard.json       # Saved dashboard layout (generated)
├── docs/
│   ├── AEGIS_Manuscript.md       # Research paper (Markdown)
│   ├── AEGIS_Manuscript.tex      # Research paper (LaTeX)
│   └── analysis/                 # Supporting analysis documents
├── tests/
│   ├── test_mapper.py            # Unit tests for SemanticMapper
│   ├── test_compiler.py          # Integration smoke-tests for compiler
│   └── test_query.py             # End-to-end tests (requires server)
├── run_demo_server.py            # FastAPI server entry point
├── run_demo_cli.py               # CLI pipeline demo
├── run_benchmark.py              # Benchmark runner (AEGIS vs. baseline)
└── requirements.txt
```

---

## Running Tests

Unit tests cover the semantic mapper, SQL compiler, and coverage validation:

```bash
python -m unittest discover -s tests
```

For the integration smoke-test (prints SQL without a database):

```bash
python tests/test_compiler.py
```

---

## Running the Benchmark

The benchmark processes all 100 queries in `evaluation_dataset/questions.json`,
comparing AEGIS output against a direct LLM baseline:

```bash
python run_benchmark.py           # resume from last checkpoint
python run_benchmark.py --rerun   # force full re-evaluation
```

Results are written to `evaluation_dataset/benchmark_results.json`.

---

## Research Paper

The full manuscript is at [`docs/AEGIS_Manuscript.md`](docs/AEGIS_Manuscript.md) (also available as LaTeX source in `docs/AEGIS_Manuscript.tex`). It covers the formal safety proof, architecture design decisions, and evaluation methodology.
