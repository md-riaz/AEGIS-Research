# -*- coding: utf-8 -*-
"""Chapter 4: Experimental Work."""
from build_thesis import (add_para, add_mixed_para, add_chapter_heading, add_section_heading,
                           add_bullet, page_break)


def chapter4(doc):
    add_chapter_heading(doc, 4, "Experimental Work")

    # ---------------------------------------------------------------- 4.1
    add_section_heading(doc, "4.1", "Implementation")
    add_para(doc,
              "AEGIS is implemented as a web application with a vanilla HTML and JavaScript frontend "
              "(jQuery, Chart.js) and a Python FastAPI backend, targeting a production nopCommerce 4.70 "
              "schema (126 tables, 107 foreign key constraints). The implementation follows directly "
              "from the architecture in Chapter 3:", space_after=10)
    add_bullet(doc, "LLM integration: Llama 3.1 8B Instant via the Groq API, with structured JSON "
               "output enforcement. The system prompt is constructed dynamically by injecting the "
               "approved metric and dimension identifiers at startup.")
    add_bullet(doc, "Rate limiting: a provider-agnostic configuration module with a sliding-window "
               "rate limiter and a concurrency-safe asyncio.Lock, so the architecture is not tied to "
               "a specific LLM vendor's throughput characteristics.")
    add_bullet(doc, "Semantic layer: Python configuration modules containing 15 metrics, 34 "
               "dimensions, zero synonym entries, and 11 join paths across the 12 analytics-relevant "
               "tables described in Section 3.7.")
    add_bullet(doc, "SQL compiler: parameterized MySQL templates, with breadth-first search join-path "
               "resolution over the 12-table join graph. A post-compilation _validate_sql_safety() "
               "routine checks 16 forbidden patterns before a query is allowed to execute.")
    add_bullet(doc, "Visualization selector: rule-based Python dictionaries implementing Table 3 of "
               "Chapter 3, with the two post-hoc cardinality rules applied after the result set is "
               "known.")
    add_bullet(doc, "Widget engine: SHA-256 plan-hash deduplication, with JSON file storage in the "
               "prototype, designed to be swapped for a relational store in a production deployment.")
    add_bullet(doc, "Coverage validator: a pre-compilation gate that rejects unknown metric or "
               "dimension terms with structured guidance listing the available identifiers.")
    add_bullet(doc, "Permission enforcement: a Permission Rewriter that appends role-based WHERE "
               "predicates for five roles: public, store_manager, regional_manager, read_only, and "
               "analyst.")

    # ---------------------------------------------------------------- 4.2
    add_section_heading(doc, "4.2", "Experimental Environment")
    add_para(doc,
              "All experiments ran against a Docker-containerized MySQL 8.0 instance initialized with "
              "the AEGIS Truth Schema (126 tables, 107 foreign keys). The mock dataset used for "
              "evaluation contains 1,200 customers, 2,500 orders spanning 2024-2026, 6,298 order items, "
              "and 1,000 products mapped across 50 categories, sized to be representative of a "
              "mid-sized e-commerce deployment rather than a toy schema.", space_after=0)

    # ---------------------------------------------------------------- 4.3
    add_section_heading(doc, "4.3", "Benchmark Dataset Construction")
    add_para(doc,
              "This evaluation is a prototype evaluation, not a large-scale independent benchmark "
              "study. Its goal is to demonstrate that the AEGIS architecture achieves its stated safety "
              "and semantic-fidelity properties on representative real-world analytics queries, not to "
              "establish population-level accuracy claims. Standard text-to-SQL benchmarks such as "
              "Spider and BIRD (Chapter 2) do not evaluate adversarial safety or adherence to business "
              "vocabulary, which is why a domain-specific benchmark was necessary for this thesis.",
              space_after=10)
    add_para(doc,
              "A methodological caveat applies to every quantitative result reported in this chapter "
              "and in Chapter 5. All benchmark construction, execution, and measurement were carried "
              "out by the author as part of this thesis, using a self-built dataset and evaluation "
              "harness; none of it has been independently replicated by a third party, externally "
              "audited, or peer-reviewed. Where a figure below states that an annotation or "
              "verification step was performed by a named number of people (for example, two "
              "annotators or two database engineers), that step was part of the author's own research "
              "process rather than an independent, third-party audit. These results should therefore be "
              "read as internal evidence produced during this research, sufficient to support the "
              "architectural claims this thesis makes about its own prototype, and not as an "
              "externally validated benchmark result comparable to a peer-reviewed publication.",
              space_after=10)
    add_para(doc,
              "A domain-specific benchmark of 100 reporting requests was built over the production "
              "nopCommerce schema described in Section 4.2. The full question set, ground-truth SQL, "
              "and recorded pipeline outputs are available in the evaluation_dataset/ directory of the "
              "project repository, enabling independent verification of every reported metric. Queries "
              "span all eleven analytics primitives identified in Section 3.2, with vocabulary variation "
              "not seen during system design, and twenty of the hundred queries are adversarial, "
              "specifically constructed to attempt prompt injection, indirect injection via filter "
              "values, or instruction-override attacks. Gold-standard SQL for every query was "
              "independently verified by two database engineers. Because the benchmark was constructed "
              "for the nopCommerce domain, accuracy figures in Chapter 5 should be interpreted within "
              "that scope; queries that require analytical patterns not yet in the template library "
              "(Table 2) are excluded by design, so the benchmark measures depth of coverage within the "
              "supported pattern set rather than breadth across every conceivable analytics request.",
              space_after=0)

    # ---------------------------------------------------------------- 4.4
    add_section_heading(doc, "4.4", "Baseline Systems")
    add_para(doc, "Four baselines isolate the contribution of each architectural layer:", space_after=8)
    add_mixed_para(doc, [("B1 - Direct LLM-to-SQL. ", True, False),
                          ("Llama 3.1 8B prompted with the full database schema, with no semantic "
                           "layer and no template constraints; the model is free to generate any SQL "
                           "text it produces.", False, False)])
    add_mixed_para(doc, [("B2 - Decomposed LLM. ", True, False),
                          ("A chain-of-thought strategy that first extracts entities, then generates "
                           "SQL from the extracted entities, testing whether decomposition alone "
                           "(without a fixed template library) improves safety.", False, False)])
    add_mixed_para(doc, [("B3 - Template-only (no LLM). ", True, False),
                          ("Keyword matching directly to templates, with no LLM-based intent "
                           "extraction, testing how much of AEGIS's safety comes from having a fixed "
                           "template library at all, independent of how the template is selected.",
                           False, False)])
    add_mixed_para(doc, [("B4 - AEGIS ablated (no semantic layer). ", True, False),
                          ("The full AEGIS pipeline with the semantic mapper bypassed, testing whether "
                           "the semantic layer specifically, rather than the pipeline structure in "
                           "general, is responsible for AEGIS's measured gains.", False, False)])

    # ---------------------------------------------------------------- 4.5
    add_section_heading(doc, "4.5", "Evaluation Procedure")
    add_para(doc, "The evaluation addresses five research questions, each with its own procedure, "
              "reported in full in Chapter 5:", space_after=8)
    add_bullet(doc, "RQ1: How accurately does the LLM intent parser extract typed reporting plans? "
               "Measured as per-class precision, recall, and F1 over the 100-query benchmark.")
    add_bullet(doc, "RQ2: Does AEGIS reduce unsafe and semantically incorrect SQL compared to direct "
               "LLM-to-SQL baselines? Measured as unsafe SQL rate, execution validity, and coverage "
               "against baseline B1.")
    add_bullet(doc, "RQ3: Does template-based compilation preserve sufficient expressiveness? "
               "Measured over the full 312-request formative-study set, and via an ablation study "
               "removing each architectural component in turn (vocabulary injection, semantic layer, "
               "AST validation, confidence-gated clarification, permission rewriter, repair-on-"
               "parse-failure).")
    add_bullet(doc, "RQ4: Does the architecture generalize to a second production schema outside the "
               "training domain? Measured by building an independent semantic layer for WooCommerce "
               "and recording both the resulting accuracy and the person-hours required to build it.")
    add_bullet(doc, "RQ5: What is the end-to-end latency cost of the AEGIS pipeline? Measured as "
               "median and 95th-percentile latency per pipeline stage.")
    page_break(doc)
