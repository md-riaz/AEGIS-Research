# AEGIS: Safety by Design for LLM Analytics

AEGIS is a research prototype demonstrating a "Safety by Design" architecture for Natural Language to SQL (NL2SQL) interfaces. It addresses the reliability and security shortcomings of end-to-end LLM approaches by introducing a deterministic, pipeline-based architecture.

## Overview

Unlike traditional LLM text-to-SQL generation (which is prone to hallucinations and injection attacks), AEGIS uses the LLM *only* for natural language understanding (intent extraction). The LLM maps user queries to a constrained, predefined semantic layer. A deterministic compiler then generates the actual SQL, guaranteeing that every executed query is safe, valid, and aligned with organizational policies.

This repository contains the codebase that accompanies my research manuscript, providing a fully functional implementation of the architecture described in the paper.

## Repository at a Glance

- **`database/`**: Contains the database schema (`schema.sql`) and mock data generation (`mock_data.sql`).
- **`demo/`**: Stores persistent widgets and dashboard configurations (`demo_dashboard.json`, `demo_widgets.json`).
- **`evaluation_dataset/`**: Benchmark dataset (`questions.json`) and evaluation scripts (`evaluate_metrics.py`, `generate_dataset.py`) to reproduce research findings.
- **`assets/`**: Project assets including images and figures.
  - **`assets/images/`**: Architecture diagrams and pattern visualizations (fig_*.png).
- **`docs/`**: Documentation, manuscripts, and analysis.
  - **`docs/AEGIS_Manuscript.md`** & **`docs/AEGIS_Manuscript.tex`**: The primary research paper detailing the architecture.
  - **`docs/aegis_architecture.png`**: System architecture diagram.
  - **`docs/analysis/`**: Detailed analysis documents (e.g., `nopcommerce_db_analysis.md`).
  - **`docs/reviews/`**: Peer review feedback and related documents.
- **`presentation_assets/`**: Technical presentation resources (slides, HTML, scripts).
- **`references/`**: Related literature PDFs, standardized to APA format without numbering.
- **`aegis/`**: Core Python library for the NL2SQL pipeline (`intent_parser.py`, `compiler.py`, etc.).
- **`scripts/`**: Utility and demo scripts.
  - **`scripts/generate_presentation.py`**: Generate HTML/PPTX slides from `presentation_script.txt`.
  - **`scripts/generate_mock.py`**: Generate mock data for testing.
  - **`scripts/fix_sql.py`**: SQL utility scripts.
- **`static/`**: Web assets for the HTML dashboard frontend (uses Tailwind CSS and jQuery).
- **`tests/`**: Unit test suite for verifying query safety and pipeline determinism.
- **`run_benchmark.py`**: Executes the evaluation benchmark.
- **`run_demo_cli.py`** & **`run_demo_server.py`**: Entry points for testing the AEGIS pipeline via CLI or FastAPI Web interface.

## Architectural Pipeline

The system is structured as a 6-stage linear pipeline. Below is a map of the pipeline stages to their concrete implementations in the codebase, directly mirroring the architecture diagram in the manuscript:

1. **Intent Extraction (`aegis/server/intent_parser.py`)**
   - **Responsibility:** Parses natural language into a structured `IntentObject` (JSON).
   - **Key Feature:** Dynamic Vocabulary Injection (`_build_system_prompt()`). The semantic layer's metrics and dimensions are embedded into the prompt, eliminating the need for complex synonym mapping.
   - **Defensive Normalization:** Includes `_fix_common_llm_errors()` to programmatically correct LLM format hallucinations (e.g., stripping markdown, flattening arrays), ensuring the pipeline remains stable even when the LLM deviates from the system prompt.
   - **See also:** `aegis/server/models.py` for the `IntentObject` schema.

2. **Semantic Mapping (`aegis/server/mapper.py`)**
   - **Responsibility:** Maps extracted terms to canonical identifiers and expands abstract business logic.
   - **Key Feature:** The `_apply_business_logic_filters()` method translates high-level terms (e.g., "abandoned") into concrete SQL predicates (`OrderStatusId = 40`).
   - **Coverage Validation:** The `can_resolve()` method serves as an early rejection gate for out-of-vocabulary requests (§8.5).

3. **Permission Rewriting (`aegis/server/permission_rewriter.py`)**
   - **Responsibility:** Enforces Row-Level Security (RLS) at the application layer (§4.3).
   - **Key Feature:** Prepends role-specific `WHERE` predicates to the generated SQL to guarantee data isolation.

4. **SQL Compilation (`aegis/server/compiler.py`)**
   - **Responsibility:** Deterministically generates T-SQL from the validated `AnalysisPlan`.
   - **Key Feature 1 (Parameter Sanitization):** `_sanitize_value()` ensures no malicious payloads can break out of string literals, supporting **Proposition 1** (SQL Safety).
   - **Key Feature 2 (AST Validation):** `_validate_sql_safety()` acts as a defense-in-depth scanner, rejecting any generated SQL that contains forbidden constructs (e.g., `DROP`, `UNION`).

5. **Visualization Selection (`aegis/server/visualization.py`)**
   - **Responsibility:** Chooses the optimal chart type based on data dimensionality and cardinality (§4.8).
   - **Key Feature:** Transparent, rule-based policy tables with automatic cardinality overrides (e.g., switching from a pie chart to a bar chart if categories > 8).

6. **Widget Persistence (`aegis/server/widget_engine.py`)**
   - **Responsibility:** Stores and retrieves widgets to support the finding that 61% of queries are recurrences.
   - **Key Feature:** The `WidgetRegistry.find_similar()` method identifies structurally equivalent queries, caching results for identical metric/dimension pairs.

## System Configuration & Semantic Layer

- **`aegis/server/semantic_layer.py`**: This file acts as the single source of truth ("LEGO blocks"). It defines the closed vocabulary of metrics, dimensions, and join paths that the LLM is allowed to reference.
- **`aegis/server/ai_config.py`**: Manages LLM provider connections (Groq, Ollama) and enforces rate limiting via `ProviderProfile` classes.

## Running the Demo Server

A FastAPI-based demonstration server is provided to interact with the pipeline.

### Using Docker (Recommended for Peer Reviewers)
You can quickly spin up the environment using Docker Compose. Ensure you have a `.env` file with your `GROQ_API_KEY`.

```bash
# Build and start the container
docker-compose up --build

# The UI will be available at http://localhost:8765
```

### Local Setup
If running locally without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server (runs on http://127.0.0.1:8765)
python run_demo_server.py
```

## Running Tests

To verify the core safety guarantees (parameter sanitization, AST validation, structural similarity), run the test suite:

```bash
python -m unittest discover -s tests
```

## Evaluation and Dataset (Proof of Claims)

To support the findings in the manuscript (100% Execution Validity, 100% Safety Rate), I have provided the full benchmark dataset, schema, and evaluation results. Reviewers do not need to set up a live database to verify these claims.

1. **Database Schema:** The semantic layer maps to an E-commerce structure based on the open-source **nopCommerce** schema. The DDL is available in `database/schema.sql`.
2. **Mock Data Generation:** You can generate realistic synthetic data to test queries using the included script: `python database/generate_data.py`. This generates a `.sql` file with `INSERT` statements to verify the relationships hold.
3. **Execution Validity Proof:** The outputs of the AEGIS pipeline and the Direct LLM Baseline are documented in `evaluation_dataset/benchmark_results.json`. This log shows that AEGIS produced 100% syntactically valid and safe T-SQL without hallucinations.

- **`evaluation_dataset/questions.json`**: The 100-query benchmark dataset containing business reporting requests.
- **`evaluation_dataset/README.md`**: Detailed statistics and reproduction instructions.

You can reproduce the evaluations at any time by running `python run_benchmark.py`.

## Research Context

This prototype was developed to substantiate the claims made in the AEGIS manuscript. All components are implemented to demonstrate the "Safety by Design" architecture. Reviewers are encouraged to examine `compiler.py`, `mapper.py`, and the `evaluation_dataset/` directory to verify the security and determinism claims discussed in the paper.
