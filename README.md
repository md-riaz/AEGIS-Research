# AEGIS: A Constraint-Based Architecture for Safe LLM-Assisted Natural Language Analytics

**AEGIS** *(Analytics Engine with Guaranteed Injection Safety)* — a research prototype that converts plain-English reporting requests into dynamic, refreshable dashboard widgets. The LLM never generates SQL; it only extracts intent. A deterministic compiler generates SQL from pre-approved templates.

> Research paper: [`docs/AEGIS_Manuscript.md`](docs/AEGIS_Manuscript.md) · LaTeX source: [`docs/AEGIS_Manuscript.tex`](docs/AEGIS_Manuscript.tex) · Defense guide: [`EXPLAINER.md`](EXPLAINER.md)

---

## The Problem

Business users need answers from their database but can't write SQL. Existing NL-to-SQL tools let the LLM generate SQL directly, which creates security and governance risks: the model can be prompted into producing unsafe queries, it may hallucinate column names, and there is no way to enforce consistent business metric definitions.

---

## How AEGIS Works

```
Natural Language Query
        │
        ▼
┌─────────────────────┐
│  Stage 1 — LLM      │  ← ONLY AI stage. Output: typed JSON (no SQL)
│  Intent Extraction  │    LLM never sees schema DDL
└─────────────────────┘
        │
        ▼  ── Pydantic validation gate ──────────────────────────────
        │
┌─────────────────────┐
│  Stage 2–7          │  Fully deterministic. No AI.
│  Deterministic      │  Coverage validation → Semantic mapping →
│  Pipeline           │  Permission rewriting → SQL compilation →
│                     │  Visualization selection → Widget persistence
└─────────────────────┘
        │
        ▼
  Dashboard Widget
```

The LLM picks from a **closed vocabulary** of 15 metrics and 34 dimensions defined in the semantic layer. It cannot reference a table, column, or join path that isn't in that vocabulary — because it never sees the schema. SQL is assembled from parameterized templates by the compiler, not by the model.

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/md-riaz/AEGIS-Research.git
cd AEGIS-Research
pip install -r requirements.txt

# Configure (copy and fill in your LLM provider and DB credentials)
cp .env.example .env

# Run with Docker (recommended)
docker-compose up --build
# Dashboard: http://localhost:8765

# Or run locally
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

If `LLM_BASE_URL` is not set, AEGIS falls back to Groq using `GROQ_API_KEY`.

---

## Project Structure

```
AEGIS-Research/
├── aegis/server/
│   ├── semantic_layer.py      # 15 metrics, 34 dimensions, 11 join paths
│   ├── intent_parser.py       # Stage 1: LLM → IntentObject (only AI code)
│   ├── mapper.py              # Stage 3: business logic expansion
│   ├── permission_rewriter.py # Stage 4: row-level security WHERE injection
│   ├── compiler.py            # Stage 5: BFS join resolution + template SQL
│   ├── visualization.py       # Stage 6: rule-based chart selection
│   ├── widget_engine.py       # Stage 7: SHA-256 dedup + persistence
│   └── ai_config.py           # LLM provider config and rate limiting
├── database/
│   ├── schema.sql                # nopCommerce table DDL (126 tables, 107 FK constraints)
│   ├── mock_data.sql             # Pre-generated test data
│   ├── generate_data.py          # Synthetic data generator
│   └── generate_mock.py          # Alternative mock data script
├── evaluation_dataset/
│   ├── questions.json         # 100-query prototype evaluation dataset
│   └── benchmark_results.json # Recorded pipeline outputs
├── docs/
│   ├── AEGIS_Manuscript.md    # Full research paper (Markdown)
│   └── AEGIS_Manuscript.tex   # Full research paper (LaTeX)
├── EXPLAINER.md               # Visual guide + defense Q&A
├── run_demo_server.py         # FastAPI server entry point
├── run_demo_cli.py            # CLI pipeline demo
└── run_benchmark.py           # Prototype evaluation runner
```

---

## Running Tests

```bash
# Unit tests: semantic mapper and SQL compiler
python -m unittest tests/test_mapper.py -v
PYTHONPATH=. python tests/test_compiler.py

# Integration tests (requires running server)
python tests/test_query.py
```

---

## Prototype Evaluation

The prototype was evaluated on a domain-specific 100-query dataset over the nopCommerce e-commerce schema. See [`evaluation_dataset/`](evaluation_dataset/) for the full question set and recorded results.

```bash
python run_benchmark.py           # resume from checkpoint (10 queries in CI)
python run_benchmark.py --limit 0 # run all 100 queries
python run_benchmark.py --rerun   # force full re-evaluation
```

Results are written to `evaluation_dataset/benchmark_results.json`.

---

## Deploying on a New Schema

Only the semantic layer changes — the LLM, compiler, and safety scanner require zero modification. The WooCommerce evaluation in this research took **14 person-hours** end-to-end. See [EXPLAINER.md § Adding a New Schema](EXPLAINER.md#9-adding-a-new-schema-eg-woocommerce) for a step-by-step guide.

---

## Research Paper

The full manuscript (`docs/AEGIS_Manuscript.md`) covers:

- Formal safety model and threat boundary (§4.2–4.3)
- Semantic layer design and vocabulary injection (§4.4–4.5)
- SQL compilation with BFS join resolution (§4.7)
- Prototype evaluation against 4 baselines (§6)
- Generalizability study on WooCommerce (§6.8)
- Limitations and future work (§8)

For committee Q&A preparation, architecture diagrams, and a complete walkthrough of a query through all 7 stages, see [`EXPLAINER.md`](EXPLAINER.md).
