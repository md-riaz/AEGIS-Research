# SafeDash: Safety by Design for LLM Analytics

SafeDash is a research prototype demonstrating a "Safety by Design" architecture for Natural Language to SQL (NL2SQL) interfaces. It addresses the reliability and security shortcomings of end-to-end LLM approaches by introducing a deterministic, pipeline-based architecture.

## Overview

Unlike traditional LLM text-to-SQL generation (which is prone to hallucinations and injection attacks), SafeDash uses the LLM *only* for natural language understanding (intent extraction). The LLM maps user queries to a constrained, predefined semantic layer. A deterministic compiler then generates the actual SQL, guaranteeing that every executed query is safe, valid, and aligned with organizational policies.

This repository contains the codebase that accompanies our academic manuscript, providing a fully functional implementation of the architecture described in the paper.

## Architectural Pipeline

The system is structured as a 6-stage linear pipeline. Below is a map of the pipeline stages to their concrete implementations in the codebase, directly mirroring the architecture diagram in the manuscript:

1. **Intent Extraction (`safedash/server/intent_parser.py`)**
   - **Responsibility:** Parses natural language into a structured `IntentObject` (JSON).
   - **Key Feature:** Dynamic Vocabulary Injection (`_build_system_prompt()`). The semantic layer's metrics and dimensions are embedded into the prompt, eliminating the need for complex synonym mapping.
   - **See also:** `safedash/server/models.py` for the `IntentObject` schema.

2. **Semantic Mapping (`safedash/server/mapper.py`)**
   - **Responsibility:** Maps extracted terms to canonical identifiers and expands abstract business logic.
   - **Key Feature:** The `_apply_business_logic_filters()` method translates high-level terms (e.g., "abandoned") into concrete SQL predicates (`OrderStatusId = 40`).
   - **Coverage Validation:** The `can_resolve()` method serves as an early rejection gate for out-of-vocabulary requests (§8.5).

3. **Permission Rewriting (`safedash/server/permission_rewriter.py`)**
   - **Responsibility:** Enforces Row-Level Security (RLS) at the application layer (§4.3).
   - **Key Feature:** Prepends role-specific `WHERE` predicates to the generated SQL to guarantee data isolation.

4. **SQL Compilation (`safedash/server/compiler.py`)**
   - **Responsibility:** Deterministically generates T-SQL from the validated `AnalysisPlan`.
   - **Key Feature 1 (Parameter Sanitization):** `_sanitize_value()` ensures no malicious payloads can break out of string literals, supporting **Proposition 1** (SQL Safety).
   - **Key Feature 2 (AST Validation):** `_validate_sql_safety()` acts as a defense-in-depth scanner, rejecting any generated SQL that contains forbidden constructs (e.g., `DROP`, `UNION`).

5. **Visualization Selection (`safedash/server/visualization.py`)**
   - **Responsibility:** Chooses the optimal chart type based on data dimensionality and cardinality (§4.8).
   - **Key Feature:** Transparent, rule-based policy tables with automatic cardinality overrides (e.g., switching from a pie chart to a bar chart if categories > 8).

6. **Widget Persistence (`safedash/server/widget_engine.py`)**
   - **Responsibility:** Stores and retrieves widgets to support the finding that 61% of queries are recurrences.
   - **Key Feature:** The `WidgetRegistry.find_similar()` method identifies structurally equivalent queries, caching results for identical metric/dimension pairs.

## System Configuration & Semantic Layer

- **`safedash/server/semantic_layer.py`**: This file acts as the single source of truth ("LEGO blocks"). It defines the closed vocabulary of metrics, dimensions, and join paths that the LLM is allowed to reference.
- **`safedash/server/ai_config.py`**: Manages LLM provider connections (Groq, Ollama) and enforces rate limiting via `ProviderProfile` classes.

## Running the Demo Server

A FastAPI-based demonstration server is provided to interact with the pipeline.

```bash
# Start the server (runs on http://127.0.0.1:8765)
python demo_server.py
```

## Running Tests

To verify the core safety guarantees (parameter sanitization, AST validation, structural similarity), run the test suite:

```bash
python -m unittest discover -s tests
```

## Academic Context

This prototype was developed to substantiate the claims made in the SafeDash manuscript. All components have been implemented to ensure that the code explicitly demonstrates the "Safety by Design" philosophy. Reviewers are encouraged to examine `compiler.py` and `mapper.py` to see the exact implementation of the security and determinism claims discussed in Sections 4 and 5 of the paper.
