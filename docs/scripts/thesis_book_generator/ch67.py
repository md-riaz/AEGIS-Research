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
                           "someone with both business knowledge and schema access. The nopCommerce "
                           "prototype took approximately 40 person-hours. Organizations without this "
                           "expertise, or with rapidly evolving schemas, may find the maintenance "
                           "burden significant. AEGIS is not a zero-configuration system.", False, False)])
    add_mixed_para(doc, [("Cannot answer arbitrary SQL questions. ", True, False),
                          ("By design, AEGIS only answers questions that map to a supported analytics "
                           "primitive with an approved metric and dimension. Ad hoc queries, "
                           "multi-level nested aggregations, or requests for data fields not in the "
                           "semantic layer fail with a coverage error (Section 5.6). This is a "
                           "deliberate trade-off, not an oversight.", False, False)])
    add_mixed_para(doc, [("Complex analytical queries require new templates. ", True, False),
                          ("Approximately 2.6% of the formative-study requests (Section 3.2) required "
                           "patterns not yet in the template library. Adding a new pattern requires a "
                           "developer with SQL knowledge; it is not something a business user can do "
                           "themselves.", False, False)])
    add_mixed_para(doc, [("Quality depends on intent extraction, not just compilation. ", True, False),
                          ("The safety guarantees in Chapter 3 apply to compilation and execution, not "
                           "to intent extraction quality. A model that misclassifies a request will "
                           "produce a structurally safe but semantically wrong query. Safety and "
                           "accuracy are separate properties, and this thesis is careful not to "
                           "conflate them.", False, False)])
    add_mixed_para(doc, [("Benchmark selection. ", True, False),
                          ("The custom 100-query benchmark (Section 4.3) was necessary because "
                           "standard benchmarks such as Spider and BIRD do not evaluate adversarial "
                           "safety or adherence to business logic; this also means the reported "
                           "accuracy figures are not directly comparable to Spider- or BIRD-reported "
                           "numbers from other systems.", False, False)])
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
                           "across turns, of the kind studied for conversational text-to-SQL in Section "
                           "2.2, is not yet implemented.", False, False)])
    add_mixed_para(doc, [("Vocabulary injection limitations. ", True, False),
                          ("Highly specialized domain terminology may require supplementary few-shot "
                           "examples in the prompt beyond the label and description pairs currently "
                           "injected.", False, False)], space_after=0)

    add_section_heading(doc, "6.2", "Future Work")
    add_bullet(doc, "Clarification requests: when confidence is low, AEGIS should ask a follow-up "
               "question instead of guessing, for example “did you mean revenue or profit?”")
    add_bullet(doc, "Semantic layer wizard: a guided interface for business analysts to define new "
               "metrics and dimensions without writing Python.")
    add_bullet(doc, "Multi-step queries: currently each query produces one widget; compound questions "
               "such as “revenue trend and top 5 products side by side” require two separate "
               "queries today.")
    add_bullet(doc, "Automated denial-of-service protection: query complexity scoring and server-side "
               "timeout enforcement, since the join graph bounds query cost but does not currently "
               "score it explicitly.")
    add_bullet(doc, "Broader schema coverage: extending the nopCommerce semantic layer to cover "
               "promotions, vendor analytics, and content-management engagement metrics.")
    add_bullet(doc, "Multi-turn conversational carryover, extending the single-turn design discussed "
               "above.")
    page_break(doc)


def chapter7(doc):
    add_chapter_heading(doc, 7, "Conclusion")
    add_para(doc,
              "This thesis presented AEGIS, a system for turning plain-English reporting requests into "
              "dynamic, refreshable dashboard widgets over relational databases. The central "
              "contribution has two parts. First, a system design that limits the language model to "
              "understanding questions, while all query building, chart selection, and widget storage "
              "is handled by fixed rules and pre-approved templates, so that safety is a property "
              "guaranteed by system structure rather than a probability that improves with model "
              "quality. Second, a vocabulary injection method that removes the need for manually "
              "maintained synonym lists while improving coverage, reducing a 112-entry synonym "
              "dictionary to zero entries while raising coverage from 99% to 100%.", space_after=12)
    add_para(doc,
              "The evaluation in Chapter 5 shows that AEGIS reduces the unsafe SQL rate from 5.0% to "
              "0% relative to a direct LLM-to-SQL baseline using the same underlying model, achieves "
              "100% valid SQL and 100% coverage on its 100-query nopCommerce benchmark, and generalizes "
              "to a second production schema, WooCommerce, with only semantic layer reconfiguration "
              "required and no change to the LLM, the compiler, or the safety scanner. The pipeline "
              "latency analysis confirms that this safety infrastructure adds less than 4% overhead "
              "relative to the LLM API call that any comparable system would also need to make.",
              space_after=12)
    add_para(doc,
              "The literature review in Chapter 2 situates this contribution precisely: prior "
              "text-to-SQL research, from Seq2SQL through RAT-SQL and PICARD, treats SQL-generation "
              "accuracy as the object of study and, with the partial exception of a 2025 systematic "
              "review's discussion of injection attacks, does not evaluate safety as a first-class "
              "property at all. AEGIS's architectural choice, removing SQL generation from the "
              "language model's role entirely rather than constraining it more tightly, is a "
              "categorically different answer to the same underlying problem, and one independently "
              "echoed in recent explanatory-analytics research reviewed in Section 2.7 that arrives at "
              "the same “let a deterministic layer compute the answer” principle in an unrelated "
              "domain.", space_after=12)
    add_para(doc,
              "AEGIS is built for environments where data privacy, consistent reporting definitions, "
              "and daily reuse of saved reports matter more than unlimited query flexibility. Chapter 6 "
              "states plainly what this design gives up in exchange: a bounded vocabulary, an upfront "
              "semantic layer construction cost, and dependence on intent-extraction quality for "
              "semantic (though never safety) correctness. Within that scope, this thesis demonstrates "
              "that restricting SQL generation to a finite set of validated business patterns is a "
              "practical, measurable path to safe, auditable natural-language reporting in "
              "institutional environments.", space_after=0)
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
