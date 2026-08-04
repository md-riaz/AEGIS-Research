# -*- coding: utf-8 -*-
"""Chapter 4: Experimental Work."""
from build_thesis import (add_para, add_mixed_para, add_chapter_heading, add_section_heading,
                           add_bullet, add_table_with_caption, page_break)


def chapter4(doc):
    add_chapter_heading(doc, 4, "Experimental Work")

    # ---------------------------------------------------------------- 4.1
    add_section_heading(doc, "4.1", "Implementation")
    add_para(doc,
              "AEGIS is implemented as a web application with a vanilla HTML and JavaScript frontend "
              "(jQuery, Chart.js) and a Python FastAPI backend, targeting a production nopCommerce 4.70 "
              "schema (126 tables, 107 foreign key constraints). The implementation follows directly "
              "from the AEGIS architecture:", space_after=10)
    add_bullet(doc, "Llama 3.1 8B Instant via the Groq API, with structured JSON output enforcement. "
               "The system prompt is constructed dynamically by injecting the approved metric and "
               "dimension identifiers at startup.", bold_lead="LLM integration: ")
    add_bullet(doc, "A provider-agnostic configuration module with a sliding-window rate limiter and "
               "a concurrency-safe asyncio.Lock, so the architecture is not tied to a specific LLM "
               "vendor's throughput characteristics.", bold_lead="Rate limiting: ")
    add_bullet(doc, "Python configuration modules containing 15 metrics, 34 dimensions, zero synonym "
               "entries, and 11 join paths across the 12 analytics-relevant tables represented in "
               "the semantic layer.", bold_lead="Semantic layer: ")
    add_bullet(doc, "Parameterized MySQL templates, with breadth-first search join-path resolution "
               "over the 12-table join graph. A post-compilation _validate_sql_safety() routine "
               "checks 16 forbidden patterns before a query is allowed to execute.",
               bold_lead="SQL compiler: ")
    add_bullet(doc, "Rule-based Python dictionaries implementing the "
               "visualization mapping, with the two post-hoc cardinality rules applied after the result set is "
               "known.", bold_lead="Visualization selector: ")
    add_bullet(doc, "SHA-256 plan-hash deduplication, with JSON file storage in the prototype, "
               "designed to be swapped for a relational store in a production deployment.",
               bold_lead="Widget engine: ")
    add_bullet(doc, "A pre-compilation gate that rejects unknown metric or dimension terms with "
               "structured guidance listing the available identifiers.", bold_lead="Coverage validator: ")
    add_bullet(doc, "A Permission Rewriter that appends role-based WHERE predicates for five roles: "
               "public, store_manager, regional_manager, read_only, and analyst.",
               bold_lead="Permission enforcement: ")

    # ---------------------------------------------------------------- 4.2
    add_section_heading(doc, "4.2", "Experimental Environment")
    add_para(doc,
              "The experimental setup used a containerized relational database and a seeded "
              "e-commerce dataset, summarized in Table 4.1.", space_after=8)
    add_table_with_caption(
        doc, "Table 4.1: Experimental setup.",
        ["Setup item", "Configuration"],
        [
            ["Database engine", "MySQL 8.0"],
            ["Execution mode", "Docker container"],
            ["Schema", "AEGIS Truth Schema based on nopCommerce 4.70"],
            ["Schema size", "126 tables and 107 foreign keys"],
            ["Dataset scale", "1,200 customers, 2,500 orders, 6,298 order items, 1,000 products, and 50 categories"],
            ["Data period", "Orders spanning 2024 to 2026"],
            ["Evaluation scope", "Mid-sized e-commerce analytics workload"],
        ],
        col_widths=[1.65, 4.25],
        font_size=9.4,
        keep_together=True)

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
              "A methodological caveat applies to every quantitative result reported in the "
              "experimental work and results discussion. All benchmark construction, execution, and measurement were carried "
              "out by the author as part of this thesis, using a self-built dataset and evaluation "
              "harness; none of it has been independently replicated by a third party, externally "
              "audited, or peer-reviewed. Therefore, the reported figures should be read as prototype "
              "evaluation results produced within this research, not as independently audited benchmark "
              "results. Where an annotation or classification step is discussed, it refers to the "
              "author's own research process rather than a third-party validation study.",
              space_after=10)
    add_para(doc,
              "A domain-specific benchmark of 107 natural-language reporting requests was built over "
              "the same production nopCommerce schema. The full question set and "
              "recorded pipeline outputs were used to check every reported metric. The benchmark mixes "
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
    add_bullet(doc, "Llama 3.1 8B is prompted with the full database schema, without semantic-layer or "
               "template constraints.", bold_lead="B1 - Direct LLM-to-SQL: ")
    add_bullet(doc, "A chain-of-thought strategy first extracts entities and then generates SQL. This "
               "baseline is prepared but not included in the completed results.", bold_lead="B2 - Decomposed LLM: ")
    add_bullet(doc, "Keyword matching selects templates without LLM-based intent extraction. This "
               "baseline has been executed for true database execution validity.", bold_lead="B3 - Template-only: ")
    add_bullet(doc, "The full AEGIS pipeline runs with the semantic mapper bypassed. This remains "
               "future evaluation work.", bold_lead="B4 - No semantic layer: ")

    # ---------------------------------------------------------------- 4.5
    add_section_heading(doc, "4.5", "Evaluation Procedure")
    add_para(doc, "The current evaluation focuses on measurements that can be reproduced from the "
              "recorded benchmark data and verified through true database execution:", space_after=8)
    add_bullet(doc, "How accurately does the LLM intent parser extract typed reporting plans? This "
               "remains a semantic-correctness task requiring annotated expected labels.",
               bold_lead="RQ1: ")
    add_bullet(doc, "Does AEGIS reduce unsafe SQL compared to direct LLM-to-SQL? Measured as genuine "
               "unsafe SQL statements across the 107-query benchmark.", bold_lead="RQ2: ")
    add_bullet(doc, "Does AEGIS generate SQL that actually runs? Measured through true database "
               "execution against the seeded MySQL database, not merely by checking whether Python "
               "compilation succeeded.", bold_lead="RQ3: ")
    add_bullet(doc, "How does the deterministic downstream compiler behave when intent selection is "
               "rule-based rather than LLM-based? Measured through the B3 template-only baseline.",
               bold_lead="RQ4: ")
    page_break(doc)

