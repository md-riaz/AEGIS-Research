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
    add_bullet(doc, "The first-pass annotation found that safe SQL can still answer the wrong "
               "business question, especially when requests are unsupported or vague.",
               bold_lead="Correctness annotation: ")
    add_bullet(doc, "The custom 107-request benchmark evaluates AEGIS in one domain and is not "
               "directly comparable to Spider or BIRD leaderboard scores.", bold_lead="Benchmark scope: ")
    add_bullet(doc, "True database execution validity and the first-pass semantic-correctness "
               "annotation (Sections 5.4 and 5.6) were measured against the pipeline version that "
               "existed before the abstention-handling interventions in Section 5.9, and have not been "
               "re-measured against the current pipeline.", bold_lead="Metric currency: ")
    add_bullet(doc, "Translation precision and silent error rate (Section 5.9) are scored against "
               "correctness labels that describe the earlier pipeline's SQL and cannot be reported as "
               "current findings until the annotation file is redone against the current pipeline.",
               bold_lead="Re-annotation required: ")
    add_bullet(doc, "The current version targets MySQL, uses prototype widget storage, and handles "
               "each request independently without multi-turn context.",
               bold_lead="Prototype engineering limits: ")

    add_section_heading(doc, "6.2", "Future Work")
    add_bullet(doc, "When confidence is low, AEGIS should ask a follow-up question instead of "
               "guessing, for example \"did you mean revenue or profit?\"",
               bold_lead="Clarification requests: ")
    add_bullet(doc, "A guided interface should let business analysts define new metrics and "
               "dimensions, join paths, and approved vocabulary without editing Python code.",
               bold_lead="Semantic-layer tooling: ")
    add_bullet(doc, "The machine-assisted correctness annotation should be reviewed manually, and "
               "future work should add stronger robustness tests and cross-schema evaluation.",
               bold_lead="Stronger evaluation: ")
    add_bullet(doc, "A second schema, such as WooCommerce, should be evaluated while keeping the "
               "intent parser contract, compiler structure, and safety scanner unchanged.",
               bold_lead="Cross-schema evaluation: ")
    add_bullet(doc, "Query-cost controls, database-backed widget storage, broader schema coverage, "
               "and multi-turn support should be added before production deployment.",
               bold_lead="Production hardening: ")

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
              "no unsafe SQL statements and, in the baseline pipeline run described in Section 5.4, "
              "successfully executed 100 of 107 generated queries against the seeded MySQL database. In "
              "contrast, the direct LLM-to-SQL baseline executed 27 of 107 queries successfully and "
              "produced one genuine unsafe write statement. A first-pass semantic-correctness annotation "
              "also showed stronger answerable-request correctness for AEGIS than for the evaluated "
              "baselines, though that annotation is scored against the same earlier pipeline and is not "
              "re-measured. These results support the main argument that deterministic compilation and "
              "semantic-layer constraints can improve SQL safety in natural-language reporting systems.",
              space_after=12)
    add_para(doc,
              "The abstention-aware evaluation in Section 5.9 is the thesis's central result on "
              "correctness rather than safety. Across three measured stages, false abstention fell from "
              "61.8% to 40.0% to the current 23.6%, while abstention recall held at 100.0% throughout, "
              "and no architectural change was required at any step: each improvement came from "
              "validating a self-reported model signal, separating time granularity from time "
              "filtering, or extending the semantic layer's table coverage. This supports treating "
              "semantic accuracy in this architecture as an implementation and configuration property "
              "rather than an architectural one. Section 5.10 further shows that AEGIS reproduces all "
              "20 of nopCommerce's own standard admin reports from natural language, a coverage check "
              "whose question list is fixed by the host platform rather than by the thesis author.",
              space_after=12)
    add_para(doc,
              "AEGIS is not a general-purpose text-to-SQL system. Its limitations include semantic "
              "layer construction cost, bounded query coverage, remaining execution failures, incomplete "
              "scope detection, a false abstention rate that has not reached zero, and the need for a "
              "separately re-annotated semantic-correctness benchmark against the current pipeline. "
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

