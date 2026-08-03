# -*- coding: utf-8 -*-
"""Abstract + Chapter 1: Introduction."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from build_thesis import (add_para, add_mixed_para, add_chapter_heading, add_section_heading,
                           add_bullet, add_numbered, page_break)
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
             "query is compiled. A prototype evaluation over a 107-query mixed natural-language "
             "benchmark on a seeded nopCommerce-style database shows that AEGIS produced no unsafe SQL "
             "statements and achieved 100 successful true database executions out of 107, while a direct "
             "LLM-to-SQL baseline achieved 27 successful executions out of 107 and produced one genuine "
             "unsafe write statement. These results support the thesis's central claim that SQL safety "
             "can be made a structural property of the architecture. The evaluation also shows a "
             "remaining limitation: safe and executable SQL is not always semantically correct, so "
             "correctness and scope-handling require a separate annotated benchmark in future work.",
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
             "This thesis presents AEGIS (Analytics Engine with Guaranteed Injection Safety), a system "
             "that lets users describe their reporting needs in plain English and produces dynamic "
             "dashboard widgets that can be saved, refreshed, and reused as part of their daily workflow, "
             "without anyone writing SQL.", space_after=12)
    add_para(doc,
             "Natural language interfaces to databases (NLIDBs) try to solve this problem. The idea is "
             "simple: a user should be able to ask \"which categories have the highest refund rates "
             "this month?\" and get a correct, visual answer without writing SQL. Researchers have made "
             "good progress here. Neural text-to-SQL systems now exceed 90% accuracy on the Spider "
             f"benchmark {cite('yu_spider18')}, and large language models can produce reasonable-looking "
             f"SQL with minimal setup {cite('li_bird23')}. But there is still a gap between benchmark "
             "results and production-ready deployment.", space_after=0)

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
             "These problems are not primarily about building a smarter model; they are about designing "
             "the system properly around the model. AEGIS addresses this by splitting the work into "
             "stages. The LLM's only job is to understand what the user is asking and output a "
             "structured description of the request. Everything after that, matching to the right "
             "business terms, building the SQL, selecting the chart, and saving the widget, is done by "
             "fixed rules and pre-approved templates.", space_after=0)

    add_section_heading(doc, "1.3", "Research Novelty and Motivation")
    add_para(doc,
             "Existing text-to-SQL research asks: how accurately can a model generate SQL from natural "
             "language? This thesis asks a different question: how can large language models be used "
             "for language understanding while being structurally prevented from generating executable "
             "SQL at all? The two pipelines differ structurally.", space_after=10)
    add_para(doc, "Classical NL-to-SQL: natural-language request, then model-authored SQL, then query result.",
             italic=True, space_after=6)
    add_para(doc, "AEGIS: natural-language request, then intent extraction, semantic constraint, "
             "deterministic compilation, and a safe analytical artifact.", italic=True, space_after=12)
    add_para(doc,
             "The contribution of this thesis is therefore not improved SQL generation accuracy; it is "
             "constrained analytical artifact generation, a design approach that removes SQL generation "
             "from the LLM's role entirely and provides safety and semantic fidelity guarantees that no "
             "generative model can match unconditionally.", space_after=12)
    add_para(doc,
             "AEGIS does not propose a new LLM. The model is interchangeable: Groq-hosted Llama 3.1 8B, "
             "OpenRouter, a local Ollama instance, or any endpoint compatible with the "
             "/v1/chat/completions interface. Because the LLM's only contract with the rest of the "
             "system is to produce a typed JSON intent object, model upgrades improve quality "
             "automatically without changing the compiler or safety infrastructure. This is model "
             "independence by design, not an implementation accident.", space_after=0)

    add_section_heading(doc, "1.4", "Objectives and Contributions")
    add_para(doc, "This thesis makes the following contributions:",
             space_after=8)
    add_numbered(doc, "A design-time review of representative e-commerce and business-intelligence "
                 "reporting requests, resulting in eleven common reporting patterns later used to "
                 "structure the custom 107-request benchmark.")
    add_numbered(doc, "A system design in which all possible queries are limited to pre-approved "
                 "templates and a defined semantic layer, which prevents SQL injection and "
                 "unauthorized data access by construction.")
    add_numbered(doc, "The AEGIS system itself, including the semantic layer design, a vocabulary "
                 "injection prompting strategy, a safe SQL builder with two-layer defence, a rule-based "
                 "chart selector, and a widget storage system with scheduled refresh.")
    add_numbered(doc, "A vocabulary injection method that places approved metric and dimension names "
                 "directly into the LLM prompt, reducing dependence on a manually written synonym list.")
    add_numbered(doc, "A verified benchmark over 107 mixed natural-language requests, "
                 "separating SQL safety, true database execution validity, and semantic correctness "
                 "rather than treating them as one accuracy number.")
    add_numbered(doc, "A planned cross-schema generalizability evaluation that will test whether the "
                 "same compiler and safety architecture can be reused on a second e-commerce schema by "
                 "rebuilding only the semantic layer.")

    page_break(doc)

