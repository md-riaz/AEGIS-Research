# -*- coding: utf-8 -*-
"""Abstract + Chapter 1: Introduction."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from build_thesis import (add_para, add_mixed_para, add_chapter_heading, add_section_heading,
                           add_bullet, add_numbered, add_manual_numbered, page_break)
from refs import cite


def abstract(doc):
    add_para(doc, "ABSTRACT", size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)
    add_para(doc,
             "Relational databases hold data organizations need for decisions, but non-technical users "
             "often depend on developers to translate business questions into SQL. Natural-language "
             "interfaces try to close this gap, but many current systems still allow a language model "
             "to author executable SQL directly, making safety dependent on model behavior rather than "
             "system structure. This thesis presents AEGIS (Analytics Engine with Guaranteed Injection "
             "Safety), an architecture that restricts the model to intent extraction while deterministic "
             "software handles semantic mapping, permission enforcement, SQL compilation, validation, "
             "visualization selection, and widget persistence. AEGIS uses a closed semantic layer of "
             "approved metrics, dimensions, analytical patterns, and join paths, so the model never "
             "outputs SQL text. Instead, it produces a typed intent object that can be checked before any "
             "query is compiled. The final evaluation uses two static nopCommerce corpora: a "
             "500-question natural-language benchmark, and nopCommerce's own twenty standard admin "
             "reports checked against the platform's own report implementations. On the 500-question "
             "live benchmark, AEGIS parsed 499 of 500 prompts, answered 423 and executed 422 of 425 "
             "supported requests, and rejected or clarified 72 of 75 realistic boundary requests. "
             "Against the twenty admin reports, every request compiled to SQL and fifteen reproduced "
             "the platform's own result set exactly, the remaining five agreeing on every value and "
             "differing only in row count and label column. The same model without the semantic layer, "
             "writing SQL directly, executed 365 of 425 supported questions but also answered 25 of the "
             "75 questions it should have declined. Per-stage timing shows that substantially all "
             "latency is the model reading the question, while every deterministic stage after it "
             "completes in a few milliseconds. These results support the thesis's central claim that "
             "AEGIS is a bounded architecture for safe natural-language analytics over an approved "
             "semantic layer, not an unlimited text-to-SQL engine.",
             space_after=0)
    page_break(doc)


def chapter1(doc):
    add_chapter_heading(doc, 1, "Introduction")

    add_section_heading(doc, "1.1", "Background")
    add_para(doc,
             "Relational databases store critical institutional data in organizations: financial "
             "records, customer accounts, sales transactions, and more. But accessing this data is "
             "uneven. Technical staff can write SQL queries to get any answer they need, while "
             "non-technical users have to wait for someone else to build them a report. This waiting is "
             "expensive. Analysis of enterprise reporting workflows shows that business users frequently "
             "wait days for new reports, and a recurring theme in institutional reporting is that many "
             "questions are variations of things already asked before: the same report with a different "
             "date range, or the same chart for a different department. These are not one-off questions; "
             "they are recurring reporting needs that should be served by saved, refreshable widgets "
             "rather than regenerated from scratch every time.", space_after=12)
    add_para(doc,
             "This thesis presents AEGIS (Analytics Engine with Guaranteed Injection Safety). The "
             "system lets users describe reporting needs in plain English and produces dashboard "
             "widgets that can be saved, refreshed, and reused in daily work, without anyone writing "
             "SQL.", space_after=12)
    add_para(doc,
             "Natural language interfaces to databases (NLIDBs) try to solve this problem. A user "
             "should be able to ask \"which categories have the highest refund rates this month?\" "
             "and get a correct, visual answer without writing SQL. Benchmarks such as Spider "
             f"{cite('yu_spider18')} and BIRD {cite('li_bird23')} show clear progress. But there is "
             "still a gap between benchmark SQL generation and production-ready reporting, where "
             "answers must respect business definitions, permissions, safety rules, and reusable "
             "dashboard presentation.",
             space_after=0)

    add_section_heading(doc, "1.2", "Problem Statement")
    add_para(doc,
             "Three problems make up the gap between benchmark text-to-SQL accuracy and safe, "
             "production-ready natural-language reporting.", space_after=10)
    add_bullet(doc,
               "Models may generate SQL directly, which can expose private data or create wrong joins.",
               bold_lead="Safety: ")
    add_bullet(doc,
               "Users ask with business terms such as \"refund rate\", while systems often expect column names.",
               bold_lead="Vocabulary mismatch: ")
    add_bullet(doc,
               "Most systems answer once and discard the result instead of saving refreshable dashboard widgets.",
               bold_lead="No reusable widgets: ")
    add_para(doc,
             "These problems are not mainly about building a smarter model. They are about designing "
             "the system around the model. AEGIS splits the work into stages. The LLM understands "
             "the request and returns a structured description. Fixed rules and pre-approved templates "
             "then match business terms, build SQL, select the chart, and save the widget.", space_after=0)

    add_section_heading(doc, "1.3", "Research Novelty and Motivation")
    add_para(doc,
             "Existing text-to-SQL research asks how accurately a model can generate SQL from natural "
             "language. This thesis asks how a large language model can understand language while the "
             "system prevents it from generating executable SQL. The two pipelines differ structurally.", space_after=10)
    add_para(doc, "Classical NL-to-SQL: natural-language request, then model-authored SQL, then query result.",
             italic=True, space_after=6)
    add_para(doc, "AEGIS: natural-language request, then intent extraction, semantic constraint, "
             "deterministic compilation, and a safe analytical artifact.", italic=True, space_after=12)
    add_para(doc,
             "The contribution of this thesis is not better SQL generation. It is constrained analytical "
             "artifact generation. The design removes SQL generation from the LLM's role and gives the "
             "system safety and semantic-fidelity properties that prompt-only systems cannot guarantee.", space_after=12)
    add_para(doc,
             "AEGIS does not propose a new LLM. The model is interchangeable across APIs that expose "
             "an OpenAI-compatible /v1/chat/completions interface. Because the LLM's only contract "
             "with the rest of the system is to produce a typed JSON intent object, model upgrades "
             "can improve language understanding without changing the compiler or safety "
             "infrastructure. This model independence is part of the architecture. "
             "The evaluation in Chapter 5 used an LLM API exposed through an OpenAI-compatible "
             "interface; the SQL compiler and safety layer did not depend on that provider.",
             space_after=0)

    add_section_heading(doc, "1.4", "Objectives and Contributions")
    add_para(doc,
             "The objective of this thesis is to design and evaluate AEGIS, a constraint-based "
             "architecture that lets an LLM understand reporting requests without allowing it to "
             "generate executable SQL. Query construction, validation, visualization, and widget "
             "persistence are handled by deterministic system components.", space_after=8)
    add_para(doc, "The specific objectives and contributions are:", space_after=6)
    add_numbered(doc, "A natural-language analytics architecture where the LLM is structurally "
                 "prevented from writing executable SQL.")
    add_numbered(doc, "A closed semantic layer that maps business questions to approved metrics, "
                 "dimensions, filters, analytical patterns, and join paths.")
    add_numbered(doc, "A deterministic query compiler that builds SQL from approved templates "
                 "instead of model-written SQL.")
    add_numbered(doc, "A two-layer SQL safety mechanism combining structural prevention with "
                 "post-compilation validation.")
    add_numbered(doc, "A widget-oriented workflow that turns natural-language answers into reusable "
                 "dashboard artifacts.")
    add_numbered(doc, "A static nopCommerce evaluation corpus consisting of a 500-question "
                 "natural-language benchmark and nopCommerce's own twenty standard admin reports, "
                 "checked against the platform's own report implementations rather than against an "
                 "expected-answer set written by the authors of the system under test.")
    add_numbered(doc, "An empirical evaluation showing broad supported-request coverage, strong "
                 "boundary rejection, a measured direct LLM-to-SQL baseline under identical "
                 "conditions, per-stage latency, and a visible remaining Admin fidelity gap rather "
                 "than a suspicious claim of perfect performance.")

    page_break(doc)
