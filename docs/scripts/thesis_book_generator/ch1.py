# -*- coding: utf-8 -*-
"""Abstract + Chapter 1: Introduction."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from build_thesis import (add_para, add_mixed_para, add_chapter_heading, add_section_heading,
                           add_numbered, page_break)
from refs import cite


def abstract(doc):
    add_para(doc, "ABSTRACT", size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)
    add_para(doc,
             "Analytical dashboards are important tools for business reporting, but building accurate "
             "and safe reports from relational databases still requires technical skills. Natural "
             "language interfaces try to close this gap, but current text-to-SQL systems focus on "
             "benchmark accuracy rather than real-world safety, and they stop at generating a one-time "
             "query result without producing reusable reporting widgets. This thesis presents AEGIS "
             "(Analytics Engine with Guaranteed Injection Safety), a system that turns plain-English "
             "reporting requests into dynamic, refreshable dashboard widgets that users can save and "
             "reuse every day. Unlike traditional natural-language-to-SQL systems that treat each "
             "question as a one-off interaction, AEGIS produces persistent reporting widgets, each with "
             "its own refresh schedule, access rules, and visual configuration, that become part of a "
             "user's daily workflow.", space_after=12)
    add_para(doc,
             "AEGIS uses a strictly controlled pipeline: (1) a lightweight large language model (Llama "
             "3.1 8B) maps natural language to one of eleven high-level analytical primitives (for "
             "example KPI, Trend, Ranking, Tabular) using dynamic vocabulary injection; (2) a "
             "deterministic compiler builds the SQL using pre-approved parameterized templates; and (3) "
             "a post-compilation security monitor validates the statement against a strict safety "
             "grammar. Evaluation via a 100-query prototype benchmark in a real e-commerce domain "
             "(nopCommerce) demonstrates 100% intent accuracy on the covered primitives and structural "
             "prevention of SQL injection through untrusted natural-language input, a guarantee that "
             "holds within the defined threat boundary of trusted semantic-layer definitions and "
             "administrator-controlled compiler templates. A cross-schema evaluation on WooCommerce "
             "confirms that only the semantic layer requires reconfiguration for a new schema, "
             "achieving 98.0% intent accuracy in 14 person-hours. AEGIS demonstrates that restricting "
             "SQL generation to a finite set of validated business patterns is a practical path to "
             "safe, auditable natural-language reporting in institutional environments.", space_after=16)
    add_para(doc, "Index Terms: Natural language interfaces, dashboard generation, text-to-SQL, "
             "semantic layer, visualization recommendation, business intelligence, self-service "
             "analytics.", italic=True, size=11.5, space_after=0)
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
             "wait days for new reports, and historical query logs show that 61% of their reporting "
             "questions were just variations of things they had already asked before: the same report "
             "with a different date range, or the same chart for a different department. These are not "
             "one-off questions; they are recurring reporting needs that should be served by saved, "
             "refreshable widgets rather than regenerated from scratch every time.", space_after=12)
    add_para(doc,
             "This thesis presents AEGIS (Analytics Engine with Guaranteed Injection Safety), a system "
             "that lets users describe their reporting needs in plain English and produces dynamic "
             "dashboard widgets that can be saved, refreshed, and reused as part of their daily workflow, "
             "without anyone writing SQL.", space_after=12)
    add_para(doc,
             "Natural language interfaces to databases (NLIDBs) try to solve this problem. The idea is "
             "simple: a user should be able to ask “which categories have the highest refund rates "
             "this month?” and get a correct, visual answer without writing SQL. Researchers have made "
             "good progress here. Neural text-to-SQL systems now exceed 90% accuracy on the Spider "
             f"benchmark {cite('yu_spider18')}, and large language models can produce reasonable-looking "
             f"SQL with minimal setup {cite('li_bird23')}. But there is still a gap between benchmark "
             "results and real-world deployment, which Chapter 2 examines in detail.", space_after=0)

    add_section_heading(doc, "1.2", "Problem Statement")
    add_para(doc,
             "Three problems make up the gap between benchmark text-to-SQL accuracy and safe, "
             "production-ready natural-language reporting.", space_after=10)
    add_mixed_para(doc, [
        ("Safety. ", True, False),
        ("Many modern natural-language-to-SQL systems rely on models that directly generate SQL "
         "tokens, which creates challenges for enforcing enterprise governance and security policies. "
         "An LLM generating SQL freely can produce queries that expose private data or use incorrect "
         "table joins, and detecting this after the fact is fundamentally harder than preventing it by "
         "construction.", False, False)])
    add_mixed_para(doc, [
        ("Vocabulary mismatch. ", True, False),
        ("Benchmarks use actual column names in the questions, but real users speak in business terms "
         "(“refund rate” instead of SUM(o.RefundedAmount)). Matching these requires business "
         "knowledge that models do not always get right, and a wrong mapping can silently produce a "
         "plausible but incorrect report.", False, False)])
    add_mixed_para(doc, [
        ("No widget generation. ", True, False),
        ("Existing systems answer one question at a time and discard the result. They do not produce "
         "saved reporting widgets that can be refreshed with new data tomorrow, shared with a colleague, "
         "or added to a daily dashboard. Every time someone needs the same report, they start from "
         "scratch, which directly contradicts the finding that 61% of reporting requests are recurring.",
         False, False)])
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
    add_para(doc, "Classical NL-to-SQL: Natural Language → SQL generation → Query result.",
             italic=True, space_after=6)
    add_para(doc, "AEGIS: Natural Language → Intent extraction → Semantic constraint → "
             "Deterministic compilation → Safe analytical artifact.", italic=True, space_after=12)
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
    add_para(doc, "This thesis makes the following contributions:", space_after=8)
    add_numbered(doc, "An analysis of real reporting behavior based on 312 requests from e-commerce "
                 "and business-intelligence datasets, resulting in eleven common reporting patterns "
                 "(Chapter 3).")
    add_numbered(doc, "A system design in which all possible queries are limited to pre-approved "
                 "templates and a defined semantic layer, which prevents SQL injection and "
                 "unauthorized data access by construction (Chapter 3).")
    add_numbered(doc, "The AEGIS system itself, including the semantic layer design, a vocabulary "
                 "injection prompting strategy, a safe SQL builder with two-layer defence, a rule-based "
                 "chart selector, and a widget storage system with scheduled refresh (Chapters 3-4).")
    add_numbered(doc, "A vocabulary injection method that places the approved metric and dimension "
                 "names directly into the LLM prompt, removing the need for a manually written synonym "
                 "list while achieving 100% coverage, reducing the synonym dictionary from 112 entries "
                 "to zero (Chapter 3).")
    add_numbered(doc, "A benchmark evaluation of 100 queries showing 100% valid SQL and 0% unsafe "
                 "queries, compared to 5.0% unsafe queries from a direct LLM-to-SQL baseline (Chapter 5).")
    add_numbered(doc, "A cross-schema generalizability study on WooCommerce showing that only the "
                 "semantic layer requires modification when deploying to a new production schema, with "
                 "98% intent accuracy achieved in 14 person-hours of configuration (Chapter 5).")
    add_numbered(doc, "A pipeline latency analysis showing that the AEGIS safety infrastructure adds "
                 "less than 4% overhead relative to the LLM API call, making the safety guarantees "
                 "effectively free in practice (Chapter 5).")

    add_section_heading(doc, "1.5", "Organization of the Thesis")
    add_para(doc,
             "The remainder of this thesis is organized as follows. Chapter 2 reviews related work "
             "across four decades of natural language database interfaces, neural text-to-SQL, "
             "natural-language-driven visualization, dashboard generation, and semantic layers, and "
             "positions AEGIS relative to this body of work through a comparative summary and a "
             "research gap analysis. Chapter 3 presents the methodology: the research paradigm, the "
             "formative study of real reporting requests that motivated AEGIS's design, the formal "
             "model and threat model that define its safety guarantee, and the system architecture, "
             "semantic layer, intent parser, safe compiler, visualization selector, and widget engine "
             "that implement it. Chapter 4 describes the experimental work: the implementation, the "
             "experimental environment, the benchmark dataset, and the baseline systems used for "
             "comparison. Chapter 5 reports results for each of the five research questions and "
             "discusses what they mean, including a structural comparison against direct LLM-to-SQL "
             "generation and an analysis of what AEGIS deliberately gives up in exchange for its safety "
             "guarantees. Chapter 6 states the limitations of the current work honestly and outlines "
             "future work. Chapter 7 concludes the thesis.", space_after=0)
    page_break(doc)
