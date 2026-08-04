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
    add_mixed_para(doc, [("Semantic layer construction cost. ", True, False),
                          ("Every AEGIS deployment requires a domain-specific semantic layer built by "
                           "someone with both business knowledge and schema access. Organizations "
                           "without this expertise, or with rapidly evolving schemas, may find the "
                           "maintenance burden significant. AEGIS is not a zero-configuration system.",
                           False, False)])
    add_mixed_para(doc, [("Cannot answer arbitrary SQL questions. ", True, False),
                          ("By design, AEGIS only answers questions that map to a supported analytics "
                           "primitive with an approved metric and dimension. Ad hoc queries, "
                           "multi-level nested aggregations, or requests for data fields not in the "
                           "semantic layer fail with a coverage error. This is a deliberate trade-off, "
                           "not an oversight.", False, False)])
    add_mixed_para(doc, [("Complex analytical queries require new templates. ", True, False),
                          ("Approximately 2.6% of the formative-study requests required "
                           "patterns not yet in the template library. Adding a new pattern requires a "
                           "developer with SQL knowledge; it is not something a business user can do "
                           "themselves.", False, False)])
    add_mixed_para(doc, [("Quality depends on intent extraction, not just compilation. ", True, False),
                          ("The safety guarantees apply to compilation and execution, not "
                           "to intent extraction quality. A model that misclassifies a request will "
                           "produce a structurally safe but semantically wrong query. Safety and "
                           "accuracy are separate properties, and this thesis is careful not to "
                           "conflate them.", False, False)])
    add_mixed_para(doc, [("Benchmark selection. ", True, False),
                          ("The custom 107-query benchmark was necessary because "
                           "standard benchmarks such as Spider and BIRD do not evaluate SQL safety or "
                           "adherence to business logic; this also means the reported figures are not "
                           "directly comparable to Spider- or BIRD-reported numbers from other systems.",
                           False, False)])
    add_mixed_para(doc, [("Semantic layer scalability. ", True, False),
                          ("Modern context windows of roughly 128,000 tokens can hold approximately "
                           "2,500 distinct metric and dimension definitions; most enterprise "
                           "deployments expose fewer than 500 core concepts, so this is not a near-term "
                           "constraint, but very large vocabularies would need retrieval-augmented "
                           "vocabulary injection rather than injecting the entire semantic layer at "
                           "once.", False, False)])
    add_mixed_para(doc, [("Database agnosticism. ", True, False),
                          ("The current compiler generates MySQL syntax; supporting PostgreSQL or SQL "
                           "Server requires extending the compiler module, not redesigning the "
                           "architecture.", False, False)])
    add_mixed_para(doc, [("Storage persistence. ", True, False),
                          ("The prototype uses JSON flat files for widget storage; the widget registry "
                           "interface is designed to be swapped for a relational database in a "
                           "production deployment.", False, False)])
    add_mixed_para(doc, [("Multi-turn conversation. ", True, False),
                          ("AEGIS currently treats each request independently. Contextual carryover "
                           "across turns, of the kind studied in conversational text-to-SQL research, "
                           "is not yet implemented.", False, False)])
    add_mixed_para(doc, [("Vocabulary injection limitations. ", True, False),
                          ("Highly specialized domain terminology may require supplementary few-shot "
                           "examples in the prompt beyond the label and description pairs currently "
                           "injected.", False, False)], space_after=0)

    add_section_heading(doc, "6.2", "Future Work")
    add_bullet(doc, "Clarification requests: when confidence is low, AEGIS should ask a follow-up "
               "question instead of guessing, for example \"did you mean revenue or profit?\"")
    add_bullet(doc, "Semantic layer wizard: a guided interface for business analysts to define new "
               "metrics and dimensions without writing Python.")
    add_bullet(doc, "Multi-step queries: currently each query produces one widget; compound questions "
               "such as \"revenue trend and top 5 products side by side\" require two separate "
               "queries today.")
    add_bullet(doc, "Automated denial-of-service protection: query complexity scoring and server-side "
               "timeout enforcement, since the join graph bounds query cost but does not currently "
               "score it explicitly.")
    add_bullet(doc, "Broader schema coverage: extending the nopCommerce semantic layer to cover "
               "promotions, vendor analytics, and content-management engagement metrics.")
    add_bullet(doc, "Multi-turn conversational carryover, extending the single-turn design discussed "
               "above.")
    add_bullet(doc, "Outcome and rejection-category instrumentation: measuring, from real benchmark and "
                "production runs, the precise proportion of requests answered directly, answered after "
                "clarification, answered after a semantic layer extension, or rejected, and the relative "
                "frequency of each rejection category. This thesis currently "
                "reports these categories qualitatively; adding this instrumentation would let a future "
                "revision report a measured percentage breakdown rather than a qualitative one.")
    add_bullet(doc, "Semantic correctness benchmark: adding annotated expected-answer labels for the "
               "107 mixed requests so the evaluation can report correctness separately from SQL safety and "
               "true database execution validity.")
    add_bullet(doc, "Cross-schema generalizability benchmark: rebuilding the semantic layer for a second "
               "schema, such as WooCommerce, while keeping the intent parser contract, compiler "
               "structure, and safety scanner unchanged. This future evaluation would measure how much "
               "of AEGIS transfers across schemas and how much effort is required to configure a new "
               "domain.")
    add_bullet(doc, "Remaining baselines and latency: completing B2 and B4, then instrumenting pipeline "
               "latency with repeatable timing logs in future work.")
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

