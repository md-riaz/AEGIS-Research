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
              "from the AEGIS architecture:", space_after=10)
    add_bullet(doc, "LLM integration: Llama 3.1 8B Instant via the Groq API, with structured JSON "
               "output enforcement. The system prompt is constructed dynamically by injecting the "
               "approved metric and dimension identifiers at startup.")
    add_bullet(doc, "Rate limiting: a provider-agnostic configuration module with a sliding-window "
               "rate limiter and a concurrency-safe asyncio.Lock, so the architecture is not tied to "
               "a specific LLM vendor's throughput characteristics.")
    add_bullet(doc, "Semantic layer: Python configuration modules containing 15 metrics, 34 "
               "dimensions, zero synonym entries, and 11 join paths across the 12 analytics-relevant "
               "tables represented in the semantic layer.")
    add_bullet(doc, "SQL compiler: parameterized MySQL templates, with breadth-first search join-path "
               "resolution over the 12-table join graph. A post-compilation _validate_sql_safety() "
               "routine checks 16 forbidden patterns before a query is allowed to execute.")
    add_bullet(doc, "Visualization selector: rule-based Python dictionaries implementing the "
               "visualization mapping, with the two post-hoc cardinality rules applied after the result set is "
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
              "Spider and BIRD do not evaluate adversarial safety or adherence to business "
              "vocabulary, which is why a domain-specific benchmark was necessary for this thesis.",
              space_after=10)
    add_para(doc,
              "A methodological caveat applies to every quantitative result reported in this chapter "
              "and in the results discussion. All benchmark construction, execution, and measurement were carried "
              "out by the author as part of this thesis, using a self-built dataset and evaluation "
              "harness; none of it has been independently replicated by a third party, externally "
              "audited, or peer-reviewed. This is distinct from reproducibility: the underlying "
              "artifacts (evaluation_dataset/questions.json, benchmark_results.json, "
              "pattern_classification.json, and the scripts that compute statistics from them) are "
              "published alongside this thesis specifically so that any reader can independently "
              "re-run the computation and check the reported figures against the raw data, even though "
              "no one outside this research has done so yet. Where a figure states that an annotation "
              "or classification step was performed by a named number of people (for example, two "
              "database engineers verifying gold-standard SQL), that step was part of the author's own "
              "research process rather than an independent, third-party audit. These results should "
              "therefore be read as internal evidence produced during this research and reproducible "
              "from the published artifacts, but not yet independently verified by anyone outside it.",
              space_after=10)
    add_para(doc,
              "A domain-specific benchmark of 107 natural-language reporting requests was built over "
              "the production nopCommerce schema described above. The full question set and "
              "recorded pipeline outputs are available in the evaluation_dataset/ directory of the "
              "project repository, enabling verification of every reported metric. The benchmark mixes "
              "ordinary analytical requests with harder boundary cases in the same run; this thesis does "
              "not report those harder cases as a separate benchmark. Because the benchmark was constructed for "
              "the nopCommerce domain, accuracy and validity reported figures should be interpreted "
              "within that scope. The current artifact verifies SQL safety and true execution validity; "
              "semantic correctness still requires an annotated expected-answer benchmark in future "
              "work.", space_after=0)

    # ---------------------------------------------------------------- 4.4
    add_section_heading(doc, "4.4", "Baseline Systems")
    add_para(doc, "The evaluation plan defines four baselines, but not all are complete in the current prototype:",
              space_after=8)
    add_mixed_para(doc, [("B1 - Direct LLM-to-SQL. ", True, False),
                          ("Llama 3.1 8B prompted with the full database schema, with no semantic "
                           "layer and no template constraints; the model is free to generate any SQL "
                           "text it produces.", False, False)])
    add_mixed_para(doc, [("B2 - Decomposed LLM. ", True, False),
                          ("A chain-of-thought strategy that first extracts entities, then generates "
                           "SQL from the extracted entities. This baseline is prepared for evaluation "
                           "but is not included in the verified results.", False, False)])
    add_mixed_para(doc, [("B3 - Template-only (no LLM). ", True, False),
                          ("Keyword matching directly to templates, with no LLM-based intent "
                           "extraction. This baseline has been executed for true database execution "
                           "validity and is discussed as B3 in the results.",
                           False, False)])
    add_mixed_para(doc, [("B4 - AEGIS ablated (no semantic layer). ", True, False),
                          ("The full AEGIS pipeline with the semantic mapper bypassed. This remains "
                           "future evaluation work.", False, False)])

    # ---------------------------------------------------------------- 4.5
    add_section_heading(doc, "4.5", "Evaluation Procedure")
    add_para(doc, "The current evaluation focuses on the measurements that can be verified from "
              "repository artifacts and true database execution:", space_after=8)
    add_bullet(doc, "RQ1: How accurately does the LLM intent parser extract typed reporting plans? "
               "This remains a semantic-correctness task requiring annotated expected labels.")
    add_bullet(doc, "RQ2: Does AEGIS reduce unsafe SQL compared to direct LLM-to-SQL? Measured as "
               "genuine unsafe SQL statements across the 107-query benchmark.")
    add_bullet(doc, "RQ3: Does AEGIS generate SQL that actually runs? Measured through true database "
               "execution against the seeded MySQL database, not merely by checking whether Python "
               "compilation succeeded.")
    add_bullet(doc, "RQ4: How does the deterministic downstream compiler behave when intent selection "
               "is rule-based rather than LLM-based? Measured through the B3 template-only baseline.")
    add_bullet(doc, "RQ5: Which remaining work is required in future work? Semantic correctness, "
               "B2/B4 baseline completion, and latency instrumentation are explicitly listed as "
               "future work rather than reported as completed results.")
    page_break(doc)

