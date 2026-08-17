# -*- coding: utf-8 -*-
"""Chapters 6-7: Limitations and Future Work, Conclusion, and References."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from build_thesis import (
    add_para,
    add_chapter_heading,
    add_section_heading,
    add_bullet,
    set_hanging_indent,
    page_break,
    FONT,
)
from refs import REFS


def chapter6(doc):
    add_chapter_heading(doc, 6, "Limitations and Future Work")

    add_section_heading(doc, "6.1", "Limitations")
    add_para(
        doc,
        "AEGIS is intentionally bounded. Its safety and auditability come from the "
        "fact that all answerable concepts must be declared in the semantic layer "
        "and all executable SQL must be produced by deterministic compiler templates. "
        "The limitations below should therefore be read as explicit boundaries of "
        "the current nopCommerce prototype, not as reasons to bypass the architecture "
        "with free-form SQL generation.",
        space_after=10,
    )
    add_bullet(
        doc,
        "The final evaluation is over one e-commerce deployment, nopCommerce. The "
        "results show that the architecture works in this domain, but they do not "
        "prove cross-domain generality.",
        bold_lead="Single-domain evaluation: ",
    )
    add_bullet(
        doc,
        "The 500-question dataset is static and checkable, but it is still "
        "author-generated. A stronger study would collect questions from store "
        "owners or administrators and annotate them with at least two reviewers.",
        bold_lead="Author-generated natural-language data: ",
    )
    add_bullet(
        doc,
        "Boundary questions about web telemetry, marketing attribution, support "
        "tickets, review-text sentiment, forecasting, churn prediction, supplier "
        "performance, fraud scoring, delivery SLA analysis, and product affinity "
        "are deliberately outside the current semantic layer.",
        bold_lead="Finite semantic coverage: ",
    )
    add_bullet(
        doc,
        "The Admin oracle benchmark reaches 15/16 result accuracy. The remaining "
        "dashboard mismatch requires a general multi-period matrix-summary primitive, "
        "not a hardcoded report-name preset.",
        bold_lead="Remaining Admin fidelity gap: ",
    )
    add_bullet(
        doc,
        "The compiler and safety layer are deterministic, but natural-language intent "
        "extraction still depends on the configured LLM API. Future work should compare "
        "multiple OpenAI-compatible models on the same static dataset.",
        bold_lead="LLM dependence for intent extraction: ",
    )
    add_bullet(
        doc,
        "The evaluated prototype targets nopCommerce on MySQL. This is an implementation "
        "and evaluation-scope choice, not an architectural limitation; other databases "
        "require dialect-specific compiler templates and safety rules.",
        bold_lead="Prototype database target: ",
    )
    add_bullet(
        doc,
        "The prototype stores widget metadata in simple local persistence. A production "
        "deployment should move the widget registry to a transactional database with "
        "migrations, ownership policies, and administrative audit views.",
        bold_lead="Widget persistence: ",
    )

    add_section_heading(doc, "6.2", "Future Work")
    add_bullet(
        doc,
        "Add the general matrix-summary primitive needed for the remaining Admin fidelity "
        "mismatch, while keeping the compiler template-based and avoiding report-specific "
        "presets.",
        bold_lead="Matrix summaries: ",
    )
    add_bullet(
        doc,
        "Repeat the static-dataset process on a second schema such as WooCommerce or a "
        "non-commerce operational database.",
        bold_lead="Cross-schema evaluation: ",
    )
    add_bullet(
        doc,
        "Build a guided interface so analysts can define metrics, dimensions, predicates, "
        "join paths, and display labels without editing Python code.",
        bold_lead="Semantic-layer tooling: ",
    )
    add_bullet(
        doc,
        "Collect real user questions and perform independent answerability and oracle "
        "annotation, including inter-annotator agreement.",
        bold_lead="Human dataset study: ",
    )
    add_bullet(
        doc,
        "Compare parser accuracy, refusal behavior, and execution validity across several "
        "OpenAI-compatible LLM APIs while keeping the compiler and semantic layer fixed.",
        bold_lead="Model comparison: ",
    )


def chapter7(doc):
    add_chapter_heading(doc, 7, "Conclusion")
    add_para(
        doc,
        "This thesis presented AEGIS, a constraint-based architecture for safe "
        "LLM-assisted natural-language analytics over relational databases. The "
        "system limits the language model to intent extraction while query construction, "
        "chart selection, and widget persistence are handled by deterministic components. "
        "This design makes approved business terms explicit through a semantic layer and "
        "avoids exposing raw SQL generation authority to the language model.",
        space_after=12,
    )
    add_para(
        doc,
        "The final evaluation used static nopCommerce datasets rather than an ad hoc "
        "one-time question set. On the 500-question live benchmark, AEGIS parsed 498 "
        "of 500 prompts, answered and executed 422 of 425 supported requests, and "
        "rejected or clarified 74 of 75 realistic boundary requests. Against 16 "
        "source-derived Admin analytics oracles, it achieved 16 of 16 execution "
        "validity, 16 of 16 shape accuracy, and 15 of 16 result accuracy. The focused "
        "semantic-coverage suite further confirmed representative supported and boundary "
        "cases.",
        space_after=12,
    )
    add_para(
        doc,
        "These results should be read with the right scope. AEGIS is not an infinite "
        "natural-language-to-SQL engine, and the thesis does not claim perfect accuracy. "
        "Its contribution is a bounded reporting architecture: if the semantic layer "
        "defines a business concept, the system can map natural language to a safe, "
        "refreshable analytical widget; if the concept is outside the layer, the correct "
        "behavior is to reject or clarify rather than invent an answer.",
        space_after=12,
    )
    add_para(
        doc,
        "The remaining Admin mismatch strengthens the evaluation because it shows that "
        "the benchmark can expose real implementation gaps. Fixing that gap should extend "
        "the general compiler with a reusable matrix-summary primitive, not add a "
        "nopCommerce-specific shortcut. Within this scope, AEGIS demonstrates a practical "
        "path toward safer, more auditable natural-language analytics in institutional "
        "dashboard systems.",
        space_after=0,
    )
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
