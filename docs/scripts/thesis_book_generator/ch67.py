# -*- coding: utf-8 -*-
"""Chapters 6-7: Limitations and Future Work, Conclusion, and References."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from build_thesis import (add_para, add_mixed_para, add_chapter_heading, add_section_heading,
                           add_bullet, set_hanging_indent, page_break, FONT)
from refs import REFS
from docx.shared import Pt


def chapter6(doc):
    add_chapter_heading(doc, 6, "Limitations and Future Work")

    add_section_heading(doc, "6.1", "Limitations")
    add_bullet(doc, "Each deployment requires a domain-specific semantic layer prepared by someone "
               "with both business knowledge and schema access.", bold_lead="Semantic layer construction: ")
    add_bullet(doc, "AEGIS only answers questions that map to supported metrics, dimensions, "
               "patterns, and join paths.", bold_lead="Bounded query coverage: ")
    add_bullet(doc, "New analytical patterns require new compiler templates and SQL knowledge.",
               bold_lead="Template expansion: ")
    add_bullet(doc, "A misclassified intent can produce a safe but semantically wrong query, so "
               "accuracy must be measured separately from safety.", bold_lead="Intent extraction quality: ")
    add_bullet(doc, "The custom 107-request benchmark evaluates AEGIS in one domain and is not "
               "directly comparable to Spider or BIRD leaderboard scores.", bold_lead="Benchmark scope: ")
    add_bullet(doc, "Very large vocabularies may require retrieval-assisted selection instead of "
               "injecting the whole semantic layer.", bold_lead="Semantic layer scale: ")
    add_bullet(doc, "The current compiler targets MySQL; PostgreSQL or SQL Server support would "
               "require dialect-specific compiler extensions.", bold_lead="Database portability: ")
    add_bullet(doc, "The prototype uses JSON flat files for widget storage; production deployment "
               "should use a database-backed registry.", bold_lead="Storage persistence: ")
    add_bullet(doc, "Each request is handled independently, so follow-up questions and contextual "
               "carryover are not yet implemented.", bold_lead="Multi-turn conversation: ")
    add_bullet(doc, "Highly specialized terminology may require extra few-shot examples beyond "
               "the injected label and description pairs.", bold_lead="Domain vocabulary: ")

    add_section_heading(doc, "6.2", "Future Work")
    add_bullet(doc, "When confidence is low, AEGIS should ask a follow-up question instead of "
               "guessing, for example \"did you mean revenue or profit?\"",
               bold_lead="Clarification requests: ")
    add_bullet(doc, "A guided interface should let business analysts define new metrics and "
               "dimensions without writing Python.", bold_lead="Semantic layer wizard: ")
    add_bullet(doc, "Compound questions such as \"revenue trend and top 5 products side by side\" "
               "should create multiple coordinated widgets instead of requiring separate queries.",
               bold_lead="Multi-step queries: ")
    add_bullet(doc, "Query complexity scoring and server-side timeout enforcement should be added "
               "because the join graph bounds query shape but does not currently score runtime cost.",
               bold_lead="Automated denial-of-service protection: ")
    add_bullet(doc, "The nopCommerce semantic layer should be extended to cover promotions, vendor "
               "analytics, and content-management engagement metrics.", bold_lead="Broader schema coverage: ")
    add_bullet(doc, "Multi-turn conversational carryover, extending the single-turn design discussed "
               "above.")
    add_bullet(doc, "Future runs should measure the proportion of requests answered directly, answered "
                "after clarification, answered after a semantic-layer extension, or rejected.",
                bold_lead="Outcome and rejection-category instrumentation: ")
    add_bullet(doc, "Annotated expected-answer labels should be added for the 107 mixed requests so "
               "correctness can be reported separately from SQL safety and true execution validity.",
               bold_lead="Semantic correctness benchmark: ")
    add_bullet(doc, "A second schema, such as WooCommerce, should be evaluated while keeping the "
               "intent parser contract, compiler structure, and safety scanner unchanged.",
               bold_lead="Cross-schema generalizability benchmark: ")
    add_bullet(doc, "B2 and B4 should be completed, and pipeline latency should be instrumented with "
               "repeatable timing logs.", bold_lead="Remaining baselines and latency: ")
    page_break(doc)


def chapter7(doc):
    add_chapter_heading(doc, 7, "Conclusion")
    add_para(doc,
              "This thesis presented AEGIS, a constraint-based architecture for safe LLM-assisted "
              "natural-language analytics over relational databases. The system limits the language "
              "model to intent extraction while query construction, chart selection, and widget "
              "persistence are handled by deterministic components. This design makes approved "
              "business terms explicit through a semantic layer and avoids exposing raw SQL generation "
              "authority to the language model.",
              space_after=12)
    add_para(doc,
              "The prototype evaluation on a 107-request mixed benchmark showed that AEGIS produced "
              "no unsafe SQL statements and successfully executed 100 of 107 generated queries against "
              "the seeded MySQL database. In contrast, the direct LLM-to-SQL baseline executed 27 of "
              "107 queries successfully and produced one genuine unsafe write statement. These results "
              "support the main argument that deterministic compilation and semantic-layer constraints "
              "can improve SQL safety in natural-language reporting systems.",
              space_after=12)
    add_para(doc,
              "AEGIS is not a general-purpose text-to-SQL system. Its limitations include semantic "
              "layer construction cost, bounded query coverage, remaining execution failures, incomplete "
              "scope detection, and the need for a separately annotated semantic-correctness benchmark. "
              "Within this scope, the thesis demonstrates that restricting SQL generation to validated "
              "business patterns is a practical direction for safer, reusable, and more auditable "
              "natural-language analytics in institutional environments.", space_after=0)
    page_break(doc)


def references_chapter(doc):
    add_para(doc, "REFERENCES", size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)
    for i, (_key, text) in enumerate(REFS, start=1):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_after = Pt(10)
        pf.line_spacing = 1.3
        set_hanging_indent(p, 0.4, 0.4)
        r = p.add_run(f"[{i}]  {text}")
        r.font.name = FONT
        r.font.size = Pt(11.5)

