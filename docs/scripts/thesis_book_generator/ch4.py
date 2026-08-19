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
        "frontend and a Python FastAPI backend, targeting a nopCommerce 4.70-style "
        "e-commerce schema. The prototype follows the architecture from Chapter 3: "
        "the model extracts intent, the semantic layer supplies Approved business "
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
    add_bullet(doc, "Python configuration modules define Approved metrics, dimensions, predicates, "
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
        "This module map is included to make the prototype auditable: the thesis architecture is "
        "not only a conceptual pipeline, and each stage has a corresponding implementation boundary.",
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
            ["Application schema", "nopCommerce 4.70-style e-commerce schema"],
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
            ["Natural-language benchmark", "500 questions", "Tests broad nopCommerce semantic-layer coverage and realistic boundary refusal."],
            ["Admin analytics oracles", "16 tasks", "Checks fidelity against source-derived nopCommerce Admin reporting logic."],
            ["Admin-fidelity phrasings", "80 prompts", "Tests five natural phrasings for each Admin oracle task."],
            ["Semantic coverage suite", "25 checks", "Tests representative supported combinations and focused boundary cases."],
        ],
        font_size=8.9,
        col_widths=[1.65, 1.1, 3.45],
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
        "The evaluation uses two kinds of comparison. First, the thesis discusses the "
        "structural contrast between AEGIS and direct LLM-to-SQL systems, where the model "
        "is allowed to generate SQL text. Second, the Admin fidelity benchmark compares "
        "AEGIS output with source-derived nopCommerce Admin analytics oracles. The second "
        "comparison is the stronger evidence for result accuracy because it checks returned "
        "business values rather than only whether SQL text was emitted.",
        space_after=10,
    )
    add_bullet(
        doc,
        "The model is prompted to generate SQL directly from a database schema. This baseline "
        "has broad expressive freedom but weak control because joins, filters, and business "
        "definitions are inferred per request.",
        bold_lead="Direct LLM-to-SQL: ",
    )
    add_bullet(
        doc,
        "Expected outputs are extracted from nopCommerce Admin analytics logic. AEGIS can use "
        "different SQL text, but the returned result shape and values must match the oracle.",
        bold_lead="Admin oracle comparison: ",
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
        "Do AEGIS outputs match the shape and values of source-derived nopCommerce Admin "
        "analytics oracles?",
        bold_lead="RQ4: ",
    )
    add_bullet(
        doc,
        "What implementation gaps remain after the current semantic-layer and compiler updates?",
        bold_lead="RQ5: ",
    )
    page_break(doc)
