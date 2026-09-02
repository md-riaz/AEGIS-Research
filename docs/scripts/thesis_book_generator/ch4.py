# -*- coding: utf-8 -*-
"""Chapter 4: Experimental Work."""
from build_thesis import (
    add_para,
    add_chapter_heading,
    add_section_heading,
    add_bullet,
    add_table_with_caption,
    page_break,
)


def chapter4(doc):
    add_chapter_heading(doc, 4, "Experimental Work")

    add_section_heading(doc, "4.1", "Implementation")
    add_para(
        doc,
        "AEGIS is implemented as a web application with a vanilla HTML and JavaScript "
        "frontend and a Python FastAPI backend, targeting a nopCommerce-derived MySQL "
        "schema of 126 tables and 107 foreign-key constraints. The oracle queries are "
        "read from nopCommerce source at commit 64bdf2ff (version 5.00.0), and all "
        "twenty executed against this schema without a missing table or column, which "
        "is the evidence that the schema and the report logic agree on the entities "
        "those reports touch. The prototype follows the architecture from Chapter 3: "
        "the model extracts intent, the semantic layer supplies approved business "
        "definitions, and deterministic compiler templates produce SQL.",
        space_after=10,
    )
    add_bullet(
        doc,
        "An LLM API exposed through an OpenAI-compatible /v1/chat/completions interface "
        "with structured JSON output enforcement. The prompt injects approved metric "
        "and dimension identifiers at request time. The compiler and safety layer are "
        "provider-independent because they consume only the typed intent object, not "
        "model-written SQL.",
        bold_lead="LLM integration: ",
    )
    add_bullet(doc, "Python configuration modules define approved metrics, dimensions, predicates, "
               "time anchors, join paths, grain rules, and mandatory platform filters.",
               bold_lead="Semantic layer: ")
    add_bullet(doc, "Parameterized MySQL templates build read-only SQL from approved analytical "
               "patterns. The compiler logs the selected pattern, resolved tables, join path, metric "
               "expression, dimension expression, and safety result.",
               bold_lead="SQL compiler: ")
    add_bullet(
        doc,
        "Rule-based chart selection maps analytical patterns and result shapes to "
        "dashboard widgets.",
        bold_lead="Visualization selector: ",
    )
    add_bullet(
        doc,
        "The prototype stores widget metadata locally with plan-hash deduplication. "
        "The interface is designed so production storage can be moved to a database.",
        bold_lead="Widget engine: ",
    )
    add_bullet(
        doc,
        "Structured intent validation checks the LLM's normalized intent against the "
        "semantic layer, while the original question is used only for narrow safety and "
        "scope cues such as writes, direct secrets, and explicit non-SQL analysis modes.",
        bold_lead="Intent validator: ",
    )
    add_table_with_caption(
        doc,
        "Table 4.1: Prototype module-to-architecture mapping.",
        ["Architecture stage", "Implementation module", "Main technical responsibility"],
        [
            ["Intent extraction", "intent_parser.py, models.py", "OpenAI-compatible structured JSON output into IntentObject"],
            ["Grounding", "grounding.py, mapper.py", "Ranked semantic-layer binding with resolved, ambiguous, unsupported, or absent outcomes"],
            ["Intent validation", "coverage.py, mapper.py", "Structured binding checks plus narrow raw-text safety/scope cues"],
            ["Semantic layer", "semantic_layer.py", "Metrics, dimensions, predicates, time anchors, join graph, and mandatory filters"],
            ["Compilation", "compiler.py", "Pattern templates, BFS join-path resolution, parameter binding, and SQL safety scan"],
            ["Visualization", "visualization.py", "Rule-based chart selection from pattern and result shape"],
            ["Persistence", "widget_engine.py", "Plan hashing, widget storage, refresh metadata, and reuse"],
        ],
        col_widths=[1.45, 1.65, 3.1],
        font_size=8.4,
    )
    add_para(
        doc,
        "This module map makes the prototype auditable. The thesis architecture is more than "
        "a conceptual pipeline. Each stage has a corresponding implementation boundary.",
        space_after=0,
    )

    add_section_heading(doc, "4.2", "Experimental Environment")
    add_table_with_caption(
        doc,
        "Table 4.2: Experimental setup.",
        ["Setup item", "Configuration"],
        [
            ["Database engine", "MySQL 8.0"],
            ["Execution mode", "Local/Laragon or Docker-compatible MySQL evaluation database"],
            ["Application schema", "nopCommerce-derived MySQL schema, 126 tables, 107 foreign keys"],
            ["Report oracle source", "nopCommerce source at commit 64bdf2ff (version 5.00.0)"],
            ["Dataset scope", "Orders, customers, products, categories, manufacturers, payments, shipping, refunds, stores, countries, and search terms"],
            ["LLM interface", "OpenAI-compatible /v1/chat/completions API"],
            ["Evaluation scope", "Single-domain prototype evaluation over nopCommerce analytics"],
        ],
        col_widths=[1.65, 4.25],
        font_size=9.3,
        keep_together=True,
    )

    add_section_heading(doc, "4.3", "Benchmark Dataset Construction")
    add_para(
        doc,
        "This evaluation is a prototype evaluation, not a large-scale independent "
        "leaderboard study. Its goal is to test whether the AEGIS architecture provides "
        "safe, Approved natural-language analytics for a realistic e-commerce schema. "
        "General text-to-SQL benchmarks such as Spider and BIRD are valuable for SQL "
        "generation research, but they do not measure reusable dashboard widgets, semantic "
        "layer control, or refusal of unsupported business questions.",
        space_after=10,
    )
    add_table_with_caption(
        doc,
        "Table 4.3: Static evaluation datasets.",
        ["Dataset", "Size", "Purpose"],
        [
            ["Natural-language benchmark", "500 questions", "Breadth: 425 answerable questions and 75 realistic e-commerce boundary questions that should be declined."],
            ["nopCommerce standard admin reports", "20 reports", "Fidelity: the platform's own admin report list, with the platform's own report implementations as the oracle."],
        ],
        font_size=8.9,
        col_widths=[1.65, 1.1, 3.45],
    )
    add_para(
        doc,
        "The two corpora differ in who chose them, and that difference is deliberate. The 500 "
        "questions were written for this study, so they measure how the architecture behaves "
        "across the range of language a store owner uses. The twenty reports were not: the list "
        "is nopCommerce's own admin menu and the comparison target is nopCommerce's own "
        "service-layer code, read from source. Comparing against a platform's shipped "
        "implementation is stronger evidence than comparing against an expected-answer set "
        "written by the same authors as the system under test, because the latter tends to "
        "agree with the implementation wherever both authors reasoned the same way.",
        space_after=10,
    )
    add_para(
        doc,
        "All benchmark datasets are static repository artifacts. They are not regenerated "
        "during evaluation, because a thesis dataset must be inspectable and stable. The "
        "reported result files are also stored with the repository so a reader can compare "
        "the manuscript tables with the underlying evidence.",
        space_after=0,
    )

    add_section_heading(doc, "4.4", "Baseline and Oracle Comparisons")
    add_para(
        doc,
        "The evaluation uses two kinds of comparison, and both are measured rather than "
        "argued. The first is a direct LLM-to-SQL baseline run under identical conditions. "
        "The second compares AEGIS output against nopCommerce's own admin report "
        "implementations. The second is the stronger evidence for result accuracy, because it "
        "checks returned business values rather than only whether SQL text was emitted.",
        space_after=10,
    )
    add_bullet(
        doc,
        "The same model, through the same gateway, is asked to write MySQL directly for the "
        "same 500 questions against the same database, with no semantic layer in between. The "
        "arms therefore differ only in whether the model authors the query, which isolates the "
        "architectural variable rather than confounding it with model or data differences. "
        "Both arms are scanned for forbidden constructs with the same pattern set, imported "
        "from the compiler rather than restated, so neither arm is judged by a more lenient rule.",
        bold_lead="Direct LLM-to-SQL baseline: ",
    )
    add_bullet(
        doc,
        "Each of nopCommerce's twenty standard admin reports is requested in ordinary business "
        "phrasing. Two checks are applied: whether the request reaches an answer and compiles "
        "to SQL, and whether executing that SQL against the seeded database returns the same "
        "rows as the platform's own query. Only the second tests the claim; the first is "
        "satisfied by any query that compiles, including ones that are silently wrong.",
        bold_lead="Admin report differential: ",
    )
    add_bullet(
        doc,
        "Every stage of the live benchmark is timed separately, so that the cost of intent "
        "extraction can be separated from the cost of resolution, compilation, and execution. "
        "A single end-to-end figure would conflate a property of the model provider with a "
        "property of the architecture.",
        bold_lead="Per-stage latency: ",
    )

    page_break(doc)
    add_section_heading(doc, "4.5", "Evaluation Procedure")
    add_para(
        doc,
        "The current evaluation focuses on measurements that can be reproduced from static "
        "benchmark data, verifier scripts, and recorded result artifacts:",
        space_after=8,
    )
    add_bullet(
        doc,
        "How reliably does the LLM parser produce typed reporting intents on the 500-question "
        "natural-language dataset?",
        bold_lead="RQ1: ",
    )
    add_bullet(
        doc,
        "Does AEGIS answer supported semantic-layer questions while rejecting or clarifying "
        "realistic unsupported e-commerce questions?",
        bold_lead="RQ2: ",
    )
    add_bullet(
        doc,
        "Does the compiled SQL execute successfully against the evaluation database?",
        bold_lead="RQ3: ",
    )
    add_bullet(
        doc,
        "Do AEGIS results match the rows returned by nopCommerce's own report implementations "
        "on the same database?",
        bold_lead="RQ4: ",
    )
    add_bullet(
        doc,
        "How does the same model behave on the same questions when the semantic layer is "
        "removed and it writes SQL directly?",
        bold_lead="RQ5: ",
    )
    add_bullet(
        doc,
        "Where does the response time go, and how much of it does the architecture control?",
        bold_lead="RQ6: ",
    )
    add_bullet(
        doc,
        "What implementation gaps remain after the current semantic-layer and compiler updates?",
        bold_lead="RQ7: ",
    )
    page_break(doc)
